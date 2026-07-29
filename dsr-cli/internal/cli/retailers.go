package cli

// Domain commands for retailers / outlets (tbl_retailers). Reference template
// for all domain command files — see domain.go for the conventions.
//
// Note: distributors and modern-trade stores live in this same table,
// distinguished by `type` (e.g. 'Distributor'). state/zone/area are nvarchar
// columns holding ids-as-text.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newRetailersCmd) }

func newRetailersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "retailers",
		Short:   "Retailers / outlets — list, get, count (tbl_retailers)",
		Aliases: []string{"retailer", "outlets", "shops"},
	}
	c.AddCommand(retailersListCmd(app), retailersGetCmd(app), retailersCountCmd(app))
	return c
}

// retailersSelectCols is the friendly column set for list output.
const retailersSelectCols = "Id, retailerName, type, category, state, zone, area, mobileNo, contactPerson, lastVisitDate, lastMonthSale, target"

func retailersWhere(f *domFilters, typ string) string {
	return fWhere(
		fEqStr("type", typ),
		fEqStr("state", f.State),
		fEqStr("zone", f.Zone),
		fLive("", f.IncludeDeleted),
	)
}

func retailersListCmd(app *App) *cobra.Command {
	var f domFilters
	var typ string
	c := &cobra.Command{
		Use:     "list",
		Short:   "List retailers (newest first); filter by --type/--state/--zone",
		Example: "  dsr retailers list --type Distributor\n  dsr retailers list --state 5 -n 20 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_retailers%s ORDER BY Id DESC",
				topN(app, 100), retailersSelectCols, retailersWhere(&f, typ))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "zone", "deleted")
	c.Flags().StringVar(&typ, "type", "", "filter by type (e.g. Shop, Distributor, Modern Store)")
	return c
}

func retailersCountCmd(app *App) *cobra.Command {
	var f domFilters
	var typ string
	c := &cobra.Command{
		Use:   "count",
		Short: "Count retailers matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS retailers FROM tbl_retailers" + retailersWhere(&f, typ)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "zone", "deleted")
	c.Flags().StringVar(&typ, "type", "", "filter by type (e.g. Shop, Distributor, Modern Store)")
	return c
}

func retailersGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <id>",
		Short:   "Show a single retailer by Id (all columns except password)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr retailers get 10432 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("retailer id must be an integer, got %q", args[0])
			}
			// Exclude password/otp/refreshToken from output.
			q := fmt.Sprintf("SELECT Id, erpId, type, retailerName, contactNo, mobileNo, contactPerson, "+
				"address, state, zone, area, subArea, category, ShopType, groupType, SAPID, GSTNum, "+
				"latitude, longitude, pincode, CreatedOn, lastVisitDate, lastVisitStatus, lastVisitSale, "+
				"lastMonthSale, sixMonthAvg, threeMonthAvg, target, deleted "+
				"FROM tbl_retailers WHERE Id = %d", id)
			return runSelect(app, q)
		},
	}
}
