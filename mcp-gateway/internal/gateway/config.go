// Package gateway is a unified, strictly read-only MCP gateway in front of
// JIVO's eight MCP backends (SAP B1, Postgres, ecom, oms, factory, HANA, EXIM,
// JSAP).
//
// The front side speaks the stateless "streamable HTTP" transport that postsql
// serves: one JSON-RPC message per POST, one JSON response back, no sessions.
// The back side speaks whatever the backend needs — mcp-go v0.47.0 hands out an
// Mcp-Session-Id on initialize and 404s requests that carry a stale one, so the
// gateway keeps one lazily-initialized session per backend and re-inits once on
// expiry. Stateless backends never issue that header, so nothing special is
// configured per backend: the protocol self-discriminates.
//
// READ ONLY, structurally: the only methods this package can ever emit toward a
// backend are initialize, notifications/initialized, tools/list and tools/call.
// There is no code path that writes anything anywhere.
package gateway

import (
	"fmt"
	"net/url"
	"strings"
	"time"
)

// Compiled-in defaults. The URLs are the docker-compose service names of the
// eight backends; nothing here is a credential.
const (
	defaultAddr        = "127.0.0.1:7700"
	defaultToolsTTL    = 5 * time.Minute
	defaultListTimeout = 10 * time.Second
	defaultCallTimeout = 120 * time.Second
)

// BackendConf describes one upstream MCP server.
//
// Prefix includes its trailing underscore, so a prefixed tool name is exactly
// Prefix + the backend's own tool name.
//
// StripPrefix is a redundant prefix that every tool of that backend already
// carries and that is removed before Prefix is added, so sapb1's sapb1_query
// is advertised as sap_query and not as sap_sapb1_query. It is the exact
// inverse on the way back: routing strips Prefix and re-adds StripPrefix, so
// the backend always receives its own original tool name. Empty means "the
// backend's names are used as they are".
type BackendConf struct {
	Name        string
	Prefix      string
	StripPrefix string
	URL         string
}

// Config is the whole runtime configuration. Nothing here is a compiled-in
// credential: every backend is reached over the private compose network with no
// auth. (If an operator does put userinfo in a backend URL it is honoured as
// basic auth and never stored, logged or reported in clear — see splitURL.)
type Config struct {
	Addr        string        // front-side listen address
	ToolsTTL    time.Duration // how long a merged tools/list snapshot stays fresh
	ListTimeout time.Duration // per-backend budget for one tools/list refresh
	CallTimeout time.Duration // budget for one forwarded tools/call
	Backends    []BackendConf // merge order; also the tools/list order

	// CorrectionsPath is the JIVO corrections digest handed to clients on
	// initialize (harness/corrections/INDEX.md). Empty — the compiled default —
	// means the embedded snapshot only, which is a working rule set, not a
	// failure. It is deliberately absent from Validate(): a mount can appear
	// late, and a gateway that refuses to boot because a rules file is not
	// there yet trades a degraded read-only service for no service at all.
	// gateway_status is where a missing or stale digest is reported.
	CorrectionsPath string

	// AllowedOrigins are the browser Origins the front side accepts. Empty —
	// the default — means NO browser origin is accepted, which is the safe
	// default and costs nothing: a CLI, an MCP client and the Claude connector
	// all send no Origin header at all. See http.go for what this defends.
	AllowedOrigins []string

	// AllowedHosts are the Host header values the front side accepts, for a
	// gateway bound to loopback. Empty — the default — accepts any Host,
	// because unlike hana-sql this gateway is DELIBERATELY reachable by a public
	// name through a reverse proxy, and the proxy is free to pass any Host it
	// likes; a loopback-only allowlist would 403 the entire deployment. Set it
	// (--allow-host) on a loopback-bound gateway to get the anti-DNS-rebinding
	// check hana-sql has by default.
	AllowedHosts []string
}

