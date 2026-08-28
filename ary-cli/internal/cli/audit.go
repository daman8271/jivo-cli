package cli

// Audit — the physical stock count trail, and the variance the system recorded
// from it. This is the module an internal stock audit actually needs.
//
// How FusionERP8 records a count:
//   PhysicalStockHeader/Detail hold what was COUNTED (per warehouse, per SKU),
//   and posting the count moves the difference into the Stock table's Sho
//   (shortage), Exc (excess) and Was (wastage) buckets. So:
//     - `ary audit counts`     = the count documents themselves
//     - `ary audit variance`   = Sho/Exc/Was by warehouse, the posted difference
//     - `ary audit shortage`   = the SKUs that lost the most, valued at cost
//   Sho/Exc/Was are cumulative since the books began, not per count.

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newAuditCmd) }

func newAuditCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "audit",
		Short:   "Physical stock counts and the shortage/excess/wastage they posted",
		Aliases: []string{"count-audit", "physical"},
	}
	c.AddCommand(auditCountsCmd(app), auditCountCmd(app), auditVarianceCmd(app),
		auditShortageCmd(app), auditUncountedCmd(app))
	return c
}

func auditCountsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "counts",
		Short:   "Physical count documents — when, which warehouse, how much was counted",
		Example: "  ary audit counts --from 2026-08-01\n  ary audit counts --warehouse 10 -n 30",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d h.SerialNumber AS serial, CONVERT(varchar(16), h.VoucherDate, 120) AS date, "+
				"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS doc_no, w.WarehouseName AS warehouse, "+
				"(SELECT COUNT(*) FROM PhysicalStockDetail d WHERE d.SerialNumber = h.SerialNumber) AS lines_, "+
				"CAST(h.QtyTotal AS decimal(18,2)) AS counted_qty, CAST(h.PCostTotal AS decimal(18,2)) AS value_at_cost, "+
				"CAST(h.SRateTotal AS decimal(18,2)) AS value_at_sale_rate, u.UserName AS counted_by, "+
				"CONVERT(varchar(16), h.RecordDateTime, 120) AS entered_at, h.Narration AS narration "+
				"FROM PhysicalStockHeader h "+
				"LEFT JOIN WarehouseMaster w ON w.WarehouseID = h.WarehouseID "+
				"LEFT JOIN UserMaster u ON u.UserID = h.UserID%s "+
				"ORDER BY h.VoucherDate DESC, h.SerialNumber DESC", topN(app, 40),
				fWhere(fDateGE("h.VoucherDate", f.From), fDateLT("h.VoucherDate", f.To),
					fEqInt("h.WarehouseID", f.Warehouse)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "warehouse")
	return c
}

func auditCountCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "count <SerialNumber>",
		Short:   "One physical count in full: header and every counted line",
		Example: "  ary audit count 2835",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			sn := db.Lit(args[0])
			return runSections(app, []section{
				{"header", "SELECT h.SerialNumber AS serial, CONVERT(varchar(16), h.VoucherDate, 120) AS date, " +
					"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS doc_no, w.WarehouseName AS warehouse, " +
					"CAST(h.QtyTotal AS decimal(18,2)) AS counted_qty, CAST(h.PCostTotal AS decimal(18,2)) AS value_at_cost, " +
					"u.UserName AS counted_by, CONVERT(varchar(16), h.RecordDateTime, 120) AS entered_at, h.Narration AS narration " +
					"FROM PhysicalStockHeader h " +
					"LEFT JOIN WarehouseMaster w ON w.WarehouseID = h.WarehouseID " +
					"LEFT JOIN UserMaster u ON u.UserID = h.UserID WHERE h.SerialNumber = " + sn},
				{"counted lines", "SELECT d.SrlNo AS line, d.ProductID AS id, p.ProductName AS product, d.ChildID AS child, " +
					"CAST(d.Quantity AS decimal(18,3)) AS counted_qty, CAST(d.PurchaseCost AS decimal(18,2)) AS purchase_cost, " +
					"CAST(d.PCostAmount AS decimal(18,2)) AS value_at_cost, CAST(d.SaleRate AS decimal(18,2)) AS sale_rate " +
					"FROM PhysicalStockDetail d LEFT JOIN ProductMaster p ON p.ProductID = d.ProductID " +
					"WHERE d.SerialNumber = " + sn + " ORDER BY d.SrlNo"},
			})
		},
	}
}

func auditVarianceCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "variance",
		Short: "Posted shortage / excess / wastage by warehouse, in units and at cost",
		Long: "This is the difference the counts actually booked: Sho, Exc and Was in the Stock table.\n" +
			"Cumulative since the books began (2023-04-01), not per count. net_variance is\n" +
			"excess minus shortage minus wastage — negative means stock went missing overall.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT w.WarehouseName AS warehouse, " +
				"CAST(SUM(s.Sho) AS decimal(18,2)) AS shortage_qty, " +
				"CAST(SUM(s.Sho * s.PurchaseCost) AS decimal(18,2)) AS shortage_at_cost, " +
				"CAST(SUM(s.Exc) AS decimal(18,2)) AS excess_qty, " +
				"CAST(SUM(s.Exc * s.PurchaseCost) AS decimal(18,2)) AS excess_at_cost, " +
				"CAST(SUM(s.Was) AS decimal(18,2)) AS wastage_qty, " +
				"CAST(SUM(s.Was * s.PurchaseCost) AS decimal(18,2)) AS wastage_at_cost, " +
				"CAST(SUM(s.Exc - s.Sho - s.Was) AS decimal(18,2)) AS net_variance_qty, " +
				"CAST(SUM((s.Exc - s.Sho - s.Was) * s.PurchaseCost) AS decimal(18,2)) AS net_variance_at_cost " +
				"FROM Stock s LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID " +
				"GROUP BY w.WarehouseName ORDER BY shortage_at_cost DESC"
			return runSelect(app, q)
		},
	}
	return c
}

func auditShortageCmd(app *App) *cobra.Command {
	var f domFilters
	var kind string
	c := &cobra.Command{
		Use:   "shortage",
		Short: "The SKUs that lost the most stock, valued at cost (--kind shortage|excess|wastage)",
		Example: "  ary audit shortage -n 40\n" +
			"  ary audit shortage --warehouse 12\n" +
			"  ary audit shortage --kind wastage",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			col, ok := map[string]string{"shortage": "Sho", "excess": "Exc", "wastage": "Was"}[kind]
			if !ok {
				return Usagef("--kind must be one of: shortage, excess, wastage")
			}
			q := fmt.Sprintf("SELECT TOP %d s.ProductID AS id, p.ProductName AS product, w.WarehouseName AS warehouse, "+
				"CAST(SUM(s.%s) AS decimal(18,2)) AS %s_qty, "+
				"CAST(SUM(s.%s * s.PurchaseCost) AS decimal(18,2)) AS %s_at_cost, "+
				"CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, CAST(MAX(s.PurchaseCost) AS decimal(18,2)) AS purchase_cost "+
				"FROM Stock s "+
				"LEFT JOIN ProductMaster p ON p.ProductID = s.ProductID "+
				"LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID%s "+
				"GROUP BY s.ProductID, p.ProductName, w.WarehouseName "+
				"HAVING SUM(s.%s) > 0 ORDER BY %s_at_cost DESC",
				topN(app, 40), col, kind, col, kind, stockWhere(&f), col, kind)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "warehouse", "product", "search")
	c.Flags().StringVar(&kind, "kind", "shortage", "which bucket: shortage | excess | wastage")
	return c
}

func auditUncountedCmd(app *App) *cobra.Command {
	var months int
	c := &cobra.Command{
		Use:   "uncounted",
		Short: "Warehouses and their last count date — what has not been counted lately",
		Long: "A warehouse holding stock that has not been physically counted in months is where an\n" +
			"audit finds the surprises. months_since_count is NULL when it has never been counted.",
		Example: "  ary audit uncounted --months 6",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT w.WarehouseID AS id, w.WarehouseName AS warehouse, "+
				"CAST(SUM(CASE WHEN s.Quantity > 0 THEN s.Quantity * s.PurchaseCost ELSE 0 END) AS decimal(18,2)) AS stock_at_cost, "+
				"CONVERT(varchar(10), MAX(pc.last_count), 120) AS last_count, "+
				"DATEDIFF(month, MAX(pc.last_count), GETDATE()) AS months_since_count, MAX(pc.counts) AS counts_ever "+
				"FROM WarehouseMaster w "+
				"LEFT JOIN Stock s ON s.WarehouseID = w.WarehouseID "+
				"LEFT JOIN (SELECT WarehouseID, MAX(VoucherDate) AS last_count, COUNT(*) AS counts "+
				"FROM PhysicalStockHeader GROUP BY WarehouseID) pc ON pc.WarehouseID = w.WarehouseID "+
				"GROUP BY w.WarehouseID, w.WarehouseName "+
				"HAVING MAX(pc.last_count) IS NULL OR MAX(pc.last_count) < DATEADD(month, -%d, GETDATE()) "+
				"ORDER BY stock_at_cost DESC", months)
			return runSelect(app, q)
		},
	}
	c.Flags().IntVar(&months, "months", 3, "flag warehouses not counted within this many months")
	return c
}
