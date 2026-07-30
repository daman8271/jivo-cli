package gateway

import (
	"encoding/json"
	"net/http"
	"strings"
	"testing"
	"time"
)

// --- five-backend fleet -------------------------------------------------------
//
// Modelled on production: sapb1 (mcp-go v0.56, stateless) and postsql
// (hand-rolled, stateless) issue no session id; ecom / oms / factory are
// v0.47.0 and do, with oms answering over SSE and factory paginating. sapb1
// names every one of its tools sapb1_*, so it is configured with the matching
// StripPrefix and must be advertised as sap_query, not sap_sapb1_query.

type fleet struct {
	sapb1, postsql, ecom, oms, factory *fakeBackend
	g                                  *Gateway
	h                                  http.Handler
}

func newFleet(t *testing.T, ttl time.Duration) *fleet {
	t.Helper()
	f := &fleet{
		sapb1:   newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"sapb1_doctor", "sapb1_query"}}),
		postsql: newFakeBackend(t, fakeOpts{name: "postsql", tools: []string{"postgres_query", "list_databases"}}),
		ecom:    newFakeBackend(t, fakeOpts{name: "ecom", stateful: true, tools: []string{"orders"}}),
		oms:     newFakeBackend(t, fakeOpts{name: "oms", stateful: true, sse: true, sseNoise: true, tools: []string{"approvals"}}),
		factory: newFakeBackend(t, fakeOpts{name: "factory", stateful: true, pages: [][]string{{"production"}, {"stock"}}}),
	}
	cfg := DefaultConfig()
	cfg.ToolsTTL = ttl
	cfg.ListTimeout = 5 * time.Second
	cfg.CallTimeout = 5 * time.Second
	cfg.Backends = []BackendConf{
		f.sapb1.confStrip("sap_", "sapb1_"),
		f.postsql.conf("pg_"),
		f.ecom.conf("ecom_"),
		f.oms.conf("oms_"),
		f.factory.conf("fct_"),
	}
	f.g = New(cfg, "0.1.0-test")
	f.h = f.g.Handler()
	return f
}

// The merged list is every backend's tools, prefixed, in configured order, with
// gateway_status last.
func TestGatewayToolsListMergesAllBackends(t *testing.T) {
	f := newFleet(t, time.Hour)

	rec := postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	got := toolNames(t, rec)
	want := []string{
		"sap_doctor", "sap_query",
		"pg_postgres_query", "pg_list_databases",
		"ecom_orders",
		"oms_approvals",
		"fct_production", "fct_stock", // both pages
		"gateway_status",
	}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("tools =\n  %v\nwant\n  %v", got, want)
	}

	// Descriptions and annotations survive the rename.
	m := decodeRPC(t, rec)
	result, _ := m["result"].(map[string]any)
	tools, _ := result["tools"].([]any)
	first, _ := tools[0].(map[string]any)
	if desc, _ := first["description"].(string); desc != "sapb1 tool sapb1_doctor" {
		t.Fatalf("description = %q, want the backend's own", desc)
	}
	ann, _ := first["annotations"].(map[string]any)
	if ro, _ := ann["readOnlyHint"].(bool); !ro {
		t.Fatalf("annotations = %v, want readOnlyHint preserved", ann)
	}

	// A second tools/list inside the TTL does not re-list the backends.
	postMCP(t, f.h, `{"jsonrpc":"2.0","id":2,"method":"tools/list"}`)
	if n := len(f.ecom.callsOf("tools/list")); n != 1 {
		t.Fatalf("ecom tools/list requests = %d, want 1 (cached)", n)
	}
}

