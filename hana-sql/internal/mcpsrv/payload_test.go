package mcpsrv

import (
	"encoding/json"
	"os"
	"strings"
	"testing"
)

// --- the tools/list payload, asserted rather than asserted-about ----------------
//
// facts.go used to carry the sentence "The other tools stay short so tools/list
// is cheap behind the gateway". It was true when there were four tools; there are
// now seven, and nothing measured it. A comment that claims a property nothing
// checks is how a payload doubles without anyone noticing — so the claim is a
// test now, and the comment points here.
//
// The cap is deliberately loose (not a golden number): it exists to catch a
// doubling, not to make every description edit a test failure. The per-tool
// budgets in TestDescriptionsCarryFacts are the fine-grained control.
const toolsListByteCap = 22 << 10

func TestToolsListPayloadStaysBounded(t *testing.T) {
	s := &Server{}
	defs := s.ToolDefs()
	if len(defs) == 0 {
		t.Fatal("no tool definitions; the assertion is vacuous")
	}

	body, err := json.Marshal(map[string]any{"tools": defs})
	if err != nil {
		t.Fatalf("marshal tools/list: %v", err)
	}
	t.Logf("tools/list is %d bytes across %d tools", len(body), len(defs))
	if len(body) > toolsListByteCap {
		t.Errorf("tools/list is %d bytes across %d tools, over the %d-byte cap. Every byte here is paid on EVERY session behind the gateway. Take it from prose, never from a measured fact — and if a fact genuinely needs the room, raise the cap in one commit that says what was measured.",
			len(body), len(defs), toolsListByteCap)
	}

	// A single tool must not quietly become most of the payload.
	for _, d := range defs {
		one, err := json.Marshal(d)
		if err != nil {
			t.Fatalf("marshal tool def: %v", err)
		}
		if len(one) > len(body)/2 {
			t.Errorf("tool %q is %d of the %d payload bytes", d["name"], len(one), len(body))
		}
	}
}

func readDoc(t *testing.T, path string) string {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v — the shipped docs are part of what this server advertises", path, err)
	}
	return string(b)
}

// The docs must not go on describing a tool set that no longer exists. MCP.md
// said "the identical four tools" and headed a section "## The four tools" while
// seven were shipping, and README.md described injection safety in terms of the
// old set only.
func TestDocsDoNotAdvertiseAStaleToolCount(t *testing.T) {
	defs := (&Server{}).ToolDefs()
	n := len(defs)
	if n == 4 {
		t.Skip("back to four tools; the stale-count assertions do not apply")
	}
	for _, doc := range []string{"../../MCP.md", "../../README.md"} {
		body := readDoc(t, doc)
		for _, stale := range []string{"the four tools", "The four tools", "identical four tools", "four tools"} {
			if strings.Contains(body, stale) {
				t.Errorf("%s still says %q while %d tools ship", doc, stale, n)
			}
		}
		// And every shipped tool must at least be named in MCP.md.
		if strings.HasSuffix(doc, "MCP.md") {
			for _, d := range defs {
				name, _ := d["name"].(string)
				if name == "" {
					t.Fatal("a tool definition has no name")
				}
				if !strings.Contains(body, name) {
					t.Errorf("%s never mentions the %s tool", doc, name)
				}
			}
		}
	}
}
