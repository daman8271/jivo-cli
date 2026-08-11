package mcp

import (
	"encoding/json"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"regexp"
	"sort"
	"strings"
	"testing"

	"github.com/mark3labs/mcp-go/server"
)

// The MCP surface for a JIVO system is read-only forever. The CLI may write
// when an operator explicitly asks; the MCP may not, because an agent-trusted
// surface has no operator in the loop to ask.
//
// EXIM already carries a transport-level GET-only vow in
// internal/client/client.go (see .printing-press-patches/client-readonly-guard.md),
// which sits BELOW this layer and covers more. These tests are the layer above
// it: they pin the MCP surface itself, so a client-layer regression cannot
// silently open a write path through an agent-trusted tool.
//
// There are TWO execution paths that reach the HTTP client:
//
//	tools.go      the direct endpoint-tool handler
//	code_orch.go  the code-orchestration executor (the Cloudflare pattern the
//	              press applies above 50 endpoints)
//
// Guarding only the first leaves the second as a complete write bypass. A
// fresh `cli-printing-press generate` restores the generic POST/PUT/PATCH/
// DELETE machinery in BOTH, so these tests exist to fail loudly the next time
// somebody reprints and forgets the GET-only guard.

var writeClientCalls = regexp.MustCompile(
	`\bc\.(Post|Put|Patch|Delete)[A-Za-z]*\(`)

// writeToolNames matches a tool name that advertises a mutation. Registering
// one is a hard failure regardless of what the handler actually does — the
// name is what an agent routes on.
var writeToolNames = regexp.MustCompile(
	`(?i)(^|_)(create|update|delete|remove|post|put|patch|write|insert|upsert|import|dispatch|move|register|submit|approve|cancel|close|set|add|edit|save|send|login|logout|revoke)(_|$)`)

