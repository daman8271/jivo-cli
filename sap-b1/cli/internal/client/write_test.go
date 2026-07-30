package client

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// testPassword is what the fake Service Layer "accepts". It exists so tests can
// assert it never leaks into the write log.
const testPassword = "n0t-in-the-log"

// newFakeClient points a Client at srv (an httptest TLS server standing in for
// the Service Layer) and redirects both the session cache and the write log
// into t.TempDir(), so no real file and no real SAP host is ever touched.
func newFakeClient(t *testing.T, srv *httptest.Server) *Client {
	t.Helper()
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(home, "writes.jsonl"))

	u, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatalf("parsing test server URL: %v", err)
	}
	port, err := strconv.Atoi(u.Port())
	if err != nil {
		t.Fatalf("parsing test server port: %v", err)
	}

	c := New(&config.Config{
		Host:       u.Hostname(),
		Port:       port,
		CompanyDB:  "TESTDB",
		User:       "tester",
		Password:   testPassword,
		Insecure:   true,
		Timeout:    5,
		TimeoutSet: true, // keep tests fast: don't inherit the 120s write default
	})
	c.SetErrWriter(io.Discard)
	return c
}

// loginHandler writes a B1SESSION cookie, like the real Login does.
func loginHandler(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{Name: "B1SESSION", Value: "fake-session"})
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write([]byte(`{"SessionId":"fake-session"}`))
}

func readWriteLog(t *testing.T) []writeLogEntry {
	t.Helper()
	return parseWriteLog(t, os.Getenv("SAPB1_WRITE_LOG"))
}

func parseWriteLog(t *testing.T, path string) []writeLogEntry {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("reading write log: %v", err)
	}
	var out []writeLogEntry
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		if line == "" {
			continue
		}
		var e writeLogEntry
		if err := json.Unmarshal([]byte(line), &e); err != nil {
			t.Fatalf("write log line is not valid JSON: %v\n%s", err, line)
		}
		out = append(out, e)
	}
	return out
}

// outcomes filters a log to just the outcome lines, which is what most
// assertions care about.
func outcomes(entries []writeLogEntry) []writeLogEntry {
	var out []writeLogEntry
	for _, e := range entries {
		if e.Event == logOutcome {
			out = append(out, e)
		}
	}
	return out
}

func statusOf(t *testing.T, e writeLogEntry) int {
	t.Helper()
	if e.Status == nil {
		t.Fatalf("expected a status on outcome line %+v", e)
	}
	return *e.Status
}

