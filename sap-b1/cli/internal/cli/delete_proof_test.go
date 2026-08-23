package cli

import (
	"errors"
	"strings"
	"testing"
	"time"

	"sapb1/internal/errs"
)

// The guards are sold to the operator as five INDEPENDENT statements, each with
// its own flag: "I know it isn't in the log", "I know it's old", "I know it has
// paper on it", "I know it's closed", "I know it's someone else's". If any one
// flag quietly lifted another guard, the recorded justification in the write log
// would be a lie — the operator asserted one fact and got a different guard
// switched off. So: put a draft that trips FOUR guards at once in front of the
// command and check that every flag covers exactly its own guard and no other.
//
// --not-created-here is the dangerous one to get wrong. It is the strongest
// override (it needs a human at the prompt), so it is the one a tired operator
// reaches for when anything refuses, and the one most likely to be written as a
// catch-all.
func TestGuardsDoNotShadowOneAnother(t *testing.T) {
	// Trips: age (3 days), attachment, closed, other-operator.
	created := time.Now().Add(-72 * time.Hour)
	setup := func(t *testing.T) *fakeDraftSAP {
		t.Helper()
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.putDraft(54990, map[string]interface{}{
			"AttachmentEntry": 170187,
			"DocumentStatus":  "bost_Close",
			"CreationDate":    created.Format("2006-01-02T15:04:05Z"),
		})
		seedCreation(t, operatorLog(root, "someone-else"), "Drafts", "TESTDB", 54990, "someone-else", created)
		return f
	}

	// Each flag alone must leave the OTHER three guards refusing.
	cases := []struct {
		name       string
		flags      []string
		stillNames []string // refusal must still mention these
	}{
		{"no flags at all", nil,
			[]string{"--older-than", "--with-attachment", "--closed", "--other-operator"}},
		{"only the age is asserted", []string{"--older-than", "96h"},
			[]string{"--with-attachment", "--closed", "--other-operator"}},
		{"only the attachment is asserted", []string{"--with-attachment"},
			[]string{"--older-than", "--closed", "--other-operator"}},
		{"only the closed status is asserted", []string{"--closed"},
			[]string{"--older-than", "--with-attachment", "--other-operator"}},
		{"only the operator is asserted", []string{"--other-operator"},
			[]string{"--older-than", "--with-attachment", "--closed"}},
		// Two assertions cover two guards and not a third and fourth. (The
		// provenance override cannot be table-driven: every row here appends
		// --yes, which validate() refuses in combination with it. It gets its own
		// test below — TestNotCreatedHereIsNotAMasterKey.)
		{"two overrides do not cover the other two guards", []string{"--other-operator", "--closed"},
			[]string{"--older-than", "--with-attachment"}},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := setup(t)
			args := append([]string{"delete", "draft", "54990", "--yes"}, tc.flags...)
			_, _, err := execWrite(t, "", args...)
			if err == nil {
				t.Fatalf("%v must not be enough to delete a draft that trips four guards", tc.flags)
			}
			var refused *errs.RefusedError
			if !errors.As(err, &refused) {
				t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
			}
			for _, want := range tc.stillNames {
				if !strings.Contains(refused.Msg, want) {
					t.Errorf("the refusal must still name %s:\n%s", want, refused.Msg)
				}
			}
			if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
				t.Errorf("a refused delete must send no DELETE, sent %d", n)
			}
		})
	}

	// All four asserted together: it goes, and the log records all four so an
	// auditor sees exactly which four statements the operator made.
	t.Run("all four asserted together", func(t *testing.T) {
		f := setup(t)
		if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes",
			"--older-than", "96h", "--with-attachment", "--closed", "--other-operator"); err != nil {
			t.Fatalf("with every guard asserted the delete should proceed: %v", err)
		}
		for _, want := range []string{"older-than=96h", "with-attachment", "closed", "other-operator"} {
			assertOverrideRecorded(t, f, want)
		}
	})
}

// TestNotCreatedHereIsNotAMasterKey — the header above says --not-created-here
// is the one a tired operator reaches for when anything refuses. The table
// cannot check it (every row there appends --yes, and the two are refused
// together by design), so it gets a run of its own with a human at the prompt.
//
// It asserts ONE thing — "no write log shows this CLI creating it" — so the
// attachment and the closed status must still stop the delete.
func TestNotCreatedHereIsNotAMasterKey(t *testing.T) {
	withTTY(t, true)
	f := newFakeDraftSAP(t)
	provenanceRepo(t) // a checkout with no creation line at all
	f.putDraft(54990, map[string]interface{}{
		"AttachmentEntry": 170187,
		"DocumentStatus":  "bost_Close",
	})

	_, _, err := execWrite(t, "yes\n", "delete", "draft", "54990", "--not-created-here")
	if err == nil {
		t.Fatal("--not-created-here must not carry a draft past the attachment and closed guards")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"--with-attachment", "--closed"} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("the refusal must still name %s:\n%s", want, refused.Msg)
		}
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("a refused delete must send no DELETE, sent %d", n)
	}
}

