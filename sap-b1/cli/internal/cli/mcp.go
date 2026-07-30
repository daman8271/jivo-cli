package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/joho/godotenv"
	"github.com/spf13/cobra"

	"sapb1/internal/mcp"
)

// newMCPCmd runs a read-only Model Context Protocol server, exposing the same
// SAP B1 reads the CLI offers as tools an AI agent can call. Default transport
// is stdio; --transport http serves the identical tool set over streamable
// HTTP instead.
func newMCPCmd() *cobra.Command {
	var (
		transport string
		addr      string
	)
	cmd := &cobra.Command{
		Use:   "mcp",
		Short: "Run a read-only MCP server over stdio or streamable HTTP (for Claude Code / Claude Desktop)",
		Long: `mcp starts a Model Context Protocol server so an AI agent (Claude Code /
Claude Desktop) can call the SAP Business One Service Layer as tools.

Every tool is strictly READ-ONLY — the server only ever issues GET requests
(plus Login/Logout for the session). It exposes no tool that can create,
update, or delete business data.

Transports (--transport):
  stdio (default)  JSON-RPC over stdin/stdout, for an MCP client that launches
                   this process itself.
  http             Streamable HTTP at http://<addr>/mcp, for MCP clients that
                   connect over the network. The default bind is loopback
                   (127.0.0.1:7778) on purpose — there is no auth layer in
                   front of production SAP, so exposing it beyond this machine
                   (e.g. --addr 0.0.0.0:7778) is an explicit operator choice.

Configuration is resolved exactly like every other command (flags > SAPB1_*
env vars > .env > defaults). Because an MCP client launches this process with
an arbitrary working directory, it ALSO loads .env from the directory holding
the sapb1 binary, so ~/sapb1-cli/.env is picked up wherever it's launched from.

You normally don't run this by hand — register it with your MCP client. See
MCP.md for copy-paste registration for Claude Code and Claude Desktop.`,
		Example: exampleBlock(
			`sapb1 mcp`,
			`sapb1 mcp --transport http`,
			`sapb1 mcp --transport http --addr 127.0.0.1:9000`,
		),
		Args: cobra.NoArgs,
		// stdout is reserved for the JSON-RPC protocol stream in stdio mode;
		// suppress cobra's usage/error printing so nothing corrupts it.
		SilenceUsage:  true,
		SilenceErrors: true,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Best-effort: load .env sitting next to the binary so the server
			// finds ~/sapb1-cli/.env regardless of the client's working
			// directory. godotenv never overrides variables already set in the
			// real environment, preserving precedence (env var > this .env).
			if exe, err := os.Executable(); err == nil {
				_ = godotenv.Load(filepath.Join(filepath.Dir(exe), ".env"))
			}

			cfg, err := loadConfig(cmd)
			if err != nil {
				return err
			}

			srv := mcp.NewServer(cfg)
			switch strings.ToLower(transport) {
			case "stdio":
				return srv.Serve()
			case "http":
				fmt.Fprintf(cmd.ErrOrStderr(), "sapb1 serving MCP over streamable HTTP at %s (path /mcp)\n", addr)
				return srv.ServeStreamableHTTP(addr)
			default:
				return fmt.Errorf("unknown --transport %q (supported: stdio, http)", transport)
			}
		},
	}

	cmd.Flags().StringVar(&transport, "transport", "stdio", "MCP transport: stdio | http")
	cmd.Flags().StringVar(&addr, "addr", "127.0.0.1:7778", "bind address for --transport http (host:port or :port)")
	return cmd
}
