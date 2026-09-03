package cli

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// A drafts-only desk must not reach SAP at all — not to send, and not to read.
// The whole point is that the operator presses Add herself; a preview is one
// keystroke from a send, so the command stops before the first request.
func TestAddDraftRefusesOnDraftsOnlyDesk(t *testing.T) {
	var hits int
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hits++
		w.WriteHeader(http.StatusOK)
	}))
	t.Cleanup(srv.Close)
	u, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	pointCLIAtFake(t, u)
	t.Setenv("SAPB1_DRAFTS_ONLY", "1")

	for _, mode := range []string{"--yes", "--dry-run"} {
		t.Run(mode, func(t *testing.T) {
			_, _, err := execWrite(t, "", "add-draft", "55126", mode)
			var refused *errs.RefusedError
			if !errors.As(err, &refused) {
				t.Fatalf("expected *errs.RefusedError (exit 9), got %T: %v", err, err)
			}
			for _, want := range []string{
				"DRAFTS ONLY",
				"Nothing was sent",
				"Document Drafts",
				"TO THE AI READING THIS",
			} {
				if !strings.Contains(refused.Msg, want) {
					t.Errorf("refusal must say %q; got:\n%s", want, refused.Msg)
				}
			}
		})
	}
	if hits != 0 {
		t.Fatalf("a drafts-only desk must send NOTHING to SAP; the fake server saw %d request(s)", hits)
	}
}

// The lock is set in a shared, reviewed file — not by a marker somebody's next
// re-unzip removes. This is the path Mahak's box actually runs.
func TestDraftsOnlyComesFromDesksJSON(t *testing.T) {
	deskRoot(t, `{
	  "drafts_only": [
	    {"who": ["PC-AUDIT-05", "mahak"], "note": "Mahak - GRPO desk. Daman 2026-09-03"}
	  ]
	}`)

	t.Setenv("JIVO_DESK_AS", "PC-AUDIT-05")
	if d := config.DraftsOnlyDesk(); !d.On || !strings.Contains(d.Note, "Mahak") {
		t.Fatalf("PC-AUDIT-05 must be a drafts-only desk; got %+v", d)
	}
	// desks.json matches the way desk.py does: case-insensitive substring, so
	// the operator slug in harness/.operator catches the box too.
	t.Setenv("JIVO_DESK_AS", "Mahak-laptop")
	if d := config.DraftsOnlyDesk(); !d.On {
		t.Fatalf("the operator slug must match the same way desk.py matches it; got %+v", d)
	}
	t.Setenv("JIVO_DESK_AS", "HO-IT-PC1")
	if d := config.DraftsOnlyDesk(); d.On {
		t.Fatalf("a desk that is not listed must keep add-draft; got %+v", d)
	}
}

// A JSON typo must not stop twenty operators from submitting bills, so the
// read fails OPEN. The lock that matters is reviewed in git; a corrupt file on
// one box is a bug to fix, not a fleet-wide outage.
func TestDraftsOnlyFailsOpen(t *testing.T) {
	deskRoot(t, `{ this is not json`)
	t.Setenv("JIVO_DESK_AS", "PC-AUDIT-05")
	if d := config.DraftsOnlyDesk(); d.On {
		t.Fatalf("a broken desks.json must not lock anybody out; got %+v", d)
	}
}

// $SAPB1_DRAFTS_ONLY can arm the lock before the commit reaches a box; it can
// never disarm one desks.json set.
func TestDraftsOnlyEnvCannotUnlock(t *testing.T) {
	deskRoot(t, `{"drafts_only": [{"who": ["PC-AUDIT-05"], "note": "n"}]}`)
	t.Setenv("JIVO_DESK_AS", "PC-AUDIT-05")
	for _, v := range []string{"0", "false", "no", ""} {
		t.Setenv("SAPB1_DRAFTS_ONLY", v)
		if d := config.DraftsOnlyDesk(); !d.On {
			t.Fatalf("SAPB1_DRAFTS_ONLY=%q must not lift a desks.json lock; got %+v", v, d)
		}
	}
}

// deskRoot stands the test in a throwaway checkout carrying the given
// desks.json, so config.RepoRoot resolves to it and not to the developer's own
// jivo-cli.
func deskRoot(t *testing.T, desks string) {
	t.Helper()
	root := t.TempDir()
	for _, d := range []string{".git", "harness"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(root, "harness", "desks.json"), []byte(desks), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Chdir(root)
	t.Setenv("SAPB1_DRAFTS_ONLY", "")
}
