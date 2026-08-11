// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — the read-only guard tests for the client + catalogue.
//
// Three independent layers, because a read-only guarantee asserted in one place
// is a promise, not a property:
//  1. the catalogue is read-shaped (declaration level);
//  2. the client refuses anything else (runtime level);
//  3. driving the WHOLE catalogue against a fake JSAP puts only GETs, guarded
//     POST-reads and the three bootstrap requests on the wire (wire level).

package jsap

import (
	"context"
	"encoding/json"
	"go/ast"
	"go/parser"
	"go/token"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

// mutatingLeafPrefixes are the action-name prefixes JSAP uses for its write
// endpoints. The test applies them to the LEAF action, not the whole path: a
// substring match would flag GetApprovedBudgetWithDetails and GetAssignedTickets,
// which are reads whose SUBJECT happens to be an approval or an assignment. What
// matters is the verb the action starts with.
var mutatingLeafPrefixes = []string{
	"insert", "create", "update", "delete", "remove", "save", "assign", "upload",
	"approve", "reject", "submit", "unlock", "import", "cancel", "revoke", "reset",
	"add", "set", "edit", "post", "put", "send", "sync", "process", "generate",
}

// nounLeaves are the catalogued read endpoints whose action is a noun rather
// than a read verb (ASP.NET route names like /api/Dashboard/stats). Each was
// read out of the JSAP CLI's module for that page, where it feeds a table or a
// stat card. Anything not on this list must start with a read verb, so a new
// entry cannot slip in under a name nobody classified.
var nounLeaves = map[string]bool{
	"stats":               true, // /api/Dashboard/stats — task KPI row
	"status-distribution": true, // task status counts
	"employee-stats":      true, // per-assignee task totals
	"trend":               true, // daily created/completed series
	"projects":            true, // project-name list
	"employees":           true, // employee list
	"details":             true, // one dashboard task
	"fileaccessinfo":      true, // Document Hub file metadata + access flags
	"versionhistory":      true, // Document Hub stored versions
	"activitylog":         true, // Document Hub per-file audit trail
}

// redirectingParams are parameter names that would hand a caller control of
// WHERE the request goes or WHAT it does, rather than which rows come back.
// `mode` is the specific one that matters: GetLastBundleId?mode=update mutates.
var redirectingParams = map[string]bool{
	"mode": true, "path": true, "url": true, "endpoint": true, "method": true, "action": true,
}

// forbiddenPathFragments are the specific surfaces that must never appear in
// the catalogue, each for a stated reason.
var forbiddenPathFragments = map[string]string{
	"/api/DocumentDispatch":           "SAP-mirror + HTTP-500 dispatch surface; GetLastBundleId has a mutating mode=update variant",
	"GetLastBundleId":                 "its mode=update variant mutates a server-side counter",
	"/api/BPmaster":                   "SAP business-partner master, mirrored worse than sap_/hana_",
	"GetSalarySessionData":            "HR compensation on a publicly-routed gateway",
	"GetEmployeesForSalaryPermission": "HR compensation on a publicly-routed gateway",
	"/DocumentHub/Download":           "read with a side effect: appends a server-side activity-log row",
	"/DocumentHub/Preview":            "streams raw bytes; not a tool result",
}

// forbiddenGroups are the CLI groups excluded wholesale.
var forbiddenGroups = map[string]string{
	"documents": "SAP mirrors + a dead dispatch half + the mutating bundle counter",
	"bpmaster":  "SAP master data, mirrored",
	"bills":     "another organisation's books (Baru Sahib / Akal institutional supply)",
}

func TestCatalogueIsReadShaped(t *testing.T) {
	seen := map[string]bool{}
	for _, cmd := range Commands() {
		if seen[cmd.ID] {
			t.Errorf("duplicate command id %q", cmd.ID)
		}
		seen[cmd.ID] = true

		switch cmd.Method {
		case verbGet:
		case verbPost:
			if !hasReadLeaf(cmd.Path) {
				t.Errorf("%s: POST %s — leaf action is not a read verb, so it may mutate", cmd.ID, cmd.Path)
			}
		default:
			t.Errorf("%s: method %q — only GET and guarded POST-reads exist", cmd.ID, cmd.Method)
		}

		if !strings.HasPrefix(cmd.Path, "/") {
			t.Errorf("%s: path %q is not absolute", cmd.ID, cmd.Path)
		}
		leaf := leafAction(cmd.Path)
		for _, verb := range mutatingLeafPrefixes {
			if strings.HasPrefix(leaf, verb) {
				t.Errorf("%s: path %q has the mutating leaf action %q — the MCP surface is read-only forever", cmd.ID, cmd.Path, leaf)
			}
		}
		if !startsWithReadVerb(leaf) && !nounLeaves[leaf] {
			t.Errorf("%s: leaf action %q is neither a read verb nor a classified noun endpoint — classify it before exposing it", cmd.ID, leaf)
		}
		for fragment, why := range forbiddenPathFragments {
			if strings.Contains(cmd.Path, fragment) {
				t.Errorf("%s: path %q contains %q, which is excluded (%s)", cmd.ID, cmd.Path, fragment, why)
			}
		}
		if why, bad := forbiddenGroups[cmd.Group]; bad {
			t.Errorf("%s: group %q is excluded (%s)", cmd.ID, cmd.Group, why)
		}

		for _, p := range cmd.Params {
			if redirectingParams[strings.ToLower(p.Name)] {
				t.Errorf("%s: declares a caller-supplied %q parameter — that is exactly how GetLastBundleId?mode=update would be reached", cmd.ID, p.Name)
			}
			if p.InPath && !strings.Contains(cmd.Path, "{"+p.Name+"}") {
				t.Errorf("%s: parameter %q is marked in-path but %q has no such placeholder", cmd.ID, p.Name, cmd.Path)
			}
		}
		for _, placeholder := range placeholders(cmd.Path) {
			found := false
			for _, p := range cmd.Params {
				if p.InPath && p.Name == placeholder {
					found = true
				}
			}
			if !found {
				t.Errorf("%s: path placeholder {%s} has no declared in-path parameter", cmd.ID, placeholder)
			}
		}
	}
	t.Logf("catalogue: %d commands, all read-shaped", len(Commands()))
}

// startsWithReadVerb applies the client's read-verb list to a leaf action that
// has already had its {placeholder} segment stripped.
func startsWithReadVerb(leaf string) bool {
	for _, prefix := range readLeafPrefixes {
		if strings.HasPrefix(leaf, prefix) {
			return true
		}
	}
	return false
}

// leafAction is the lowercased last path segment, ignoring placeholders.
func leafAction(path string) string {
	trimmed := strings.TrimRight(path, "/")
	if idx := strings.Index(trimmed, "/{"); idx >= 0 {
		trimmed = trimmed[:idx]
	}
	if idx := strings.LastIndexByte(trimmed, '/'); idx >= 0 {
		trimmed = trimmed[idx+1:]
	}
	return strings.ToLower(trimmed)
}

func placeholders(path string) []string {
	var out []string
	for {
		open := strings.IndexByte(path, '{')
		if open < 0 {
			return out
		}
		close := strings.IndexByte(path[open:], '}')
		if close < 0 {
			return out
		}
		out = append(out, path[open+1:open+close])
		path = path[open+close:]
	}
}

// TestReadPostRefusesMutatingLeaves is the Go port of the Python CLI's
// test_read_post_refuses_mutating_leaves: the four real JSAP write endpoints
// must be refused at runtime even if something hands the client a Command
// pointing at one.
func TestReadPostRefusesMutatingLeaves(t *testing.T) {
	fake := newFakeJSAP(t)
	client := NewSessions(fake.config()).For(1)

	for _, path := range []string{
		"/api/Tickets/CreateTicket",
		"/api/Tickets/AssignTicket",
		"/api/DocumentDispatch/SaveAllAttachments",
		"/api/BPmaster/InsertBPmasterData",
	} {
		cmd := Command{ID: "synthetic", Method: verbPost, Path: path}
		if _, err := client.Run(context.Background(), cmd, nil); err == nil {
			t.Errorf("POST %s was accepted — the read-only law must refuse it", path)
		} else if !strings.Contains(err.Error(), "READ-ONLY LAW") {
			t.Errorf("POST %s refused with %q, want a READ-ONLY LAW refusal", path, err)
		}
	}
	if got := fake.pathsHit(); len(got) != 0 {
		t.Errorf("refused calls still reached JSAP: %v", got)
	}
}

// TestRunRefusesNonReadVerbs pins that the only two verbs Run can dispatch are
// GET and the guarded POST-read; a Command carrying anything else is refused
// rather than sent.
func TestRunRefusesNonReadVerbs(t *testing.T) {
	fake := newFakeJSAP(t)
	client := NewSessions(fake.config()).For(1)

	for _, method := range []string{"PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} {
		cmd := Command{ID: "synthetic", Method: method, Path: "/api/Hierarchy/GetRoleTypes"}
		if _, err := client.Run(context.Background(), cmd, nil); err == nil {
			t.Errorf("%s was accepted — only GET and guarded POST-reads exist", method)
		}
	}
	if got := fake.pathsHit(); len(got) != 0 {
		t.Errorf("refused calls still reached JSAP: %v", got)
	}
}

// TestWholeCatalogueIssuesOnlyReadsAndLogins drives EVERY catalogued command
// against a fake JSAP and inspects what actually arrived on the wire. This is
// the guard that would catch a future entry whose declaration looks innocent
// but whose path is not.
func TestWholeCatalogueIssuesOnlyReadsAndLogins(t *testing.T) {
	fake := newFakeJSAP(t)
	client := NewSessions(fake.config()).For(1)

	for _, cmd := range Commands() {
		args := syntheticArgs(cmd)
		if _, err := client.Run(context.Background(), cmd, args); err != nil {
			t.Errorf("%s: %v", cmd.ID, err)
		}
	}

	logins := 0
	for _, req := range fake.requests() {
		switch {
		case bootstrapPaths[req.path]:
			logins++
		case req.method == http.MethodGet:
			// fine
		case req.method == http.MethodPost:
			if !hasReadLeaf(req.path) {
				t.Errorf("POST %s reached JSAP but its leaf is not a read verb", req.path)
			}
		default:
			t.Errorf("%s %s reached JSAP — only GET, guarded POST-reads and the bootstrap are permitted", req.method, req.path)
		}
		if strings.Contains(req.query, "mode=") {
			t.Errorf("%s carried a mode parameter (%s) — the mutating GetLastBundleId variant is reached exactly that way", req.path, req.query)
		}
	}
	if logins != 3 {
		t.Errorf("bootstrap requests = %d, want exactly 3 (Login, websession/set, updateSelectedCompany) for %d commands — sessions are not being shared",
			logins, len(Commands()))
	}
	t.Logf("drove %d catalogued commands: %d requests, %d of them the one-time bootstrap",
		len(Commands()), len(fake.requests()), logins)
}

// TestConcurrentCallsShareOneLogin pins the session-sharing property: a gateway
// fans tool calls out in parallel against ONE shared JSAP identity, and a login
// per call would be a login storm on a production account.
func TestConcurrentCallsShareOneLogin(t *testing.T) {
	fake := newFakeJSAP(t)
	sessions := NewSessions(fake.config())
	cmd, ok := Lookup("hierarchy.roles")
	if !ok {
		t.Fatal("hierarchy.roles missing from the catalogue")
	}

	var wg sync.WaitGroup
	for n := 0; n < 25; n++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, err := sessions.For(1).Run(context.Background(), cmd, nil); err != nil {
				t.Errorf("run: %v", err)
			}
		}()
	}
	wg.Wait()

	logins := 0
	for _, req := range fake.requests() {
		if req.path == "/api/auth/Login" {
			logins++
		}
	}
	if logins != 1 {
		t.Errorf("Login count = %d for 25 concurrent calls, want 1", logins)
	}
}

