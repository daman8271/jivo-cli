package client

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"strconv"
	"strings"
	"sync"
	"testing"

	"sapb1/internal/config"
)

// TestWriteLogSurvivesConcurrentDeletes — the write log is the ONLY surviving
// copy of a deleted draft, and it is a single file that every sapb1 on the box
// appends to (queries/<operator>/sap-writes.jsonl). The acc/ batch tooling runs
// drafts 50 at a time, and nothing stops an operator opening a second terminal
// while a batch is running.
//
// A DELETE line is not small — it carries the whole snapshot — so a torn write
// is not theoretical: that is exactly the size of write that splits if the log
// is opened without O_APPEND, or buffered across a boundary. If a line tears,
// two things break at once: the record of what was destroyed is unreadable, AND
// the provenance guard reads a corrupt file for every later delete.
//
// One Client per goroutine on purpose — that is the production shape (one
// process, one client) multiplied, not one Client shared, which nothing does.
func TestWriteLogSurvivesConcurrentDeletes(t *testing.T) {
	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/b1s/v1/Login" {
			loginHandler(w)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()

	// newFakeClient plants HOME and SAPB1_WRITE_LOG for the whole test; every
	// client built below lands in the same log, like several processes would.
	first := newFakeClient(t, srv)
	logPath := os.Getenv("SAPB1_WRITE_LOG")

	u, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatalf("parsing the test server URL: %v", err)
	}
	port, err := strconv.Atoi(u.Port())
	if err != nil {
		t.Fatalf("parsing the test server port: %v", err)
	}
	newClient := func() *Client {
		c := New(&config.Config{
			Host: u.Hostname(), Port: port, CompanyDB: "TESTDB",
			User: "tester", Password: testPassword, Insecure: true,
			Timeout: 5, TimeoutSet: true,
		})
		c.SetErrWriter(io.Discard)
		return c
	}

	// A snapshot big enough that a torn write would be obvious, and shaped like
	// the real thing: header fields plus lines.
	lines := make([]map[string]interface{}, 0, 40)
	for i := 0; i < 40; i++ {
		lines = append(lines, map[string]interface{}{
			"LineNum": i, "ItemCode": "RM0000052", "Quantity": 10, "LineTotal": 214500,
			"ItemDescription": strings.Repeat("MUSTARD OIL 1L ", 20),
		})
	}
	snapBody, err := json.Marshal(map[string]interface{}{
		"DocEntry": 54990, "CardCode": "VENDA000939",
		"CardName": "TPAC PACKAGING INDIA PVT LTD II", "DocumentLines": lines,
	})
	if err != nil {
		t.Fatalf("building the snapshot: %v", err)
	}

	const n = 24
	clients := make([]*Client, n)
	clients[0] = first
	for i := 1; i < n; i++ {
		clients[i] = newClient()
	}

	var wg sync.WaitGroup
	errCh := make(chan error, n)
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			_, err := clients[i].Delete(context.Background(), "Drafts", int64(50000+i), DeleteOptions{
				Snapshot:  json.RawMessage(snapBody),
				Overrides: []string{"not-created-here"},
			})
			errCh <- err
		}(i)
	}
	wg.Wait()
	close(errCh)
	for err := range errCh {
		if err != nil {
			t.Fatalf("concurrent Delete failed: %v", err)
		}
	}

	// Every line must parse — parseWriteLog fails the test on the first that does not.
	entries := parseWriteLog(t, logPath)
	if len(entries) != 2*n {
		t.Fatalf("want %d log lines (an intent and an outcome each), got %d", 2*n, len(entries))
	}
	intents, outcomes := 0, 0
	seen := map[string]int{}
	shas := map[string]bool{}
	for _, e := range entries {
		switch e.Event {
		case logIntent:
			intents++
			if e.SnapshotSHA256 == "" {
				t.Errorf("an intent line lost its snapshot hash: %+v", e)
			}
			shas[e.SnapshotSHA256] = true
		case logOutcome:
			outcomes++
		}
		seen[e.Path]++
	}

	// The big line is now the SNAPSHOT line, so that is where a torn write would
	// show. readSnapshotLog fails on the first that does not parse.
	snaps := readSnapshotLog(t)
	if len(snaps) != n {
		t.Fatalf("want %d snapshot lines, got %d", n, len(snaps))
	}
	for _, s := range snaps {
		if !shas[s.SHA256] {
			t.Errorf("snapshot %s is in no write-log line — the trail does not join up", s.SHA256)
		}
		if !strings.Contains(string(s.Snapshot), "TPAC PACKAGING") {
			t.Errorf("a snapshot line came back short: %s", s.Snapshot)
		}
	}
	// And none of it reached the file that gets committed.
	committed, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("reading the write log: %v", err)
	}
	if strings.Contains(string(committed), "TPAC PACKAGING") {
		t.Error("snapshot contents reached the committed write log")
	}
	if intents != n || outcomes != n {
		t.Errorf("intents = %d, outcomes = %d, want %d each", intents, outcomes, n)
	}
	for path, count := range seen {
		if count != 2 {
			t.Errorf("%s has %d line(s), want exactly an intent and an outcome", path, count)
		}
	}
}
