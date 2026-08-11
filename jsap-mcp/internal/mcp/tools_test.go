// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — tool-surface tests.

package mcp

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	"jsap-mcp/internal/jsap"

	mcplib "github.com/mark3labs/mcp-go/mcp"
)

// wantTools is the exact advertised surface. Pinned deliberately: the cost of a
// new tool is paid by every agent routing against the gateway's 84 existing
// tools, so adding one is a decision, not an accident.
var wantTools = []string{
	"jsap_admin",
	"jsap_budget_approvals",
	"jsap_context",
	"jsap_dochub",
	"jsap_execute",
	"jsap_hierarchy",
	"jsap_inventory_audit",
	"jsap_search",
	"jsap_tasks",
	"jsap_tickets",
}

// mutatingToolWord catches a write tool sneaking in under an obvious name.
// Necessary but not sufficient — TestNoToolCanReachAWrite is the real guard.
var mutatingToolWord = []string{
	"create", "insert", "update", "delete", "remove", "save", "assign", "upload",
	"post", "put", "patch", "write", "submit", "approve", "reject", "cancel", "close", "set_",
}

func TestRegisteredToolsArePinnedAndReadOnly(t *testing.T) {
	s := newTestServer(t, "http://jsap.invalid")
	tools := s.MCPServer().ListTools()

	if len(tools) != len(wantTools) {
		t.Errorf("registered %d tools, want %d: %v", len(tools), len(wantTools), toolNames(t, s))
	}
	for _, name := range wantTools {
		st, ok := tools[name]
		if !ok {
			t.Errorf("tool %q is not registered", name)
			continue
		}
		if st.Tool.Annotations.ReadOnlyHint == nil || !*st.Tool.Annotations.ReadOnlyHint {
			t.Errorf("tool %q is not annotated read-only", name)
		}
		if st.Tool.Annotations.DestructiveHint != nil && *st.Tool.Annotations.DestructiveHint {
			t.Errorf("tool %q is annotated destructive", name)
		}
	}
	for name := range tools {
		if !strings.HasPrefix(name, "jsap_") {
			t.Errorf("tool %q does not carry the jsap_ prefix — the gateway strips and re-adds exactly that string", name)
		}
		lower := strings.ToLower(name)
		for _, word := range mutatingToolWord {
			if strings.Contains(lower, word) {
				t.Errorf("tool %q names a mutating action — the MCP surface is read-only forever", name)
			}
		}
	}
}

// TestNoToolCanReachAWrite is the structural half: every curated action, and
// every id jsap_execute will accept, resolves to a command in the compiled-in
// catalogue — which TestCatalogueIsReadShaped has already proved is read-only.
// There is no third path: run() looks the id up or refuses.
func TestNoToolCanReachAWrite(t *testing.T) {
	for _, tool := range curatedTools {
		for _, pair := range tool.Actions {
			cmd, ok := jsap.Lookup(pair[1])
			if !ok {
				t.Errorf("%s action %q maps to %q, which is not in the catalogue", tool.Name, pair[0], pair[1])
				continue
			}
			if cmd.Method != http.MethodGet && cmd.Method != http.MethodPost {
				t.Errorf("%s action %q maps to a %s command", tool.Name, pair[0], cmd.Method)
			}
		}
	}

	s := newTestServer(t, "http://jsap.invalid")
	res := s.run(context.Background(), "documents.po", nil, 1)
	if !isError(t, res) {
		t.Error("an excluded SAP-mirror command was accepted by run()")
	}
	res = s.run(context.Background(), "/api/DocumentDispatch/GetLastBundleId?mode=update", nil, 1)
	if !isError(t, res) {
		t.Error("run() accepted a URL path as a command id — dispatch must be by catalogued id only")
	}
}

// TestCuratedSchemasAreDerivedAndConsistent: a curated tool's inputs come from
// the catalogue, so they cannot drift from what the command accepts; and one
// name may not mean two types inside one tool, which would make the advertised
// schema ambiguous.
func TestCuratedSchemasAreDerivedAndConsistent(t *testing.T) {
	for _, tool := range curatedTools {
		types := map[string]jsap.ParamType{}
		for _, pair := range tool.Actions {
			cmd, ok := jsap.Lookup(pair[1])
			if !ok {
				continue
			}
			for _, p := range cmd.Params {
				if seen, ok := types[p.Name]; ok && seen != p.Type {
					t.Errorf("%s: parameter %q is %s under one action and %s under another", tool.Name, p.Name, seen, p.Type)
				}
				types[p.Name] = p.Type
			}
		}

		schema := buildCuratedTool(tool).InputSchema
		if _, ok := schema.Properties["action"]; !ok {
			t.Errorf("%s: no action property", tool.Name)
		}
		for name := range types {
			if _, ok := schema.Properties[name]; !ok {
				t.Errorf("%s: catalogue parameter %q is missing from the advertised schema", tool.Name, name)
			}
		}
		for name := range schema.Properties {
			if name == "action" || name == "company" {
				continue
			}
			if _, ok := types[name]; !ok {
				t.Errorf("%s: advertises parameter %q that no catalogued command declares", tool.Name, name)
			}
		}
	}
}

