package cli

// Stock — the Stock table is FusionERP8's per-(product, child, warehouse) ledger
// of movement buckets, and Stock.Quantity is the system's own on-hand.
//
// PROVEN IDENTITY (104,221 of 104,221 rows, 2026-08-27):
//   Quantity = OP + Pur - PR - Sal + SR + Prod - Cons + TrIn - TrOut + Exc - Sho - Was
// The challan buckets (PurCh/PRCh/SalCh/SRCh) are zero throughout.
//
// So a negative Quantity is REAL DATA, not a query artefact: that counter billed
// stock it was never shown receiving. `ary stock negative` is the list of them.
// Do NOT use ProductMaster.QuantityOnHand — non-zero on exactly one SKU.

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() { register(newStockCmd) }

func newStockCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "stock",
		Short:   "Stock — on-hand by warehouse/SKU, movement buckets, negatives, dead stock, transfers, journals",
		Aliases: []string{"inventory"},
	}
	c.AddCommand(stockSummaryCmd(app), stockListCmd(app), stockMovementCmd(app), stockNegativeCmd(app),
		stockDeadCmd(app), stockValueCmd(app), stockTransfersCmd(app), stockJournalsCmd(app))
	return c
}

func stockWhere(f *domFilters) string {
	return fWhere(
		fEqInt("s.WarehouseID", f.Warehouse),
		fEqStr("s.ProductID", f.Product),
		fLike("p.ProductName", f.Search),
	)
}

func stockSummaryCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "summary",
		Short: "One row per warehouse: SKUs, on-hand, and the movement buckets behind it",
		Long: "book_qty is Stock.Quantity. The remaining columns are the buckets that produce it, so a\n" +
			"strange on-hand can be traced to the movement type responsible without another query.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT w.WarehouseName AS warehouse, COUNT(DISTINCT s.ProductID) AS skus, " +
				"CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, CAST(SUM(s.OP) AS decimal(18,2)) AS opening, " +
				"CAST(SUM(s.Pur) AS decimal(18,2)) AS purchased, CAST(SUM(s.Sal) AS decimal(18,2)) AS sold, " +
				"CAST(SUM(s.SR) AS decimal(18,2)) AS sale_returns, CAST(SUM(s.Prod) AS decimal(18,2)) AS produced, " +
				"CAST(SUM(s.Cons) AS decimal(18,2)) AS consumed, CAST(SUM(s.TrIn) AS decimal(18,2)) AS transfer_in, " +
				"CAST(SUM(s.TrOut) AS decimal(18,2)) AS transfer_out, CAST(SUM(s.Sho) AS decimal(18,2)) AS shortage, " +
				"CAST(SUM(s.Exc) AS decimal(18,2)) AS excess, CAST(SUM(s.Was) AS decimal(18,2)) AS wastage " +
				"FROM Stock s LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID " +
				"GROUP BY w.WarehouseName ORDER BY book_qty DESC"
			return runSelect(app, q)
		},
	}
	return c
}

func stockListCmd(app *App) *cobra.Command {
	var f domFilters
	var nonZero bool
	c := &cobra.Command{
		Use:     "list",
		Short:   "On-hand by SKU (and warehouse), with valuation at purchase cost",
		Example: "  ary stock list --warehouse 10 -n 50\n  ary stock list --search \"maggi\"",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			having := ""
			if nonZero {
				having = " HAVING SUM(s.Quantity) <> 0"
			}
			q := fmt.Sprintf("SELECT TOP %d s.ProductID AS id, p.ProductName AS product, w.WarehouseName AS warehouse, "+
				"CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, CAST(MAX(s.PurchaseCost) AS decimal(18,2)) AS purchase_cost, "+
				"CAST(SUM(s.Quantity) * MAX(s.PurchaseCost) AS decimal(18,2)) AS value_at_cost, "+
				"CAST(MAX(s.MRP) AS decimal(18,2)) AS mrp "+
				"FROM Stock s "+
				"LEFT JOIN ProductMaster p ON p.ProductID = s.ProductID "+
				"LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID%s "+
				"GROUP BY s.ProductID, p.ProductName, w.WarehouseName%s ORDER BY value_at_cost DESC",
				topN(app, 50), stockWhere(&f), having)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "warehouse", "product", "search")
	c.Flags().BoolVar(&nonZero, "non-zero", false, "hide SKUs whose on-hand is exactly zero")
	return c
}

func stockMovementCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "movement",
		Short:   "Every movement bucket for one SKU, warehouse by warehouse",
		Example: "  ary stock movement --product 0CU7",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if f.Product == "" && f.Search == "" {
				return Usagef("give --product <ProductID> or --search <name>")
			}
			q := fmt.Sprintf("SELECT TOP %d s.ProductID AS id, p.ProductName AS product, w.WarehouseName AS warehouse, "+
				"CAST(s.OP AS decimal(18,2)) AS opening, CAST(s.Pur AS decimal(18,2)) AS purchased, "+
				"CAST(s.PR AS decimal(18,2)) AS purch_returns, CAST(s.Sal AS decimal(18,2)) AS sold, "+
				"CAST(s.SR AS decimal(18,2)) AS sale_returns, CAST(s.Prod AS decimal(18,2)) AS produced, "+
				"CAST(s.Cons AS decimal(18,2)) AS consumed, CAST(s.TrIn AS decimal(18,2)) AS tr_in, "+
				"CAST(s.TrOut AS decimal(18,2)) AS tr_out, CAST(s.Sho AS decimal(18,2)) AS shortage, "+
				"CAST(s.Exc AS decimal(18,2)) AS excess, CAST(s.Was AS decimal(18,2)) AS wastage, "+
				"CAST(s.Quantity AS decimal(18,2)) AS book_qty "+
				"FROM Stock s "+
				"LEFT JOIN ProductMaster p ON p.ProductID = s.ProductID "+
				"LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID%s "+
				"ORDER BY s.ProductID, w.WarehouseName", topN(app, 100), stockWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "warehouse", "product", "search")
	return c
}

func stockNegativeCmd(app *App) *cobra.Command {
	var f domFilters
	var below float64
	c := &cobra.Command{
		Use:   "negative",
		Short: "SKUs showing NEGATIVE book stock — sold without a recorded receipt",
		Long: "Negative on-hand means the counter billed goods the system never saw arrive: a missing\n" +
			"purchase entry, a transfer keyed one way only, or a wrong unit. It is the cheapest\n" +
			"leakage signal in the database and the first thing a stock audit should be handed.",
		Example: "  ary stock negative -n 40\n  ary stock negative --warehouse 11 --below -100",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d s.ProductID AS id, p.ProductName AS product, w.WarehouseName AS warehouse, "+
				"CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, CAST(SUM(s.Sal) AS decimal(18,2)) AS sold, "+
				"CAST(SUM(s.Pur) AS decimal(18,2)) AS purchased, CAST(SUM(s.TrIn) AS decimal(18,2)) AS tr_in, "+
				"CAST(SUM(s.TrOut) AS decimal(18,2)) AS tr_out, CAST(SUM(s.Sho) AS decimal(18,2)) AS shortage, "+
				"CAST(SUM(s.Quantity) * MAX(s.PurchaseCost) AS decimal(18,2)) AS value_at_cost "+
				"FROM Stock s "+
				"LEFT JOIN ProductMaster p ON p.ProductID = s.ProductID "+
				"LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID%s "+
				"GROUP BY s.ProductID, p.ProductName, w.WarehouseName "+
				"HAVING SUM(s.Quantity) < %.2f ORDER BY book_qty ASC", topN(app, 50), stockWhere(&f), below)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "warehouse", "product", "search")
	c.Flags().Float64Var(&below, "below", 0, "only rows with on-hand below this (default 0)")
	return c
}

func stockDeadCmd(app *App) *cobra.Command {
	var f domFilters
	var days int
	c := &cobra.Command{
		Use:   "dead",
		Short: "Stock on hand with NO sale in the last N days, valued at cost",
		Long: "Joins live on-hand to the last sale date from SaleDetail. A SKU with stock and no recent\n" +
			"sale is working capital sitting still; the value_at_cost column is what it is costing.",
		Example: "  ary stock dead --days 180 -n 40",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d s.ProductID AS id, p.ProductName AS product, "+
				"CAST(SUM(s.Quantity) AS decimal(18,2)) AS book_qty, "+
				"CAST(SUM(s.Quantity) * MAX(s.PurchaseCost) AS decimal(18,2)) AS value_at_cost, "+
				"CONVERT(varchar(10), MAX(ls.last_sale), 120) AS last_sale, "+
				"DATEDIFF(day, MAX(ls.last_sale), GETDATE()) AS days_since_sale "+
				"FROM Stock s "+
				"LEFT JOIN ProductMaster p ON p.ProductID = s.ProductID "+
				"LEFT JOIN (SELECT d.ProductID, MAX(h.VoucherDate) AS last_sale FROM SaleDetail d "+
				"JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber GROUP BY d.ProductID) ls ON ls.ProductID = s.ProductID%s "+
				"GROUP BY s.ProductID, p.ProductName "+
				"HAVING SUM(s.Quantity) > 0 AND (MAX(ls.last_sale) IS NULL OR MAX(ls.last_sale) < DATEADD(day, -%d, GETDATE())) "+
				"ORDER BY value_at_cost DESC", topN(app, 50), stockWhere(&f), days)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "warehouse", "search")
	c.Flags().IntVar(&days, "days", 180, "a SKU is dead if it has not sold in this many days")
	return c
}

func stockValueCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:   "value",
		Short: "Total stock valuation per warehouse, at purchase cost and at MRP",
		Long: "Only POSITIVE on-hand is valued; the negative rows are reported separately in the same\n" +
			"output, because netting them silently understates the stock actually on the floor.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT w.WarehouseName AS warehouse, " +
				"CAST(SUM(CASE WHEN s.Quantity > 0 THEN s.Quantity ELSE 0 END) AS decimal(18,2)) AS positive_qty, " +
				"CAST(SUM(CASE WHEN s.Quantity > 0 THEN s.Quantity * s.PurchaseCost ELSE 0 END) AS decimal(18,2)) AS value_at_cost, " +
				"CAST(SUM(CASE WHEN s.Quantity > 0 THEN s.Quantity * s.MRP ELSE 0 END) AS decimal(18,2)) AS value_at_mrp, " +
				"CAST(SUM(CASE WHEN s.Quantity < 0 THEN s.Quantity ELSE 0 END) AS decimal(18,2)) AS negative_qty, " +
				"SUM(CASE WHEN s.Quantity < 0 THEN 1 ELSE 0 END) AS negative_rows " +
				"FROM Stock s LEFT JOIN WarehouseMaster w ON w.WarehouseID = s.WarehouseID " +
				"GROUP BY w.WarehouseName ORDER BY value_at_cost DESC"
			return runSelect(app, q)
		},
	}
	return c
}

func stockTransfersCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "transfers",
		Short:   "Stock transfers between warehouses/locations",
		Example: "  ary stock transfers --from 2026-08-01 -n 40",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d t.SerialNumber AS serial, CONVERT(varchar(10), t.VoucherDate, 120) AS date, "+
				"t.VchIDPrefix + CAST(t.VchNumber AS varchar(16)) AS doc_no, "+
				"fw.WarehouseName AS from_warehouse, tw.WarehouseName AS to_warehouse, "+
				"CAST(t.QtyTotal AS decimal(18,2)) AS qty, CAST(t.PCostTotal AS decimal(18,2)) AS value_at_cost, "+
				"t.Status AS status, t.Narration AS narration "+
				"FROM StockTransferHeader t "+
				"LEFT JOIN WarehouseMaster fw ON fw.WarehouseID = t.FromWarehouseID "+
				"LEFT JOIN WarehouseMaster tw ON tw.WarehouseID = t.ToWarehouseID%s "+
				"ORDER BY t.VoucherDate DESC, t.SerialNumber DESC", topN(app, 50),
				fWhere(fDateGE("t.VoucherDate", f.From), fDateLT("t.VoucherDate", f.To),
					stockTransferWarehouse(f.Warehouse)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "warehouse")
	return c
}

// stockTransferWarehouse matches a warehouse on EITHER side of a transfer.
func stockTransferWarehouse(id int) string {
	if id == 0 {
		return ""
	}
	return fmt.Sprintf("(t.FromWarehouseID = %d OR t.ToWarehouseID = %d)", id, id)
}

func stockJournalsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "journals",
		Short:   "Stock journals — the adjustment documents (production, consumption, write-offs)",
		Example: "  ary stock journals --from 2026-04-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d j.SerialNumber AS serial, CONVERT(varchar(10), j.VoucherDate, 120) AS date, "+
				"j.VchIDPrefix + CAST(j.VchNumber AS varchar(16)) AS doc_no, v.VoucherName AS voucher, "+
				"CAST(j.QtyTotal AS decimal(18,2)) AS qty, j.Narration AS narration, u.UserName AS entered_by "+
				"FROM StockJournalHeader j "+
				"LEFT JOIN VoucherMaster v ON v.VoucherID = j.VoucherID "+
				"LEFT JOIN UserMaster u ON u.UserID = j.UserID%s "+
				"ORDER BY j.VoucherDate DESC, j.SerialNumber DESC", topN(app, 50),
				fWhere(fDateGE("j.VoucherDate", f.From), fDateLT("j.VoucherDate", f.To)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}
