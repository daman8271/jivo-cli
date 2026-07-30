package mcp

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"
)

// postMCP POSTs one JSON-RPC message to the streamable HTTP endpoint the way a
// real MCP client would (Content-Type: application/json, Accept including
// text/event-stream), deliberately sending NO Mcp-Session-Id header — the
// server runs stateless and must not require one.
func postMCP(t *testing.T, url, body string) (*http.Response, []byte) {
	t.Helper()
	req, err := http.NewRequest(http.MethodPost, url, strings.NewReader(body))
	if err != nil {
		t.Fatalf("building request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("POST %s: %v", url, err)
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("reading response body: %v", err)
	}
	return resp, raw
}

// TestStreamableHTTPTransport serves the exact same Server over mcp-go's
// streamable HTTP transport (stateless) and drives initialize + tools/list
// through real HTTP, verifying the identical read-only tool surface is
// advertised. httptest binds a loopback host, which passes mcp-go's built-in
// DNS-rebinding (localhost) protection.
func TestStreamableHTTPTransport(t *testing.T) {
	s := newTestServer()
	ts := httptest.NewServer(s.newStreamableServer())
	defer ts.Close()
	endpoint := ts.URL + "/mcp"

	// initialize
	initReq := `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test-http","version":"0"}}}`
	resp, raw := postMCP(t, endpoint, initReq)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("initialize: status = %d, want 200; body: %s", resp.StatusCode, raw)
	}
	var initParsed struct {
		Result struct {
			ServerInfo struct {
				Name string `json:"name"`
			} `json:"serverInfo"`
		} `json:"result"`
	}
	if err := json.Unmarshal(raw, &initParsed); err != nil {
		t.Fatalf("parsing initialize response %s: %v", raw, err)
	}
	if got := initParsed.Result.ServerInfo.Name; got != "sapb1" {
		t.Fatalf("serverInfo.name = %q, want %q (body: %s)", got, "sapb1", raw)
	}

	// tools/list — no Mcp-Session-Id header on purpose: stateless mode must
	// serve it without one.
	listReq := `{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}`
	resp, raw = postMCP(t, endpoint, listReq)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("tools/list: status = %d, want 200; body: %s", resp.StatusCode, raw)
	}
	var listParsed struct {
		Result struct {
			Tools []struct {
				Name string `json:"name"`
			} `json:"tools"`
		} `json:"result"`
	}
	if err := json.Unmarshal(raw, &listParsed); err != nil {
		t.Fatalf("parsing tools/list response %s: %v", raw, err)
	}

	var got []string
	for _, tl := range listParsed.Result.Tools {
		got = append(got, tl.Name)
	}
	sort.Strings(got)

	if len(got) != len(wantTools) {
		t.Fatalf("HTTP transport advertised %d tools, want %d\n got:  %v\n want: %v", len(got), len(wantTools), got, wantTools)
	}
	for i := range wantTools {
		if got[i] != wantTools[i] {
			t.Fatalf("HTTP transport tool set mismatch\n got:  %v\n want: %v", got, wantTools)
		}
	}
}

// postToolCall drives ONE tools/call over the streamable HTTP endpoint and
// returns (isError, text). It takes no *testing.T so it is safe to call from a
// goroutine — the concurrency test below needs many callers at once.
//
// A streamable-HTTP response may arrive either as plain JSON or as a
// single-event SSE frame, depending on negotiation, so both are accepted.
func postToolCall(url, name string, args map[string]any) (isError bool, text string, err error) {
	payload, err := json.Marshal(map[string]any{
		"jsonrpc": "2.0", "id": 7, "method": "tools/call",
		"params": map[string]any{"name": name, "arguments": args},
	})
	if err != nil {
		return false, "", err
	}
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(payload))
	if err != nil {
		return false, "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return false, "", err
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return false, "", err
	}
	if resp.StatusCode != http.StatusOK {
		return false, "", fmt.Errorf("tools/call %s: HTTP %d: %s", name, resp.StatusCode, raw)
	}
	return parseToolCallResponse(sseUnwrap(raw))
}

// sseUnwrap returns the JSON payload of a single-event SSE frame, or the input
// unchanged when it is already plain JSON.
func sseUnwrap(raw []byte) []byte {
	if !bytes.HasPrefix(bytes.TrimSpace(raw), []byte("event:")) && !bytes.HasPrefix(bytes.TrimSpace(raw), []byte("data:")) {
		return raw
	}
	for _, line := range bytes.Split(raw, []byte("\n")) {
		if bytes.HasPrefix(line, []byte("data:")) {
			return bytes.TrimSpace(bytes.TrimPrefix(line, []byte("data:")))
		}
	}
	return raw
}

// httpEndpoint serves one fake-backed Server over streamable HTTP and returns
// its /mcp URL.
func httpEndpoint(t *testing.T, s *Server) string {
	t.Helper()
	ts := httptest.NewServer(s.newStreamableServer())
	t.Cleanup(ts.Close)
	return ts.URL + "/mcp"
}

