package cli

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"sapb1/internal/catalog"
	"sapb1/internal/errs"
)

// fakeDraftSAP is a Service Layer stand-in that can hold drafts, hand them back
// by key, and lose them when they are deleted — everything `delete` needs to be
// exercised without touching a real SAP box.
type fakeDraftSAP struct {
	srv     *httptest.Server
	logPath string

	mu      sync.Mutex
	methods []string          // "METHOD /b1s/v1/<path>" of every non-Login request
	objects map[string]string // "Drafts(54990)" -> JSON body; absent = 404

	deleteStatus    int            // status to answer a DELETE with (default 204)
	failDelete      map[string]int // per-key DELETE status, for "the third one blows up"
	keepAfterDelete bool           // answer 2xx but leave the object in place
	dropVerify      bool           // kill the connection on the GET that follows a DELETE
	stallDelete     map[string]bool
	beforeGet       func(f *fakeDraftSAP, key string) // fires before each keyed GET

	deleted map[string]bool
	release chan struct{}
}

// sapNotFound is the Service Layer's envelope for a key that isn't there.
const sapNotFound = `{"error":{"code":-2028,"message":{"lang":"en-us","value":"No matching records found (ODBC -2028)"}}}`

func newFakeDraftSAP(t *testing.T) *fakeDraftSAP {
	t.Helper()
	f := &fakeDraftSAP{
		objects:      map[string]string{},
		deleteStatus: http.StatusNoContent,
		failDelete:   map[string]int{},
		stallDelete:  map[string]bool{},
		deleted:      map[string]bool{},
		release:      make(chan struct{}),
	}

	f.srv = httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/Login") {
			http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
			_, _ = w.Write([]byte(`{"SessionId":"fake-session"}`))
			return
		}
		key := strings.TrimPrefix(r.URL.Path, "/b1s/v1/")

		f.mu.Lock()
		f.methods = append(f.methods, r.Method+" "+r.URL.Path)
		hook := f.beforeGet
		f.mu.Unlock()

		switch r.Method {
		case http.MethodGet:
			if hook != nil {
				hook(f, key)
			}
			f.mu.Lock()
			body, ok := f.objects[key]
			wasDeleted := f.deleted[key]
			drop := f.dropVerify
			f.mu.Unlock()

			if wasDeleted && drop {
				// Hijack and close: the DELETE was answered, the read-back
				// never gets one.
				if hj, canHijack := w.(http.Hijacker); canHijack {
					conn, _, err := hj.Hijack()
					if err == nil {
						_ = conn.Close()
						return
					}
				}
			}
			if !ok {
				w.WriteHeader(http.StatusNotFound)
				_, _ = w.Write([]byte(sapNotFound))
				return
			}
			_, _ = w.Write([]byte(body))

		case http.MethodDelete:
			f.mu.Lock()
			stall := f.stallDelete[key]
			status := f.deleteStatus
			if s, ok := f.failDelete[key]; ok {
				status = s
			}
			keep := f.keepAfterDelete
			f.mu.Unlock()

			if stall {
				<-f.release
				return
			}
			if status < 200 || status >= 300 {
				w.WriteHeader(status)
				_, _ = w.Write([]byte(`{"error":{"code":-5002,"message":{"lang":"en-us","value":"cannot remove this draft"}}}`))
				return
			}
			f.mu.Lock()
			f.deleted[key] = true
			if !keep {
				delete(f.objects, key)
			}
			f.mu.Unlock()
			w.WriteHeader(status)

		default:
			w.WriteHeader(http.StatusMethodNotAllowed)
		}
	}))
	t.Cleanup(func() {
		close(f.release)
		f.srv.Close()
	})

	u, err := url.Parse(f.srv.URL)
	if err != nil {
		t.Fatalf("parsing fake server URL: %v", err)
	}
	f.logPath = pointCLIAtFake(t, u)
	return f
}

// put installs a draft body under Drafts(<docEntry>) (or another entity set).
func (f *fakeDraftSAP) put(entitySet string, docEntry int64, fields map[string]interface{}) {
	if fields == nil {
		fields = map[string]interface{}{}
	}
	if _, ok := fields["DocEntry"]; !ok {
		fields["DocEntry"] = docEntry
	}
	b, err := json.Marshal(fields)
	if err != nil {
		panic(err)
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	f.objects[fmt.Sprintf("%s(%d)", entitySet, docEntry)] = string(b)
}

// putRaw installs a body verbatim, so a test can answer 200 with something that
// is not a draft at all.
func (f *fakeDraftSAP) putRaw(entitySet string, docEntry int64, body string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.objects[fmt.Sprintf("%s(%d)", entitySet, docEntry)] = body
}

func (f *fakeDraftSAP) putDraft(docEntry int64, extra map[string]interface{}) {
	fields := map[string]interface{}{
		"DocEntry":       docEntry,
		"DocNum":         600000 + docEntry,
		"DocObjectCode":  "oPurchaseInvoices",
		"CardCode":       "VENDA000939",
		"CardName":       "TPAC PACKAGING INDIA PVT LTD II",
		"DocDate":        "2026-08-14T00:00:00Z",
		"DocTotal":       253110,
		"NumAtCard":      "2606000806",
		"DocumentStatus": "bost_Open",
		"UserSign":       48,
		"Comments":       "Based On Goods Receipt PO 2026086625",
		"DocumentLines": []interface{}{
			map[string]interface{}{
				"LineNum": 0, "ItemCode": "RM0000052", "Quantity": 10, "LineTotal": 214500,
				"AccountCode": "5110001", "GrossPrice": 21450,
			},
		},
	}
	for k, v := range extra {
		fields[k] = v
	}
	f.put("Drafts", docEntry, fields)
}

func (f *fakeDraftSAP) seenMethods() []string {
	f.mu.Lock()
	defer f.mu.Unlock()
	out := make([]string, len(f.methods))
	copy(out, f.methods)
	return out
}

// logEntries returns every line of the write log, decoded.
func (f *fakeDraftSAP) logEntries(t *testing.T) []map[string]interface{} {
	t.Helper()
	data, err := os.ReadFile(f.logPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		t.Fatalf("reading write log: %v", err)
	}
	var out []map[string]interface{}
	for _, line := range splitLines(string(data)) {
		var e map[string]interface{}
		if err := json.Unmarshal([]byte(line), &e); err != nil {
			t.Fatalf("write log line is not JSON: %v\n%s", err, line)
		}
		out = append(out, e)
	}
	return out
}

// snapshotEntries returns every line of the LOCAL snapshot log — where a
// delete's contents go, addressed from the shared write log by hash.
func (f *fakeDraftSAP) snapshotEntries(t *testing.T) []map[string]interface{} {
	t.Helper()
	data, err := os.ReadFile(os.Getenv("SAPB1_SNAPSHOT_LOG"))
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		t.Fatalf("reading snapshot log: %v", err)
	}
	var out []map[string]interface{}
	for _, line := range splitLines(string(data)) {
		var e map[string]interface{}
		if err := json.Unmarshal([]byte(line), &e); err != nil {
			t.Fatalf("snapshot log line is not JSON: %v\n%s", err, line)
		}
		out = append(out, e)
	}
	return out
}

// recordedSnapshot returns the single snapshot a test's delete recorded.
func (f *fakeDraftSAP) recordedSnapshot(t *testing.T) map[string]interface{} {
	t.Helper()
	entries := f.snapshotEntries(t)
	if len(entries) != 1 {
		t.Fatalf("want exactly one recorded snapshot, got %d", len(entries))
	}
	snap, ok := entries[0]["snapshot"].(map[string]interface{})
	if !ok {
		t.Fatalf("the snapshot line carries no snapshot: %v", entries[0])
	}
	return snap
}

// deleteLogLines returns the intent/outcome pair(s) for DELETE requests.
func (f *fakeDraftSAP) deleteLogLines(t *testing.T) []map[string]interface{} {
	t.Helper()
	var out []map[string]interface{}
	for _, e := range f.logEntries(t) {
		if e["method"] == "DELETE" {
			out = append(out, e)
		}
	}
	return out
}

// seedCreation writes the one line the provenance guard is looking for: the
// successful POST that created this DocEntry.
func seedCreation(t *testing.T, path, entitySet, companyDB string, docEntry int64, user string, when time.Time) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("creating log dir: %v", err)
	}
	line := map[string]interface{}{
		"time":       when.Format(time.RFC3339Nano),
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
	b, err := json.Marshal(line)
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

// provenanceRepo builds a temp tree that looks like a JIVO checkout and points
// the guard at it, returning the root.
func provenanceRepo(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	for _, d := range []string{"harness", ".git", "queries"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building fake repo: %v", err)
		}
	}
	setProvenanceRoot(t, root)
	return root
}

// operatorLog is the path a given operator's committed write log lives at.
func operatorLog(root, operator string) string {
	return filepath.Join(root, "queries", operator, "sap-writes.jsonl")
}

// countMethod counts requests of one HTTP method in a recorded sequence.
func countMethod(methods []string, method string) int {
	n := 0
	for _, m := range methods {
		if strings.HasPrefix(m, method+" ") {
			n++
		}
	}
	return n
}

// --- the command tree -------------------------------------------------------

// TestDeleteParentRefuses — `sapb1 delete` with no subcommand must explain
// itself, not fall through to something that deletes.
func TestDeleteParentRefuses(t *testing.T) {
	f := newFakeDraftSAP(t)

	_, _, err := execWrite(t, "", "delete")
	if err == nil {
		t.Fatal("expected `delete` alone to fail")
	}
	var usage *errs.UsageError
	if !errors.As(err, &usage) {
		t.Fatalf("expected *errs.UsageError, got %T: %v", err, err)
	}
	for _, want := range []string{"delete draft", "delete payment-draft", "Drafts are the only thing"} {
		if !strings.Contains(usage.Msg, want) {
			t.Errorf("refusal must mention %q, got:\n%s", want, usage.Msg)
		}
	}
	if got := len(f.seenMethods()); got != 0 {
		t.Errorf("nothing may be sent: %v", f.seenMethods())
	}
}

