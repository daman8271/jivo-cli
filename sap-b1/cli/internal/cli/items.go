package cli

import (
	"fmt"

	"github.com/spf13/cobra"
)

const itemsDefaultSelect = "ItemCode,ItemName,ItemsGroupCode,QuantityOnStock,Valid"

func newItemsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "items",
		Short: "Read items (products)",
	}
	cmd.AddCommand(newItemsListCmd())
	return cmd
}

func newItemsListCmd() *cobra.Command {
	var lf listFlags
	var lowStock int

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List items (Items)",
		Example: exampleBlock(
			`sapb1 items list`,
			`sapb1 items list --low-stock 10`,
			`sapb1 items list --filter "ItemsGroupCode eq 100"`,
			`sapb1 items list --all --json`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			extra := ""
			if lowStock > 0 {
				extra = fmt.Sprintf("QuantityOnStock le %d", lowStock)
			}
			return runList(cmd, "Items", lf, extra, itemsDefaultSelect, "ItemCode")
		},
	}

	cmd.Flags().IntVar(&lowStock, "low-stock", 0, "only items with QuantityOnStock <= N")
	addListFlags(cmd, &lf, 20)
	return cmd
}
