package mcp

import (
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

// The MCP surface for a JIVO system is read-only forever (repo CLAUDE.md RULE 0
// and memory [[mcp-never-exposes-writes]]). The CLI may write when an operator
// explicitly asks; the MCP may not, because an agent-trusted surface has no
// operator in the loop to ask.
//
// sap-b1, oms-cli and ecom-cli each carry a readonly_guard_test.go that simply
// bans every non-GET client call. Control Panel cannot reuse that test: the
// Django app takes eleven date-range READ queries as POST-JSON, because the
// filter payload does not fit a query string (call pattern 1 in
// control-panel/vault/architecture.md). A blanket POST ban here would fail on
// legitimate reads, and — worse — the obvious "fix" would be to delete the
// guard rather than narrow it.
//
// So this guard is narrower and states the boundary explicitly:
//
//	(a) tools.go makes no c.Put* / c.Patch* / c.Delete* call, and no mutating
//	    c.Post* call either (only the PostQuery* read twins);
//	(b) every makeAPIHandler("POST", ...) registration names a path in the
//	    vetted allowlist AND passes readOnly=true;
//	(c) no registered path matches the Control Panel's mutation vocabulary;
//	(d) the generic JSONL write vector (newImportCmd) stays unregistered;
//	(e) the live, fully-registered tool set contains no tool that advertises
//	    itself as a writer.
//
// (a)-(d) are structural (AST/source) assertions rather than behavioural calls,
// because the handlers are closures built inside registration functions with no
// exported seam — pinning the absence of a client write call is strictly
// stronger than proving one path refuses one method. (e) is behavioural and
// covers the runtime Cobra-tree mirror, which the AST checks cannot see.
//
// A fresh `cli-printing-press generate --force` restores the full generic
// POST/PUT/PATCH/DELETE machinery in tools.go and re-registers `import` in
// root.go. These tests exist to fail loudly the next time somebody reprints.

// vettedReadOnlyPOSTPaths is an INDEPENDENT copy of the allowlist, deliberately
// duplicated rather than imported from tools.go. If the test read the same
// variable it is meant to police, widening the runtime list would silently
// widen the test with it. Divergence is the signal.
var vettedReadOnlyPOSTPaths = []string{
	"/realise/api/beverages-data/",
	"/realise/api/compare-docs/",
	"/realise/api/dispatch-details/",
	"/realise/api/drill-down/",
	"/realise/api/hidden-sales/",
	"/realise/api/historical-realise/",
	"/realise/api/open-payments/",
	"/realise/api/sales-cn/",
	"/realise/api/sales-data/",
	"/realise/api/sales-flow/",
	"/realise/api/sales-flow/open-items/",
}

// mutatingPathVocabulary is how the Control Panel's real writes are spelled.
// The vault documents save-targets, save-closing-remark, rate-list/save,
// rate-list/delete, realise-calculator/upload, the aging-remark family,
// credit-lock / credit-unlock, verify-pin, /api/users/save, /api/users/delete
// and the OTP-gated /api/cogs/. None of them may ever appear in a registration.
var mutatingPathVocabulary = regexp.MustCompile(
	`(?i)(save|delete|upload|remark|lock|verify-pin|cogs|export)`)

// writeClientCalls matches the mutating client methods. PostQuery* is excluded
// by the negative lookahead's manual expansion below: `Post` followed by
// anything other than `Query` is a write.
var writeClientCalls = regexp.MustCompile(
	`\bc\.(Put|Patch|Delete)[A-Za-z]*\(`)

func sourceOf(t *testing.T, file string) string {
	t.Helper()
	b, err := os.ReadFile(file)
	if err != nil {
		t.Fatalf("read %s: %v", file, err)
	}
	return string(b)
}

// callGraphOf flattens every `x.Method(` call in a file into one string, with
// comments discarded, so a mention of a forbidden method in prose does not trip
// the regexes above.
func callGraphOf(t *testing.T, file string) string {
	t.Helper()
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, file, sourceOf(t, file), parser.ParseComments)
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
	return code.String()
}

// TestMCPMakesNoWriteClientCall is the load-bearing assertion: the MCP
// execution path cannot reach a mutating client method at all. It does not
// depend on the current spec being read-only.
func TestMCPMakesNoWriteClientCall(t *testing.T) {
	code := callGraphOf(t, "tools.go")

	if m := writeClientCalls.FindAllString(code, -1); len(m) > 0 {
		t.Errorf("tools.go calls mutating client methods %v — the MCP surface "+
			"must never expose a write. A fresh printing-press generate "+
			"restores this machinery; re-apply the READ-ONLY LAW guard.", m)
	}

	// POST is allowed, but only through the PostQuery* read twins. c.Post,
	// c.PostWithParams and c.PostWithParamsAndHeaders are the writers.
	for _, call := range strings.Split(code, "\n") {
		if !strings.HasPrefix(call, "c.Post") {
			continue
		}
		if !strings.HasPrefix(call, "c.PostQuery") {
			t.Errorf("tools.go calls %s — POST is permitted here ONLY via the "+
				"PostQuery* read path; %s is the mutating twin", call, call)
		}
	}
}

