package mcp

import (
	"os"
	"regexp"
	"strings"
	"testing"

	"go/ast"
	"go/parser"
	"go/token"
)

// The MCP surface for a JIVO system is read-only forever. The CLI may write
// when an operator explicitly asks; the MCP may not, because an agent-trusted
// surface has no operator in the loop to ask.
//
// There are TWO execution paths that reach the HTTP client:
//
//	tools.go      the direct endpoint-tool handler
//	code_orch.go  the code-orchestration executor (the Cloudflare pattern the
//	              press applies above 50 endpoints; this CLI is well above it)
//
// On OMS this is not currently exploitable: both paths take the method from the
// generated endpoint catalog, and every catalogued endpoint is a GET. That is
// precisely the reason to assert it structurally rather than rely on it. The
// only thing between the restored write machinery and a live write into JIVO's
// order and invoice systems is one future spec edit that nobody reviews as a
// security change. OMS carries POST /api/service-layer/invoice/, which submits
// a document into SAP Business One.
//
// Guarding only the first leaves the second as a complete write bypass. A
// fresh `cli-printing-press generate` restores the generic POST/PUT/PATCH/
// DELETE machinery in BOTH, so these tests exist to fail loudly the next time
// somebody reprints and forgets patch 0005.
//
// These are structural (AST/source) assertions rather than behavioural calls
// because the two handlers are closures built inside registration functions
// with no exported seam. A structural test that pins the absence of a client
// write call is strictly stronger than a behavioural test that only proves one
// path refuses one method.

var writeClientCalls = regexp.MustCompile(
	`\bc\.(Post|Put|Patch|Delete)[A-Za-z]*\(`)

func sourceOf(t *testing.T, file string) string {
	t.Helper()
	b, err := readFile(file)
	if err != nil {
		t.Fatalf("read %s: %v", file, err)
	}
	return b
}

// TestMCPExecutionPathsMakeNoWriteClientCall proves neither execution path can
// reach a mutating client method at all. This is the load-bearing assertion:
// it does not depend on the current spec being GET-only.
func TestMCPExecutionPathsMakeNoWriteClientCall(t *testing.T) {
	for _, file := range []string{"tools.go", "code_orch.go"} {
		src := sourceOf(t, file)
		// strip comments so a mention in prose does not trip the check
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
				"never expose a write (patch 0005). A fresh printing-press "+
				"generate restores this machinery; re-apply the GET-only guard.",
				file, m)
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

// TestSpecIsGETOnly is the weaker, spec-level check: every published endpoint
// is a GET today. It is NOT sufficient on its own — that is exactly why the
// two tests above assert on the code instead — but a failure here means the
// spec itself grew a write and needs a human decision.
func TestSpecIsGETOnly(t *testing.T) {
	src, err := readFile("../../oms-spec.yaml")
	if err != nil {
		t.Skipf("spec.yaml not readable from the test working directory: %v", err)
	}
	for _, verb := range []string{"POST", "PUT", "PATCH", "DELETE"} {
		if strings.Contains(src, "method: "+verb) {
			t.Errorf("spec.yaml declares a %s endpoint; this CLI is read-only "+
				"(RULE 0) and its MCP surface must never expose a write", verb)
		}
	}
	if n := strings.Count(src, "method: GET"); n == 0 {
		t.Error("spec.yaml declares no GET endpoints at all — wrong file?")
	}
}

func readFile(p string) (string, error) {
	b, err := os.ReadFile(p)
	return string(b), err
}
