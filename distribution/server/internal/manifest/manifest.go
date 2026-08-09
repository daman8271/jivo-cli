// Package manifest loads distribution/manifest.json (the 14-agent inventory of
// every JIVO CLI: its binaries, credentials, companion files and gotchas) into
// typed Go values, and checks what of it actually exists on this machine.
package manifest

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

// Manifest is the whole of distribution/manifest.json. Round-trips byte-for-
// byte-equivalent JSON: every key in the file has a home here, and `envmap`
// stays raw because only humans and the docs read it.
type Manifest struct {
	Components []Component     `json:"components"`
	Envmap     json.RawMessage `json:"envmap"`
	Lessons    Lessons         `json:"lessons"`
}

// Component is one JIVO subsystem — the unit an operator ticks in the UI.
type Component struct {
	ID            string   `json:"component"`
	Distributable bool     `json:"distributable"`
	UIName        string   `json:"ui_name"`
	UIDescription string   `json:"ui_description"`
	Tools         []Tool   `json:"tools"`
	DocsToShip    []string `json:"docs_to_ship"`
	ZipGotchas    string   `json:"zip_gotchas"`
	Notes         string   `json:"notes"`

	// Present on only some components; pointers so an empty string that was
	// written in the file survives a round-trip and an absent key stays absent.
	CompanionFilesNote *string `json:"companion_files_note,omitempty"`
	WhyNot             *string `json:"why_not,omitempty"`
}

// Tool is one runnable thing inside a component (a CLI, or its MCP server).
type Tool struct {
	Name           string     `json:"name"`
	Binaries       []Binary   `json:"binaries"`
	Env            []EnvEntry `json:"env"`
	CompanionFiles []string   `json:"companion_files"`
	OfflineCheck   string     `json:"offline_check"`
}

// Binary is one prebuilt artefact for one target OS.
type Binary struct {
	OS       string `json:"os"`
	Path     string `json:"path"`
	Exists   bool   `json:"exists"`
	Format   string `json:"format"`
	BuildCmd string `json:"build_cmd"`
}

// EnvEntry documents where a tool reads its credentials from. Paths starting
// with ~ or containing " (" are outside the repo and are never staged from here.
type EnvEntry struct {
	Path       string `json:"path"`
	Required   bool   `json:"required"`
	Secrets    bool   `json:"secrets"`
	Resolution string `json:"resolution"`
}

// Lessons is the hard-won field knowledge; ReadmeMustSay and
// NetworkRequirements are consumed verbatim by the README generator.
type Lessons struct {
	FullKitFiles        []string `json:"full_kit_files"`
	WindowsNotes        string   `json:"windows_notes"`
	MacNotes            string   `json:"mac_notes"`
	NetworkRequirements string   `json:"network_requirements"`
	ReadmeMustSay       []string `json:"readme_must_say"`
	Pitfalls            []string `json:"pitfalls"`
}

// Load reads and parses distribution/manifest.json under repoRoot.
func Load(repoRoot string) (*Manifest, error) {
	return LoadFile(filepath.Join(repoRoot, "distribution", "manifest.json"))
}

// LoadFile reads and parses a manifest from an explicit path.
func LoadFile(path string) (*Manifest, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("manifest: %w", err)
	}
	var m Manifest
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&m); err != nil {
		return nil, fmt.Errorf("manifest %s: %w", path, err)
	}
	if len(m.Components) == 0 {
		return nil, fmt.Errorf("manifest %s: no components", path)
	}
	return &m, nil
}

// Component returns the component with the given id.
func (m *Manifest) Component(id string) (*Component, bool) {
	for i := range m.Components {
		if m.Components[i].ID == id {
			return &m.Components[i], true
		}
	}
	return nil, false
}

// Distributable lists the components an operator may pick, in manifest order.
func (m *Manifest) Distributable() []*Component {
	var out []*Component
	for i := range m.Components {
		if m.Components[i].Distributable {
			out = append(out, &m.Components[i])
		}
	}
	return out
}

// ErrRepoRootNotFound means we are not inside a jivo-cli checkout.
var ErrRepoRootNotFound = errors.New("repo root not found: no ancestor directory contains distribution/manifest.json")

// FindRepoRoot walks up from start until it finds a directory holding
// distribution/manifest.json.
func FindRepoRoot(start string) (string, error) {
	dir, err := filepath.Abs(start)
	if err != nil {
		return "", err
	}
	for {
		if st, err := os.Stat(filepath.Join(dir, "distribution", "manifest.json")); err == nil && !st.IsDir() {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", ErrRepoRootNotFound
		}
		dir = parent
	}
}
