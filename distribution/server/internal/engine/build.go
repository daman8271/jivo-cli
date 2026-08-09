package engine

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"jivodist/internal/manifest"
)

// Selection is what an operator ticked in the UI. It is also the CLI's
// -selection file and the POST /api/bundle body.
type Selection struct {
	Target      string   `json:"target"`
	Components  []string `json:"components"`
	Recipient   string   `json:"recipient"`
	IncludeDocs bool     `json:"include_docs"`
}

// Result is what a build produced, reported before the download so warnings are
// read first.
type Result struct {
	BundleID    string   `json:"bundle_id"`
	Filename    string   `json:"filename"`
	ZipPath     string   `json:"zip_path"`
	SizeBytes   int64    `json:"size_bytes"`
	SHA256      string   `json:"sha256"`
	Warnings    []string `json:"warnings"`
	Skipped     []Skip   `json:"skipped"`
	DownloadURL string   `json:"download_url"`
	FileCount   int      `json:"file_count"`
}

// Options are the knobs a caller may change; the zero value is the normal case.
type Options struct {
	KeepStaging bool      // stage under distribution/staging/ instead of a temp dir
	OutPath     string    // explicit output path (CLI -o); relative to the repo root
	Now         time.Time // fixed clock, for tests
	HomeDir     string    // overrides os.UserHomeDir, for tests
}

// DistDir and StagingDir are the two gitignored output directories.
const (
	DistDir    = "distribution/dist"
	StagingDir = "distribution/staging"
)

// Build produces one bundle. In order: gitignore guard, resolve the ship list,
// stage outside the repo, generate the README, deny-list gate over the finished
// staging tree, zip, checksum.
func Build(repoRoot string, sel Selection, opt Options) (*Result, error) {
	if opt.Now.IsZero() {
		opt.Now = time.Now()
	}
	if opt.HomeDir == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("home directory: %w", err)
		}
		opt.HomeDir = home
	}

	// Secrets can only be committed from a directory git can see. Refuse to
	// build if either output directory has stopped being ignored.
	if err := AssertIgnored(repoRoot, GuardedOutputDirs...); err != nil {
		return nil, err
	}

	m, err := manifest.Load(repoRoot)
	if err != nil {
		return nil, err
	}
	overrides, err := manifest.LoadOverrides(repoRoot)
	if err != nil {
		return nil, err
	}

	files, skipped, warnings, err := ShipList(repoRoot, opt.HomeDir, m, sel.Components, sel.Target, sel.IncludeDocs)
	if err != nil {
		return nil, err
	}

	// Settle the identity and the output path before anything is rendered: the
	// bundle id goes into the README, so it has to be final first.
	bundleID := newBundleID(opt.Now)
	filename := bundleFilename(sel, bundleID)
	outAbs, err := resolveOutPath(repoRoot, opt.OutPath, filename)
	if err != nil {
		return nil, err
	}
	if opt.OutPath == "" {
		// The random suffix makes a same-minute collision unlikely, not
		// impossible. Overwriting would destroy a bundle an operator may
		// already have sent, so re-mint until the name is genuinely free.
		for tries := 0; ; tries++ {
			if _, statErr := os.Stat(outAbs); os.IsNotExist(statErr) {
				break
			}
			if tries >= 20 {
				return nil, fmt.Errorf("could not find a free bundle name in %s — clear out old bundles", DistDir)
			}
			bundleID = newBundleID(opt.Now)
			filename = bundleFilename(sel, bundleID)
			outAbs, err = resolveOutPath(repoRoot, "", filename)
			if err != nil {
				return nil, err
			}
		}
	}

	var included []string
	for _, id := range sel.Components {
		if toolIncluded(files, id) {
			included = append(included, id)
		}
	}

	warnings = CollectWarnings(overrides, included, files, sel.Target, warnings)

	readme := RenderReadme(ReadmeInput{
		Target:      sel.Target,
		Recipient:   sel.Recipient,
		BundleID:    bundleID,
		GeneratedAt: opt.Now,
		Manifest:    m,
		Components:  included,
		Files:       files,
		Skipped:     skipped,
		Warnings:    warnings,
		Overrides:   overrides,
	})
	files = append(files, StagedFile{
		ZipPath: "README.txt", Mode: 0o644, Kind: KindGenerated,
		Component: "kit", Content: readme,
	})
	files = Dedupe(files)

	stageRoot, cleanup, err := makeStaging(repoRoot, bundleID, opt.KeepStaging)
	if err != nil {
		return nil, err
	}
	defer cleanup()

	if err := stageFiles(repoRoot, stageRoot, files); err != nil {
		return nil, err
	}

	// Last gate before anything is archived: independent of the allowlist.
	if err := AssertClean(stageRoot); err != nil {
		return nil, err
	}

	if err := WriteZip(stageRoot, outAbs); err != nil {
		return nil, err
	}
	if err := AssertZipClean(outAbs); err != nil {
		os.Remove(outAbs)
		os.Remove(outAbs + TmpSuffix)
		return nil, err
	}

	sum, err := SHA256File(outAbs)
	if err != nil {
		return nil, err
	}
	st, err := os.Stat(outAbs)
	if err != nil {
		return nil, err
	}

	// Never null in JSON: the UI iterates these unconditionally.
	if warnings == nil {
		warnings = []string{}
	}
	if skipped == nil {
		skipped = []Skip{}
	}

	return &Result{
		BundleID:    bundleID,
		Filename:    filepath.Base(outAbs),
		ZipPath:     outAbs,
		SizeBytes:   st.Size(),
		SHA256:      sum,
		Warnings:    warnings,
		Skipped:     skipped,
		DownloadURL: "/api/bundle/" + bundleID + "/download",
		FileCount:   len(files),
	}, nil
}