// TestDeleteRejectsAnythingButADraft — the entity set is fixed by the
// subcommand, so a posted document is not a refusal but an unknown command.
func TestDeleteRejectsAnythingButADraft(t *testing.T) {
	unknownCommand := []string{
		"Invoices(9)",
		"Drafts(1)/Cancel",
		"Drafts",
		"PaymentDrafts(5)",
		"$batch",
		"../Login",
		"BusinessPartners",
	}
	for _, arg := range unknownCommand {
		t.Run("delete "+arg, func(t *testing.T) {
			f := newFakeDraftSAP(t)
			_, _, err := execWrite(t, "", "delete", arg)
			if err == nil {
				t.Fatalf("expected `delete %s` to fail", arg)
			}
			if !strings.Contains(err.Error(), "unknown command") {
				t.Errorf("want an unknown-command error, got: %v", err)
			}
			if got := len(f.seenMethods()); got != 0 {
				t.Errorf("nothing may be sent: %v", f.seenMethods())
			}
			if _, statErr := os.Stat(f.logPath); statErr == nil {
				t.Error("nothing may be logged for a command that does not exist")
			}
		})
	}

	// (-1 never reaches the command: cobra reads it as a shorthand flag.)
	notADocEntry := []string{"Invoices(9)", "1/Cancel", "Drafts(1)", "0", "abc"}
	for _, arg := range notADocEntry {
		t.Run("delete draft "+arg, func(t *testing.T) {
			f := newFakeDraftSAP(t)
			_, _, err := execWrite(t, "", "delete", "draft", arg)
			if err == nil {
				t.Fatalf("expected `delete draft %s` to fail", arg)
			}
			if !strings.Contains(err.Error(), "not a DocEntry") {
				t.Errorf("want a \"not a DocEntry\" error, got: %v", err)
			}
			if got := len(f.seenMethods()); got != 0 {
				t.Errorf("nothing may be sent: %v", f.seenMethods())
			}
		})
	}
}

func TestParseDocEntries(t *testing.T) {
	valid := map[string][]int64{
		"1":          {1},
		"54990":      {54990},
		"2147483647": {2147483647},
	}
	for arg, want := range valid {
		got, _, err := parseDocEntries([]string{arg})
		if err != nil {
			t.Errorf("parseDocEntries(%q) errored: %v", arg, err)
			continue
		}
		if len(got) != len(want) || got[0] != want[0] {
			t.Errorf("parseDocEntries(%q) = %v, want %v", arg, got, want)
		}
	}

	invalid := []string{"0", "007", "-1", "+1", "1.0", "1e3", " 1 ", "abc", "", "２５", "1,2"}
	for _, arg := range invalid {
		if _, _, err := parseDocEntries([]string{arg}); err == nil {
			t.Errorf("parseDocEntries(%q) should have failed", arg)
		}
	}

	// Over the 32-bit DocEntry column: a specific, checkable message.
	for _, arg := range []string{"2147483648", "9999999999"} {
		_, _, err := parseDocEntries([]string{arg})
		if err == nil {
			t.Fatalf("parseDocEntries(%q) should have failed", arg)
		}
		if !strings.Contains(err.Error(), "larger than SAP can hold") {
			t.Errorf("want the int32 message for %q, got: %v", arg, err)
		}
	}

	entries, dupes, err := parseDocEntries([]string{"5", "7", "5"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(entries) != 2 || entries[0] != 5 || entries[1] != 7 {
		t.Errorf("dedupe must keep operator order: got %v", entries)
	}
	if len(dupes) != 1 || dupes[0] != 5 {
		t.Errorf("the repeat must be reported: got %v", dupes)
	}
}

// --- dry run ----------------------------------------------------------------

func TestDeleteDryRunReadsButNeverDeletes(t *testing.T) {
	f := newFakeDraftSAP(t)
	f.putDraft(54990, nil)

	stdout, _, err := execWrite(t, "", "delete", "draft", "54990", "--dry-run", "--not-created-here")
	if err != nil {
		t.Fatalf("dry run failed: %v", err)
	}

	want := []string{"GET /b1s/v1/Drafts(54990)"}
	if got := f.seenMethods(); len(got) != 1 || got[0] != want[0] {
		t.Errorf("dry run must send exactly one GET, got %v", got)
	}
	for _, phrase := range []string{"DRY RUN", "no DELETE was sent", "did contact SAP", "DELETE https://"} {
		if !strings.Contains(stdout, phrase) {
			t.Errorf("dry-run output must contain %q, got:\n%s", phrase, stdout)
		}
	}
	if _, statErr := os.Stat(f.logPath); statErr == nil {
		t.Error("a dry run must not write to the audit log")
	}
}

// TestDeleteDryRunJSONCarriesTheRequestAndTheSnapshotHash — a dry-run record
// carries everything a caller needs to build the real command, and the sha256 of
// the snapshot, but NOT the snapshot itself. Nothing has been destroyed yet: the
// draft is still in SAP to be read, so putting the vendor, their bill number and
// every line price on stdout — into a journal, a CI transcript, a log file —
// buys nothing. The contents appear on one record only, the receipt for a draft
// that is actually gone.
func TestDeleteDryRunJSONCarriesTheRequestAndTheSnapshotHash(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	// 54999 is already gone. Its record must still say it came from a dry run:
	// a skip written in its own shape used to be byte-identical to the same skip
	// from a real delete, so nothing reading the stream could tell a preview
	// from something that had already happened.
	stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "54999", "--dry-run")
	if err != nil {
		t.Fatalf("dry run failed: %v", err)
	}
	lines := splitLines(stdout)
	if len(lines) != 2 {
		t.Fatalf("want one JSON line per DocEntry, got %d:\n%s", len(lines), stdout)
	}
	type dryRunRecord struct {
		DryRun         bool   `json:"dryRun"`
		DocEntry       int64  `json:"docEntry"`
		Host           string `json:"host"`
		Port           int    `json:"port"`
		Method         string `json:"method"`
		URL            string `json:"url"`
		Skipped        string `json:"skipped"`
		Overrides      []string
		SnapshotSHA256 string                 `json:"snapshotSha256"`
		Snapshot       map[string]interface{} `json:"snapshot"`
	}
	var recs []dryRunRecord
	for _, l := range lines {
		var rec dryRunRecord
		if err := json.Unmarshal([]byte(l), &rec); err != nil {
			t.Fatalf("dry-run JSON is not JSON: %v\n%s", err, l)
		}
		recs = append(recs, rec)
	}
	for _, rec := range recs {
		if !rec.DryRun {
			t.Errorf("EVERY line of a --dry-run stream must carry dryRun:true, got %+v", rec)
		}
	}

	found, skipped := recs[0], recs[1]
	if found.DocEntry != 54990 || found.Method != "DELETE" {
		t.Errorf("unexpected record: %+v", found)
	}
	if found.Host == "" || found.Port == 0 {
		t.Errorf("host/port must be in the dry-run record (they say WHICH SAP): %+v", found)
	}
	if len(found.SnapshotSHA256) != 64 {
		t.Errorf("the record must carry the snapshot's sha256, got %q", found.SnapshotSHA256)
	}
	if found.Snapshot != nil {
		t.Errorf("nothing was deleted, so the snapshot CONTENTS must not be on stdout: %v", found.Snapshot)
	}
	if strings.Contains(stdout, "TPAC PACKAGING") {
		t.Errorf("the vendor must not reach stdout on a dry run:\n%s", stdout)
	}
	if skipped.DocEntry != 54999 || !strings.Contains(skipped.Skipped, "already deleted") {
		t.Errorf("the missing DocEntry needs its own record: %+v", skipped)
	}
	if skipped.SnapshotSHA256 != "" {
		t.Errorf("a draft that isn't there has no snapshot to hash: %+v", skipped)
	}
}

// TestDeletedRecordCarriesTheSnapshotAsAReceipt — the other half of the rule.
// The one record that DOES carry the contents is the one for a draft SAP has
// destroyed: it is the only copy the operator has left of what is gone, and the
// hash on it points at the local snapshot log holding the same bytes.
func TestDeletedRecordCarriesTheSnapshotAsAReceipt(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--yes")
	if err != nil {
		t.Fatalf("delete failed: %v", err)
	}
	var rec struct {
		Verified       bool                   `json:"verified"`
		SnapshotSHA256 string                 `json:"snapshotSha256"`
		Snapshot       map[string]interface{} `json:"snapshot"`
	}
	lines := splitLines(stdout)
	if len(lines) != 1 {
		t.Fatalf("want one record, got %d:\n%s", len(lines), stdout)
	}
	if err := json.Unmarshal([]byte(lines[0]), &rec); err != nil {
		t.Fatalf("record is not JSON: %v\n%s", err, lines[0])
	}
	if !rec.Verified || rec.Snapshot["CardName"] != "TPAC PACKAGING INDIA PVT LTD II" {
		t.Errorf("the receipt for a destroyed draft must carry what it held: %+v", rec)
	}
	// And it names the same bytes the local snapshot log kept.
	if got := f.snapshotEntries(t)[0]["sha256"]; got != rec.SnapshotSHA256 {
		t.Errorf("record hash %q does not point at the recorded snapshot %v", rec.SnapshotSHA256, got)
	}
}

// --- not found --------------------------------------------------------------

func TestDeleteSingleMissingDraftStops(t *testing.T) {
	f := newFakeDraftSAP(t)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a missing draft to stop the command")
	}
	var usage *errs.UsageError
	if !errors.As(err, &usage) {
		t.Fatalf("expected *errs.UsageError, got %T: %v", err, err)
	}
	if !strings.Contains(usage.Msg, "nothing to delete") {
		t.Errorf("want \"nothing to delete\", got: %s", usage.Msg)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

// TestDeleteBatchSkipsAlreadyGoneDrafts is what makes "just run it again" work
// after a batch died halfway.
func TestDeleteBatchSkipsAlreadyGoneDrafts(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "54991", "--yes")
	if err != nil {
		t.Fatalf("a batch with one already-gone draft must succeed: %v", err)
	}

	lines := splitLines(stdout)
	if len(lines) != 2 {
		t.Fatalf("want one record per DocEntry, got %d:\n%s", len(lines), stdout)
	}
	var deletedOK, skippedOK bool
	for _, l := range lines {
		var rec struct {
			DocEntry int64  `json:"docEntry"`
			Verified bool   `json:"verified"`
			Skipped  string `json:"skipped"`
			DryRun   bool   `json:"dryRun"`
		}
		if err := json.Unmarshal([]byte(l), &rec); err != nil {
			t.Fatalf("record is not JSON: %v\n%s", err, l)
		}
		// Nothing from a real run may claim to be a preview — that is the other
		// half of the dry-run marker being on every line.
		if rec.DryRun {
			t.Errorf("a live delete emitted dryRun:true:\n%s", l)
		}
		switch rec.DocEntry {
		case 54990:
			deletedOK = rec.Verified
		case 54991:
			skippedOK = strings.Contains(rec.Skipped, "already deleted")
		}
	}
	if !deletedOK {
		t.Error("54990 should have been deleted and verified")
	}
	if !skippedOK {
		t.Error("54991 should have been reported as already deleted")
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 1 {
		t.Errorf("exactly one DELETE, got %v", f.seenMethods())
	}
}

// TestDeleteBatchWhereEverythingIsAlreadyGone — the second run of a batch that
// succeeded. It must not prompt to delete zero drafts.
func TestDeleteBatchWhereEverythingIsAlreadyGone(t *testing.T) {
	withTTY(t, true)
	f := newFakeDraftSAP(t)
	provenanceRepo(t)

	stdout, stderr, err := execWrite(t, "", "--json", "delete", "draft", "54990", "54991")
	if err != nil {
		t.Fatalf("a batch that is entirely gone is not a failure: %v", err)
	}
	if strings.Contains(stderr, "Type 'yes'") {
		t.Errorf("there is nothing to confirm:\n%s", stderr)
	}
	if !strings.Contains(stderr, "already gone") {
		t.Errorf("say so out loud:\n%s", stderr)
	}
	if n := len(splitLines(stdout)); n != 2 {
		t.Errorf("the JSON stream still gets a record each, got %d:\n%s", n, stdout)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

// --- the provenance guard ---------------------------------------------------

func TestDeleteRefusesADraftThisCLIDidNotCreate(t *testing.T) {
	f := newFakeDraftSAP(t)
	provenanceRepo(t)
	f.putDraft(54990, nil)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected the provenance guard to refuse")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError (exit %d), got %T: %v", ExitRefused, err, err)
	}
	if ExitCodeFor(err) != ExitRefused {
		t.Errorf("a guard refusal is exit %d, got %d", ExitRefused, ExitCodeFor(err))
	}
	for _, want := range []string{
		"no record that this CLI created it",
		"re-key it from scratch",
		"--not-created-here",
		"git log -- queries/",
	} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}
	// The shared history is an intention, not a fact: no sap-writes.jsonl is on
	// main today, so telling the operator to `git pull` would train them to
	// override after a pull that changes nothing.
	if strings.Contains(refused.Msg, "git pull") {
		t.Errorf("refusal must not promise `git pull` delivers evidence:\n%s", refused.Msg)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

func TestDeleteProceedsOnACreationRecord(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now().Add(-2*time.Hour))

	stdout, stderr, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err != nil {
		t.Fatalf("delete failed: %v\nstderr: %s", err, stderr)
	}

	wantSeq := []string{
		"GET /b1s/v1/Drafts(54990)",    // pre-flight
		"GET /b1s/v1/Drafts(54990)",    // fresh read, just before the DELETE
		"DELETE /b1s/v1/Drafts(54990)", // the delete
		"GET /b1s/v1/Drafts(54990)",    // verification
	}
	got := f.seenMethods()
	if len(got) != len(wantSeq) {
		t.Fatalf("request sequence = %v, want %v", got, wantSeq)
	}
	for i := range wantSeq {
		if got[i] != wantSeq[i] {
			t.Errorf("request %d = %s, want %s", i, got[i], wantSeq[i])
		}
	}
	if !strings.Contains(stdout, "verified gone") {
		t.Errorf("stdout must confirm the verification: %s", stdout)
	}
	if !strings.Contains(stderr, "created here") || !strings.Contains(stderr, "sap-writes.jsonl:1") {
		t.Errorf("the summary must show WHICH log line vouched for it:\n%s", stderr)
	}

	lines := f.deleteLogLines(t)
	if len(lines) != 2 {
		t.Fatalf("a delete must log an intent and an outcome, got %d", len(lines))
	}
	intent, outcome := lines[0], lines[1]
	if intent["event"] != "intent" || outcome["event"] != "outcome" {
		t.Fatalf("intent must come first: %v", lines)
	}
	// The snapshot is the only surviving copy of what was destroyed. The shared
	// write log — which is committed, to a public repo — carries only its hash;
	// the contents live in the local snapshot log.
	sha, ok := intent["snapshot_sha256"].(string)
	if !ok || sha == "" {
		t.Fatalf("intent line must carry the snapshot hash: %v", intent)
	}
	if _, dup := outcome["snapshot_sha256"]; dup {
		t.Error("the outcome line must not repeat the snapshot hash")
	}
	for _, line := range lines {
		if _, leaked := line["snapshot"]; leaked {
			t.Errorf("snapshot contents must not reach the committed write log: %v", line)
		}
	}

	snap := f.recordedSnapshot(t)
	if fmt.Sprint(snap["DocEntry"]) != "54990" || snap["CardCode"] != "VENDA000939" {
		t.Errorf("snapshot lost the draft: %v", snap)
	}
	if got := f.snapshotEntries(t)[0]["sha256"]; got != sha {
		t.Errorf("the write log's hash %v does not point at the snapshot %v", sha, got)
	}
	for _, line := range lines {
		origin, ok := line["origin"].(map[string]interface{})
		if !ok {
			t.Fatalf("both lines must record the origin that authorised this: %v", line)
		}
		if origin["user"] != "tester" || fmt.Sprint(origin["line"]) != "1" {
			t.Errorf("origin must name the vouching line: %v", origin)
		}
		if _, has := line["payload"]; has {
			t.Errorf("a DELETE has no payload: %v", line)
		}
		if _, has := line["payload_omitted"]; has {
			t.Errorf("a DELETE has no payload, and nothing was omitted: %v", line)
		}
	}
}

func TestDeleteScansEveryOperatorsLog(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	// Created by a colleague, in a log this box only has because they committed it.
	seedCreation(t, operatorLog(root, "USER01"), "Drafts", "TESTDB", 54990, "USER01", time.Now())
	// Noise from another operator that has nothing to do with this draft.
	seedCreation(t, operatorLog(root, "USER06"), "Drafts", "TESTDB", 12345, "USER06", time.Now())

	_, stderr, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--other-operator")
	if err != nil {
		t.Fatalf("delete failed: %v\nstderr: %s", err, stderr)
	}
	if !strings.Contains(stderr, filepath.Join("queries", "USER01", "sap-writes.jsonl")) {
		t.Errorf("the summary must name the colleague's log:\n%s", stderr)
	}
}

// TestDeleteRefusesAnotherOperatorsDraft — a draft is owned by the login that
// made it, so it isn't even in this operator's Document Drafts list.
func TestDeleteRefusesAnotherOperatorsDraft(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "USER01"), "Drafts", "TESTDB", 54990, "USER01", time.Now())

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a refusal for another operator's draft")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"as USER01", "you are tester", "--other-operator"} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}

	// With the override it goes, and the override is recorded.
	f2 := newFakeDraftSAP(t)
	root2 := provenanceRepo(t)
	f2.putDraft(54990, nil)
	seedCreation(t, operatorLog(root2, "USER01"), "Drafts", "TESTDB", 54990, "USER01", time.Now())
	if _, stderr, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--other-operator"); err != nil {
		t.Fatalf("--other-operator should proceed: %v\n%s", err, stderr)
	}
	assertOverrideRecorded(t, f2, "other-operator")
}

