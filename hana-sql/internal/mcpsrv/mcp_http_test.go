package mcpsrv

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// None of these paths touch a database: initialize, tools/list, parse errors
// and argument validation all complete before any pool exists. testServer has
// DB == nil precisely so that is enforced rather than hoped for — any code path
// that reached the driver would nil-panic.
func testServer() *Server { return &Server{Log: nil} }

func postMCP(t *testing.T, h http.Handler, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
	// httptest defaults Host to example.com; a real client reaches this
	// loopback-bound endpoint by its loopback name, and the transport validates
	// Host as the anti-DNS-rebinding check.
	req.Host = "127.0.0.1:7706"
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func decodeRPC(t *testing.T, rec *httptest.ResponseRecorder) map[string]any {
	t.Helper()
	var m map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &m); err != nil {
		t.Fatalf("response is not JSON: %v\nbody: %s", err, rec.Body.String())
	}
	return m
}

func TestMCPHTTPInitialize(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(),
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	if ct := rec.Header().Get("Content-Type"); ct != "application/json" {
		t.Fatalf("Content-Type = %q, want application/json", ct)
	}
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	if result == nil {
		t.Fatalf("no result object in %s", rec.Body.String())
	}
	if pv := result["protocolVersion"]; pv != "2025-03-26" {
		t.Fatalf("protocolVersion = %v, want the client's 2025-03-26 echoed back", pv)
	}
	info, _ := result["serverInfo"].(map[string]any)
	if info["name"] != ServerName {
		t.Fatalf("serverInfo.name = %v, want %q", info["name"], ServerName)
	}
}

func TestMCPHTTPInitializeDefaultsProtocolVersion(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"2.0","id":1,"method":"initialize"}`)
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	if pv, _ := result["protocolVersion"].(string); pv == "" {
		t.Fatalf("protocolVersion = %v, want a default when the client sent none", result["protocolVersion"])
	}
}

func TestMCPHTTPNotificationAccepted(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"2.0","method":"notifications/initialized"}`)
	if rec.Code != http.StatusAccepted {
		t.Fatalf("status = %d, want 202; body: %s", rec.Code, rec.Body.String())
	}
	if rec.Body.Len() != 0 {
		t.Fatalf("notification response body = %q, want empty", rec.Body.String())
	}
}

func TestMCPHTTPInvalidJSON(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `{not json`)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	rpcErr, _ := m["error"].(map[string]any)
	if rpcErr == nil {
		t.Fatalf("no error object in %s", rec.Body.String())
	}
	if code, _ := rpcErr["code"].(float64); code != -32700 {
		t.Fatalf("error.code = %v, want -32700", rpcErr["code"])
	}
}

func TestMCPHTTPMethodNotAllowed(t *testing.T) {
	for _, method := range []string{http.MethodGet, http.MethodDelete, http.MethodPut} {
		req := httptest.NewRequest(method, "/mcp", nil)
		rec := httptest.NewRecorder()
		testServer().HTTPHandler().ServeHTTP(rec, req)
		if rec.Code != http.StatusMethodNotAllowed {
			t.Fatalf("%s status = %d, want 405", method, rec.Code)
		}
		if allow := rec.Header().Get("Allow"); allow != "POST" {
			t.Fatalf("%s Allow header = %q, want POST", method, allow)
		}
	}
}

func TestMCPHTTPBodyTooLarge(t *testing.T) {
	big := `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"hana_query","arguments":{"sql":"` +
		strings.Repeat("A", (4<<20)+1024) + `"}}}`
	rec := postMCP(t, testServer().HTTPHandler(), big)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400 for a body over the 4 MiB cap; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	rpcErr, _ := m["error"].(map[string]any)
	if code, _ := rpcErr["code"].(float64); code != -32700 {
		t.Fatalf("error.code = %v, want -32700", rpcErr["code"])
	}
}

func TestMCPHTTPUnknownMethod(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"2.0","id":9,"method":"resources/list"}`)
	m := decodeRPC(t, rec)
	rpcErr, _ := m["error"].(map[string]any)
	if rpcErr == nil {
		t.Fatalf("want a JSON-RPC error for an unimplemented method; got %s", rec.Body.String())
	}
	if code, _ := rpcErr["code"].(float64); code != -32601 {
		t.Fatalf("error.code = %v, want -32601", rpcErr["code"])
	}
}

func TestMCPHTTPPing(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"2.0","id":4,"method":"ping"}`)
	m := decodeRPC(t, rec)
	if _, ok := m["result"]; !ok {
		t.Fatalf("ping has no result: %s", rec.Body.String())
	}
}

func TestMCPHTTPToolsList(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(), `{"jsonrpc":"2.0","id":2,"method":"tools/list"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	tools, _ := result["tools"].([]any)
	var names []string
	for _, tool := range tools {
		tm, _ := tool.(map[string]any)
		name, _ := tm["name"].(string)
		names = append(names, name)
	}
	want := []string{"hana_query", "hana_tables", "hana_columns", "hana_doctor"}
	if len(names) != len(want) {
		t.Fatalf("tool names = %v, want exactly %v", names, want)
	}
	for i, n := range want {
		if names[i] != n {
			t.Fatalf("tool[%d] = %q, want %q (all: %v)", i, names[i], n, names)
		}
		// No hana_hana_ stutter: behind the gateway Prefix == StripPrefix ==
		// "hana_", so the rename is the identity in both directions.
		if strings.HasPrefix(n, "hana_hana_") {
			t.Fatalf("tool name %q stutters", n)
		}
	}
}

func TestMCPHTTPUnknownToolCall(t *testing.T) {
	rec := postMCP(t, testServer().HTTPHandler(),
		`{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"no_such_tool","arguments":{}}}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	if isErr, _ := result["isError"].(bool); !isErr {
		t.Fatalf("isError = %v, want true; body: %s", result["isError"], rec.Body.String())
	}
	content, _ := result["content"].([]any)
	if len(content) != 1 {
		t.Fatalf("content = %v, want one text item", content)
	}
	item, _ := content[0].(map[string]any)
	text, _ := item["text"].(string)
	if !strings.HasPrefix(text, "unknown tool: ") {
		t.Fatalf("text = %q, want prefix \"unknown tool: \"", text)
	}
}

// Stdio parity: an id-less message is a notification — no response, no error.
func TestHandleMessageNotificationIsSilent(t *testing.T) {
	resp, err := testServer().handleMessage(context.Background(), []byte(`{"jsonrpc":"2.0","method":"tools/list"}`))
	if err != nil {
		t.Fatalf("err = %v, want nil", err)
	}
	if resp != nil {
		t.Fatalf("resp = %+v, want nil for an id-less message", resp)
	}
}

func TestHandleMessageParseErrorIsAnError(t *testing.T) {
	resp, err := testServer().handleMessage(context.Background(), []byte(`{`))
	if err == nil {
		t.Fatal("want a parse error so the HTTP arm can answer -32700")
	}
	if resp != nil {
		t.Fatalf("resp = %+v, want nil on a parse error", resp)
	}
}
