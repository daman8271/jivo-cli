package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"sapb1/internal/errs"
)

// This file covers the gaps found by probing the built binary against a fake
// Service Layer: the guards that rest on a TIMESTAMP, and the cross-check that
// is supposed to stop a local file from vouching for a draft it knows nothing
// about. Everything here is about what happens when the clock in the write log
// is wrong, missing, or ahead of the server's.

// seedRawCreationLine writes a creation line with fields the caller controls,
// including the ability to LEAVE ONE OUT. seedCreation always stamps `time`,
// so it cannot express the line an older sapb1 (or a hand-edit, or a merge of
// two operators' logs) can leave behind.
func seedRawCreationLine(t *testing.T, path string, fields map[string]interface{}) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("creating log dir: %v", err)
	}
	b, err := json.Marshal(fields)
	if err != nil {
		t.Fatalf("marshaling seed line: %v", err)
	}
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
	if err != nil {
		t.Fatalf("opening seed log: %v", err)
	}
	defer f.Close()
	if _, err := f.Write(append(b, '\n')); err != nil {
		t.Fatalf("writing seed line: %v", err)
	}
}

// creationLineFields is a well-formed creation record; callers delete or override the
// one field the test is about.
func creationLineFields(companyDB, entitySet string, docEntry int64, user string) map[string]interface{} {
	return map[string]interface{}{
		"time":       time.Now().UTC().Format(time.RFC3339Nano),
		"event":      "outcome",
		"host":       "sap.example",
		"port":       50000,
		"company_db": companyDB,
		"user":       user,
		"method":     "POST",
		"path":       entitySet,
		"status":     201,
		"result_key": fmt.Sprintf("DocEntry=%d", docEntry),
	}
}

// --- the age guard's arithmetic ---------------------------------------------

// TestSuggestOlderThanNeverOverflows — the refusal hands the operator a flag
// value to paste. It is only useful if pasting it works, which means it must be
// positive and must actually cover the age it was computed from.
//
// The failing input is not exotic: a creation line with no `time` field decodes
// to the zero Time, and time.Since(zero) saturates near the maximum Duration.
// Rounding that up to the next whole day overflows int64 and comes back
// NEGATIVE, so the suggested command can never satisfy the guard it is meant to
// lift.
func TestSuggestOlderThanNeverOverflows(t *testing.T) {
	cases := []struct {
		name string
		age  time.Duration
	}{
		{"just past the threshold", 25 * time.Hour},
		{"three days", 72 * time.Hour},
		{"a year", 365 * 24 * time.Hour},
		{"a decade", 3650 * 24 * time.Hour},
		{"the zero timestamp", time.Since(time.Time{})},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := suggestOlderThan(tc.age)
			if got <= 0 {
				t.Fatalf("suggestion for age %v is %v — a non-positive duration is not a command anyone can run", tc.age, got)
			}
			if got < tc.age {
				t.Errorf("suggestion %v does not cover the age %v it was computed from", got, tc.age)
			}
			if _, err := time.ParseDuration(shortDuration(got)); err != nil {
				t.Errorf("suggestion renders as %q, which does not reparse: %v", shortDuration(got), err)
			}
		})
	}
}

// TestCreationLineWithNoTimestampRefuses — end to end, and the half that
// matters most: a creation line with no `time` must not authorise a delete. It
// does not: the timestamp guard refuses the line on its own account, because
// every age check rests on that field. This test pins that it fails SAFE.
//
// What it does NOT assert is the quality of the advice; see
// TestTimelessCreationLineSuggestsAUsableFlag for that.
func TestCreationLineWithNoTimestampRefuses(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)

	line := creationLineFields("TESTDB", "Drafts", 54990, "tester")
	delete(line, "time") // an older sapb1, a hand-edit, a torn merge
	seedRawCreationLine(t, operatorLog(root, "tester"), line)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")

	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("a timeless creation line must not authorise a delete; got %T: %v", err, err)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Fatalf("nothing may be deleted, saw %d DELETE(s)", n)
	}
	if lines := f.deleteLogLines(t); len(lines) != 0 {
		t.Errorf("a refused delete writes no DELETE log lines, got %d", len(lines))
	}
}