// TestCreatePostsPayloadAndReturnsBody verifies Create logs in, POSTs the exact
// payload with a JSON content type and the session cookie, and hands back the
// created object.
func TestCreatePostsPayloadAndReturnsBody(t *testing.T) {
	var gotMethod, gotPath, gotBody, gotContentType, gotCookie string

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		body, _ := io.ReadAll(r.Body)
		gotMethod, gotPath, gotBody = r.Method, r.URL.Path, string(body)
		gotContentType = r.Header.Get("Content-Type")
		gotCookie = r.Header.Get("Cookie")
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"DocEntry":4321,"DocNum":99,"DocObjectCode":"oOrders"}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	res, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`))
	if err != nil {
		t.Fatalf("Create: %v", err)
	}

	if gotMethod != http.MethodPost {
		t.Errorf("method = %s, want POST", gotMethod)
	}
	if gotPath != "/b1s/v1/Drafts" {
		t.Errorf("path = %s, want /b1s/v1/Drafts", gotPath)
	}
	if gotBody != `{"CardCode":"C0001"}` {
		t.Errorf("body = %s, want the payload verbatim", gotBody)
	}
	if gotContentType != "application/json" {
		t.Errorf("Content-Type = %q, want application/json", gotContentType)
	}
	if !strings.Contains(gotCookie, "B1SESSION=fake-session") {
		t.Errorf("Cookie = %q, want the session cookie attached", gotCookie)
	}
	if res.Status != http.StatusCreated {
		t.Errorf("Status = %d, want 201", res.Status)
	}
	if !strings.Contains(string(res.Body), `"DocEntry":4321`) {
		t.Errorf("Body = %s, want the created object", res.Body)
	}
}

// TestWriteReloginsOnceOn401AndRetries verifies the one-shot re-login: exactly
// two entity POSTs, never a third.
func TestWriteReloginsOnceOn401AndRetries(t *testing.T) {
	var logins, posts int

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			logins++
			loginHandler(w)
			return
		}
		posts++
		if posts == 1 {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session."}}}`))
			return
		}
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"DocEntry":7}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	res, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`))
	if err != nil {
		t.Fatalf("Create after re-login: %v", err)
	}
	if res.Status != http.StatusCreated {
		t.Errorf("Status = %d, want 201", res.Status)
	}
	if posts != 2 {
		t.Errorf("entity POSTs = %d, want exactly 2 (original + one retry)", posts)
	}
	if logins != 2 {
		t.Errorf("logins = %d, want 2 (initial + one re-login)", logins)
	}
}

// TestUpdateReturns204NoBody covers the normal PATCH outcome: HTTP 204 with an
// empty body must be a success, not an error.
func TestUpdateReturns204NoBody(t *testing.T) {
	var gotMethod, gotPath string

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		gotMethod, gotPath = r.Method, r.URL.Path
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	res, err := c.Update(context.Background(), "Orders(123)", []byte(`{"Comments":"ok"}`))
	if err != nil {
		t.Fatalf("Update: %v", err)
	}
	if gotMethod != http.MethodPatch {
		t.Errorf("method = %s, want PATCH", gotMethod)
	}
	if gotPath != "/b1s/v1/Orders(123)" {
		t.Errorf("path = %s, want /b1s/v1/Orders(123)", gotPath)
	}
	if res.Status != http.StatusNoContent {
		t.Errorf("Status = %d, want 204", res.Status)
	}
	if len(res.Body) != 0 {
		t.Errorf("Body = %q, want empty", res.Body)
	}
}

// TestWriteSAPErrorIsAPIError verifies a rejected write surfaces SAP's own
// message as an *errs.APIError (exit code 6), not a raw HTTP status.
func TestWriteSAPErrorIsAPIError(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error":{"code":-5002,"message":{"lang":"en-us","value":"Business partner code not found"}}}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	_, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"NOPE"}`))
	if err == nil {
		t.Fatal("expected an error for a rejected write")
	}
	var apiErr *errs.APIError
	if !errors.As(err, &apiErr) {
		t.Fatalf("expected *errs.APIError, got %T: %v", err, err)
	}
	if apiErr.Msg != "Business partner code not found" {
		t.Errorf("Msg = %q, want SAP's message", apiErr.Msg)
	}
}

// TestWriteAppendsLogOnSuccessAndFailure is the audit-trail guarantee: one JSONL
// line per attempted write, failures included, and never the SAP password.
func TestWriteAppendsLogOnSuccessAndFailure(t *testing.T) {
	var posts int

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		posts++
		if posts == 1 {
			w.WriteHeader(http.StatusCreated)
			_, _ = w.Write([]byte(`{"DocEntry":4321,"DocNum":99}`))
			return
		}
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error":{"code":-1,"message":{"lang":"en-us","value":"nope"}}}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	ctx := context.Background()
	if _, err := c.Create(ctx, "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Fatalf("first Create should succeed: %v", err)
	}
	if _, err := c.Create(ctx, "Drafts", []byte(`{"CardCode":"BAD"}`)); err == nil {
		t.Fatal("second Create should fail")
	}

	entries := readWriteLog(t)
	// Two writes → two intent/outcome pairs, interleaved in order.
	if len(entries) != 4 {
		t.Fatalf("write log has %d entries, want 4 (intent+outcome per write)", len(entries))
	}
	for i, wantEvent := range []string{logIntent, logOutcome, logIntent, logOutcome} {
		if entries[i].Event != wantEvent {
			t.Errorf("entry %d event = %q, want %q", i, entries[i].Event, wantEvent)
		}
	}
	if entries[0].Status != nil {
		t.Errorf("an intent line must not claim a status, got %v", *entries[0].Status)
	}

	// Every line says where it went — the log has to answer "was that production?".
	for i, e := range entries {
		if e.Host == "" || e.Port == 0 {
			t.Errorf("entry %d has no host/port: %+v", i, e)
		}
		if e.CompanyDB != "TESTDB" || e.User != "tester" {
			t.Errorf("entry %d missing company/user: %+v", i, e)
		}
	}

	done := outcomes(entries)
	ok := done[0]
	if ok.Method != http.MethodPost || ok.Path != "Drafts" || statusOf(t, ok) != http.StatusCreated {
		t.Errorf("success outcome = %+v, want POST Drafts 201", ok)
	}
	if ok.ResultKey != "DocEntry=4321" {
		t.Errorf("ResultKey = %q, want DocEntry=4321", ok.ResultKey)
	}
	if ok.Error != "" {
		t.Errorf("success entry should have no error, got %q", ok.Error)
	}
	if !strings.Contains(string(ok.Payload), "C0001") {
		t.Errorf("success entry payload = %s, want the sent payload", ok.Payload)
	}

	bad := done[1]
	if statusOf(t, bad) != http.StatusBadRequest {
		t.Errorf("failure outcome status = %d, want 400", statusOf(t, bad))
	}
	if !strings.Contains(bad.Error, "nope") {
		t.Errorf("failure entry error = %q, want SAP's message", bad.Error)
	}

	raw, err := os.ReadFile(os.Getenv("SAPB1_WRITE_LOG"))
	if err != nil {
		t.Fatalf("reading write log: %v", err)
	}
	if strings.Contains(string(raw), testPassword) {
		t.Fatal("the SAP password must never appear in the write log")
	}
}

