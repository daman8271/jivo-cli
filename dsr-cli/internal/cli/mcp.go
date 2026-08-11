package cli

// `dsr mcp` — serve the read-only dsr surface to AI agents over the Model
// Context Protocol. The server lives inside this binary rather than in a
// separate cmd/dsr-mcp: the tools shell out to os.Executable(), which is THIS
// binary, so the tool surface cannot drift from the CLI it mirrors and a
// container needs exactly one mount.
//
// Default transport is stdio; --transport http serves the identical tool set
// over streamable HTTP for a hosted gateway. HTTP adds a transport, never a
// capability — same tools, same read-only gates.

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	dsrmcp "dsr/internal/mcp"
)

func init() { register(newMCPCmd) }

func newMCPCmd(app *App) *cobra.Command {
	var (
		transport string
		addr      string
	)

	cmd := &cobra.Command{
		Use:   "mcp",
		Short: "Serve the read-only DSR tools over the Model Context Protocol",
		Long: "Serve dsr's read-only surface as MCP tools an AI agent can call.\n\n" +
			"The tool set is a hand-authored allowlist, not a mirror of every subcommand:\n" +
			"15 grouped tools, each action pinned to a fixed dsr command. Nothing here can\n" +
			"write — dsr has no write commands at all, and the one command with filesystem\n" +
			"side effects (schema dump) is deliberately not exposed.\n\n" +
			"Transports (--transport):\n" +
			"  stdio  JSON-RPC on stdin/stdout, for a local MCP client (the default).\n" +
			"  http   Streamable HTTP at http://<addr>/mcp, for a hosted gateway.\n" +
			"         Binds 127.0.0.1 by default; exposing it on all interfaces\n" +
			"         (e.g. --addr 0.0.0.0:7709) is an explicit operator choice.",
		Example: "  dsr mcp\n" +
			"  dsr mcp --transport http --addr :7709",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			srv := dsrmcp.NewServer()
			switch strings.ToLower(transport) {
			case "", "stdio":
				return srv.Serve()
			case "http":
				fmt.Fprintf(cmd.ErrOrStderr(), "dsr serving MCP over streamable HTTP at %s (path /mcp)\n", addr)
				return srv.ServeStreamableHTTP(addr)
			default:
				return Usagef("unknown --transport %q (supported: stdio, http)", transport)
			}
		},
	}

	cmd.Flags().StringVar(&transport, "transport", "stdio", "MCP transport: stdio | http")
	cmd.Flags().StringVar(&addr, "addr", "127.0.0.1:7709", "bind address for --transport http (host:port or :port)")
	return cmd
}
