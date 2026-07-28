package cli

import (
	"github.com/spf13/cobra"
)

const invoicesDefaultSelect = "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocStatus,DocCurrency"

func newInvoicesCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "invoices",
		Short: "Read A/R invoices",
	}
	cmd.AddCommand(newInvoicesListCmd())
	return cmd
}

func newInvoicesListCmd() *cobra.Command {
	var lf listFlags
	var open bool

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List A/R invoices (Invoices)",
		Example: exampleBlock(
			`sapb1 invoices list`,
			`sapb1 invoices list --open --top 50`,
			`sapb1 invoices list --filter "DocTotal gt 10000"`,
			`sapb1 invoices list --all --json | jq '. | length'`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			extra := ""
			if open {
				extra = "DocStatus eq 'O'"
			}
			return runList(cmd, "Invoices", lf, extra, invoicesDefaultSelect, "DocDate desc")
		},
	}

	cmd.Flags().BoolVar(&open, "open", false, "only open invoices (DocStatus eq 'O')")
	addListFlags(cmd, &lf, 20)
	return cmd
}
