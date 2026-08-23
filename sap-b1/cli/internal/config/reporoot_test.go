package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// fakeCheckout builds a directory that looks like a JIVO checkout (both markers)
// and returns it.
func fakeCheckout(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	for _, d := range []string{"harness", ".git"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
	}
	return root
}

func stubExecutable(t *testing.T, path string) {
	t.Helper()
	prev := executablePath
	executablePath = func() (string, error) { return path, nil }
	t.Cleanup(func() { executablePath = prev })
}

// TestRepoRootNeedsBothMarkers — a scratch directory, or a month-old Drive zip
// with no .git, must NOT qualify as a trust root. A kit like that then gets "no
// write log found" and has to use the recorded override, which is the honest
// outcome: its history is stale and incomplete.
func TestRepoRootNeedsBothMarkers(t *testing.T) {
	cases := []struct {
		name    string
		dirs    []string
		wantHit bool
	}{
		{"a real checkout", []string{"harness", ".git"}, true},
		{"a Drive zip (no .git)", []string{"harness"}, false},
		{"some other git repo", []string{".git"}, false},
		{"a scratch directory", nil, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			root := t.TempDir()
			for _, d := range tc.dirs {
				if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
					t.Fatalf("mkdir: %v", err)
				}
			}
			deep := filepath.Join(root, "sap-b1", "cli")
			if err := os.MkdirAll(deep, 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
			got := walkUpToRepoRoot(deep)
			if tc.wantHit && got != root {
				t.Errorf("walkUpToRepoRoot = %q, want %q", got, root)
			}
			if !tc.wantHit && got != "" {
				t.Errorf("walkUpToRepoRoot = %q, want \"\"", got)
			}
		})
	}
}

// TestRepoRootPrefersTheBinarysCheckout — when the exe and the working directory
// disagree, one of the two copies is stale. The binary's wins, and the note says
// both out loud.
func TestRepoRootPrefersTheBinarysCheckout(t *testing.T) {
	exeRoot := fakeCheckout(t)
	cwdRoot := fakeCheckout(t)

	stubExecutable(t, filepath.Join(exeRoot, "sap-b1", "cli", "sapb1"))
	t.Chdir(cwdRoot)

	root, note := RepoRoot()
	if root != exeRoot {
		t.Errorf("RepoRoot = %q, want the binary's checkout %q", root, exeRoot)
	}
	if !strings.Contains(note, exeRoot) || !strings.Contains(note, cwdRoot) {
		t.Errorf("the note must name both checkouts, got: %s", note)
	}
}

// TestOperatorWriteLogFollowsRepoRoot — there must be exactly one answer to
// "which checkout am I in". operatorWriteLog used to walk up on its own, cwd
// first, while RepoRoot walks exe first: with the binary in one copy and the
// operator standing in another — the stale-kit shape this fleet keeps hitting —
// the delete guard read its evidence from one checkout and the write log that
// vouches for it was written into the other.
func TestOperatorWriteLogFollowsRepoRoot(t *testing.T) {
	exeRoot := fakeCheckout(t)
	cwdRoot := fakeCheckout(t)
	for root, slug := range map[string]string{exeRoot: "exe-op", cwdRoot: "cwd-op"} {
		if err := os.WriteFile(filepath.Join(root, "harness", ".operator"), []byte(`{"slug":"`+slug+`"}`), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	stubExecutable(t, filepath.Join(exeRoot, "sap-b1", "cli", "sapb1"))
	t.Chdir(cwdRoot)
	t.Setenv("SAPB1_WRITE_LOG", "")

	root, _ := RepoRoot()
	got, err := WriteLogPath()
	if err != nil {
		t.Fatalf("WriteLogPath: %v", err)
	}
	if want := filepath.Join(root, "queries", "exe-op", "sap-writes.jsonl"); got != want {
		t.Errorf("WriteLogPath = %q, want the log in RepoRoot's checkout %q", got, want)
	}
	if shared := SharedWriteLogPath(); shared != got {
		t.Errorf("the shared log %q and the configured default %q must be the same file here", shared, got)
	}
}

// TestRepoRootIsNotEnvSelectable — $SAPB1_WRITE_LOG must not be able to choose
// the evidence corpus a delete is authorised against. It stays a scanned log
// path; picking the root is a different power.
func TestRepoRootIsNotEnvSelectable(t *testing.T) {
	planted := fakeCheckout(t)
	if err := os.MkdirAll(filepath.Join(planted, "queries", "tester"), 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(planted, "queries", "tester", "sap-writes.jsonl"))

	stubExecutable(t, filepath.Join(t.TempDir(), "sapb1"))
	t.Chdir(t.TempDir())

	if root, _ := RepoRoot(); root == planted {
		t.Errorf("RepoRoot followed $SAPB1_WRITE_LOG to %q — one env var must not choose the trust root", root)
	}
}

// TestRepoRootFallsBackToTheWorkingDirectory — the common case is a binary run
// from anywhere against a checkout the operator is standing in.
func TestRepoRootFallsBackToTheWorkingDirectory(t *testing.T) {
	cwdRoot := fakeCheckout(t)
	stubExecutable(t, filepath.Join(t.TempDir(), "sapb1"))
	t.Chdir(cwdRoot)

	root, note := RepoRoot()
	if root != cwdRoot {
		t.Errorf("RepoRoot = %q, want %q", root, cwdRoot)
	}
	if note != "" {
		t.Errorf("no divergence, so no note: %q", note)
	}
}
