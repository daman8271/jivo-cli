package cli

// Domain commands for promoter / merchandiser in-store sales — the mirror of
// the SO secondary-sales flow. A visit is a header row in
// tbl_SalesReportPromoter (PK salesId) plus one line per SKU in
// tbl_ProductsSoldPromoter (join on salesId, NEVER on Id). See domain.go for
// the shared helper conventions and study/vault/promoter-activity.md for the
// data model.

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newPromotersCmd) }

func newPromotersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "promoters",
		Short:   "Promoter in-store sales — visits, lines, count (tbl_SalesReportPromoter)",
		Aliases: []string{"promoter", "merchandisers"},
	}
	c.AddCommand(promotersVisitsCmd(app), promotersLinesCmd(app), promotersCountCmd(app))
	return c
}

// promotersVisitCols is the friendly header column set for visit listings.
const promotersVisitCols = "salesId, date, personId, personName, retailerId, retailerName, state, zone, area, status, imagePath"

// promotersWhere builds the shared header filter (date/person/retailer/state/zone + soft-delete).
func promotersWhere(f *domFilters) string {
	return fWhere(
		fDateGE("date", f.From),
		fDateLT("date", f.To),
		fEqInt("personId", f.Person),
		fEqInt("retailerId", f.Retailer),
		fEqStr("state", f.State),
		fEqStr("zone", f.Zone),
		fLive("", f.IncludeDeleted),
	)
}

func promotersVisitsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "visits",
		Short:   "List promoter store visits (newest first); filter by --from/--to/--salesperson/--retailer/--state/--zone",
		Example: "  dsr promoters visits --from 2026-07-01 --to 2026-08-01\n  dsr promoters visits --salesperson 2871 -n 20 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_SalesReportPromoter%s ORDER BY salesId DESC",
				topN(app, 100), promotersVisitCols, promotersWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "retailer", "state", "zone", "deleted")
	return c
}

func promotersCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "count",
		Short:   "Count promoter visits matching the filters",
		Example: "  dsr promoters count --from 2026-07-01 --to 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS visits FROM tbl_SalesReportPromoter" + promotersWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "person", "retailer", "state", "zone", "deleted")
	return c
}

func promotersLinesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "lines <salesId>",
		Short:   "Show the SKU lines sold on one promoter visit (join on salesId)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr promoters lines 207626 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			salesID, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("salesId must be an integer, got %q", args[0])
			}
			q := fmt.Sprintf("SELECT TOP %d Id, salesId, productId, productName, pieces, "+
				"productQuantity, totalQuantity, openingStock, closingStock, sampleStock "+
				"FROM tbl_ProductsSoldPromoter%s ORDER BY Id",
				topN(app, 500),
				fWhere(fEqInt("salesId", salesID), fLive("", f.IncludeDeleted)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "deleted")
	return c
}
