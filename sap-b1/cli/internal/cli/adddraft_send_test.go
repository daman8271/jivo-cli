package cli

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"path/filepath"
	"strings"
	"sync"
	"testing"

	"sapb1/internal/errs"
)

// ---------------------------------------------------------------------------
// The send path: everything from "the operator typed yes" onwards.
//
// These are the tests that matter most in this package. Every other guard in
// add-draft refuses BEFORE anything is sent, so getting one of them wrong costs
// an operator an argument with the tool. Getting one of THESE wrong puts a
// duplicate A/P invoice on a vendor's ledger and in a GST return, and nothing
// in this CLI can take it back.
// ---------------------------------------------------------------------------

// fakeAddSAP serves the four things add-draft reads and the one thing it sends.
type fakeAddSAP struct {
	srv *httptest.Server

	mu       sync.Mutex
	requests []string          // "METHOD /b1s/v1/<path>" of every non-Login request
	objects  map[string]string // "Drafts(55126)" -> JSON body; absent = 404

	addStatus int    // status to answer the Add with (default 200)
	addBody   string // body to answer the Add with
	// afterAdd rewrites the draft the way SAP would have, and is what the
	// outcome classification is then made to read.
	afterAdd func(f *fakeAddSAP)
	// beforeGet fires before every keyed GET — the hook that lets a test change
	// the draft between the preview and the send, which is the whole point of
	// guard 7.
	beforeGet func(f *fakeAddSAP, key string)
	became    []map[string]interface{} // rows the PurchaseInvoices lookup returns
	added     int
	// diApproval is what CompanyService_GetAdminInfo answers for
	// EnableApprovalProcedureInDI. Empty means tYES (Oil's setting, the one
	// every older test was written against); a test sets tNO to be Mart.
	diApproval string
	// adminStatus lets a test make the settings read itself fail.
	adminStatus int
}

func newFakeAddSAP(t *testing.T) *fakeAddSAP {
	t.Helper()
	f := &fakeAddSAP{objects: map[string]string{}, addStatus: http.StatusOK, addBody: `{}`}

	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/Login") {
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake"})
			_, _ = w.Write([]byte(`{"SessionId":"fake"}`))
			return
		}
		path := strings.TrimPrefix(r.URL.Path, "/b1s/v1/")
		f.mu.Lock()
		f.requests = append(f.requests, r.Method+" "+r.URL.Path)
		hook, after := f.beforeGet, f.afterAdd
		f.mu.Unlock()

		if r.Method == http.MethodPost && path == "CompanyService_GetAdminInfo" {
			f.mu.Lock()
			di, st := f.diApproval, f.adminStatus
			f.mu.Unlock()
			if di == "" {
				di = "tYES"
			}
			if st != 0 && st != http.StatusOK {
				w.WriteHeader(st)
				_, _ = w.Write([]byte(`{"error":{"code":-1,"message":{"lang":"en-us","value":"General Settings unavailable"}}}`))
				return
			}
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"EnableApprovalProcedureInDI": di, "EnableUpdateDocAfterApproval": "tYES",
			})
			return
		}

		if r.Method == http.MethodPost && path == "DraftsService_SaveDraftToDocument" {
			f.mu.Lock()
			f.added++
			f.mu.Unlock()
			if after != nil {
				after(f)
			}
			w.WriteHeader(f.addStatus)
			_, _ = w.Write([]byte(f.addBody))
			return
		}

		// Collection reads (the vendor card, the "what did it become" lookup).
		// A filtered read arrives with its $filter in RawQuery, never in Path —
		// looking for a '?' in the path finds nothing and silently 404s the
		// lookup instead.
		if r.URL.RawQuery != "" {
			rows := []map[string]interface{}{}
			switch path {
			case "BusinessPartners":
				rows = append(rows, map[string]interface{}{
					"CardCode": "VENDA000939", "SubjectToWithholdingTax": "boNO",
				})
			case "PurchaseInvoices":
				rows = f.became
			}
			_ = json.NewEncoder(w).Encode(map[string]interface{}{"value": rows})
			return
		}

		if hook != nil {
			hook(f, path)
		}
		f.mu.Lock()
		body, ok := f.objects[path]
		f.mu.Unlock()
		if !ok {
			w.WriteHeader(http.StatusNotFound)
			_, _ = w.Write([]byte(sapNotFound))
			return
		}
		_, _ = w.Write([]byte(body))
	}))
	t.Cleanup(f.srv.Close)

	u, err := url.Parse(f.srv.URL)
	if err != nil {
		t.Fatalf("parsing the fake server URL: %v", err)
	}
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(home, "writes.jsonl"))
	t.Setenv("SAPB1_SNAPSHOT_LOG", filepath.Join(home, "snapshots.jsonl"))
	// add-draft fans its log out to the checkout it is standing in
	// (config.SharedWriteLogPath), and this package sits inside the developer's
	// real jivo-cli. Stand somewhere empty so the suite can never append a
	// fabricated Add to the team's committed write log.
	t.Chdir(t.TempDir())
	t.Setenv("SAPB1_HOST", u.Hostname())
	t.Setenv("SAPB1_PORT", u.Port())
	t.Setenv("SAPB1_COMPANYDB", "TESTDB")
	t.Setenv("SAPB1_USER", "tester")
	t.Setenv("SAPB1_PASSWORD", "irrelevant")
	t.Setenv("SAPB1_INSECURE", "true")
	t.Setenv("SAPB1_TIMEOUT", "5")
	setProvenanceRoot(t, t.TempDir())
	withTTY(t, false)
	return f
}

