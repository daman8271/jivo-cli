package mcp

import (
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// forbiddenCalls are the write-capable entry points that exist elsewhere in this
// binary. internal/client has Create (POST) and Update (PATCH), and internal/cli
// exposes draft/post/patch commands on top of them. None of that may EVER be
// reachable from the MCP surface: the MCP server is published to the internet
// through a gateway and answers questions from a phone, so a write path here is
// a write path for anyone holding the URL.
//
// TestRegisteredToolsAreReadOnly already checks the advertised ReadOnlyHint
// annotation and pins the exact tool set. That is necessary but not sufficient —
// an annotation is a claim, and a handler marked read-only can still call a
// write method. This test closes that gap structurally by refusing to compile a
// package that so much as mentions the write API.
var forbiddenCalls = map[string]string{
	"Create":       "client.Create issues an HTTP POST to the Service Layer",
	"Update":       "client.Update issues an HTTP PATCH to the Service Layer",
	"Delete":       "client.Delete issues an HTTP DELETE to the Service Layer",
	"attemptWrite": "internal write helper",
	// The most dangerous of the four, and the reason this list is worth keeping.
	// client.SaveDraftToDocument presses Add on a draft: stock moves, a vendor's
	// ledger moves, and it lands in a GST return. Every other write on this list
	// has a way back from inside this binary; this one has none — only SAP can
	// reverse it, and only a human in the SAP B1 client. It is reachable from
	// `sapb1 add-draft` in a terminal and from nowhere else.
	"SaveDraftToDocument": "client.SaveDraftToDocument POSTs a draft into the books — irreversible from this CLI",
}

// knownReadOnlyMethods are the exported methods on *client.Client that are
// safe from here: reads, and session bookkeeping that changes nothing in SAP's
// books. Every exported method must appear either here or in forbiddenCalls —
// see TestEveryClientWriteMethodIsClassified. Adding a name here is a decision,
// which is the point: it cannot happen by accident.
var knownReadOnlyMethods = map[string]bool{
	"Query":              true,
	"QueryAll":           true,
	"GetEntity":          true, // a keyed GET; 404 is an answer, not a write
	"GetAdminInfo":       true, // General Settings; a body-less POST to a function import that changes nothing (client/admininfo.go)
	"Login":              true,
	"Logout":             true,
	"HasSession":         true,
	"SessionAge":         true,
	"LoadCachedSession":  true,
	"ClearCachedSession": true,
	"ClearSharedSession": true,
	"SetErrWriter":       true,
}

// forbiddenIdents are HTTP verbs that must never appear in this package. Reads
// go out as GET; the only non-GET the client may perform is Login/Logout, which
// lives in internal/client and is never referenced by verb from here.
var forbiddenIdents = map[string]bool{
	"MethodPost":   true,
	"MethodPut":    true,
	"MethodPatch":  true,
	"MethodDelete": true,
}

// TestMCPPackageCannotReachWriteAPI walks the AST of every non-test file in this
// package and fails if any of them calls a write method or names a mutating HTTP
// verb. It reads the AST rather than grepping so that comments and strings (this
// file's own doc comment included, and server.go's "Write operations are not
// exposed" description text) cannot trip it.
func TestMCPPackageCannotReachWriteAPI(t *testing.T) {
	files, err := filepath.Glob("*.go")
	if err != nil {
		t.Fatalf("glob: %v", err)
	}
	if len(files) == 0 {
		t.Fatal("no .go files found — is the test running in the package directory?")
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
			name := sel.Sel.Name
			if why, bad := forbiddenCalls[name]; bad {
				t.Errorf("%s: MCP package references %q — %s. RULE 0: the MCP surface is strictly read-only and must never reach a write path.",
					fset.Position(sel.Pos()), name, why)
			}
			if forbiddenIdents[name] {
				if pkg, ok := sel.X.(*ast.Ident); ok && pkg.Name == "http" {
					t.Errorf("%s: MCP package names http.%s — only GET is permitted from the MCP surface.",
						fset.Position(sel.Pos()), name)
				}
			}
			return true
		})
	}

	if checked == 0 {
		t.Fatal("no non-test files were scanned — the guard would pass vacuously")
	}
	t.Logf("read-only guard scanned %d non-test file(s) in package mcp", checked)
}

