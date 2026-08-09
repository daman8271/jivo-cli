package engine

import (
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strings"

	"jivodist/internal/manifest"
)

// Kind orders what a staged file is, and doubles as the precedence rule when
// two sources claim the same bundle path: a binary listed as another tool's
// companion file must still land executable.
type Kind int

const (
	KindBinary    Kind = iota // 0755, the runnable thing
	KindEnv                   // 0600, credentials
	KindData                  // companion files, product-identity, examples
	KindDoc                   // 0644, documentation
	KindGenerated             // README.txt and other per-bundle output
)

func (k Kind) String() string {
	switch k {
	case KindBinary:
		return "binary"
	case KindEnv:
		return "env"
	case KindData:
		return "data"
	case KindDoc:
		return "doc"
	default:
		return "generated"
	}
}

// StagedFile is one entry of the ship list. Exactly one of Src (copy from disk)
// and Content (generated in memory) is set.
type StagedFile struct {
	Src       string      `json:"src,omitempty"` // repo-relative, or absolute for out-of-repo sources
	ZipPath   string      `json:"zip_path"`      // path below the bundle's jivo-cli/ root
	Mode      os.FileMode `json:"-"`
	Kind      Kind        `json:"kind"`
	Component string      `json:"component"`
	Content   []byte      `json:"-"`
}

// Skip is a tool that could not be included, and why. It is reported to the
// operator before the download rather than discovered by the recipient.
type Skip struct {
	Component string `json:"component"`
	Tool      string `json:"tool"`
	Reason    string `json:"reason"`
}

// Resolution is the outcome of resolving one component's ship list.
type Resolution struct {
	Files    []StagedFile
	Skipped  []Skip
	Warnings []string
	// ToolsIncluded/ToolsSkipped drive the UI's availability badge.
	ToolsIncluded int
	ToolsSkipped  int
}