func TestBindRejectsUndeclaredParameters(t *testing.T) {
	cmd, ok := Lookup("dochub.hub")
	if !ok {
		t.Fatal("dochub.hub missing from the catalogue")
	}
	_, _, _, err := cmd.bind(map[string]any{"mode": "update"}, 68, 1)
	if err == nil {
		t.Fatal("bind accepted an undeclared parameter")
	}
	if !strings.Contains(err.Error(), "unknown parameter") {
		t.Fatalf("bind error = %q, want an unknown-parameter refusal", err)
	}
}

func TestBindFillsDefaultsCompanyAndUser(t *testing.T) {
	cmd, ok := Lookup("inventory.active")
	if !ok {
		t.Fatal("inventory.active missing from the catalogue")
	}
	_, query, _, err := cmd.bind(nil, 68, 2)
	if err != nil {
		t.Fatalf("bind: %v", err)
	}
	if got := query.Get("userId"); got != "68" {
		t.Errorf("userId = %q, want the configured user 68", got)
	}

	companyScoped, _ := Lookup("meta.permissions")
	_, query, _, err = companyScoped.bind(nil, 68, 2)
	if err != nil {
		t.Fatalf("bind: %v", err)
	}
	if got := query.Get("CompanyId"); got != "2" {
		t.Errorf("CompanyId = %q, want 2", got)
	}

	postCmd, _ := Lookup("tasks.list")
	_, _, body, err := postCmd.bind(map[string]any{"page_size": float64(10)}, 68, 1)
	if err != nil {
		t.Fatalf("bind: %v", err)
	}
	if body["limit"] != 10 {
		t.Errorf("page_size did not map to the wire name limit: %#v", body)
	}
	if body["sortBy"] != "created_on" {
		t.Errorf("fixed field sortBy missing: %#v", body)
	}
	if body["viewMode"] != "ALL" {
		t.Errorf("default viewMode missing: %#v", body)
	}
}