func TestToolsListOverJSONRPCIsReadOnly(t *testing.T) {
	s := newTestServer(t, "http://jsap.invalid")
	ctx := context.Background()

	initReq := `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}`
	if resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(initReq)); resp == nil {
		t.Fatal("initialize returned no response")
	}
	resp := s.MCPServer().HandleMessage(ctx, json.RawMessage(`{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}`))
	encoded, err := json.Marshal(resp)
	if err != nil {
		t.Fatalf("marshal tools/list response: %v", err)
	}
	var listed struct {
		Result struct {
			Tools []struct {
				Name        string `json:"name"`
				Annotations struct {
					ReadOnlyHint *bool `json:"readOnlyHint"`
				} `json:"annotations"`
			} `json:"tools"`
		} `json:"result"`
	}
	if err := json.Unmarshal(encoded, &listed); err != nil {
		t.Fatalf("decode tools/list: %v\n%s", err, encoded)
	}
	if len(listed.Result.Tools) != len(wantTools) {
		t.Fatalf("tools/list returned %d tools, want %d", len(listed.Result.Tools), len(wantTools))
	}
	for _, tool := range listed.Result.Tools {
		if tool.Annotations.ReadOnlyHint == nil || !*tool.Annotations.ReadOnlyHint {
			t.Errorf("tools/list advertises %q without readOnlyHint", tool.Name)
		}
	}
}

// TestWholeToolSurfaceIssuesOnlyReads drives every action of every curated tool
// plus jsap_execute against a fake JSAP, then inspects the wire. Annotations are
// a claim; this is the observation.
func TestWholeToolSurfaceIssuesOnlyReads(t *testing.T) {
	fake := newFakeJSAP(t)
	s := newTestServer(t, fake.srv.URL)
	ctx := context.Background()

	for _, tool := range curatedTools {
		for _, pair := range tool.Actions {
			cmd, ok := jsap.Lookup(pair[1])
			if !ok {
				continue
			}
			args := map[string]any{"action": pair[0]}
			for name, value := range syntheticArgs(cmd) {
				args[name] = value
			}
			res := s.handleCuratedForTest(ctx, tool, args)
			if isError(t, res) {
				t.Errorf("%s action %q returned an error: %s", tool.Name, pair[0], resultText(t, res))
			}
		}
	}

	for _, req := range fake.requests() {
		switch {
		case req.path == "/api/auth/Login", req.path == "/websession/set", req.path == "/websession/updateSelectedCompany":
		case req.method == http.MethodGet:
		case req.method == http.MethodPost:
			leaf := strings.ToLower(req.path[strings.LastIndexByte(req.path, '/')+1:])
			if !strings.HasPrefix(leaf, "get") && !strings.HasPrefix(leaf, "all") {
				t.Errorf("POST %s reached JSAP with a non-read leaf", req.path)
			}
		default:
			t.Errorf("%s %s reached JSAP from the tool surface", req.method, req.path)
		}
		if strings.Contains(req.query, "mode=") {
			t.Errorf("a tool call carried mode=%q", req.query)
		}
	}
}

func TestCuratedToolRejectsUndeclaredParameter(t *testing.T) {
	fake := newFakeJSAP(t)
	s := newTestServer(t, fake.srv.URL)

	res := s.handleCuratedForTest(context.Background(), curatedByName(t, "jsap_hierarchy"), map[string]any{
		"action": "flat",
		"mode":   "update",
	})
	if !isError(t, res) {
		t.Fatal("a caller-supplied mode parameter was accepted")
	}
	if text := resultText(t, res); !strings.Contains(text, "unknown parameter") {
		t.Fatalf("error = %q, want an unknown-parameter refusal", text)
	}
}