// TestTimelessCreationLineSuggestsAUsableFlag — a refusal that ends with a flag
// value to paste is only useful if pasting it works. The timeless line now gets
// a refusal that does not offer --older-than at all (an age nobody can compute
// is not an age you can assert past), which is the strongest form of "no dead
// end": there is nothing negative to paste.
func TestTimelessCreationLineSuggestsAUsableFlag(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)

	line := creationLineFields("TESTDB", "Drafts", 54990, "tester")
	delete(line, "time")
	seedRawCreationLine(t, operatorLog(root, "tester"), line)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected a refusal, got %T: %v", err, err)
	}
	if strings.Contains(refused.Msg, "--older-than -") {
		t.Fatalf("the refusal suggests a NEGATIVE --older-than, which cannot work:\n%s", refused.Msg)
	}
}

// --- the cross-check that a local file cannot forge --------------------------

// TestCreationDateCheckAnnouncesWhenItCannotRun — checkDraftStatus already says
// so out loud when an entity carries no DocumentStatus. The CreationDate
// cross-check is the guard that stops an unsigned local file vouching for a row
// it knows nothing about, and on an entity that returns no CreationDate it
// silently does not run. Silence is the problem: the operator is shown "created
// here: yes" with no hint that the only server-side corroboration was skipped.
func TestCreationDateCheckAnnouncesWhenItCannotRun(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)

	// A payment-draft-shaped row: no DocumentStatus, and no CreationDate.
	f.put("PaymentDrafts", 812, map[string]interface{}{
		"DocEntry": 812, "DocNum": 5501, "DocObjectCode": "oVendorPayments",
		"CardCode": "VENDA000939", "CardName": "TPAC PACKAGING INDIA PVT LTD II",
		"DocDate": "2026-08-14T00:00:00Z", "TransferSum": 2500000,
	})
	seedCreation(t, operatorLog(root, "tester"), "PaymentDrafts", "TESTDB", 812, "tester", time.Now())

	_, stderr, err := execWrite(t, "", "delete", "payment-draft", "812", "--yes")
	if err != nil {
		t.Fatalf("a well-formed delete must still work: %v", err)
	}
	if !strings.Contains(stderr, "CreationDate") {
		t.Errorf("the operator must be told the CreationDate cross-check did not run, got:\n%s", stderr)
	}
}

// TestFutureDatedLineCannotBeatTheAgeGuard — the age guard asks "how long ago
// did this CLI create it", and answers with time.Since(origin.Time). A line
// stamped in the future makes that negative, so the guard cannot fire. On
// Drafts the CreationDate cross-check catches it; on an entity with no
// CreationDate nothing does.
func TestFutureDatedLineCannotBeatTheAgeGuard(t *testing.T) {
	t.Run("Drafts — SAP's CreationDate catches it", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.putDraft(54990, map[string]interface{}{"CreationDate": "2026-08-14T00:00:00Z"})
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990,
			"tester", time.Now().AddDate(10, 0, 0))

		_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("a future-dated line must not vouch; got %T: %v", err, err)
		}
		if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
			t.Errorf("nothing may be deleted, saw %d DELETE(s)", n)
		}
	})

	// The entity that has no server-side date to contradict the line is exactly
	// where the timestamp guard has to stand on its own: on PaymentDrafts a
	// future-dated line used to satisfy every check at once and delete a
	// hand-keyed payment non-interactively, under a summary reading
	// "created here : yes".
	t.Run("an entity with no CreationDate — the timestamp guard catches it", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.put("PaymentDrafts", 812, map[string]interface{}{
			"DocEntry": 812, "DocNum": 5501, "CardCode": "VENDA000939",
			"DocDate": "2026-08-14T00:00:00Z", "TransferSum": 2500000,
		})
		seedCreation(t, operatorLog(root, "tester"), "PaymentDrafts", "TESTDB", 812,
			"tester", time.Now().AddDate(10, 0, 0))

		_, _, err := execWrite(t, "", "delete", "payment-draft", "812", "--yes")
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("a future-dated line must not vouch; got %T: %v", err, err)
		}
		for _, want := range []string{"in the future", "--not-created-here"} {
			if !strings.Contains(refused.Msg, want) {
				t.Errorf("the refusal must say %q, got:\n%s", want, refused.Msg)
			}
		}
		if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
			t.Errorf("nothing may be deleted, saw %d DELETE(s)", n)
		}
	})
}

