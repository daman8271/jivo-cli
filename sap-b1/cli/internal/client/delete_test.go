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
	"testing"
	"time"

	"sapb1/internal/catalog"
	"sapb1/internal/errs"
)

// TestDeleteSendsNoBodyAndNoContentType — a DELETE carries nothing, and setting
// Content-Type on zero bytes just invites a proxy to have an opinion.
func TestDeleteSendsNoBodyAndNoContentType(t *testing.T) {
	var gotMethod, gotPath, gotContentType, gotCookie string
	var gotBody []byte

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		gotMethod = r.Method
		gotPath = r.URL.Path
		gotContentType = r.Header.Get("Content-Type")
		gotCookie = r.Header.Get("Cookie")
		gotBody, _ = io.ReadAll(r.Body)
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	res, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{
		Snapshot:  json.RawMessage(`{"DocEntry":54990,"CardCode":"V10000"}`),
		Overrides: []string{"not-created-here"},
		Origin:    &WriteOrigin{File: "queries/USER36/sap-writes.jsonl", Line: 2, User: "USER36", Time: time.Now()},
	})
	if err != nil {
		t.Fatalf("Delete returned error: %v", err)
	}
	if res.Status != http.StatusNoContent {
		t.Errorf("status = %d, want 204", res.Status)
	}
	if gotMethod != http.MethodDelete {
		t.Errorf("method = %s, want DELETE", gotMethod)
	}
	if gotPath != "/b1s/v1/Drafts(54990)" {
		t.Errorf("path = %s, want /b1s/v1/Drafts(54990)", gotPath)
	}
	if len(gotBody) != 0 {
		t.Errorf("a DELETE must carry no body, got %q", gotBody)
	}
	if gotContentType != "" {
		t.Errorf("no Content-Type for an empty body, got %q", gotContentType)
	}
	if !strings.Contains(gotCookie, "B1SESSION=") {
		t.Errorf("the session cookie must be attached, got %q", gotCookie)
	}

	entries := readWriteLog(t)
	if len(entries) != 2 {
		t.Fatalf("want an intent and an outcome, got %d: %+v", len(entries), entries)
	}
	intent, outcome := entries[0], entries[1]
	if intent.Event != logIntent || outcome.Event != logOutcome {
		t.Fatalf("intent must be logged first: %+v", entries)
	}
	// The shared log carries the HASH of the snapshot, never its contents: that
	// file is committed to a public repo and a snapshot holds the vendor, their
	// bill number and every line price. The contents go to the local snapshot log.
	if intent.SnapshotSHA256 == "" {
		t.Error("the intent line must carry the snapshot hash — it is what points at the only surviving copy")
	}
	if outcome.SnapshotSHA256 != "" {
		t.Error("the outcome line must not repeat the snapshot hash")
	}
	raw, err := os.ReadFile(os.Getenv("SAPB1_WRITE_LOG"))
	if err != nil {
		t.Fatalf("reading the write log: %v", err)
	}
	if strings.Contains(string(raw), "V10000") {
		t.Errorf("the snapshot's CONTENTS must not reach the committed write log:\n%s", raw)
	}

	snaps := readSnapshotLog(t)
	if len(snaps) != 1 {
		t.Fatalf("want one snapshot line, got %d", len(snaps))
	}
	if snaps[0].SHA256 != intent.SnapshotSHA256 {
		t.Errorf("the write log's hash %q does not point at the snapshot %q", intent.SnapshotSHA256, snaps[0].SHA256)
	}
	if !strings.Contains(string(snaps[0].Snapshot), "V10000") {
		t.Errorf("the local snapshot log must keep the contents, got %s", snaps[0].Snapshot)
	}
	if snaps[0].Path != "Drafts(54990)" {
		t.Errorf("the snapshot must name what it was, got %q", snaps[0].Path)
	}
	for _, e := range entries {
		if len(e.Payload) != 0 {
			t.Errorf("a DELETE has no payload, got %s", e.Payload)
		}
		if e.PayloadOmitted {
			t.Error("nothing was omitted — there was no payload to omit")
		}
		if e.Origin == nil || e.Origin.User != "USER36" || e.Origin.Line != 2 {
			t.Errorf("both lines must record the authorising origin, got %+v", e.Origin)
		}
		if len(e.Overrides) != 1 || e.Overrides[0] != "not-created-here" {
			t.Errorf("both lines must record the overrides, got %v", e.Overrides)
		}
	}
}

