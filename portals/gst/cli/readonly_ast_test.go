package main

import (
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

// readonly_ast_test.go walks the source of this package and refuses, at the
// syntax level, the things that would let a write exist.
//
// It is stricter than the usual "scan for http.MethodPut" pattern, deliberately:
// pinning the IMPORT is stronger than pinning a selector, because a helper in
// another file cannot open a connection at all if it cannot import net/http.
// (CRITIQUE §5b.)

func parsePackage(t *testing.T) map[string]*ast.File {
	t.Helper()
	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, ".", func(fi fs.FileInfo) bool {
		return !strings.HasSuffix(fi.Name(), "_test.go")
	}, parser.ParseComments)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	out := map[string]*ast.File{}
	for _, p := range pkgs {
		for name, f := range p.Files {
			out[filepath.Base(name)] = f
		}
	}
	if len(out) == 0 {
		t.Fatal("parsed 0 source files — the scanner is broken")
	}
	return out
}

// TestOnlyTheClientMayTalkHTTP: exactly one file may import net/*. Nothing else
// in the binary can reach the network, by construction.
func TestOnlyTheClientMayTalkHTTP(t *testing.T) {
	// file → the net/* imports it is allowed to have
	allowed := map[string]bool{"client.go": true}
	for name, f := range parsePackage(t) {
		for _, imp := range f.Imports {
			path, _ := strconv.Unquote(imp.Path.Value)
			switch {
			case path == "net/http/httputil":
				// a request/response dump would print the login body, password included
				t.Errorf("%s imports net/http/httputil — it can dump a login request, password and all", name)
			case path == "net" || strings.HasPrefix(path, "net/"):
				if !allowed[name] {
					t.Errorf("%s imports %q — only client.go may talk to the network", name, path)
				}
			case path == "os/exec":
				// reserved for the captcha solver, which does not exist yet
				if name != "captcha.go" {
					t.Errorf("%s imports os/exec — only the captcha solver may run a subprocess", name)
				}
			}
		}
	}
}

// TestNoMutatingHTTPCalls: no PUT/PATCH/DELETE, no http.Post shortcut, anywhere.
func TestNoMutatingHTTPCalls(t *testing.T) {
	banned := map[string]string{
		"http.MethodPut":    "this CLI never sends PUT",
		"http.MethodPatch":  "this CLI never sends PATCH",
		"http.MethodDelete": "this CLI never sends DELETE",
		"http.Post":         "POST goes through the guarded do() path, never the package shortcut",
		"http.PostForm":     "POST goes through the guarded do() path, never the package shortcut",
		"ioutil.WriteFile":  "use os.WriteFile in session.go",
	}
	for name, f := range parsePackage(t) {
		ast.Inspect(f, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			id, ok := sel.X.(*ast.Ident)
			if !ok {
				return true
			}
			full := id.Name + "." + sel.Sel.Name
			if why, bad := banned[full]; bad {
				t.Errorf("%s uses %s — %s", name, full, why)
			}
			return true
		})
	}
}

// TestOnlySessionWritesFiles: the binary's only writes are the session file (and
// later the snapshot output). Anything else writing to disk is a bug or worse.
func TestOnlySessionWritesFiles(t *testing.T) {
	writers := map[string]bool{"os.WriteFile": true, "os.Create": true, "os.MkdirAll": true,
		"os.Remove": true, "os.RemoveAll": true, "os.Truncate": true, "os.Rename": true}
	allowed := map[string]bool{"session.go": true, "snapshot.go": true, "captcha.go": true}
	for name, f := range parsePackage(t) {
		if allowed[name] {
			continue
		}
		ast.Inspect(f, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			id, ok := sel.X.(*ast.Ident)
			if !ok {
				return true
			}
			if full := id.Name + "." + sel.Sel.Name; writers[full] {
				t.Errorf("%s calls %s — only session.go (and later snapshot.go) may write to disk", name, full)
			}
			return true
		})
	}
}

// TestEveryPortalPathLiteralIsAllowlisted — inverted per CRITIQUE §5a: ANY
// path-shaped string literal must be a table path or an explicitly-listed
// exception. The old form (`^/(services|returns|payment|master)/`) silently
// missed /gstr2b/, /services2/ and /imsweb/, which is exactly how a fourth host
// gets wired in without review.
func TestEveryPortalPathLiteralIsAllowlisted(t *testing.T) {
	tablePaths := map[string]bool{}
	for _, e := range endpoints {
		tablePaths[e.Path] = true
	}
	// The exception list is deliberately tiny, and every entry is a path we
	// RECOGNISE but never REQUEST.
	exceptions := map[string]bool{
		"/services/error/accessdenied": true, // the WAF bounce we detect in CheckRedirect
		"/":                            true, // cookie path
	}
	// guard.go legitimately names path fragments — but only the ones on its own
	// blocklist. It gets no other exemption.
	for _, b := range blockedSubstrings {
		if strings.HasPrefix(b, "/") {
			exceptions[b] = true
		}
	}
	for name, f := range parsePackage(t) {
		ast.Inspect(f, func(n ast.Node) bool {
			lit, ok := n.(*ast.BasicLit)
			if !ok || lit.Kind != token.STRING {
				return true
			}
			v, err := strconv.Unquote(lit.Value)
			if err != nil || !strings.HasPrefix(v, "/") {
				return true
			}
			if len(v) < 2 || !isPathish(v) {
				return true
			}
			if tablePaths[v] || exceptions[v] {
				return true
			}
			t.Errorf("%s contains the path literal %q, which is neither an allowlisted endpoint nor a listed exception", name, v)
			return true
		})
	}
}

// isPathish reports whether a "/..."-literal looks like a URL path rather than a
// format string or a lone separator.
func isPathish(v string) bool {
	for _, r := range v[1:] {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9',
			r == '/', r == '-', r == '_', r == '.', r == '{', r == '}':
		default:
			return false
		}
	}
	return true
}

// TestNoCredentialEverFormatted: nothing may put a Registration's Pass into a
// string except masked(). A grep-level check, but it is the check that would
// have caught the leak in the capture fixtures.
func TestNoCredentialEverFormatted(t *testing.T) {
	for name, f := range parsePackage(t) {
		ast.Inspect(f, func(n ast.Node) bool {
			sel, ok := n.(*ast.SelectorExpr)
			if !ok || (sel.Sel.Name != "Pass" && sel.Sel.Name != "Password") {
				return true
			}
			// r.Pass is legal only as masked(r.Pass) or as a body value in login.
			if name != "config.go" && name != "login.go" && name != "client.go" && name != "cmd_auth.go" && name != "doctor.go" {
				t.Errorf("%s reads a credential field; keep credentials in config.go/login.go", name)
			}
			return true
		})
	}
}
