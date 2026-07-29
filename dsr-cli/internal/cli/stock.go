package cli

// Domain commands for stock declarations (subsystem #12). Read-only.
//
// Tables:
//   tbl_retailerStock     — per-visit retailer stock lines (keyed by salesId; itemId -> tbl_item.Id).
//                           NOTE: no retailerId and no delete column here — the link to a retailer is
//                           via salesId (the sales/visit row), so this command keys on salesId.
//   tbl_distributorStock  — distributor stock-declaration headers (distId -> tbl_retailers.retailerId).
//   tbl_distStockProducts — per-SKU lines inside one distributor header (distStockId -> header).
//   tbl_monthlystock      — month-end closing stock per distributor x item (no delete column).

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newStockCmd) }

func newStockCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "stock",
		Short:   "Stock declarations — retailer, distributor, lines, monthly, count",
		Aliases: []string{"stocks"},
	}
	c.AddCommand(
		stockRetailerCmd(app),
		stockDistributorCmd(app),
		stockLinesCmd(app),
		stockMonthlyCmd(app),
		stockCountCmd(app),
	)
	return c
}

// stockRetailerCmd — retailer stock lines for a sales/visit row (tbl_retailerStock by salesId).
func stockRetailerCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "retailer <salesId>",
		Short:   "Retailer stock lines for a sales/visit id (tbl_retailerStock.salesId)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr stock retailer 84213\n  dsr stock retailer 84213 --item 55 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			salesID, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("salesId must be an integer, got %q", args[0])
			}
			where := fWhere(
				fEqInt("salesId", salesID),
				fEqInt("itemId", f.Item),
			)
			q := fmt.Sprintf("SELECT TOP %d id, salesId, itemId, stock, stockType "+
				"FROM tbl_retailerStock%s ORDER BY id DESC", topN(app, 200), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "item")
	return c
}

// stockDistributorCmd — distributor stock-declaration headers (tbl_distributorStock by distId).
func stockDistributorCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "distributor <distId>",
		Short:   "Distributor stock declarations (headers) for one distributor",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr stock distributor 10432\n  dsr stock distributor 10432 --from 2026-07-01 --to 2026-08-01",
		RunE: func(cmd *cobra.Command, args []string) error {
			distID, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("distId must be an integer, got %q", args[0])
			}
			where := fWhere(
				fEqInt("distId", distID),
				fEqInt("personId", f.Person),
				fDateGE("stockDate", f.From),
				fDateLT("stockDate", f.To),
				fLive("", f.IncludeDeleted),
			)
			q := fmt.Sprintf("SELECT TOP %d distStockId, stockDate, distId, distName, "+
				"personId, personName, personType, ApprovedStatus, remarks "+
				"FROM tbl_distributorStock%s ORDER BY stockDate DESC", topN(app, 100), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "deleted")
	return c
}

// stockLinesCmd — per-SKU lines inside one distributor stock header (tbl_distStockProducts).
func stockLinesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "lines <distStockId>",
		Short:   "SKU lines inside one distributor stock header (tbl_distStockProducts)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr stock lines 30581\n  dsr stock lines 30581 --item 55 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			hdrID, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("distStockId must be an integer, got %q", args[0])
			}
			where := fWhere(
				fEqInt("distStockId", hdrID),
				fEqInt("productId", f.Item),
				fLive("", f.IncludeDeleted),
			)
			q := fmt.Sprintf("SELECT TOP %d distStockId, productId, productName, boxes, "+
				"totalPieces, totalQuantity, productQuantity, productMrp, totalMrp "+
				"FROM tbl_distStockProducts%s ORDER BY productName", topN(app, 300), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "item", "deleted")
	return c
}

// stockMonthlyCmd — month-end closing stock per distributor x item (tbl_monthlystock).
func stockMonthlyCmd(app *App) *cobra.Command {
	var f domFilters
	var distID int
	c := &cobra.Command{
		Use:     "monthly",
		Short:   "Month-end closing stock per distributor x item (tbl_monthlystock)",
		Args:    cobra.NoArgs,
		Example: "  dsr stock monthly --distributor 10432\n  dsr stock monthly --from 2026-07-01 --to 2026-08-01 --item 55",
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fEqInt("distid", distID),
				fEqInt("itemid", f.Item),
				fDateGE("stockdate", f.From),
				fDateLT("stockdate", f.To),
			)
			q := fmt.Sprintf("SELECT TOP %d id, distid, stockdate, itemid, boxes, quantity "+
				"FROM tbl_monthlystock%s ORDER BY stockdate DESC, distid", topN(app, 300), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "item")
	c.Flags().IntVar(&distID, "distributor", 0, "filter by distributor id (tbl_monthlystock.distid)")
	return c
}

// stockCountCmd — count distributor stock declarations matching the filters.
func stockCountCmd(app *App) *cobra.Command {
	var f domFilters
	var distID int
	c := &cobra.Command{
		Use:     "count",
		Short:   "Count distributor stock declarations matching the filters",
		Args:    cobra.NoArgs,
		Example: "  dsr stock count --from 2026-07-01 --to 2026-08-01",
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fEqInt("distId", distID),
				fEqInt("personId", f.Person),
				fDateGE("stockDate", f.From),
				fDateLT("stockDate", f.To),
				fLive("", f.IncludeDeleted),
			)
			q := "SELECT COUNT(*) AS declarations FROM tbl_distributorStock" + where
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "deleted")
	c.Flags().IntVar(&distID, "distributor", 0, "filter by distributor id (tbl_distributorStock.distId)")
	return c
}
