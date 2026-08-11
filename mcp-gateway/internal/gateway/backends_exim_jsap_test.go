package gateway

import (
	"net/http"
	"strings"
	"testing"
	"time"
)

// --- the compiled-in backend table --------------------------------------------
//
// exim and jsap joined sapb1/postsql/ecom/oms/factory/hana on 2026-08-10. The
// tests here lock down the three things that go wrong silently when a backend is
// added: a stale count in the strings clients read (covered in
// corrections_hardening_test.go), a colliding prefix, and — the dangerous one —
// a StripPrefix that only SOME of a backend's tools carry.

// realToolNames is every tool each backend actually registers, transcribed from
// the backends' own source (not from a doc):
//
//   - sapb1:   sap-b1/cli internal/mcp tool registrations
//   - postsql: postsql's MCP handler
//   - ecom/oms/factory: <api>_search + <api>_execute plus the bare
//     search/sql/context tools and the Cobra-tree mirror
//   - hana:    hana-sql/internal/mcp
//   - exim:    exim/cli/exim-pp-cli/internal/mcp/{tools.go,code_orch.go} + cobratree
//   - jsap:    jsap-mcp/internal/mcp/tools.go
//
// Only the backends whose StripPrefix decision this change is responsible for
// are listed exhaustively; the older ones are here as the control group that
// proves the rule below is the rule the existing config already follows.
var realToolNames = map[string][]string{
	"sapb1": {
		"sapb1_doctor", "sapb1_entities", "sapb1_fields", "sapb1_invoices",
		"sapb1_items", "sapb1_ops", "sapb1_orders", "sapb1_partners", "sapb1_query",
	},
	"postsql": {
		"postgres_query", "list_databases", "list_tables", "describe_table",
		"search", "schema_dump",
	},
	"hana": {
		"hana_query", "hana_tables", "hana_columns", "hana_doctor",
		"hana_sales_by_variety", "hana_turnover", "hana_payments",
	},
	"exim": {
		"analytics", "context", "exim_execute", "exim_search", "search", "sql",
		"sync", "tail", "workflow", "workflow_archive", "workflow_status",
	},
	"jsap": {
		"jsap_context", "jsap_search", "jsap_execute", "jsap_budget_approvals",
		"jsap_tickets", "jsap_tasks", "jsap_hierarchy", "jsap_dochub",
		"jsap_inventory_audit", "jsap_admin",
	},
}

// The compiled table is the deployment contract: the service name in the URL is
// what docker-compose must call the container, and the port is what that
// container must bind. Both are asserted literally, because a typo in either is
// a backend that is simply never reachable and shows only as "DOWN" in a health
// check nobody reads.
func TestDefaultBackendsTable(t *testing.T) {
	want := []BackendConf{
		{Name: "sapb1", Prefix: "sap_", StripPrefix: "sapb1_", URL: "http://sapb1:7701/mcp"},
		{Name: "postsql", Prefix: "pg_", URL: "http://postsql:7702/mcp"},
		{Name: "ecom", Prefix: "ecom_", URL: "http://ecom:7703/mcp"},
		{Name: "oms", Prefix: "oms_", URL: "http://oms:7704/mcp"},
		{Name: "factory", Prefix: "fct_", URL: "http://factory:7705/mcp"},
		{Name: "hana", Prefix: "hana_", StripPrefix: "hana_", URL: "http://hana:7706/mcp"},
		{Name: "exim", Prefix: "exim_", URL: "http://exim:7707/mcp"},
		{Name: "jsap", Prefix: "jsap_", StripPrefix: "jsap_", URL: "http://jsap:7711/mcp"},
	}
	got := DefaultBackends()
	if len(got) != len(want) {
		t.Fatalf("DefaultBackends returns %d backends, want %d: %+v", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("backend #%d = %+v, want %+v", i, got[i], want[i])
		}
	}
}

