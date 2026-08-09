package engine

import (
	"fmt"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"strings"
)

// DenyList is the final gate. It runs twice: as a filter while staging, and
// again over the finished staging tree just before the zip is written. It is
// deliberately independent of the allowlist — if the ship-list resolver is ever
// "helpfully" replaced by a directory copy, this is what still keeps the SAP
// per-operator env, live portal tokens, admin cookies and 99 MB of scrape
// captures out of an operator's bundle.
var DenyList = []string{
	"env-vault/**",
	"**/token.json", // covers exim/.secrets/token.json and every portal's
	"lovepreet-veerji.env",
	"control-panel/recon/**",
	"**/captures/**",
	"**/.git/**",
	"**/__pycache__/**",
	"*.pyc",
	".DS_Store",
	"connections/fleet-access.env",
}

// Denied reports whether a bundle-relative path (below the jivo-cli/ root) is
// refused, and by which pattern.
//
// Matching is case-insensitive. APFS is case-insensitive by default, so a
// file renamed Token.json or .DS_STORE is the same file to the filesystem but
// would slip past a case-sensitive pattern — the deny list must not be
// disarmed by a capital letter.
func Denied(rel string) (string, bool) {
	rel = path.Clean(strings.ReplaceAll(rel, string(filepath.Separator), "/"))
	folded := strings.ToLower(rel)
	for _, p := range DenyList {
		if denyMatch(strings.ToLower(p), folded) {
			return p, true
		}
	}
	return "", false
}

// ValidZipPath refuses anything that would escape the bundle root when joined
// to the staging directory. Every path here comes from manifest.json, which is
// hand-edited, so this is the containment check that keeps a future typo from
// writing outside the staging tree.
func ValidZipPath(zipPath string) error {
	if zipPath == "" {
		return fmt.Errorf("empty bundle path")
	}
	if strings.HasPrefix(zipPath, "/") {
		return fmt.Errorf("bundle path %q is absolute", zipPath)
	}
	for _, seg := range strings.Split(zipPath, "/") {
		if seg == ".." {
			return fmt.Errorf("bundle path %q escapes the bundle root", zipPath)
		}
	}
	if !filepath.IsLocal(filepath.FromSlash(zipPath)) {
		return fmt.Errorf("bundle path %q is not contained in the bundle root", zipPath)
	}
	return nil
}

func denyMatch(pattern, rel string) bool {
	switch {
	case strings.HasSuffix(pattern, "/**"):
		prefix := strings.TrimSuffix(pattern, "/**")
		if seg := strings.TrimPrefix(prefix, "**/"); seg != prefix {
			// **/captures/** — the segment may appear at any depth.
			return hasSegment(rel, seg)
		}
		// env-vault/** — anchored at the bundle root.
		return rel == prefix || strings.HasPrefix(rel, prefix+"/")

	case strings.HasPrefix(pattern, "**/"):
		// **/token.json, **/.secrets/token.json — match the path tail.
		suffix := strings.TrimPrefix(pattern, "**/")
		return rel == suffix || strings.HasSuffix(rel, "/"+suffix)

	case strings.Contains(pattern, "/"):
		// connections/fleet-access.env — anchored, or the same tail anywhere.
		return rel == pattern || strings.HasSuffix(rel, "/"+pattern)

	default:
		// Bare names and globs match the basename at any depth.
		base := path.Base(rel)
		if strings.ContainsAny(pattern, "*?[") {
			ok, _ := path.Match(pattern, base)
			return ok
		}
		return base == pattern
	}
}

// hasSegment reports whether seg appears as a whole path segment of rel.
func hasSegment(rel, seg string) bool {
	for _, part := range strings.Split(rel, "/") {
		if part == seg {
			return true
		}
	}
	return false
}

// DeniedFinding is one file that reached the staging tree but must not ship.
type DeniedFinding struct {
	Path    string `json:"path"`
	Pattern string `json:"pattern"`
}

// ScanStaging walks a finished staging tree and reports every denied file.
// stageRoot is the directory that becomes the zip's jivo-cli/ folder.
func ScanStaging(stageRoot string) ([]DeniedFinding, error) {
	var found []DeniedFinding
	err := filepath.WalkDir(stageRoot, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, rerr := filepath.Rel(stageRoot, p)
		if rerr != nil {
			return rerr
		}
		if rel == "." {
			return nil
		}
		rel = filepath.ToSlash(rel)
		if pattern, bad := Denied(rel); bad {
			found = append(found, DeniedFinding{Path: rel, Pattern: pattern})
			if d.IsDir() {
				return fs.SkipDir
			}
		}
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("deny-list scan: %w", err)
	}
	return found, nil
}

// AssertClean fails the build if anything denied reached the staging tree.
func AssertClean(stageRoot string) error {
	found, err := ScanStaging(stageRoot)
	if err != nil {
		return err
	}
	if len(found) == 0 {
		return nil
	}
	var b strings.Builder
	b.WriteString("deny-list gate: refusing to zip, staging tree contains files that must never ship:")
	for _, f := range found {
		fmt.Fprintf(&b, "\n  %s  (matched %s)", f.Path, f.Pattern)
	}
	return fmt.Errorf("%s", b.String())
}

// ntfsIllegal are the characters NTFS refuses in a file name. A Windows bundle
// containing one of them fails or silently skips at extraction time — the known
// example is sap-b1/vault/services/Entities:.md.
const ntfsIllegal = `:*?"<>|`

// AssertWindowsSafe returns an error naming the first path that cannot be
// extracted on Windows. It asserts rather than dropping: a silently missing
// file is how a bundle arrives broken.
func AssertWindowsSafe(files []StagedFile) error {
	for _, f := range files {
		if i := strings.IndexAny(f.ZipPath, ntfsIllegal); i >= 0 {
			return fmt.Errorf("windows bundle: %q contains %q, which is illegal on NTFS — exclude or rename it",
				f.ZipPath, string(f.ZipPath[i]))
		}
	}
	return nil
}

// fileMode returns 0755 when the source file carries any execute bit, else the
// given default. Companion files are a mix (exim/exim is a shell wrapper,
// exim/scripts/eximapi.py is imported) so the source is the authority.
func fileMode(abs string, def os.FileMode) os.FileMode {
	st, err := os.Stat(abs)
	if err != nil {
		return def
	}
	if st.Mode()&0o111 != 0 {
		return 0o755
	}
	return def
}
