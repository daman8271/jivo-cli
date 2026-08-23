package cli

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"sapb1/internal/errs"
)

// This file holds the cases Proof found by probing the built binary against a
// stand-in Service Layer, which the main suite did not cover. Each one is
// characterisation: it pins what the code does TODAY so that a deliberate change
// is visible in a diff, and each names the operator-visible consequence in its
// comment.

// --- what the operator is shown before they destroy something ---------------

// TestPaymentDraftSummaryShowsEveryFundingLeg — a payment is funded by any of
// five legs (draftpayment.go, which creates these, checks all five:
// TransferSum, CashSum, BillOfExchangeAmount, PaymentChecks,
// PaymentCreditCards). Every one of them has to reach the operator's eyes,
// because the sanity check a human actually performs before typing "yes" is
// "does this draft look empty?" — and for a 25-lakh cheque payment the honest
// answer is no.
//
// The table is shaped so that narrowing kindPaymentDraft again fails loudly
// here rather than quietly reintroducing a preview full of zeroes.
func TestPaymentDraftSummaryShowsEveryFundingLeg(t *testing.T) {
	cases := []struct {
		name    string
		funding map[string]interface{}
		want    []string // must all appear in what the operator is shown
	}{
		{
			name:    "transfer-funded draft",
			funding: map[string]interface{}{"TransferSum": 2500000.0, "CashSum": 0.0},
			want:    []string{"2500000"},
		},
		{
			name:    "cash-funded draft",
			funding: map[string]interface{}{"CashSum": 1750000.0, "TransferSum": 0.0},
			want:    []string{"1750000"},
		},
		{
			// The one that mattered: 25 lakh by cheque, previously shown as 0.0.
			name: "cheque-funded draft",
			funding: map[string]interface{}{
				"CashSum": 0.0, "TransferSum": 0.0,
				"PaymentChecks": []interface{}{
					map[string]interface{}{"CheckNumber": "000123", "BankCode": "HDFC", "CheckSum": 2500000.0},
				},
			},
			want: []string{"ChequeSum", "2500000", "1 cheque"},
		},
		{
			name: "two cheques are totalled and counted",
			funding: map[string]interface{}{
				"CashSum": 0.0, "TransferSum": 0.0,
				"PaymentChecks": []interface{}{
					map[string]interface{}{"CheckNumber": "000123", "CheckSum": 2500000.0},
					map[string]interface{}{"CheckNumber": "000124", "CheckSum": 500000.0},
				},
			},
			want: []string{"3000000", "2 cheques"},
		},
		{
			name:    "bill-of-exchange draft",
			funding: map[string]interface{}{"CashSum": 0.0, "TransferSum": 0.0, "BillOfExchangeAmount": 990000.0},
			want:    []string{"990000"},
		},
		{
			name: "credit-card draft",
			funding: map[string]interface{}{
				"CashSum": 0.0, "TransferSum": 0.0,
				"PaymentCreditCards": []interface{}{
					map[string]interface{}{"CreditCard": 3, "CreditSum": 120000.0},
				},
			},
			want: []string{"CreditCardSum", "120000"},
		},
		{
			// If SAP ever renames the amount on a leg, the operator must be told
			// there IS money here that could not be read — never shown a zero.
			name: "a leg whose amount cannot be read says so",
			funding: map[string]interface{}{
				"CashSum": 0.0, "TransferSum": 0.0,
				"PaymentChecks": []interface{}{
					map[string]interface{}{"CheckNumber": "000123", "SomeNewSumField": 2500000.0},
				},
			},
			want: []string{"amount not readable here"},
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)

			fields := map[string]interface{}{
				"DocEntry":      77,
				"DocNum":        900,
				"DocObjectCode": "bopdt_OutgoingPayments",
				"DocType":       "bopdt_Vendor",
				"CardCode":      "VENDA000939",
				"CardName":      "TPAC PACKAGING INDIA PVT LTD II",
				"DocDate":       "2026-08-24T00:00:00Z",
				"Remarks":       "august bills",
			}
			for k, v := range tc.funding {
				fields[k] = v
			}
			f.put("PaymentDrafts", 77, fields)
			seedCreation(t, operatorLog(root, "tester"), "PaymentDrafts", "TESTDB", 77, "tester", time.Now())

			stdout, stderr, err := execWrite(t, "", "delete", "payment-draft", "77", "--dry-run")
			if err != nil {
				t.Fatalf("dry-run failed: %v", err)
			}
			shown := stdout + stderr
			for _, want := range tc.want {
				if !strings.Contains(shown, want) {
					t.Errorf("the operator must see %q before deleting this draft\n--- stdout ---\n%s\n--- stderr ---\n%s",
						want, stdout, stderr)
				}
			}
			// The amount is what the operator needs; the cheque number and the
			// bank are not, and they must not be printed either.
			for _, secret := range []string{"000123", "HDFC"} {
				if strings.Contains(shown, secret) {
					t.Errorf("%q is bank data and must stay off the screen:\n%s", secret, shown)
				}
			}
		})
	}
}