// TestWriteTransportErrorIsNetworkError verifies a write that never reaches the
// server maps to *errs.NetworkError (exit 5) — and is still logged, with
// status 0, so an operator can see the attempt happened.
func TestWriteTransportErrorIsNetworkError(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		loginHandler(w)
	}))

	c := newFakeClient(t, srv)
	if err := c.Login(context.Background()); err != nil {
		t.Fatalf("Login against fake server: %v", err)
	}
	srv.Close() // now nothing is listening — the POST can't complete

	_, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`))
	if err == nil {
		t.Fatal("expected an error writing to a closed server")
	}
	var netErr *errs.NetworkError
	if !errors.As(err, &netErr) {
		t.Fatalf("expected *errs.NetworkError, got %T: %v", err, err)
	}

	entries := readWriteLog(t)
	if len(entries) != 2 {
		t.Fatalf("write log has %d entries, want 2 (intent + outcome)", len(entries))
	}
	done := outcomes(entries)
	if statusOf(t, done[0]) != 0 {
		t.Errorf("status = %d, want 0 for a request that never completed", statusOf(t, done[0]))
	}
	if done[0].Error == "" {
		t.Error("transport failure must be recorded with an error message")
	}
}

// TestWriteLogsIntentBeforeTheRequest is the Ctrl-C guarantee: by the time SAP
// sees the request, the intent line is already on disk, so a process killed
// mid-POST still leaves evidence that something was sent.
func TestWriteLogsIntentBeforeTheRequest(t *testing.T) {
	var logAtRequestTime []writeLogEntry

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		// Read the write log from inside the handler — i.e. exactly while the
		// request is in flight and its outcome is not yet known.
		logAtRequestTime = parseWriteLog(t, os.Getenv("SAPB1_WRITE_LOG"))
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"DocEntry":4321}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	if _, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Fatalf("Create: %v", err)
	}

	if len(logAtRequestTime) != 1 {
		t.Fatalf("log had %d lines while the request was in flight, want exactly 1 (the intent)", len(logAtRequestTime))
	}
	if logAtRequestTime[0].Event != logIntent {
		t.Errorf("in-flight line event = %q, want %q", logAtRequestTime[0].Event, logIntent)
	}
	if logAtRequestTime[0].Status != nil {
		t.Error("the in-flight line must not claim an outcome")
	}
	if !strings.Contains(string(logAtRequestTime[0].Payload), "C0001") {
		t.Errorf("the intent line must carry the payload, got %s", logAtRequestTime[0].Payload)
	}
}

// TestWriteLogRecordsEveryAttemptOn401 proves the re-login path leaves a pair per
// request, not one line for two POSTs.
func TestWriteLogRecordsEveryAttemptOn401(t *testing.T) {
	var posts int
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		posts++
		if posts == 1 {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session."}}}`))
			return
		}
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"DocEntry":7}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	if _, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Fatalf("Create: %v", err)
	}

	entries := readWriteLog(t)
	if len(entries) != 4 {
		t.Fatalf("write log has %d lines, want 4 (two POSTs, each intent+outcome):\n%+v", len(entries), entries)
	}
	done := outcomes(entries)
	if statusOf(t, done[0]) != http.StatusUnauthorized {
		t.Errorf("first outcome = %d, want the 401", statusOf(t, done[0]))
	}
	if !strings.Contains(done[0].Error, "401") {
		t.Errorf("the 401 line should say what happened, got %q", done[0].Error)
	}
	if statusOf(t, done[1]) != http.StatusCreated {
		t.Errorf("second outcome = %d, want 201", statusOf(t, done[1]))
	}
}

