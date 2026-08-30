package cli

// Assortment expansion — "does ARY carry everything the 5,000 residents need?"
//
// Baru Sahib is a closed township: ~5,000 people live there and ARY is their only
// shop. Anything ARY does not stock is either done without or bought 30-50 km away
// in town. So the interesting question is not "what did we sell" but "what should
// be on the shelf and is not".
//
// Two halves, and they are deliberately separate:
//
//   SQL-backed (what we have) — taxonomy, coverage, dead, wallet, velocity,
//     headroom. These read FR8HODBNEW live and are always current.
//
//   Corpus-backed (what people need) — gaps, priority, research, sweep. These read
//     JSON files written by the assortment research runs under assort/research/.
//     The research is done BLIND to ARY's catalogue on purpose: an ideal-assortment
//     list built while looking at our own shelf just reproduces our own shelf.
//
// Notes (verified live 2026-08-28):
//   - SaleHeader dates are VoucherDate (smalldatetime); there is no cancel flag,
//     reversals are separate SaleReturn documents, so these figures are GROSS of
//     returns. Returns are 0.78-3.66% a year — see `ary sales net`.
//   - Sales value is SUM(SaleDetail.Quantity * SaleDetail.SaleRate). SaleDetail has
//     no Amount column.
//   - ProductMaster.StandardCostPrice is set on 41 of 19,481 active SKUs and
//     MaxRetailPrice on ZERO, so margin cannot come from the master. Real cost and
//     price live per-location on ProductChildMaster; Stock.PurchaseCost is the
//     valuation cost these commands use.
//   - 19,481 SKUs are flagged active but only ~6,100 sold in 12 months. "active"
//     in this database means "not deleted", not "on the shelf".

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newAssortCmd) }

// assortResidents is the Baru Sahib resident population every per-head figure is
// divided by. Overridable with --residents because it is a stated headcount, not
// a queried one.
const assortResidents = 5000

func newAssortCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "assort",
		Short:   "Assortment expansion — what the 5,000 residents need vs what ARY stocks",
		Aliases: []string{"assortment", "expand", "gap"},
		Long: "ARY is the only shop for ~5,000 residents of Baru Sahib. These commands measure the\n" +
			"catalogue against that population: which categories are thin, which SKUs are listed but\n" +
			"dead, how much of each resident's wallet ARY actually captures, and — from the research\n" +
			"corpus — which SKU lines a store serving this township should carry and does not.\n\n" +
			"SQL-backed:    taxonomy  coverage  dead  wallet  velocity  headroom\n" +
			"Corpus-backed: research  gaps  priority  sweep",
	}
	c.AddCommand(
		assortTaxonomyCmd(app), assortCoverageCmd(app), assortDeadCmd(app),
		assortWalletCmd(app), assortVelocityCmd(app), assortHeadroomCmd(app),
		assortBenchmarkCmd(app), assortProbeCmd(app), assortLeakCmd(app),
		assortResearchCmd(app), assortGapsCmd(app), assortPriorityCmd(app),
		assortSweepCmd(app),
	)
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// shared SQL fragments
// ─────────────────────────────────────────────────────────────────────────────

// assortWindow returns the sale-date bound for the last n months, or explicit
// --from/--to when given.
func assortWindow(f *domFilters, months int, col string) string {
	if strings.TrimSpace(f.From) != "" || strings.TrimSpace(f.To) != "" {
		return fAnd(fDateGE(col, f.From), fDateLT(col, f.To))
	}
	if months <= 0 {
		return ""
	}
	return fmt.Sprintf(" AND %s >= DATEADD(month, -%d, CAST(GETDATE() AS date))", col, months)
}

// assortSoldCTE is the per-SKU sales roll-up for the window, used as a LEFT JOIN
// so SKUs that sold nothing still appear.
func assortSoldCTE(window string) string {
	return "(SELECT d.ProductID, COUNT(DISTINCT d.SerialNumber) AS bills, " +
		"SUM(d.Quantity) AS qty, SUM(d.Quantity * d.SaleRate) AS value, MAX(h.VoucherDate) AS last_sale " +
		"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber" +
		fWhere(strings.TrimPrefix(strings.TrimSpace(window), "AND ")) +
		" GROUP BY d.ProductID)"
}

// assortStockCTE is the per-SKU on-hand and cost valuation roll-up.
//
// Value MUST be summed row-wise. Stock holds one row per warehouse/location child,
// each carrying its own PurchaseCost, and rows may be negative. The earlier form
// SUM(Quantity) * MAX(PurchaseCost) priced every unit at the dearest row's cost and
// then applied it to a netted quantity: measured 2026-08-30 it read the book at
// Rs 30.78 L against a true Rs 96.90 L, and turned -Rs 13.97 L of negative book stock
// into -Rs 182.16 L — the source of the bogus "-Rs 1.56 Cr posted without receipts".
const assortStockCTE = "(SELECT s.ProductID, SUM(s.Quantity) AS book_qty, " +
	"SUM(s.Quantity * s.PurchaseCost) AS value_at_cost FROM Stock s GROUP BY s.ProductID)"

func assortMonthsFlag(c *cobra.Command, months *int) {
	c.Flags().IntVar(months, "months", 12, "sales window in months (0 = all time); --from/--to override")
}

func assortResidentsFlag(c *cobra.Command, residents *int) {
	c.Flags().IntVar(residents, "residents", assortResidents,
		"Baru Sahib resident population used as the per-head denominator")
}

// ─────────────────────────────────────────────────────────────────────────────
// taxonomy
// ─────────────────────────────────────────────────────────────────────────────