func TestBindRequiresDeclaredRequiredParameters(t *testing.T) {
	cmd, _ := Lookup("reports.flow")
	if _, _, _, err := cmd.bind(nil, 68, 1); err == nil {
		t.Fatal("bind accepted reports.flow without its required budgetId")
	}
}

// TestPackageNamesNoMutatingHTTPVerb walks the AST of every non-test file in
// this package. GET and POST are named (POST is the bootstrap and the guarded
// POST-read); PUT, PATCH and DELETE must not exist anywhere, so a future edit
// cannot quietly add a write path.
func TestPackageNamesNoMutatingHTTPVerb(t *testing.T) {
	forbidden := map[string]bool{"MethodPut": true, "MethodPatch": true, "MethodDelete": true}

	files, err := filepath.Glob("*.go")
	if err != nil {
		t.Fatalf("glob: %v", err)
	}
	checked := 0
	for _, f := range files {
		if strings.HasSuffix(f, "_test.go") {
			continue
		}
		checked++
		src, err := os.ReadFile(f)
		if err != nil {
			t.Fatalf("read %s: %v", f, err)
		}
		fset := token.NewFileSet()
		// Comments are dropped on purpose: only real code counts.
		file, err := parser.ParseFile(fset, f, src, 0)
		if err != nil {
			t.Fatalf("parse %s: %v", f, err)
		}
		ast.Inspect(file, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			if pkg, ok := sel.X.(*ast.Ident); ok && pkg.Name == "http" && forbidden[sel.Sel.Name] {
				t.Errorf("%s: package jsap names http.%s — RULE 0: this client is read-only",
					fset.Position(sel.Pos()), sel.Sel.Name)
			}
			return true
		})
	}
	if checked == 0 {
		t.Fatal("no non-test files were scanned — the guard would pass vacuously")
	}
	t.Logf("read-only guard scanned %d non-test file(s) in package jsap", checked)
}

