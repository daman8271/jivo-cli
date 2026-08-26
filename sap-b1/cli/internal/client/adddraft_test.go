package client

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"sapb1/internal/errs"
)

// addDraftRecorder is a Service Layer stand-in that records every request it is
// given, so a test can assert both "exactly these bytes went out" and "nothing
// went out at all".
type addDraftRecorder struct {
	mu       sync.Mutex
	requests []recordedRequest
	status   int
	body     string
}

type recordedRequest struct {
	Method  string
	Path    string
	RawPath string
	Query   string
	Body    string
	Headers http.Header
}

func newAddDraftRecorder(t *testing.T) (*addDraftRecorder, *Client) {
	t.Helper()
	r := &addDraftRecorder{status: http.StatusOK, body: `{}`}
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		if req.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		body, _ := io.ReadAll(req.Body)
		r.mu.Lock()
		r.requests = append(r.requests, recordedRequest{
			Method:  req.Method,
			Path:    req.URL.Path,
			RawPath: req.URL.EscapedPath(),
			Query:   req.URL.RawQuery,
			Body:    string(body),
			Headers: req.Header.Clone(),
		})
		status, respBody := r.status, r.body
		r.mu.Unlock()
		w.WriteHeader(status)
		if respBody != "" {
			_, _ = w.Write([]byte(respBody))
		}
	}))
	t.Cleanup(srv.Close)
	return r, newFakeClient(t, srv)
}

func (r *addDraftRecorder) seen() []recordedRequest {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]recordedRequest, len(r.requests))
	copy(out, r.requests)
	return out
}

// TestSaveDraftToDocumentWireFormat pins the two things about this request that
// nothing may drift: the flat function-import path, and DocEntry as a STRING.
//
// The string form is the vendor's own example and what the live Service Layer
// accepted on probe. It reads like a bug and will look like one to whoever
// touches this next — hence the test, not just the comment.
func TestSaveDraftToDocumentWireFormat(t *testing.T) {
	r, c := newAddDraftRecorder(t)

	res, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{})
	if err != nil {
		t.Fatalf("SaveDraftToDocument: %v", err)
	}
	if res.Status != http.StatusOK {
		t.Errorf("status = %d, want 200", res.Status)
	}

	reqs := r.seen()
	if len(reqs) != 1 {
		t.Fatalf("want exactly one request, got %d: %+v", len(reqs), reqs)
	}
	got := reqs[0]
	if got.Method != http.MethodPost {
		t.Errorf("method = %s, want POST", got.Method)
	}
	if got.Path != "/b1s/v1/DraftsService_SaveDraftToDocument" {
		t.Errorf("path = %s, want the flat function import with no key and no slash", got.Path)
	}
	if got.RawPath != got.Path {
		t.Errorf("nothing should need percent-encoding in this path, got %q", got.RawPath)
	}
	if got.Query != "" {
		t.Errorf("this request carries no query string, got %q", got.Query)
	}
	if got.Body != `{"Document":{"DocEntry":"55126"}}` {
		t.Errorf("body = %s, want {\"Document\":{\"DocEntry\":\"55126\"}} — DocEntry is a STRING here", got.Body)
	}
	if ct := got.Headers.Get("Content-Type"); ct != "application/json" {
		t.Errorf("Content-Type = %q, want application/json", ct)
	}
	if !strings.Contains(got.Headers.Get("Cookie"), "B1SESSION=") {
		t.Errorf("the session cookie must be attached, got %q", got.Headers.Get("Cookie"))
	}
}