// putAddDraft seeds a clean, addable A/P invoice draft drawn from a GRPO.
func (f *fakeAddSAP) putAddDraft(docEntry int64, over map[string]interface{}) {
	row := map[string]interface{}{
		"DocEntry": docEntry, "DocNum": 5000 + docEntry,
		"DocObjectCode": "oPurchaseInvoices", "DocumentStatus": "bost_Open",
		"AuthorizationStatus": "dasWithout", "CardCode": "VENDA000939",
		"CardName": "TPAC PACKAGING", "NumAtCard": "2606000806",
		"DocTotal": 253110, "VatSum": 38610, "WTAmount": 0,
		"DocDate": "2026-08-14", "TaxDate": "2026-08-13", "Series": 3684,
		"AttachmentEntry": 170187,
		"DocumentLines": []map[string]interface{}{{
			"LineNum": 0, "ItemCode": "RM0000052", "LineTotal": 214500,
			"WTLiable": "tNO", "BaseType": 20, "BaseEntry": 9001, "BaseLine": 0,
			"LineStatus": "bost_Open",
		}},
	}
	for k, v := range over {
		row[k] = v
	}
	b, _ := json.Marshal(row)
	f.mu.Lock()
	f.objects[fmt.Sprintf("Drafts(%d)", docEntry)] = string(b)
	f.mu.Unlock()

	grpo, _ := json.Marshal(map[string]interface{}{
		"DocEntry": 9001, "DocNum": 77001,
		"DocumentLines": []map[string]interface{}{{"LineNum": 0, "LineStatus": "bost_Open"}},
	})
	f.mu.Lock()
	f.objects["PurchaseDeliveryNotes(9001)"] = string(grpo)
	f.mu.Unlock()
}

// mutate rewrites one field on a seeded draft, in place.
func (f *fakeAddSAP) mutate(key string, field string, value interface{}) {
	f.mu.Lock()
	defer f.mu.Unlock()
	var row map[string]interface{}
	_ = json.Unmarshal([]byte(f.objects[key]), &row)
	row[field] = value
	b, _ := json.Marshal(row)
	f.objects[key] = string(b)
}

func (f *fakeAddSAP) addCount() int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return f.added
}

// TestAddRefusesADraftThatChangedAfterTheOperatorLookedAtIt is guard 7, and it
// is the reason this command can be trusted with --yes.
//
// The operator reads a summary saying ₹2,53,110 and types yes. In the seconds
// between, a colleague in the SAP client edits the draft to ₹12,00,000. delete
// deliberately TOLERATES this window (delete.go:1204 re-snapshots instead of
// refusing) because a delete destroys the row either way. Here the operator
// approved a DOCUMENT, not a DocEntry, and if the document changed their yes
// was about something that no longer exists.
func TestAddRefusesADraftThatChangedAfterTheOperatorLookedAtIt(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, nil)

	// The preflight GET sees the original; the pre-send GET sees the edit. That
	// is exactly the real race: a colleague editing the draft in the SAP client
	// between the operator reading the summary and typing yes.
	reads := 0
	f.beforeGet = func(f *fakeAddSAP, key string) {
		if key != "Drafts(55126)" {
			return
		}
		reads++
		// beforeGet fires BEFORE the body is served, so mutating on read 1 would
		// corrupt the very read the operator is shown and the two snapshots would
		// agree again. Read 1 must serve the original; the edit lands just before
		// read 2, which is the pre-send re-read.
		if reads == 2 {
			f.mutate("Drafts(55126)", "DocTotal", 1200000)
		}
	}

	_, stderr, err := execWrite(t, "", "add-draft", "55126", "--yes")

	if f.addCount() != 0 {
		t.Fatalf("a draft that changed must NEVER be sent — got %d Add(s)", f.addCount())
	}
	var refused *errs.RefusedError
	if err == nil || !asRefused(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"has CHANGED", "Nothing was sent", "DocTotal"} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must mention %q, got:\n%s\n%s", want, refused.Msg, stderr)
		}
	}
}