func TestSalaryFieldsAreRedacted(t *testing.T) {
	fake := newFakeJSAP(t)
	s := newTestServer(t, fake.srv.URL)

	res := s.handleCuratedForTest(context.Background(), curatedByName(t, "jsap_hierarchy"), map[string]any{"action": "flat"})
	if isError(t, res) {
		t.Fatalf("hierarchy flat failed: %s", resultText(t, res))
	}
	text := resultText(t, res)
	var envelope struct {
		RedactedFields []string        `json:"redacted_fields"`
		Data           json.RawMessage `json:"data"`
	}
	if err := json.Unmarshal([]byte(text), &envelope); err != nil {
		t.Fatalf("result is not JSON: %v\n%s", err, text)
	}
	// The DATA must be clean; the envelope names what was removed, so the answer
	// reads as "this field was withheld" rather than "this employee has no pay".
	for _, forbidden := range []string{"hodSalary", "subHodSalary", "execSalary", "125000"} {
		if strings.Contains(string(envelope.Data), forbidden) {
			t.Errorf("data still carries %q:\n%s", forbidden, envelope.Data)
		}
	}
	if len(envelope.RedactedFields) != 3 {
		t.Errorf("redacted_fields = %v, want the three salary keys — silent redaction under-reports a record", envelope.RedactedFields)
	}
	// A ledger account NAMED "SALARY & WAGES" is a value, not a key, and must survive.
	if !strings.Contains(text, "SALARY AND WAGES") {
		t.Errorf("redaction removed a value, not just keys:\n%s", text)
	}
	if !strings.Contains(text, "MANDEEP") {
		t.Errorf("redaction removed the surrounding record:\n%s", text)
	}
}

func TestResultEchoesCompanyNameNotJustID(t *testing.T) {
	fake := newFakeJSAP(t)
	s := newTestServer(t, fake.srv.URL)

	res := s.handleCuratedForTest(context.Background(), curatedByName(t, "jsap_admin"), map[string]any{
		"action":  "roles",
		"company": float64(2),
	})
	if isError(t, res) {
		t.Fatalf("admin roles failed: %s", resultText(t, res))
	}
	if text := resultText(t, res); !strings.Contains(text, "JIVO BEVERAGE") {
		t.Errorf("result does not name the company; a bare id cross-attributes between systems:\n%s", text)
	}
}

func TestUnknownCompanyIsRefusedNotDefaulted(t *testing.T) {
	if _, err := companyFrom(map[string]any{"company": float64(3)}); err == nil {
		t.Error("company id 3 was accepted — JSAP has exactly two companies")
	}
	got, err := companyFrom(map[string]any{})
	if err != nil || got != defaultCompany {
		t.Errorf("companyFrom(nothing) = %d, %v; want %d, nil", got, err, defaultCompany)
	}
	got, err = companyFrom(map[string]any{"company": "JIVO BEVERAGE"})
	if err != nil || got != 2 {
		t.Errorf("companyFrom(name) = %d, %v; want 2, nil", got, err)
	}
}

func TestSearchAndContextNeedNoNetwork(t *testing.T) {
	s := newTestServer(t, "http://jsap.invalid")
	ctx := context.Background()

	res, err := s.handleSearch(ctx, callRequest(map[string]any{"query": "meeting minutes MoM"}))
	if err != nil || isError(t, res) {
		t.Fatalf("search failed: %v %s", err, resultText(t, res))
	}
	if !strings.Contains(resultText(t, res), "dashboards.mom") {
		t.Errorf("search did not surface dashboards.mom:\n%s", resultText(t, res))
	}

	res, err = s.handleContext(ctx, callRequest(nil))
	if err != nil || isError(t, res) {
		t.Fatalf("context failed: %v %s", err, resultText(t, res))
	}
	text := resultText(t, res)
	for _, want := range []string{"JIVO BEVERAGE", "not a view of SAP", "read", "excluded"} {
		if !strings.Contains(strings.ToLower(text), strings.ToLower(want)) {
			t.Errorf("context is missing %q:\n%s", want, text)
		}
	}
}

