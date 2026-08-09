// Package engine builds JIVO distribution bundles: it resolves what ships,
// stages it outside the repo, bakes the right credentials in, writes the
// per-bundle README and produces the zip.
package engine

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// ErrNotIgnored is returned when an output directory that will hold live
// credentials is not covered by .gitignore. Callers surface it as HTTP 409.
var ErrNotIgnored = errors.New("output directory is not gitignored")

// AssertIgnored verifies that every given repo-relative path is ignored by
// git. Generated bundles carry live production credentials, so a build must
// never start while its output directory is committable.
//
// Directories are created first on purpose: `git check-ignore` cannot tell
// that a non-existent path is a directory, so a directory-only pattern such
// as `dist/` does not match until the directory exists on disk.
func AssertIgnored(repoRoot string, relPaths ...string) error {
	for _, rel := range relPaths {
		abs := filepath.Join(repoRoot, rel)
		if err := os.MkdirAll(abs, 0o755); err != nil {
			return fmt.Errorf("guard: cannot create %s: %w", rel, err)
		}
	}
	for _, rel := range relPaths {
		cmd := exec.Command("git", "check-ignore", "-q", "--", rel)
		cmd.Dir = repoRoot
		err := cmd.Run()
		if err == nil {
			continue // exit 0 == ignored
		}
		var ee *exec.ExitError
		if errors.As(err, &ee) && ee.ExitCode() == 1 {
			return fmt.Errorf("%w: %s — add it to distribution/.gitignore before building "+
				"(generated bundles contain live credentials)", ErrNotIgnored, rel)
		}
		return fmt.Errorf("guard: git check-ignore %s failed: %w", rel, err)
	}
	return nil
}

// GuardedOutputDirs are the directories a build writes into, all of which must
// stay untrackable.
var GuardedOutputDirs = []string{
	"distribution/dist",
	"distribution/staging",
}
