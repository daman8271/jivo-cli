package cli

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"

	"sapb1/internal/errs"
)

// --- the note about the configured write log --------------------------------
//
// provenanceLogPaths ends with one line of advice, and it is advice about
// EVIDENCE, printed immediately above a destroy prompt. Two things about it have
// to be true or it is worse than silence: it must only appear when the
// configured log genuinely is not evidence, and it must not blame an
// environment variable that nobody set.

// TestConfiguredLogNoteStaysQuietWhenTheLogIsAlreadyEvidence — the normal fleet
// setup is a checkout whose own queries/<operator>/sap-writes.jsonl is both the
// destination and one of the scanned evidence files. When that is so, the note
// must not fire; it flatly contradicts the "created here: yes — …
// queries/<operator>/sap-writes.jsonl:1" line printed a moment later off the
// same file.
//
// It used to compare by string rather than by identity, so the two spellings of
// one path never matched: RepoRoot symlink-resolves the exe's directory while
// os.Getwd honours the logical $PWD. On macOS /tmp is a symlink to /private/tmp,
// and the fleet's operator boxes reach their checkout through a synced Documents
// folder — the same shape config.sameDirectory was written to survive. The
// comparison is now made on the symlink-resolved paths.
func TestConfiguredLogNoteStaysQuietWhenTheLogIsAlreadyEvidence(t *testing.T) {
	root := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building fake repo: %v", err)
		}
	}
	logPath := operatorLog(root, "tester")
	writeLogLines(t, logPath, creationLine(t, nil))

	// The checkout reached by a second, symlinked spelling — exactly what
	// /tmp -> /private/tmp does on every Mac in this fleet.
	link := filepath.Join(t.TempDir(), "kit")
	if err := os.Symlink(root, link); err != nil {
		t.Skipf("cannot symlink on this filesystem: %v", err)
	}

	setProvenanceRoot(t, root)
	t.Setenv("SAPB1_WRITE_LOG", operatorLog(link, "tester"))
	t.Setenv("HOME", t.TempDir())

	paths, notes := provenanceLogPaths()

	var scanned bool
	for _, p := range paths {
		if filepath.Clean(p) == filepath.Clean(logPath) {
			scanned = true
		}
	}
	if !scanned {
		t.Fatalf("the operator's own committed log must be scanned as evidence, got %v", paths)
	}
	if joined := strings.Join(notes, "\n"); strings.Contains(joined, "RECORDS writes, not evidence") {
		t.Errorf("the log IS being read as evidence (%v), so the note must not fire; got:\n%s", paths, joined)
	}
}

// TestConfiguredLogNoteNamesWhereThePathActuallyCameFrom — config.WriteLogPath
// has three sources in order: $SAPB1_WRITE_LOG, the checkout's
// queries/<operator>/ file, and ~/.sapb1-writes.jsonl. The note used to name the
// first one whatever the answer came from, so an operator with the variable
// unset was told to go and look at an environment variable that does not exist —
// and, on a box outside any checkout, was pointed at their home file as though
// they had chosen it.
func TestConfiguredLogNoteNamesWhereThePathActuallyCameFrom(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("SAPB1_WRITE_LOG", "") // provably not set
	setProvenanceRoot(t, "")        // no checkout: WriteLogPath falls back to HOME

	_, notes := provenanceLogPaths()
	joined := strings.Join(notes, "\n")
	if joined == "" {
		t.Fatal("outside a checkout the operator should still be told where their log is")
	}
	if strings.Contains(joined, "$SAPB1_WRITE_LOG") {
		t.Errorf("the note blames $SAPB1_WRITE_LOG when it is unset — the path came from the home fallback:\n%s", joined)
	}
}

// --- which log line gets to vouch -------------------------------------------

// TestProvenanceIndexPrefersTheEarliestLineAcrossFiles — buildProvenanceIndex
// used to take the FIRST line it saw for a DocEntry and document that as "first
// match wins, so the log stays chronological". That holds inside one file, which
// is append-only. Across files it did not: the paths come from filepath.Glob, so
// the winner was whichever operator's directory sorts first alphabetically.
//
// It matters because the loser is not merely unrecorded. The origin that wins
// decides the age guard, the other-operator guard, and the file:line written
// into the shared audit trail as the authority for the delete. A stale line
// under queries/avtar/ outranks the true line under queries/tester/ for no
// reason but the letter it starts with — and this fleet has the exact
// precondition on file: DocEntry numbers come round again after a company
// restore, and one person's writes already land under two logins (Param's box
// runs as USER01).
//
// The rule is EARLIEST-in-time, not latest, and that is the security half: a
// planted line can always be stamped "now", so letting the latest win would let
// anyone with write access to a queries/ file outrank a real creation record.
// Backdating one instead runs into the two checks that already exist — SAP's own
// CreationDate on the row, and the age guard.
func TestProvenanceIndexPrefersTheEarliestLineAcrossFiles(t *testing.T) {
	root := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building fake repo: %v", err)
		}
	}
	setProvenanceRoot(t, root)

	created := time.Now().Add(-2 * time.Hour) // the POST that made this draft
	later := time.Now().Add(-1 * time.Hour)   // a line an hour afterwards

	// "avtar" sorts before "tester", so glob order hands avtar's line over first;
	// it is the LATER of the two and must not win on that alone.
	seedCreation(t, operatorLog(root, "avtar"), "Drafts", "TESTDB", 54990, "avtar", later)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", created)

	paths, _ := provenanceLogPaths()
	idx, _, _ := buildProvenanceIndex(paths, "Drafts", "TESTDB")

	got, ok := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]
	if !ok {
		t.Fatal("two logs vouch for this draft; the index found neither")
	}
	if got.Time.After(created.Add(time.Minute)) {
		t.Errorf("the index kept the later line from %s (%s); the earliest-in-time line is the one that describes the creation",
			got.User, got.Time.Format(time.RFC3339))
	}
	if got.User != "tester" {
		t.Errorf("origin user is %q — the chronologically first creation was %q; file order must not decide who is recorded as having created it",
			got.User, "tester")
	}

	// The same two lines in the opposite file order must give the same answer.
	// That is the whole point: the index cannot depend on which directory the
	// glob reached first.
	other := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(other, d), 0o755); err != nil {
			t.Fatalf("building fake repo: %v", err)
		}
	}
	setProvenanceRoot(t, other)
	seedCreation(t, operatorLog(other, "avtar"), "Drafts", "TESTDB", 54990, "avtar", created)
	seedCreation(t, operatorLog(other, "tester"), "Drafts", "TESTDB", 54990, "tester", later)

	paths, _ = provenanceLogPaths()
	idx, _, _ = buildProvenanceIndex(paths, "Drafts", "TESTDB")
	got = idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]
	if got.User != "avtar" {
		t.Errorf("origin user is %q — with the earlier line under queries/avtar/ it is avtar's that describes the creation", got.User)
	}
}