// TestDeleteRefusesEverySetButDrafts walks the whole embedded catalog. This, not
// the command tree, is what makes `DELETE Invoices(9)` inexpressible: a future
// caller inside this binary cannot widen it by passing a different string.
func TestDeleteRefusesEverySetButDrafts(t *testing.T) {
	hits := 0
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		hits++
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	allowed := map[string]bool{"Drafts": true, "PaymentDrafts": true}

	checked := 0
	for _, svc := range catalog.Services() {
		if allowed[svc.Service] {
			continue
		}
		checked++
		_, err := c.Delete(context.Background(), svc.Service, 1, DeleteOptions{})
		if err == nil {
			t.Fatalf("Delete(%q) must be refused", svc.Service)
		}
		var usage *errs.UsageError
		if !errors.As(err, &usage) {
			t.Fatalf("Delete(%q): want *errs.UsageError, got %T: %v", svc.Service, err, err)
		}
	}
	if checked < 50 {
		t.Fatalf("only %d entity sets were checked — the catalog did not load", checked)
	}

	// Nothing shaped like a path gets through either.
	for _, bad := range []string{"Drafts(1)/Cancel", "Drafts(1)", "drafts", "Drafts?$top=1", "", "../Login"} {
		if _, err := c.Delete(context.Background(), bad, 1, DeleteOptions{}); err == nil {
			t.Errorf("Delete(%q) must be refused", bad)
		}
	}
	// And neither does a non-positive key.
	for _, key := range []int64{0, -1} {
		if _, err := c.Delete(context.Background(), "Drafts", key, DeleteOptions{}); err == nil {
			t.Errorf("Delete(Drafts, %d) must be refused", key)
		}
	}

	if hits != 0 {
		t.Errorf("a refused Delete must send nothing, got %d request(s)", hits)
	}
	if _, err := os.Stat(os.Getenv("SAPB1_WRITE_LOG")); err == nil {
		t.Error("a refused Delete must not log — nothing was attempted")
	}
}

// TestDeleteRefusesWhenTheWriteLogIsUnwritable is the one place this tool puts
// the audit trail ahead of the operation. For a POST the object survives and SAP
// can be queried for it; for a DELETE the log line is the only record the draft
// ever existed.
func TestDeleteRefusesWhenTheWriteLogIsUnwritable(t *testing.T) {
	hits := 0
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		hits++
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	// A path whose parent does not exist: OpenFile cannot create it.
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "no", "such", "dir", "writes.jsonl"))

	_, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{})
	if err == nil {
		t.Fatal("expected Delete to refuse an unrecordable delete")
	}
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("want *errs.ConfigError (exit 3), got %T: %v", err, err)
	}
	for _, want := range []string{"A delete with no record is not allowed", "SAPB1_WRITE_LOG"} {
		if !strings.Contains(cfgErr.Msg, want) {
			t.Errorf("message must contain %q, got: %s", want, cfgErr.Msg)
		}
	}
	if hits != 0 {
		t.Errorf("nothing may reach SAP when the delete cannot be recorded, got %d request(s)", hits)
	}

	// The same broken log must NOT stop a Create: for a POST, warning and
	// carrying on is still the right trade.
	if _, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Errorf("Create must stay best-effort about the log, got: %v", err)
	}
	if hits != 1 {
		t.Errorf("the Create should have gone out, got %d request(s)", hits)
	}
}

