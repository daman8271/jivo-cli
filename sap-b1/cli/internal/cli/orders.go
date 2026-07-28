package cli

import (
	"github.com/spf13/cobra"
)

const ordersDefaultSelect = "DocEntry,DocNum,DocDate,CardCode,CardName,DocTotal,DocStatus,DocCurrency"

func newOrdersCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "orders",
		Short: "Read sales orders",
	}
	cmd.AddCommand(newOrdersListCmd())
	return cmd
}

func newOrdersListCmd() *cobra.Command {
	var lf listFlags
	var open bool

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List sales orders (Orders)",
		Example: exampleBlock(
			`sapb1 orders list`,
			`sapb1 orders list --open --top 50`,
			`sapb1 orders list --filter "CardCode eq 'C0001'" --orderby "DocDate desc"`,
			`sapb1 orders list --all --json | jq '.[] | .DocTotal' `,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			extra := ""
			if open {
				extra = "DocStatus eq 'O'"
			}
			return runList(cmd, "Orders", lf, extra, ordersDefaultSelect, "DocDate desc")
		},
	}

	cmd.Flags().BoolVar(&open, "open", false, "only open orders (DocStatus eq 'O')")
	addListFlags(cmd, &lf, 20)
	return cmd
}