// TestMCPPackageBuildsClientsOnlyThroughClientFor is the structural half of the
// login-storm fix, and the reason (*Server).clientFor is not dead code.
//
// The defect: every tool built its own client with client.New — the constructor
// that shares NOTHING — so a burst of concurrent tool calls all missed the
// on-disk session cache before any of them had finished writing it, and each
// opened its own SAP session. Measured: 30 parallel calls, 29 Logins, 29
// licensed Service Layer slots held for their full TTL, since the MCP path
// never logs out.
//
// The behavioural regression tests (TestConcurrentToolCallsShareOneLogin and
// friends) prove the tools that exist today share sessions. This one proves the
// property for tools that do NOT exist yet: a new handler that reaches for
// client.New instead of s.clientFor fails the build's tests immediately, rather
// than quietly reintroducing the storm on one code path while the others stay
// correct — which is exactly how the DocumentStatus fix ended up applied to the
// MCP surface and not to the CLI.
func TestMCPPackageBuildsClientsOnlyThroughClientFor(t *testing.T) {
	files, err := filepath.Glob("*.go")
	if err != nil {
		t.Fatalf("glob: %v", err)
	}

	sharing := 0
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
		file, err := parser.ParseFile(fset, f, src, 0)
		if err != nil {
			t.Fatalf("parse %s: %v", f, err)
		}
		ast.Inspect(file, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			pkg, ok := sel.X.(*ast.Ident)
			if !ok || pkg.Name != "client" {
				return true
			}
			switch sel.Sel.Name {
			case "New":
				t.Errorf("%s: MCP package calls client.New, which shares no session store — "+
					"use (*Server).clientFor so concurrent tool calls cost ONE Login per company instead of one per call",
					fset.Position(sel.Pos()))
			case "NewWithSessions":
				sharing++
			}
			return true
		})
	}

	if checked == 0 {
		t.Fatal("no non-test files were scanned — the guard would pass vacuously")
	}
	if sharing != 1 {
		t.Errorf("client.NewWithSessions is called from %d place(s), want exactly 1 (inside clientFor) — "+
			"one constructor is what makes the session-sharing property checkable at all", sharing)
	}
}

// TestEveryClientWriteMethodIsClassified is the guard on the guard.
//
// forbiddenCalls is a hand-written list, and a hand-written list of dangerous
// things silently stops protecting you the day somebody adds a dangerous thing
// and forgets. This test walks EVERY exported method on *client.Client in the
// whole client package and insists each one has been classified: either named
// as forbidden, or explicitly listed as read-only.
//
// Note the guard matches bare SELECTOR names, so an unrelated `x.Delete(...)`
// anywhere in package mcp would also trip TestMCPPackageCannotReachWriteAPI.
// None exists today, and that false positive is the cheap direction to fail in.
func TestEveryClientWriteMethodIsClassified(t *testing.T) {
	files, err := filepath.Glob(filepath.Join("..", "client", "*.go"))
	if err != nil {
		t.Fatalf("glob: %v", err)
	}
	if len(files) == 0 {
		t.Fatal("no client files found — the guard would pass vacuously")
	}

	found := 0
	for _, f := range files {
		if strings.HasSuffix(f, "_test.go") {
			continue
		}
		src, err := os.ReadFile(f)
		if err != nil {
			t.Fatalf("read %s: %v", f, err)
		}
		fset := token.NewFileSet()
		file, err := parser.ParseFile(fset, f, src, 0)
		if err != nil {
			t.Fatalf("parse %s: %v", f, err)
		}

		for _, decl := range file.Decls {
			fn, ok := decl.(*ast.FuncDecl)
			if !ok || fn.Recv == nil || len(fn.Recv.List) == 0 || !fn.Name.IsExported() {
				continue
			}
			star, ok := fn.Recv.List[0].Type.(*ast.StarExpr)
			if !ok {
				continue
			}
			ident, ok := star.X.(*ast.Ident)
			if !ok || ident.Name != "Client" {
				continue
			}
			found++
			name := fn.Name.Name
			_, forbidden := forbiddenCalls[name]
			if !forbidden && !knownReadOnlyMethods[name] {
				t.Errorf("%s: (*client.Client).%s is neither named as forbidden nor listed as read-only — classify it. "+
					"If it can change anything in SAP, add it to forbiddenCalls; if it cannot, add it to knownReadOnlyMethods.",
					fset.Position(fn.Pos()), name)
			}
		}
	}

	if found < 10 {
		t.Fatalf("only %d exported *Client methods were scanned — the walk is broken", found)
	}
	t.Logf("classified %d exported methods on *client.Client", found)
}
