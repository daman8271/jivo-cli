package cli

// Domain commands for distributors. Distributors are NOT a separate master —
// they live in tbl_retailers with type='Distributor'. distId throughout the
// distributor subsystem points at tbl_retailers.Id.
//
// This file also exposes the two small mapping tables that tie distributors to
// shops and to input/output value mappings:
//   - tbl_distributorShopMap (distId, shopId)   — which shops sit under a dist
//   - tbl_distmappings        (distid, applyto)  — value mappings per dist
// See study/vault/distributor-stock.md. Follows domain.go conventions.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newDistributorsCmd) }

func newDistributorsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "distributors",
		Short:   "Distributors — list, count, shops, mappings (tbl_retailers type='Distributor')",
		Aliases: []string{"distributor", "dist"},
	}
	c.AddCommand(
		distributorsListCmd(app),
		distributorsCountCmd(app),
		distributorsShopsCmd(app),
		distributorsMappingsCmd(app),
	)
	return c
}

// distributorsType is the tbl_retailers.type value that marks a distributor.
const distributorsType = "Distributor"

// distributorsSelectCols is the friendly column set for list output.
const distributorsSelectCols = "Id, erpId, retailerName, contactPerson, mobileNo, contactNo, state, zone, area, category, SAPID"

// distributorsWhere builds the tbl_retailers filter for distributor rows.
func distributorsWhere(f *domFilters) string {
	return fWhere(
		fEqStr("type", distributorsType),
		fEqStr("state", f.State),
		fEqStr("zone", f.Zone),
		fLive("", f.IncludeDeleted),
	)
}

func distributorsListCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "list",
		Short:   "List distributors (newest first); filter by --state/--zone",
		Example: "  dsr distributors list -n 20\n  dsr distributors list --state 5 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_retailers%s ORDER BY Id DESC",
				topN(app, 100), distributorsSelectCols, distributorsWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "zone", "deleted")
	return c
}

func distributorsCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count distributors matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS distributors FROM tbl_retailers" + distributorsWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "state", "zone", "deleted")
	return c
}

func distributorsShopsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "shops <distId>",
		Short:   "Retail shops mapped under a distributor (tbl_distributorShopMap)",
		Example: "  dsr distributors shops 10432 --json",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("distributor id must be an integer, got %q", args[0])
			}
			where := fWhere(
				fEqInt("distId", id),
				fLive("", f.IncludeDeleted),
			)
			q := fmt.Sprintf("SELECT TOP %d Id, distId, shopId, deleted FROM tbl_distributorShopMap%s ORDER BY Id DESC",
				topN(app, 500), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	return c
}

func distributorsMappingsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "mappings <distId>",
		Short:   "Value mappings for a distributor (tbl_distmappings)",
		Example: "  dsr distributors mappings 10432 --json",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("distributor id must be an integer, got %q", args[0])
			}
			where := fWhere(fEqInt("distid", id))
			q := fmt.Sprintf("SELECT TOP %d applyto, distid, status, inputvalue, outputvalue FROM tbl_distmappings%s ORDER BY applyto",
				topN(app, 500), where)
			return runSelect(app, q)
		},
	}
	return c
}