// DefaultBackends returns the eight compiled-in backends in merge order.
//
// StripPrefix is set only where EVERY single tool of that backend shares one
// redundant prefix, verified against the backends' real tool registrations:
//
//   - sapb1 registers sapb1_doctor / _entities / _fields / _invoices / _items /
//     _ops / _orders / _partners / _query — all nine share "sapb1_", so it is
//     stripped.
//   - postsql registers postgres_query, list_databases, list_tables,
//     describe_table, search, schema_dump — no shared prefix.
//   - ecom, oms, factory and exim register <api>_search + <api>_execute
//     alongside the un-prefixed search / sql / context tools and the Cobra-tree
//     mirror, so they have no shared prefix either.
//
// Stripping anything else would corrupt names — and worse than corrupt them.
// renameTool strips with strings.TrimPrefix (a no-op on a tool that does not
// carry it) while resolve re-adds StripPrefix unconditionally, so a StripPrefix
// that only SOME tools share is asymmetric: the un-prefixed tools keep their
// advertised name but every call to one is forwarded upstream under a different
// tool's name. That is silent mis-routing, not a cosmetic wart, which is why the
// rule here is "every tool or nothing".
func DefaultBackends() []BackendConf {
	return []BackendConf{
		{Name: "sapb1", Prefix: "sap_", StripPrefix: "sapb1_", URL: "http://sapb1:7701/mcp"},
		{Name: "postsql", Prefix: "pg_", URL: "http://postsql:7702/mcp"},
		{Name: "ecom", Prefix: "ecom_", URL: "http://ecom:7703/mcp"},
		{Name: "oms", Prefix: "oms_", URL: "http://oms:7704/mcp"},
		{Name: "factory", Prefix: "fct_", URL: "http://factory:7705/mcp"},
		// hana registers seven tools — hana_query / _tables / _columns / _doctor
		// plus the domain three, hana_sales_by_variety / _turnover / _payments —
		// and every one of them already starts with "hana_", so Prefix and
		// StripPrefix are the same string and the rename is the identity in both
		// directions: the tools read as hana_query standalone and behind the
		// gateway alike, with no hana_hana_ stutter.
		{Name: "hana", Prefix: "hana_", StripPrefix: "hana_", URL: "http://hana:7706/mcp"},
		// exim (imports/exports) registers eleven tools: analytics, context,
		// exim_execute, exim_search, search, sql, sync, tail, workflow,
		// workflow_archive and workflow_status. Only two of the eleven carry
		// "exim_", so NOTHING is stripped — the same shape as ecom/oms/factory,
		// and it produces the same familiar exim_exim_search / exim_exim_execute
		// stutter on exactly those two (compare oms_oms_search today). Setting
		// StripPrefix here would make exim_search and search collide on one
		// advertised name and forward the nine bare tools to the wrong upstream
		// name; the stutter is the cheap, correct outcome.
		{Name: "exim", Prefix: "exim_", URL: "http://exim:7707/mcp"},
		// jsap (JIVO's internal ops platform) registers ten tools — jsap_context,
		// jsap_search, jsap_execute, jsap_budget_approvals, jsap_tickets,
		// jsap_tasks, jsap_hierarchy, jsap_dochub, jsap_inventory_audit and
		// jsap_admin. All ten already start with "jsap_", so, like hana, Prefix
		// and StripPrefix are the same string and the rename is the identity in
		// both directions: no jsap_jsap_ stutter.
		{Name: "jsap", Prefix: "jsap_", StripPrefix: "jsap_", URL: "http://jsap:7711/mcp"},
	}
}

// DefaultConfig returns the compiled-in defaults, no environment consulted.
func DefaultConfig() Config {
	return Config{
		Addr:        defaultAddr,
		ToolsTTL:    defaultToolsTTL,
		ListTimeout: defaultListTimeout,
		CallTimeout: defaultCallTimeout,
		Backends:    DefaultBackends(),
	}
}

// ConfigFromEnv layers environment overrides on top of DefaultConfig:
//
//	JIVO_GW_ADDR          front-side listen address
//	JIVO_GW_TTL           tools/list cache TTL (any Go duration, e.g. "90s")
//	JIVO_GW_CORRECTIONS   path to the corrections digest served on initialize
//	JIVO_GW_ALLOW_ORIGIN  comma-separated browser Origins to accept (default: none)
//	JIVO_GW_ALLOW_HOST    comma-separated Host values to accept (default: any)
//	JIVO_GW_URL_<NAME>    URL of one backend (NAME upper-cased: SAPB1, POSTSQL,
//	                      ECOM, OMS, FACTORY, HANA, EXIM, JSAP)
//
// getenv is injected so this is testable without touching the real process
// environment. Unparseable values are ignored in favour of the default.
func ConfigFromEnv(getenv func(string) string) Config {
	cfg := DefaultConfig()
	if v := strings.TrimSpace(getenv("JIVO_GW_ADDR")); v != "" {
		cfg.Addr = v
	}
	if v := strings.TrimSpace(getenv("JIVO_GW_TTL")); v != "" {
		if d, err := time.ParseDuration(v); err == nil && d > 0 {
			cfg.ToolsTTL = d
		}
	}
	if v := strings.TrimSpace(getenv("JIVO_GW_CORRECTIONS")); v != "" {
		cfg.CorrectionsPath = v
	}
	if v := splitList(getenv("JIVO_GW_ALLOW_ORIGIN")); len(v) > 0 {
		cfg.AllowedOrigins = v
	}
	if v := splitList(getenv("JIVO_GW_ALLOW_HOST")); len(v) > 0 {
		cfg.AllowedHosts = v
	}
	for i := range cfg.Backends {
		if v := strings.TrimSpace(getenv(backendURLEnv(cfg.Backends[i].Name))); v != "" {
			cfg.Backends[i].URL = v
		}
	}
	return cfg
}

