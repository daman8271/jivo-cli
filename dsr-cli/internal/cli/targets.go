package cli

// Domain commands for targets & sales rollups — the planning + precomputed
// aggregate layer of the DSR SFA. See domain.go for shared conventions.
//
// Tables here are DERIVED/planning tables with NO soft-delete column
// (tbl_salesPersonMontlhyTarget, tbl_retailerMonthlyTarget,
// tbl_categoryWiseTargets, tbl_retailerMonthlySale, retailerLastSale), so we
// do NOT apply fLive() — instead every command is bounded by TOP + optional
// month/date filters. Note tbl_salesPersonMontlhyTarget keys on `userId`
// (not personId) and the table name is misspelled "Montlhy".

import (
	"fmt"
	"strconv"

	"github.com/spf13/cobra"
)

func init() { register(newTargetsCmd) }

func newTargetsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "targets",
		Short:   "Targets & sales rollups — person/retailer targets vs actuals",
		Aliases: []string{"target"},
	}
	c.AddCommand(
		targetsPersonCmd(app),
		targetsRetailerCmd(app),
		targetsCategoryCmd(app),
		targetsCountCmd(app),
	)
	return c
}

// targetsMonthWhere builds the month-bucket range filter for a given column.
func targetsMonthWhere(col string, f *domFilters, extra ...string) string {
	parts := append([]string{
		fDateGE(col, f.From),
		fDateLT(col, f.To),
	}, extra...)
	return fWhere(parts...)
}

// targetsPersonCmd — monthly value/box targets for one salesperson (by userId),
// newest month first. Optional --from/--to bound the month bucket.
func targetsPersonCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "person <userId>",
		Short:   "Monthly value/box targets for a salesperson (tbl_salesPersonMontlhyTarget.userId)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr targets person 142\n  dsr targets person 142 --from 2026-01-01 --to 2026-08-01 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			uid, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("userId must be an integer, got %q", args[0])
			}
			where := targetsMonthWhere("month", &f, fEqInt("userId", uid))
			q := fmt.Sprintf(
				"SELECT TOP %d id, userId, month, target, targetBoxes, personType "+
					"FROM tbl_salesPersonMontlhyTarget%s ORDER BY month DESC",
				topN(app, 100), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

// targetsCategoryCmd — per-SKU-category monthly targets for one salesperson
// (tbl_categoryWiseTargets keys on personId + date).
func targetsCategoryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "category <personId>",
		Short:   "Per-category monthly targets for a salesperson (tbl_categoryWiseTargets)",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr targets category 142\n  dsr targets category 142 --from 2026-01-01 --to 2026-08-01",
		RunE: func(cmd *cobra.Command, args []string) error {
			pid, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("personId must be an integer, got %q", args[0])
			}
			where := targetsMonthWhere("date", &f, fEqInt("personId", pid))
			q := fmt.Sprintf(
				"SELECT TOP %d id, personId, date, canola, gold, olive, mustard, sunflower, "+
					"soyabean, cottonseed, riceBran, groundnut, extraVirgin, pomace, desiGhee "+
					"FROM tbl_categoryWiseTargets%s ORDER BY date DESC",
				topN(app, 100), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

// targetsRetailerCmd — for one retailer: monthly target vs actual monthly sale,
// plus the last-sale snapshot. Bounded by --from/--to on the month bucket.
func targetsRetailerCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "retailer <retailerId>",
		Short:   "Retailer monthly target vs actual sale + last-sale snapshot",
		Args:    cobra.ExactArgs(1),
		Example: "  dsr targets retailer 10432\n  dsr targets retailer 10432 --from 2026-01-01 --to 2026-08-01 --json",
		RunE: func(cmd *cobra.Command, args []string) error {
			rid, err := strconv.Atoi(args[0])
			if err != nil {
				return Usagef("retailerId must be an integer, got %q", args[0])
			}
			where := targetsMonthWhere("s.saleMonth", &f, fEqInt("s.retailerId", rid))
			q := fmt.Sprintf(
				"SELECT TOP %d s.retailerId, s.saleMonth, s.sale AS actualSale, "+
					"t.target AS targetQty, l.lastSale, l.lastSaleDate, l.avgLastYear "+
					"FROM tbl_retailerMonthlySale s "+
					"LEFT JOIN tbl_retailerMonthlyTarget t "+
					"ON t.retailerId = s.retailerId AND t.month = s.saleMonth "+
					"LEFT JOIN retailerLastSale l ON l.retailerId = s.retailerId"+
					"%s ORDER BY s.saleMonth DESC",
				topN(app, 100), where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

// targetsCountCmd — count rows across the target/aggregate tables (optionally
// scoped to a salesperson/retailer via flags), for quick coverage checks.
func targetsCountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "count",
		Short:   "Count salesperson monthly-target rows (filter --salesperson/--from/--to)",
		Args:    cobra.NoArgs,
		Example: "  dsr targets count\n  dsr targets count --salesperson 142",
		RunE: func(cmd *cobra.Command, args []string) error {
			where := targetsMonthWhere("month", &f, fEqInt("userId", f.Person))
			q := "SELECT COUNT(*) AS personMonthTargets FROM tbl_salesPersonMontlhyTarget" + where
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "person", "date")
	return c
}