// fakeCheckout builds a directory that looks like a registered JIVO checkout —
// both repo markers plus harness/.operator — and stands the test in it, so
// config.SharedWriteLogPath resolves inside the temp tree.
func fakeCheckout(t *testing.T, slug string) (root, sharedLog string) {
	t.Helper()
	root = t.TempDir()
	for _, d := range []string{"harness", ".git"} {
		if err := os.MkdirAll(filepath.Join(root, d), 0o755); err != nil {
			t.Fatalf("building the checkout: %v", err)
		}
	}
	reg := filepath.Join(root, "harness", ".operator")
	if err := os.WriteFile(reg, []byte(`{"slug":"`+slug+`"}`), 0o600); err != nil {
		t.Fatalf("registering the operator: %v", err)
	}
	t.Chdir(root)
	return root, filepath.Join(root, "queries", slug, "sap-writes.jsonl")
}

// TestDeleteAlwaysRecordsInTheCheckoutLog — $SAPB1_WRITE_LOG must not be able to
// take a delete out of the team's history.
//
// For a POST a diverted log costs an audit line: the object is in SAP and can be
// queried for. A DELETE leaves nothing behind, so `SAPB1_WRITE_LOG=/tmp/x sapb1
// delete draft …` used to destroy fifty drafts and leave the shared log with no
// trace they had ever existed — no forgery needed, a stale wrapper script does
// it by accident. The configured log is still written, so anything tailing it
// keeps working.
func TestDeleteAlwaysRecordsInTheCheckoutLog(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	_, sharedLog := fakeCheckout(t, "tester")

	scratch := filepath.Join(t.TempDir(), "scratch.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", scratch)

	if _, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{
		Snapshot: json.RawMessage(`{"DocEntry":54990}`),
	}); err != nil {
		t.Fatalf("Delete returned error: %v", err)
	}

	shared := parseWriteLog(t, sharedLog)
	if len(shared) != 2 {
		t.Fatalf("the checkout's log must carry the intent and the outcome, got %d line(s)", len(shared))
	}
	if shared[0].Path != "Drafts(54990)" || shared[0].Method != http.MethodDelete {
		t.Errorf("unexpected record in the shared log: %+v", shared[0])
	}
	// And the caller's own file still gets everything, so existing tooling works.
	if diverted := parseWriteLog(t, scratch); len(diverted) != 2 {
		t.Errorf("the configured log must still be written, got %d line(s)", len(diverted))
	}

	// A POST is unchanged: one destination, the configured one.
	if _, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Fatalf("Create returned error: %v", err)
	}
	if got := len(parseWriteLog(t, sharedLog)); got != 2 {
		t.Errorf("a POST must not be duplicated into the checkout log, got %d line(s)", got)
	}
}

// TestDeleteRefusesWhenTheCheckoutLogIsUnwritable — the checkout's log is the
// one that has to succeed. If it cannot be written the delete does not happen,
// even though the caller's own $SAPB1_WRITE_LOG is perfectly writable.
func TestDeleteRefusesWhenTheCheckoutLogIsUnwritable(t *testing.T) {
	hits := 0
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		hits++
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	_, sharedLog := fakeCheckout(t, "tester")
	t.Setenv("SAPB1_WRITE_LOG", filepath.Join(t.TempDir(), "scratch.jsonl"))

	// A directory where the log file should be: OpenFile cannot append to it.
	if err := os.MkdirAll(sharedLog, 0o755); err != nil {
		t.Fatalf("blocking the shared log: %v", err)
	}

	_, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{})
	if err == nil {
		t.Fatal("expected a refusal when the team's log cannot be written")
	}
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("want *errs.ConfigError (exit 3), got %T: %v", err, err)
	}
	if hits != 0 {
		t.Errorf("nothing may reach SAP when the delete cannot be recorded, got %d request(s)", hits)
	}
}

