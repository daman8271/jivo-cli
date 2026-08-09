package manifest

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

// repoRoot locates the live checkout from the test's working directory.
func repoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	root, err := FindRepoRoot(wd)
	if err != nil {
		t.Fatal(err)
	}
	return root
}

// TestLoadRoundTrips is the loader's contract: nothing in manifest.json may be
// silently dropped. Re-marshalling the typed value must reproduce the file's
// JSON structure exactly (DisallowUnknownFields catches the other direction).
func TestLoadRoundTrips(t *testing.T) {
	root := repoRoot(t)
	path := filepath.Join(root, "distribution", "manifest.json")

	m, err := Load(root)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var original any
	if err := json.Unmarshal(raw, &original); err != nil {
		t.Fatal(err)
	}

	out, err := json.Marshal(m)
	if err != nil {
		t.Fatal(err)
	}
	var reserialized any
	if err := json.Unmarshal(out, &reserialized); err != nil {
		t.Fatal(err)
	}

	if !reflect.DeepEqual(original, reserialized) {
		t.Errorf("round-trip lost or changed data; diff the two JSON trees")
		diffJSON(t, "", original, reserialized)
	}
}

// diffJSON reports the first few structural differences by path, so a failure
// names the key that was dropped instead of dumping 96 KB.
func diffJSON(t *testing.T, path string, a, b any) {
	t.Helper()
	switch av := a.(type) {
	case map[string]any:
		bv, ok := b.(map[string]any)
		if !ok {
			t.Errorf("  %s: type changed", path)
			return
		}
		for k, v := range av {
			bw, ok := bv[k]
			if !ok {
				t.Errorf("  %s/%s: dropped by the loader", path, k)
				continue
			}
			diffJSON(t, path+"/"+k, v, bw)
		}
		for k := range bv {
			if _, ok := av[k]; !ok {
				t.Errorf("  %s/%s: invented by the loader", path, k)
			}
		}
	case []any:
		bv, ok := b.([]any)
		if !ok || len(av) != len(bv) {
			t.Errorf("  %s: list shape changed", path)
			return
		}
		for i := range av {
			diffJSON(t, path+"/"+itoa(i), av[i], bv[i])
		}
	default:
		if !reflect.DeepEqual(a, b) {
			t.Errorf("  %s: value changed", path)
		}
	}
}

func itoa(i int) string {
	if i == 0 {
		return "0"
	}
	var b []byte
	for i > 0 {
		b = append([]byte{byte('0' + i%10)}, b...)
		i /= 10
	}
	return string(b)
}

// TestLoadShape pins the facts the rest of the builder relies on.
func TestLoadShape(t *testing.T) {
	m, err := Load(repoRoot(t))
	if err != nil {
		t.Fatal(err)
	}
	if got := len(m.Components); got != 12 {
		t.Errorf("components = %d, want 12", got)
	}
	if len(m.Distributable()) != len(m.Components) {
		t.Errorf("every manifest component is expected to be distributable")
	}
	if len(m.Lessons.ReadmeMustSay) == 0 {
		t.Error("lessons.readme_must_say is empty — the README generator needs it")
	}
	if m.Lessons.NetworkRequirements == "" {
		t.Error("lessons.network_requirements is empty — the README needs the network matrix")
	}
	for _, c := range m.Components {
		if c.ID == "" {
			t.Errorf("component with empty id: %+v", c.UIName)
		}
		if len(c.Tools) == 0 {
			t.Errorf("%s: no tools", c.ID)
		}
		for _, tool := range c.Tools {
			if len(tool.Binaries) == 0 {
				t.Errorf("%s/%s: no binaries", c.ID, tool.Name)
			}
			if tool.OfflineCheck == "" {
				t.Errorf("%s/%s: no offline_check — the README quotes it", c.ID, tool.Name)
			}
		}
	}
	if _, ok := m.Component("hana-sql"); !ok {
		t.Error("hana-sql component missing")
	}
}