// TestHonestClockSkewStillVouches — the other side of the timestamp guard. The
// line is stamped by whichever fleet box created the draft and read back on
// another, and those clocks are minutes apart (not all of them are on NTP). If a
// couple of minutes of drift refused a delete, the guard would fire on ordinary
// work and be routed around with --not-created-here, which is worse than not
// having it.
func TestHonestClockSkewStillVouches(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester",
		time.Now().Add(2*time.Minute))

	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes"); err != nil {
		t.Fatalf("a two-minute skew between fleet boxes must not refuse a delete: %v", err)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 1 {
		t.Errorf("want the delete to go through, got %v", f.seenMethods())
	}
}

// --- coverage the suite did not have ----------------------------------------

// TestProvenanceIsScopedToTheCompany — Oil's DocEntry 54990 and Mart's are
// different documents. A creation line from one company must not authorise a
// delete in another, or a --company typo silently destroys the wrong row.
func TestProvenanceIsScopedToTheCompany(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	// The line vouches for TESTDB; the command runs against OTHERDB.
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	_, _, err := execWrite(t, "", "--company", "OTHERDB", "delete", "draft", "54990", "--yes")

	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("a creation line from another company must not vouch; got %T: %v", err, err)
	}
	if !strings.Contains(refused.Msg, "OTHERDB") {
		t.Errorf("the refusal must name the company it looked in, got:\n%s", refused.Msg)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("nothing may be deleted, saw %d DELETE(s)", n)
	}
}

// TestDryRunBeatsYes — --yes means "don't ask me", not "send it anyway". An
// operator who pastes both must get the preview, not a delete.
func TestDryRunBeatsYes(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	stdout, _, err := execWrite(t, "", "delete", "draft", "54990", "--dry-run", "--yes")
	if err != nil {
		t.Fatalf("dry run with --yes must succeed: %v", err)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Fatalf("--dry-run with --yes still sent %d DELETE(s): %v", n, f.seenMethods())
	}
	if !strings.Contains(stdout, "DRY RUN") {
		t.Errorf("expected the dry-run report, got:\n%s", stdout)
	}
	if lines := f.deleteLogLines(t); len(lines) != 0 {
		t.Errorf("a dry run must write no DELETE log lines, got %d", len(lines))
	}
}

// TestBatchCapCountsUniqueDocEntries — the cap is about how many drafts die, so
// repeats must not consume it. Pins the order of dedupe and cap, which decides
// whether `... 50 50` is a refusal or a note.
func TestBatchCapCountsUniqueDocEntries(t *testing.T) {
	args := make([]string, 0, maxDeleteBatch+1)
	for i := 0; i < maxDeleteBatch; i++ {
		args = append(args, fmt.Sprintf("%d", 60000+i))
	}
	args = append(args, args[len(args)-1]) // one repeat: 51 args, 50 drafts

	entries, dupes, err := parseDocEntries(args)
	if err != nil {
		t.Fatalf("parsing: %v", err)
	}
	if len(entries) != maxDeleteBatch {
		t.Fatalf("got %d unique entries, want %d", len(entries), maxDeleteBatch)
	}
	if len(dupes) != 1 {
		t.Errorf("the repeat must be reported, got %v", dupes)
	}
	if err := (deleteFlags{yes: true}).validate(len(entries), false); err != nil {
		t.Errorf("50 unique DocEntries must be accepted even when 51 arguments were typed: %v", err)
	}
	if err := (deleteFlags{yes: true}).validate(maxDeleteBatch+1, false); err == nil {
		t.Error("51 unique DocEntries must be refused")
	}
}