// TestDeleteRefusesWhenTheSnapshotCannotBeWritten — the snapshot is the only
// surviving copy of what the draft held, so it is a precondition too. It is also
// where the sensitive half of the trail lives, and it must never fall back to
// the committed log.
func TestDeleteRefusesWhenTheSnapshotCannotBeWritten(t *testing.T) {
	hits := 0
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		hits++
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	t.Setenv("SAPB1_SNAPSHOT_LOG", filepath.Join(t.TempDir(), "no", "such", "dir", "snapshots.jsonl"))

	_, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{
		Snapshot: json.RawMessage(`{"DocEntry":54990,"CardCode":"V10000"}`),
	})
	if err == nil {
		t.Fatal("expected a refusal when the snapshot cannot be recorded")
	}
	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("want *errs.ConfigError (exit 3), got %T: %v", err, err)
	}
	if !strings.Contains(cfgErr.Msg, "SAPB1_SNAPSHOT_LOG") {
		t.Errorf("the message must say how to fix it, got: %s", cfgErr.Msg)
	}
	if hits != 0 {
		t.Errorf("nothing may reach SAP when the snapshot cannot be recorded, got %d request(s)", hits)
	}
	if raw, err := os.ReadFile(os.Getenv("SAPB1_WRITE_LOG")); err == nil && strings.Contains(string(raw), "V10000") {
		t.Error("the snapshot must never fall back into the committed write log")
	}
}

// TestDeleteRelogsInOnce mirrors Create's 401 behaviour.
func TestDeleteRelogsInOnce(t *testing.T) {
	logins, deletes := 0, 0
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			logins++
			loginHandler(w)
			return
		}
		deletes++
		if deletes == 1 {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session"}}}`))
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	c := newFakeClient(t, srv)
	if _, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{}); err != nil {
		t.Fatalf("Delete returned error: %v", err)
	}
	if logins != 2 {
		t.Errorf("want exactly 2 logins (initial + one retry), got %d", logins)
	}
	if deletes != 2 {
		t.Errorf("want exactly 2 DELETEs, got %d", deletes)
	}
}

// TestDeleteTimeoutAdviceIsDeleteShaped — the POST advice ("a blind retry can
// create a duplicate") is exactly backwards for a DELETE, which cannot
// double-delete. What must not change is "look before you re-run".
func TestDeleteTimeoutAdviceIsDeleteShaped(t *testing.T) {
	release := make(chan struct{})
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		<-release
		w.WriteHeader(http.StatusNoContent)
	}))
	defer func() { close(release); srv.Close() }()

	c := newFakeClient(t, srv)
	c.cfg.Timeout = 1

	_, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{})
	if err == nil {
		t.Fatal("expected an error when the response never arrives")
	}
	var unknown *errs.WriteOutcomeUnknownError
	if !errors.As(err, &unknown) {
		t.Fatalf("want *errs.WriteOutcomeUnknownError, got %T: %v", err, err)
	}
	for _, want := range []string{
		"outcome is unknown",
		"MAY have been committed",
		`sapb1 query Drafts --filter "DocEntry eq 54990"`,
		"cannot create a duplicate",
	} {
		if !strings.Contains(unknown.Msg, want) {
			t.Errorf("delete advice must contain %q, got: %s", want, unknown.Msg)
		}
	}
}