// TestMCPRefusesNonGETByConstruction proves the handler carries an explicit
// fail-closed guard naming the read-only law, so a future endpoint registered
// with a mutating method is refused rather than silently dispatched.
func TestMCPRefusesNonGETByConstruction(t *testing.T) {
	src := sourceOf(t, "tools.go")
	if !strings.Contains(src, "READ-ONLY LAW") {
		t.Error("tools.go has no READ-ONLY LAW guard comment — the guard was " +
			"lost, most likely by a regeneration")
	}
	if !strings.Contains(src, "is not permitted (GET only") {
		t.Error("tools.go does not refuse non-GET methods with the fail-closed " +
			"error; check the method switch has a refusing guard")
	}
	for _, verb := range []string{`case "PUT":`, `case "PATCH":`, `case "DELETE":`} {
		if strings.Contains(src, verb) {
			t.Errorf("tools.go has a %s dispatch branch — the write machinery "+
				"came back with a regeneration; delete it again", verb)
		}
	}
}

// TestRuntimePOSTAllowlistMatchesVettedList pins the runtime allowlist against
// this test's independent copy. Widening one without the other fails here,
// which is the point: adding a POST path must be a deliberate, reviewed act.
func TestRuntimePOSTAllowlistMatchesVettedList(t *testing.T) {
	got := make([]string, 0, len(readOnlyPOSTPaths))
	for p, ok := range readOnlyPOSTPaths {
		if ok {
			got = append(got, p)
		}
	}
	sort.Strings(got)
	want := append([]string(nil), vettedReadOnlyPOSTPaths...)
	sort.Strings(want)

	if strings.Join(got, "\n") != strings.Join(want, "\n") {
		t.Errorf("readOnlyPOSTPaths drifted from the vetted allowlist.\n"+
			" runtime: %v\n  vetted: %v\n"+
			"Every POST path must be proven a read against the live app before "+
			"it is added to BOTH lists.", got, want)
	}
}

// TestEveryRegisteredPOSTIsAVettedRead walks the actual makeAPIHandler
// registrations and checks each one's method, path and readOnly flag. This is
// what catches a regenerated tools.go that registers `POST /realise/api/
// save-targets/` with readOnly=false.
func TestEveryRegisteredPOSTIsAVettedRead(t *testing.T) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, "tools.go", sourceOf(t, "tools.go"), parser.ParseComments)
	if err != nil {
		t.Fatalf("parse tools.go: %v", err)
	}

	allowed := make(map[string]bool, len(vettedReadOnlyPOSTPaths))
	for _, p := range vettedReadOnlyPOSTPaths {
		allowed[p] = true
	}

	registrations := 0
	ast.Inspect(f, func(n ast.Node) bool {
		ce, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}
		ident, ok := ce.Fun.(*ast.Ident)
		if !ok || ident.Name != "makeAPIHandler" || len(ce.Args) < 3 {
			return true
		}
		registrations++

		method, ok := stringLit(ce.Args[0])
		if !ok {
			t.Errorf("makeAPIHandler at %s has a non-literal method — the guard "+
				"can only verify literal registrations", fset.Position(ce.Pos()))
			return true
		}
		path, ok := stringLit(ce.Args[1])
		if !ok {
			t.Errorf("makeAPIHandler at %s has a non-literal path — the guard "+
				"can only verify literal registrations", fset.Position(ce.Pos()))
			return true
		}
		readOnly := isTrueLit(ce.Args[2])

		if mutatingPathVocabulary.MatchString(path) {
			t.Errorf("registered path %q matches the Control Panel's mutation "+
				"vocabulary %s — this endpoint changes data and must never be "+
				"an MCP tool", path, mutatingPathVocabulary)
		}

		switch method {
		case "GET":
			// always fine
		case "POST":
			if !allowed[path] {
				t.Errorf("registered POST %q is not in the vetted read-only "+
					"allowlist. POST is permitted here only for the Django "+
					"app's date-range READ queries; prove this endpoint is a "+
					"read against the live app, or drop the tool.", path)
			}
			if !readOnly {
				t.Errorf("registered POST %q passes readOnly=false, which "+
					"routes it to the mutating client path", path)
			}
		default:
			t.Errorf("registered %s %q — the MCP surface allows GET and the "+
				"vetted POST reads only", method, path)
		}
		return true
	})

	if registrations == 0 {
		t.Error("found no makeAPIHandler registrations at all — wrong file, or " +
			"the registration shape changed and this guard is now blind")
	}
}

