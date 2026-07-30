package cli

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

// None of these paths touch the database: initialize / tools/list / parse
// errors are handled before any pool exists, and tools/call with an unknown
// name returns from mcpDispatch before any DB use.
func testApp() *App { return &App{Flags: &GlobalFlags{}} }

func postMCP(t *testing.T, h http.Handler, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(http.MethodPost, "/mcp", strings.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json, text/event-stream")
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
	rec := postMCP(t, mcpHTTPHandler(testApp()),
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
		t.Fatalf("protocolVersion = %v, want echoed 2025-03-26", pv)
	}
}

func TestMCPHTTPNotificationAccepted(t *testing.T) {
	rec := postMCP(t, mcpHTTPHandler(testApp()),
		`{"jsonrpc":"2.0","method":"notifications/initialized"}`)
	if rec.Code != http.StatusAccepted {
		t.Fatalf("status = %d, want 202; body: %s", rec.Code, rec.Body.String())
	}
	if rec.Body.Len() != 0 {
		t.Fatalf("notification response body = %q, want empty", rec.Body.String())
	}
}

func TestMCPHTTPInvalidJSON(t *testing.T) {
	rec := postMCP(t, mcpHTTPHandler(testApp()), `{not json`)
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
	for _, method := range []string{http.MethodGet, http.MethodDelete} {
		req := httptest.NewRequest(method, "/mcp", nil)
		rec := httptest.NewRecorder()
		mcpHTTPHandler(testApp()).ServeHTTP(rec, req)
		if rec.Code != http.StatusMethodNotAllowed {
			t.Fatalf("%s status = %d, want 405", method, rec.Code)
		}
		if allow := rec.Header().Get("Allow"); allow != "POST" {
			t.Fatalf("%s Allow header = %q, want POST", method, allow)
		}
	}
}

func TestMCPHTTPToolsList(t *testing.T) {
	rec := postMCP(t, mcpHTTPHandler(testApp()),
		`{"jsonrpc":"2.0","id":2,"method":"tools/list"}`)
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
	want := []string{"postgres_query", "list_databases", "list_tables", "describe_table", "search", "schema_dump"}
	if len(names) != len(want) {
		t.Fatalf("tool names = %v, want exactly %v", names, want)
	}
	for i, n := range want {
		if names[i] != n {
			t.Fatalf("tool[%d] = %q, want %q (all: %v)", i, names[i], n, names)
		}
	}
}

func TestMCPHTTPUnknownToolCall(t *testing.T) {
	rec := postMCP(t, mcpHTTPHandler(testApp()),
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
func TestMCPHandleMessageNotificationIsSilent(t *testing.T) {
	resp, err := mcpHandleMessage(testApp(), []byte(`{"jsonrpc":"2.0","method":"tools/list"}`))
	if err != nil {
		t.Fatalf("err = %v, want nil", err)
	}
	if resp != nil {
		t.Fatalf("resp = %+v, want nil for id-less message", resp)
	}
}
