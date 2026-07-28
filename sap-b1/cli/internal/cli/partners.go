package cli

import (
	"github.com/spf13/cobra"

	"sapb1/internal/errs"
)

const partnersDefaultSelect = "CardCode,CardName,CardType,Phone1,EmailAddress,CurrentAccountBalance"

func newPartnersCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "partners",
		Short: "Read business partners (customers & suppliers)",
	}
	cmd.AddCommand(newPartnersListCmd())
	return cmd
}

func newPartnersListCmd() *cobra.Command {
	var lf listFlags
	var customers, suppliers bool

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List business partners (BusinessPartners)",
		Example: exampleBlock(
			`sapb1 partners list`,
			`sapb1 partners list --customers --top 50`,
			`sapb1 partners list --suppliers --json`,
			`sapb1 partners list --filter "CurrentAccountBalance gt 0"`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if customers && suppliers {
				return &errs.UsageError{Msg: "--customers and --suppliers are mutually exclusive"}
			}
			extra := ""
			switch {
			case customers:
				extra = "CardType eq 'cCustomer'"
			case suppliers:
				extra = "CardType eq 'cSupplier'"
			}
			return runList(cmd, "BusinessPartners", lf, extra, partnersDefaultSelect, "CardCode")
		},
	}

	cmd.Flags().BoolVar(&customers, "customers", false, "only customers (CardType eq 'cCustomer')")
	cmd.Flags().BoolVar(&suppliers, "suppliers", false, "only suppliers (CardType eq 'cSupplier')")
	addListFlags(cmd, &lf, 20)
	return cmd
}