// TestNotCreatedHereDisownsTheLineAndEverythingReadOffIt — a written-down
// decision rather than an accident of control flow: when the override is used,
// checkProvenance returns before the age and other-operator checks, because both
// of those read the very log line the operator has just said does not describe
// this draft. Guards that read SAP's own answer (attachment, closed) are
// unaffected — see TestNotCreatedHereIsNotAMasterKey.
//
// The audit consequence is the part worth pinning: exactly one assertion was
// made, so exactly one override is recorded, and no origin is recorded as having
// authorised the delete.
func TestNotCreatedHereDisownsTheLineAndEverythingReadOffIt(t *testing.T) {
	withTTY(t, true)
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	// SAP says 2020; the line claims a delete-worthy three days ago, by somebody
	// else. The line is disowned, so its age and its author decide nothing.
	f.putDraft(54990, map[string]interface{}{"CreationDate": "2020-01-01T00:00:00Z"})
	seedCreation(t, operatorLog(root, "someone-else"), "Drafts", "TESTDB", 54990,
		"someone-else", time.Now().Add(-72*time.Hour))

	_, stderr, err := execWrite(t, "yes\n", "delete", "draft", "54990", "--not-created-here")
	if err != nil {
		t.Fatalf("a disowned line must not leave --older-than/--other-operator standing: %v\nstderr: %s", err, stderr)
	}

	lines := f.deleteLogLines(t)
	if len(lines) == 0 {
		t.Fatal("no DELETE was logged")
	}
	for _, line := range lines {
		raw, ok := line["overrides"].([]interface{})
		if !ok || len(raw) != 1 || raw[0] != "not-created-here" {
			t.Errorf("one assertion was made, so one override must be recorded, got %v", line["overrides"])
		}
		if origin, present := line["origin"]; present {
			t.Errorf("the disowned line must not be recorded as the authority for the delete, got %v", origin)
		}
	}
}

// TestOlderThanTakesAnyWindowHoweverAbsurd pins a real property of the age
// guard: --older-than is a magnitude, not a switch, but it has no upper bound.
// `--older-than 1000000h` (114 years) lifts the guard for anything the CLI has
// ever created, and a batch script can carry it forever.
//
// That is arguably fine — it is typed, and it is recorded — but it is only fine
// BECAUSE it is recorded verbatim. If the log ever normalised the value, or
// recorded a bare "older-than", the audit trail would show a careful 48h
// assertion and a blanket one identically. Pin the verbatim record.
func TestOlderThanTakesAnyWindowHoweverAbsurd(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester",
		time.Now().Add(-72*time.Hour))

	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes",
		"--older-than", "1000000h"); err != nil {
		t.Fatalf("an absurd window is still a window: %v", err)
	}
	// Recorded as typed, so "he waved the guard away entirely" is visible in the
	// shared history rather than looking like any other --older-than.
	assertOverrideRecorded(t, f, "older-than=1000000h")
}

// TestDryRunNeverDeletesWhateverElseIsAsked — --dry-run is the preview an
// operator is told to run first, so it has to be inert no matter what else is on
// the command line. Every combination here reaches the code that would send a
// DELETE if the flag were mis-wired.
func TestDryRunNeverDeletesWhateverElseIsAsked(t *testing.T) {
	cases := [][]string{
		{"--dry-run"},
		{"--dry-run", "--yes"},
		{"--dry-run", "--json"},
		{"--dry-run", "--closed"},
		{"--dry-run", "--with-attachment", "--other-operator", "--older-than", "96h"},
	}
	for _, flags := range cases {
		t.Run(strings.Join(flags, " "), func(t *testing.T) {
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)
			f.putDraft(54990, map[string]interface{}{"AttachmentEntry": 1, "DocumentStatus": "bost_Close"})
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

			args := append([]string{"delete", "draft", "54990"}, flags...)
			// A dry run may still REFUSE (a guard that is not covered is
			// reported in the preview, which is the point of a preview). What it
			// must never do is send. Both outcomes are checked the same way.
			_, _, err := execWrite(t, "", args...)
			if err != nil {
				var refused *errs.RefusedError
				if !errors.As(err, &refused) {
					t.Fatalf("a dry run may only fail as a refusal, got %T: %v", err, err)
				}
			}
			if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
				t.Errorf("a dry run sent %d DELETE(s): %v", n, f.seenMethods())
			}
			if lines := f.deleteLogLines(t); len(lines) != 0 {
				t.Errorf("a dry run must log no DELETE, got %d line(s)", len(lines))
			}
		})
	}
}

// TestBatchCapIsAnnouncedBeforeAnythingIsRead — the 50-DocEntry cap has to be a
// usage error found from the argument list alone. If it were discovered halfway
// through the pre-flight reads, an operator who pasted 200 numbers would have
// waited out 200 round trips to be told to split the list.
func TestBatchCapIsAnnouncedBeforeAnythingIsRead(t *testing.T) {
	f := newFakeDraftSAP(t)
	provenanceRepo(t)

	args := []string{"delete", "draft"}
	for i := 1; i <= 51; i++ {
		args = append(args, itoa(i))
	}
	_, _, err := execWrite(t, "", append(args, "--yes")...)
	requireUsageError(t, err, "50")
	if got := len(f.seenMethods()); got != 0 {
		t.Errorf("the cap must be checked before SAP is contacted, saw %d request(s): %v",
			got, f.seenMethods())
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
