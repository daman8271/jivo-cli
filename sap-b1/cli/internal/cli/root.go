// Package cli wires up the sapb1 command tree (cobra) on top of
// internal/config and internal/client.
package cli

import (
	"github.com/spf13/cobra"

	"sapb1/internal/config"
)

// Global flag values, bound once on the root command and inherited by every
// subcommand. Precedence with config.Load is: these flags > env vars > .env
// file > built-in defaults (see internal/config).
var (
	flagHost     string
	flagPort     int
	flagCompany  string
	flagUser     string
	flagInsecure bool
	flagTimeout  int
	flagJSON     bool
	flagCSV      bool
)

// NewRootCmd builds the full sapb1 command tree.
func NewRootCmd() *cobra.Command {
	root := &cobra.Command{
		Use:   "sapb1",
		Short: "Read-only CLI for the SAP Business One Service Layer",
		Long: `sapb1 is a read-only command-line client for the SAP Business One
Service Layer (b1s/v1), built for SAP B1 for HANA.

It never issues POST/PUT/PATCH/DELETE against business data — only Login and
Logout write anything, and that's just a session cookie.

Configuration is read from .env in the current directory (copy .env.example),
from SAPB1_* environment variables, and can be overridden per-invocation with
the flags below. Get on the company VPN (or get your IP whitelisted) before
using anything beyond --help.`,
		SilenceUsage:  true,
		SilenceErrors: true,
	}
	root.CompletionOptions.DisableDefaultCmd = true

	root.PersistentFlags().StringVar(&flagHost, "host", "", "SAP Service Layer host (overrides SAPB1_HOST)")
	root.PersistentFlags().IntVar(&flagPort, "port", 0, "SAP Service Layer port (overrides SAPB1_PORT, default 50000)")
	root.PersistentFlags().StringVar(&flagCompany, "company", "", "SAP CompanyDB (overrides SAPB1_COMPANYDB)")
	root.PersistentFlags().StringVar(&flagUser, "user", "", "SAP username (overrides SAPB1_USER)")
	root.PersistentFlags().BoolVar(&flagInsecure, "insecure", false, "skip TLS certificate verification (overrides SAPB1_INSECURE)")
	root.PersistentFlags().IntVar(&flagTimeout, "timeout", 0, "request timeout in seconds (overrides SAPB1_TIMEOUT, default 30)")
	root.PersistentFlags().BoolVar(&flagJSON, "json", false, "emit raw OData JSON instead of a text table (read commands only)")
	root.PersistentFlags().BoolVar(&flagCSV, "csv", false, "emit CSV (header + rows) instead of a text table; mutually exclusive with --json (read commands only)")

	// Offline discovery — works with zero network, reads only the embedded catalog.
	root.AddCommand(newEntitiesCmd())
	root.AddCommand(newOpsCmd())
	root.AddCommand(newCatalogCmd())
	root.AddCommand(newFieldsCmd())

	// Session + live reads.
	root.AddCommand(newAuthCmd())
	root.AddCommand(newDoctorCmd())
	root.AddCommand(newOrdersCmd())
	root.AddCommand(newInvoicesCmd())
	root.AddCommand(newItemsCmd())
	root.AddCommand(newPartnersCmd())
	root.AddCommand(newQueryCmd())

	// Read-only MCP server over stdio (for AI agents).
	root.AddCommand(newMCPCmd())

	return root
}

// loadConfig resolves the effective Config for a command invocation, layering
// flags (only those explicitly set on this command line) over env vars, the
// .env file, and built-in defaults.
func loadConfig(cmd *cobra.Command) (*config.Config, error) {
	flags := config.Flags{
		Host:        flagHost,
		HostSet:     cmd.Flags().Changed("host"),
		Port:        flagPort,
		PortSet:     cmd.Flags().Changed("port"),
		Company:     flagCompany,
		CompanySet:  cmd.Flags().Changed("company"),
		User:        flagUser,
		UserSet:     cmd.Flags().Changed("user"),
		Insecure:    flagInsecure,
		InsecureSet: cmd.Flags().Changed("insecure"),
		Timeout:     flagTimeout,
		TimeoutSet:  cmd.Flags().Changed("timeout"),
		JSON:        flagJSON,
		CSV:         flagCSV,
	}
	return config.Load(flags)
}

// exampleBlock is a tiny helper for building cobra Example blocks (which are
// conventionally indented two spaces per line) consistently.
func exampleBlock(lines ...string) string {
	out := ""
	for i, l := range lines {
		if i > 0 {
			out += "\n"
		}
		out += "  " + l
	}
	return out
}