// resolveOutPath picks where the zip lands: the operator's explicit -o, or the
// gitignored dist/ directory under the generated name.
func resolveOutPath(repoRoot, explicit, filename string) (string, error) {
	rel := explicit
	if rel == "" {
		rel = filepath.Join(DistDir, filename)
	}
	if filepath.IsAbs(rel) {
		return rel, nil
	}
	return filepath.Join(repoRoot, rel), nil
}

// makeStaging returns the directory that becomes the zip's jivo-cli/ folder.
// It lives in a temp dir by default — outside the repo, where a stray `git add`
// cannot reach it.
func makeStaging(repoRoot, bundleID string, keep bool) (string, func(), error) {
	if keep {
		root := filepath.Join(repoRoot, StagingDir, bundleID)
		if err := os.MkdirAll(root, 0o755); err != nil {
			return "", nil, err
		}
		return root, func() {}, nil
	}
	dir, err := os.MkdirTemp("", "jivodist-"+bundleID+"-")
	if err != nil {
		return "", nil, err
	}
	root := filepath.Join(dir, BundleRoot)
	if err := os.MkdirAll(root, 0o755); err != nil {
		os.RemoveAll(dir)
		return "", nil, err
	}
	return root, func() { os.RemoveAll(dir) }, nil
}

func stageFiles(repoRoot, stageRoot string, files []StagedFile) error {
	for _, f := range files {
		// Containment, checked again at the moment of the join: nothing may be
		// written outside the staging tree, whatever the manifest says.
		if err := ValidZipPath(f.ZipPath); err != nil {
			return fmt.Errorf("staging: %w", err)
		}
		dst := filepath.Join(stageRoot, filepath.FromSlash(f.ZipPath))
		if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
			return err
		}
		if f.Content != nil {
			if err := os.WriteFile(dst, f.Content, f.Mode); err != nil {
				return err
			}
		} else {
			src := f.Src
			if !filepath.IsAbs(src) {
				src = filepath.Join(repoRoot, f.Src)
			}
			if err := copyFile(src, dst); err != nil {
				return fmt.Errorf("staging %s: %w", f.ZipPath, err)
			}
		}
		// Explicit chmod: os.WriteFile and os.Create both apply the umask.
		if err := os.Chmod(dst, f.Mode); err != nil {
			return err
		}
	}
	return nil
}