// TestPaymentDraftSnapshotRecordsFundingWithoutBankData pins the audit-trail
// half of the same gap: the snapshot is described as "what was destroyed", so
// for a cheque-funded payment draft it has to carry the funded amount — while
// the cheque number, the bank and the account stay out of a file that is
// designed to be committed and shared.
func TestPaymentDraftSnapshotRecordsFundingWithoutBankData(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)

	f.put("PaymentDrafts", 77, map[string]interface{}{
		"DocEntry": 77, "DocNum": 900, "DocObjectCode": "bopdt_OutgoingPayments",
		"CardCode": "VENDA000939", "CardName": "TPAC PACKAGING INDIA PVT LTD II",
		"CashSum": 0.0, "TransferSum": 0.0,
		"PaymentChecks": []interface{}{
			map[string]interface{}{"CheckNumber": "000123", "BankCode": "HDFC", "CheckSum": 2500000.0},
		},
		"PaymentInvoices": []interface{}{
			map[string]interface{}{"LineNum": 0, "DocEntry": 54983, "SumApplied": 2500000.0},
		},
	})
	seedCreation(t, operatorLog(root, "tester"), "PaymentDrafts", "TESTDB", 77, "tester", time.Now())

	if _, _, err := execWrite(t, "", "delete", "payment-draft", "77", "--yes"); err != nil {
		t.Fatalf("delete failed: %v", err)
	}

	snapshot := f.recordedSnapshot(t)

	// The cheque LINES are dropped by the redaction allowlist — they carry the
	// number, the bank and the account — but their total is recorded, because a
	// trail that says a 25-lakh payment was worth zero is worse than no trail.
	if _, ok := snapshot["PaymentChecks"]; ok {
		t.Error("PaymentChecks must stay out of the recorded snapshot")
	}
	// And none of it — redacted or not — reaches the file that gets committed.
	for _, e := range f.deleteLogLines(t) {
		b, err := json.Marshal(e)
		if err != nil {
			t.Fatalf("re-marshaling the log line: %v", err)
		}
		for _, secret := range []string{"000123", "HDFC", "TPAC PACKAGING"} {
			if strings.Contains(string(b), secret) {
				t.Errorf("%q must not reach the committed write log:\n%s", secret, b)
			}
		}
	}
	raw, err := json.Marshal(snapshot)
	if err != nil {
		t.Fatalf("re-marshaling snapshot: %v", err)
	}
	for _, secret := range []string{"000123", "HDFC"} {
		if strings.Contains(string(raw), secret) {
			t.Errorf("%q is bank data and must not reach the write log:\n%s", secret, raw)
		}
	}
	if got := snapshot["ChequeSum"]; got != 2500000.0 {
		t.Errorf("ChequeSum = %v, want 2500000 — the funded amount is what was destroyed", got)
	}

	// What the trail DOES keep: the allocation.
	lines, ok := snapshot["PaymentInvoices"].([]interface{})
	if !ok || len(lines) == 0 {
		t.Fatalf("expected PaymentInvoices to survive into the snapshot, got %v", snapshot["PaymentInvoices"])
	}
	first, _ := lines[0].(map[string]interface{})
	if first["SumApplied"] != 2500000.0 {
		t.Errorf("SumApplied = %v, want 2500000", first["SumApplied"])
	}
	t.Logf("confirmed: the only surviving figure is the allocation, not the funding: %v", snapshot)
}

// --- what may vouch for a delete --------------------------------------------