// ---------------------------------------------------------------------------
// fake JSAP
// ---------------------------------------------------------------------------

type recordedRequest struct {
	method string
	path   string
	query  string
}

type fakeJSAP struct {
	t   *testing.T
	srv *httptest.Server

	mu  sync.Mutex
	log []recordedRequest
}

func newFakeJSAP(t *testing.T) *fakeJSAP {
	t.Helper()
	f := &fakeJSAP{t: t}
	f.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		f.mu.Lock()
		f.log = append(f.log, recordedRequest{method: r.Method, path: r.URL.Path, query: r.URL.RawQuery})
		f.mu.Unlock()

		w.Header().Set("Content-Type", "application/json")
		switch r.URL.Path {
		case "/api/auth/Login":
			_, _ = w.Write([]byte(`{"success":true,"user":{"userId":68,"userName":"tester"}}`))
		case "/UserManagement/AllUsers":
			w.Header().Set("Content-Type", "text/html")
			_, _ = w.Write([]byte(`<tr class="user-row"><td><input type="checkbox" data-userid="7"></td>` +
				`<td class="user-name">Test User</td><td class="user-empid">E7</td><td>Employee</td>` +
				`<td>ACCOUNTS</td><td><div class="slider round green"></div></td></tr>`))
		default:
			_, _ = w.Write([]byte(`{"success":true,"data":[]}`))
		}
	}))
	t.Cleanup(f.srv.Close)
	return f
}