// --- age and attachment -----------------------------------------------------

func TestDeleteRefusesAnOldDraft(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	created := time.Now().Add(-72*time.Hour - time.Minute)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", created)

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a refusal for a three-day-old draft")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"3 days ago", "--older-than 96h ("} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}
	// The suggestion must be pasteable as typed: "96h", not Go's "96h0m0s".
	if strings.Contains(refused.Msg, "96h0m0s") {
		t.Errorf("the suggested flag value must read like a flag value:\n%s", refused.Msg)
	}

	// A value that does not actually cover the age is still a refusal — the flag
	// is a statement about how old, not a switch.
	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--older-than", "48h"); err == nil {
		t.Error("--older-than 48h must not permit deleting a 72h-old draft")
	}

	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--older-than", "96h"); err != nil {
		t.Fatalf("--older-than 96h should proceed: %v", err)
	}
	// Recorded as the operator typed it, not as Go spells a Duration.
	assertOverrideRecorded(t, f, "older-than=96h")
}

// TestShortDuration — this string is written into the shared write log as the
// override the operator asserted, so it has to be a duration, not a prefix of
// one. Trimming Go's "25h30m0s" down blindly used to yield "25h3": not what
// anybody typed, not parseable, and silently wrong in the audit trail.
func TestShortDuration(t *testing.T) {
	cases := map[time.Duration]string{
		24 * time.Hour:                "24h",
		48 * time.Hour:                "48h",
		96 * time.Hour:                "96h",
		time.Hour:                     "1h",
		30 * time.Minute:              "30m0s",
		20 * time.Minute:              "20m0s",
		90 * time.Minute:              "1h30m0s",
		25*time.Hour + 30*time.Minute: "25h30m0s",
		48*time.Hour + 30*time.Minute: "48h30m0s",
		72*time.Hour + 10*time.Minute: "72h10m0s",
		time.Duration(0):              "0s",
		36*time.Hour + 30*time.Second: "36h0m30s",
	}
	for d, want := range cases {
		got := shortDuration(d)
		if got != want {
			t.Errorf("shortDuration(%v) = %q, want %q", d, got, want)
		}
		// Whatever it prints must read back as the same duration — the log line
		// and the command line have to agree.
		back, err := time.ParseDuration(got)
		if err != nil {
			t.Errorf("shortDuration(%v) = %q, which does not reparse: %v", d, got, err)
			continue
		}
		if back != d {
			t.Errorf("shortDuration(%v) = %q, which reparses as %v", d, got, back)
		}
	}
}

// TestOlderThanOverrideIsRecordedAsTyped — the recorded override is the whole
// justification for having one, so a value carrying minutes must survive into
// the log intact.
func TestOlderThanOverrideIsRecordedAsTyped(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now().Add(-25*time.Hour))

	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--older-than", "25h30m"); err != nil {
		t.Fatalf("--older-than 25h30m covers a 25h-old draft: %v", err)
	}
	assertOverrideRecorded(t, f, "older-than=25h30m0s")

	for _, e := range f.deleteLogLines(t) {
		overrides, _ := e["overrides"].([]interface{})
		for _, o := range overrides {
			s, _ := o.(string)
			if !strings.HasPrefix(s, "older-than=") {
				continue
			}
			if _, err := time.ParseDuration(strings.TrimPrefix(s, "older-than=")); err != nil {
				t.Errorf("the recorded override %q is not a duration: %v", s, err)
			}
		}
	}
}