// TestEnvWriteLogCannotAuthoriseADelete — $SAPB1_WRITE_LOG says where this run
// RECORDS its writes. It must never be able to say what HAPPENED.
//
// config.RepoRoot already refuses to let that one variable choose the trust root
// (TestRepoRootIsNotEnvSelectable pins it). If the provenance scan then reads
// the env-named file as evidence, the same door is open one step further along:
// point it at a hand-written line and a draft a person keyed by hand deletes
// non-interactively, in a batch, without ever meeting --not-created-here — which
// is deliberately built to need one DocEntry and a human at a prompt. Worse, the
// audit line recording the delete lands in that same caller-chosen file, so
// nothing about it reaches the shared history.
func TestEnvWriteLogCannotAuthoriseADelete(t *testing.T) {
	f := newFakeDraftSAP(t)

	// No checkout at all: an empty directory, so the queries/*/ glob finds
	// nothing and only the configured log could possibly vouch.
	setProvenanceRoot(t, t.TempDir())

	planted := filepath.Join(t.TempDir(), "anything.jsonl")
	seedCreation(t, planted, "Drafts", "TESTDB", 54990, "tester", time.Now())
	t.Setenv("SAPB1_WRITE_LOG", planted)

	f.putDraft(54990, nil)

	_, stderr, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("the env-named log vouched for a draft; it is a destination, not a witness")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	if !strings.Contains(refused.Msg, "no record that this CLI created it") {
		t.Errorf("unexpected refusal:\n%s", refused.Msg)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}

	// And the operator is told why their log did not count, rather than left to
	// wonder why a draft they just made will not delete.
	if !strings.Contains(stderr, "is where this run RECORDS writes, not evidence") {
		t.Errorf("stderr must explain why the configured log was not read as evidence:\n%s", stderr)
	}

	// The one route that still works is the one with a person on it.
	withTTY(t, true)
	stdout, _, err := execWrite(t, "yes\n", "delete", "draft", "54990", "--not-created-here")
	if err != nil {
		t.Fatalf("--not-created-here at a prompt must still work: %v", err)
	}
	if !strings.Contains(stdout, "Deleted Drafts(54990)") {
		t.Errorf("expected the human-confirmed delete to go through:\n%s", stdout)
	}
}

// TestHomeWriteLogCannotAuthoriseADelete — the same lever, one step to the left.
//
// The guard excluded $SAPB1_WRITE_LOG by name and then read
// ~/.sapb1-writes.jsonl, which on Unix is $HOME — still one environment
// variable. `HOME=/tmp/planted sapb1 delete draft 54990 --yes` with a single
// forged line deleted a hand-keyed draft with no checkout, no TTY, no human and
// no --not-created-here: the whole gate, gone, exactly as the comment above
// provenanceLogPaths said it must not be.
//
// Outside a registered checkout there is no shared history to read, so the
// honest answer is "no write log found" — which is what a month-old Drive zip
// already gets, and it routes to the recorded override with a person on it.
func TestHomeWriteLogCannotAuthoriseADelete(t *testing.T) {
	f := newFakeDraftSAP(t)
	setProvenanceRoot(t, t.TempDir()) // no checkout: nothing legitimate can vouch

	// The attacker's whole toolkit: one line, in the home directory they control.
	planted := filepath.Join(os.Getenv("HOME"), ".sapb1-writes.jsonl")
	seedCreation(t, planted, "Drafts", "TESTDB", 54990, "tester", time.Now())
	// And point the configured log somewhere else entirely, so the home file is
	// the only thing that could possibly be read as evidence.
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "elsewhere.jsonl"))

	f.putDraft(54990, nil)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("a file in $HOME vouched for a draft — that is one environment variable holding the whole guard")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	if !strings.Contains(refused.Msg, "no record that this CLI created it") {
		t.Errorf("unexpected refusal:\n%s", refused.Msg)
	}
	if !strings.Contains(refused.Msg, "No write log was found on this machine at all") {
		t.Errorf("with no checkout the refusal must say there is nothing to read:\n%s", refused.Msg)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

// TestPlantedOperatorDirectoryIsNotEvidence — os.Lstat only refuses a symlink in
// the LAST path component, so `queries/ghost -> /somewhere/outside` used to walk
// straight through the glob and be printed back to the operator as the
// reassuring in-repo path "queries/ghost/sap-writes.jsonl".
func TestPlantedOperatorDirectoryIsNotEvidence(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("symlinks need a privilege on Windows")
	}
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)

	outside := t.TempDir()
	seedCreation(t, filepath.Join(outside, "sap-writes.jsonl"), "Drafts", "TESTDB", 54990, "tester", time.Now())
	if err := os.Symlink(outside, filepath.Join(root, "queries", "ghost")); err != nil {
		t.Fatalf("symlink: %v", err)
	}

	_, stderr, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("a log reached through a symlinked operator directory vouched for a draft")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
	if !strings.Contains(stderr, "outside this checkout") {
		t.Errorf("skipping planted evidence must be said out loud:\n%s", stderr)
	}
}

