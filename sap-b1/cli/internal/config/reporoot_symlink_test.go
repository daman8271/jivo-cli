package config

import (
	"os"
	"path/filepath"
	"testing"
)

// TestRepoRootDivergenceIgnoresSymlinkedPaths — regression test for a defect
// Proof found by running the real binary (2026-08-24).
//
// RepoRoot resolved the executable's path with filepath.EvalSymlinks but took
// os.Getwd() as-is. os.Getwd honours $PWD, which the shell fills with the
// LOGICAL path the operator typed. So standing in a directory reached through a
// symlink made exeRoot and cwdRoot two different strings for one directory, and
// the command printed:
//
//	note: this sapb1 lives in the checkout at /private/tmp/x but you are standing
//	in /tmp/x — using the binary's checkout ... One of the two is probably a stale copy
//
// Observed live (macOS, /tmp is a symlink to /private/tmp, both paths the SAME
// inode). The chosen root was still right, so nothing was deleted wrongly — the
// cost was that the fleet's stale-kit alarm, the one that catches an operator
// running a month-old Drive zip, cried wolf for a path that is not stale at all.
// An alarm that fires when nothing is wrong stops being read.
//
// Fixed by comparing the two roots with sameDirectory (strings, then resolved
// strings, then the inode) instead of string equality.
func TestRepoRootDivergenceIgnoresSymlinkedPaths(t *testing.T) {
	real := t.TempDir()
	root := filepath.Join(real, "checkout")
	for _, d := range []string{"harness", ".git", filepath.Join("sap-b1", "cli")} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building the checkout: %v", err)
		}
	}
	// A second name for the very same directory, exactly like /tmp -> /private/tmp.
	link := filepath.Join(real, "link")
	if err := os.Symlink(root, link); err != nil {
		t.Skipf("this filesystem will not make a symlink: %v", err)
	}

	exe := filepath.Join(root, "sap-b1", "cli", "sapb1")
	if err := os.WriteFile(exe, []byte("binary"), 0o755); err != nil {
		t.Fatalf("planting the binary: %v", err)
	}
	prev := executablePath
	executablePath = func() (string, error) { return exe, nil }
	t.Cleanup(func() { executablePath = prev })

	// Stand in the checkout via its symlinked name.
	t.Chdir(filepath.Join(link, "sap-b1", "cli"))

	got, note := RepoRoot()
	if note != "" {
		t.Errorf("the same directory reached by two names is not two checkouts; got note:\n%s", note)
	}
	wantResolved, err := filepath.EvalSymlinks(root)
	if err != nil {
		t.Fatalf("resolving the checkout: %v", err)
	}
	gotResolved, err := filepath.EvalSymlinks(got)
	if err != nil {
		t.Fatalf("resolving the chosen root %q: %v", got, err)
	}
	if gotResolved != wantResolved {
		t.Errorf("root = %q, want %q", gotResolved, wantResolved)
	}
}