// TestWriteTimeoutIsOutcomeUnknown is the double-post guardrail: a write whose
// response never comes back must NOT be reported as "cannot reach SAP", because
// that reads like "nothing happened" and invites a retry.
func TestWriteTimeoutIsOutcomeUnknown(t *testing.T) {
	release := make(chan struct{})
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		// Accept the write, then stall past the client timeout — models SAP
		// committing the document while the answer never gets back.
		<-release
		w.WriteHeader(http.StatusCreated)
	}))
	defer func() { close(release); srv.Close() }()

	c := newFakeClient(t, srv)
	c.cfg.Timeout = 1 // 1s, explicitly set by newFakeClient's TimeoutSet

	_, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`))
	if err == nil {
		t.Fatal("expected an error when the response never arrives")
	}
	var unknown *errs.WriteOutcomeUnknownError
	if !errors.As(err, &unknown) {
		t.Fatalf("expected *errs.WriteOutcomeUnknownError, got %T: %v", err, err)
	}
	var netErr *errs.NetworkError
	if errors.As(err, &netErr) {
		t.Fatal("a sent-but-unanswered write must NOT be a NetworkError (that reads as 'nothing happened')")
	}
	for _, want := range []string{"outcome is unknown", "MAY have been committed", "before re-running"} {
		if !strings.Contains(unknown.Msg, want) {
			t.Errorf("message must contain %q, got: %s", want, unknown.Msg)
		}
	}

	done := outcomes(readWriteLog(t))
	if len(done) != 1 || done[0].Error == "" {
		t.Errorf("the unknown outcome must be logged, got %+v", done)
	}
}

// TestWriteGatewayErrorIsOutcomeUnknown — a bare 502/504 came from something in
// front of SAP, so SAP may well have committed the write.
func TestWriteGatewayErrorIsOutcomeUnknown(t *testing.T) {
	for _, status := range []int{http.StatusBadGateway, http.StatusGatewayTimeout, http.StatusServiceUnavailable} {
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				loginHandler(w)
				return
			}
			w.WriteHeader(status)
			_, _ = w.Write([]byte("<html>502 Bad Gateway</html>"))
		}))

		c := newFakeClient(t, srv)
		_, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`))
		srv.Close()

		var unknown *errs.WriteOutcomeUnknownError
		if !errors.As(err, &unknown) {
			t.Errorf("HTTP %d: expected *errs.WriteOutcomeUnknownError, got %T: %v", status, err, err)
		}
	}
}

