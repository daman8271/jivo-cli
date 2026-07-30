package gateway

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// None of these tests reach a backend: initialize / ping / whitelist rejections
// / parse errors are answered natively, and tools/list here runs against a
// gateway with zero configured backends.
func testGateway(t *testing.T, backends ...BackendConf) *Gateway {
	t.Helper()
	cfg := DefaultConfig()
	cfg.Backends = backends
	return New(cfg, "test")
}

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

// toolNames pulls result.tools[].name out of a tools/list response.
func toolNames(t *testing.T, rec *httptest.ResponseRecorder) []string {
	t.Helper()
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	tools, _ := result["tools"].([]any)
	names := make([]string, 0, len(tools))
	for _, tool := range tools {
		tm, _ := tool.(map[string]any)
		name, _ := tm["name"].(string)
		names = append(names, name)
	}
	return names
}

// toolResultOf pulls result.content[0].text and result.isError out of a
// tools/call response.
func toolResultOf(t *testing.T, rec *httptest.ResponseRecorder) (string, bool) {
	t.Helper()
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	if result == nil {
		t.Fatalf("no result object in %s", rec.Body.String())
	}
	isErr, _ := result["isError"].(bool)
	content, _ := result["content"].([]any)
	if len(content) != 1 {
		t.Fatalf("content = %v, want one text item; body: %s", content, rec.Body.String())
	}
	item, _ := content[0].(map[string]any)
	text, _ := item["text"].(string)
	return text, isErr
}