// Names, prefixes and URLs must all be unique, and no prefix may be a prefix of
// another. resolve() scans the table in order and takes the first prefix that
// matches, so a shadowed backend would be unreachable for every tool whose name
// happens to start with the shadowing one — a routing bug with no error message.
func TestBackendPrefixesDoNotShadowEachOther(t *testing.T) {
	backends := DefaultBackends()
	seenName := map[string]bool{}
	seenPrefix := map[string]bool{}
	seenURL := map[string]bool{}
	for _, b := range backends {
		if b.Prefix == "" || !strings.HasSuffix(b.Prefix, "_") {
			t.Fatalf("backend %s has prefix %q; it must be non-empty and end in _", b.Name, b.Prefix)
		}
		if seenName[b.Name] {
			t.Fatalf("duplicate backend name %q", b.Name)
		}
		if seenPrefix[b.Prefix] {
			t.Fatalf("duplicate backend prefix %q (%s)", b.Prefix, b.Name)
		}
		if seenURL[b.URL] {
			t.Fatalf("duplicate backend URL %q (%s) — two services cannot share one port", b.URL, b.Name)
		}
		seenName[b.Name], seenPrefix[b.Prefix], seenURL[b.URL] = true, true, true
	}
	for i, a := range backends {
		for j, b := range backends {
			if i == j {
				continue
			}
			if strings.HasPrefix(b.Prefix, a.Prefix) {
				t.Fatalf("%s's prefix %q shadows %s's %q: resolve() takes the first match in order",
					a.Name, a.Prefix, b.Name, b.Prefix)
			}
		}
	}
}

// THE rule: StripPrefix is legal only when EVERY tool of the backend carries it.
//
// Why a partial StripPrefix is corruption rather than cosmetics — the two halves
// of the rename are not symmetric:
//
//	advertise: prefix + strings.TrimPrefix(name, strip)   (no-op if absent)
//	route:     strip + name-without-prefix                (added unconditionally)
//
// So with exim wrongly configured StripPrefix "exim_", the backend's own
// "search" would be advertised as "exim_search" — the same name its "exim_search"
// gets, so one of the two is silently dropped as a duplicate — and a call to
// "exim_search" would be forwarded upstream as "exim_search", i.e. the OTHER
// tool. Nine of exim's eleven tools would answer as something else, with no
// error anywhere. Hence: every tool, or nothing.
func TestStripPrefixSetOnlyWhenEveryToolSharesIt(t *testing.T) {
	for _, b := range DefaultBackends() {
		tools, known := realToolNames[b.Name]
		if !known {
			continue // ecom/oms/factory: covered by the older tests and unchanged here
		}
		shared := sharedUnderscorePrefix(tools)
		if b.StripPrefix != shared {
			t.Fatalf("backend %s: StripPrefix = %q, but the prefix ALL %d of its real tools share is %q; "+
				"stripping a prefix only some tools carry mis-routes the rest, and stripping none "+
				"when they all carry one produces a %s stutter",
				b.Name, b.StripPrefix, len(tools), shared, b.Prefix+b.Prefix)
		}
	}
}

// sharedUnderscorePrefix returns the longest "word_" prefix that every name
// carries, or "" when they do not all share one. Trailing partial words are
// trimmed back to the last underscore, so a coincidental character overlap
// (jsap_t{ickets,asks} -> "jsap_t") can never be mistaken for a real prefix.
func sharedUnderscorePrefix(names []string) string {
	if len(names) < 2 {
		return ""
	}
	common := names[0]
	for _, n := range names[1:] {
		i := 0
		for i < len(common) && i < len(n) && common[i] == n[i] {
			i++
		}
		common = common[:i]
	}
	cut := strings.LastIndexByte(common, '_')
	if cut < 0 {
		return ""
	}
	prefix := common[:cut+1]
	// A tool whose whole name IS the prefix could not survive the round trip
	// (renameTool rejects it), so that is never a strippable prefix.
	for _, n := range names {
		if n == prefix {
			return ""
		}
	}
	return prefix
}