// Each prefixed call lands on exactly one backend, with the prefix stripped.
func TestGatewayRoutesAndStripsPrefix(t *testing.T) {
	f := newFleet(t, time.Hour)

	cases := []struct {
		tool     string
		backend  *fakeBackend
		upstream string
	}{
		{"sap_query", f.sapb1, "sapb1_query"}, // the backend gets its own name back
		{"pg_postgres_query", f.postsql, "postgres_query"},
		{"ecom_orders", f.ecom, "orders"},
		{"oms_approvals", f.oms, "approvals"},
		{"fct_production", f.factory, "production"},
	}
	for _, c := range cases {
		rec := postMCP(t, f.h, `{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"`+c.tool+`","arguments":{}}}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("%s status = %d; body: %s", c.tool, rec.Code, rec.Body.String())
		}
		text, isErr := toolResultOf(t, rec)
		if isErr {
			t.Fatalf("%s isError = true: %s", c.tool, text)
		}
		if want := c.backend.opts.name + ":" + c.upstream; text != want {
			t.Fatalf("%s text = %q, want %q (prefix stripped, right backend)", c.tool, text, want)
		}
	}
	// And nobody else was called.
	for _, c := range cases {
		if n := len(c.backend.callsOf("tools/call")); n != 1 {
			t.Fatalf("%s got %d tools/call, want exactly 1", c.backend.opts.name, n)
		}
	}
}

// Routing works before any tools/list: it comes from the static prefix table,
// not from the cache.
func TestGatewayCallWorksWithoutAnyRefresh(t *testing.T) {
	f := newFleet(t, time.Hour)
	rec := postMCP(t, f.h, `{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"ecom_orders","arguments":{}}}`)
	text, isErr := toolResultOf(t, rec)
	if isErr || text != "ecom:orders" {
		t.Fatalf("text = %q isError = %v, want ecom:orders", text, isErr)
	}
	if n := len(f.ecom.callsOf("tools/list")); n != 0 {
		t.Fatalf("ecom tools/list requests = %d, want 0 (routing must not need the cache)", n)
	}
}

// The backend's result bytes reach the client unchanged.
func TestGatewayResultPassthroughIsByteIdentical(t *testing.T) {
	payload := `{"content":[{"type":"text","text":"₹1,23,456 até"}],"isError":false,` +
		`"structuredContent":{"rows":[{"a":1,"b":null},{"a":2.5,"b":true}],"n":2},"_meta":{"ms":12}}`
	back := newFakeBackend(t, fakeOpts{name: "sapb1", callResult: payload})

	cfg := DefaultConfig()
	cfg.Backends = []BackendConf{back.conf("sap_")}
	g := New(cfg, "test")

	rec := postMCP(t, g.Handler(), `{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"sap_query","arguments":{"q":1}}}`)
	want := `{"jsonrpc":"2.0","id":11,"result":` + payload + `}`
	if got := rec.Body.String(); got != want {
		t.Fatalf("body =\n  %s\nwant\n  %s", got, want)
	}
}

// encoding/json escapes <, > and & inside forwarded bytes (< etc). That is
// the same JSON value, and it is what postsql's own MCP endpoint does too — this
// test pins the behaviour so nobody is surprised by it.
func TestGatewayResultPassthroughEscapesHTMLButKeepsValue(t *testing.T) {
	payload := `{"content":[{"type":"text","text":"a<b & c>d"}],"isError":false}`
	back := newFakeBackend(t, fakeOpts{name: "sapb1", callResult: payload})
	cfg := DefaultConfig()
	cfg.Backends = []BackendConf{back.conf("sap_")}

	rec := postMCP(t, New(cfg, "test").Handler(),
		`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"sap_query"}}`)
	text, _ := toolResultOf(t, rec)
	if text != "a<b & c>d" {
		t.Fatalf("decoded text = %q, want the original string", text)
	}
}

// A backend JSON-RPC error is forwarded as a JSON-RPC error with code, message
// and data intact — and stitched onto the client's own id.
func TestGatewayForwardsBackendErrorIntact(t *testing.T) {
	back := newFakeBackend(t, fakeOpts{name: "oms", stateful: true, toolError: true})
	cfg := DefaultConfig()
	cfg.Backends = []BackendConf{back.conf("oms_")}

	rec := postMCP(t, New(cfg, "test").Handler(),
		`{"jsonrpc":"2.0","id":"client-77","method":"tools/call","params":{"name":"oms_approvals"}}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	m := decodeRPC(t, rec)
	if m["id"] != "client-77" {
		t.Fatalf("id = %v, want the client's own id echoed", m["id"])
	}
	rpcErr, _ := m["error"].(map[string]any)
	if rpcErr == nil {
		t.Fatalf("no error object in %s", rec.Body.String())
	}
	if code, _ := rpcErr["code"].(float64); code != -32001 {
		t.Fatalf("code = %v, want -32001 unchanged", rpcErr["code"])
	}
	if msg, _ := rpcErr["message"].(string); msg != "backend says no" {
		t.Fatalf("message = %q, want unchanged", msg)
	}
	data, _ := rpcErr["data"].(map[string]any)
	if data["detail"] != "upstream" {
		t.Fatalf("data = %v, want the backend's data", data)
	}
}