func TestDeleteRefusesADraftWithAnAttachment(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, map[string]interface{}{"AttachmentEntry": 170187})
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a refusal for a draft with a file attached")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"file attached", "AttachmentEntry 170187", "--with-attachment"} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}

	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--with-attachment"); err != nil {
		t.Fatalf("--with-attachment should proceed: %v", err)
	}
	assertOverrideRecorded(t, f, "with-attachment")
}

// assertOverrideRecorded checks the write log kept the override that permitted
// the delete — a recorded override is the whole point of having one.
func assertOverrideRecorded(t *testing.T, f *fakeDraftSAP, want string) {
	t.Helper()
	lines := f.deleteLogLines(t)
	if len(lines) == 0 {
		t.Fatal("no DELETE was logged")
	}
	for _, line := range lines {
		raw, ok := line["overrides"].([]interface{})
		if !ok {
			t.Fatalf("line must record overrides: %v", line)
		}
		found := false
		for _, o := range raw {
			if o == want {
				found = true
			}
		}
		if !found {
			t.Errorf("overrides must include %q, got %v", want, raw)
		}
	}
}

// --- the --not-created-here override ----------------------------------------

func TestNotCreatedHereIsOneDraftAndOneHuman(t *testing.T) {
	t.Run("refuses a batch", func(t *testing.T) {
		newFakeDraftSAP(t)
		_, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "--not-created-here")
		if err == nil || !strings.Contains(err.Error(), "one at a time") {
			t.Errorf("want a one-at-a-time refusal, got: %v", err)
		}
	})

	t.Run("refuses --yes", func(t *testing.T) {
		newFakeDraftSAP(t)
		_, _, err := execWrite(t, "", "delete", "draft", "54990", "--not-created-here", "--yes")
		if err == nil || !strings.Contains(err.Error(), "needs a person at the prompt") {
			t.Errorf("want a person-at-the-prompt refusal, got: %v", err)
		}
	})

	t.Run("refuses a non-terminal stdin", func(t *testing.T) {
		withTTY(t, false)
		newFakeDraftSAP(t)
		_, _, err := execWrite(t, "", "delete", "draft", "54990", "--not-created-here")
		if err == nil || !strings.Contains(err.Error(), "needs a person at the prompt") {
			t.Errorf("want a person-at-the-prompt refusal, got: %v", err)
		}
	})

	t.Run("proceeds for one draft with a typed yes", func(t *testing.T) {
		withTTY(t, true)
		f := newFakeDraftSAP(t)
		provenanceRepo(t)
		f.putDraft(54990, nil)

		_, stderr, err := execWrite(t, "yes\n", "delete", "draft", "54990", "--not-created-here")
		if err != nil {
			t.Fatalf("delete failed: %v\nstderr: %s", err, stderr)
		}
		if !strings.Contains(stderr, "created here") || !strings.Contains(stderr, "NO") {
			t.Errorf("the summary must say out loud that this CLI did not create it:\n%s", stderr)
		}
		assertOverrideRecorded(t, f, "not-created-here")
	})
}

// --- confirmation -----------------------------------------------------------

func TestDeleteRefusesWithoutATerminal(t *testing.T) {
	withTTY(t, false)
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	_, stderr, err := execWrite(t, "", "delete", "draft", "54990")
	if err == nil {
		t.Fatal("expected a refusal without --yes on a non-terminal stdin")
	}
	if !strings.Contains(err.Error(), "--yes") || !strings.Contains(err.Error(), "not a terminal") {
		t.Errorf("refusal must name --yes and the terminal, got: %v", err)
	}
	if !strings.Contains(stderr, "About to DELETE from SAP:") {
		t.Errorf("the preview must still be shown:\n%s", stderr)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

func TestDeleteConfirmationContract(t *testing.T) {
	cases := []struct {
		typed   string
		deletes int
	}{
		{"yes\n", 1},
		{"  yes  \n", 1},
		{"y\n", 0},
		{"YES\n", 0},
		{"yes please\n", 0},
		{"\n", 0},
		{"", 0},
	}
	for _, tc := range cases {
		t.Run(strings.TrimSpace(tc.typed)+"|", func(t *testing.T) {
			withTTY(t, true)
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)
			f.putDraft(54990, nil)
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

			_, stderr, err := execWrite(t, tc.typed, "delete", "draft", "54990")
			got := countMethod(f.seenMethods(), "DELETE")
			if got != tc.deletes {
				t.Errorf("typed %q → %d DELETEs, want %d (err: %v)", tc.typed, got, tc.deletes, err)
			}
			if tc.deletes == 0 && err == nil {
				t.Errorf("typed %q must abort with an error", tc.typed)
			}
			for _, want := range []string{"DELETE 1 draft(s)", "cannot be undone", "TESTDB"} {
				if !strings.Contains(stderr, want) {
					t.Errorf("the prompt must contain %q, got:\n%s", want, stderr)
				}
			}
		})
	}
}

// TestDraftPromptIsUnchanged pins the sentence the other three write commands
// use. Splitting confirmWrite must not have moved a byte of it.
func TestDraftPromptIsUnchanged(t *testing.T) {
	withTTY(t, true)
	newFakeSAP(t)

	_, stderr, _ := execWrite(t, "no\n", "draft", "order", "--data", `{"CardCode":"C0001"}`)
	if !strings.Contains(stderr, "Type 'yes' to send this write to TESTDB: ") {
		t.Errorf("the draft/post/patch prompt must be byte-identical, got:\n%s", stderr)
	}
	if !strings.Contains(stderr, "About to WRITE to SAP:") {
		t.Errorf("the draft/post/patch preview header must be unchanged, got:\n%s", stderr)
	}
}

// --- batches ----------------------------------------------------------------

func TestDeleteBatchPreviewsAllAndAsksOnce(t *testing.T) {
	withTTY(t, true)
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	for _, n := range []int64{54990, 54991, 54992} {
		f.putDraft(n, nil)
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
	}

	_, stderr, err := execWrite(t, "yes\n", "delete", "draft", "54990", "54991", "54992")
	if err != nil {
		t.Fatalf("batch failed: %v\nstderr: %s", err, stderr)
	}
	if n := strings.Count(stderr, "  request : DELETE "); n != 3 {
		t.Errorf("the preview must list all three requests, got %d:\n%s", n, stderr)
	}
	if !strings.Contains(stderr, "drafts  : 3") {
		t.Errorf("the preview must name the count:\n%s", stderr)
	}
	if n := strings.Count(stderr, "to DELETE 3 draft(s)"); n != 1 {
		t.Errorf("exactly one confirmation for the batch, got %d:\n%s", n, stderr)
	}
	// Before they type yes, the operator is told where the record goes and where
	// the CONTENTS go — they are two different files now, and only one of them is
	// shared. This test stands outside any checkout, so the preview must say the
	// team will NOT see it rather than promising they will.
	for _, want := range []string{
		"record  :", "OUTSIDE any checkout", "the team will not see it",
		"contents:", "party, bill number, totals, line prices", "THIS machine only",
		f.logPath, os.Getenv("SAPB1_SNAPSHOT_LOG"),
	} {
		if !strings.Contains(stderr, want) {
			t.Errorf("the preview must say where the record and the contents land (%q):\n%s", want, stderr)
		}
	}
	if strings.Contains(stderr, "shared with the team") {
		t.Errorf("nothing here reaches the team — the preview must not say it does:\n%s", stderr)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 3 {
		t.Errorf("want 3 DELETEs, got %v", f.seenMethods())
	}
	// 3 pre-flight GETs, then GET/DELETE/GET per draft.
	if n := countMethod(f.seenMethods(), "GET"); n != 3+6 {
		t.Errorf("want 9 GETs, got %v", f.seenMethods())
	}
}

func TestDeleteBatchStopsAtTheFirstFailure(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	for _, n := range []int64{54990, 54991, 54992} {
		f.putDraft(n, nil)
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
	}
	// Fail the second one: SAP rejects it outright.
	f.failDelete["Drafts(54991)"] = http.StatusBadRequest

	stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "54991", "54992", "--yes")
	if err == nil {
		t.Fatal("expected the batch to fail")
	}
	var apiErr *errs.APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("the underlying error must survive for errors.As, got %T: %v", err, err)
	}
	for _, want := range []string{"deleted (1)", "failed (1)", "not attempted (1)", "54992"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("the tally must contain %q, got:\n%s", want, err.Error())
		}
	}
	if n := len(splitLines(stdout)); n != 3 {
		t.Errorf("the JSON stream must have a record per draft, got %d:\n%s", n, stdout)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 2 {
		t.Errorf("54992 must never be attempted, got %v", f.seenMethods())
	}
}

// TestDeleteBatchTallyDoesNotCallAnUnverifiedDeleteAFailure — the tally is what
// an operator reads at the bottom of a fifty-draft run, and it used to
// contradict the line printed immediately above it: "Deleted Drafts(54991) …
// (HTTP 204) — could not verify" and then "failed (1) : 54991". SAP answered
// that DELETE; the draft is almost certainly gone. An operator who trusts the
// tally re-keys a document that does not need re-keying, which is the exact cost
// this command exists to avoid.
func TestDeleteBatchTallyDoesNotCallAnUnverifiedDeleteAFailure(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	for _, n := range []int64{54990, 54991, 54992} {
		f.putDraft(n, nil)
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
	}
	// Kill the connection on the read-back after 54991's DELETE, and only that
	// one: 54990 must still verify normally. Armed during 54991's fresh read
	// (the second GET of that key), which is the last event before its DELETE.
	gets := 0
	f.beforeGet = func(f *fakeDraftSAP, key string) {
		if key != "Drafts(54991)" {
			return
		}
		gets++
		if gets == 2 {
			f.mu.Lock()
			f.dropVerify = true
			f.mu.Unlock()
		}
	}

	stdout, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "54992", "--yes")
	if err == nil {
		t.Fatal("expected the batch to stop at the draft it could not verify")
	}
	var verify *errs.WriteVerifyError
	if !errors.As(err, &verify) {
		t.Fatalf("expected *errs.WriteVerifyError, got %T: %v", err, err)
	}
	if code := ExitCodeFor(err); code != ExitVerifyFailed {
		t.Errorf("exit code = %d, want %d", code, ExitVerifyFailed)
	}
	if !strings.Contains(stdout, "Deleted Drafts(54991)") || !strings.Contains(stdout, "could not verify") {
		t.Fatalf("the headline must say SAP answered the DELETE, got:\n%s", stdout)
	}
	tally := err.Error()
	if strings.Contains(tally, "failed (1)") {
		t.Errorf("a DELETE SAP answered 204 is not a failure; the tally contradicts the line above it:\n%s", tally)
	}
	for _, want := range []string{"deleted (1)", "unverified (1)", "54991", "re-running is safe", "not attempted (1)", "54992"} {
		if !strings.Contains(tally, want) {
			t.Errorf("the tally must contain %q, got:\n%s", want, tally)
		}
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 2 {
		t.Errorf("54992 must never be attempted, got %v", f.seenMethods())
	}
}