// TestAddDraftSendsNoIdempotencyKey — write.go's rawWrite says the ABSENCE of
// that header is load-bearing: Go's net/http treats a request carrying one as
// replayable and will silently retry it after a connection error. On the one
// write in this tool that cannot be undone, a silent replay is a duplicate
// invoice on a vendor's ledger. Asserted over the headers the server actually
// received, not over the code that builds them.
func TestAddDraftSendsNoIdempotencyKey(t *testing.T) {
	r, c := newAddDraftRecorder(t)
	if _, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{}); err != nil {
		t.Fatalf("SaveDraftToDocument: %v", err)
	}
	reqs := r.seen()
	if len(reqs) != 1 {
		t.Fatalf("want one request, got %d", len(reqs))
	}
	for _, h := range []string{"Idempotency-Key", "X-Idempotency-Key", "Idempotency-Token"} {
		if v := reqs[0].Headers.Get(h); v != "" {
			t.Errorf("%s must never be sent (net/http would replay this write), got %q", h, v)
		}
	}
}

// TestSaveDraftToDocumentRefusesImpossibleDocEntries — the client is the last
// gate before the wire, so it re-checks what the command already checked. Zero
// requests either way.
func TestSaveDraftToDocumentRefusesImpossibleDocEntries(t *testing.T) {
	cases := []struct {
		name     string
		docEntry int64
	}{
		{"zero", 0},
		{"negative", -1},
		{"beyond SAP's 32-bit DocEntry column", 2147483648},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			r, c := newAddDraftRecorder(t)
			_, err := c.SaveDraftToDocument(context.Background(), tc.docEntry, AddDraftOptions{})
			if err == nil {
				t.Fatalf("DocEntry %d must be refused", tc.docEntry)
			}
			var usageErr *errs.UsageError
			if !errors.As(err, &usageErr) {
				t.Errorf("got %T, want *errs.UsageError: %v", err, err)
			}
			if n := len(r.seen()); n != 0 {
				t.Errorf("%d request(s) reached SAP; a refused DocEntry must send nothing", n)
			}
		})
	}
}

// TestSaveDraftToDocumentRetriesOnceOn401 — a 401 is the Service Layer rejecting
// the session cookie BEFORE it dispatches, so nothing is committed and one
// re-login + retry is safe. It must happen at most once: a loop would be a loop
// of live Adds.
func TestSaveDraftToDocumentRetriesOnceOn401(t *testing.T) {
	var mu sync.Mutex
	logins, posts := 0, 0

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		defer mu.Unlock()
		if r.URL.Path == "/b1s/v1/Login" {
			logins++
			loginHandler(w)
			return
		}
		posts++
		if posts == 1 {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session"}}}`))
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	if _, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{}); err != nil {
		t.Fatalf("SaveDraftToDocument: %v", err)
	}

	mu.Lock()
	defer mu.Unlock()
	if posts != 2 {
		t.Errorf("POSTs = %d, want exactly 2 (the original and one retry)", posts)
	}
	if logins != 2 {
		t.Errorf("logins = %d, want 2 (the first session and the one re-login)", logins)
	}
}

// TestSaveDraftToDocumentDoesNotRetryAPersistent401 — if the second attempt is
// also refused the command stops. Two POSTs is the ceiling, whatever SAP says.
func TestSaveDraftToDocumentDoesNotRetryAPersistent401(t *testing.T) {
	var mu sync.Mutex
	posts := 0

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		mu.Lock()
		posts++
		mu.Unlock()
		w.WriteHeader(http.StatusUnauthorized)
		_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session"}}}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	_, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{})
	var authErr *errs.AuthError
	if !errors.As(err, &authErr) {
		t.Fatalf("got %T, want *errs.AuthError: %v", err, err)
	}
	mu.Lock()
	defer mu.Unlock()
	if posts != 2 {
		t.Errorf("POSTs = %d, want exactly 2 — a 401 buys one retry, not a loop", posts)
	}
}