// TestAddOfAnUnsubmittedDraftReportsApprovalNotPosting — the expected outcome
// for an Oil A/P draft. The operator must not read this as money moving.
func TestAddOfAnUnsubmittedDraftReportsApprovalNotPosting(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, nil)
	f.afterAdd = func(f *fakeAddSAP) { f.mutate("Drafts(55126)", "AuthorizationStatus", "dasPending") }

	stdout, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
	if err != nil {
		t.Fatalf("add failed: %v", err)
	}
	if f.addCount() != 1 {
		t.Fatalf("expected exactly 1 Add, got %d", f.addCount())
	}
	for _, want := range []string{"submitted for approval", "not in the ledger", "NOTHING was added"} {
		if !strings.Contains(stdout, want) {
			t.Errorf("approval outcome must say %q, got:\n%s", want, stdout)
		}
	}
	if strings.Contains(stdout, "ADDED in") {
		t.Error("an approval request must never be reported as a posted document")
	}
}

// TestAddOfAnApprovedDraftReportsItPostedAndNamesTheDocument — click two. This
// one really does move money, and the wording has to say so unmistakably.
func TestAddOfAnApprovedDraftReportsItPostedAndNamesTheDocument(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, map[string]interface{}{"AuthorizationStatus": "dasApproved"})
	f.afterAdd = func(f *fakeAddSAP) { f.mutate("Drafts(55126)", "DocumentStatus", "bost_Close") }
	f.became = []map[string]interface{}{{"DocEntry": 47577, "DocNum": "626074104", "DocTotal": 253110}}

	stdout, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
	if err != nil {
		t.Fatalf("add failed: %v", err)
	}
	for _, want := range []string{"ADDED in", "47577", "626074104", "LIVE", "Only SAP can reverse it"} {
		if !strings.Contains(stdout, want) {
			t.Errorf("posted outcome must say %q, got:\n%s", want, stdout)
		}
	}
}

// TestAddThatChangesNothingIsNotSuccess — a 2xx with the draft reading exactly
// as before is the state most likely to be mistaken for success. It is exit 8,
// and it must tell the operator not to re-run.
func TestAddThatChangesNothingIsNotSuccess(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, nil)
	// afterAdd deliberately absent: SAP says 200 and nothing moves.

	_, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
	var verify *errs.WriteVerifyError
	if err == nil || !asVerify(err, &verify) {
		t.Fatalf("expected *errs.WriteVerifyError (exit 8), got %T: %v", err, err)
	}
	if ExitCodeFor(err) != 8 {
		t.Errorf("a 2xx with no visible change must be exit 8, got %d", ExitCodeFor(err))
	}
	for _, want := range []string{"nothing visibly changed", "Do NOT run add-draft"} {
		if !strings.Contains(verify.Msg, want) {
			t.Errorf("message must say %q, got:\n%s", want, verify.Msg)
		}
	}
}

// TestAddRefusesAnAlreadyAddedDraftWithNoWayRound is guard 4 — the single most
// important refusal in the command. delete offers --closed for exactly this
// state; here that flag would be a duplicate-invoice button, so it does not
// exist and the JSON stream must positively say there is no flag to reach for.
func TestAddRefusesAnAlreadyAddedDraftWithNoWayRound(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, map[string]interface{}{"DocumentStatus": "bost_Close"})

	stdout, _, err := execWrite(t, "", "add-draft", "55126", "--yes", "--json")
	if f.addCount() != 0 {
		t.Fatal("an already-Added draft must never be sent again")
	}
	if ExitCodeFor(err) != 9 {
		t.Fatalf("expected exit 9, got %d (%v)", ExitCodeFor(err), err)
	}
	for _, line := range splitLines(stdout) {
		var rec struct {
			SuggestedFlags []string `json:"suggestedFlags"`
		}
		if json.Unmarshal([]byte(line), &rec) == nil && len(rec.SuggestedFlags) != 0 {
			t.Errorf("suggestedFlags must ALWAYS be empty on add-draft — a flag here is a double-post button; got %v", rec.SuggestedFlags)
		}
	}
	if !strings.Contains(stdout, `"suggestedFlags":[]`) {
		t.Error(`the record must carry an explicitly EMPTY suggestedFlags, so a caller stops looking for one`)
	}
}

// TestAddRefusesADraftInSomebodyElsesQueue — dasPending and dasRejected are
// other people's decisions. No override.
func TestAddRefusesADraftInSomebodyElsesQueue(t *testing.T) {
	for _, status := range []string{"dasPending", "dasRejected", "dasGenerated"} {
		t.Run(status, func(t *testing.T) {
			f := newFakeAddSAP(t)
			f.putAddDraft(55126, map[string]interface{}{"AuthorizationStatus": status})
			_, _, err := execWrite(t, "", "add-draft", "55126", "--yes")
			if f.addCount() != 0 {
				t.Fatalf("%s must never be Added", status)
			}
			if ExitCodeFor(err) != 9 {
				t.Fatalf("expected exit 9 for %s, got %d (%v)", status, ExitCodeFor(err), err)
			}
		})
	}
}

