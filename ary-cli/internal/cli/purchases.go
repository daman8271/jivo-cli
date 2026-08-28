package cli

// Purchases — PurchaseHeader / PurchaseDetail, returns and orders.
//
// Notes (verified live 2026-08-27):
//   - 9,221 purchase bills / 89,960 lines. PurchaseHeader DOES have IsDeleted
//     (unlike SaleHeader), so every read filters it unless --include-deleted.
//   - AccountID is the SUPPLIER (AccountMaster), SupplierRef/SupplierRefDate are
//     the vendor's own bill number and date — that pair is the paper key.
//   - Margin on the header is the document's overall margin %, not an amount.

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newPurchasesCmd) }

func newPurchasesCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "purchases",
		Short:   "Purchases — summary, bills, one bill, by supplier, by product, returns, orders",
		Aliases: []string{"purchase", "buy"},
	}
	c.AddCommand(purchasesSummaryCmd(app), purchasesMonthlyCmd(app), purchasesBillsCmd(app),
		purchasesBillCmd(app), purchasesBySupplierCmd(app), purchasesByProductCmd(app),
		purchasesReturnsCmd(app), purchasesOrdersCmd(app))
	return c
}

func purchasesWhere(f *domFilters) string {
	return fWhere(
		fDateGE("h.VoucherDate", f.From),
		fDateLT("h.VoucherDate", f.To),
		fEqInt("h.LocationID", f.Location),
		fEqInt("h.AccountID", f.Account),
		fLive("h.", f.IncludeDeleted),
	)
}

func purchasesSummaryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "summary",
		Short:   "Bills, quantity, sub-total, tax and bill amount for a period",
		Example: "  ary purchases summary --from 2026-04-01 --to 2026-09-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS bills, CAST(SUM(h.QtyTotal) AS decimal(18,2)) AS qty, " +
				"CAST(SUM(h.SubTotal) AS decimal(18,2)) AS sub_total, CAST(SUM(h.TaxTotal) AS decimal(18,2)) AS tax, " +
				"CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount, " +
				"CONVERT(varchar(10), MIN(h.VoucherDate), 120) AS first_bill, " +
				"CONVERT(varchar(10), MAX(h.VoucherDate), 120) AS last_bill " +
				"FROM PurchaseHeader h" + purchasesWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "account", "deleted")
	return c
}

func purchasesMonthlyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "monthly",
		Short: "Month-by-month purchase value",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d FORMAT(h.VoucherDate, 'yyyy-MM') AS month, COUNT(*) AS bills, "+
				"CAST(SUM(h.QtyTotal) AS decimal(18,2)) AS qty, CAST(SUM(h.SubTotal) AS decimal(18,2)) AS sub_total, "+
				"CAST(SUM(h.TaxTotal) AS decimal(18,2)) AS tax, CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount "+
				"FROM PurchaseHeader h%s GROUP BY FORMAT(h.VoucherDate, 'yyyy-MM') ORDER BY month DESC",
				topN(app, 48), purchasesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "account", "deleted")
	return c
}

func purchasesBillsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "bills",
		Short:   "List purchase bills with supplier and the vendor's own bill number",
		Example: "  ary purchases bills --from 2026-08-01 -n 40",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d h.SerialNumber AS serial, CONVERT(varchar(10), h.VoucherDate, 120) AS date, "+
				"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS doc_no, a.AccountName AS supplier, "+
				"h.SupplierRef AS supplier_bill_no, CONVERT(varchar(10), h.SupplierRefDate, 120) AS supplier_bill_date, "+
				"l.LocationName AS location, CAST(h.QtyTotal AS decimal(18,2)) AS qty, "+
				"CAST(h.SubTotal AS decimal(18,2)) AS sub_total, CAST(h.TaxTotal AS decimal(18,2)) AS tax, "+
				"CAST(h.BillAmount AS decimal(18,2)) AS bill_amount, CONVERT(varchar(10), h.DueDate, 120) AS due_date "+
				"FROM PurchaseHeader h "+
				"LEFT JOIN AccountMaster a ON a.AccountID = h.AccountID "+
				"LEFT JOIN LocationMaster l ON l.LocationID = h.LocationID%s "+
				"ORDER BY h.VoucherDate DESC, h.SerialNumber DESC", topN(app, 50), purchasesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "account", "deleted")
	return c
}

func purchasesBillCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "bill <SerialNumber>",
		Short:   "One purchase bill in full: header and lines",
		Example: "  ary purchases bill 9221",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			sn := db.Lit(args[0])
			return runSections(app, []section{
				{"header", "SELECT h.SerialNumber AS serial, CONVERT(varchar(10), h.VoucherDate, 120) AS date, " +
					"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS doc_no, v.VoucherName AS voucher, " +
					"a.AccountName AS supplier, a.GSTINNo AS supplier_gstin, h.SupplierRef AS supplier_bill_no, " +
					"CONVERT(varchar(10), h.SupplierRefDate, 120) AS supplier_bill_date, l.LocationName AS location, " +
					"CAST(h.QtyTotal AS decimal(18,2)) AS qty, CAST(h.SubTotal AS decimal(18,2)) AS sub_total, " +
					"CAST(h.TaxTotal AS decimal(18,2)) AS tax, CAST(h.RoundOffAmt AS decimal(18,2)) AS round_off, " +
					"CAST(h.BillAmount AS decimal(18,2)) AS bill_amount, h.Narration AS narration, " +
					"u.UserName AS entered_by, CONVERT(varchar(16), h.RecordDateTime, 120) AS entered_at, " +
					"h.IsDeleted AS is_deleted " +
					"FROM PurchaseHeader h " +
					"LEFT JOIN VoucherMaster v ON v.VoucherID = h.VoucherID " +
					"LEFT JOIN AccountMaster a ON a.AccountID = h.AccountID " +
					"LEFT JOIN LocationMaster l ON l.LocationID = h.LocationID " +
					"LEFT JOIN UserMaster u ON u.UserID = h.UserID " +
					"WHERE h.SerialNumber = " + sn},
				{"lines", "SELECT d.SrlNo AS line, d.ProductID AS id, p.ProductName AS product, w.WarehouseName AS warehouse, " +
					"CAST(d.Quantity AS decimal(18,3)) AS qty, un.UnitName AS unit, " +
					"CAST(d.PurchaseCost AS decimal(18,2)) AS purchase_cost, CAST(d.SellingRate AS decimal(18,2)) AS selling_rate, " +
					"CAST(d.TaxAmount1 + d.TaxAmount2 + d.TaxAmount3 + d.TaxAmount4 AS decimal(18,2)) AS tax_amt, " +
					"CAST(d.ItemValue AS decimal(18,2)) AS line_amount " +
					"FROM PurchaseDetail d " +
					"LEFT JOIN ProductMaster p ON p.ProductID = d.ProductID " +
					"LEFT JOIN WarehouseMaster w ON w.WarehouseID = d.WarehouseID " +
					"LEFT JOIN UnitMaster un ON un.UnitID = d.UnitID " +
					"WHERE d.SerialNumber = " + sn + " AND ISNULL(d.IsDeleted,0) = 0 ORDER BY d.SrlNo"},
			})
		},
	}
}

func purchasesBySupplierCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-supplier",
		Short:   "Top suppliers by purchase value",
		Aliases: []string{"by-vendor"},
		Example: "  ary purchases by-supplier --from 2026-04-01 -n 25",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d h.AccountID AS account_id, a.AccountName AS supplier, a.GSTINNo AS gstin, "+
				"COUNT(*) AS bills, CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount, "+
				"CONVERT(varchar(10), MAX(h.VoucherDate), 120) AS last_bill "+
				"FROM PurchaseHeader h LEFT JOIN AccountMaster a ON a.AccountID = h.AccountID%s "+
				"GROUP BY h.AccountID, a.AccountName, a.GSTINNo ORDER BY bill_amount DESC",
				topN(app, 25), purchasesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "deleted")
	return c
}

func purchasesByProductCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-product",
		Short:   "Top SKUs purchased, with the average landed rate",
		Example: "  ary purchases by-product --from 2026-04-01 -n 25",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d d.ProductID AS id, p.ProductName AS product, b.BrandName AS brand, "+
				"COUNT(DISTINCT d.SerialNumber) AS bills, CAST(SUM(d.Quantity) AS decimal(18,2)) AS qty, "+
				"CAST(SUM(d.ItemValue) AS decimal(18,2)) AS value, "+
				"CAST(SUM(d.ItemValue) / NULLIF(SUM(d.Quantity),0) AS decimal(18,2)) AS avg_rate "+
				"FROM PurchaseDetail d JOIN PurchaseHeader h ON h.SerialNumber = d.SerialNumber "+
				"LEFT JOIN ProductMaster p ON p.ProductID = d.ProductID "+
				"LEFT JOIN BrandMaster b ON b.BrandID = p.BrandID%s "+
				"GROUP BY d.ProductID, p.ProductName, b.BrandName ORDER BY value DESC",
				topN(app, 25), purchasesWhere(&f)+fAnd(fLive("d.", f.IncludeDeleted)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "account", "deleted")
	return c
}

func purchasesReturnsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "returns",
		Short: "Purchase returns (debit notes to suppliers)",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d r.SerialNumber AS serial, CONVERT(varchar(10), r.VoucherDate, 120) AS date, "+
				"r.VchIDPrefix + CAST(r.VchNumber AS varchar(16)) AS doc_no, a.AccountName AS supplier, "+
				"CAST(r.QtyTotal AS decimal(18,2)) AS qty, CAST(r.BillAmount AS decimal(18,2)) AS amount, r.Narration AS narration "+
				"FROM PurchaseReturnHeader r LEFT JOIN AccountMaster a ON a.AccountID = r.AccountID%s "+
				"ORDER BY r.VoucherDate DESC", topN(app, 50),
				fWhere(fDateGE("r.VoucherDate", f.From), fDateLT("r.VoucherDate", f.To),
					fEqInt("r.AccountID", f.Account), fLive("r.", f.IncludeDeleted)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "account", "deleted")
	return c
}

func purchasesOrdersCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "orders",
		Short:   "Purchase orders (only a handful exist — POs are barely used here)",
		Aliases: []string{"po"},
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d h.SerialNumber AS serial, CONVERT(varchar(10), h.VoucherDate, 120) AS date, "+
				"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS doc_no, a.AccountName AS supplier, "+
				"CAST(h.QtyTotal AS decimal(18,2)) AS qty, CAST(h.BillAmount AS decimal(18,2)) AS amount, h.Narration AS narration "+
				"FROM PurchaseOrderHeader h LEFT JOIN AccountMaster a ON a.AccountID = h.AccountID%s "+
				"ORDER BY h.VoucherDate DESC", topN(app, 50),
				fWhere(fDateGE("h.VoucherDate", f.From), fDateLT("h.VoucherDate", f.To), fEqInt("h.AccountID", f.Account)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "account")
	return c
}
