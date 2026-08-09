package manifest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// Targets are the bundle targets v1 supports. They match the manifest's `os`
// values for binaries.
var Targets = []string{"mac-arm64", "windows"}

// ValidTarget reports whether t is a supported bundle target.
func ValidTarget(t string) bool {
	for _, x := range Targets {
		if x == t {
			return true
		}
	}
	return false
}

// FileFact is disk truth about one manifest path on this machine. IsDir
// matters: jsap-cli/jsap is the Python package directory, not a launcher, so a
// bare existence check on it is a false positive.
type FileFact struct {
	Path    string    `json:"path"`
	Exists  bool      `json:"exists"`
	IsDir   bool      `json:"is_dir"`
	Size    int64     `json:"size_bytes"`
	ModTime time.Time `json:"mod_time"`
}

// Runnable reports whether the path is something that can actually be shipped
// and run — a regular file, not a directory.
func (f FileFact) Runnable() bool { return f.Exists && !f.IsDir }

// Scan stats every binary path in the manifest and returns the facts keyed by
// repo-relative path. Availability is decided from this, never from the
// manifest's `exists` flags — those were true on the machine that wrote them
// (e.g. portals/tankhapay/ exists only on Daman's Mac, not on the VPS).
func Scan(repoRoot string, m *Manifest) map[string]FileFact {
	facts := make(map[string]FileFact)
	for _, c := range m.Components {
		for _, t := range c.Tools {
			for _, b := range t.Binaries {
				if _, seen := facts[b.Path]; seen {
					continue
				}
				facts[b.Path] = StatRel(repoRoot, b.Path)
			}
		}
	}
	return facts
}

// StatRel is disk truth for one repo-relative path.
func StatRel(repoRoot, rel string) FileFact {
	f := FileFact{Path: rel}
	st, err := os.Stat(filepath.Join(repoRoot, rel))
	if err != nil {
		return f
	}
	f.Exists = true
	f.IsDir = st.IsDir()
	f.Size = st.Size()
	f.ModTime = st.ModTime()
	return f
}

// Overrides holds the hand-maintained warnings that the manifest cannot know:
// staleness, dead passwords, leaked credentials pending rotation. Committed at
// distribution/overrides.json.
type Overrides struct {
	// Global warnings apply to every bundle that bakes credentials.
	Global []string `json:"global"`
	// Components maps a component id to warnings shown whenever it is picked.
	Components map[string][]string `json:"components"`
	// Binaries maps a repo-relative binary path to warnings shown only when
	// that exact artefact would ship (i.e. only for its target).
	Binaries map[string][]string `json:"binaries"`
}

// LoadOverrides reads distribution/overrides.json. A missing file is not an
// error — it just means no extra warnings.
func LoadOverrides(repoRoot string) (*Overrides, error) {
	path := filepath.Join(repoRoot, "distribution", "overrides.json")
	raw, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return &Overrides{Components: map[string][]string{}, Binaries: map[string][]string{}}, nil
	}
	if err != nil {
		return nil, fmt.Errorf("overrides: %w", err)
	}
	var o Overrides
	if err := json.Unmarshal(raw, &o); err != nil {
		return nil, fmt.Errorf("overrides %s: %w", path, err)
	}
	if o.Components == nil {
		o.Components = map[string][]string{}
	}
	if o.Binaries == nil {
		o.Binaries = map[string][]string{}
	}
	return &o, nil
}