// TestDeleteBatchTallyDoesNotCountAVanishedDraftAsDeleted — a draft that goes
// between the preview and the DELETE returns a skip: no request is sent and no
// log line exists for it. It used to land in the "deleted" column anyway, so the
// tally at the bottom of a fifty-draft run told the operator a DocEntry nobody
// touched had been destroyed — and the write log, the only record that would
// settle it, has nothing to say about that number.
func TestDeleteBatchTallyDoesNotCountAVanishedDraftAsDeleted(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	for _, n := range []int64{54990, 54991, 54992} {
		f.putDraft(n, nil)
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
	}
	// The middle one is deleted by somebody else between the preview and its own
	// fresh read; the third is rejected by SAP.
	gets := 0
	f.beforeGet = func(f *fakeDraftSAP, key string) {
		if key != "Drafts(54991)" {
			return
		}
		gets++
		if gets == 2 {
			f.mu.Lock()
			delete(f.objects, "Drafts(54991)")
			f.mu.Unlock()
		}
	}
	f.failDelete["Drafts(54992)"] = http.StatusBadRequest

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "54992", "--yes")
	if err == nil {
		t.Fatal("expected the batch to fail on the third draft")
	}
	tally := err.Error()
	for _, want := range []string{"deleted (1)", "skipped (1)", "failed (1)"} {
		if !strings.Contains(tally, want) {
			t.Errorf("the tally must contain %q, got:\n%s", want, tally)
		}
	}
	if strings.Contains(tally, "deleted (2)") {
		t.Errorf("a draft that was already gone was never deleted here:\n%s", tally)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 2 {
		t.Errorf("only 54990 and 54992 may be attempted, got %v", f.seenMethods())
	}
	// The write log agrees with the tally: two DocEntries, four lines.
	if n := len(f.deleteLogLines(t)); n != 4 {
		t.Errorf("want an intent and an outcome for each DELETE sent, got %d", n)
	}
}

func TestDeleteBatchCap(t *testing.T) {
	newFakeDraftSAP(t)
	args := []string{"delete", "draft"}
	for i := 1; i <= maxDeleteBatch+1; i++ {
		args = append(args, fmt.Sprint(60000+i))
	}
	_, _, err := execWrite(t, "", append(args, "--yes")...)
	if err == nil || !strings.Contains(err.Error(), "Split the list") {
		t.Errorf("want a batch-cap refusal, got: %v", err)
	}
}

// --- TOCTOU -----------------------------------------------------------------

// TestDeleteRechecksJustBeforeSending — a fifty-draft batch runs for minutes
// while Accounts is Adding drafts in the SAP client.
func TestDeleteRechecksJustBeforeSending(t *testing.T) {
	t.Run("a draft Added mid-batch stops it", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		for _, n := range []int64{54990, 54991} {
			f.putDraft(n, nil)
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
		}
		preflightDone := false
		f.beforeGet = func(f *fakeDraftSAP, key string) {
			if key != "Drafts(54991)" {
				return
			}
			if !preflightDone {
				preflightDone = true
				return
			}
			f.putDraft(54991, map[string]interface{}{"DocumentStatus": "bost_Close"})
		}

		_, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "--yes")
		if err == nil {
			t.Fatal("expected the batch to stop when a draft was Added under it")
		}
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
		}
		if !strings.Contains(err.Error(), "was Open a moment ago") {
			t.Errorf("the message must explain what changed, got: %v", err)
		}
		if n := countMethod(f.seenMethods(), "DELETE"); n != 1 {
			t.Errorf("only 54990 may be deleted, got %v", f.seenMethods())
		}
	})

	// --closed says "I looked at this draft and it was already closed off". It
	// does not say "and I accept whatever happens to it in the next four
	// minutes" — so a draft a colleague Adds mid-batch must still stop the run,
	// destroying no trail behind a document that now exists.
	t.Run("a draft Added mid-batch stops it even with --closed", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		// 54990 was closed off by hand (which is what --closed is for); 54991 is
		// Open and gets Added while the batch runs.
		f.putDraft(54990, map[string]interface{}{"DocumentStatus": "bost_Close"})
		f.putDraft(54991, nil)
		for _, n := range []int64{54990, 54991} {
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
		}
		preflightDone := false
		f.beforeGet = func(f *fakeDraftSAP, key string) {
			if key != "Drafts(54991)" {
				return
			}
			if !preflightDone {
				preflightDone = true
				return
			}
			f.putDraft(54991, map[string]interface{}{"DocumentStatus": "bost_Close"})
		}

		_, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "--yes", "--closed")
		if err == nil {
			t.Fatal("--closed must not switch off the just-before-send re-check")
		}
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
		}
		if !strings.Contains(err.Error(), "was Open a moment ago") {
			t.Errorf("the message must explain what changed, got: %v", err)
		}
		if n := countMethod(f.seenMethods(), "DELETE"); n != 1 {
			t.Errorf("only the draft that did not change may be deleted, got %v", f.seenMethods())
		}
	})

	// The other half: a draft that was closed when the operator previewed it and
	// is still closed must go, or --closed would be useless.
	t.Run("an unchanged closed draft still deletes under --closed", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.putDraft(54990, map[string]interface{}{"DocumentStatus": "bost_Close"})
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

		if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--closed"); err != nil {
			t.Fatalf("a draft whose status has not moved must delete: %v", err)
		}
	})

	t.Run("a draft deleted mid-batch is skipped", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		for _, n := range []int64{54990, 54991} {
			f.putDraft(n, nil)
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
		}
		preflightDone := false
		f.beforeGet = func(f *fakeDraftSAP, key string) {
			if key != "Drafts(54991)" {
				return
			}
			if !preflightDone {
				preflightDone = true
				return
			}
			f.mu.Lock()
			delete(f.objects, "Drafts(54991)")
			f.mu.Unlock()
		}

		stdout, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "--yes")
		if err != nil {
			t.Fatalf("a draft that vanished mid-batch must be skipped, not fatal: %v", err)
		}
		if !strings.Contains(stdout, "already gone") {
			t.Errorf("stdout must say it was already gone:\n%s", stdout)
		}
	})
}

// --- the closed guard -------------------------------------------------------

func TestDeleteRefusesAClosedDraft(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, map[string]interface{}{"DocumentStatus": "bost_Close"})
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a closed draft to be refused")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	for _, want := range []string{"not bost_Open", "already Added", "--closed"} {
		if !strings.Contains(refused.Msg, want) {
			t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
		}
	}

	if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--closed"); err != nil {
		t.Fatalf("--closed should proceed: %v", err)
	}
	assertOverrideRecorded(t, f, "closed")
}

// TestDeleteSaysWhenTheStatusCheckDoesNotApply — PaymentDrafts (OPDF) carries no
// DocumentStatus at all. That must be said out loud, not silently skipped.
func TestDeleteSaysWhenTheStatusCheckDoesNotApply(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.put("PaymentDrafts", 812, map[string]interface{}{
		"DocNum": 1124246744, "DocObjectCode": "bopot_IncomingPayments", "DocType": "rCustomer",
		"CardCode": "CUSTA000883", "CardName": "SHRI JEE TRADING CO", "TransferSum": 2800000,
	})
	seedCreation(t, operatorLog(root, "tester"), "PaymentDrafts", "TESTDB", 812, "tester", time.Now())

	_, stderr, err := execWrite(t, "", "delete", "payment-draft", "812", "--yes")
	if err != nil {
		t.Fatalf("delete failed: %v\nstderr: %s", err, stderr)
	}
	if !strings.Contains(stderr, "already-Added check does not apply") {
		t.Errorf("the missing check must announce itself:\n%s", stderr)
	}
	if !strings.Contains(stderr, "SHRI JEE TRADING CO") {
		t.Errorf("the summary must show live PaymentDrafts fields:\n%s", stderr)
	}
}

// TestPaymentDraftProvenanceIsPerEntitySet — a Drafts creation line must not
// authorise deleting the PaymentDrafts row with the same DocEntry. They are
// different SAP tables that share a numbering space.
func TestPaymentDraftProvenanceIsPerEntitySet(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.put("PaymentDrafts", 77, map[string]interface{}{"CardCode": "V10000"})
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 77, "tester", time.Now())

	_, _, err := execWrite(t, "", "delete", "payment-draft", "77", "--yes")
	if err == nil {
		t.Fatal("a Drafts creation line must not vouch for a PaymentDrafts row")
	}
	var refused *errs.RefusedError
	if !errors.As(err, &refused) {
		t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

// --- verification -----------------------------------------------------------

func TestDeleteWhenTheDraftStillReadsBack(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	f.keepAfterDelete = true
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a verification failure")
	}
	var verifyErr *errs.WriteVerifyError
	if !errors.As(err, &verifyErr) {
		t.Fatalf("expected *errs.WriteVerifyError, got %T: %v", err, err)
	}
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Errorf("want exit %d, got %d", ExitVerifyFailed, ExitCodeFor(err))
	}
	for _, want := range []string{"still reads back", "Re-running this command is safe"} {
		if !strings.Contains(verifyErr.Msg, want) {
			t.Errorf("message must contain %q, got:\n%s", want, verifyErr.Msg)
		}
	}
}

func TestDeleteWhenTheVerifyingReadFails(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	f.dropVerify = true
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	stdout, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected a verification failure")
	}
	var verifyErr *errs.WriteVerifyError
	if !errors.As(err, &verifyErr) {
		t.Fatalf("expected *errs.WriteVerifyError, got %T: %v", err, err)
	}
	// A failed read-back must NOT read as "nothing was sent": SAP answered the
	// DELETE, and exit 5 is documented fleet-wide as retryable-because-nothing-
	// happened.
	var netErr *errs.NetworkError
	if errors.As(err, &netErr) {
		t.Error("a failed verification must not be a NetworkError")
	}
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Errorf("want exit %d, got %d", ExitVerifyFailed, ExitCodeFor(err))
	}
	if !strings.Contains(verifyErr.Msg, "could not verify") {
		t.Errorf("message must say it could not verify, got:\n%s", verifyErr.Msg)
	}
	if !strings.Contains(stdout, "Deleted Drafts(54990)") {
		t.Errorf("the delete itself must still be reported on stdout:\n%s", stdout)
	}
}