// TestWriteSAPErrorWithEnvelopeIsDefinitive — the flip side: when SAP itself
// answered with its error envelope, the write definitively did not happen, even
// for a 500. That must stay an APIError (exit 6), not "unknown".
func TestWriteSAPErrorWithEnvelopeIsDefinitive(t *testing.T) {
	for _, status := range []int{http.StatusBadRequest, http.StatusInternalServerError, http.StatusBadGateway} {
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				loginHandler(w)
				return
			}
			w.WriteHeader(status)
			_, _ = w.Write([]byte(`{"error":{"code":-5002,"message":{"lang":"en-us","value":"Business partner code not found"}}}`))
		}))

		c := newFakeClient(t, srv)
		_, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"NOPE"}`))
		srv.Close()

		var apiErr *errs.APIError
		if !errors.As(err, &apiErr) {
			t.Errorf("HTTP %d with a SAP envelope: expected *errs.APIError, got %T: %v", status, err, err)
			continue
		}
		if fmt.Sprint(apiErr.Code) != "-5002" {
			t.Errorf("HTTP %d: APIError.Code = %v, want SAP's -5002", status, apiErr.Code)
		}
		if !strings.Contains(apiErr.Error(), "-5002") {
			t.Errorf("HTTP %d: Error() should surface SAP's code, got %q", status, apiErr.Error())
		}
	}
}

// TestWriteLogTightensExistingFilePermissions — a log created 0644 by an earlier
// build (or a careless touch) must not stay world-readable.
func TestWriteLogTightensExistingFilePermissions(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"DocEntry":1}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	logPath := os.Getenv("SAPB1_WRITE_LOG")
	if err := os.WriteFile(logPath, []byte(""), 0o644); err != nil {
		t.Fatalf("seeding a 0644 log: %v", err)
	}

	if _, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Fatalf("Create: %v", err)
	}

	fi, err := os.Stat(logPath)
	if err != nil {
		t.Fatalf("stat: %v", err)
	}
	if perm := fi.Mode().Perm(); perm != 0o600 {
		t.Errorf("write log mode = %04o, want 0600", perm)
	}
}

// TestWriteLogFailureWarnsOnceAndStillWrites — an unwritable log must never fail
// the write, but it must not be silent either.
func TestWriteLogFailureWarnsOnceAndStillWrites(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{"DocEntry":4321}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	// Point the log at a path that cannot exist (a file inside a file).
	blocker := filepath.Join(t.TempDir(), "not-a-dir")
	if err := os.WriteFile(blocker, []byte("x"), 0o600); err != nil {
		t.Fatalf("seeding blocker: %v", err)
	}
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(blocker, "writes.jsonl"))

	var warnings bytes.Buffer
	c.SetErrWriter(&warnings)

	res, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`))
	if err != nil {
		t.Fatalf("an unwritable log must not fail the write: %v", err)
	}
	if res.Status != http.StatusCreated {
		t.Errorf("status = %d, want 201", res.Status)
	}
	if !strings.Contains(warnings.String(), "write log unavailable") {
		t.Errorf("expected a warning about the write log, got: %q", warnings.String())
	}
	// Once per client, not once per log line (there are two per write).
	if n := strings.Count(warnings.String(), "write log unavailable"); n != 1 {
		t.Errorf("warning printed %d times, want exactly 1", n)
	}
}

// TestWriteLogMarksNonJSONPayload — the payload is never silently dropped.
func TestWriteLogMarksNonJSONPayload(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error":{"code":-1,"message":{"lang":"en-us","value":"not json"}}}`))
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	// Create is only ever called with validated JSON by the CLI, but the client
	// is exported: a caller that hands over garbage must still be logged honestly.
	_, _ = c.Create(context.Background(), "Drafts", []byte(`this is not json`))

	for _, e := range readWriteLog(t) {
		if len(e.Payload) != 0 {
			t.Errorf("non-JSON payload should not be embedded, got %s", e.Payload)
		}
		if !e.PayloadOmitted {
			t.Errorf("expected payload_omitted=true on %+v", e)
		}
	}
}

// TestWriteUsesLongerDefaultTimeout — writes must not inherit the short read
// timeout, because a client-side timeout is exactly the unknown-outcome case.
func TestWriteUsesLongerDefaultTimeout(t *testing.T) {
	cfg := &config.Config{Timeout: config.DefaultTimeout}
	c := New(cfg)
	if got := c.writeClient().Timeout; got != time.Duration(config.DefaultWriteTimeout)*time.Second {
		t.Errorf("default write timeout = %v, want %ds", got, config.DefaultWriteTimeout)
	}
	if c.http.Timeout != time.Duration(config.DefaultTimeout)*time.Second {
		t.Errorf("read timeout changed to %v — reads must be unaffected", c.http.Timeout)
	}

	// An explicit --timeout/SAPB1_TIMEOUT still wins, even a short one.
	explicit := New(&config.Config{Timeout: 7, TimeoutSet: true})
	if got := explicit.writeClient().Timeout; got != 7*time.Second {
		t.Errorf("explicit write timeout = %v, want 7s", got)
	}
}
