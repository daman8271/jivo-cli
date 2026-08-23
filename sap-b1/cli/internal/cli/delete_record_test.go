package cli

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"sapb1/internal/errs"
)

// Everything here is about one sentence being true: where a write is recorded,
// and who can read it afterwards. The delete guard reads its evidence from
// queries/*/sap-writes.jsonl inside the checkout, while an UNREGISTERED checkout
// records its own writes to ~/.sapb1-writes.jsonl — so a box that skipped
// `python3 harness/bin/setup.py` creates drafts it can then never delete in
// bulk. The code must say so, at the moment it can still be fixed, and it must
// not describe the file it is writing to as being somewhere it is not.

// unregisterOperatorLog makes config.WriteLogPath fall through to its HOME
// default, which is what a checkout with no harness/.operator really does.
func unregisterOperatorLog(t *testing.T) {
	t.Helper()
	t.Setenv("SAPB1_WRITE_LOG", "")
	t.Chdir(t.TempDir()) // nothing above cwd registers an operator
}

// TestUnregisteredCheckoutIsTaughtHowToBeEvidence — the sequence this comes
// from: `sapb1 draft ap-invoice … --yes` creates Drafts(54990) and records it in
// $HOME, and `sapb1 delete draft 54990` thirty seconds later refuses, because
// the guard reads queries/ and nothing else. Pointing only at
// --not-created-here there is a dead end: it takes one DocEntry and a human at
// the prompt, i.e. fifty prompts for the fifty-draft batch this command exists
// to clean up. The refusal has to name the command that fixes it for good.
func TestUnregisteredCheckoutIsTaughtHowToBeEvidence(t *testing.T) {
	f := newFakeDraftSAP(t)
	provenanceRepo(t) // a real-looking checkout: harness/ + .git/, no operator
	unregisterOperatorLog(t)
	f.putDraft(54990, nil)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")

	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{
		"no record that this CLI created it",
		"no registered operator",
		"harness/bin/setup.py",
		"--not-created-here",
	} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("the refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("nothing may be deleted, saw %d DELETE(s)", n)
	}
}

// TestRecordLinesDescribeWhereTheFileActuallyIS — the two lines above the
// "Type yes to DELETE" prompt. "Outside a checkout" is a fact about the path;
// "the team will not see it" is a fact about registration. Deciding the first
// from the second printed, on a real operator box running through
// acc/_playbook/sap: "each DELETE is appended to queries/USER36/sap-writes.jsonl,
// which is OUTSIDE any checkout — Run this from the JIVO checkout if it should
// reach them." A relative in-repo path, said to be nowhere near the repo, to an
// operator already standing in it, with an instruction they were already
// following.
func TestRecordLinesDescribeWhereTheFileActuallyIS(t *testing.T) {
	t.Run("inside the checkout, but nobody registered", func(t *testing.T) {
		root := t.TempDir()
		for _, d := range []string{"harness", ".git", "queries"} {
			if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
		}
		setProvenanceRoot(t, root)
		t.Chdir(t.TempDir())
		t.Setenv("HOME", t.TempDir())
		t.Setenv("SAPB1_WRITE_LOG", filepath.Join(root, "queries", "USER36", "sap-writes.jsonl"))

		var b bytes.Buffer
		writeRecordLines(&b, kindDraft)
		got := b.String()

		if strings.Contains(got, "OUTSIDE any checkout") {
			t.Errorf("the path is plainly inside the checkout; saying otherwise above a destroy prompt is worse than saying nothing:\n%s", got)
		}
		for _, want := range []string{"inside this checkout", "no operator is registered", "harness/bin/setup.py"} {
			if !strings.Contains(got, want) {
				t.Errorf("must contain %q, got:\n%s", want, got)
			}
		}
	})

	t.Run("genuinely outside any checkout", func(t *testing.T) {
		root := t.TempDir()
		for _, d := range []string{"harness", ".git", "queries"} {
			if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
		}
		setProvenanceRoot(t, root)
		t.Chdir(t.TempDir())
		t.Setenv("HOME", t.TempDir())
		t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "writes.jsonl"))

		var b bytes.Buffer
		writeRecordLines(&b, kindDraft)
		got := b.String()

		for _, want := range []string{"OUTSIDE any checkout", "the team will not see it", "harness/bin/setup.py"} {
			if !strings.Contains(got, want) {
				t.Errorf("must contain %q, got:\n%s", want, got)
			}
		}
	})
}

// TestDeleteHelpQualifiesTheSharedRecordPromise — `--help` is what an operator
// reads BEFORE a fifty-draft cleanup, and it stated flatly that the DELETE goes
// to queries/<operator>/sap-writes.jsonl "whatever $SAPB1_WRITE_LOG says". That
// property is implemented only when the checkout has a registered operator, so
// on a fresh box the headline guarantee was simply untrue.
func TestDeleteHelpQualifiesTheSharedRecordPromise(t *testing.T) {
	stdout, _, err := execWrite(t, "", "delete", "draft", "--help")
	if err != nil {
		t.Fatalf("--help: %v", err)
	}
	if !strings.Contains(stdout, "shared with the team") {
		t.Fatalf("the help should still describe the shared record, got:\n%s", stdout)
	}
	for _, want := range []string{"REGISTERED", "harness/bin/setup.py"} {
		if !strings.Contains(stdout, want) {
			t.Errorf("the promise must be qualified by %q, got:\n%s", want, stdout)
		}
	}
}