// TestSAPsCreationDateBeatsTheLogLine — the write log is a local unsigned file
// and DocEntry numbers come round again after a company restore. When the row
// SAP just handed back says it was created in 2020 and the vouching line claims
// this afternoon, the line is not about this draft.
func TestSAPsCreationDateBeatsTheLogLine(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, map[string]interface{}{"CreationDate": "2020-01-01T00:00:00Z", "UserSign": 9})
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("a log line contradicted by SAP's own CreationDate must not vouch")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"SAP says the row was created on 2020-01-01", "--not-created-here"} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}

	// A draft whose CreationDate agrees with the log line is untouched by this
	// check — it is the disagreement that matters, and a date either side of the
	// log's own day is honest (SAP's date is local, the log line is UTC).
	f2 := newFakeDraftSAP(t)
	root2 := provenanceRepo(t)
	f2.putDraft(54991, map[string]interface{}{"CreationDate": time.Now().Format("2006-01-02") + "T00:00:00Z"})
	seedCreation(t, operatorLog(root2, "tester"), "Drafts", "TESTDB", 54991, "tester", time.Now())
	if _, _, err := execWrite(t, "", "delete", "draft", "54991", "--yes"); err != nil {
		t.Fatalf("a CreationDate that agrees with the log must delete normally: %v", err)
	}
}

// TestProvenanceIgnoresANonOutcomeCreation guards the shape of the evidence
// rule from the other side: near-miss lines must not vouch. buildProvenanceIndex
// is unit-tested directly; this drives the same rule end to end through the
// command, which is where an operator would actually meet it.
func TestProvenanceIgnoresANonOutcomeCreation(t *testing.T) {
	cases := []struct {
		name    string
		mutate  func(e map[string]interface{})
		vouches bool
	}{
		{name: "exact creation line", mutate: func(map[string]interface{}) {}, vouches: true},
		{name: "intent, never resolved", mutate: func(e map[string]interface{}) { e["event"] = "intent" }},
		{name: "PATCH not POST", mutate: func(e map[string]interface{}) { e["method"] = "PATCH" }},
		{name: "another company", mutate: func(e map[string]interface{}) { e["company_db"] = "JIVO_MART_HANADB" }},
		{name: "another entity set", mutate: func(e map[string]interface{}) { e["path"] = "PaymentDrafts" }},
		{name: "SAP rejected it", mutate: func(e map[string]interface{}) { e["status"] = 400 }},
		{name: "a longer DocEntry", mutate: func(e map[string]interface{}) { e["result_key"] = "DocEntry=549901" }},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)
			f.putDraft(54990, nil)

			line := map[string]interface{}{
				"time": time.Now().Format(time.RFC3339Nano), "event": "outcome",
				"host": "sap.example", "port": 50000, "company_db": "TESTDB",
				"user": "tester", "method": "POST", "path": "Drafts",
				"status": 201, "result_key": "DocEntry=54990",
			}
			tc.mutate(line)

			path := operatorLog(root, "tester")
			if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
				t.Fatalf("creating log dir: %v", err)
			}
			b, err := json.Marshal(line)
			if err != nil {
				t.Fatalf("marshaling line: %v", err)
			}
			if err := os.WriteFile(path, append(b, '\n'), 0o600); err != nil {
				t.Fatalf("writing log: %v", err)
			}

			_, _, err = execWrite(t, "", "delete", "draft", "54990", "--yes")
			vouched := err == nil
			if vouched != tc.vouches {
				t.Errorf("line vouched = %v, want %v (err=%v)", vouched, tc.vouches, err)
			}
			if !tc.vouches && countMethod(f.seenMethods(), "DELETE") != 0 {
				t.Error("a non-vouching line still let a DELETE onto the wire")
			}
		})
	}
}