// TestDeleteVerificationRefusesABodyThatIsNotTheRow — the read-back after a
// DELETE branched on "SAP answered 2xx" alone, and client.GetEntity calls any
// 2xx "found". A gateway answering 200 for a keyed path — the shape the two
// reads BEFORE the delete already refuse — therefore read as "the draft is still
// there": the operator was sent to Document Drafts to look for a row SAP had
// already removed, and the tally filed it under failed as though the DELETE had
// not taken.
//
// "Still present" and "something else answered" are different facts and get
// different sentences. The second is an unverified delete, which is what it is.
func TestDeleteVerificationRefusesABodyThatIsNotTheRow(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	// Preflight and the fresh read see the draft; the verifying GET gets a
	// gateway's idea of an answer, with a 200 on it.
	gets := 0
	f.beforeGet = func(f *fakeDraftSAP, key string) {
		if key != "Drafts(54990)" {
			return
		}
		gets++
		if gets == 3 {
			f.putRaw("Drafts", 54990, `{"DocEntry":99999,"CardCode":"V10000"}`)
		}
	}

	stdout, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("a read-back that is not the row cannot verify anything")
	}
	var verify *errs.WriteVerifyError
	if !errors.As(err, &verify) {
		t.Fatalf("want *errs.WriteVerifyError (exit %d), got %T: %v", ExitVerifyFailed, err, err)
	}
	if ExitCodeFor(err) != ExitVerifyFailed {
		t.Errorf("want exit %d, got %d", ExitVerifyFailed, ExitCodeFor(err))
	}
	for _, want := range []string{"could not verify", "is not that draft row", "DocEntry is 99999"} {
		if !strings.Contains(verify.Msg, want) {
			t.Errorf("the message must contain %q, got:\n%s", want, verify.Msg)
		}
	}
	if strings.Contains(verify.Msg, "still reads back") {
		t.Errorf("nothing here shows the draft is still there:\n%s", verify.Msg)
	}
	if !strings.Contains(stdout, "Deleted Drafts(54990)") {
		t.Errorf("SAP answered the DELETE; stdout must still say so:\n%s", stdout)
	}
}

func TestDeleteUnknownOutcome(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	for _, n := range []int64{54990, 54991, 54992} {
		f.putDraft(n, nil)
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", n, "tester", time.Now())
	}
	f.stallDelete["Drafts(54991)"] = true
	// Keep the stall short: this is the one test that has to wait out a timeout.
	t.Setenv("SAPB1_TIMEOUT", "1")

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "54991", "54992", "--yes")
	if err == nil {
		t.Fatal("expected an unknown outcome")
	}
	var unknown *errs.WriteOutcomeUnknownError
	if !errors.As(err, &unknown) {
		t.Fatalf("expected *errs.WriteOutcomeUnknownError, got %T: %v", err, err)
	}
	if ExitCodeFor(err) != ExitWriteUnknown {
		t.Errorf("want exit %d, got %d", ExitWriteUnknown, ExitCodeFor(err))
	}
	for _, want := range []string{"query Drafts", "cannot create a duplicate"} {
		if !strings.Contains(unknown.Msg, want) {
			t.Errorf("delete advice must contain %q, got:\n%s", want, unknown.Msg)
		}
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 2 {
		t.Errorf("54992 must never be attempted, got %v", f.seenMethods())
	}
}

// --- output shape -----------------------------------------------------------

func TestDeleteRefusesCSVWithDeleteWording(t *testing.T) {
	newFakeDraftSAP(t)
	_, _, err := execWrite(t, "", "--csv", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("expected --csv to be refused")
	}
	if !strings.Contains(err.Error(), "one JSON object per draft") {
		t.Errorf("the delete --csv message must be delete-shaped, got: %v", err)
	}
	if strings.Contains(err.Error(), "created object") {
		t.Errorf("a delete creates nothing — the message must not say so: %v", err)
	}
}

// --- the snapshot allowlist -------------------------------------------------

// TestSnapshotIsAStrictAllowlist — the write log is designed to be committed,
// and a live PaymentDrafts row carries the vendor's bank account, the transfer
// GL account and cheque rows. None of that may ride along.
func TestSnapshotIsAStrictAllowlist(t *testing.T) {
	obj := map[string]interface{}{
		"DocEntry":           json.Number("812"),
		"DocNum":             json.Number("112424674412345678"),
		"CardCode":           "CUSTA000883",
		"CardName":           "SHRI JEE TRADING CO",
		"TransferSum":        json.Number("2800000"),
		"TransferAccount":    "2201101",
		"BankAccount":        "9495700012",
		"CheckAccount":       "2201105",
		"PayToBankAccountNo": "50200012345678",
		"PaymentChecks":      []interface{}{map[string]interface{}{"CheckNumber": json.Number("445566"), "BankCode": "BARB"}},
		"PaymentCreditCards": []interface{}{map[string]interface{}{"CreditCard": json.Number("7")}},
		"PaymentAccounts": []interface{}{
			map[string]interface{}{"LineNum": json.Number("0"), "SumPaid": json.Number("500"), "AccountCode": "2201101"},
		},
		"PaymentInvoices": []interface{}{
			map[string]interface{}{"LineNum": json.Number("0"), "DocEntry": json.Number("99"), "SumApplied": json.Number("2800000"), "DistributionRule": "X"},
		},
	}

	snap := snapshotOf(obj, kindPaymentDraft)
	text := string(snap)
	for _, forbidden := range []string{
		"PaymentChecks", "PaymentCreditCards", "TransferAccount", "AccountCode",
		"BankAccount", "CheckAccount", "PayToBankAccountNo", "DistributionRule",
	} {
		if strings.Contains(text, forbidden) {
			t.Errorf("snapshot must not carry %q:\n%s", forbidden, text)
		}
	}
	for _, wanted := range []string{"DocEntry", "CardName", "TransferSum", "PaymentInvoices", "SumApplied", "SumPaid"} {
		if !strings.Contains(text, wanted) {
			t.Errorf("snapshot must carry %q:\n%s", wanted, text)
		}
	}
	// The 18-digit DocNum must survive as SAP sent it, not as a float.
	if !strings.Contains(text, "112424674412345678") {
		t.Errorf("snapshot must keep numbers exact:\n%s", text)
	}
}

// --- the catalog agrees -----------------------------------------------------

// TestCatalogAgreesTheseSetsCanBeDeleted checks the Service Layer catalog
// actually lists DELETE on the two sets this command addresses, without going
// anywhere near supportsEntityOperation (which must stay POST/PATCH-only).
func TestCatalogAgreesTheseSetsCanBeDeleted(t *testing.T) {
	for _, kind := range []draftKind{kindDraft, kindPaymentDraft} {
		svc, ok := catalog.Find(kind.EntitySet)
		if !ok {
			t.Fatalf("%s is not in the catalog", kind.EntitySet)
		}
		found := false
		for _, op := range svc.Operations {
			if strings.EqualFold(op.Method, "DELETE") && op.Name == svc.Service+"(id)" {
				found = true
			}
		}
		if !found {
			t.Errorf("the catalog does not list DELETE %s(id)", kind.EntitySet)
		}
	}
}

// --- what answered is not always SAP ----------------------------------------

// TestDeleteRefusesABodyThatIsNotTheRow — client.GetEntity calls any 2xx
// "found" and hands the body over. Every guard below reads its signal off that
// object and treats an absent field as "does not apply", so a 200 carrying an
// HTML page or an {"error":…} envelope used to make the closed check, the
// attachment check and the CreationDate cross-check all pass vacuously, print a
// summary listing no fields at all, record an empty snapshot — and then send the
// DELETE.
//
// Not a hypothetical: SAP sits behind Traefik and an ssh bridge here, and a
// mis-routed proxy answering 200 for a keyed path is exactly how it arrives.
func TestDeleteRefusesABodyThatIsNotTheRow(t *testing.T) {
	cases := []struct {
		name string
		body string
		says string
	}{
		{"an HTML page from a gateway", "<html><body>502 Bad Gateway</body></html>", "not a JSON object"},
		{"a Service Layer error envelope", sapNotFound, "error envelope"},
		{"a different draft entirely", `{"DocEntry":99999,"CardCode":"V10000","DocumentStatus":"bost_Open"}`, "DocEntry is 99999"},
		{"an object with no DocEntry", `{"CardCode":"V10000"}`, "no DocEntry"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)
			f.putRaw("Drafts", 54990, tc.body)
			// Provenance would otherwise refuse first; this test is about the read.
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

			_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
			if err == nil {
				t.Fatal("a 200 that is not the row must stop the delete")
			}
			var apiErr *errs.APIError
			if !errors.As(err, &apiErr) {
				t.Fatalf("want *errs.APIError (exit 6), got %T: %v", err, err)
			}
			for _, want := range []string{"is not that draft row", tc.says, "Nothing was deleted", "bridge, a tunnel or a proxy"} {
				if !strings.Contains(apiErr.Msg, want) {
					t.Errorf("the message must contain %q, got: %s", want, apiErr.Msg)
				}
			}
			if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
				t.Errorf("no DELETE may be sent: %v", f.seenMethods())
			}
			if lines := f.deleteLogLines(t); len(lines) != 0 {
				t.Errorf("nothing was attempted, so nothing may be logged: %v", lines)
			}
		})
	}
}