// TestScanAgreesWithManifestOnThisMachine: the manifest's `exists` flags were
// recorded on this Mac, so disk truth must still match here. Anywhere else
// (the VPS, an operator box) they legitimately diverge — which is exactly why
// availability is computed from Scan and not from the flags.
func TestScanAgreesWithManifestOnThisMachine(t *testing.T) {
	root := repoRoot(t)
	m, err := Load(root)
	if err != nil {
		t.Fatal(err)
	}
	facts := Scan(root, m)
	for _, c := range m.Components {
		for _, tool := range c.Tools {
			for _, b := range tool.Binaries {
				f := facts[b.Path]
				if f.Runnable() != b.Exists {
					t.Errorf("%s: manifest says exists=%v, disk says runnable=%v (exists=%v isDir=%v)",
						b.Path, b.Exists, f.Runnable(), f.Exists, f.IsDir)
				}
				if f.Runnable() && f.Size == 0 {
					t.Errorf("%s: exists but is zero bytes", b.Path)
				}
			}
		}
	}
}

func TestLoadOverrides(t *testing.T) {
	root := repoRoot(t)
	o, err := LoadOverrides(root)
	if err != nil {
		t.Fatal(err)
	}
	if len(o.Binaries["hana-sql/hana-sql.exe"]) == 0 {
		t.Error("expected the stale hana-sql.exe warning to be seeded in overrides.json")
	}
	if len(o.Components["postsql"]) == 0 {
		t.Error("expected the dead-password warning for postsql to be seeded in overrides.json")
	}
	if len(o.Global) == 0 {
		t.Error("expected the env-vault rotation warning in overrides.json global")
	}
}

// TestNoManifestBinaryPointsAtADirectory: manifest.json's `exists` flags were
// produced by a plain existence check, which said "true" for jsap-cli/jsap —
// the Python PACKAGE DIRECTORY, not a launcher. That silently dropped jsap from
// every Windows kit. The entry now names jsap-cli/jsap-cli (run as
// `python jsap-cli\jsap-cli`); this keeps the same mistake from coming back.
func TestNoManifestBinaryPointsAtADirectory(t *testing.T) {
	root := repoRoot(t)
	m, err := Load(root)
	if err != nil {
		t.Fatal(err)
	}
	facts := Scan(root, m)
	for _, c := range m.Components {
		for _, tool := range c.Tools {
			for _, b := range tool.Binaries {
				if facts[b.Path].IsDir {
					t.Errorf("%s/%s: %s binary %q is a directory, not a runnable file",
						c.ID, tool.Name, b.OS, b.Path)
				}
			}
		}
	}
}

// TestJsapWindowsEntryPointIsRunnable pins the corrected entry: a Windows kit
// must actually contain jsap.
func TestJsapWindowsEntryPointIsRunnable(t *testing.T) {
	root := repoRoot(t)
	m, err := Load(root)
	if err != nil {
		t.Fatal(err)
	}
	c, ok := m.Component("jsap-cli")
	if !ok {
		t.Fatal("jsap-cli missing from the manifest")
	}
	var winPath string
	for _, tool := range c.Tools {
		for _, b := range tool.Binaries {
			if b.OS == "windows" {
				winPath = b.Path
			}
		}
	}
	if winPath != "jsap-cli/jsap-cli" {
		t.Fatalf("jsap windows entry point = %q, want jsap-cli/jsap-cli", winPath)
	}
	if !StatRel(root, winPath).Runnable() {
		t.Errorf("%s is not a runnable file on this machine", winPath)
	}
}

func TestFindRepoRootFails(t *testing.T) {
	if _, err := FindRepoRoot(t.TempDir()); err == nil {
		t.Error("expected FindRepoRoot to fail outside a checkout")
	}
}

func TestValidTarget(t *testing.T) {
	for _, ok := range Targets {
		if !ValidTarget(ok) {
			t.Errorf("%s should be valid", ok)
		}
	}
	for _, bad := range []string{"", "linux", "mac-intel", "MAC-ARM64"} {
		if ValidTarget(bad) {
			t.Errorf("%q should not be a valid target", bad)
		}
	}
}
