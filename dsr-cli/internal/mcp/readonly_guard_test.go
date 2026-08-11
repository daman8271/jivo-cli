package mcp

import (
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// forbiddenQualified are package-qualified calls that must never appear in the
// MCP surface. dsr has no write path to a business system at all — no
// ExecContext, no POST — so the risk this closes is the OTHER kind of write:
// `dsr schema dump` does os.MkdirAll + os.WriteFile at eight sites in
// internal/cli/schema.go, and a future "helpful" cache or export in a tool
// handler would be the same class of thing arriving quietly.
//
// The tool-set pin (TestRegisteredToolSetIsExactlyTheAllowlist) checks the
// advertised annotations and the exact names. That is necessary but not
// sufficient: an annotation is a claim, and a handler marked read-only can
// still open a file or POST. This test closes that gap structurally.
var forbiddenQualified = map[string]map[string]string{
	"os": {
		"WriteFile":   "writes a file",
		"Create":      "creates/truncates a file",
		"OpenFile":    "may open a file for writing",
		"Mkdir":       "creates a directory",
		"MkdirAll":    "creates directories (this is what `schema dump` does)",
		"Remove":      "deletes a file",
		"RemoveAll":   "deletes a tree",
		"Rename":      "moves a file",
		"Truncate":    "truncates a file",
		"Chmod":       "changes file permissions",
		"Symlink":     "creates a symlink",
		"Link":        "creates a hard link",
		"WriteString": "writes to a stream that may be a file",
	},
	"http": {
		"MethodPost":   "names a mutating HTTP verb",
		"MethodPut":    "names a mutating HTTP verb",
		"MethodPatch":  "names a mutating HTTP verb",
		"MethodDelete": "names a mutating HTTP verb",
		"Post":         "issues an HTTP POST",
		"PostForm":     "issues an HTTP POST",
	},
	"ioutil": {
		"WriteFile": "writes a file",
	},
}

// forbiddenSelectors are method names that mean "execute a mutating statement"
// on any receiver. dsr's own db layer never calls ExecContext — user SQL only
// ever reaches QueryContext, inside a transaction that is always rolled back —
// and the MCP package must not be the first place that changes.
var forbiddenSelectors = map[string]string{
	"Exec":        "executes a statement that may write",
	"ExecContext": "executes a statement that may write",
	"MustExec":    "executes a statement that may write",
}

// TestMCPPackageCannotWrite walks the AST of every non-test Go file in this
// package and in cobratree/ and fails if any of them names a write path. It
// reads the AST rather than grepping, so comments and string literals — this
// file's own doc comments, and the tool descriptions that contain the words
// "write" and "delete" — cannot trip it.
func TestMCPPackageCannotWrite(t *testing.T) {
	var files []string
	err := filepath.WalkDir(".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
			return nil
		}
		files = append(files, path)
		return nil
	})
	if err != nil {
		t.Fatalf("walk: %v", err)
	}
	if len(files) == 0 {
		t.Fatal("no non-test .go files found — the guard would pass vacuously")
	}

	for _, f := range files {
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
			if why, bad := forbiddenSelectors[name]; bad {
				t.Errorf("%s: MCP package calls .%s — %s. RULE 0: the MCP surface is read-only forever.",
					fset.Position(sel.Pos()), name, why)
			}
			pkg, ok := sel.X.(*ast.Ident)
			if !ok {
				return true
			}
			if byName, watched := forbiddenQualified[pkg.Name]; watched {
				if why, bad := byName[name]; bad {
					t.Errorf("%s: MCP package references %s.%s — %s. RULE 0: the MCP surface is read-only forever.",
						fset.Position(sel.Pos()), pkg.Name, name, why)
				}
			}
			return true
		})
	}

	t.Logf("read-only guard scanned %d non-test file(s): %v", len(files), files)
}

// TestNoToolCanReachSchemaDump is the specific exclusion the probe called out.
// `dsr schema dump` is the only dsr command with side effects of any kind: it
// MkdirAll/WriteFiles a catalog, ~131 sample JSON files and an INDEX.md under
// --out, and runs for minutes. It has no agent value (everything it writes is
// available live through the dsr_schema actions) and it must never be an
// action, a fallback, or an argv fragment.
func TestNoToolCanReachSchemaDump(t *testing.T) {
	for _, spec := range specs {
		for _, tok := range spec.Fixed {
			if tok == "dump" {
				t.Errorf("tool %s has a fixed argv containing %q", spec.Name, tok)
			}
		}
		for _, a := range spec.Actions {
			for _, tok := range a.Argv {
				if tok == "dump" {
					t.Errorf("tool %s action %s has argv %v — `schema dump` writes files and must never be exposed", spec.Name, a.Name, a.Argv)
				}
			}
			if a.Name == "dump" {
				t.Errorf("tool %s declares an action named %q", spec.Name, a.Name)
			}
		}
	}
}

// TestUnknownActionIsAnErrorNotAPassthrough proves the allowlist is closed: an
// action the table does not declare cannot fall through to the CLI. This is
// what makes "dump is not in the table" an actual guarantee rather than an
// absence.
func TestUnknownActionIsAnErrorNotAPassthrough(t *testing.T) {
	for _, spec := range specs {
		if len(spec.Actions) == 0 {
			continue
		}
		for _, bad := range []string{"dump", "post", "delete", "", "LIST"} {
			raw := map[string]any{"action": bad}
			if _, err := buildArgv(spec, raw, map[string]string{}); err == nil {
				t.Errorf("%s accepted action %q — unknown actions must be errors", spec.Name, bad)
			}
		}
	}
}