// TestSnapshotRecordsTheRowAsItReadJustBeforeTheDelete — the snapshot is the
// only surviving copy of what was destroyed, so it has to be a copy of what was
// destroyed, not of what the operator was shown minutes earlier.
//
// A fifty-draft batch runs for minutes over the bridge while Accounts works in
// the SAP client. An edit that leaves DocumentStatus alone — a line added, a
// total corrected, the vendor's bill number fixed — passes the just-before-send
// status re-check, and the log used to record the PRE-edit version under a hash
// that matched nothing anybody could produce from the row.
func TestSnapshotRecordsTheRowAsItReadJustBeforeTheDelete(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	// Between the preflight read and the fresh read, somebody corrects the total
	// and the bill number. DocumentStatus does not move, so nothing stops the
	// delete — and nothing should.
	gets := 0
	f.beforeGet = func(f *fakeDraftSAP, key string) {
		if key != "Drafts(54990)" {
			return
		}
		gets++
		if gets == 2 {
			f.putDraft(54990, map[string]interface{}{
				"DocTotal":  260000,
				"NumAtCard": "2606000806-REV",
			})
		}
	}

	stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--yes")
	if err != nil {
		t.Fatalf("delete failed: %v", err)
	}

	snap := f.recordedSnapshot(t)
	if fmt.Sprint(snap["DocTotal"]) != "260000" || snap["NumAtCard"] != "2606000806-REV" {
		t.Errorf("the snapshot is the pre-edit row; it must be the one that was destroyed: %v", snap)
	}

	// And the hash in the shared write log is the hash of THOSE bytes: the log
	// line and the row SAP had a moment before have to be the same thing.
	raw, err := os.ReadFile(os.Getenv("SAPB1_SNAPSHOT_LOG"))
	if err != nil {
		t.Fatalf("reading the snapshot log: %v", err)
	}
	var line struct {
		SHA256   string          `json:"sha256"`
		Snapshot json.RawMessage `json:"snapshot"`
	}
	if err := json.Unmarshal([]byte(splitLines(string(raw))[0]), &line); err != nil {
		t.Fatalf("snapshot line is not JSON: %v", err)
	}
	want := fmt.Sprintf("%x", sha256.Sum256(line.Snapshot))
	if line.SHA256 != want {
		t.Errorf("the snapshot log's own hash %q does not match its bytes (%q)", line.SHA256, want)
	}
	intent := f.deleteLogLines(t)[0]
	if intent["snapshot_sha256"] != want {
		t.Errorf("the write log recorded %v — the hash of the FRESH row is %q", intent["snapshot_sha256"], want)
	}
	// The operator's own receipt on stdout says the same.
	var rec struct {
		SnapshotSHA256 string                 `json:"snapshotSha256"`
		Snapshot       map[string]interface{} `json:"snapshot"`
	}
	if err := json.Unmarshal([]byte(splitLines(stdout)[0]), &rec); err != nil {
		t.Fatalf("record is not JSON: %v", err)
	}
	if rec.SnapshotSHA256 != want || fmt.Sprint(rec.Snapshot["DocTotal"]) != "260000" {
		t.Errorf("the --json receipt must carry the same row and hash: %+v", rec)
	}
}

// TestDeleteRefusesAGarbledFreshRead — the same check on the read immediately
// before the DELETE. Preflight saw a real draft; something in front of SAP then
// started answering for it. The DELETE must not go out on the strength of a
// reading taken minutes earlier.
func TestDeleteRefusesAGarbledFreshRead(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	// The first GET (preflight) sees the draft; every later one gets a gateway.
	gets := 0
	f.beforeGet = func(f *fakeDraftSAP, key string) {
		gets++
		if gets >= 2 {
			f.putRaw("Drafts", 54990, "<html>503</html>")
		}
	}

	_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes")
	if err == nil {
		t.Fatal("a garbled fresh read must stop the delete")
	}
	var apiErr *errs.APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("want *errs.APIError, got %T: %v", err, err)
	}
	if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
		t.Errorf("no DELETE may be sent: %v", f.seenMethods())
	}
}

// --- a refusal is an answer, and --json has to carry it ----------------------

// refusalRecord is the shape a batch caller reads off the JSON stream.
type refusalRecord struct {
	DryRun         bool     `json:"dryRun"`
	DocEntry       int64    `json:"docEntry"`
	EntitySet      string   `json:"entitySet"`
	CompanyDB      string   `json:"companyDb"`
	Method         string   `json:"method"`
	URL            string   `json:"url"`
	Verified       bool     `json:"verified"`
	CreatedHere    bool     `json:"createdHere"`
	Skipped        string   `json:"skipped"`
	Refused        []string `json:"refused"`
	Reason         string   `json:"reason"`
	SuggestedFlags []string `json:"suggestedFlags"`
}

func parseRefusalRecords(t *testing.T, stdout string) []refusalRecord {
	t.Helper()
	var out []refusalRecord
	for _, l := range splitLines(stdout) {
		var rec refusalRecord
		if err := json.Unmarshal([]byte(l), &rec); err != nil {
			t.Fatalf("the JSON stream is not JSON: %v\n%s", err, l)
		}
		out = append(out, rec)
	}
	return out
}

// TestRefusalIsMachineReadable — every guard refusal used to write its
// explanation to stderr as prose and leave stdout EMPTY, even with --json. The
// batch tooling this command exists for runs fifty drafts at a time; when one of
// the fifty tripped a guard, the caller got exit 9 and zero bytes — no DocEntry,
// no reason, nothing to journal or to build the follow-up command from.
func TestRefusalIsMachineReadable(t *testing.T) {
	t.Run("no provenance, --yes", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		provenanceRepo(t) // empty: nothing vouches for anything
		f.putDraft(54990, nil)

		stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--yes")
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("want *errs.RefusedError (exit 9), got %T: %v", err, err)
		}
		recs := parseRefusalRecords(t, stdout)
		if len(recs) != 1 {
			t.Fatalf("want one record for the refused draft, got %d:\n%s", len(recs), stdout)
		}
		rec := recs[0]
		if rec.DocEntry != 54990 || rec.EntitySet != "Drafts" || rec.CompanyDB != "TESTDB" {
			t.Errorf("the record must identify the draft: %+v", rec)
		}
		if len(rec.Refused) != 1 || rec.Refused[0] != "provenance" {
			t.Errorf("refused = %v, want [provenance]", rec.Refused)
		}
		if len(rec.SuggestedFlags) != 1 || rec.SuggestedFlags[0] != "--not-created-here" {
			t.Errorf("suggestedFlags = %v, want [--not-created-here]", rec.SuggestedFlags)
		}
		if !strings.Contains(rec.Reason, "no record that this CLI created it") {
			t.Errorf("the reason must be the operator's own text: %q", rec.Reason)
		}
		if rec.CreatedHere {
			t.Error("createdHere must be false when nothing vouched for it")
		}
		if rec.Method != "DELETE" || !strings.HasSuffix(rec.URL, "/Drafts(54990)") {
			t.Errorf("the record must carry the request that WOULD have gone: %+v", rec)
		}
		if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
			t.Errorf("a refusal sends nothing: %v", f.seenMethods())
		}
		// Nothing was destroyed, so the draft's contents have no business on
		// stdout — the record names the row by hash and stops there.
		if strings.Contains(stdout, "TPAC PACKAGING") || strings.Contains(stdout, `"snapshot":`) {
			t.Errorf("a refused draft is still in SAP; its contents must not be printed:\n%s", stdout)
		}
		if !strings.Contains(stdout, `"snapshotSha256":`) {
			t.Errorf("the record should still name the row it read, by hash:\n%s", stdout)
		}
	})

	t.Run("an attachment, --dry-run", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.putDraft(54990, map[string]interface{}{"AttachmentEntry": 170187})
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

		stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--dry-run")
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("want *errs.RefusedError, got %T: %v", err, err)
		}
		recs := parseRefusalRecords(t, stdout)
		if len(recs) != 1 {
			t.Fatalf("want one record, got %d:\n%s", len(recs), stdout)
		}
		if !recs[0].DryRun {
			t.Error("a refusal from a dry run must still say it came from a dry run")
		}
		if len(recs[0].Refused) != 1 || recs[0].Refused[0] != "attachment" {
			t.Errorf("refused = %v, want [attachment]", recs[0].Refused)
		}
		if len(recs[0].SuggestedFlags) != 1 || recs[0].SuggestedFlags[0] != "--with-attachment" {
			t.Errorf("suggestedFlags = %v, want [--with-attachment]", recs[0].SuggestedFlags)
		}
		if !recs[0].CreatedHere {
			t.Error("this CLI did create it — createdHere must say so")
		}
	})

	t.Run("one of a batch refuses", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		for _, n := range []int64{54990, 54991} {
			f.putDraft(n, nil)
		}
		// Only the first is vouched for; the second trips provenance and takes the
		// whole batch down with it.
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

		stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "54991", "--yes")
		var refused *errs.RefusedError
		if !errors.As(err, &refused) {
			t.Fatalf("want *errs.RefusedError, got %T: %v", err, err)
		}
		recs := parseRefusalRecords(t, stdout)
		if len(recs) != 2 {
			t.Fatalf("every DocEntry in the batch needs a record, got %d:\n%s", len(recs), stdout)
		}
		ok, bad := recs[0], recs[1]
		if ok.DocEntry != 54990 || len(ok.Refused) != 0 {
			t.Errorf("54990 tripped nothing: %+v", ok)
		}
		if !strings.Contains(ok.Skipped, "not attempted") || !strings.Contains(ok.Skipped, "Drafts(54991)") {
			t.Errorf("54990 must say WHICH draft stopped the batch: %+v", ok)
		}
		if !ok.CreatedHere {
			t.Error("54990 was created here — createdHere must say so")
		}
		if bad.DocEntry != 54991 || len(bad.Refused) != 1 || bad.Refused[0] != "provenance" {
			t.Errorf("54991 is the one that refused: %+v", bad)
		}
	})

	t.Run("several guards on one draft", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		created := time.Now().Add(-72 * time.Hour)
		f.putDraft(54990, map[string]interface{}{
			"AttachmentEntry": 170187,
			"DocumentStatus":  "bost_Close",
			"CreationDate":    created.Format("2006-01-02T15:04:05Z"),
		})
		seedCreation(t, operatorLog(root, "someone-else"), "Drafts", "TESTDB", 54990, "someone-else", created)

		stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--yes")
		if err == nil {
			t.Fatal("four guards must refuse")
		}
		recs := parseRefusalRecords(t, stdout)
		if len(recs) != 1 {
			t.Fatalf("want one record, got %d:\n%s", len(recs), stdout)
		}
		want := map[string]string{
			"closed":         "--closed",
			"attachment":     "--with-attachment",
			"older-than":     "--older-than 96h",
			"other-operator": "--other-operator",
		}
		got := map[string]bool{}
		for _, g := range recs[0].Refused {
			got[g] = true
		}
		for guard := range want {
			if !got[guard] {
				t.Errorf("refused must name %q, got %v", guard, recs[0].Refused)
			}
		}
		flags := strings.Join(recs[0].SuggestedFlags, " ")
		for _, f := range want {
			if !strings.Contains(flags, f) {
				t.Errorf("suggestedFlags must carry %q, got %v", f, recs[0].SuggestedFlags)
			}
		}
	})
}