// TestProvenanceIndexKeepsARealLineOverATimestampless One — a torn append or a
// hand-edit leaves a line with no time at all. It is not "the earliest": it is
// no time, and it must not be able to push the real creation record out of the
// index, because every age check rests on that timestamp. On its own it still
// gets indexed, so the log-timestamp guard refuses by name rather than the
// delete falling through to "no record that this CLI created it".
func TestProvenanceIndexKeepsARealLineOverATimestamplessOne(t *testing.T) {
	root := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building fake repo: %v", err)
		}
	}
	setProvenanceRoot(t, root)

	created := time.Now().Add(-2 * time.Hour)
	seedCreation(t, operatorLog(root, "avtar"), "Drafts", "TESTDB", 54990, "avtar", time.Time{})
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", created)

	paths, _ := provenanceLogPaths()
	idx, _, _ := buildProvenanceIndex(paths, "Drafts", "TESTDB")

	got := idx[originKey{EntitySet: "Drafts", CompanyDB: "TESTDB", DocEntry: 54990}]
	if got.User != "tester" || got.Time.IsZero() {
		t.Errorf("a line with no timestamp must not displace a real one, got user %q at %v", got.User, got.Time)
	}
}

// --- what a pipe closing early costs ----------------------------------------

// brokenPipe is a stdout that accepts n writes and then fails the way a closed
// pipe does. It is what `| head -1` looks like from inside the process.
type brokenPipe struct {
	ok      int // writes to let through
	written int
}

func (b *brokenPipe) Write(p []byte) (int, error) {
	if b.written >= b.ok {
		return 0, syscall.EPIPE
	}
	b.written++
	return len(p), nil
}

// TestDeleteBatchStopsWhenStdoutCloses — `sapb1 delete draft … --json | head -1`
// and `… | grep -q` are ordinary shell, and both close the pipe after the first
// record. The process used to take SIGPIPE on its next write, which happens
// AFTER the following draft has already been deleted: the run destroyed more
// than it printed and exited 141, with no tally of either.
//
// Verified against the built binary before the fix: `… 54990 54991 54992 --yes
// --json | head -1` sent 2 DELETEs, printed 1 record and exited 141
// (128+SIGPIPE). The audit trail survived — both DELETEs had their intent and
// outcome lines and both snapshots were on disk — so this was a reporting
// hazard, not a lost record. It is still the wrong failure for a destructive
// command: the caller's stdout is its receipt.
//
// Now the write comes back as an error (runDeleteDrafts ignores SIGPIPE), the
// batch stops there, and what was and was not deleted is reported on stderr. The
// bound is one DocEntry past the last record the caller read — an outcome cannot
// be printed before it is known.
func TestDeleteBatchStopsWhenStdoutCloses(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	for _, n := range []int64{54990, 54991, 54992} {
		f.putDraft(n, nil)
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
	}

	pipe := &brokenPipe{ok: 1} // `head -1`
	_, err := execWriteTo(t, "", pipe, "--json", "delete", "draft", "54990", "54991", "54992", "--yes")
	if err == nil {
		t.Fatal("a delete batch that cannot print its own records must not report success")
	}

	var verify *errs.WriteVerifyError
	if !errors.As(err, &verify) {
		t.Fatalf("want *errs.WriteVerifyError (exit %d), got %T: %v", ExitVerifyFailed, err, err)
	}
	if code := ExitCodeFor(err); code != ExitVerifyFailed {
		t.Errorf("exit code = %d, want %d — never 141, and never a code that reads as \"nothing happened\"", code, ExitVerifyFailed)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 2 {
		t.Errorf("the batch must stop one DocEntry past the last record it could print, got %d DELETE(s): %v", n, f.seenMethods())
	}
	// The tally is the whole point: it says what happened to all three.
	tally := err.Error()
	for _, want := range []string{
		"could not be written to stdout", "cannot double-delete",
		"deleted (2)", "54990, 54991", "not attempted (1)", "54992",
	} {
		if !strings.Contains(tally, want) {
			t.Errorf("the report must contain %q, got:\n%s", want, tally)
		}
	}
	// And the record of both deletes is on disk, whatever the caller saw.
	if n := len(f.deleteLogLines(t)); n != 4 {
		t.Errorf("both DELETEs must have their intent and outcome lines, got %d", n)
	}
}