// TestSaveDraftToDocumentFansOutToBothLogs — an Add is irreversible, so its
// record reaches the team's committed log whatever $SAPB1_WRITE_LOG says. This
// is the property the old verb test would have silently dropped for a POST.
func TestSaveDraftToDocumentFansOutToBothLogs(t *testing.T) {
	r, c := newAddDraftRecorder(t)
	r.body = `{"DocEntry":47577,"DocNum":626074104}`
	_, sharedLog := fakeCheckout(t, "tester")

	scratch := filepath.Join(t.TempDir(), "scratch.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", scratch)

	if _, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{
		Snapshot: json.RawMessage(`{"DocEntry":55126,"CardCode":"VENDA000939","NumAtCard":"2606000806"}`),
		Origin:   &WriteOrigin{File: "queries/tester/sap-writes.jsonl", Line: 7, User: "tester", Time: time.Now()},
	}); err != nil {
		t.Fatalf("SaveDraftToDocument: %v", err)
	}

	for name, path := range map[string]string{"shared": sharedLog, "configured": scratch} {
		entries := parseWriteLog(t, path)
		if len(entries) != 2 {
			t.Fatalf("%s log: want an intent and an outcome, got %d", name, len(entries))
		}
		intent, outcome := entries[0], entries[1]
		if intent.Event != logIntent || outcome.Event != logOutcome {
			t.Fatalf("%s log: intent must be logged first, got %+v", name, entries)
		}
		if intent.Method != http.MethodPost || intent.Path != saveDraftToDocumentPath {
			t.Errorf("%s log: the record must name the real wire request, got %s %s", name, intent.Method, intent.Path)
		}
		if string(intent.Payload) != `{"Document":{"DocEntry":"55126"}}` {
			t.Errorf("%s log: the payload must be recorded verbatim, got %s", name, intent.Payload)
		}
		if intent.SnapshotSHA256 == "" {
			t.Errorf("%s log: the intent line must carry the snapshot hash", name)
		}
		if outcome.SnapshotSHA256 != "" {
			t.Errorf("%s log: the outcome line must not repeat the snapshot hash", name)
		}
		if outcome.ResultKey != "DocEntry=47577" {
			t.Errorf("%s log: when SAP hands back a key it belongs in the record, got %q", name, outcome.ResultKey)
		}
		if intent.Origin == nil || intent.Origin.Line != 7 {
			t.Errorf("%s log: the origin must ride both lines, got %+v", name, intent.Origin)
		}
	}

	// The snapshot CONTENTS never reach a committed file: this repo is public.
	raw, err := os.ReadFile(sharedLog)
	if err != nil {
		t.Fatalf("reading the shared log: %v", err)
	}
	if strings.Contains(string(raw), "VENDA000939") || strings.Contains(string(raw), "2606000806") {
		t.Errorf("the snapshot's contents must not reach the committed write log:\n%s", raw)
	}

	snaps := readSnapshotLog(t)
	if len(snaps) != 1 {
		t.Fatalf("want one snapshot line, got %d", len(snaps))
	}
	if snaps[0].Path != "Drafts(55126)" {
		t.Errorf("the snapshot must be filed under the DRAFT, not the service path, got %q", snaps[0].Path)
	}
	if snaps[0].Method != http.MethodPost {
		t.Errorf("snapshot method = %q, want POST", snaps[0].Method)
	}
	if !strings.Contains(string(snaps[0].Snapshot), "VENDA000939") {
		t.Errorf("the local snapshot log must keep the contents, got %s", snaps[0].Snapshot)
	}
	if snaps[0].SHA256 != parseWriteLog(t, sharedLog)[0].SnapshotSHA256 {
		t.Error("the shared log's hash must point at the local snapshot")
	}
}

// TestSaveDraftToDocumentRefusesWhenTheSharedLogIsUnwritable — the record is a
// precondition, and the refusal happens with ZERO requests sent.
func TestSaveDraftToDocumentRefusesWhenTheSharedLogIsUnwritable(t *testing.T) {
	r, c := newAddDraftRecorder(t)
	_, sharedLog := fakeCheckout(t, "tester")
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "fine.jsonl"))

	if err := os.MkdirAll(sharedLog, 0o755); err != nil {
		t.Fatalf("blocking the shared log: %v", err)
	}

	_, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{})
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("got %T, want *errs.ConfigError: %v", err, err)
	}
	if !strings.Contains(cfgErr.Msg, "refusing to ADD Drafts(55126)") {
		t.Errorf("the refusal must name the draft and the verb, got: %s", cfgErr.Msg)
	}
	if strings.Contains(cfgErr.Msg, "DELETE") {
		t.Errorf("an Add must not borrow a delete's words, got: %s", cfgErr.Msg)
	}
	if n := len(r.seen()); n != 0 {
		t.Errorf("%d request(s) reached SAP; an unrecordable Add must send nothing", n)
	}
}

