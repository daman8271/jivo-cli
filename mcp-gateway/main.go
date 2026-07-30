// Command jivo-gateway serves one strictly read-only MCP endpoint that fronts
// JIVO's five MCP backends (SAP B1, Postgres, ecom, oms, factory), merging their
// tools under the prefixes sap_ / pg_ / ecom_ / oms_ / fct_ and adding a native
// gateway_status tool.
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

	fmt.Fprintf(os.Stderr, "jivo-gateway %s: read-only MCP gateway listening on http://%s/mcp\n", version, cfg.Addr)
	if err := g.ListenAndServe(); err != nil {
		fmt.Fprintf(os.Stderr, "jivo-gateway: %v\n", err)
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprint(os.Stderr, `jivo-gateway — one read-only MCP endpoint in front of five JIVO backends

Usage:
  jivo-gateway [flags]

Environment (flags win):
  JIVO_GW_ADDR         front-side listen address
  JIVO_GW_TTL          tools/list cache TTL (Go duration)
  JIVO_GW_URL_<NAME>   backend URL: SAPB1, POSTSQL, ECOM, OMS, FACTORY

Flags:
`)
	flag.PrintDefaults()
}
