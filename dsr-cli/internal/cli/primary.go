package cli

// Domain commands for JIVO -> distributor PRIMARY sales/stock/orders.
// See domain.go for the shared helpers and conventions this file follows.
//
// Flows covered (upstream leg: company -> distributor):
//   - tbl_primary_sales      : primary-sales transaction lines (main volume)
//   - tbl_distributorPrimary : field-logged distributor primary-stock headers
//   - tbl_distPrimaryProducts : product lines for a stock header
//   - tbl_distorders         : raw ingested distributor order/scheme lines

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newPrimaryCmd) }

func newPrimaryCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "primary",
		Short:   "Primary sales — JIVO -> distributor lines, stock, orders",
		Aliases: []string{"primary-sales", "prim"},
	}
	c.AddCommand(
		primaryListCmd(app),
		primaryStockCmd(app),
		primaryOrdersCmd(app),
		primaryCountCmd(app),
	)
	return c
}

// primarySalesCols is the friendly column set for primary-sales lines.
const primarySalesCols = "id, salesid, date, from_retailerid, to_retailerid, itemid, itemname, quantity, price, bill_number, bill_date, receive_date, uploaded_by"

// primaryRetailerMatch matches a retailer id on either the source or dest leg.
func primaryRetailerMatch(retailer int) string {
	if retailer == 0 {
		return ""
	}
	return fmt.Sprintf("(from_retailerid = %d OR to_retailerid = %d)", retailer, retailer)
}

// primarySalesWhere builds the WHERE clause for tbl_primary_sales.
func primarySalesWhere(f *domFilters) string {
	return fWhere(
		fDateGE("date", f.From),
		fDateLT("date", f.To),
		primaryRetailerMatch(f.Retailer),
		fEqInt("itemid", f.Item),
		fLive("", f.IncludeDeleted),
	)
}

func primaryListCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "list",
		Short:   "List primary-sales lines (newest first); filter by --from/--to/--retailer/--item",
		Example: "  dsr primary list --from 2026-07-01 --to 2026-08-01\n  dsr primary list --retailer 6163 -n 50 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_primary_sales%s ORDER BY date DESC, salesid",
				topN(app, 100), primarySalesCols, primarySalesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "retailer", "item", "deleted")
	return c
}

func primaryCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count primary-sales lines matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS primary_sales FROM tbl_primary_sales" + primarySalesWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "retailer", "item", "deleted")
	return c
}

// primaryStockCols is the friendly column set for distributor primary-stock headers.
const primaryStockCols = "distStockId, distId, distName, personId, personName, personType, stockDate, approved, received, completionStatus"

func primaryStockCmd(app *App) *cobra.Command {
	var f domFilters
	var pending bool
	c := &cobra.Command{
		Use:     "stock",
		Short:   "Field-logged distributor primary-stock entries (tbl_distributorPrimary)",
		Example: "  dsr primary stock --from 2026-07-01 --to 2026-08-01\n  dsr primary stock --salesperson 42 --pending",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			approved := ""
			if pending {
				approved = "ISNULL(approved, 0) = 0"
			}
			where := fWhere(
				fDateGE("stockDate", f.From),
				fDateLT("stockDate", f.To),
				fEqInt("personId", f.Person),
				approved,
				fLive("", f.IncludeDeleted),
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_distributorPrimary%s ORDER BY stockDate DESC",
				topN(app, 100), primaryStockCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "deleted")
	c.Flags().BoolVar(&pending, "pending", false, "only entries awaiting approval (approved = 0)")
	return c
}

// primaryOrdersCols is the friendly column set for ingested distributor orders.
const primaryOrdersCols = "id, distid, retailername, retailerid, sku, itemid, processstatus, quantity, free, rate, amount, datefrom, dateto, filename"

func primaryOrdersCmd(app *App) *cobra.Command {
	var f domFilters
	var dist string
	var unresolved bool
	c := &cobra.Command{
		Use:     "orders",
		Short:   "Ingested distributor order/scheme lines (tbl_distorders)",
		Example: "  dsr primary orders --from 2026-05-01 --to 2026-06-01\n  dsr primary orders --distributor 118 --unresolved --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			distFrag := ""
			if dist != "" {
				n, err := strconv.Atoi(dist)
				if err != nil {
					return Usagef("--distributor must be an integer, got %q", dist)
				}
				distFrag = fEqInt("distid", n)
			}
			unresolvedFrag := ""
			if unresolved {
				unresolvedFrag = "itemid IS NULL"
			}
			// tbl_distorders has no soft-delete column; bound by datefrom + TOP.
			where := fWhere(
				fDateGE("datefrom", f.From),
				fDateLT("datefrom", f.To),
				distFrag,
				unresolvedFrag,
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_distorders%s ORDER BY loadingdate DESC, id",
				topN(app, 100), primaryOrdersCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	c.Flags().StringVar(&dist, "distributor", "", "filter by distributor id (tbl_distorders.distid)")
	c.Flags().BoolVar(&unresolved, "unresolved", false, "only lines whose itemid is unresolved (NULL)")
	return c
}