// TestToolsCallOverHTTPActuallyReadsSAP closes the gap the review found: the
// HTTP transport — the one published through the gateway — had NO tools/call
// coverage at all. Every earlier test drove tools/call through the in-process
// JSON-RPC handler instead, so nothing proved the transport agents actually use
// can execute a tool, scope a company, or count.
func TestToolsCallOverHTTPActuallyReadsSAP(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 2184, pageSize: 100, honourPrefer: true})
	endpoint := httpEndpoint(t, f.server())

	isErr, text, err := postToolCall(endpoint, "sapb1_query", map[string]any{
		"entity": "BusinessPartners", "company": "JIVO_MART_HANADB", "top": 3.0,
	})
	if err != nil {
		t.Fatalf("tools/call over HTTP: %v", err)
	}
	if isErr {
		t.Fatalf("tools/call over HTTP returned a tool error: %s", text)
	}
	var got rowsResponse
	if err := json.Unmarshal([]byte(text), &got); err != nil {
		t.Fatalf("HTTP tool result is not a rows response (%v): %s", err, text)
	}
	if got.RowsInPage != 3 {
		t.Errorf("rows_in_page = %d, want 3", got.RowsInPage)
	}
	if got.Company != "JIVO_MART_HANADB" {
		t.Errorf("company = %q, want JIVO_MART_HANADB", got.Company)
	}
	if got.TotalCount == nil || *got.TotalCount != 2184 {
		t.Errorf("total_count = %v, want 2184", got.TotalCount)
	}
	// The company must have reached the LOGIN, not just the echo.
	if logins := f.logins(); len(logins) != 1 || logins[0] != "JIVO_MART_HANADB" {
		t.Errorf("HTTP call logged in as %v, want [JIVO_MART_HANADB]", logins)
	}
}

// TestToolsCallOverHTTPRejectsUnknownArguments — the D2 guarantee must hold on
// the transport that is actually exposed, not only in-process.
func TestToolsCallOverHTTPRejectsUnknownArguments(t *testing.T) {
	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 10})
	endpoint := httpEndpoint(t, f.server())

	isErr, text, err := postToolCall(endpoint, "sapb1_query", map[string]any{
		"entity": "Orders", "companyDB": "JIVO_MART_HANADB",
	})
	if err != nil {
		t.Fatalf("tools/call over HTTP: %v", err)
	}
	if !isErr {
		t.Fatalf("HTTP transport ACCEPTED an unknown argument and answered anyway: %s", text)
	}
	if !strings.Contains(text, "companyDB") || !strings.Contains(text, "valid parameters:") {
		t.Errorf("rejection must name the key and list the valid ones, got: %s", text)
	}
	if len(f.seen()) != 0 {
		t.Errorf("a rejected call still reached SAP: %v", f.seen())
	}
}

// TestConcurrentToolCallsOverHTTPShareOneLogin is the login-storm regression at
// the layer where it was measured. HTTP is the transport behind the gateway and
// agents batch tool calls, so concurrent execution is the normal case: before
// the shared session store, 30 parallel calls opened 29 SAP sessions, each
// holding a licensed Service Layer slot for its full TTL with no Logout.
func TestConcurrentToolCallsOverHTTPShareOneLogin(t *testing.T) {
	const parallel = 30

	isolateHome(t)
	f := newFakeSAP(t, &fakeSAP{total: 100, pageSize: 100, honourPrefer: true, loginDelay: 20 * time.Millisecond})
	endpoint := httpEndpoint(t, f.server())

	var wg sync.WaitGroup
	start := make(chan struct{})
	errCh := make(chan error, parallel)
	for i := 0; i < parallel; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			<-start
			isErr, text, err := postToolCall(endpoint, "sapb1_query", map[string]any{"entity": "Orders", "top": 5.0})
			switch {
			case err != nil:
				errCh <- err
			case isErr:
				errCh <- fmt.Errorf("call %d: %s", i, text)
			}
		}(i)
	}
	close(start)
	wg.Wait()
	close(errCh)
	for err := range errCh {
		t.Fatalf("%v", err)
	}

	if logins := f.logins(); len(logins) != 1 {
		t.Errorf("%d concurrent tools/call over HTTP cost %d Logins, want 1: %v", parallel, len(logins), logins)
	}
	if n := len(f.gets()); n != parallel {
		t.Errorf("GETs = %d, want %d", n, parallel)
	}
	// RULE 0 at the wire, on the transport that is actually published.
	for _, r := range f.seen() {
		switch {
		case r.Method == http.MethodGet:
		case r.Method == http.MethodPost && (strings.HasSuffix(r.Path, "/Login") || strings.HasSuffix(r.Path, "/Logout")):
		default:
			t.Errorf("RULE 0 VIOLATION over HTTP: %s %s", r.Method, r.Path)
		}
	}
}