func TestBoundPayloadTruncatesAndSaysSo(t *testing.T) {
	rows := make([]map[string]string, 0, 400)
	for n := 0; n < 400; n++ {
		rows = append(rows, map[string]string{"name": strings.Repeat("x", 600)})
	}
	encoded, err := json.Marshal(rows)
	if err != nil {
		t.Fatalf("marshal fixture: %v", err)
	}
	bounded, info := boundPayload(encoded)
	if !info.truncated {
		t.Fatal("an oversized payload was not marked truncated")
	}
	if len(bounded) > mcpToolResultMaxBytes {
		t.Fatalf("bounded payload = %d bytes, want <= %d", len(bounded), mcpToolResultMaxBytes)
	}
	if info.totalCount != 400 || info.returnedCount == 0 || info.returnedCount >= info.totalCount {
		t.Fatalf("bound info = %+v, want a partial count out of 400", info)
	}
	if !json.Valid(bounded) {
		t.Fatal("bounded payload is not valid JSON")
	}
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

func newTestServer(t *testing.T, baseURL string) *Server {
	t.Helper()
	return New(jsap.Config{BaseURL: baseURL, Username: "tester", Password: "unused-in-tests", UserID: 68}, "test")
}

func curatedByName(t *testing.T, name string) curated {
	t.Helper()
	for _, tool := range curatedTools {
		if tool.Name == name {
			return tool
		}
	}
	t.Fatalf("no curated tool named %q", name)
	return curated{}
}

func toolNames(t *testing.T, s *Server) []string {
	t.Helper()
	var out []string
	for name := range s.MCPServer().ListTools() {
		out = append(out, name)
	}
	return out
}

func syntheticArgs(cmd jsap.Command) map[string]any {
	args := map[string]any{}
	for _, p := range cmd.Params {
		if !p.Required || p.FromUser || p.Default != nil {
			continue
		}
		switch p.Type {
		case jsap.TypeInt:
			args[p.Name] = float64(1)
		case jsap.TypeBool:
			args[p.Name] = true
		default:
			args[p.Name] = "TEST"
		}
	}
	return args
}

type fakeJSAP struct {
	srv *httptest.Server

	mu  sync.Mutex
	log []recordedRequest
}

type recordedRequest struct {
	method string
	path   string
	query  string
}

func newFakeJSAP(t *testing.T) *fakeJSAP {
	t.Helper()
	f := &fakeJSAP{}
	f.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		f.mu.Lock()
		f.log = append(f.log, recordedRequest{method: r.Method, path: r.URL.Path, query: r.URL.RawQuery})
		f.mu.Unlock()

		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/api/auth/Login":
			_, _ = w.Write([]byte(`{"success":true,"user":{"userId":68,"userName":"tester"}}`))
		case "/api/Hierarchy/GetMasterFlatAdmin":
			// Shaped like the real payload: names and codes alongside pay.
			_, _ = w.Write([]byte(`{"success":true,"data":[{"hodName":"MANDEEP","hodSalary":125000,` +
				`"subHodSalary":80000,"execSalary":45000,"department":"ACCOUNTS","ledger":"SALARY AND WAGES"}]}`))
		case "/UserManagement/AllUsers":
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(`<tr class="user-row"><td><input data-userid="7"></td>` +
				`<td class="user-name">Test User</td><td class="user-empid">E7</td><td>Employee</td>` +
				`<td>ACCOUNTS</td><td><div class="slider round green"></div></td></tr>`))
		default:
			_, _ = w.Write([]byte(`{"success":true,"data":[]}`))
		}
	}))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeJSAP) requests() []recordedRequest {
	f.mu.Lock()
	defer f.mu.Unlock()
	out := make([]recordedRequest, len(f.log))
	copy(out, f.log)
	return out
}

// callRequest builds a tool-call request the way a host would.
func callRequest(args map[string]any) mcplib.CallToolRequest {
	req := mcplib.CallToolRequest{}
	if args == nil {
		args = map[string]any{}
	}
	req.Params.Arguments = args
	return req
}

// handleCuratedForTest drives one curated tool's handler directly.
func (s *Server) handleCuratedForTest(ctx context.Context, tool curated, args map[string]any) *mcplib.CallToolResult {
	res, err := s.handleCurated(tool)(ctx, callRequest(args))
	if err != nil {
		return mcplib.NewToolResultError(err.Error())
	}
	return res
}

func isError(t *testing.T, res *mcplib.CallToolResult) bool {
	t.Helper()
	if res == nil {
		t.Fatal("nil tool result")
	}
	return res.IsError
}

func resultText(t *testing.T, res *mcplib.CallToolResult) string {
	t.Helper()
	if res == nil {
		t.Fatal("nil tool result")
	}
	var parts []string
	for _, content := range res.Content {
		if text, ok := content.(mcplib.TextContent); ok {
			parts = append(parts, text.Text)
		}
	}
	return strings.Join(parts, "\n")
}