// A dead backend degrades to an MCP tool error on HTTP 200 — the gateway itself
// is still healthy.
func TestGatewayDownBackendIsToolError(t *testing.T) {
	f := newFleet(t, 0) // ttl 0: every tools/list re-lists
	f.ecom.srv.Close()

	rec := postMCP(t, f.h, `{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"ecom_orders","arguments":{}}}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200 (a down backend is not a transport failure)", rec.Code)
	}
	text, isErr := toolResultOf(t, rec)
	if !isErr {
		t.Fatalf("isError = false, want true; text: %s", text)
	}
	if !strings.HasPrefix(text, "backend ecom unavailable: ") {
		t.Fatalf("text = %q, want prefix \"backend ecom unavailable: \"", text)
	}

	// The other four still list and still work.
	names := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":6,"method":"tools/list"}`))
	if strings.Join(names, ",") != "sap_doctor,sap_query,pg_postgres_query,pg_list_databases,oms_approvals,fct_production,fct_stock,gateway_status" {
		t.Fatalf("tools with ecom down = %v", names)
	}
	text, isErr = toolResultOf(t, postMCP(t, f.h,
		`{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"sap_query","arguments":{}}}`))
	if isErr || text != "sapb1:sapb1_query" {
		t.Fatalf("sap_query with ecom down = %q isError=%v", text, isErr)
	}
}

// Stale-while-down, end to end: a backend that dies after a good refresh keeps
// its tools advertised, so a client's cached list stays valid.
func TestGatewayStaleWhileDownEndToEnd(t *testing.T) {
	f := newFleet(t, 0)

	before := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`))
	f.oms.srv.Close()
	after := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":2,"method":"tools/list"}`))

	if strings.Join(before, ",") != strings.Join(after, ",") {
		t.Fatalf("tool list churned when oms went down:\n  before %v\n  after  %v", before, after)
	}
}

