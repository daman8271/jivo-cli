package client

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"sapb1/internal/errs"
)

// TestUnwritableCheckoutLogRefusalGivesAdviceThatWorks — the refusal for an
// unwritable log ends with "fix the log path (or set $SAPB1_WRITE_LOG to
// somewhere writable) and re-run". The second half of that cannot work.
//
// The log that blocks the delete is the CHECKOUT's, and SharedWriteLogPath
// ignores $SAPB1_WRITE_LOG on purpose — that is the whole point of
// TestDeleteAlwaysRecordsInTheCheckoutLog. So an operator who does exactly what
// the message says, and points the variable at a writable file, gets the
// identical refusal a second time with nothing changed. The only fix is
// permissions on queries/<operator>/sap-writes.jsonl, which the message never
// names.
//
// Fail-closed, so nothing is destroyed. It was still a dead end printed at the
// one moment an operator is already stuck, and the same shape as the negative
// --older-than suggestion: advice that reads like a way out and is not one.
//
// Verified against the built binary before the fix: with
// queries/tester/sap-writes.jsonl at mode 444 and
// SAPB1_WRITE_LOG=/tmp/prooflab/writable.jsonl (mode 644, empty), the run exited
// 3 with the same message, sent 0 DELETEs and wrote 0 lines to the writable file.
func TestUnwritableCheckoutLogRefusalGivesAdviceThatWorks(t *testing.T) {
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

	// The operator has already done what the message told them to.
	writable := filepath.Join(t.TempDir(), "writable.jsonl")
	t.Setenv("SAPB1_WRITE_LOG", writable)

	// A directory where the shared log file should be: OpenFile cannot append.
	if err := os.MkdirAll(sharedLog, 0o755); err != nil {
		t.Fatalf("blocking the shared log: %v", err)
	}

	_, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{})

	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("want *errs.ConfigError (exit 3), got %T: %v", err, err)
	}
	if hits != 0 {
		t.Errorf("nothing may reach SAP when the delete cannot be recorded, got %d request(s)", hits)
	}
	if strings.Contains(cfgErr.Msg, "SAPB1_WRITE_LOG") {
		t.Errorf("the refusal offers a remedy the delete path ignores; it should name %s instead:\n%s", sharedLog, cfgErr.Msg)
	}
	if !strings.Contains(cfgErr.Msg, "queries/") {
		t.Errorf("the refusal never names the file that has to become writable:\n%s", cfgErr.Msg)
	}
}

// TestNoIntentLineSurvivesAHalfWritableFanOut — a delete's intent line goes to
// TWO files, shared first and configured second. Written one at a time, an
// unwritable SECOND target left the FIRST holding an intent with no outcome —
// and an intent with no outcome is precisely how this tool spells "sent, outcome
// unknown". So a delete that never left the machine published a phantom into the
// committed, shared history and then refused.
//
// Nothing may be written until every target has been proved writable.
func TestNoIntentLineSurvivesAHalfWritableFanOut(t *testing.T) {
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
	_, sharedLog := fakeCheckout(t, "tester") // target 1: perfectly writable

	// Target 2, blocked: a directory where the file should be.
	blocked := filepath.Join(t.TempDir(), "scratch.jsonl")
	if err := os.MkdirAll(blocked, 0o755); err != nil {
		t.Fatalf("blocking the configured log: %v", err)
	}
	t.Setenv("SAPB1_WRITE_LOG", blocked)

	_, err := c.Delete(context.Background(), "Drafts", 54990, DeleteOptions{
		Snapshot: json.RawMessage(`{"DocEntry":54990,"CardCode":"V10000"}`),
	})

	var cfgErr *errs.ConfigError
	if !errors.As(err, &cfgErr) {
		t.Fatalf("want *errs.ConfigError (exit 3), got %T: %v", err, err)
	}
	if hits != 0 {
		t.Errorf("nothing may reach SAP when the delete cannot be recorded, got %d request(s)", hits)
	}
	if !strings.Contains(cfgErr.Msg, "SAPB1_WRITE_LOG") {
		t.Errorf("the blocked file IS the one $SAPB1_WRITE_LOG chose, so the message should say so:\n%s", cfgErr.Msg)
	}

	raw, readErr := os.ReadFile(sharedLog)
	if readErr != nil && !os.IsNotExist(readErr) {
		t.Fatalf("reading the shared log: %v", readErr)
	}
	if len(strings.TrimSpace(string(raw))) != 0 {
		t.Errorf("the shared log must hold NO line for a delete that never went:\n%s", raw)
	}
	// The snapshot is written before the request too, and it is equally premature.
	if snaps := os.Getenv("SAPB1_SNAPSHOT_LOG"); snaps != "" {
		if data, err := os.ReadFile(snaps); err == nil && strings.Contains(string(data), "V10000") {
			t.Errorf("nothing was destroyed, so no snapshot may be recorded:\n%s", data)
		}
	}
}