// TestGetEntityReadsOneKeyedObject pins the read a delete is built on: a 404 is
// an answer, not an error.
func TestGetEntityReadsOneKeyedObject(t *testing.T) {
	t.Run("found", func(t *testing.T) {
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				loginHandler(w)
				return
			}
			if r.URL.Path != "/b1s/v1/Drafts(54990)" {
				t.Errorf("path = %s, want /b1s/v1/Drafts(54990)", r.URL.Path)
			}
			_, _ = w.Write([]byte(`{"DocEntry":54990}`))
		}))
		defer srv.Close()

		res, err := newFakeClient(t, srv).GetEntity(context.Background(), "Drafts", 54990)
		if err != nil {
			t.Fatalf("GetEntity returned error: %v", err)
		}
		if !res.Found || res.Status != 200 || !strings.Contains(string(res.Body), "54990") {
			t.Errorf("unexpected result: %+v", res)
		}
	})

	t.Run("404 is an answer", func(t *testing.T) {
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				loginHandler(w)
				return
			}
			w.WriteHeader(http.StatusNotFound)
			_, _ = w.Write([]byte(`{"error":{"code":-2028,"message":{"lang":"en-us","value":"No matching records found (ODBC -2028)"}}}`))
		}))
		defer srv.Close()

		res, err := newFakeClient(t, srv).GetEntity(context.Background(), "Drafts", 54990)
		if err != nil {
			t.Fatalf("a 404 must not be an error: %v", err)
		}
		if res.Found {
			t.Error("Found must be false for a 404")
		}
	})

	t.Run("other failures still are errors", func(t *testing.T) {
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				loginHandler(w)
				return
			}
			w.WriteHeader(http.StatusForbidden)
			_, _ = w.Write([]byte(`{"error":{"code":-1,"message":{"lang":"en-us","value":"No authorization"}}}`))
		}))
		defer srv.Close()

		_, err := newFakeClient(t, srv).GetEntity(context.Background(), "Drafts", 54990)
		var apiErr *errs.APIError
		if !errors.As(err, &apiErr) {
			t.Fatalf("want *errs.APIError, got %T: %v", err, err)
		}
	})

	t.Run("re-logs in once on 401", func(t *testing.T) {
		logins, gets := 0, 0
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				logins++
				loginHandler(w)
				return
			}
			gets++
			if gets == 1 {
				w.WriteHeader(http.StatusUnauthorized)
				_, _ = w.Write([]byte(`{"error":{"code":301,"message":{"lang":"en-us","value":"Invalid session"}}}`))
				return
			}
			_, _ = w.Write([]byte(`{"DocEntry":54990}`))
		}))
		defer srv.Close()

		res, err := newFakeClient(t, srv).GetEntity(context.Background(), "Drafts", 54990)
		if err != nil {
			t.Fatalf("GetEntity returned error: %v", err)
		}
		if !res.Found || logins != 2 || gets != 2 {
			t.Errorf("want one re-login and two GETs, got logins=%d gets=%d found=%v", logins, gets, res.Found)
		}
	})

	t.Run("refuses a path or a bad key without asking SAP", func(t *testing.T) {
		hits := 0
		srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/b1s/v1/Login" {
				loginHandler(w)
				return
			}
			hits++
			w.WriteHeader(http.StatusOK)
		}))
		defer srv.Close()

		c := newFakeClient(t, srv)
		for _, bad := range []string{"Drafts(1)", "Drafts?$top=1", "Drafts/Cancel", "", "../Login"} {
			if _, err := c.GetEntity(context.Background(), bad, 1); err == nil {
				t.Errorf("GetEntity(%q) must be refused", bad)
			}
		}
		for _, key := range []int64{0, -5} {
			if _, err := c.GetEntity(context.Background(), "Drafts", key); err == nil {
				t.Errorf("GetEntity(Drafts, %d) must be refused", key)
			}
		}
		if hits != 0 {
			t.Errorf("a refused GetEntity must send nothing, got %d request(s)", hits)
		}
	})
}

// TestCreateLogLinesGainNothing — the new fields are delete-only. A POST's log
// line must look exactly as it always has, or every existing log parser breaks.
func TestCreateLogLinesGainNothing(t *testing.T) {
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
	if _, err := c.Create(context.Background(), "Drafts", []byte(`{"CardCode":"C0001"}`)); err != nil {
		t.Fatalf("Create returned error: %v", err)
	}

	data, err := os.ReadFile(os.Getenv("SAPB1_WRITE_LOG"))
	if err != nil {
		t.Fatalf("reading write log: %v", err)
	}
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		var raw map[string]interface{}
		if err := json.Unmarshal([]byte(line), &raw); err != nil {
			t.Fatalf("log line is not JSON: %v", err)
		}
		for _, k := range []string{"snapshot", "snapshot_sha256", "overrides", "origin"} {
			if _, has := raw[k]; has {
				t.Errorf("a POST log line must not carry %q: %s", k, line)
			}
		}
		if raw["payload"] == nil {
			t.Errorf("a POST must still record its payload: %s", line)
		}
	}
}