// gateway_status reports every backend, its prefix, health and tool count.
func TestGatewayStatusTool(t *testing.T) {
	f := newFleet(t, time.Hour)

	text, isErr := toolResultOf(t, postMCP(t, f.h,
		`{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"gateway_status","arguments":{}}}`))
	if isErr {
		t.Fatalf("gateway_status isError = true: %s", text)
	}
	var report struct {
		Gateway struct {
			Name      string `json:"name"`
			Version   string `json:"version"`
			Mode      string `json:"mode"`
			ToolsLive int    `json:"tools_live"`
		} `json:"gateway"`
		BackendsUp string          `json:"backends_up"`
		Backends   []BackendStatus `json:"backends"`
	}
	if err := json.Unmarshal([]byte(text), &report); err != nil {
		t.Fatalf("gateway_status text is not JSON: %v\n%s", err, text)
	}
	if report.Gateway.Name != "jivo-gateway" || report.Gateway.Version != "0.1.0-test" || report.Gateway.Mode != "read-only" {
		t.Fatalf("gateway = %+v", report.Gateway)
	}
	if report.BackendsUp != "5/5" {
		t.Fatalf("backends_up = %q, want 5/5", report.BackendsUp)
	}
	if report.Gateway.ToolsLive != 9 {
		t.Fatalf("tools_live = %d, want 9 (8 backend tools + gateway_status)", report.Gateway.ToolsLive)
	}
	wantCounts := map[string]int{"sapb1": 2, "postsql": 2, "ecom": 1, "oms": 1, "factory": 2}
	wantPrefix := map[string]string{"sapb1": "sap_", "postsql": "pg_", "ecom": "ecom_", "oms": "oms_", "factory": "fct_"}
	if len(report.Backends) != 5 {
		t.Fatalf("backends = %d rows, want 5", len(report.Backends))
	}
	for _, st := range report.Backends {
		if !st.Up {
			t.Fatalf("%s reported down: %+v", st.Name, st)
		}
		if st.ToolCount != wantCounts[st.Name] {
			t.Fatalf("%s tool_count = %d, want %d", st.Name, st.ToolCount, wantCounts[st.Name])
		}
		if st.Prefix != wantPrefix[st.Name] {
			t.Fatalf("%s prefix = %q, want %q", st.Name, st.Prefix, wantPrefix[st.Name])
		}
		if st.LastError != "" {
			t.Fatalf("%s last_error = %q, want empty", st.Name, st.LastError)
		}
	}
}

// F1. No name stutter: sapb1 calls its tools sapb1_*, so the gateway advertises
// sap_query — not sap_sapb1_query — and a call to sap_query reaches the backend
// as its own sapb1_query.
func TestGatewayNoNameStutter(t *testing.T) {
	f := newFleet(t, time.Hour)

	names := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`))
	joined := strings.Join(names, ",")
	if strings.Contains(joined, "sap_sapb1_") {
		t.Fatalf("tools = %v, want no sap_sapb1_ stutter", names)
	}
	for _, want := range []string{"sap_query", "sap_doctor"} {
		if !strings.Contains(joined, want) {
			t.Fatalf("tools = %v, want %s advertised", names, want)
		}
	}

	postMCP(t, f.h, `{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"sap_query","arguments":{}}}`)
	calls := f.sapb1.callsOf("tools/call")
	if len(calls) != 1 {
		t.Fatalf("sapb1 tools/call = %d, want 1", len(calls))
	}
	var p struct {
		Name string `json:"name"`
	}
	if err := json.Unmarshal(calls[0].params, &p); err != nil {
		t.Fatal(err)
	}
	if p.Name != "sapb1_query" {
		t.Fatalf("backend received tool name %q, want its own sapb1_query", p.Name)
	}
}

// F3. gateway_status is a live health check, not an echo of a cache that can be
// a whole TTL old: it re-lists the backends first. Here the TTL is an hour, so a
// cached answer would still call the dead backend up.
func TestGatewayStatusIsFresherThanTheTTL(t *testing.T) {
	f := newFleet(t, time.Hour)

	// Warm the cache with everything healthy.
	if names := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`)); len(names) != 9 {
		t.Fatalf("tools = %v, want 9", names)
	}
	f.ecom.srv.Close()

	text, isErr := toolResultOf(t, postMCP(t, f.h,
		`{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"gateway_status","arguments":{}}}`))
	if isErr {
		t.Fatalf("gateway_status isError = true: %s", text)
	}
	var report struct {
		BackendsUp string          `json:"backends_up"`
		Backends   []BackendStatus `json:"backends"`
	}
	if err := json.Unmarshal([]byte(text), &report); err != nil {
		t.Fatalf("not JSON: %v\n%s", err, text)
	}
	if report.BackendsUp != "4/5" {
		t.Fatalf("backends_up = %q, want 4/5 (the dead backend must be noticed now)", report.BackendsUp)
	}
	for _, st := range report.Backends {
		if st.Name != "ecom" {
			continue
		}
		if st.Up || st.LastError == "" {
			t.Fatalf("ecom = %+v, want down with an error", st)
		}
		// Stale-while-down still holds: its tools stay advertised.
		if st.ToolCount != 1 {
			t.Fatalf("ecom tool_count = %d, want its 1 stale tool kept", st.ToolCount)
		}
	}
	// tools/list is unchanged — a status check must not churn the client's list.
	if names := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":3,"method":"tools/list"}`)); len(names) != 9 {
		t.Fatalf("tools after status = %v, want the same 9", names)
	}
}