// copyFile copies bytes verbatim. Nothing is translated — the product-identity
// JSON is checksum-pinned and a single changed byte breaks it.
func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.OpenFile(dst, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		return err
	}
	return out.Close()
}

// bundleIDPattern matches the id embedded in every bundle filename:
// 20260810-1430-a1b2. It is what lets a zip found on disk be mapped back to its
// build id without any server-side state.
var bundleIDPattern = regexp.MustCompile(`\d{8}-\d{4}-[0-9a-f]{4}`)

func newBundleID(now time.Time) string {
	var b [2]byte
	if _, err := rand.Read(b[:]); err != nil {
		return now.Format("20060102-1504") + "-0000"
	}
	return now.Format("20060102-1504") + "-" + hex.EncodeToString(b[:])
}

// BundleIDFromFilename recovers the build id from a bundle filename, or ""
// if the name does not carry one.
func BundleIDFromFilename(name string) string {
	return bundleIDPattern.FindString(name)
}

// bundleFilename embeds the whole bundle id — date, time and the random suffix.
// Two bundles built for the same person on the same day must not collide: the
// second would silently overwrite the first, and the id-to-file mapping would
// stop being one-to-one.
func bundleFilename(sel Selection, bundleID string) string {
	recipient := sanitize(sel.Recipient)
	if recipient == "" {
		recipient = "kit"
	}
	return fmt.Sprintf("jivo-kit-%s-%s-%s.zip", sel.Target, bundleID, recipient)
}

// sanitize keeps a recipient name safe for a filename and a URL.
func sanitize(s string) string {
	var b strings.Builder
	for _, r := range strings.ToLower(strings.TrimSpace(s)) {
		switch {
		case r >= 'a' && r <= 'z', r >= '0' && r <= '9':
			b.WriteRune(r)
		case r == '-' || r == '_' || r == ' ':
			b.WriteRune('-')
		}
	}
	return strings.Trim(b.String(), "-")
}

// CollectWarnings merges the build's own findings with the hand-maintained
// overrides that apply to this selection. Both the API response and the
// recipient's README are rendered from the result, so they can never disagree.
func CollectWarnings(o *manifest.Overrides, included []string, files []StagedFile, target string, base []string) []string {
	out := append([]string(nil), base...)
	out = append(out, scopeWarnings(o.Global, target)...)
	for _, id := range included {
		out = append(out, scopeWarnings(o.Components[id], target)...)
	}
	for _, f := range files {
		if f.Kind == KindBinary {
			out = append(out, scopeWarnings(o.Binaries[f.Src], target)...)
		}
	}
	return dedupeStrings(out)
}

// scopeWarnings applies the optional `[target] ` prefix convention in
// overrides.json: a warning tagged for one target is dropped from every other
// bundle, so a Mac kit never carries Windows-only advice.
func scopeWarnings(warnings []string, target string) []string {
	var out []string
	for _, w := range warnings {
		if !strings.HasPrefix(w, "[") {
			out = append(out, w)
			continue
		}
		end := strings.Index(w, "] ")
		if end < 0 {
			out = append(out, w)
			continue
		}
		scope := w[1:end]
		if scope != target {
			continue
		}
		out = append(out, strings.TrimSpace(w[end+2:]))
	}
	return out
}

func dedupeStrings(xs []string) []string {
	seen := map[string]bool{}
	var out []string
	for _, x := range xs {
		if x == "" || seen[x] {
			continue
		}
		seen[x] = true
		out = append(out, x)
	}
	return out
}
