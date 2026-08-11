// Command jivo-gateway serves one strictly read-only MCP endpoint that fronts
// JIVO's eight MCP backends (SAP B1, Postgres, ecom, oms, factory, HANA, EXIM,
// JSAP), merging their tools under the prefixes sap_ / pg_ / ecom_ / oms_ /
// fct_ / hana_ / exim_ / jsap_ and adding a native gateway_status tool.
//
// Front side: stateless streamable HTTP at /mcp (POST one JSON-RPC message, get
// one JSON response). Back side: one lazily-initialized session per backend.
// Nothing in this binary can create, update or delete anything.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"

	"mcp-gateway/internal/gateway"
)

// version is the gateway's version, overridable at build time via
// -ldflags "-X main.version=...", matching the other JIVO MCP binaries.
var version = "0.0.0-dev"

func main() {
	// Precedence: flag > environment (JIVO_GW_*) > compiled default.
	cfg := gateway.ConfigFromEnv(os.Getenv)

	addr := flag.String("addr", cfg.Addr, "front-side listen address (host:port or :port)")
	ttl := flag.Duration("ttl", cfg.ToolsTTL, "how long a merged tools/list snapshot stays fresh")
	listTimeout := flag.Duration("list-timeout", cfg.ListTimeout, "per-backend timeout for one tools/list refresh")
	callTimeout := flag.Duration("call-timeout", cfg.CallTimeout, "timeout for one forwarded tools/call")
	corrections := flag.String("corrections", cfg.CorrectionsPath, "path to the JIVO corrections digest (harness/corrections/INDEX.md); the embedded snapshot is the fallback")
	allowOrigin := newListFlag("allow-origin", cfg.AllowedOrigins, "browser Origin to accept (repeatable; default: none — a real MCP client sends no Origin)")
	allowHost := newListFlag("allow-host", cfg.AllowedHosts, "Host header value to accept (repeatable; default: any, because this gateway is proxied under a public name)")
	showVersion := flag.Bool("version", false, "print version and exit")

	urls := make([]*string, len(cfg.Backends))
	for i, b := range cfg.Backends {
		urls[i] = flag.String("url-"+b.Name, b.URL, "MCP endpoint URL of the "+b.Name+" backend")
	}

	flag.Usage = usage
	flag.Parse()

	if *showVersion {
		fmt.Println("jivo-gateway", version)
		return
	}
	if flag.NArg() > 0 {
		fmt.Fprintf(os.Stderr, "jivo-gateway takes no positional arguments (got %q)\n", flag.Arg(0))
		os.Exit(2)
	}

	cfg.Addr = *addr
	cfg.ToolsTTL = *ttl
	cfg.ListTimeout = *listTimeout
	cfg.CallTimeout = *callTimeout
	cfg.CorrectionsPath = *corrections
	cfg.AllowedOrigins = allowOrigin.values
	cfg.AllowedHosts = allowHost.values
	for i := range cfg.Backends {
		cfg.Backends[i].URL = *urls[i]
	}

	// A zero or negative duration would make every backend request fail
	// instantly and every backend look down: refuse to start instead.
	if err := cfg.Validate(); err != nil {
		fmt.Fprintf(os.Stderr, "jivo-gateway: %v\n", err)
		os.Exit(2)
	}

	g := gateway.New(cfg, version)

	// Warm the tool cache so the first client sees a full list. Backends that
	// are still booting are non-fatal: they are marked down, reported by
	// gateway_status, and picked up by the next lazy refresh. The warmup is
	// bounded by the per-backend --list-timeout, not by this context.
	for _, st := range g.Warmup(context.Background()) {
		state := "DOWN"
		detail := " (" + st.LastError + ")"
		if st.Up {
			state, detail = "up", ""
		}
		// st.URL is the display form: a password in a backend URL is masked.
		fmt.Fprintf(os.Stderr, "jivo-gateway: backend %-8s %-24s %-4s %3d tools%s\n",
			st.Name, st.URL, state, st.ToolCount, detail)
	}

	// Which rule set clients will be handed on initialize, and from where. Only
	// the provenance is printed, never the digest's contents.
	logCorrections(g.CorrectionsStatus())

	fmt.Fprintf(os.Stderr, "jivo-gateway %s: read-only MCP gateway listening on http://%s/mcp\n", version, cfg.Addr)
	if err := g.ListenAndServe(); err != nil {
		fmt.Fprintf(os.Stderr, "jivo-gateway: %v\n", err)
		os.Exit(1)
	}
}

// listFlag is a repeatable string flag, seeded from the environment. The first
// -flag occurrence REPLACES the environment's list rather than appending to it,
// so a flag always wins outright — the same precedence as every other setting.
type listFlag struct {
	values  []string
	fromEnv bool
}

func newListFlag(name string, seed []string, usage string) *listFlag {
	f := &listFlag{values: seed, fromEnv: len(seed) > 0}
	flag.Var(f, name, usage)
	return f
}

func (f *listFlag) String() string {
	if f == nil {
		return ""
	}
	return strings.Join(f.values, ",")
}

func (f *listFlag) Set(v string) error {
	if f.fromEnv {
		f.values, f.fromEnv = nil, false
	}
	for _, part := range strings.Split(v, ",") {
		if p := strings.TrimSpace(part); p != "" {
			f.values = append(f.values, p)
		}
	}
	return nil
}

// logCorrections prints one line of provenance for the corrections digest:
// how many rules, from which file — or that the embedded snapshot is standing
// in, and why. A gateway serving stale or fallback rules looks healthy in every
// other respect, so this is the one place a boot makes it obvious.
func logCorrections(st map[string]any) {
	origin := "embedded snapshot"
	if src, _ := st["source"].(string); src == "file" {
		origin = fmt.Sprintf("file %v", st["path"])
	}
	if lastErr, _ := st["last_error"].(string); lastErr != "" {
		origin += ", last re-read failed: " + lastErr
	}
	fmt.Fprintf(os.Stderr, "jivo-gateway: corrections %v rules (%s)\n", st["count"], origin)
}

func usage() {
	fmt.Fprint(os.Stderr, `jivo-gateway — one read-only MCP endpoint in front of eight JIVO backends

Backends and the prefix each contributes:
  sapb1    sap_   SAP B1 Service Layer
  postsql  pg_    Postgres
  ecom     ecom_  e-commerce
  oms      oms_   orders
  factory  fct_   factory
  hana     hana_  SAP B1's HANA database direct (hana_sales_by_variety,
                  hana_turnover and hana_payments compute JIVO's settled
                  definitions; prefer them to hand-written SQL)
  exim     exim_  imports/exports (licences, shipments, tanks, stock status)
  jsap     jsap_  JSAP ops platform (budget approvals, tickets, tasks,
                  org hierarchy, Document Hub, inventory audits)

Usage:
  jivo-gateway [flags]

Environment (flags win):
  JIVO_GW_ADDR         front-side listen address
  JIVO_GW_TTL          tools/list cache TTL (Go duration)
  JIVO_GW_CORRECTIONS  path to the JIVO corrections digest served on initialize
  JIVO_GW_ALLOW_ORIGIN comma-separated browser Origins to accept (default: none)
  JIVO_GW_ALLOW_HOST   comma-separated Host values to accept (default: any)
  JIVO_GW_URL_<NAME>   backend URL: SAPB1, POSTSQL, ECOM, OMS, FACTORY, HANA,
                       EXIM, JSAP

Flags:
`)
	flag.PrintDefaults()
}