// registeredMCPToolNames builds the real server exactly as cmd/exim-pp-mcp
// does and reports every tool name the MCP handshake would advertise.
func registeredMCPToolNames(t *testing.T) []string {
	t.Helper()
	s := server.NewMCPServer("Jivo Exim", "test", server.WithToolCapabilities(false))
	RegisterTools(s)
	names := make([]string, 0, 16)
	for name := range s.ListTools() {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

// TestNoWriteToolIsRegistered is the behavioural guard the task asks for: it
// registers the real tool set and fails if any tool whose name advertises a
// mutation ever appears. This catches a new generated command reaching the
// cobratree walker as much as a hand-added typed tool.
func TestNoWriteToolIsRegistered(t *testing.T) {
	for _, name := range registeredMCPToolNames(t) {
		if writeToolNames.MatchString(name) {
			t.Errorf("MCP tool %q advertises a write operation — the JIVO MCP "+
				"surface is read-only forever. Either the command must be added "+
				"to cobratree.frameworkCommands / marked mcp:hidden, or the typed "+
				"tool must not be registered.", name)
		}
	}
}

// TestRegisteredToolSetIsPinned pins the exact advertised surface. A new tool
// appearing here is not automatically wrong, but it must be looked at by a
// human and re-pinned deliberately rather than shipped by a regeneration.
func TestRegisteredToolSetIsPinned(t *testing.T) {
	want := []string{
		"analytics",
		"context",
		"exim_execute",
		"exim_search",
		"search",
		"sql",
		"sync",
		"tail",
		"workflow",
		"workflow_archive",
		"workflow_status",
	}
	got := registeredMCPToolNames(t)
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Errorf("registered MCP tool set changed.\n got: %v\nwant: %v\n"+
			"Re-pin only after confirming every new tool is read-only.", got, want)
	}
}

// TestMCPExecutionPathsMakeNoWriteClientCall proves neither execution path can
// reach a mutating client method at all. This is the load-bearing assertion:
// it does not depend on the current spec being GET-only.
func TestMCPExecutionPathsMakeNoWriteClientCall(t *testing.T) {
	for _, file := range []string{"tools.go", "code_orch.go"} {
		src := sourceOf(t, file)
		// Walk the AST rather than grepping the source so a mention of a
		// write method in prose or a string literal does not trip the check.
		fset := token.NewFileSet()
		f, err := parser.ParseFile(fset, file, src, parser.ParseComments)
		if err != nil {
			t.Fatalf("parse %s: %v", file, err)
		}
		var code strings.Builder
		ast.Inspect(f, func(n ast.Node) bool {
			ce, ok := n.(*ast.CallExpr)
			if !ok {
				return true
			}
			sel, ok := ce.Fun.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			ident, ok := sel.X.(*ast.Ident)
			if !ok {
				return true
			}
			code.WriteString(ident.Name + "." + sel.Sel.Name + "(\n")
			return true
		})
		if m := writeClientCalls.FindAllString(code.String(), -1); len(m) > 0 {
			t.Errorf("%s calls mutating client methods %v — the MCP surface must "+
				"never expose a write. A fresh printing-press generate restores "+
				"this machinery; re-apply the GET-only guard.", file, m)
		}
	}
}

// TestMCPGuardsRefuseNonGETByConstruction proves each path carries an explicit
// fail-closed default branch naming the read-only law, so a future endpoint
// with a non-GET method is refused rather than silently unhandled.
func TestMCPGuardsRefuseNonGETByConstruction(t *testing.T) {
	for _, file := range []string{"tools.go", "code_orch.go"} {
		src := sourceOf(t, file)
		if !strings.Contains(src, "READ-ONLY LAW") {
			t.Errorf("%s has no READ-ONLY LAW guard comment — the GET-only guard "+
				"was lost, most likely by a regeneration", file)
		}
		if !strings.Contains(src, "is not permitted (GET only") {
			t.Errorf("%s does not refuse non-GET methods with the fail-closed "+
				"error; check the method switch has a refusing default branch", file)
		}
	}
}

// TestCodeOrchCatalogIsGETOnly checks the in-binary endpoint catalog that
// exim_execute dispatches against. exim_execute takes only a catalogued
// endpoint_id — there is no free-form method/path input — so a GET-only
// catalog is what makes the tool safe in fact as well as by construction.
func TestCodeOrchCatalogIsGETOnly(t *testing.T) {
	if len(codeOrchEndpoints) == 0 {
		t.Fatal("codeOrchEndpoints is empty — wrong build or a lost catalog?")
	}
	for _, ep := range codeOrchEndpoints {
		if ep.Method != "GET" {
			t.Errorf("catalogued endpoint %s is %s %s; EXIM is read-only (RULE 0) "+
				"and its MCP surface must never expose a write", ep.ID, ep.Method, ep.Path)
		}
	}
}

// TestSpecIsGETOnly is the weaker, spec-level check: every published endpoint
// is a GET today. It is NOT sufficient on its own — that is exactly why the
// tests above assert on the code and the catalog instead — but a failure here
// means the spec itself grew a write and needs a human decision.
func TestSpecIsGETOnly(t *testing.T) {
	raw, err := readFile("../../../exim-openapi.json")
	if err != nil {
		t.Skipf("exim-openapi.json not readable from the test working directory: %v", err)
	}
	var doc struct {
		Paths map[string]map[string]json.RawMessage `json:"paths"`
	}
	if err := json.Unmarshal([]byte(raw), &doc); err != nil {
		t.Fatalf("parse exim-openapi.json: %v", err)
	}
	gets := 0
	for p, ops := range doc.Paths {
		for verb := range ops {
			switch strings.ToLower(verb) {
			case "get":
				gets++
			case "post", "put", "patch", "delete":
				t.Errorf("spec declares %s %s; EXIM is read-only (RULE 0) and its "+
					"MCP surface must never expose a write", strings.ToUpper(verb), p)
			}
		}
	}
	if gets == 0 {
		t.Error("spec declares no GET operations at all — wrong file?")
	}
}

func sourceOf(t *testing.T, file string) string {
	t.Helper()
	b, err := readFile(file)
	if err != nil {
		t.Fatalf("read %s: %v", file, err)
	}
	return b
}

func readFile(p string) (string, error) {
	b, err := os.ReadFile(p)
	return string(b), err
}
