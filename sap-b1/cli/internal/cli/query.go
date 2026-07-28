package cli

import (
	"github.com/spf13/cobra"

	"sapb1/internal/errs"
)

func newQueryCmd() *cobra.Command {
	var lf listFlags

	cmd := &cobra.Command{
		Use:   "query <EntitySet>",
		Short: "Generic read of any Service Layer entity set",
		Long: `query is the power tool: a generic read-only GET against ANY Service Layer
entity set, with full control over $select/$filter/$top/$skip/$orderby and
pagination. Use this for entity sets that don't have a dedicated subcommand
yet (Quotations, PurchaseOrders, PurchaseInvoices, Warehouses, ItemGroups,
Users, JournalEntries, BusinessPartnerGroups, ...) — or for anything else in
your SAP schema.`,
		Example: exampleBlock(
			`sapb1 query Quotations --top 10`,
			`sapb1 query Warehouses --select "WarehouseCode,WarehouseName"`,
			`sapb1 query JournalEntries --filter "ReferenceDate ge '2024-01-01'" --all`,
			`sapb1 query Items --filter "ItemCode eq 'A0001'" --json`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			entitySet := args[0]
			if entitySet == "" {
				return &errs.UsageError{Msg: "entity set name is required, e.g. `sapb1 query Orders`"}
			}
			return runList(cmd, entitySet, lf, "", "", "")
		},
	}

	addListFlags(cmd, &lf, 20)
	return cmd
}