// S6. A password in a backend URL must never be printed: not in gateway_status's
// url field, not in an error. The host:port stays visible on purpose (see the
// README's "Known behaviours") — the credential does not.
func TestGatewayStatusRedactsCredentials(t *testing.T) {
	const secret = "s3cr3t-do-not-print"
	back := newFakeBackend(t, fakeOpts{name: "sapb1", tools: []string{"sapb1_query"}})
	dead := newFakeBackend(t, fakeOpts{name: "postsql"})
	deadURL := withCredentials(dead.url(), "pguser", secret)
	dead.srv.Close() // so its status carries a transport error too

	env := map[string]string{
		"JIVO_GW_URL_SAPB1":   withCredentials(back.url(), "sapuser", secret),
		"JIVO_GW_URL_POSTSQL": deadURL,
	}
	cfg := ConfigFromEnv(func(k string) string { return env[k] })
	cfg.ToolsTTL = 0
	cfg.ListTimeout = 2 * time.Second
	cfg.Backends = cfg.Backends[:2] // sapb1 + postsql only

	text, isErr := toolResultOf(t, postMCP(t, New(cfg, "test").Handler(),
		`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"gateway_status","arguments":{}}}`))
	if isErr {
		t.Fatalf("gateway_status isError = true: %s", text)
	}
	if strings.Contains(text, secret) {
		t.Fatalf("gateway_status leaked the password:\n%s", text)
	}
	var report struct {
		Backends []BackendStatus `json:"backends"`
	}
	if err := json.Unmarshal([]byte(text), &report); err != nil {
		t.Fatalf("not JSON: %v\n%s", err, text)
	}
	for _, st := range report.Backends {
		if !strings.Contains(st.URL, ":***@") {
			t.Fatalf("%s url = %q, want the password masked as ***", st.Name, st.URL)
		}
		if !strings.Contains(st.URL, "127.0.0.1:") {
			t.Fatalf("%s url = %q, want the host:port kept for diagnosis", st.Name, st.URL)
		}
	}
	// The credential survives as auth, so the reachable backend still works.
	if report.Backends[0].ToolCount != 1 || !report.Backends[0].Up {
		t.Fatalf("sapb1 = %+v, want up with its 1 tool", report.Backends[0])
	}
	// And the dead backend's error text — which quotes the URL — is clean too.
	if report.Backends[1].LastError == "" {
		t.Fatalf("postsql = %+v, want a transport error", report.Backends[1])
	}

	// Same for a forwarded tools/call against the dead, credentialled backend.
	callText, isErr := toolResultOf(t, postMCP(t, New(cfg, "test").Handler(),
		`{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"pg_postgres_query","arguments":{}}}`))
	if !isErr {
		t.Fatalf("call against a dead backend isError = false: %s", callText)
	}
	if strings.Contains(callText, secret) {
		t.Fatalf("tool error leaked the password: %s", callText)
	}
}

// withCredentials injects userinfo into a URL, the way a misconfigured
// JIVO_GW_URL_* would.
func withCredentials(raw, user, pass string) string {
	return strings.Replace(raw, "http://", "http://"+user+":"+pass+"@", 1)
}

