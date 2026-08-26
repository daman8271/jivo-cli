package client

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestWriteLogFanOutIsAPolicyNotAVerb pins the fix for the trap that
// SaveDraftToDocument walked into: writeLogTargets used to decide "does this
// record go to the team's committed log?" by asking whether the method was
// DELETE.
//
// That was true of every caller until an irreversible POST existed. Had it
// stayed a verb test, `sapb1 add-draft` would have posted live documents whose
// only record sat in one machine's $SAPB1_WRITE_LOG — and nothing would have
// failed to say so. The decision is now a flag the CALLER sets, and this test
// exercises it with no HTTP method anywhere in sight.
func TestWriteLogFanOutIsAPolicyNotAVerb(t *testing.T) {
	t.Setenv("HOME", t.TempDir())
	_, sharedLog := fakeCheckout(t, "tester")
	configured := filepath.Join(t.TempDir(), "configured.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", configured)

	notShared, err := writeLogTargets(false)
	if err != nil {
		t.Fatalf("writeLogTargets(false): %v", err)
	}
	if len(notShared) != 1 || notShared[0] != configured {
		t.Errorf("an ordinary write goes to the configured log only, got %v", notShared)
	}

	shared, err := writeLogTargets(true)
	if err != nil {
		t.Fatalf("writeLogTargets(true): %v", err)
	}
	if len(shared) != 2 {
		t.Fatalf("a shared record must reach two files, got %v", shared)
	}
	if shared[0] != sharedLog {
		t.Errorf("the checkout's log must come first (it is the one that has to succeed), got %v", shared)
	}
	if shared[1] != configured {
		t.Errorf("the configured log must still be written, got %v", shared)
	}
}

// TestLogExtraSharedDefaultsToLocalOnly — a nil extra is a plain Create/Update,
// and the fan-out must never happen by accident.
func TestLogExtraSharedDefaultsToLocalOnly(t *testing.T) {
	var nilExtra *logExtra
	if nilExtra.shared() {
		t.Error("a nil logExtra must not fan out — that is a Create/Update")
	}
	if (&logExtra{}).shared() {
		t.Error("the zero logExtra must not fan out")
	}
	if !(&logExtra{Shared: true}).shared() {
		t.Error("logExtra{Shared:true} must fan out")
	}
}

// TestCheckWriteLogTargetsProvesTheSharedLogToo — the pre-flight has to cover
// every file the record will land in, or a shared write refuses only after
// publishing an intent line with no outcome into the team's history.
func TestCheckWriteLogTargetsProvesTheSharedLogToo(t *testing.T) {
	t.Setenv("HOME", t.TempDir())
	_, sharedLog := fakeCheckout(t, "tester")
	configured := filepath.Join(t.TempDir(), "configured.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", configured)

	// A directory where the shared log's file has to go: os.OpenFile cannot
	// create or append to it.
	if err := os.MkdirAll(sharedLog, 0o755); err != nil {
		t.Fatalf("blocking the shared log: %v", err)
	}

	if bad, err := checkWriteLogTargets(false); err != nil {
		t.Errorf("an ordinary write must not care about the shared log, got %s: %v", bad, err)
	}
	bad, err := checkWriteLogTargets(true)
	if err == nil {
		t.Fatal("a shared record must refuse when the checkout's log cannot be written")
	}
	if bad != sharedLog {
		t.Errorf("the refusal must name the file that failed, got %q want %q", bad, sharedLog)
	}
}

// TestUnrecordableSentenceBelongsToTheCaller — Delete owns its wording, and a
// caller that sets RequireIntent without a sentence still gets one that does not
// claim a DELETE happened.
func TestUnrecordableSentenceBelongsToTheCaller(t *testing.T) {
	withOwner := &logExtra{RequireIntent: true, Unrecordable: unrecordableDelete}
	msg := withOwner.unrecordable("Drafts(54990)", "/tmp/x.jsonl", os.ErrPermission).Error()
	if !strings.Contains(msg, "refusing to DELETE Drafts(54990)") {
		t.Errorf("Delete's own wording must survive, got: %s", msg)
	}

	fallback := (&logExtra{RequireIntent: true}).unrecordable("DraftsService_SaveDraftToDocument", "/tmp/x.jsonl", os.ErrPermission).Error()
	if strings.Contains(fallback, http.MethodDelete) {
		t.Errorf("the fallback must not borrow a delete's words for another write, got: %s", fallback)
	}
	if !strings.Contains(fallback, "DraftsService_SaveDraftToDocument") {
		t.Errorf("the fallback must still name what was refused, got: %s", fallback)
	}
}