// splitList parses a comma-separated environment value into trimmed, non-empty
// entries. An empty or all-whitespace value yields nil, so it never turns into
// an allowlist containing "".
func splitList(v string) []string {
	var out []string
	for _, part := range strings.Split(v, ",") {
		if p := strings.TrimSpace(part); p != "" {
			out = append(out, p)
		}
	}
	return out
}

// backendURLEnv is the environment variable that overrides one backend's URL.
func backendURLEnv(name string) string {
	return "JIVO_GW_URL_" + strings.ToUpper(name)
}

// Validate rejects a configuration that would misbehave silently. A
// non-positive duration is the dangerous one: context.WithTimeout(ctx, 0) is
// already expired, so every backend request would fail instantly and every
// backend would be reported down — a typo that looks like an outage.
func (c Config) Validate() error {
	for _, d := range []struct {
		flag string
		val  time.Duration
	}{
		{"--ttl", c.ToolsTTL},
		{"--list-timeout", c.ListTimeout},
		{"--call-timeout", c.CallTimeout},
	} {
		if d.val <= 0 {
			return fmt.Errorf("%s must be positive, got %v", d.flag, d.val)
		}
	}
	if strings.TrimSpace(c.Addr) == "" {
		return fmt.Errorf("--addr must not be empty")
	}
	for _, b := range c.Backends {
		if strings.TrimSpace(b.URL) == "" {
			return fmt.Errorf("backend %s has no URL", b.Name)
		}
	}
	return nil
}

// splitURL separates a backend URL into the three things the gateway needs:
//
//   - request: the URL actually put on the wire, with any userinfo removed. The
//     point is that no error string can ever carry a password: net/http quotes
//     the request URL in every *url.Error it produces.
//   - display: the same URL with the password masked as "***", which is what
//     gateway_status reports and what the startup log prints. The username and
//     the host:port survive on purpose — this is a secret-path, read-only
//     service on a private network and topology is what makes it diagnosable.
//   - user/pass: the credentials, if any, sent as an HTTP basic-auth header
//     instead. None of the eight JIVO backends uses auth; this only keeps an
//     operator-supplied credential working while keeping it out of every log.
//
// A URL with no userinfo (the normal case) comes back unchanged.
func splitURL(raw string) (request, display, user, pass string) {
	u, err := url.Parse(raw)
	if err != nil {
		// Unparseable. It will fail at http.NewRequest anyway; the only job
		// here is to never display something that might be a secret.
		return raw, maskUserinfo(raw), "", ""
	}
	if u.User == nil {
		return raw, raw, "", ""
	}
	user = u.User.Username()
	pass, hasPass := u.User.Password()

	stripped := *u
	stripped.User = nil
	request = stripped.String()

	shown := user
	if hasPass {
		shown = user + ":***"
	}
	return request, spliceUserinfo(request, shown), user, pass
}

// spliceUserinfo puts an already-masked userinfo string back into a URL. It is
// textual on purpose: url.URL.String() percent-encodes the "*" of the mask.
func spliceUserinfo(raw, info string) string {
	if i := strings.Index(raw, "://"); i >= 0 {
		return raw[:i+3] + info + "@" + raw[i+3:]
	}
	return info + "@" + raw
}

// maskUserinfo replaces an authority's userinfo with "***" by string surgery,
// for URLs url.Parse could not handle. Display only.
func maskUserinfo(raw string) string {
	i := strings.Index(raw, "://")
	if i < 0 {
		return raw
	}
	authority := raw[i+3:]
	at := strings.Index(authority, "@")
	// Only an "@" inside the authority is userinfo; one in the path is not.
	if at < 0 || (strings.IndexByte(authority, '/') >= 0 && strings.IndexByte(authority, '/') < at) {
		return raw
	}
	return raw[:i+3] + "***@" + authority[at+1:]
}