// ResolveComponent works out exactly which files a component contributes to a
// bundle for one target. It is an allowlist: every file is named, by the
// manifest or by PLAN.md §5. Nothing is ever included by copying a directory,
// except the package directories the manifest itself names (a Python package
// cannot be split), and those are filtered through the deny list.
func ResolveComponent(repoRoot, homeDir string, c *manifest.Component, target string, includeDocs bool) Resolution {
	var res Resolution
	add := func(f StagedFile) {
		if err := ValidZipPath(f.ZipPath); err != nil {
			res.Warnings = append(res.Warnings, fmt.Sprintf("%s: %v", c.ID, err))
			return
		}
		if pattern, bad := Denied(f.ZipPath); bad {
			res.Warnings = append(res.Warnings,
				fmt.Sprintf("%s: %s was refused by the deny list (%s) and is not in the bundle", c.ID, f.ZipPath, pattern))
			return
		}
		f.Component = c.ID
		res.Files = append(res.Files, f)
	}

	for _, tool := range c.Tools {
		staged := 0
		var declared []string
		var reasons []string
		for _, b := range tool.Binaries {
			if b.OS != target {
				if !containsString(declared, b.OS) {
					declared = append(declared, b.OS)
				}
				continue
			}
			abs := filepath.Join(repoRoot, b.Path)
			st, err := os.Stat(abs)
			switch {
			case err != nil && b.Exists:
				// The manifest was written on a machine where this existed.
				reasons = append(reasons, fmt.Sprintf(
					"the manifest lists %s but it is not on this machine — build it (%s) and re-bundle", b.Path, b.BuildCmd))
			case err != nil:
				reasons = append(reasons, fmt.Sprintf("no %s binary prebuilt (%s has never been built)", target, b.Path))
			case st.IsDir():
				reasons = append(reasons, fmt.Sprintf(
					"%s is a directory, not a runnable file — the manifest's %s entry for this tool is wrong", b.Path, target))
			default:
				add(StagedFile{Src: b.Path, ZipPath: b.Path, Mode: 0o755, Kind: KindBinary})
				staged++
			}
		}

		if staged == 0 {
			if len(reasons) == 0 {
				sort.Strings(declared)
				reason := fmt.Sprintf("no %s binary prebuilt", target)
				if len(declared) > 0 {
					reason += " (the manifest has only: " + strings.Join(declared, ", ") + ")"
				}
				reasons = append(reasons, reason)
			}
			res.Skipped = append(res.Skipped, Skip{
				Component: c.ID, Tool: tool.Name, Reason: strings.Join(reasons, "; "),
			})
			res.ToolsSkipped++
			continue
		}
		res.ToolsIncluded++

		// Companion files travel only with an included tool.
		for _, raw := range tool.CompanionFiles {
			for _, f := range expandCompanion(repoRoot, raw) {
				add(f)
			}
		}
	}

	// Nothing of this component runs on this target: skip its docs and env too,
	// so a bundle never carries credentials for a tool it does not contain.
	if res.ToolsIncluded == 0 {
		return res
	}

	if includeDocs {
		for _, d := range c.DocsToShip {
			abs := filepath.Join(repoRoot, d)
			if st, err := os.Stat(abs); err != nil || st.IsDir() {
				res.Warnings = append(res.Warnings, fmt.Sprintf("%s: doc %s is missing on this machine", c.ID, d))
				continue
			}
			add(StagedFile{Src: d, ZipPath: d, Mode: fileMode(abs, 0o644), Kind: KindDoc})
		}
	}

	spec := envPlan[c.ID]

	for _, e := range spec.extras {
		abs := filepath.Join(repoRoot, e.src)
		if st, err := os.Stat(abs); err != nil || st.IsDir() {
			res.Warnings = append(res.Warnings, fmt.Sprintf("%s: %s is missing on this machine", c.ID, e.src))
			continue
		}
		add(StagedFile{Src: e.src, ZipPath: e.dst, Mode: fileMode(abs, 0o644), Kind: KindData})
	}

	for _, cp := range spec.copies {
		if !appliesToTarget(cp.targets, target) {
			continue
		}
		abs := resolveSrc(repoRoot, homeDir, cp.src)
		if st, err := os.Stat(abs); err != nil || st.IsDir() {
			msg := fmt.Sprintf("%s: credential file %s not found — %s is not in the bundle", c.ID, cp.src, cp.dst)
			if cp.note != "" {
				msg += " (" + cp.note + ")"
			}
			if !cp.optional {
				msg = "MISSING CREDENTIAL — " + msg
			}
			res.Warnings = append(res.Warnings, msg)
			continue
		}
		add(StagedFile{Src: abs, ZipPath: cp.dst, Mode: cp.mode, Kind: KindEnv})
	}

	// Per-component generated files.
	switch c.ID {
	case "dsr-cli":
		content, warns := BakeDSREnv(repoRoot)
		res.Warnings = append(res.Warnings, warns...)
		add(StagedFile{ZipPath: "dsr-cli/.env", Mode: 0o600, Kind: KindEnv, Content: content})
	case "exim":
		add(StagedFile{ZipPath: "exim/.secrets/README.txt", Mode: 0o644, Kind: KindData,
			Content: []byte(eximSecretsPlaceholder)})
	}

	return res
}

// expandCompanion turns one companion_files entry into staged files. Entries
// carry human annotations in parentheses, and a trailing slash means a package
// directory that must ship whole (a Python package cannot be split).
func expandCompanion(repoRoot, raw string) []StagedFile {
	p := strings.TrimSpace(raw)
	if i := strings.Index(p, " ("); i >= 0 {
		p = strings.TrimSpace(p[:i])
	}
	if p == "" {
		return nil
	}
	abs := filepath.Join(repoRoot, p)

	if !strings.HasSuffix(p, "/") {
		st, err := os.Stat(abs)
		if err != nil || st.IsDir() {
			return nil
		}
		return []StagedFile{{Src: p, ZipPath: p, Mode: fileMode(abs, 0o644), Kind: KindData}}
	}

	dir := strings.TrimSuffix(p, "/")
	abs = filepath.Join(repoRoot, dir)
	var out []StagedFile
	_ = filepath.WalkDir(abs, func(fp string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		rel, rerr := filepath.Rel(repoRoot, fp)
		if rerr != nil {
			return nil
		}
		rel = filepath.ToSlash(rel)
		if _, bad := Denied(rel); bad {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}
		if d.IsDir() {
			return nil
		}
		out = append(out, StagedFile{Src: rel, ZipPath: rel, Mode: fileMode(fp, 0o644), Kind: KindData})
		return nil
	})
	sort.Slice(out, func(i, j int) bool { return out[i].ZipPath < out[j].ZipPath })
	return out
}