// TestHelpDescribesWhereADeleteIsRecorded — the two-file split is the reason a
// delete is allowed from a terminal at all, and both --help texts used to
// describe it wrongly: "a local write log (~/.sapb1-writes.jsonl, or
// $SAPB1_WRITE_LOG) — a delete also records a snapshot of what it destroyed".
// Neither half is true. The record ALSO goes to the checkout's committed log
// whatever that variable says, and the snapshot's contents go to a separate
// local file, with only its sha256 in the shared line — this repo is public.
func TestHelpDescribesWhereADeleteIsRecorded(t *testing.T) {
	for _, tc := range []struct {
		name string
		args []string
		want []string
	}{
		{"the root", []string{"--help"}, []string{
			"queries/<operator>/sap-writes.jsonl", "sha256", "$SAPB1_SNAPSHOT_LOG", "approval workflow",
		}},
		{"delete", []string{"delete", "--help"}, []string{
			"queries/<operator>/sap-writes.jsonl", "sha256", "on this machine only", "--in-approval",
		}},
		{"delete draft", []string{"delete", "draft", "--help"}, []string{
			"six guards", "--in-approval", "Two more checks have no flag",
		}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			stdout, _, err := execWrite(t, "", tc.args...)
			if err != nil {
				t.Fatalf("--help: %v", err)
			}
			for _, want := range tc.want {
				if !strings.Contains(stdout, want) {
					t.Errorf("help must contain %q, got:\n%s", want, stdout)
				}
			}
		})
	}

	// The one sentence that must never come back: the shared, committed log does
	// not carry what the draft held.
	stdout, _, err := execWrite(t, "", "delete", "--help")
	if err != nil {
		t.Fatalf("--help: %v", err)
	}
	if strings.Contains(stdout, "with a snapshot of what the draft held, so the shared history") {
		t.Errorf("the shared history carries the hash, not the contents:\n%s", stdout)
	}
}

// TestWritePreviewWarnsWhenTheRecordCannotVouch — the warning belongs at
// CREATION, because that is the last moment it is free. A draft made while the
// write log lands outside queries/ can never afterwards be shown to be this
// CLI's, and the operator finds that out during the cleanup instead.
func TestWritePreviewWarnsWhenTheRecordCannotVouch(t *testing.T) {
	t.Run("an unregistered checkout is warned", func(t *testing.T) {
		f := newFakeSAP(t)
		withTTY(t, false)
		root := t.TempDir()
		for _, d := range []string{"harness", ".git", "queries"} {
			if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
		}
		setProvenanceRoot(t, root)
		unregisterOperatorLog(t)

		_, stderr, err := execWrite(t, "", "draft", "order", "--yes", "--data", `{"CardCode":"C0001"}`)
		if err != nil {
			t.Fatalf("draft order: %v", err)
		}
		if f.hits != 1 {
			t.Fatalf("hits = %d, want 1", f.hits)
		}
		for _, want := range []string{"no registered operator", "harness/bin/setup.py", "sapb1 delete"} {
			if !strings.Contains(stderr, want) {
				t.Errorf("the preview must warn about %q, got:\n%s", want, stderr)
			}
		}
	})

	// post and patch are not drafts, and `delete` removes drafts and nothing
	// else — so on those two the note was an accurate sentence about a
	// consequence that cannot arise, printed above a prompt where the operator
	// has exactly one thing to check.
	t.Run("post and patch say nothing about it", func(t *testing.T) {
		for _, args := range [][]string{
			{"post", "BusinessPartners", "--yes", "--data", `{"CardCode":"C0001"}`},
			{"patch", "BusinessPartners('C0001')", "--yes", "--data", `{"Phone1":"1"}`},
		} {
			newFakeSAP(t)
			withTTY(t, false)
			root := t.TempDir()
			for _, d := range []string{"harness", ".git", "queries"} {
				if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
					t.Fatalf("mkdir: %v", err)
				}
			}
			setProvenanceRoot(t, root)
			unregisterOperatorLog(t) // the gap is real; it just isn't relevant here

			_, stderr, err := execWrite(t, "", args...)
			if err != nil {
				t.Fatalf("%v: %v", args[0], err)
			}
			if strings.Contains(stderr, "harness/bin/setup.py") {
				t.Errorf("%s creates nothing `delete` can remove, so the evidence-gap note does not apply:\n%s", args[0], stderr)
			}
		}
	})

	// The normal fleet setup says nothing extra. A note printed on every write
	// is a note nobody reads.
	t.Run("the normal setup is silent", func(t *testing.T) {
		newFakeSAP(t)
		withTTY(t, false)
		root := t.TempDir()
		for _, d := range []string{"harness", ".git"} {
			if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
				t.Fatalf("mkdir: %v", err)
			}
		}
		log := filepath.Join(root, "queries", "tester", "sap-writes.jsonl")
		if err := os.MkdirAll(filepath.Dir(log), 0o755); err != nil {
			t.Fatalf("mkdir: %v", err)
		}
		setProvenanceRoot(t, root)
		t.Setenv("SAPB1_WRITE_LOG", log)

		_, stderr, err := execWrite(t, "", "draft", "order", "--yes", "--data", `{"CardCode":"C0001"}`)
		if err != nil {
			t.Fatalf("draft order: %v", err)
		}
		if strings.Contains(stderr, "harness/bin/setup.py") {
			t.Errorf("nothing is wrong here; the preview must not say anything:\n%s", stderr)
		}
	})
}
