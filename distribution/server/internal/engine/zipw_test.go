package engine

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// TestZipPreservesModesReadBackFromTheArchive is the one that matters. A naive
// zip.Create() writes mode-0 entries and every Mac binary extracts
// non-executable; the modes are therefore re-read from the FINISHED archive,
// never from the staging directory.
func TestZipPreservesModesReadBackFromTheArchive(t *testing.T) {
	stage := t.TempDir()
	seed := map[string]os.FileMode{
		"hana-sql/hana-sql":    0o755,
		"jsap-cli/jsap-cli":    0o755,
		"connections/hana.env": 0o600,
		".env":                 0o600,
		"README.txt":           0o644,
		"hana-sql/README.md":   0o644,
	}
	for rel, mode := range seed {
		p := filepath.Join(stage, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte("content of "+rel), mode); err != nil {
			t.Fatal(err)
		}
		if err := os.Chmod(p, mode); err != nil {
			t.Fatal(err)
		}
	}

	zipPath := filepath.Join(t.TempDir(), "bundle.zip")
	if err := WriteZip(stage, zipPath); err != nil {
		t.Fatal(err)
	}

	entries, err := ReadZipEntries(zipPath)
	if err != nil {
		t.Fatal(err)
	}
	got := map[string]os.FileMode{}
	var haveRoot bool
	for _, e := range entries {
		if e.Name == BundleRoot+"/" {
			haveRoot = true
		}
		if strings.HasSuffix(e.Name, "/") {
			continue
		}
		if !strings.HasPrefix(e.Name, BundleRoot+"/") {
			t.Errorf("%s is not under the %s/ root", e.Name, BundleRoot)
			continue
		}
		got[strings.TrimPrefix(e.Name, BundleRoot+"/")] = e.Mode.Perm()
	}
	if !haveRoot {
		t.Errorf("archive has no explicit %s/ directory entry", BundleRoot)
	}
	for rel, want := range seed {
		if got[rel] != want {
			t.Errorf("%s: mode in the archive = %04o, want %04o", rel, got[rel], want)
		}
	}
	for _, bin := range []string{"hana-sql/hana-sql", "jsap-cli/jsap-cli"} {
		if got[bin]&0o111 == 0 {
			t.Errorf("%s extracts non-executable — the bundle would be dead on arrival", bin)
		}
	}
	for _, env := range []string{"connections/hana.env", ".env"} {
		if got[env] != 0o600 {
			t.Errorf("%s must be 0600 in the archive, got %04o", env, got[env])
		}
	}
}

// TestZipHasNoMacJunk: archive/zip writes no __MACOSX sidecars, and .DS_Store
// is refused by the deny gate before it can be staged.
func TestZipHasNoMacJunk(t *testing.T) {
	stage := t.TempDir()
	for _, rel := range []string{"a/file.txt", "b/other.txt"} {
		p := filepath.Join(stage, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(p, []byte("x"), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	zipPath := filepath.Join(t.TempDir(), "bundle.zip")
	if err := WriteZip(stage, zipPath); err != nil {
		t.Fatal(err)
	}
	entries, err := ReadZipEntries(zipPath)
	if err != nil {
		t.Fatal(err)
	}
	for _, e := range entries {
		if strings.Contains(e.Name, "__MACOSX") || strings.HasSuffix(e.Name, ".DS_Store") {
			t.Errorf("junk entry %s", e.Name)
		}
		if strings.Contains(e.Name, `\`) {
			t.Errorf("%s uses a backslash — zip paths must use forward slashes", e.Name)
		}
	}
	if err := AssertZipClean(zipPath); err != nil {
		t.Error(err)
	}
}

// TestUnzipAgreesWithUsAboutExecBits cross-checks the external attributes with
// the system unzip, so the assertion does not rest on Go's own reader alone.
func TestUnzipAgreesWithUsAboutExecBits(t *testing.T) {
	unzip, err := exec.LookPath("unzip")
	if err != nil {
		t.Skip("unzip not installed")
	}
	stage := t.TempDir()
	bin := filepath.Join(stage, "hana-sql", "hana-sql")
	if err := os.MkdirAll(filepath.Dir(bin), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(bin, []byte("#!/bin/sh\necho hi\n"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(bin, 0o755); err != nil {
		t.Fatal(err)
	}
	zipPath := filepath.Join(t.TempDir(), "bundle.zip")
	if err := WriteZip(stage, zipPath); err != nil {
		t.Fatal(err)
	}

	out, err := exec.Command(unzip, "-Z", "-l", zipPath).CombinedOutput()
	if err != nil {
		t.Fatalf("unzip -Z: %v\n%s", err, out)
	}
	var line string
	for _, l := range strings.Split(string(out), "\n") {
		if strings.HasSuffix(strings.TrimSpace(l), "jivo-cli/hana-sql/hana-sql") {
			line = strings.TrimSpace(l)
		}
	}
	if line == "" {
		t.Fatalf("binary not listed by unzip -Z:\n%s", out)
	}
	if !strings.HasPrefix(line, "-rwxr-xr-x") {
		t.Errorf("unzip reports %q — want -rwxr-xr-x", strings.Fields(line)[0])
	}

	// And it really extracts executable.
	dest := t.TempDir()
	if out, err := exec.Command(unzip, "-q", zipPath, "-d", dest).CombinedOutput(); err != nil {
		t.Fatalf("extract: %v\n%s", err, out)
	}
	st, err := os.Stat(filepath.Join(dest, BundleRoot, "hana-sql", "hana-sql"))
	if err != nil {
		t.Fatal(err)
	}
	if st.Mode()&0o111 == 0 {
		t.Errorf("extracted mode %v is not executable", st.Mode())
	}
}

func TestWriteZipRefusesSymlinks(t *testing.T) {
	stage := t.TempDir()
	target := filepath.Join(stage, "real.txt")
	if err := os.WriteFile(target, []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(target, filepath.Join(stage, "link.txt")); err != nil {
		t.Skipf("symlinks unavailable: %v", err)
	}
	err := WriteZip(stage, filepath.Join(t.TempDir(), "b.zip"))
	if err == nil || !strings.Contains(err.Error(), "symlink") {
		t.Errorf("want a symlink refusal, got %v", err)
	}
}

func TestSHA256FileIsStable(t *testing.T) {
	p := filepath.Join(t.TempDir(), "f")
	if err := os.WriteFile(p, []byte("jivo"), 0o644); err != nil {
		t.Fatal(err)
	}
	got, err := SHA256File(p)
	if err != nil {
		t.Fatal(err)
	}
	// sha256("jivo"), checked against `printf 'jivo' | shasum -a 256`
	const want = "61edd224fab53f59f698480ebe6f5f35e6b4b6d114926c8330cd3831e55ec6a9"
	if got != want {
		t.Errorf("digest = %s, want %s", got, want)
	}
	again, err := SHA256File(p)
	if err != nil {
		t.Fatal(err)
	}
	if got != again {
		t.Error("digest is not stable across reads")
	}
}