// With everything down, gateway_status says so — five rows, all down, each with
// an error. This is the shape of the local smoke test.
func TestGatewayStatusAllBackendsDown(t *testing.T) {
	f := newFleet(t, 0)
	for _, b := range []*fakeBackend{f.sapb1, f.postsql, f.ecom, f.oms, f.factory} {
		b.srv.Close()
	}

	text, isErr := toolResultOf(t, postMCP(t, f.h,
		`{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"gateway_status","arguments":{}}}`))
	if isErr {
		t.Fatalf("gateway_status isError = true: %s", text)
	}
	var report struct {
		BackendsUp string          `json:"backends_up"`
		Backends   []BackendStatus `json:"backends"`
	}
	if err := json.Unmarshal([]byte(text), &report); err != nil {
		t.Fatalf("not JSON: %v\n%s", err, text)
	}
	if report.BackendsUp != "0/5" {
		t.Fatalf("backends_up = %q, want 0/5", report.BackendsUp)
	}
	for _, st := range report.Backends {
		if st.Up || st.LastError == "" {
			t.Fatalf("%s = %+v, want down with an error", st.Name, st)
		}
	}
	// The gateway still lists its own tool.
	if names := toolNames(t, postMCP(t, f.h, `{"jsonrpc":"2.0","id":10,"method":"tools/list"}`)); len(names) != 1 || names[0] != statusToolName {
		t.Fatalf("tools with everything down = %v, want just gateway_status", names)
	}
}

// Unknown or unprefixed tool names never reach a backend.
func TestGatewayUnknownToolNeverForwards(t *testing.T) {
	f := newFleet(t, time.Hour)
	for _, name := range []string{"no_such_tool", "query", "sap", "SAP_query", "gateway_statuses"} {
		rec := postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"`+name+`"}}`)
		text, isErr := toolResultOf(t, rec)
		if !isErr || !strings.HasPrefix(text, "unknown tool: ") {
			t.Fatalf("%q -> %q (isError=%v), want an unknown-tool error", name, text, isErr)
		}
	}
	for _, b := range []*fakeBackend{f.sapb1, f.postsql, f.ecom, f.oms, f.factory} {
		if n := len(b.callsOf("tools/call")); n != 0 {
			t.Fatalf("%s received %d tools/call, want 0", b.opts.name, n)
		}
	}
}

// Malformed tools/call params are a tool error, not a crash.
func TestGatewayBadToolCallParams(t *testing.T) {
	f := newFleet(t, time.Hour)
	rec := postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":"not-an-object"}`)
	text, isErr := toolResultOf(t, rec)
	if !isErr || !strings.HasPrefix(text, "invalid tool-call params: ") {
		t.Fatalf("text = %q isError = %v, want an invalid-params tool error", text, isErr)
	}
}

// Warmup lists everything once, up front, and reports per-backend health.
func TestGatewayWarmup(t *testing.T) {
	f := newFleet(t, time.Hour)
	f.factory.srv.Close()

	st := f.g.Warmup(t.Context())
	if len(st) != 5 {
		t.Fatalf("Warmup = %d rows, want 5", len(st))
	}
	byName := map[string]BackendStatus{}
	for _, s := range st {
		byName[s.Name] = s
	}
	if !byName["sapb1"].Up || byName["sapb1"].ToolCount != 2 {
		t.Fatalf("sapb1 = %+v, want up with 2 tools", byName["sapb1"])
	}
	if byName["factory"].Up || byName["factory"].LastError == "" {
		t.Fatalf("factory = %+v, want down with an error", byName["factory"])
	}
	// Warmed: a following tools/list serves the cache.
	postMCP(t, f.h, `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`)
	if n := len(f.ecom.callsOf("tools/list")); n != 1 {
		t.Fatalf("ecom tools/list requests = %d, want 1 (warmup only)", n)
	}
}