// Dedupe collapses files claimed by more than one tool or component, keeping
// the strongest kind. ecom-cli's MCP server lists the CLI binary as a companion
// file; without this the binary would land at 0644 and the bundle is dead.
func Dedupe(files []StagedFile) []StagedFile {
	best := map[string]StagedFile{}
	var order []string
	for _, f := range files {
		prev, seen := best[f.ZipPath]
		if !seen {
			best[f.ZipPath] = f
			order = append(order, f.ZipPath)
			continue
		}
		if f.Kind < prev.Kind {
			best[f.ZipPath] = f
		}
	}
	out := make([]StagedFile, 0, len(order))
	for _, p := range order {
		out = append(out, best[p])
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ZipPath < out[j].ZipPath })
	return out
}

// ShipList resolves a whole selection: every component, deduped, plus the
// filtered root .env. It does not write anything.
func ShipList(repoRoot, homeDir string, m *manifest.Manifest, components []string, target string, includeDocs bool) (files []StagedFile, skipped []Skip, warnings []string, err error) {
	if !manifest.ValidTarget(target) {
		return nil, nil, nil, fmt.Errorf("unknown target %q (want one of %s)", target, strings.Join(manifest.Targets, ", "))
	}
	if len(components) == 0 {
		return nil, nil, nil, fmt.Errorf("empty selection: pick at least one component")
	}

	var included []string
	for _, id := range components {
		c, ok := m.Component(id)
		if !ok {
			return nil, nil, nil, fmt.Errorf("unknown component %q", id)
		}
		if !c.Distributable {
			return nil, nil, nil, fmt.Errorf("component %q is not distributable", id)
		}
		if !HasEnvPlan(id) {
			// Refuse rather than ship a component whose credential story nobody
			// has written down — the alternative is a silent, credential-less
			// bundle that claims to be ready.
			return nil, nil, nil, fmt.Errorf(
				"no env plan for component %q — add it to envPlan in internal/engine/envbake.go (see PLAN.md §5)", id)
		}
		res := ResolveComponent(repoRoot, homeDir, c, target, includeDocs)
		files = append(files, res.Files...)
		skipped = append(skipped, res.Skipped...)
		warnings = append(warnings, res.Warnings...)
		if res.ToolsIncluded > 0 {
			included = append(included, id)
		} else {
			warnings = append(warnings, fmt.Sprintf("%s: nothing to ship for %s — the whole component was left out", id, target))
		}
	}

	// A zip holding nothing but a README is not a bundle. Fail rather than hand
	// an operator a file to send that contains none of the tools they picked.
	if len(included) == 0 {
		return nil, nil, nil, fmt.Errorf(
			"selection contains nothing for target %s: none of %s has a binary for it on this machine",
			target, strings.Join(components, ", "))
	}

	rootEnv, envWarns, err := BakeRootEnv(repoRoot, included, target)
	if err != nil {
		return nil, nil, nil, err
	}
	warnings = append(warnings, envWarns...)
	if rootEnv != nil {
		files = append(files, StagedFile{ZipPath: ".env", Mode: 0o600, Kind: KindEnv, Content: rootEnv, Component: "kit"})
	}

	files = Dedupe(files)

	if target == "windows" {
		if err := AssertWindowsSafe(files); err != nil {
			return nil, nil, nil, err
		}
	}
	return files, skipped, warnings, nil
}

// ZipPaths is the ship list as plain sorted paths — the shape the golden tests
// compare against.
func ZipPaths(files []StagedFile) []string {
	out := make([]string, 0, len(files))
	for _, f := range files {
		out = append(out, f.ZipPath)
	}
	sort.Strings(out)
	return out
}

// EstimatedSize is the uncompressed size of a ship list, for the UI.
//
// It deduplicates first, with the same key staging uses. Several components
// nominate the same files (product-identity is claimed by both factory-cli and
// jivo-scraping-cli; ecom-cli's MCP tool nominates the CLI binary), and
// counting the raw list over-reported the full kit by about a fifth — a number
// the operator reads before every click.
func EstimatedSize(repoRoot string, files []StagedFile) int64 {
	var total int64
	for _, f := range Dedupe(files) {
		if f.Content != nil {
			total += int64(len(f.Content))
			continue
		}
		p := f.Src
		if !filepath.IsAbs(p) {
			p = filepath.Join(repoRoot, f.Src)
		}
		if st, err := os.Stat(p); err == nil {
			total += st.Size()
		}
	}
	return total
}

// BundleRoot is the single top-level folder inside every zip. The mirrored repo
// layout is what lets every tool's own env-resolution work unchanged.
const BundleRoot = "jivo-cli"

// zipName joins the bundle root to a staged path with forward slashes.
func zipName(rel string) string { return path.Join(BundleRoot, rel) }