// TestAddDryRunReadsEverythingAndSendsNothing.
func TestAddDryRunReadsEverythingAndSendsNothing(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, nil)

	stdout, _, err := execWrite(t, "", "add-draft", "55126", "--dry-run")
	if err != nil {
		t.Fatalf("dry run failed: %v", err)
	}
	if f.addCount() != 0 {
		t.Fatal("a dry run must send no Add")
	}
	if !strings.Contains(strings.Join(f.requests, "\n"), "GET /b1s/v1/Drafts(55126)") {
		t.Error("a dry run must still READ the draft — it is how the guards run")
	}
	if !strings.Contains(stdout, "DraftsService_SaveDraftToDocument") {
		t.Errorf("dry run must show the exact request that would be sent, got:\n%s", stdout)
	}
}

// TestAddBatchStopsAtTheFirstProblemAndNamesWhatWentLive — the tally after a
// partial batch is the operator's only map of what is now real. "failed" and
// "not attempted" must never be muddled with a document that posted.
func TestAddBatchStopsAtTheFirstProblemAndNamesWhatWentLive(t *testing.T) {
	f := newFakeAddSAP(t)
	for _, n := range []int64{55126, 55130, 55165} {
		f.putAddDraft(n, map[string]interface{}{"AuthorizationStatus": "dasApproved"})
	}
	f.became = []map[string]interface{}{{"DocEntry": 47577, "DocNum": "626074104", "DocTotal": 253110}}
	// The first posts; the second is answered with a SAP refusal.
	f.afterAdd = func(f *fakeAddSAP) {
		if f.addCount() == 1 {
			f.mutate("Drafts(55126)", "DocumentStatus", "bost_Close")
			return
		}
		f.addStatus = http.StatusBadRequest
		f.addBody = `{"error":{"code":-5002,"message":{"lang":"en-us","value":"Attachments folder not defined [131-102]"}}}`
	}

	_, _, err := execWrite(t, "", "add-draft", "55126", "55130", "55165", "--yes")
	if err == nil {
		t.Fatal("a batch whose second document failed must return an error")
	}
	msg := err.Error()
	for _, want := range []string{"POSTED LIVE (1)", "55126", "not attempted", "55165", "Do not re-run"} {
		if !strings.Contains(msg, want) {
			t.Errorf("batch tally must say %q, got:\n%s", want, msg)
		}
	}
	if f.addCount() != 2 {
		t.Errorf("the batch must stop after the failure, not carry on: %d Adds sent", f.addCount())
	}
	if !strings.Contains(msg, "attachments folder on the SAP server") {
		t.Errorf("the -5002 [131-102] hint must fire — it reads like a problem with the draft and is not one; got:\n%s", msg)
	}
}

// TestAddMixedBatchSeparatesLiveMoneyFromApprovalMoney — a person confirming a
// batch that mixes click one and click two must not think all of it is inert.
func TestAddMixedBatchSeparatesLiveMoneyFromApprovalMoney(t *testing.T) {
	f := newFakeAddSAP(t)
	f.putAddDraft(55126, nil)                                                          // submit
	f.putAddDraft(55130, map[string]interface{}{"AuthorizationStatus": "dasApproved"}) // POST LIVE
	_, stderr, _ := execWrite(t, "", "add-draft", "55126", "55130", "--dry-run")
	_ = stderr
	stdout, _, err := execWrite(t, "", "add-draft", "55126", "55130", "--dry-run")
	if err != nil {
		t.Fatalf("dry run failed: %v", err)
	}
	if !strings.Contains(stdout, "POST LIVE") || !strings.Contains(stdout, "submit for approval") {
		t.Errorf("a mixed batch must label BOTH actions, got:\n%s", stdout)
	}
}

func asRefused(err error, target **errs.RefusedError) bool {
	for e := err; e != nil; {
		if r, ok := e.(*errs.RefusedError); ok {
			*target = r
			return true
		}
		u, ok := e.(interface{ Unwrap() error })
		if !ok {
			return false
		}
		e = u.Unwrap()
	}
	return false
}

func asVerify(err error, target **errs.WriteVerifyError) bool {
	for e := err; e != nil; {
		if r, ok := e.(*errs.WriteVerifyError); ok {
			*target = r
			return true
		}
		u, ok := e.(interface{ Unwrap() error })
		if !ok {
			return false
		}
		e = u.Unwrap()
	}
	return false
}