// The read-only whitelist must survive the failure paths, not just the happy
// one. Every backend here is broken in a different way — expiring sessions,
// a session header that never arrives, a permanent 400, looping pagination — so
// the re-init and retry code runs hard, and it still may not put anything
// downstream except the four allowed methods.
func TestGatewayWhitelistHoldsThroughRetryPaths(t *testing.T) {
	backs := []*fakeBackend{
		newFakeBackend(t, fakeOpts{name: "expire", stateful: true, alwaysExpire: true, tools: []string{"a"}}),
		newFakeBackend(t, fakeOpts{name: "nohdr", stateful: true, noSessionHeader: true, tools: []string{"b"}}),
		newFakeBackend(t, fakeOpts{name: "bad400", stateful: true, badRequest: true, tools: []string{"c"}}),
		newFakeBackend(t, fakeOpts{name: "loop", repeatCursor: true, tools: []string{"d"}}),
		newFakeBackend(t, fakeOpts{name: "decoy", decoyID: true, tools: []string{"e"}}),
	}
	prefixes := []string{"x1_", "x2_", "x3_", "x4_", "x5_"}

	cfg := DefaultConfig()
	cfg.ToolsTTL = 0 // every request re-lists, so the failure paths run repeatedly
	cfg.ListTimeout = 2 * time.Second
	cfg.CallTimeout = 2 * time.Second
	cfg.Backends = nil
	for i, b := range backs {
		cfg.Backends = append(cfg.Backends, b.confStrip(prefixes[i], "sapb1_"))
	}
	h := New(cfg, "test").Handler()

	for round := 0; round < 2; round++ {
		postMCP(t, h, `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}`)
		postMCP(t, h, `{"jsonrpc":"2.0","id":2,"method":"tools/list"}`)
		postMCP(t, h, `{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"gateway_status"}}`)
		for _, p := range prefixes {
			postMCP(t, h, `{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"`+p+`anything","arguments":{"k":1}}}`)
		}
	}

	allowed := map[string]bool{
		"initialize": true, "notifications/initialized": true,
		"tools/list": true, "tools/call": true,
	}
	for _, b := range backs {
		_, _, calls := b.stats()
		if len(calls) == 0 {
			t.Fatalf("%s received nothing, so this proves nothing", b.opts.name)
		}
		for _, c := range calls {
			if !allowed[c.method] {
				t.Fatalf("%s received %q through a failure path, outside the read-only whitelist",
					b.opts.name, c.method)
			}
		}
	}
}

// The gateway sends exactly four methods downstream — the read-only whitelist,
// observed from the backend's side after exercising the whole surface.
func TestGatewayOnlyEmitsWhitelistedMethods(t *testing.T) {
	f := newFleet(t, 0)

	bodies := []string{
		`{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}`,
		`{"jsonrpc":"2.0","method":"notifications/initialized"}`,
		`{"jsonrpc":"2.0","id":2,"method":"ping"}`,
		`{"jsonrpc":"2.0","id":3,"method":"tools/list"}`,
		`{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"ecom_orders","arguments":{}}}`,
		`{"jsonrpc":"2.0","id":5,"method":"resources/list"}`,
		`{"jsonrpc":"2.0","id":6,"method":"prompts/get","params":{"name":"x"}}`,
		`{"jsonrpc":"2.0","id":7,"method":"completion/complete"}`,
		`{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"name":"ecom_orders_delete","arguments":{}}}`,
	}
	for _, b := range bodies {
		postMCP(t, f.h, b)
	}

	allowed := map[string]bool{
		"initialize": true, "notifications/initialized": true,
		"tools/list": true, "tools/call": true,
	}
	for _, b := range []*fakeBackend{f.sapb1, f.postsql, f.ecom, f.oms, f.factory} {
		_, _, calls := b.stats()
		for _, c := range calls {
			if !allowed[c.method] {
				t.Fatalf("%s received %q, outside the read-only whitelist", b.opts.name, c.method)
			}
		}
	}
	// ping is answered natively: it must not have reached anyone.
	for _, b := range []*fakeBackend{f.sapb1, f.postsql, f.ecom, f.oms, f.factory} {
		if n := len(b.callsOf("ping")); n != 0 {
			t.Fatalf("%s received ping %d times, want 0", b.opts.name, n)
		}
	}
}