// End to end through the real gateway with exim's and jsap's REAL tool names:
// what the client is advertised, and what the backend is actually asked for.
func TestEximAndJSAPRoundTripRealToolNames(t *testing.T) {
	exim := newFakeBackend(t, fakeOpts{name: "exim", stateful: true, tools: realToolNames["exim"]})
	jsap := newFakeBackend(t, fakeOpts{name: "jsap", stateful: true, tools: realToolNames["jsap"]})

	cfg := DefaultConfig()
	cfg.ToolsTTL = time.Hour
	cfg.ListTimeout = 5 * time.Second
	cfg.CallTimeout = 5 * time.Second
	cfg.Backends = []BackendConf{
		{Name: "exim", Prefix: "exim_", URL: exim.url()},
		{Name: "jsap", Prefix: "jsap_", StripPrefix: "jsap_", URL: jsap.url()},
	}
	h := New(cfg, "0.1.0-test").Handler()

	rec := postMCP(t, h, `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body: %s", rec.Code, rec.Body.String())
	}
	got := toolNames(t, rec)
	want := []string{
		// exim strips nothing: the nine bare tools gain exim_, and the two that
		// already carry it stutter — exactly as oms_oms_search does in production.
		"exim_analytics", "exim_context", "exim_exim_execute", "exim_exim_search",
		"exim_search", "exim_sql", "exim_sync", "exim_tail",
		"exim_workflow", "exim_workflow_archive", "exim_workflow_status",
		// jsap's rename is the identity, like hana's: no jsap_jsap_ stutter.
		"jsap_context", "jsap_search", "jsap_execute", "jsap_budget_approvals",
		"jsap_tickets", "jsap_tasks", "jsap_hierarchy", "jsap_dochub",
		"jsap_inventory_audit", "jsap_admin",
		"gateway_status",
	}
	if strings.Join(got, ",") != strings.Join(want, ",") {
		t.Fatalf("tools =\n  %v\nwant\n  %v", got, want)
	}
	// No tool was lost to a name collision on the way through.
	if len(got) != len(realToolNames["exim"])+len(realToolNames["jsap"])+1 {
		t.Fatalf("advertised %d tools, want all %d backend tools plus gateway_status",
			len(got), len(realToolNames["exim"])+len(realToolNames["jsap"]))
	}

	// And every one of them reaches its backend under the backend's OWN name.
	cases := []struct {
		tool     string
		backend  *fakeBackend
		upstream string
	}{
		{"exim_search", exim, "search"},           // the bare tool
		{"exim_exim_search", exim, "exim_search"}, // the one that already carried exim_
		{"exim_workflow_status", exim, "workflow_status"},
		{"jsap_context", jsap, "jsap_context"}, // identity in both directions
		{"jsap_admin", jsap, "jsap_admin"},
		{"jsap_inventory_audit", jsap, "jsap_inventory_audit"},
	}
	for _, c := range cases {
		rec := postMCP(t, h, `{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"`+c.tool+`","arguments":{}}}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("%s status = %d; body: %s", c.tool, rec.Code, rec.Body.String())
		}
		text, isErr := toolResultOf(t, rec)
		if isErr {
			t.Fatalf("%s isError = true: %s", c.tool, text)
		}
		if want := c.backend.opts.name + ":" + c.upstream; text != want {
			t.Fatalf("%s reached the backend as %q, want %q", c.tool, text, want)
		}
	}
	if strings.Contains(strings.Join(got, ","), "jsap_jsap_") {
		t.Fatalf("jsap tools stutter: %v", got)
	}
}

// Each new backend's URL is overridable by its own environment variable, using
// the same JIVO_GW_URL_<NAME> convention as the original six.
func TestConfigFromEnvOverridesNewBackends(t *testing.T) {
	env := map[string]string{
		"JIVO_GW_URL_EXIM": "http://127.0.0.1:7707/mcp",
		"JIVO_GW_URL_JSAP": "http://jsap.internal:9/mcp",
	}
	cfg := ConfigFromEnv(func(k string) string { return env[k] })
	got := map[string]string{}
	for _, b := range cfg.Backends {
		got[b.Name] = b.URL
	}
	if got["exim"] != "http://127.0.0.1:7707/mcp" {
		t.Fatalf("exim URL = %q, want the env override", got["exim"])
	}
	if got["jsap"] != "http://jsap.internal:9/mcp" {
		t.Fatalf("jsap URL = %q, want the env override", got["jsap"])
	}
	if got["hana"] != "http://hana:7706/mcp" {
		t.Fatalf("hana URL = %q, want the compiled default (unset env must not disturb it)", got["hana"])
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("Validate = %v, want nil", err)
	}
}
