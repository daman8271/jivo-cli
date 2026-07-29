package cli

// Domain commands for SO secondary sales (field-sales-entry). See domain.go
// for the shared helpers and conventions.
//
// tbl_SalesReport is the visit header (PK salesId): personId->salesperson,
// retailerId->retailers, `date` = visit date. There is NO beatId here (beat is
// resolved via person+geo). Line items hang off the header by salesId:
// tbl_ProductsSold (normal) and tbl_SchemeProductsSold (scheme/offer). Sentinel
// productId rows (<= 0) are dropped from line output.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newSalesCmd) }

func newSalesCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "sales",
		Short:   "SO secondary sales — visits, lines, summary, count (tbl_SalesReport)",
		Aliases: []string{"sale", "visits"},
	}
	c.AddCommand(salesVisitsCmd(app), salesLinesCmd(app), salesSummaryCmd(app), salesCountCmd(app))
	return c
}

// salesVisitCols is the friendly header column set for visit listings.
const salesVisitCols = "salesId, date, personId, personName, retailerId, retailerName, " +
	"distributor, status, totalPieces, totalQuantity, totalPrice"

// salesWhere builds the common WHERE for the visit header.
func salesWhere(f *domFilters) string {
	return fWhere(
		fEqInt("personId", f.Person),
		fEqInt("retailerId", f.Retailer),
		fDateGE("date", f.From),
		fDateLT("date", f.To),
		fLive("", f.IncludeDeleted),
	)
}

func salesVisitsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "visits",
		Short:   "List field visits (newest first); filter by --salesperson/--retailer/--from/--to",
		Example: "  dsr sales visits --from 2026-07-01 --to 2026-08-01 --salesperson 71\n  dsr sales visits --retailer 10432 -n 20 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_SalesReport%s ORDER BY date DESC, salesId DESC",
				topN(app, 100), salesVisitCols, salesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "retailer", "deleted")
	return c
}

func salesCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "count",
		Short: "Count visits matching the filters",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS visits FROM tbl_SalesReport" + salesWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "retailer", "deleted")
	return c
}

func salesLinesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "lines <salesId>",
		Short:   "Product lines punched at one visit (sold + scheme), by salesId",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr sales lines 123456 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			id, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("salesId must be an integer, got %q", args[0])
			}
			// productId > 0 drops sentinel/placeholder rows.
			q := fmt.Sprintf(
				"SELECT 'sold' AS kind, productId, productName, pieces, productQuantity, "+
					"totalQuantity, totalPrice FROM tbl_ProductsSold "+
					"WHERE salesId = %d AND productId > 0 AND %s "+
					"UNION ALL "+
					"SELECT 'scheme' AS kind, productId, productName, pieces, productQuantity, "+
					"totalQuantity, NULL FROM tbl_SchemeProductsSold "+
					"WHERE salesId = %d AND productId > 0 AND %s "+
					"ORDER BY kind, productId",
				id, fLive("", f.IncludeDeleted), id, fLive("", f.IncludeDeleted))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	return c
}

func salesSummaryCmd(app *App) *cobra.Command {
	var f domFilters
	var by string
	c := &cobra.Command{
		Use:     "summary",
		Short:   "Sum totalPrice/totalPieces over a range, grouped by day or salesperson",
		Example: "  dsr sales summary --from 2026-07-01 --to 2026-08-01 --by day\n  dsr sales summary --from 2026-07-01 --to 2026-08-01 --by person",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			var groupCol, label string
			switch by {
			case "person", "salesperson", "so":
				groupCol, label = "personId, personName", "personId, personName"
			case "day", "date", "":
				groupCol, label = "date", "date"
			default:
				return Usagef("--by must be 'day' or 'person', got %q", by)
			}
			q := fmt.Sprintf(
				"SELECT TOP %d %s, COUNT(*) AS visits, "+
					"SUM(ISNULL(totalPieces,0)) AS pieces, "+
					"SUM(ISNULL(totalQuantity,0)) AS bottles, "+
					"SUM(ISNULL(totalPrice,0)) AS value "+
					"FROM tbl_SalesReport%s GROUP BY %s ORDER BY value DESC",
				topN(app, 200), label, salesWhere(&f), groupCol)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "retailer", "deleted")
	c.Flags().StringVar(&by, "by", "day", "group by: day | person")
	return c
}
