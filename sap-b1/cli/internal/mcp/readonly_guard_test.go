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
	"attemptWrite": "internal write helper",
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