func assortTaxonomyCmd(app *App) *cobra.Command {
	var f domFilters
	var months, group int
	var subgroups bool
	c := &cobra.Command{
		Use:   "taxonomy",
		Short: "The category tree — department, group, subgroup — with SKUs and what actually sold",
		Long: "Every level shows three counts that should be read together: skus (in the catalogue),\n" +
			"active (not deleted), and sold (moved at least once in the window). A group where active\n" +
			"is large and sold is small is a listing, not a range.",
		Example: "  ary assort taxonomy\n" +
			"  ary assort taxonomy --subgroups --group 138\n" +
			"  ary assort taxonomy --months 24",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			w := assortWindow(&f, months, "h.VoucherDate")
			sold := assortSoldCTE(w)

			if subgroups {
				q := fmt.Sprintf("SELECT TOP %d g.ProductGroupName AS product_group, "+
					"sg.SubGroupName AS sub_group, COUNT(*) AS skus, "+
					"SUM(CASE WHEN p.IsActive = 1 THEN 1 ELSE 0 END) AS active, "+
					"COUNT(sl.ProductID) AS sold, "+
					"CAST(ISNULL(SUM(sl.value), 0) AS decimal(18,2)) AS sales "+
					"FROM ProductMaster p "+
					"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
					"LEFT JOIN SubGroupMaster sg ON sg.SubGroupID = p.SubGroupID "+
					"LEFT JOIN %s sl ON sl.ProductID = p.ProductID%s "+
					"GROUP BY g.ProductGroupName, sg.SubGroupName "+
					"ORDER BY g.ProductGroupName, SUM(ISNULL(sl.value, 0)) DESC",
					topN(app, 400), sold, fWhere(fEqInt("p.ProductGroupID", group), fLike("g.ProductGroupName", f.Search)))
				return runSelect(app, q)
			}

			q := fmt.Sprintf("SELECT TOP %d dp.DepartmentName AS department, g.ProductGroupID AS group_id, "+
				"g.ProductGroupName AS product_group, COUNT(DISTINCT p.SubGroupID) AS subgroups, "+
				"COUNT(*) AS skus, SUM(CASE WHEN p.IsActive = 1 THEN 1 ELSE 0 END) AS active, "+
				"COUNT(sl.ProductID) AS sold, "+
				"CAST(ISNULL(SUM(sl.value), 0) AS decimal(18,2)) AS sales "+
				"FROM ProductMaster p "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN DepartmentMaster dp ON dp.DepartmentID = p.DepartmentID "+
				"LEFT JOIN %s sl ON sl.ProductID = p.ProductID%s "+
				"GROUP BY dp.DepartmentName, g.ProductGroupID, g.ProductGroupName "+
				"ORDER BY SUM(ISNULL(sl.value, 0)) DESC",
				topN(app, 200), sold, fWhere(fEqInt("p.ProductGroupID", group), fLike("g.ProductGroupName", f.Search)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "search")
	assortMonthsFlag(c, &months)
	c.Flags().IntVar(&group, "group", 0, "restrict to one ProductGroupID")
	c.Flags().BoolVar(&subgroups, "subgroups", false, "break down to subgroup level")
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// coverage
// ─────────────────────────────────────────────────────────────────────────────

func assortCoverageCmd(app *App) *cobra.Command {
	var f domFilters
	var months, residents int
	c := &cobra.Command{
		Use:   "coverage",
		Short: "Per category: SKUs listed vs SKUs moving, sales, revenue share, spend per resident",
		Long: "The single table to read first. dead_skus is active SKUs with no sale in the window —\n" +
			"catalogue that looks like range but is not. per_resident_yr is that category's annualised\n" +
			"sales divided by the resident population: it is the number to compare against what an\n" +
			"Indian household actually spends on that category in a year.",
		Example: "  ary assort coverage\n" +
			"  ary assort coverage --months 12 --residents 5000\n" +
			"  ary assort coverage --csv > coverage.csv",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if residents <= 0 {
				return Usagef("--residents must be positive")
			}
			w := assortWindow(&f, months, "h.VoucherDate")
			sold := assortSoldCTE(w)
			mo := months
			if mo <= 0 {
				mo = 12
			}
			q := fmt.Sprintf("SELECT TOP %d g.ProductGroupID AS group_id, g.ProductGroupName AS product_group, "+
				"COUNT(*) AS skus, SUM(CASE WHEN p.IsActive = 1 THEN 1 ELSE 0 END) AS active_skus, "+
				"COUNT(sl.ProductID) AS sold_skus, "+
				"SUM(CASE WHEN p.IsActive = 1 AND sl.ProductID IS NULL THEN 1 ELSE 0 END) AS dead_skus, "+
				"CAST(100.0 * COUNT(sl.ProductID) / NULLIF(SUM(CASE WHEN p.IsActive = 1 THEN 1 ELSE 0 END), 0) AS decimal(9,1)) AS moving_pct, "+
				"CAST(ISNULL(SUM(sl.value), 0) AS decimal(18,2)) AS sales, "+
				"CAST(ISNULL(SUM(sl.bills), 0) AS bigint) AS bill_lines, "+
				"CAST(ISNULL(SUM(sl.value), 0) * 12.0 / %d / %d AS decimal(18,2)) AS per_resident_yr "+
				"FROM ProductMaster p "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN %s sl ON sl.ProductID = p.ProductID%s "+
				"GROUP BY g.ProductGroupID, g.ProductGroupName "+
				"ORDER BY SUM(ISNULL(sl.value, 0)) DESC",
				topN(app, 200), mo, residents, sold, fWhere(fLike("g.ProductGroupName", f.Search)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "search")
	assortMonthsFlag(c, &months)
	assortResidentsFlag(c, &residents)
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// dead
// ─────────────────────────────────────────────────────────────────────────────

func assortDeadCmd(app *App) *cobra.Command {
	var f domFilters
	var months, group int
	var byGroup, withStockOnly bool
	c := &cobra.Command{
		Use:   "dead",
		Short: "Active SKUs that did not sell in the window — the listing tail, and what it ties up",
		Long: "Differs from `ary stock dead`, which starts from stock on hand. This starts from the\n" +
			"CATALOGUE: a SKU flagged active with no sale is a line the operator still has to price,\n" +
			"count and shelf. --by-group is the summary worth acting on.",
		Example: "  ary assort dead --by-group\n" +
			"  ary assort dead --group 141 --with-stock -n 60\n" +
			"  ary assort dead --months 24 --by-group",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			w := assortWindow(&f, months, "h.VoucherDate")
			sold := assortSoldCTE(w)
			having := "sl.ProductID IS NULL"
			if withStockOnly {
				having += " AND ISNULL(st.book_qty, 0) > 0"
			}
			where := fWhere("p.IsActive = 1", fEqInt("p.ProductGroupID", group), fLike("p.ProductName", f.Search), having)

			if byGroup {
				q := fmt.Sprintf("SELECT TOP %d g.ProductGroupName AS product_group, "+
					"COUNT(*) AS dead_skus, "+
					"SUM(CASE WHEN ISNULL(st.book_qty, 0) > 0 THEN 1 ELSE 0 END) AS dead_with_stock, "+
					"CAST(ISNULL(SUM(CASE WHEN st.book_qty > 0 THEN st.value_at_cost ELSE 0 END), 0) AS decimal(18,2)) AS locked_at_cost "+
					"FROM ProductMaster p "+
					"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
					"LEFT JOIN %s sl ON sl.ProductID = p.ProductID "+
					"LEFT JOIN %s st ON st.ProductID = p.ProductID%s "+
					"GROUP BY g.ProductGroupName ORDER BY COUNT(*) DESC",
					topN(app, 200), sold, assortStockCTE, where)
				return runSelect(app, q)
			}

			q := fmt.Sprintf("SELECT TOP %d p.ProductID AS id, p.ProductName AS product, "+
				"g.ProductGroupName AS product_group, sg.SubGroupName AS sub_group, "+
				"CAST(ISNULL(st.book_qty, 0) AS decimal(18,2)) AS book_qty, "+
				"CAST(ISNULL(st.value_at_cost, 0) AS decimal(18,2)) AS value_at_cost "+
				"FROM ProductMaster p "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN SubGroupMaster sg ON sg.SubGroupID = p.SubGroupID "+
				"LEFT JOIN %s sl ON sl.ProductID = p.ProductID "+
				"LEFT JOIN %s st ON st.ProductID = p.ProductID%s "+
				"ORDER BY ISNULL(st.value_at_cost, 0) DESC",
				topN(app, 100), sold, assortStockCTE, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "search")
	assortMonthsFlag(c, &months)
	c.Flags().IntVar(&group, "group", 0, "restrict to one ProductGroupID")
	c.Flags().BoolVar(&byGroup, "by-group", false, "summarise per product group instead of per SKU")
	c.Flags().BoolVar(&withStockOnly, "with-stock", false, "only dead SKUs that still hold stock")
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// wallet
// ─────────────────────────────────────────────────────────────────────────────

func assortWalletCmd(app *App) *cobra.Command {
	var f domFilters
	var months, residents int
	c := &cobra.Command{
		Use:   "wallet",
		Short: "What ARY captures per resident per month, overall and by category",
		Long: "Divides ARY's sales by the resident population. The top block is the whole township; the\n" +
			"table below is per category. These are CAPTURE figures — the gap between them and a\n" +
			"household's real spend on that category is the wallet leaking to town.\n\n" +
			"The denominator is a stated headcount (~5,000), not a queried one: override with\n" +
			"--residents. Figures are gross of sale returns (0.8-3.7% a year).",
		Example: "  ary assort wallet\n" +
			"  ary assort wallet --months 12 --residents 5000",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if residents <= 0 {
				return Usagef("--residents must be positive")
			}
			w := assortWindow(&f, months, "h.VoucherDate")
			mo := months
			if mo <= 0 {
				mo = 12
			}
			whereH := fWhere(strings.TrimPrefix(strings.TrimSpace(w), "AND "))

			total := fmt.Sprintf("SELECT COUNT(DISTINCT h.SerialNumber) AS bills, "+
				"CAST(SUM(d.Quantity * d.SaleRate) AS decimal(18,2)) AS sales, "+
				"CAST(SUM(d.Quantity * d.SaleRate) / %d AS decimal(18,2)) AS per_resident_window, "+
				"CAST(SUM(d.Quantity * d.SaleRate) / %d / %d AS decimal(18,2)) AS per_resident_month, "+
				"CAST(1.0 * COUNT(DISTINCT h.SerialNumber) / %d / %d AS decimal(9,2)) AS bills_per_resident_month, "+
				"CAST(SUM(d.Quantity * d.SaleRate) / NULLIF(COUNT(DISTINCT h.SerialNumber), 0) AS decimal(18,2)) AS avg_bill "+
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber%s",
				residents, residents, mo, residents, mo, whereH)

			byGroup := fmt.Sprintf("SELECT TOP %d g.ProductGroupName AS product_group, "+
				"CAST(SUM(d.Quantity * d.SaleRate) AS decimal(18,2)) AS sales, "+
				"CAST(100.0 * SUM(d.Quantity * d.SaleRate) / NULLIF(SUM(SUM(d.Quantity * d.SaleRate)) OVER (), 0) AS decimal(9,2)) AS rev_pct, "+
				"CAST(SUM(d.Quantity * d.SaleRate) / %d / %d AS decimal(18,2)) AS per_resident_month, "+
				"CAST(SUM(d.Quantity * d.SaleRate) * 12.0 / %d / %d AS decimal(18,2)) AS per_resident_yr "+
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber "+
				"JOIN ProductMaster p ON p.ProductID = d.ProductID "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID%s "+
				"GROUP BY g.ProductGroupName ORDER BY SUM(d.Quantity * d.SaleRate) DESC",
				topN(app, 100), residents, mo, mo, residents, whereH)

			byCounter := fmt.Sprintf("SELECT wm.WarehouseName AS counter, "+
				"COUNT(DISTINCT h.SerialNumber) AS bills, "+
				"CAST(SUM(d.Quantity * d.SaleRate) AS decimal(18,2)) AS sales, "+
				"CAST(SUM(d.Quantity * d.SaleRate) / %d / %d AS decimal(18,2)) AS per_resident_month "+
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber "+
				"LEFT JOIN WarehouseMaster wm ON wm.WarehouseID = d.WarehouseID%s "+
				"GROUP BY wm.WarehouseName ORDER BY SUM(d.Quantity * d.SaleRate) DESC",
				residents, mo, whereH)

			return runSections(app, []section{
				{fmt.Sprintf("township (%d residents, %d-month window)", residents, mo), total},
				{"by counter", byCounter},
				{"by category", byGroup},
			})
		},
	}
	addDomFilters(c, &f, "date")
	assortMonthsFlag(c, &months)
	assortResidentsFlag(c, &residents)
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// velocity
// ─────────────────────────────────────────────────────────────────────────────

func assortVelocityCmd(app *App) *cobra.Command {
	var f domFilters
	var months int
	c := &cobra.Command{
		Use:   "velocity",
		Short: "How concentrated sales are — SKUs by revenue decile, and the long tail",
		Long: "Answers 'how many SKUs actually earn their shelf'. If a small band of SKUs carries most\n" +
			"of the revenue, the room for new categories is already on the shelf — it is just occupied\n" +
			"by the tail.",
		Example: "  ary assort velocity\n  ary assort velocity --months 6",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			w := assortWindow(&f, months, "h.VoucherDate")
			whereH := fWhere(strings.TrimPrefix(strings.TrimSpace(w), "AND "))

			bands := "WITH sold AS (SELECT d.ProductID, SUM(d.Quantity * d.SaleRate) AS value " +
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber" + whereH +
				" GROUP BY d.ProductID), " +
				"ranked AS (SELECT ProductID, value, " +
				"SUM(value) OVER (ORDER BY value DESC ROWS UNBOUNDED PRECEDING) AS cum, " +
				"SUM(value) OVER () AS total, " +
				"ROW_NUMBER() OVER (ORDER BY value DESC) AS rn FROM sold) " +
				"SELECT band, MIN(rn) AS from_rank, MAX(rn) AS to_rank, COUNT(*) AS skus, " +
				"CAST(SUM(value) AS decimal(18,2)) AS sales, " +
				"CAST(100.0 * SUM(value) / MAX(total) AS decimal(9,2)) AS rev_pct FROM (" +
				"SELECT rn, value, total, CASE " +
				"WHEN cum <= 0.50 * total THEN '1. top 50% of revenue' " +
				"WHEN cum <= 0.80 * total THEN '2. next 30% (to 80%)' " +
				"WHEN cum <= 0.95 * total THEN '3. next 15% (to 95%)' " +
				"ELSE '4. last 5% of revenue' END AS band FROM ranked) x " +
				"GROUP BY band ORDER BY band"

			shape := "WITH sold AS (SELECT d.ProductID, SUM(d.Quantity * d.SaleRate) AS value, " +
				"COUNT(DISTINCT d.SerialNumber) AS bills " +
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber" + whereH +
				" GROUP BY d.ProductID) " +
				"SELECT (SELECT COUNT(*) FROM ProductMaster WHERE IsActive = 1) AS active_skus, " +
				"COUNT(*) AS skus_sold, " +
				"(SELECT COUNT(*) FROM ProductMaster WHERE IsActive = 1) - COUNT(*) AS never_sold, " +
				"SUM(CASE WHEN bills = 1 THEN 1 ELSE 0 END) AS sold_once_only, " +
				"SUM(CASE WHEN value < 1000 THEN 1 ELSE 0 END) AS under_1k_sales, " +
				"CAST(SUM(value) AS decimal(18,2)) AS sales FROM sold"

			return runSections(app, []section{
				{"catalogue shape", shape},
				{"revenue bands", bands},
			})
		},
	}
	addDomFilters(c, &f, "date")
	assortMonthsFlag(c, &months)
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// headroom
// ─────────────────────────────────────────────────────────────────────────────

func assortHeadroomCmd(app *App) *cobra.Command {
	var f domFilters
	var months int
	c := &cobra.Command{
		Use:   "headroom",
		Short: "Per counter: SKUs, sales, stock, turns, and how much of the range is dead",
		Long: "Where a new category could physically go. A counter carrying many SKUs that do not move\n" +
			"has shelf to reclaim; a counter with high sales per SKU is working and should be left alone.",
		Example: "  ary assort headroom",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			w := assortWindow(&f, months, "h.VoucherDate")
			whereH := fWhere(strings.TrimPrefix(strings.TrimSpace(w), "AND "))
			mo := months
			if mo <= 0 {
				mo = 12
			}
			q := fmt.Sprintf("WITH sold AS (SELECT d.WarehouseID, d.ProductID, "+
				"SUM(d.Quantity * d.SaleRate) AS value, COUNT(DISTINCT d.SerialNumber) AS bills "+
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber%s "+
				"GROUP BY d.WarehouseID, d.ProductID), "+
				"stk AS (SELECT WarehouseID, COUNT(DISTINCT ProductID) AS skus_stocked, "+
				"SUM(CASE WHEN Quantity > 0 THEN Quantity * PurchaseCost ELSE 0 END) AS stock_at_cost, "+
				"SUM(CASE WHEN Quantity < 0 THEN 1 ELSE 0 END) AS negative_rows FROM Stock GROUP BY WarehouseID) "+
				"SELECT TOP %d wm.WarehouseName AS counter, wm.IsActive AS active, "+
				"ISNULL(stk.skus_stocked, 0) AS skus_stocked, "+
				"ISNULL(sl.skus_sold, 0) AS skus_sold, "+
				"ISNULL(stk.skus_stocked, 0) - ISNULL(sl.skus_sold, 0) AS skus_not_moving, "+
				"CAST(ISNULL(sl.sales, 0) AS decimal(18,2)) AS sales, "+
				"CAST(ISNULL(sl.sales, 0) / NULLIF(sl.skus_sold, 0) AS decimal(18,2)) AS sales_per_moving_sku, "+
				"CAST(ISNULL(stk.stock_at_cost, 0) AS decimal(18,2)) AS stock_at_cost, "+
				"CAST(ISNULL(sl.sales, 0) * 12.0 / %d / NULLIF(stk.stock_at_cost, 0) AS decimal(9,2)) AS turns_yr, "+
				"ISNULL(stk.negative_rows, 0) AS negative_rows "+
				"FROM WarehouseMaster wm "+
				"LEFT JOIN (SELECT WarehouseID, COUNT(*) AS skus_sold, SUM(value) AS sales FROM sold GROUP BY WarehouseID) sl "+
				"ON sl.WarehouseID = wm.WarehouseID "+
				"LEFT JOIN stk ON stk.WarehouseID = wm.WarehouseID "+
				"ORDER BY ISNULL(sl.sales, 0) DESC", whereH, topN(app, 50), mo)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	assortMonthsFlag(c, &months)
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// leak — SKUs sold below what ARY actually paid
// ─────────────────────────────────────────────────────────────────────────────

func assortLeakCmd(app *App) *cobra.Command {
	var months, minUnits int
	c := &cobra.Command{
		Use:   "leak",
		Short: "SKUs sold BELOW the price ARY paid — costed off the purchase ledger, not the price master",
		Long: "Compares each SKU's weighted-average SALE rate against its weighted-average PURCHASE\n" +
			"cost over the same window, both computed from documents rather than from master data.\n\n" +
			"This matters because ProductChildMaster prices go stale. Verified live 2026-08-28: loose\n" +
			"milk's purchase cost rose from Rs 45 to Rs 55 over the year while the retail price stayed\n" +
			"hard-coded at Rs 47.00 across all 16,105 litres — yet the price master still carried the\n" +
			"old Rs 38.83 cost, so every margin report showed that SKU at a healthy +35%. The loss only\n" +
			"appears when you cost it off PurchaseDetail. 27 SKUs were leaking about Rs 3.06 lakh a year.\n\n" +
			"Read the buckets: a sale rate below HALF the purchase cost is usually a pricing or\n" +
			"single-versus-case error at the till, not a policy. A small negative on large volume is\n" +
			"usually a cost rise nobody passed on. Both are worth fixing; only the second is a\n" +
			"judgement call, because a subsidised price to a captive population may be deliberate.",
		Example: "  ary assort leak\n" +
			"  ary assort leak --min-units 100\n" +
			"  ary assort leak --months 6 --csv",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			mo := months
			if mo <= 0 {
				mo = 12
			}
			win := fmt.Sprintf("DATEADD(month, -%d, CAST(GETDATE() AS date))", mo)

			ctes := fmt.Sprintf("WITH pur AS ("+
				"SELECT pd.ProductID, SUM(pd.Quantity) AS qty_b, "+
				"SUM(pd.Quantity * pd.PurchaseCost) / NULLIF(SUM(pd.Quantity), 0) AS cost "+
				"FROM PurchaseDetail pd JOIN PurchaseHeader ph ON ph.SerialNumber = pd.SerialNumber "+
				"WHERE ph.VoucherDate >= %s AND ISNULL(ph.IsDeleted, 0) = 0 "+
				"GROUP BY pd.ProductID), "+
				"sal AS (SELECT d.ProductID, SUM(d.Quantity) AS qty_s, "+
				"SUM(d.Quantity * d.SaleRate) AS rev, "+
				"SUM(d.Quantity * d.SaleRate) / NULLIF(SUM(d.Quantity), 0) AS rate "+
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber "+
				"WHERE h.VoucherDate >= %s GROUP BY d.ProductID) ", win, win)

			where := fmt.Sprintf("WHERE pu.cost > 0 AND s.rate < pu.cost AND s.qty_s > %d", minUnits)

			summary := ctes + "SELECT CASE WHEN s.rate < pu.cost * 0.5 " +
				"THEN '2. sale under HALF cost — likely a pricing/pack error' " +
				"ELSE '1. plausible real below-cost selling' END AS bucket, " +
				"COUNT(*) AS skus, " +
				"CAST(SUM((s.rate - pu.cost) * s.qty_s) AS decimal(18,2)) AS window_loss " +
				"FROM sal s JOIN pur pu ON pu.ProductID = s.ProductID " + where +
				" GROUP BY CASE WHEN s.rate < pu.cost * 0.5 " +
				"THEN '2. sale under HALF cost — likely a pricing/pack error' " +
				"ELSE '1. plausible real below-cost selling' END ORDER BY bucket"

			detail := ctes + fmt.Sprintf("SELECT TOP %d p.ProductName AS product, "+
				"g.ProductGroupName AS product_group, "+
				"CAST(s.qty_s AS decimal(18,2)) AS units_sold, "+
				"CAST(pu.cost AS decimal(18,2)) AS purchase_cost, "+
				"CAST(s.rate AS decimal(18,2)) AS sale_rate, "+
				"CAST(s.rate - pu.cost AS decimal(18,2)) AS per_unit, "+
				"CAST((s.rate - pu.cost) * s.qty_s AS decimal(18,2)) AS window_loss, "+
				"CAST(pcm.PurchaseCost AS decimal(18,2)) AS master_cost, "+
				"u.UnitName AS unit, CAST(p.ConversionFactor AS decimal(9,3)) AS conv "+
				"FROM sal s JOIN pur pu ON pu.ProductID = s.ProductID "+
				"JOIN ProductMaster p ON p.ProductID = s.ProductID "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN UnitMaster u ON u.UnitID = p.UnitID "+
				"LEFT JOIN (SELECT ProductID, MAX(PurchaseCost) AS PurchaseCost "+
				"FROM ProductChildMaster GROUP BY ProductID) pcm ON pcm.ProductID = s.ProductID "+
				"%s ORDER BY (s.rate - pu.cost) * s.qty_s ASC", topN(app, 40), where)

			return runSections(app, []section{
				{fmt.Sprintf("summary (%d-month window, min %d units)", mo, minUnits), summary},
				{"the leaking SKUs — master_cost is what the price master WRONGLY believes", detail},
			})
		},
	}
	assortMonthsFlag(c, &months)
	c.Flags().IntVar(&minUnits, "min-units", 20, "ignore SKUs selling fewer than this many units in the window")
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// probe — does ARY carry this, wherever it happens to be filed?
// ─────────────────────────────────────────────────────────────────────────────


// assortSquash lowercases a term and removes the punctuation and spacing that
// ARY product names are inconsistent about, so "sugar-free", "Sugar Free" and
// "sugarfree" all reduce to the same key.
func assortSquash(t string) string {
	r := strings.NewReplacer("-", "", " ", "", ".", "", "/", "", "'", "", "&", "", ",", "")
	return strings.ToLower(r.Replace(t))
}

// assortSquashSQL applies the same normalisation to a column in T-SQL.
func assortSquashSQL(col string) string {
	for _, ch := range []string{"-", " ", ".", "/", "'", "&", ","} {
		lit := "'" + ch + "'"
		if ch == "'" {
			lit = "''''"
		}
		col = "REPLACE(" + col + ", " + lit + ", '')"
	}
	return col
}

func assortProbeCmd(app *App) *cobra.Command {
	var months int
	var soldOnly bool
	c := &cobra.Command{
		Use:   "probe <term> [term...]",
		Short: "Does ARY carry this? Name-search across EVERY group — the honest coverage test",
		Long: "Use this, not `coverage`, to decide whether a category is actually missing.\n\n" +
			"ARY's category tree cannot be trusted for that question. Verified live 2026-08-28:\n" +
			"Loose Milk is filed under 'Mini Meals', curd under 'Others', khoya under\n" +
			"'Confectionery', fresh peas under 'Fruits', kala chana under 'Atta & Other Flours'.\n" +
			"Name-searching every dairy word finds ₹64.8 L of 12-month sales spread over 14 groups,\n" +
			"with under 15% of it inside 'Dairy Products'. A group that looks empty usually is not.\n\n" +
			"Each term is matched as a case-insensitive substring of the product name. Several terms\n" +
			"are OR-ed, so one probe can cover a whole category's vocabulary. The summary shows which\n" +
			"groups the matches really live in; --sold-only drops SKUs that did not move.\n\n" +
			"Read the result as: matched but not sold = listed, not stocked. No match at all = a real\n" +
			"gap. Matched and selling = ARY has it, wherever the tree filed it.",
		Example: "  ary assort probe paracetamol crocin dolo\n" +
			"  ary assort probe diaper pampers huggies mamypoko\n" +
			"  ary assort probe milk dahi curd paneer butter cheese --sold-only\n" +
			"  ary assort probe charger cable earphone powerbank",
		Args: cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			var likes []string
			for _, a := range args {
				t := strings.TrimSpace(a)
				if t == "" {
					continue
				}
				// Plain match, plus a punctuation- and space-insensitive match.
				//
				// ARY's product names are irregular about punctuation: "Sugar Free"
				// is two words, "Mama Earth" is two words, and 1,116 of 21,479 names
				// carry a hyphen. Probing "sugar-free" or "mamaearth" against a plain
				// LIKE returns ZERO and reads as a gap that is not there. Since probe
				// is the anti-false-gap guard it errs toward recall: a false "covered"
				// is caught by the sales column, a false "missing" is invisible and
				// has already produced five wrong findings in this project.
				likes = append(likes, fLike("p.ProductName", t))
				// Always add the normalised clause: the term may be clean while the
				// COLUMN is not ("mamaearth" vs the stored "Mama Earth"), so gating
				// this on the term changing misses exactly half the cases.
				//
				// But guard it by length. Stripping punctuation makes SHORT terms
				// promiscuous: "pan-d" squashes to "pand" and matches "Meiji Hello
				// Panda Biscuits" and "Pandol", a vegetable. Five characters is the
				// floor at which the normalised match stops inventing hits.
				if n := assortSquash(t); len(n) >= 5 {
					likes = append(likes, "LOWER("+assortSquashSQL("p.ProductName")+") LIKE "+db.Lit("%"+n+"%"))
				}
			}
			if len(likes) == 0 {
				return Usagef("give at least one non-empty search term")
			}
			match := "(" + strings.Join(likes, " OR ") + ")"

			mo := months
			if mo <= 0 {
				mo = 12
			}
			sold := "(SELECT d.ProductID, COUNT(DISTINCT d.SerialNumber) AS bills, " +
				"SUM(d.Quantity) AS qty, SUM(d.Quantity * d.SaleRate) AS value, " +
				"MAX(h.VoucherDate) AS last_sale, AVG(d.SaleRate) AS avg_rate " +
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber " +
				fmt.Sprintf("WHERE h.VoucherDate >= DATEADD(month, -%d, CAST(GETDATE() AS date)) ", mo) +
				"GROUP BY d.ProductID)"

			soldFilter := ""
			if soldOnly {
				soldFilter = " AND sl.ProductID IS NOT NULL"
			}

			verdict := fmt.Sprintf("SELECT COUNT(*) AS skus_matched, "+
				"SUM(CASE WHEN p.IsActive = 1 THEN 1 ELSE 0 END) AS active, "+
				"COUNT(sl.ProductID) AS sold_%dm, "+
				"COUNT(DISTINCT p.ProductGroupID) AS groups_they_live_in, "+
				"CAST(ISNULL(SUM(sl.value), 0) AS decimal(18,2)) AS sales, "+
				"CAST(ISNULL(SUM(sl.value), 0) * 12.0 / %d / %d AS decimal(18,2)) AS per_resident_yr "+
				"FROM ProductMaster p LEFT JOIN %s sl ON sl.ProductID = p.ProductID "+
				"WHERE %s%s", mo, mo, assortResidents, sold, match, soldFilter)

			byGroup := fmt.Sprintf("SELECT g.ProductGroupName AS filed_under, "+
				"sg.SubGroupName AS sub_group, COUNT(*) AS skus, COUNT(sl.ProductID) AS sold, "+
				"CAST(ISNULL(SUM(sl.value), 0) AS decimal(18,2)) AS sales "+
				"FROM ProductMaster p "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN SubGroupMaster sg ON sg.SubGroupID = p.SubGroupID "+
				"LEFT JOIN %s sl ON sl.ProductID = p.ProductID "+
				"WHERE %s%s GROUP BY g.ProductGroupName, sg.SubGroupName "+
				"ORDER BY ISNULL(SUM(sl.value), 0) DESC", sold, match, soldFilter)

			skus := fmt.Sprintf("SELECT TOP %d p.ProductID AS id, p.ProductName AS product, "+
				"g.ProductGroupName AS filed_under, p.IsActive AS active, "+
				"CAST(ISNULL(sl.qty, 0) AS decimal(18,2)) AS qty, "+
				"CAST(ISNULL(sl.value, 0) AS decimal(18,2)) AS sales, "+
				"CAST(ISNULL(sl.avg_rate, 0) AS decimal(18,2)) AS avg_rate, "+
				"CONVERT(varchar(10), sl.last_sale, 120) AS last_sale "+
				"FROM ProductMaster p "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN %s sl ON sl.ProductID = p.ProductID "+
				"WHERE %s%s ORDER BY ISNULL(sl.value, 0) DESC, p.ProductName",
				topN(app, 60), sold, match, soldFilter)

			return runSections(app, []section{
				{fmt.Sprintf("verdict (%d-month window)", mo), verdict},
				{"where these actually live", byGroup},
				{"the SKUs", skus},
			})
		},
	}
	assortMonthsFlag(c, &months)
	c.Flags().BoolVar(&soldOnly, "sold-only", false, "only SKUs that actually sold in the window")
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// benchmark — capture rate against what a household actually spends
// ─────────────────────────────────────────────────────────────────────────────

// assortBenchmark is one row of assort/data/benchmark.json: what a resident of a
// place like Baru Sahib spends on a category in a year, whatever shop they use.
// Populated from published consumption data (MoSPI HCES, category reports) by the
// research run — never invented here.
type assortBenchmark struct {
	Group       string   `json:"group"`       // ARY ProductGroupName, or a group of them
	AryGroups   []string `json:"aryGroups"`   // ARY groups that roll into this benchmark
	PerYearInr  float64  `json:"perYearInr"`  // benchmark spend per resident per year (0 = unknown)
	LinesBench  float64  `json:"linesBenchmark"` // benchmark SKU-line count for this category
	Addressable float64  `json:"addressable"` // 0-1: share a campus shop can realistically win
	Source      string   `json:"source"`      // where the figure came from
	Note        string   `json:"note"`
}

func assortBenchmarkCmd(app *App) *cobra.Command {
	var residents, months int
	var minGap float64
	var spendAxis bool
	c := &cobra.Command{
		Use:   "benchmark",
		Short: "ARY's range and capture vs an external benchmark — how many lines a category should carry",
		Long: "Compares ARY's live position per category against a sourced external benchmark, on two\n" +
			"axes, whichever the benchmark file supplies:\n\n" +
			"  LINES   how many SKU lines a store serving this population should carry, against how\n" +
			"          many ARY lists and how many actually SELL. This is the axis that matters given\n" +
			"          ARY lists 19,481 active SKUs and sells 6,197 — the shortfall is availability,\n" +
			"          not range.\n" +
			"  SPEND   ₹ per resident per year captured against what a resident really spends. The\n" +
			"          gap is wallet leaving campus.\n\n" +
			"Benchmarks live in assort/data/benchmark.json, written by the research run from published\n" +
			"sources (BigBasket/Blinkit category counts pro-rated to population; MoSPI HCES for spend).\n" +
			"Every row carries its source and an 'addressable' fraction — never 100%. A row with\n" +
			"addressable 0 is a structural zero (eggs/meat/fish at a vegetarian institution) and is\n" +
			"excluded from totals rather than counted as a gap.\n\n" +
			"If the file is absent this command says so rather than guessing: an invented benchmark is\n" +
			"worse than no benchmark.",
		Example: "  ary assort benchmark\n" +
			"  ary assort benchmark --spend            # the ₹/resident axis instead of SKU lines\n" +
			"  ary assort benchmark --residents 5000 --csv",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if residents <= 0 {
				return Usagef("--residents must be positive")
			}
			root, err := assortCorpusDir()
			if err != nil {
				return err
			}
			path := filepath.Join(root, "data", "benchmark.json")
			raw, err := os.ReadFile(path)
			if err != nil {
				return fmt.Errorf("no benchmark file at %s\n"+
					"It is written by the assortment research run (the 'wallet' lane) and holds, per\n"+
					"category, what a resident really spends in a year plus the source. Until it exists\n"+
					"use `ary assort coverage` for the per-resident figures on their own", path)
			}
			var marks []assortBenchmark
			if err := json.Unmarshal(raw, &marks); err != nil {
				return fmt.Errorf("%s: %w", path, err)
			}
			if len(marks) == 0 {
				return fmt.Errorf("%s is empty", path)
			}

			// live per-group annualised sales
			mo := months
			if mo <= 0 {
				mo = 12
			}
			// one query serves both axes: per group, annualised sales, active SKUs
			// and SKUs that actually sold in the window
			q := fmt.Sprintf("SELECT g.ProductGroupName AS product_group, "+
				"CAST(ISNULL(SUM(sl.value), 0) * 12.0 / %d AS decimal(18,2)) AS annual_sales, "+
				"SUM(CASE WHEN p.IsActive = 1 THEN 1 ELSE 0 END) AS active_skus, "+
				"COUNT(sl.ProductID) AS sold_skus "+
				"FROM ProductMaster p "+
				"LEFT JOIN ProductGroupMaster g ON g.ProductGroupID = p.ProductGroupID "+
				"LEFT JOIN %s sl ON sl.ProductID = p.ProductID "+
				"GROUP BY g.ProductGroupName", mo,
				assortSoldCTE(fmt.Sprintf(" AND h.VoucherDate >= DATEADD(month, -%d, CAST(GETDATE() AS date))", mo)))

			ctx, cancel := app.Ctx()
			defer cancel()
			res, err := app.DB.Query(ctx, app.DBName(), q)
			if err != nil {
				return err
			}
			num := func(v any) float64 {
				f, _ := strconv.ParseFloat(strings.TrimSpace(fmt.Sprintf("%v", v)), 64)
				return f
			}
			live := map[string]float64{}
			liveActive := map[string]float64{}
			liveSold := map[string]float64{}
			for _, row := range res.Rows {
				if len(row) < 4 || row[0] == nil {
					continue
				}
				k := strings.ToLower(strings.TrimSpace(fmt.Sprintf("%v", row[0])))
				live[k] += num(row[1])
				liveActive[k] += num(row[2])
				liveSold[k] += num(row[3])
			}

			// ── SKU-line axis: the default, because ARY's shortfall is availability ──
			if !spendAxis {
				out := &db.Result{Columns: []string{"category", "benchmark_lines", "ary_active_skus",
					"ary_selling_skus", "selling_vs_benchmark_pct", "listed_vs_benchmark", "verdict", "source"}}
				type lrow struct {
					cat                          string
					bench, active, sold, pct     float64
					listedRatio                  float64
					verdict, src                 string
					structuralZero               bool
				}
				var rows []lrow
				var tb, ta, ts float64
				for _, m := range marks {
					groups := m.AryGroups
					if len(groups) == 0 && m.Group != "" {
						groups = []string{m.Group}
					}
					var act, sld float64
					for _, g := range groups {
						k := strings.ToLower(strings.TrimSpace(g))
						act += liveActive[k]
						sld += liveSold[k]
					}
					zero := m.Addressable == 0
					pct, ratio := 0.0, 0.0
					if m.LinesBench > 0 {
						pct = 100 * sld / m.LinesBench
						ratio = act / m.LinesBench
					}
					v := ""
					switch {
					case zero:
						v = "structural zero — excluded"
					case m.LinesBench == 0:
						v = "no line benchmark"
					case len(m.AryGroups) == 0:
						v = "NO ARY GROUP EXISTS"
					case pct < 25:
						v = "severe range gap"
					case pct < 60:
						v = "range gap"
					case ratio > 2.5:
						v = "over-listed, under-stocked"
					default:
						v = "adequate"
					}
					name := m.Group
					if name == "" && len(groups) > 0 {
						name = strings.Join(groups, "+")
					}
					if !zero {
						tb += m.LinesBench
						ta += act
						ts += sld
					}
					rows = append(rows, lrow{name, m.LinesBench, act, sld, pct, ratio, v, m.Source, zero})
				}
				sort.Slice(rows, func(i, j int) bool {
					if rows[i].structuralZero != rows[j].structuralZero {
						return !rows[i].structuralZero
					}
					return rows[i].pct < rows[j].pct
				})
				for _, r := range rows {
					out.Rows = append(out.Rows, []any{r.cat,
						fmt.Sprintf("%.0f", r.bench), fmt.Sprintf("%.0f", r.active),
						fmt.Sprintf("%.0f", r.sold), fmt.Sprintf("%.1f", r.pct),
						fmt.Sprintf("%.2fx", r.listedRatio), r.verdict, r.src})
				}
				totPct, totRatio := 0.0, 0.0
				if tb > 0 {
					totPct = 100 * ts / tb
					totRatio = ta / tb
				}
				out.Rows = append(out.Rows, []any{"— TOTAL (structural zeros excluded) —",
					fmt.Sprintf("%.0f", tb), fmt.Sprintf("%.0f", ta), fmt.Sprintf("%.0f", ts),
					fmt.Sprintf("%.1f", totPct), fmt.Sprintf("%.2fx", totRatio),
					"", fmt.Sprintf("%d rows, %d-month window", len(rows), mo)})
				return app.Render(out)
			}

			out := &db.Result{Columns: []string{"category", "ary_per_resident_yr", "benchmark_per_resident_yr",
				"addressable_yr", "capture_pct", "annual_gap_inr", "source"}}
			type row struct {
				cat                       string
				ary, bench, addr, cap, gp float64
				src                       string
			}
			var rows []row
			for _, m := range marks {
				groups := m.AryGroups
				if len(groups) == 0 && m.Group != "" {
					groups = []string{m.Group}
				}
				var arySales float64
				for _, g := range groups {
					arySales += live[strings.ToLower(strings.TrimSpace(g))]
				}
				aryPer := arySales / float64(residents)
				addr := m.Addressable
				if addr <= 0 || addr > 1 {
					addr = 1
				}
				target := m.PerYearInr * addr
				capPct := 0.0
				if target > 0 {
					capPct = 100 * aryPer / target
				}
				gap := (target - aryPer) * float64(residents)
				if gap < 0 {
					gap = 0
				}
				name := m.Group
				if name == "" && len(groups) > 0 {
					name = strings.Join(groups, "+")
				}
				rows = append(rows, row{name, aryPer, m.PerYearInr, target, capPct, gap, m.Source})
			}
			sort.Slice(rows, func(i, j int) bool { return rows[i].gp > rows[j].gp })
			var totalGap float64
			for _, r := range rows {
				totalGap += r.gp
				if r.gp < minGap {
					continue
				}
				out.Rows = append(out.Rows, []any{r.cat,
					fmt.Sprintf("%.0f", r.ary), fmt.Sprintf("%.0f", r.bench),
					fmt.Sprintf("%.0f", r.addr), fmt.Sprintf("%.1f", r.cap),
					fmt.Sprintf("%.0f", r.gp), r.src})
			}
			out.Rows = append(out.Rows, []any{"— TOTAL ADDRESSABLE GAP —", "", "", "", "",
				fmt.Sprintf("%.0f", totalGap), fmt.Sprintf("%d rows, %d residents", len(rows), residents)})
			return app.Render(out)
		},
	}
	assortResidentsFlag(c, &residents)
	assortMonthsFlag(c, &months)
	c.Flags().Float64Var(&minGap, "min-gap", 0, "hide categories whose annual ₹ gap is below this (spend axis only)")
	c.Flags().BoolVar(&spendAxis, "spend", false, "report the ₹/resident/year capture axis instead of SKU lines")
	return c
}

// ─────────────────────────────────────────────────────────────────────────────
// research corpus
// ─────────────────────────────────────────────────────────────────────────────

// assortCorpusDir resolves where the research JSON lives. $ARY_ASSORT_DIR wins,
// then ./assort, then <dir of the ary binary>/assort.
func assortCorpusDir() (string, error) {
	if d := strings.TrimSpace(os.Getenv("ARY_ASSORT_DIR")); d != "" {
		if st, err := os.Stat(d); err == nil && st.IsDir() {
			return d, nil
		}
		return "", fmt.Errorf("ARY_ASSORT_DIR=%q is not a directory", d)
	}
	var tried []string
	if wd, err := os.Getwd(); err == nil {
		tried = append(tried, filepath.Join(wd, "assort"))
	}
	if exe, err := os.Executable(); err == nil {
		if p, err := filepath.EvalSymlinks(exe); err == nil {
			exe = p
		}
		tried = append(tried, filepath.Join(filepath.Dir(exe), "assort"))
	}
	for _, d := range tried {
		if st, err := os.Stat(d); err == nil && st.IsDir() {
			return d, nil
		}
	}
	return "", fmt.Errorf("no research corpus found (looked in %s)\n"+
		"set ARY_ASSORT_DIR, or run from the ary-cli directory", strings.Join(tried, ", "))
}

// assortDemand is one category's ideal-assortment research (stage 1).
type assortDemand struct {
	Category     string `json:"category"`
	CategoryName string `json:"categoryName"`
	SKULines     []struct {
		Line         string `json:"line"`
		Examples     string `json:"examples"`
		PackSizes    string `json:"packSizes"`
		PriceBand    string `json:"priceBand"`
		Cohort       string `json:"cohort"`
		Essentiality string `json:"essentiality"`
		Frequency    string `json:"frequency"`
		Seasonality  string `json:"seasonality"`
		MarginBand   string `json:"marginBand"`
		Notes        string `json:"notes"`
	} `json:"skuLines"`
	Trends2026 []string `json:"trends2026"`
}

// assortCoverage is one category's diff against ARY's live catalogue (stage 2).
type assortCoverageDoc struct {
	Category    string  `json:"category"`
	ActiveSKUs  float64 `json:"aryActiveSkusInCategory"`
	Sales12m    float64 `json:"arySales12mInr"`
	CoveragePct float64 `json:"coveragePct"`
	CommodityPct float64 `json:"commodityOnlyPct"`
	Lines        []struct {
		Line     string `json:"line"`
		State    string `json:"state"`
		Quality  string `json:"matchQuality"`
		Ess      string `json:"essentiality"`
		Examples string `json:"arySkuExamples"`
		Sales    float64 `json:"arySales12m"`
		Evidence string `json:"evidence"`
	} `json:"lines"`
	Surprises []string `json:"surprises"`
}

// assortPriorityDoc is one category's ranked recommendation (stage 3).
type assortPriorityDoc struct {
	Category        string `json:"category"`
	Headline        string `json:"headline"`
	Confidence      string `json:"confidence"`
	Recommendations []struct {
		Line          string  `json:"line"`
		Priority      string  `json:"priority"`
		State         string  `json:"state"`
		WhyItMatters  string  `json:"whyItMatters"`
		Assumption    string  `json:"assumption"`
		MonthlyRev    float64 `json:"monthlyRevenueInr"`
		MarginPct     float64 `json:"marginPct"`
		MonthlyProfit float64 `json:"monthlyGrossProfitInr"`
		Feasibility   string  `json:"feasibility"`
		Blocker       string  `json:"blocker"`
	} `json:"recommendations"`
	TotalMonthlyRev    float64 `json:"categoryTotalMonthlyRevenueInr"`
	TotalMonthlyProfit float64 `json:"categoryTotalMonthlyGrossProfitInr"`
}

// assortSweepDoc is one intelligence lane (population, wallet, leakage, …).
type assortSweepDoc struct {
	Lane     string `json:"lane"`
	Headline string `json:"headline"`
	Findings []struct {
		Claim    string `json:"claim"`
		Status   string `json:"status"`
		Evidence string `json:"evidence"`
		Number   string `json:"number"`
		SoWhat   string `json:"soWhat"`
	} `json:"findings"`
	Recommendations []struct {
		Action        string  `json:"action"`
		Priority      string  `json:"priority"`
		MonthlyImpact float64 `json:"monthlyImpactInr"`
		Effort        string  `json:"effort"`
		Blocker       string  `json:"blocker"`
	} `json:"recommendations"`
	Confidence    string `json:"confidence"`
	ConfidenceGap string `json:"confidenceGap"`
}

// assortLoad reads every *.json in <corpus>/research/<sub> into T.
func assortLoad[T any](sub string) ([]T, string, error) {
	root, err := assortCorpusDir()
	if err != nil {
		return nil, "", err
	}
	dir := filepath.Join(root, "research", sub)
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, dir, fmt.Errorf("no %s corpus yet at %s — the research run has not written it", sub, dir)
	}
	var out []T
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		b, err := os.ReadFile(filepath.Join(dir, e.Name()))
		if err != nil {
			return nil, dir, err
		}
		var v T
		if err := json.Unmarshal(b, &v); err != nil {
			return nil, dir, fmt.Errorf("%s: %w", e.Name(), err)
		}
		out = append(out, v)
	}
	if len(out) == 0 {
		return nil, dir, fmt.Errorf("no %s corpus files in %s", sub, dir)
	}
	return out, dir, nil
}

func assortResearchCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "research",
		Short: "Status of the research corpus — which categories are researched, diffed and ranked",
		Long: "The corpus is JSON written by the assortment research runs under assort/research/:\n" +
			"  demand/    the ideal assortment per category, built blind to ARY\n" +
			"  coverage/  that list diffed against ARY's live SKUs\n" +
			"  priority/  the ranked, rupee-sized recommendation\n" +
			"  sweep/     the surrounding intelligence lanes (population, wallet, leakage, …)\n" +
			"This command says what is present, so a half-finished run is obvious.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			root, err := assortCorpusDir()
			if err != nil {
				return err
			}
			res := &db.Result{Columns: []string{"stage", "files", "path"}}
			for _, sub := range []string{"demand", "coverage", "priority", "sweep"} {
				dir := filepath.Join(root, "research", sub)
				n := 0
				if entries, err := os.ReadDir(dir); err == nil {
					for _, e := range entries {
						if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
							n++
						}
					}
				}
				res.Rows = append(res.Rows, []any{sub, n, dir})
			}

			secs := []*db.Result{res}
			if docs, _, err := assortLoad[assortCoverageDoc]("coverage"); err == nil {
				cov := &db.Result{Columns: []string{"category", "lines", "line_match", "commodity_only",
					"dormant", "missing", "line_coverage_pct"}}
				sort.Slice(docs, func(i, j int) bool { return docs[i].CoveragePct < docs[j].CoveragePct })
				for _, d := range docs {
					var spec, broad, dm, ms int
					for _, l := range d.Lines {
						switch strings.ToLower(l.State) {
						case "covered":
							// a broad match proves ARY is in the commodity, not that this
							// pack/grade is stocked -- keep the two apart or every food
							// category reads as fully covered
							if strings.EqualFold(l.Quality, "specific") {
								spec++
							} else {
								broad++
							}
						case "dormant":
							dm++
						case "missing":
							ms++
						}
					}
					cov.Rows = append(cov.Rows, []any{d.Category, len(d.Lines),
						spec, broad, dm, ms, d.CoveragePct})
				}
				secs = append(secs, cov)
			}
			return assortRenderMulti(app, []string{"corpus", "coverage by category (worst first)"}, secs)
		},
	}
	return c
}

func assortGapsCmd(app *App) *cobra.Command {
	var category, state string
	c := &cobra.Command{
		Use:   "gaps",
		Short: "Every SKU line the research says ARY should carry and does not",
		Long: "Reads the coverage corpus. --state selects what to show:\n" +
			"  missing    no ARY product name matches, specific or broad. The real finding.\n" +
			"  dormant    a SKU exists but sold nothing, or under the floor. Listed, not stocked.\n" +
			"  commodity  only the commodity word matched -- ARY is IN the line, but this pack,\n" +
			"             grade or brand is unproven. Worth a buyer's eye.\n" +
			"  covered    a match of any quality.\n\n" +
			"With no --state the default shows everything that is NOT a solid line-level match,\n" +
			"i.e. missing + dormant + commodity-only.\n\n" +
			"Before acting on a 'missing', re-check it with `ary assort probe <commodity words>`,\n" +
			"passing SINGLE words rather than phrases. The first version of the diff called arhar\n" +
			"dal and almonds missing while ARY was selling Rs 8.7 lakh of them.",
		Example: "  ary assort gaps\n" +
			"  ary assort gaps --state missing --category pharmacy-otc\n" +
			"  ary assort gaps --csv > gaps.csv",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			docs, _, err := assortLoad[assortCoverageDoc]("coverage")
			if err != nil {
				return err
			}
			want := strings.ToLower(strings.TrimSpace(state))
			res := &db.Result{Columns: []string{"category", "state", "match", "essentiality",
				"line", "ary_sales_12m", "evidence"}}
			for _, d := range docs {
				if category != "" && !strings.EqualFold(d.Category, category) {
					continue
				}
				for _, l := range d.Lines {
					st := strings.ToLower(l.State)
					switch want {
					case "":
						// default view: everything that is NOT a solid line-level match
						if st == "covered" && strings.EqualFold(l.Quality, "specific") {
							continue
						}
					case "commodity":
						if st != "covered" || strings.EqualFold(l.Quality, "specific") {
							continue
						}
					default:
						if st != want {
							continue
						}
					}
					res.Rows = append(res.Rows, []any{d.Category, st, l.Quality, l.Ess,
						l.Line, fmt.Sprintf("%.0f", l.Sales), l.Evidence})
				}
			}
			if len(res.Rows) == 0 {
				return fmt.Errorf("no gaps matched (category=%q state=%q)", category, state)
			}
			if app.Flags.Limit > 0 && len(res.Rows) > app.Flags.Limit {
				res.Rows = res.Rows[:app.Flags.Limit]
			}
			return app.Render(res)
		},
	}
	c.Flags().StringVar(&category, "category", "", "restrict to one research category key (see `ary assort research`)")
	c.Flags().StringVar(&state, "state", "", "missing | dormant | commodity | covered (default: all but solid matches)")
	return c
}

func assortPriorityCmd(app *App) *cobra.Command {
	var category, priority, feasibility string
	var byCategory bool
	c := &cobra.Command{
		Use:   "priority",
		Short: "The ranked build order — what to add first, sized in rupees a month",
		Long: "Reads the priority corpus. monthly_rev and monthly_profit are ESTIMATES built from a\n" +
			"stated penetration assumption against ~5,000 residents; the assumption travels with every\n" +
			"row so it can be argued with. Sort order is P0 first, then by monthly gross profit.",
		Example: "  ary assort priority\n" +
			"  ary assort priority --p P0\n" +
			"  ary assort priority --by-category\n" +
			"  ary assort priority --feasibility easy",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			docs, _, err := assortLoad[assortPriorityDoc]("priority")
			if err != nil {
				return err
			}
			if byCategory {
				res := &db.Result{Columns: []string{"category", "recos", "p0", "monthly_rev", "monthly_profit", "confidence", "headline"}}
				sort.Slice(docs, func(i, j int) bool { return docs[i].TotalMonthlyProfit > docs[j].TotalMonthlyProfit })
				var tr, tp float64
				for _, d := range docs {
					p0 := 0
					for _, r := range d.Recommendations {
						if strings.EqualFold(r.Priority, "P0") {
							p0++
						}
					}
					tr += d.TotalMonthlyRev
					tp += d.TotalMonthlyProfit
					res.Rows = append(res.Rows, []any{d.Category, len(d.Recommendations), p0,
						d.TotalMonthlyRev, d.TotalMonthlyProfit, d.Confidence, d.Headline})
				}
				res.Rows = append(res.Rows, []any{"— TOTAL —", nil, nil, tr, tp, "", ""})
				return app.Render(res)
			}

			type row struct {
				cat, line, pri, state, why, assume, feas, blocker string
				rev, margin, profit                               float64
			}
			var rows []row
			for _, d := range docs {
				if category != "" && !strings.EqualFold(d.Category, category) {
					continue
				}
				for _, r := range d.Recommendations {
					if priority != "" && !strings.EqualFold(r.Priority, priority) {
						continue
					}
					if feasibility != "" && !strings.Contains(strings.ToLower(r.Feasibility), strings.ToLower(feasibility)) {
						continue
					}
					rows = append(rows, row{d.Category, r.Line, strings.ToUpper(r.Priority), r.State,
						r.WhyItMatters, r.Assumption, r.Feasibility, r.Blocker,
						r.MonthlyRev, r.MarginPct, r.MonthlyProfit})
				}
			}
			if len(rows) == 0 {
				return fmt.Errorf("no recommendations matched (category=%q priority=%q feasibility=%q)",
					category, priority, feasibility)
			}
			sort.SliceStable(rows, func(i, j int) bool {
				pi, pj := assortPriRank(rows[i].pri), assortPriRank(rows[j].pri)
				if pi != pj {
					return pi < pj
				}
				return rows[i].profit > rows[j].profit
			})
			if app.Flags.Limit > 0 && len(rows) > app.Flags.Limit {
				rows = rows[:app.Flags.Limit]
			}
			res := &db.Result{Columns: []string{"p", "category", "line", "state", "monthly_rev",
				"margin_pct", "monthly_profit", "feasibility", "blocker", "why", "assumption"}}
			for _, r := range rows {
				res.Rows = append(res.Rows, []any{r.pri, r.cat, r.line, r.state, r.rev,
					r.margin, r.profit, r.feas, r.blocker, r.why, r.assume})
			}
			return app.Render(res)
		},
	}
	c.Flags().StringVar(&category, "category", "", "restrict to one research category key")
	c.Flags().StringVar(&priority, "p", "", "restrict to P0 | P1 | P2 | P3")
	c.Flags().StringVar(&feasibility, "feasibility", "", "substring match: easy | needs-supplier | needs-licence | needs-cold-chain | hard")
	c.Flags().BoolVar(&byCategory, "by-category", false, "one row per category with its totals")
	return c
}

func assortPriRank(p string) int {
	switch strings.ToUpper(strings.TrimSpace(p)) {
	case "P0":
		return 0
	case "P1":
		return 1
	case "P2":
		return 2
	case "P3":
		return 3
	}
	return 9
}

func assortSweepCmd(app *App) *cobra.Command {
	var lane string
	var recos bool
	c := &cobra.Command{
		Use:   "sweep",
		Short: "The intelligence lanes — population, wallet, leakage, benchmarks, internal diagnostics",
		Long: "Reads the sweep corpus. Every finding carries its own status: VERIFIED (a query was run\n" +
			"or a source read), ESTIMATED (derived), or NOT-CHECKED. Read the status column before\n" +
			"quoting a number.",
		Example: "  ary assort sweep\n" +
			"  ary assort sweep --lane population\n" +
			"  ary assort sweep --recommendations",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			docs, _, err := assortLoad[assortSweepDoc]("sweep")
			if err != nil {
				return err
			}
			if recos {
				res := &db.Result{Columns: []string{"p", "lane", "action", "monthly_impact", "effort", "blocker"}}
				type r struct {
					lane, action, pri, effort, blocker string
					impact                             float64
				}
				var all []r
				for _, d := range docs {
					if lane != "" && !strings.EqualFold(d.Lane, lane) {
						continue
					}
					for _, x := range d.Recommendations {
						all = append(all, r{d.Lane, x.Action, strings.ToUpper(x.Priority), x.Effort, x.Blocker, x.MonthlyImpact})
					}
				}
				sort.SliceStable(all, func(i, j int) bool {
					pi, pj := assortPriRank(all[i].pri), assortPriRank(all[j].pri)
					if pi != pj {
						return pi < pj
					}
					return all[i].impact > all[j].impact
				})
				if app.Flags.Limit > 0 && len(all) > app.Flags.Limit {
					all = all[:app.Flags.Limit]
				}
				for _, x := range all {
					res.Rows = append(res.Rows, []any{x.pri, x.lane, x.action, x.impact, x.effort, x.blocker})
				}
				return app.Render(res)
			}

			if lane != "" {
				for _, d := range docs {
					if !strings.EqualFold(d.Lane, lane) {
						continue
					}
					res := &db.Result{Columns: []string{"status", "claim", "number", "so_what", "evidence"}}
					for _, f := range d.Findings {
						res.Rows = append(res.Rows, []any{f.Status, f.Claim, f.Number, f.SoWhat, f.Evidence})
					}
					if !app.Flags.Quiet && !app.Flags.JSON && !app.Flags.CSV {
						fmt.Fprintf(os.Stdout, "%s — %s\n(confidence: %s; gap: %s)\n\n",
							strings.ToUpper(d.Lane), d.Headline, d.Confidence, d.ConfidenceGap)
					}
					return app.Render(res)
				}
				return fmt.Errorf("no sweep lane named %q — run `ary assort sweep` for the list", lane)
			}

			res := &db.Result{Columns: []string{"lane", "findings", "verified", "recos", "confidence", "headline"}}
			sort.Slice(docs, func(i, j int) bool { return docs[i].Lane < docs[j].Lane })
			for _, d := range docs {
				v := 0
				for _, f := range d.Findings {
					if strings.EqualFold(f.Status, "VERIFIED") {
						v++
					}
				}
				res.Rows = append(res.Rows, []any{d.Lane, len(d.Findings), v,
					len(d.Recommendations), d.Confidence, d.Headline})
			}
			return app.Render(res)
		},
	}
	c.Flags().StringVar(&lane, "lane", "", "show one lane's findings in full")
	c.Flags().BoolVar(&recos, "recommendations", false, "every lane's recommendations, ranked")
	return c
}

