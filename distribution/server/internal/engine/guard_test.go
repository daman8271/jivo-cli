package engine

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"jivodist/internal/manifest"
)

func testRepoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	root, err := manifest.FindRepoRoot(wd)
	if err != nil {
		t.Fatal(err)
	}
	return root
}

// TestOutputDirsAreIgnored is the live guard: distribution/dist and
// distribution/staging must be untrackable in this checkout, because both hold
// zips full of production credentials.
func TestOutputDirsAreIgnored(t *testing.T) {
	root := testRepoRoot(t)
	if err := AssertIgnored(root, GuardedOutputDirs...); err != nil {
		t.Fatalf("output dirs are not gitignored: %v", err)
	}
}

// TestProbeFilesStayInvisibleToGit drops a file in each output directory and
// asserts git still reports a clean tree. This is the failure mode that would
// commit a credential zip.
func TestProbeFilesStayInvisibleToGit(t *testing.T) {
	root := testRepoRoot(t)
	if err := AssertIgnored(root, GuardedOutputDirs...); err != nil {
		t.Fatal(err)
	}

	before := gitStatus(t, root)
	for _, dir := range GuardedOutputDirs {
		probe := filepath.Join(root, dir, "guard-probe.zip")
		if err := os.WriteFile(probe, []byte("probe"), 0o600); err != nil {
			t.Fatal(err)
		}
		t.Cleanup(func() { os.Remove(probe) })
	}
	after := gitStatus(t, root)

	if before != after {
		t.Errorf("git noticed the probe files — an output directory is not ignored.\nbefore:\n%s\nafter:\n%s", before, after)
	}
	for _, dir := range GuardedOutputDirs {
		if strings.Contains(after, dir) {
			t.Errorf("git status mentions %s", dir)
		}
	}
}

// TestAssertIgnoredRejectsUnignoredDir proves the guard actually fails when the
// directory is committable — otherwise it is decoration.
func TestAssertIgnoredRejectsUnignoredDir(t *testing.T) {
	root := t.TempDir()
	run(t, root, "git", "init", "-q")

	err := AssertIgnored(root, "not-ignored-output")
	if !errors.Is(err, ErrNotIgnored) {
		t.Fatalf("want ErrNotIgnored, got %v", err)
	}
	if !strings.Contains(err.Error(), "not-ignored-output") {
		t.Errorf("error should name the offending path, got: %v", err)
	}

	if err := os.WriteFile(filepath.Join(root, ".gitignore"), []byte("not-ignored-output/\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := AssertIgnored(root, "not-ignored-output"); err != nil {
		t.Fatalf("should pass once ignored: %v", err)
	}
}

func gitStatus(t *testing.T, root string) string {
	t.Helper()
	out, err := exec.Command("git", "-C", root, "status", "--porcelain").Output()
	if err != nil {
		t.Fatal(err)
	}
	return string(out)
}

func run(t *testing.T, dir, name string, args ...string) {
	t.Helper()
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%s %v: %v\n%s", name, args, err, out)
	}
}
