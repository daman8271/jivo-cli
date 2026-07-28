package cli

import (
	"os"
	"path/filepath"

	"github.com/joho/godotenv"
	"github.com/spf13/cobra"

	"sapb1/internal/mcp"
)

// newMCPCmd runs a read-only Model Context Protocol server over stdio, exposing
// the same SAP B1 reads the CLI offers as tools an AI agent can call.
func newMCPCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "mcp",
		Short: "Run a read-only MCP server over stdio (for Claude Code / Claude Desktop)",
		Long: `mcp starts a Model Context Protocol server that speaks JSON-RPC over
stdin/stdout, so an AI agent (Claude Code / Claude Desktop) can call the SAP
Business One Service Layer as tools.

Every tool is strictly READ-ONLY — the server only ever issues GET requests
(plus Login/Logout for the session). It exposes no tool that can create,
update, or delete business data.

Configuration is resolved exactly like every other command (flags > SAPB1_*
env vars > .env > defaults). Because an MCP client launches this process with
an arbitrary working directory, it ALSO loads .env from the directory holding
the sapb1 binary, so ~/sapb1-cli/.env is picked up wherever it's launched from.

You normally don't run this by hand — register it with your MCP client. See
MCP.md for copy-paste registration for Claude Code and Claude Desktop.`,
		Example: exampleBlock(
			`sapb1 mcp`,
		),
		Args: cobra.NoArgs,
		// stdout is reserved for the JSON-RPC protocol stream; suppress cobra's
		// usage/error printing so nothing corrupts it.
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
			return mcp.NewServer(cfg).Serve()
		},
	}
}