// TestSaveDraftToDocumentRefusesWhenTheSnapshotCannotBeWritten — same rule for
// the contents. Zero requests.
func TestSaveDraftToDocumentRefusesWhenTheSnapshotCannotBeWritten(t *testing.T) {
	r, c := newAddDraftRecorder(t)
	blocked := filepath.Join(t.TempDir(), "snapshots.jsonl")
	if err := os.MkdirAll(blocked, 0o755); err != nil {
		t.Fatalf("blocking the snapshot log: %v", err)
	}
	t.Setenv("SAPB1_SNAPSHOT_LOG", blocked)

	_, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{
		Snapshot: json.RawMessage(`{"DocEntry":55126}`),
	})
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("got %T, want *errs.ConfigError: %v", err, err)
	}
	if n := len(r.seen()); n != 0 {
		t.Errorf("%d request(s) reached SAP; an unrecordable Add must send nothing", n)
	}
}

// TestSaveDraftToDocumentClassifiesSAPAnswers — the difference an operator acts
// on. A SAP error envelope is a definitive "no" (exit 6, nothing committed); a
// bare gateway status is "we never heard back" (exit 7, it may have posted).
func TestSaveDraftToDocumentClassifiesSAPAnswers(t *testing.T) {
	t.Run("SAP said no", func(t *testing.T) {
		r, c := newAddDraftRecorder(t)
		r.status = http.StatusNotFound
		r.body = `{"error":{"code":-2028,"message":{"lang":"en-us","value":"No matching records found (ODBC -2028)"}}}`

		_, err := c.SaveDraftToDocument(context.Background(), 999999999, AddDraftOptions{})
		var apiErr *errs.APIError
		if !errors.As(err, &apiErr) {
			t.Fatalf("got %T, want *errs.APIError: %v", err, err)
		}
		if !strings.Contains(apiErr.Msg, "No matching records found") {
			t.Errorf("SAP's own words must survive, got: %s", apiErr.Msg)
		}
	})

	t.Run("a gateway answered, not SAP", func(t *testing.T) {
		r, c := newAddDraftRecorder(t)
		r.status = http.StatusBadGateway
		r.body = "<html>502 Bad Gateway</html>"

		_, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{})
		var unknown *errs.WriteOutcomeUnknownError
		if !errors.As(err, &unknown) {
			t.Fatalf("got %T, want *errs.WriteOutcomeUnknownError: %v", err, err)
		}
		if !strings.Contains(unknown.Msg, "outcome is unknown") {
			t.Errorf("the message must say the outcome is unknown, got: %s", unknown.Msg)
		}
	})
}

// TestSaveDraftToDocumentSurvivesAnUnexpectedResponseShape — nobody in this repo
// has ever made this call succeed, so its success body is a guess. Nothing may
// depend on it: a 2xx with a body that is not an object, or no body at all, is
// still a successful call and the caller classifies the outcome by reading the
// row back.
func TestSaveDraftToDocumentSurvivesAnUnexpectedResponseShape(t *testing.T) {
	for _, body := range []string{"", "true", `"OK"`, `[{"DocEntry":1}]`, "not json at all"} {
		r, c := newAddDraftRecorder(t)
		r.status = http.StatusOK
		r.body = body

		res, err := c.SaveDraftToDocument(context.Background(), 55126, AddDraftOptions{})
		if err != nil {
			t.Errorf("body %q must still be a successful call, got: %v", body, err)
			continue
		}
		if res.Status != http.StatusOK {
			t.Errorf("body %q: status = %d, want 200", body, res.Status)
		}
	}
}