func TestHTTPInitialize(t *testing.T) {
	rec := postMCP(t, testGateway(t).Handler(),
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	if ct := rec.Header().Get("Content-Type"); ct != "application/json" {
		t.Fatalf("Content-Type = %q, want application/json", ct)
	}
	if sid := rec.Header().Get("Mcp-Session-Id"); sid != "" {
		t.Fatalf("front side emitted Mcp-Session-Id = %q, want none (stateless)", sid)
	}
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	if result == nil {
		t.Fatalf("no result object in %s", rec.Body.String())
	}
	if pv := result["protocolVersion"]; pv != "2025-03-26" {
		t.Fatalf("protocolVersion = %v, want echoed 2025-03-26", pv)
	}
	info, _ := result["serverInfo"].(map[string]any)
	if info["name"] != "jivo-gateway" || info["version"] != "test" {
		t.Fatalf("serverInfo = %v, want name jivo-gateway version test", info)
	}
	caps, _ := result["capabilities"].(map[string]any)
	if _, ok := caps["tools"]; !ok {
		t.Fatalf("capabilities = %v, want a tools object", caps)
	}
	instr, _ := result["instructions"].(string)
	for _, want := range []string{"read-only", "sap_", "pg_", "ecom_", "oms_", "fct_", "gateway_status"} {
		if !strings.Contains(instr, want) {
			t.Fatalf("instructions missing %q: %q", want, instr)
		}
	}
}

func TestHTTPInitializeDefaultsProtocolVersion(t *testing.T) {
	rec := postMCP(t, testGateway(t).Handler(), `{"jsonrpc":"2.0","id":1,"method":"initialize"}`)
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	if pv := result["protocolVersion"]; pv != "2024-11-05" {
		t.Fatalf("protocolVersion = %v, want default 2024-11-05", pv)
	}
}

func TestHTTPPing(t *testing.T) {
	rec := postMCP(t, testGateway(t).Handler(), `{"jsonrpc":"2.0","id":9,"method":"ping"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	if got := strings.TrimSpace(rec.Body.String()); got != `{"jsonrpc":"2.0","id":9,"result":{}}` {
		t.Fatalf("ping body = %s, want an empty result object", got)
	}
}

func TestHTTPNotificationAccepted(t *testing.T) {
	rec := postMCP(t, testGateway(t).Handler(), `{"jsonrpc":"2.0","method":"notifications/initialized"}`)
	if rec.Code != http.StatusAccepted {
		t.Fatalf("status = %d, want 202; body: %s", rec.Code, rec.Body.String())
	}
	if rec.Body.Len() != 0 {
		t.Fatalf("notification response body = %q, want empty", rec.Body.String())
	}
}

func TestHTTPInvalidJSON(t *testing.T) {
	rec := postMCP(t, testGateway(t).Handler(), `{not json`)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	if m["id"] != nil {
		t.Fatalf("id = %v, want null", m["id"])
	}
	rpcErr, _ := m["error"].(map[string]any)
	if rpcErr == nil {
		t.Fatalf("no error object in %s", rec.Body.String())
	}
	if code, _ := rpcErr["code"].(float64); code != -32700 {
		t.Fatalf("error.code = %v, want -32700", rpcErr["code"])
	}
}

func TestHTTPMethodNotAllowed(t *testing.T) {
	for _, method := range []string{http.MethodGet, http.MethodDelete} {
		req := httptest.NewRequest(method, "/mcp", nil)
		rec := httptest.NewRecorder()
		testGateway(t).Handler().ServeHTTP(rec, req)
		if rec.Code != http.StatusMethodNotAllowed {
			t.Fatalf("%s status = %d, want 405", method, rec.Code)
		}
		if allow := rec.Header().Get("Allow"); allow != "POST" {
			t.Fatalf("%s Allow header = %q, want POST", method, allow)
		}
	}
}

// A body over the 4 MiB cap is refused by MaxBytesReader and reported as a
// parse error, never buffered whole.
func TestHTTPBodyTooLarge(t *testing.T) {
	big := `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"pg_postgres_query","arguments":{"sql":"` +
		strings.Repeat("x", httpBodyLimit+1024) + `"}}}`
	rec := postMCP(t, testGateway(t).Handler(), big)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	rpcErr, _ := m["error"].(map[string]any)
	if code, _ := rpcErr["code"].(float64); code != -32700 {
		t.Fatalf("error.code = %v, want -32700; body: %s", rpcErr["code"], rec.Body.String())
	}
}

// N16. An explicit null id is a notification, not a request with id null.
// JSON-RPC 2.0 has no request with a null id, and clients do send it.
func TestHTTPNullIDIsNotification(t *testing.T) {
	for _, body := range []string{
		`{"jsonrpc":"2.0","id":null,"method":"tools/list"}`,
		`{"jsonrpc":"2.0","id": null ,"method":"ping"}`,
		`{"jsonrpc":"2.0","id":null,"method":"resources/list"}`,
	} {
		rec := postMCP(t, testGateway(t).Handler(), body)
		if rec.Code != http.StatusAccepted {
			t.Fatalf("%s status = %d, want 202; body: %s", body, rec.Code, rec.Body.String())
		}
		if rec.Body.Len() != 0 {
			t.Fatalf("%s body = %q, want empty", body, rec.Body.String())
		}
	}
	// A real id still gets a real response.
	if rec := postMCP(t, testGateway(t).Handler(), `{"jsonrpc":"2.0","id":0,"method":"ping"}`); rec.Code != http.StatusOK {
		t.Fatalf("id 0 status = %d, want 200 (zero is a valid id)", rec.Code)
	}
}

// F7. Both /mcp and /mcp/ serve the endpoint: behind a reverse proxy the exact
// path is whatever stripPrefix leaves behind, and a 404 there is a silent outage.
func TestHTTPTrailingSlashPath(t *testing.T) {
	h := testGateway(t).Handler()
	for _, path := range []string{"/mcp", "/mcp/"} {
		req := httptest.NewRequest(http.MethodPost, path, strings.NewReader(`{"jsonrpc":"2.0","id":1,"method":"ping"}`))
		req.Header.Set("Content-Type", "application/json")
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, req)
		if rec.Code != http.StatusOK {
			t.Fatalf("POST %s = %d, want 200; body: %s", path, rec.Code, rec.Body.String())
		}
		if got := strings.TrimSpace(rec.Body.String()); got != `{"jsonrpc":"2.0","id":1,"result":{}}` {
			t.Fatalf("POST %s body = %s", path, got)
		}
	}
	// A wrong method on the trailing-slash path is still the same 405.
	req := httptest.NewRequest(http.MethodGet, "/mcp/", nil)
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("GET /mcp/ = %d, want 405", rec.Code)
	}
}

// S10. The front door is reachable through a public reverse proxy, so a
// connection that opens and then says nothing must time out. There is
// deliberately no WriteTimeout: a forwarded SAP query may take the full
// --call-timeout before there is anything to write.
func TestHTTPServerTimeouts(t *testing.T) {
	srv := testGateway(t).server()
	if srv.ReadHeaderTimeout <= 0 {
		t.Fatalf("ReadHeaderTimeout = %v, want positive", srv.ReadHeaderTimeout)
	}
	if srv.ReadTimeout <= 0 || srv.ReadTimeout < srv.ReadHeaderTimeout {
		t.Fatalf("ReadTimeout = %v, want positive and at least ReadHeaderTimeout", srv.ReadTimeout)
	}
	if srv.IdleTimeout <= 0 {
		t.Fatalf("IdleTimeout = %v, want positive", srv.IdleTimeout)
	}
	if srv.WriteTimeout != 0 {
		t.Fatalf("WriteTimeout = %v, want unset so a slow backend call is not cut off", srv.WriteTimeout)
	}
	if srv.Addr != defaultAddr {
		t.Fatalf("Addr = %q, want %q", srv.Addr, defaultAddr)
	}
}

// N12. A non-positive duration would expire every context before it was used:
// every backend request would fail instantly and every backend would look down.
// Refuse the configuration instead.
func TestConfigValidate(t *testing.T) {
	if err := DefaultConfig().Validate(); err != nil {
		t.Fatalf("DefaultConfig().Validate() = %v, want nil", err)
	}
	cases := []struct {
		name string
		mut  func(*Config)
		want string
	}{
		{"zero ttl", func(c *Config) { c.ToolsTTL = 0 }, "--ttl"},
		{"negative ttl", func(c *Config) { c.ToolsTTL = -time.Second }, "--ttl"},
		{"zero list timeout", func(c *Config) { c.ListTimeout = 0 }, "--list-timeout"},
		{"negative list timeout", func(c *Config) { c.ListTimeout = -1 }, "--list-timeout"},
		{"zero call timeout", func(c *Config) { c.CallTimeout = 0 }, "--call-timeout"},
		{"empty addr", func(c *Config) { c.Addr = "  " }, "--addr"},
		{"backend without url", func(c *Config) { c.Backends[0].URL = "" }, "sapb1"},
	}
	for _, c := range cases {
		cfg := DefaultConfig()
		cfg.Backends = append([]BackendConf(nil), cfg.Backends...) // don't share the slice
		c.mut(&cfg)
		err := cfg.Validate()
		if err == nil {
			t.Fatalf("%s: Validate() = nil, want an error", c.name)
		}
		if !strings.Contains(err.Error(), c.want) {
			t.Fatalf("%s: err = %v, want it to name %s", c.name, err, c.want)
		}
	}
}

// S6. splitURL is what keeps a credential out of every log line and every error:
// the URL that goes on the wire never carries userinfo, and the one that is
// displayed never carries a password.
func TestSplitURL(t *testing.T) {
	cases := []struct {
		raw              string
		request, display string
		user, pass       string
	}{
		{"http://sapb1:7701/mcp", "http://sapb1:7701/mcp", "http://sapb1:7701/mcp", "", ""},
		{
			"http://u:sw0rdf1sh@sapb1:7701/mcp",
			"http://sapb1:7701/mcp", "http://u:***@sapb1:7701/mcp", "u", "sw0rdf1sh",
		},
		{ // username only: nothing to mask, nothing to hide
			"http://u@sapb1:7701/mcp",
			"http://sapb1:7701/mcp", "http://u@sapb1:7701/mcp", "u", "",
		},
		{ // an @ in the path is not userinfo
			"http://sapb1:7701/a@b", "http://sapb1:7701/a@b", "http://sapb1:7701/a@b", "", "",
		},
	}
	for _, c := range cases {
		request, display, user, pass := splitURL(c.raw)
		if request != c.request || display != c.display || user != c.user || pass != c.pass {
			t.Fatalf("splitURL(%q) = (%q, %q, %q, %q), want (%q, %q, %q, %q)",
				c.raw, request, display, user, pass, c.request, c.display, c.user, c.pass)
		}
		if c.pass != "" && strings.Contains(display, c.pass) {
			t.Fatalf("splitURL(%q) display %q still contains the password", c.raw, display)
		}
	}
}

// A URL url.Parse cannot handle must still not display anything secret.
func TestSplitURLUnparseable(t *testing.T) {
	raw := "http://u:pa ss@host:7701/mcp\x7f" // a space and a control byte
	request, display, _, _ := splitURL(raw)
	if request != raw {
		t.Fatalf("request = %q, want the raw URL (it will fail at NewRequest)", request)
	}
	if strings.Contains(display, "pa ss") {
		t.Fatalf("display = %q, want the userinfo masked", display)
	}
	if !strings.Contains(display, "***@host:7701") {
		t.Fatalf("display = %q, want ***@host:7701", display)
	}
}

func TestHTTPHealthz(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	rec := httptest.NewRecorder()
	testGateway(t).Handler().ServeHTTP(rec, req)
	if rec.Code != http.StatusOK || strings.TrimSpace(rec.Body.String()) != "ok" {
		t.Fatalf("healthz = %d %q, want 200 ok", rec.Code, rec.Body.String())
	}
}

// The read-only whitelist: every MCP method outside initialize / ping /
// tools/list / tools/call is -32601, so no client request can make the gateway
// speak anything else to a backend.
func TestHTTPWhitelistRejectsEverythingElse(t *testing.T) {
	methods := []string{
		"resources/list", "resources/read", "resources/subscribe", "resources/templates/list",
		"prompts/list", "prompts/get", "completion/complete", "logging/setLevel",
		"roots/list", "sampling/createMessage", "elicitation/create", "tools/write",
	}
	for _, method := range methods {
		rec := postMCP(t, testGateway(t).Handler(),
			`{"jsonrpc":"2.0","id":1,"method":"`+method+`"}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("%s status = %d, want 200 with a JSON-RPC error", method, rec.Code)
		}
		m := decodeRPC(t, rec)
		if _, ok := m["result"]; ok {
			t.Fatalf("%s returned a result, want -32601: %s", method, rec.Body.String())
		}
		rpcErr, _ := m["error"].(map[string]any)
		if code, _ := rpcErr["code"].(float64); code != -32601 {
			t.Fatalf("%s error.code = %v, want -32601", method, rpcErr["code"])
		}
		if msg, _ := rpcErr["message"].(string); !strings.Contains(msg, method) {
			t.Fatalf("%s error.message = %q, want it to name the method", method, msg)
		}
	}
}

// Stdio parity (postsql): an id-less message is a notification — no response,
// no error, even for a real method.
func TestHandleMessageNotificationIsSilent(t *testing.T) {
	for _, body := range []string{
		`{"jsonrpc":"2.0","method":"tools/list"}`,
		`{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":1}}`,
	} {
		resp, err := testGateway(t).handleMessage(t.Context(), []byte(body))
		if err != nil {
			t.Fatalf("%s: err = %v, want nil", body, err)
		}
		if resp != nil {
			t.Fatalf("%s: resp = %+v, want nil for id-less message", body, resp)
		}
	}
}

// With no backends configured (or all of them down and never listed) the
// gateway still advertises its own tool, and only its own tool.
func TestHTTPToolsListGatewayStatusOnly(t *testing.T) {
	rec := postMCP(t, testGateway(t).Handler(), `{"jsonrpc":"2.0","id":2,"method":"tools/list"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	names := toolNames(t, rec)
	if len(names) != 1 || names[0] != statusToolName {
		t.Fatalf("tool names = %v, want exactly [%s]", names, statusToolName)
	}
}

func TestStatusToolDefIsValidJSON(t *testing.T) {
	var def map[string]any
	if err := json.Unmarshal([]byte(statusToolDefJSON), &def); err != nil {
		t.Fatalf("statusToolDefJSON is not valid JSON: %v", err)
	}
	if def["name"] != statusToolName {
		t.Fatalf("name = %v, want %s", def["name"], statusToolName)
	}
	if _, ok := def["inputSchema"].(map[string]any); !ok {
		t.Fatalf("inputSchema = %v, want an object", def["inputSchema"])
	}
}

func TestHTTPUnknownToolCall(t *testing.T) {
	rec := postMCP(t, testGateway(t, DefaultBackends()...).Handler(),
		`{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"no_such_tool","arguments":{}}}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	text, isErr := toolResultOf(t, rec)
	if !isErr {
		t.Fatalf("isError = false, want true; body: %s", rec.Body.String())
	}
	if !strings.HasPrefix(text, "unknown tool: no_such_tool") {
		t.Fatalf("text = %q, want prefix \"unknown tool: no_such_tool\"", text)
	}
	for _, prefix := range []string{"sap_", "pg_", "ecom_", "oms_", "fct_"} {
		if !strings.Contains(text, prefix) {
			t.Fatalf("text = %q, want it to list prefix %q", text, prefix)
		}
	}
}

func TestConfigFromEnv(t *testing.T) {
	env := map[string]string{
		"JIVO_GW_ADDR":        ":9000",
		"JIVO_GW_TTL":         "90s",
		"JIVO_GW_URL_POSTSQL": "http://127.0.0.1:7702/mcp",
		"JIVO_GW_URL_FACTORY": "http://fct.internal:9/mcp",
	}
	cfg := ConfigFromEnv(func(k string) string { return env[k] })
	if cfg.Addr != ":9000" {
		t.Fatalf("Addr = %q, want :9000", cfg.Addr)
	}
	if cfg.ToolsTTL.String() != "1m30s" {
		t.Fatalf("ToolsTTL = %v, want 90s", cfg.ToolsTTL)
	}
	if cfg.ListTimeout != defaultListTimeout || cfg.CallTimeout != defaultCallTimeout {
		t.Fatalf("timeouts = %v/%v, want compiled defaults", cfg.ListTimeout, cfg.CallTimeout)
	}
	got := map[string]string{}
	for _, b := range cfg.Backends {
		got[b.Name] = b.URL
	}
	if got["postsql"] != "http://127.0.0.1:7702/mcp" || got["factory"] != "http://fct.internal:9/mcp" {
		t.Fatalf("overridden URLs = %v", got)
	}
	if got["sapb1"] != "http://sapb1:7701/mcp" {
		t.Fatalf("sapb1 URL = %q, want the compiled default", got["sapb1"])
	}
}

// Bad env values must not break startup: they fall back to the default.
func TestConfigFromEnvIgnoresJunkTTL(t *testing.T) {
	cfg := ConfigFromEnv(func(k string) string {
		if k == "JIVO_GW_TTL" {
			return "not-a-duration"
		}
		return ""
	})
	if cfg.ToolsTTL != defaultToolsTTL {
		t.Fatalf("ToolsTTL = %v, want default %v", cfg.ToolsTTL, defaultToolsTTL)
	}
}