func (f *fakeJSAP) config() Config {
	return Config{BaseURL: f.srv.URL, Username: "tester", Password: "unused-in-tests", UserID: 68}
}

func (f *fakeJSAP) requests() []recordedRequest {
	f.mu.Lock()
	defer f.mu.Unlock()
	out := make([]recordedRequest, len(f.log))
	copy(out, f.log)
	return out
}

func (f *fakeJSAP) pathsHit() []string {
	var out []string
	for _, r := range f.requests() {
		out = append(out, r.path)
	}
	return out
}

// syntheticArgs fills a command's required parameters with type-correct
// placeholder values so the whole catalogue can be driven in one pass.
func syntheticArgs(cmd Command) map[string]any {
	args := map[string]any{}
	for _, p := range cmd.Params {
		if !p.Required || p.FromUser || p.Default != nil {
			continue
		}
		switch p.Type {
		case TypeInt:
			args[p.Name] = float64(1)
		case TypeBool:
			args[p.Name] = true
		default:
			args[p.Name] = "TEST"
		}
	}
	return args
}

// TestScrapedUserTableParsesRows keeps the one HTML-sourced command honest: the
// User Management page has no JSON endpoint, so the parse is the contract.
func TestScrapedUserTableParsesRows(t *testing.T) {
	fake := newFakeJSAP(t)
	client := NewSessions(fake.config()).For(1)
	cmd, _ := Lookup("users.list")

	payload, err := client.Run(context.Background(), cmd, nil)
	if err != nil {
		t.Fatalf("run: %v", err)
	}
	var rows []map[string]any
	if err := json.Unmarshal(payload, &rows); err != nil {
		t.Fatalf("scraped rows are not JSON: %v (%s)", err, payload)
	}
	if len(rows) != 1 {
		t.Fatalf("rows = %d, want 1: %s", len(rows), payload)
	}
	if rows[0]["name"] != "Test User" || rows[0]["status"] != "active" {
		t.Errorf("scraped row = %#v", rows[0])
	}
}