// assortRenderMulti renders several locally-built results as labelled sections,
// mirroring runSections but for data that did not come from a single query.
func assortRenderMulti(app *App, names []string, results []*db.Result) error {
	if app.Flags.JSON || app.Flags.Compact {
		out := make(map[string]any, len(results))
		for i, r := range results {
			name := strconv.Itoa(i)
			if i < len(names) {
				name = names[i]
			}
			out[name] = assortMaps(r)
		}
		return assortWriteJSON(out, app.Flags.Compact)
	}
	for i, r := range results {
		if i > 0 {
			fmt.Fprintln(os.Stdout)
		}
		if !app.Flags.Quiet && !app.Flags.CSV && i < len(names) {
			fmt.Fprintf(os.Stdout, "== %s ==\n", strings.ToUpper(names[i]))
		}
		if err := app.Render(r); err != nil {
			return err
		}
	}
	return nil
}

func assortMaps(res *db.Result) []map[string]any {
	out := make([]map[string]any, 0, len(res.Rows))
	for _, row := range res.Rows {
		m := make(map[string]any, len(res.Columns))
		for i, c := range res.Columns {
			if i < len(row) {
				m[c] = row[i]
			}
		}
		out = append(out, m)
	}
	return out
}

func assortWriteJSON(v any, compact bool) error {
	enc := json.NewEncoder(os.Stdout)
	if !compact {
		enc.SetIndent("", "  ")
	}
	return enc.Encode(v)
}
