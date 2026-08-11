// Copyright 2026 daman8271 and contributors.
// jsap-mcp — a strictly read-only MCP server over JSAP, JIVO's internal ops
// platform.
//
// Transport selection order: --transport flag, then JSAP_MCP_TRANSPORT env,
// then stdio. The flag surface lets one binary serve stdio locally and
// streamable HTTP when hosted in the gateway's container, which is how the
// other five JIVO backends run.

package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"jsap-mcp/internal/jsap"
	mcptools "jsap-mcp/internal/mcp"

	"github.com/mark3labs/mcp-go/server"
)

// defaultHTTPAddr is the next free port in the gateway's block: sapb1 7701,
// postsql 7702, ecom 7703, oms 7704, factory 7705, hana 7706, jsap 7707.
const defaultHTTPAddr = ":7707"

// version is the served MCP server version, overridable at build time via ldflags.
var version = "0.1.0"

func main() {
	transport := flag.String("transport", defaultTransport(), "MCP transport: stdio | http")
	addr := flag.String("addr", defaultHTTPAddr, "bind address for http transport (host:port or :port)")
	flag.Parse()

	cfg := jsap.LoadConfig()
	// Credentials are NOT required to start: tools/list must answer even when
	// the .env has not been mounted yet, so a misconfigured deploy shows up as
	// a clear per-call error instead of a container that will not boot.
	if err := cfg.RequireCreds(); err != nil {
		fmt.Fprintf(os.Stderr, "jsap-mcp: warning: %v — tool calls will fail until it is set\n", err)
	}

	s := mcptools.New(cfg, version)

	switch strings.ToLower(*transport) {
	case "stdio":
		if err := server.ServeStdio(s.MCPServer()); err != nil {
			fmt.Fprintf(os.Stderr, "MCP server error: %v\n", err)
			os.Exit(1)
		}
	case "http":
		httpSrv := server.NewStreamableHTTPServer(s.MCPServer())
		// The base URL is not a secret (the credentials are, and they are never
		// printed); naming it here makes a misdirected deploy obvious in the logs.
		fmt.Fprintf(os.Stderr, "jsap-mcp %s serving MCP over streamable HTTP at %s (JSAP %s, READ-ONLY)\n",
			version, *addr, cfg.BaseURL)
		if err := httpSrv.Start(*addr); err != nil {
			fmt.Fprintf(os.Stderr, "MCP server error: %v\n", err)
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "unknown --transport %q (supported: stdio, http)\n", *transport)
		os.Exit(2)
	}
}

// defaultTransport reads JSAP_MCP_TRANSPORT when set, otherwise stdio, so
// running the binary with no arguments behaves like every other JIVO MCP
// server and a container can pin the transport through the environment.
func defaultTransport() string {
	if t := os.Getenv("JSAP_MCP_TRANSPORT"); t != "" {
		return t
	}
	return "stdio"
}