// TestImportCommandStaysUnregistered pins the removal of the generator's
// generic JSONL-driven write vector. newImportCmd remains defined but must
// never be wired into the command tree, because the runtime Cobra-tree mirror
// would turn it into an MCP tool that POSTs arbitrary payloads.
func TestImportCommandStaysUnregistered(t *testing.T) {
	src := sourceOf(t, "../cli/root.go")
	if strings.Contains(src, "AddCommand(newImportCmd(") {
		t.Error("root.go registers newImportCmd — the generic JSONL-driven " +
			"POST is the only write vector the generator ships, and it must " +
			"stay unregistered (re-apply the removal after generate --force)")
	}
}

// TestCobraMirrorStaysUnregistered pins the removal of the runtime Cobra-tree
// mirror. It shelled out to a sibling CLI for every user-facing command, and it
// is the one registration path the AST checks above cannot inspect — the tool
// set is decided at runtime by walking cli.RootCmd(), so a write command added
// to the CLI later would silently become an MCP tool. It also produced the only
// two tools on this surface that advertised destructiveHint=true (`sync` and
// `workflow_archive`).
func TestCobraMirrorStaysUnregistered(t *testing.T) {
	code := callGraphOf(t, "tools.go")
	if strings.Contains(code, "cobratree.RegisterAll(") {
		t.Error("tools.go calls cobratree.RegisterAll — the runtime Cobra-tree " +
			"mirror decides its tool set by walking the CLI at startup, so any " +
			"write command added to the CLI becomes an MCP tool without " +
			"touching this package. Keep it unregistered (re-apply after " +
			"generate --force).")
	}
}

// TestLocalStoreToolsStayUnregistered pins the removal of `search` and `sql`.
// They read a SQLite file that only the (now removed) `sync` tool populates, so
// in the gateway container they can only ever error. The handlers stay defined
// and unit-tested; only the registration is gone.
func TestLocalStoreToolsStayUnregistered(t *testing.T) {
	src := sourceOf(t, "tools.go")
	for _, reg := range []string{`mcplib.NewTool("search"`, `mcplib.NewTool("sql"`} {
		if strings.Contains(src, reg) {
			t.Errorf("tools.go registers %s — the local-store tools depend on a "+
				"sync that no longer exists and on a container-local DB with no "+
				"volume behind it; they cannot return data as deployed", reg)
		}
	}
}

// TestRegisteredToolsAdvertiseNoWrites is the behavioural backstop. It builds
// the real, fully-registered tool set — typed endpoint tools AND the runtime
// Cobra-tree mirror, which the AST checks above cannot see — and fails if any
// tool advertises itself as destructive or omits the read-only hint.
func TestRegisteredToolsAdvertiseNoWrites(t *testing.T) {
	s := server.NewMCPServer("guard", "test", server.WithToolCapabilities(false))
	RegisterTools(s)

	tools := s.ListTools()
	if len(tools) == 0 {
		t.Fatal("RegisterTools registered nothing — the guard is blind")
	}

	for name, st := range tools {
		ann := st.Tool.Annotations
		if ann.DestructiveHint != nil && *ann.DestructiveHint {
			t.Errorf("tool %q advertises destructiveHint=true — no write tool "+
				"may ever be registered on a JIVO MCP surface", name)
		}
		if ann.ReadOnlyHint == nil || !*ann.ReadOnlyHint {
			t.Errorf("tool %q does not carry readOnlyHint=true. Either it "+
				"writes (remove it) or the hint was dropped (restore it) — an "+
				"unhinted tool reads to a host as 'could write or delete'.",
				name)
		}
		if mutatingPathVocabulary.MatchString(name) {
			t.Errorf("tool name %q matches the mutation vocabulary %s — check "+
				"it is not a write that slipped in through the Cobra mirror",
				name, mutatingPathVocabulary)
		}
	}
}

func stringLit(e ast.Expr) (string, bool) {
	bl, ok := e.(*ast.BasicLit)
	if !ok || bl.Kind != token.STRING {
		return "", false
	}
	return strings.Trim(bl.Value, "`\""), true
}

func isTrueLit(e ast.Expr) bool {
	ident, ok := e.(*ast.Ident)
	return ok && ident.Name == "true"
}
