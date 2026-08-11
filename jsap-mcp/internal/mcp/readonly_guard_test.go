// Copyright 2026 daman8271 and contributors.
// JSAP MCP server — structural read-only guard for the tool package.

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

// forbiddenSelectors are call names that would mean this package is talking to
// JSAP itself rather than through the catalogued-command path. Every request
// must go through jsap.Client.Run, which accepts a compiled-in Command and
// nothing else; a hand-built request here would bypass the catalogue, and with
// it the exclusion of GetLastBundleId?mode=update, DocumentHub/Download and
// every Insert*/Save* endpoint JSAP exposes.
var forbiddenSelectors = map[string]string{
	"Do":                    "an HTTP request built here would bypass the catalogue",
	"Post":                  "no non-GET request may originate in the tool layer",
	"PostForm":              "no non-GET request may originate in the tool layer",
	"Put":                   "the MCP surface is read-only forever",
	"Patch":                 "the MCP surface is read-only forever",
	"Delete":                "the MCP surface is read-only forever",
	"NewRequest":            "requests are built in package jsap, under the read-only law",
	"NewRequestWithContext": "requests are built in package jsap, under the read-only law",
	"MethodPost":            "the tool layer must not name an HTTP verb at all",
	"MethodPut":             "the MCP surface is read-only forever",
	"MethodPatch":           "the MCP surface is read-only forever",
	"MethodDelete":          "the MCP surface is read-only forever",
}

// forbiddenImports are packages the tool layer has no business importing. Its
// only route to JSAP is package jsap.
var forbiddenImports = map[string]string{
	`"net/http"`: "the tool layer must not speak HTTP; package jsap owns every request",
	`"net/url"`:  "a URL assembled here would be a path this catalogue never approved",
	`"os/exec"`:  "nothing here shells out",
	`"net/rpc"`:  "no side channel to anything",
}

// TestMCPPackageCannotBuildItsOwnRequest walks the AST of every non-test file in
// this package. Reading the AST rather than grepping means comments and
// description strings — this file's own doc comment, and the tool descriptions
// that talk about writes being excluded — cannot trip it.
func TestMCPPackageCannotBuildItsOwnRequest(t *testing.T) {
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
		file, err := parser.ParseFile(fset, f, src, parser.ImportsOnly)
		if err != nil {
			t.Fatalf("parse imports of %s: %v", f, err)
		}
		for _, imp := range file.Imports {
			if why, bad := forbiddenImports[imp.Path.Value]; bad {
				t.Errorf("%s: package mcp imports %s — %s", fset.Position(imp.Pos()), imp.Path.Value, why)
			}
		}

		fset = token.NewFileSet()
		file, err = parser.ParseFile(fset, f, src, 0)
		if err != nil {
			t.Fatalf("parse %s: %v", f, err)
		}
		ast.Inspect(file, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			if why, bad := forbiddenSelectors[sel.Sel.Name]; bad {
				t.Errorf("%s: package mcp references %q — %s. RULE 0: the MCP surface is strictly read-only.",
					fset.Position(sel.Pos()), sel.Sel.Name, why)
			}
			return true
		})
	}

	if checked == 0 {
		t.Fatal("no non-test files were scanned — the guard would pass vacuously")
	}
	t.Logf("read-only guard scanned %d non-test file(s) in package mcp", checked)
}

// TestExecutionPathIsSingle pins that every tool result comes from run(), the
// one function that resolves a catalogued id. If a future handler grew its own
// dispatch, the catalogue would stop being the whole surface — which is the
// only reason any of the exclusions hold.
func TestExecutionPathIsSingle(t *testing.T) {
	src, err := os.ReadFile("tools.go")
	if err != nil {
		t.Fatalf("read tools.go: %v", err)
	}
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, "tools.go", src, 0)
	if err != nil {
		t.Fatalf("parse tools.go: %v", err)
	}

	runCalls, sessionUses := 0, 0
	ast.Inspect(file, func(n ast.Node) bool {
		sel, ok := n.(*ast.SelectorExpr)
		if !ok {
			return true
		}
		switch sel.Sel.Name {
		case "run":
			runCalls++
		case "Run":
			// jsap.Client.Run — must appear exactly once, inside run().
			sessionUses++
		}
		return true
	})
	if sessionUses != 1 {
		t.Errorf("jsap.Client.Run is called from %d place(s) in tools.go, want exactly 1 (inside run) — "+
			"one execution path is what makes the catalogue the whole surface", sessionUses)
	}
	if runCalls == 0 {
		t.Error("no handler calls run() — the guard would pass vacuously")
	}
}