// TestCreatedHereIsStatedNotInferred — a caller reading the stream should not
// have to know that "origin is present" means "this CLI made it".
func TestCreatedHereIsStatedNotInferred(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, nil)
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--yes")
	if err != nil {
		t.Fatalf("delete failed: %v", err)
	}
	recs := parseRefusalRecords(t, stdout)
	if len(recs) != 1 || !recs[0].CreatedHere || !recs[0].Verified {
		t.Fatalf("a successful delete must carry createdHere:true: %+v", recs)
	}

	// And the human-confirmed override case says NO, though it deleted anyway.
	f2 := newFakeDraftSAP(t)
	provenanceRepo(t)
	f2.putDraft(54991, nil)
	withTTY(t, true)
	stdout, _, err = execWrite(t, "yes\n", "--json", "delete", "draft", "54991", "--not-created-here")
	if err != nil {
		t.Fatalf("the override at a prompt must work: %v", err)
	}
	recs = parseRefusalRecords(t, stdout)
	if len(recs) != 1 || recs[0].CreatedHere {
		t.Fatalf("--not-created-here means createdHere:false: %+v", recs)
	}
}

// TestSummaryShowsTheApprovalStatus — an Oil A/P invoice draft routes through
// approval template "USER03 AP" and sits in somebody's Approval Status Report as
// Pending while still reading bost_Open, so no other guard here sees it.
// AuthorizationStatus was read off the row and written to the snapshot, but
// never shown — the operator typed "yes" over a summary that said nothing about
// the person waiting to approve it.
func TestSummaryShowsTheApprovalStatus(t *testing.T) {
	f := newFakeDraftSAP(t)
	root := provenanceRepo(t)
	f.putDraft(54990, map[string]interface{}{"AuthorizationStatus": "dasPending"})
	seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

	// --in-approval, because showing it is no longer all this does: the guard
	// below refuses it outright. This case is about the summary.
	_, stderr, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--in-approval")
	if err != nil {
		t.Fatalf("delete failed: %v", err)
	}
	if !strings.Contains(stderr, "AuthorizationStatus") || !strings.Contains(stderr, "dasPending") {
		t.Errorf("the summary above the prompt must show the approval status:\n%s", stderr)
	}

	// A draft outside any workflow prints nothing extra — writeDraftSummary skips
	// absent fields, and a line saying "AuthorizationStatus:" with nothing after
	// it would be noise on every single delete.
	f2 := newFakeDraftSAP(t)
	root2 := provenanceRepo(t)
	f2.putDraft(54991, nil)
	seedCreation(t, operatorLog(root2, "tester"), "Drafts", "TESTDB", 54991, "tester", time.Now())
	if _, stderr, err = execWrite(t, "", "delete", "draft", "54991", "--yes"); err != nil {
		t.Fatalf("delete failed: %v", err)
	}
	if strings.Contains(stderr, "AuthorizationStatus") {
		t.Errorf("a draft with no approval status must print no line for it:\n%s", stderr)
	}
}

// TestDeleteRefusesADraftInAnApprovalWorkflow — showing the status is not
// enough. With --yes nobody reads the summary, and a draft in a workflow is in
// use by a second person: it sits in their Approval Status Report while still
// reading bost_Open, so no other guard here sees it. Deleting it takes the
// request out from under them with no notice.
func TestDeleteRefusesADraftInAnApprovalWorkflow(t *testing.T) {
	// Every status SAP puts on a draft a template has matched. None of them is a
	// draft nobody is acting on.
	// Both prefixes: ODRF drafts return das*, OPDF payment drafts return pas*.
	for _, status := range []string{
		"dasPending", "dasApproved", "dasGenerated", "dasRejected",
		"pasPending", "pasApproved", "pasGenerated", "pasRejected",
	} {
		t.Run(status, func(t *testing.T) {
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)
			f.putDraft(54990, map[string]interface{}{"AuthorizationStatus": status})
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

			stdout, _, err := execWrite(t, "", "--json", "delete", "draft", "54990", "--yes")
			if err == nil {
				t.Fatal("expected a draft in an approval workflow to be refused")
			}
			var refused *errs.RefusedError
			if !errors.As(err, &refused) {
				t.Fatalf("expected *errs.RefusedError, got %T: %v", err, err)
			}
			if ExitCodeFor(err) != ExitRefused {
				t.Errorf("a guard refusal is exit %d, got %d", ExitRefused, ExitCodeFor(err))
			}
			for _, want := range []string{"approval workflow", "AuthorizationStatus " + status, "someone is acting on it", "--in-approval"} {
				if !strings.Contains(refused.Msg, want) {
					t.Errorf("refusal must contain %q, got:\n%s", want, refused.Msg)
				}
			}
			if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
				t.Errorf("no DELETE may be sent: %v", f.seenMethods())
			}
			// And the batch tooling can read which guard it was.
			recs := parseRefusalRecords(t, stdout)
			if len(recs) != 1 || len(recs[0].Refused) != 1 || recs[0].Refused[0] != "in-approval" {
				t.Fatalf("refused = %v, want [in-approval]", recs)
			}
			if len(recs[0].SuggestedFlags) != 1 || recs[0].SuggestedFlags[0] != "--in-approval" {
				t.Errorf("suggestedFlags = %v, want [--in-approval]", recs[0].SuggestedFlags)
			}
		})
	}

	// dasWithout is the normal state of a draft no template matched, and an
	// entity that carries no such field at all (PaymentDrafts) must not be
	// refused by a check that cannot run.
	for _, tc := range []struct {
		name  string
		extra map[string]interface{}
	}{
		{"dasWithout", map[string]interface{}{"AuthorizationStatus": "dasWithout"}},
		// A payment draft nobody is approving. Live: Beverages OPDF 292 read this,
		// and a das*-only comparison refused every payment draft ever made.
		{"pasWithout", map[string]interface{}{"AuthorizationStatus": "pasWithout"}},
		{"no such field", nil},
	} {
		t.Run(tc.name+" deletes normally", func(t *testing.T) {
			f := newFakeDraftSAP(t)
			root := provenanceRepo(t)
			f.putDraft(54990, tc.extra)
			seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

			if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes"); err != nil {
				t.Fatalf("nothing is acting on this draft: %v", err)
			}
			if n := countMethod(f.seenMethods(), "DELETE"); n != 1 {
				t.Errorf("want one DELETE, got %v", f.seenMethods())
			}
		})
	}

	t.Run("--in-approval lifts this guard and is recorded", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.putDraft(54990, map[string]interface{}{"AuthorizationStatus": "dasPending"})
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

		if _, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--in-approval"); err != nil {
			t.Fatalf("--in-approval should proceed: %v", err)
		}
		assertOverrideRecorded(t, f, "in-approval")
	})

	t.Run("--in-approval lifts ONLY this guard", func(t *testing.T) {
		f := newFakeDraftSAP(t)
		root := provenanceRepo(t)
		f.putDraft(54990, map[string]interface{}{
			"AuthorizationStatus": "dasPending",
			"AttachmentEntry":     170187,
		})
		seedCreation(t, operatorLog(root, "tester"), "Drafts", "TESTDB", 54990, "tester", time.Now())

		_, _, err := execWrite(t, "", "delete", "draft", "54990", "--yes", "--in-approval")
		if err == nil {
			t.Fatal("the attachment guard must still refuse")
		}
		if !strings.Contains(err.Error(), "--with-attachment") {
			t.Errorf("the remaining refusal must be the attachment one, got: %v", err)
		}
		if n := countMethod(f.seenMethods(), "DELETE"); n != 0 {
			t.Errorf("no DELETE may be sent: %v", f.seenMethods())
		}
	})
}

// registerCheckout stands the test in a directory that looks like a registered
// JIVO checkout, so config.SharedWriteLogPath resolves inside the temp tree, and
// returns the operator log it resolves to.
func registerCheckout(t *testing.T, slug string) string {
	t.Helper()
	root := t.TempDir()
	for _, d := range []string{"harness", ".git"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building the checkout: %v", err)
		}
	}
	if err := os.WriteFile(filepath.Join(root, "harness", ".operator"), []byte(`{"slug":"`+slug+`"}`), 0o600); err != nil {
		t.Fatalf("registering the operator: %v", err)
	}
	t.Chdir(root)
	return filepath.Join(root, "queries", slug, "sap-writes.jsonl")
}

// TestDeleteRecordReachesTheTeamWhateverTheEnvSays — $SAPB1_WRITE_LOG used to
// take the ONLY record of a delete out of the shared history, while the preview
// above the prompt claimed the opposite ("shared with the team"). No forgery
// needed: a stale wrapper script does it by accident, and for a delete there is
// no SAP row left to reconstruct it from.
func TestDeleteRecordReachesTheTeamWhateverTheEnvSays(t *testing.T) {
	withTTY(t, true)
	f := newFakeDraftSAP(t)
	sharedLog := registerCheckout(t, "tester")

	// The provenance evidence lives in the same checkout, as it would in life.
	setProvenanceRoot(t, filepath.Dir(filepath.Dir(filepath.Dir(sharedLog))))
	seedCreation(t, sharedLog, "Drafts", "TESTDB", 54990, "tester", time.Now())
	f.putDraft(54990, nil)

	// And the caller points its own log at scratch, as acc/_playbook/sap could.
	scratch := filepath.Join(t.TempDir(), "scratch.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", scratch)

	_, stderr, err := execWrite(t, "yes\n", "delete", "draft", "54990")
	if err != nil {
		t.Fatalf("delete failed: %v\nstderr: %s", err, stderr)
	}

	// The preview named the file the team reads, and it was telling the truth.
	if !strings.Contains(stderr, "shared with the team") {
		t.Errorf("the preview must name the shared log:\n%s", stderr)
	}
	if !strings.Contains(stderr, "$SAPB1_WRITE_LOG points") {
		t.Errorf("the preview must also name the diverted copy:\n%s", stderr)
	}

	raw, err := os.ReadFile(sharedLog)
	if err != nil {
		t.Fatalf("reading the checkout's log: %v", err)
	}
	if n := strings.Count(string(raw), `"method":"DELETE"`); n != 2 {
		t.Errorf("the checkout's log must carry the intent and the outcome, got %d DELETE line(s):\n%s", n, raw)
	}
	// The caller's own file still gets everything, so existing tooling works.
	diverted, err := os.ReadFile(scratch)
	if err != nil {
		t.Fatalf("reading the diverted log: %v", err)
	}
	if n := strings.Count(string(diverted), `"method":"DELETE"`); n != 2 {
		t.Errorf("the configured log must still be written, got %d DELETE line(s)", n)
	}
	// And the contents of the draft are in neither of them.
	for name, data := range map[string]string{"shared": string(raw), "diverted": string(diverted)} {
		if strings.Contains(data, "TPAC PACKAGING") {
			t.Errorf("the %s log must not carry the snapshot contents:\n%s", name, data)
		}
	}
}
