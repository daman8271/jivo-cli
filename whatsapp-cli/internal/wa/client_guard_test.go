package wa

import (
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestNothingSends walks every .go file in the module and fails if any of them
// calls a whatsmeow verb that would put something on the wire — except the one
// audited file, internal/wa/send.go.
//
// This is the whole safety story of jwa in one test. The number is linked to a
// live WhatsApp account; a stray SendMessage in a future edit would message a
// vendor from Karanpreet's number. Belt and braces: the list also lives in
// Forbidden in client.go, and this test reads it from there.
func TestNothingSends(t *testing.T) {
	root := ".."
	if wd, err := os.Getwd(); err == nil {
		root = filepath.Join(wd, "..", "..")
	}

	sawSendFile := false
	fset := token.NewFileSet()
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(path, ".go") {
			return err
		}
		if strings.HasSuffix(path, "_test.go") {
			return nil
		}
		// Since 2026-09-02 exactly one file may send: internal/wa/send.go,
		// reached only through the daemon's loopback API. Everything else
		// in the module is still held to "never".
		if strings.HasSuffix(filepath.ToSlash(path), "/internal/wa/send.go") {
			sawSendFile = true
			return nil
		}
		f, perr := parser.ParseFile(fset, path, nil, 0)
		if perr != nil {
			return nil // not ours to compile; the build will complain
		}
		ast.Inspect(f, func(n ast.Node) bool {
			call, ok := n.(*ast.CallExpr)
			if !ok {
				return true
			}
			sel, ok := call.Fun.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			for _, bad := range Forbidden {
				if sel.Sel.Name == bad {
					t.Errorf("%s calls %s — jwa must never send anything",
						fset.Position(call.Pos()), bad)
				}
			}
			return true
		})
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if !sawSendFile {
		t.Fatal("internal/wa/send.go not found — the one allowed sending file moved; fix the allowlist above")
	}
}
