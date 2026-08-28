package cli

// Sales — SaleHeader / SaleDetail / SalePayment, plus returns.
//
// Notes (verified live 2026-08-27):
//   - 1,088,607 bills, 2023-04-01 -> 2026-08-21, ₹22.83 Cr of BillAmount.
//   - There is NO cancellation flag: every row is Status=2, no SaleDetail row is
//     voided. Reversals are separate SaleReturn documents, so a net figure has to
//     subtract `ary sales returns` — the `net` command does it in one query.
//   - BillAmount = SubTotal + TaxTotal + RoundOffAmt (header level).
//     Line level: FinalSaleAmount, with TaxAmount1..4 broken out.
//   - The bill's warehouse lives on the LINE (SaleDetail.WarehouseID), not the
//     header; the header carries LocationID (which of the 3 registrations).
//   - CustomerID is nvarchar and is blank on walk-in/counter bills.

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() { register(newSalesCmd) }

func newSalesCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "sales",
		Short:   "Sales — summary, daily, bills, one bill, by product/warehouse/customer/staff, payment mix, returns",
		Aliases: []string{"sale"},
	}
	c.AddCommand(salesSummaryCmd(app), salesDailyCmd(app), salesMonthlyCmd(app), salesBillsCmd(app),
		salesBillCmd(app), salesByProductCmd(app), salesByWarehouseCmd(app), salesByCustomerCmd(app),
		salesByStaffCmd(app), salesPaymentsCmd(app), salesReturnsCmd(app), salesNetCmd(app))
	return c
}

// salesWhere filters SaleHeader (alias h). Warehouse filters via an EXISTS on
// the line table, because the warehouse is a line-level attribute.
func salesWhere(f *domFilters) string {
	var wh string
	if f.Warehouse != 0 {
		wh = fmt.Sprintf("EXISTS (SELECT 1 FROM SaleDetail d WHERE d.SerialNumber = h.SerialNumber AND d.WarehouseID = %d)", f.Warehouse)
	}
	return fWhere(
		fDateGE("h.VoucherDate", f.From),
		fDateLT("h.VoucherDate", f.To),
		fEqInt("h.LocationID", f.Location),
		fEqStr("h.CustomerID", f.Customer),
		wh,
	)
}

func salesSummaryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "summary",
		Short: "Bills, quantity, sub-total, tax and bill amount for a period",
		Example: "  ary sales summary --from 2026-08-01 --to 2026-09-01\n" +
			"  ary sales summary --from 2026-04-01 --to 2026-09-01 --location 15",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COUNT(*) AS bills, CAST(SUM(h.QtyTotal) AS decimal(18,2)) AS qty, " +
				"CAST(SUM(h.SubTotal) AS decimal(18,2)) AS sub_total, CAST(SUM(h.TaxTotal) AS decimal(18,2)) AS tax, " +
				"CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount, " +
				"CAST(AVG(h.BillAmount) AS decimal(18,2)) AS avg_bill, " +
				"CONVERT(varchar(10), MIN(h.VoucherDate), 120) AS first_bill, " +
				"CONVERT(varchar(10), MAX(h.VoucherDate), 120) AS last_bill " +
				"FROM SaleHeader h" + salesWhere(&f)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse", "customer")
	return c
}

func salesDailyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "daily",
		Short:   "Day-by-day bills and value (also shows when the feed last wrote a row)",
		Example: "  ary sales daily --from 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d CONVERT(varchar(10), h.VoucherDate, 120) AS date, COUNT(*) AS bills, "+
				"CAST(SUM(h.QtyTotal) AS decimal(18,2)) AS qty, CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount, "+
				"CONVERT(varchar(16), MAX(h.RecordDateTime), 120) AS last_entry "+
				"FROM SaleHeader h%s GROUP BY CONVERT(varchar(10), h.VoucherDate, 120) ORDER BY date DESC",
				topN(app, 60), salesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse", "customer")
	return c
}

func salesMonthlyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "monthly",
		Short:   "Month-by-month bills and value",
		Example: "  ary sales monthly --from 2025-04-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d FORMAT(h.VoucherDate, 'yyyy-MM') AS month, COUNT(*) AS bills, "+
				"CAST(SUM(h.QtyTotal) AS decimal(18,2)) AS qty, CAST(SUM(h.SubTotal) AS decimal(18,2)) AS sub_total, "+
				"CAST(SUM(h.TaxTotal) AS decimal(18,2)) AS tax, CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount "+
				"FROM SaleHeader h%s GROUP BY FORMAT(h.VoucherDate, 'yyyy-MM') ORDER BY month DESC",
				topN(app, 48), salesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse", "customer")
	return c
}

func salesBillsCmd(app *App) *cobra.Command {
	var f domFilters
	var minAmt float64
	c := &cobra.Command{
		Use:     "bills",
		Short:   "List bills (newest first) with customer, counter and value",
		Example: "  ary sales bills --from 2026-08-20 -n 50\n  ary sales bills --min-amount 10000",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			min := ""
			if minAmt > 0 {
				min = fmt.Sprintf("h.BillAmount >= %.2f", minAmt)
			}
			w := salesWhere(&f)
			if min != "" {
				if w == "" {
					w = " WHERE " + min
				} else {
					w += " AND " + min
				}
			}
			q := fmt.Sprintf("SELECT TOP %d h.SerialNumber AS serial, CONVERT(varchar(16), h.VoucherDate, 120) AS date, "+
				"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS bill_no, v.VoucherName AS voucher, "+
				"l.LocationName AS location, COALESCE(NULLIF(h.CompanyName,''), c.CustomerName, '(walk-in)') AS customer, "+
				"CAST(h.QtyTotal AS decimal(18,2)) AS qty, CAST(h.SubTotal AS decimal(18,2)) AS sub_total, "+
				"CAST(h.TaxTotal AS decimal(18,2)) AS tax, CAST(h.BillAmount AS decimal(18,2)) AS bill_amount "+
				"FROM SaleHeader h "+
				"LEFT JOIN VoucherMaster v ON v.VoucherID = h.VoucherID "+
				"LEFT JOIN LocationMaster l ON l.LocationID = h.LocationID "+
				"LEFT JOIN CustomerMaster c ON c.CustomerID = h.CustomerID%s "+
				"ORDER BY h.VoucherDate DESC, h.SerialNumber DESC", topN(app, 50), w)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse", "customer")
	c.Flags().Float64Var(&minAmt, "min-amount", 0, "only bills at or above this value")
	return c
}

func salesBillCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "bill <SerialNumber>",
		Short:   "One bill in full: header, lines and payments",
		Example: "  ary sales bill 1088607",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			sn := db.Lit(args[0])
			return runSections(app, []section{
				{"header", "SELECT h.SerialNumber AS serial, CONVERT(varchar(16), h.VoucherDate, 120) AS date, " +
					"h.VchIDPrefix + CAST(h.VchNumber AS varchar(16)) AS bill_no, v.VoucherName AS voucher, " +
					"l.LocationName AS location, COALESCE(NULLIF(h.CompanyName,''), c.CustomerName, '(walk-in)') AS customer, " +
					"h.GSTINNumberCustomer AS customer_gstin, h.Narration AS narration, h.BillReference AS reference, " +
					"CAST(h.QtyTotal AS decimal(18,2)) AS qty, CAST(h.SubTotal AS decimal(18,2)) AS sub_total, " +
					"CAST(h.TaxTotal AS decimal(18,2)) AS tax, CAST(h.RoundOffAmt AS decimal(18,2)) AS round_off, " +
					"CAST(h.BillAmount AS decimal(18,2)) AS bill_amount, u.UserName AS entered_by, " +
					"CONVERT(varchar(16), h.RecordDateTime, 120) AS entered_at " +
					"FROM SaleHeader h " +
					"LEFT JOIN VoucherMaster v ON v.VoucherID = h.VoucherID " +
					"LEFT JOIN LocationMaster l ON l.LocationID = h.LocationID " +
					"LEFT JOIN CustomerMaster c ON c.CustomerID = h.CustomerID " +
					"LEFT JOIN UserMaster u ON u.UserID = h.UserID " +
					"WHERE h.SerialNumber = " + sn},
				{"lines", "SELECT d.SrlNo AS line, d.ProductID AS id, p.ProductName AS product, w.WarehouseName AS warehouse, " +
					"CAST(d.Quantity AS decimal(18,3)) AS qty, un.UnitName AS unit, CAST(d.MRP AS decimal(18,2)) AS mrp, " +
					"CAST(d.SaleRate AS decimal(18,2)) AS rate, CAST(d.DiscountFinal AS decimal(18,2)) AS discount, " +
					"CAST(d.TaxRate1 + d.TaxRate2 + d.TaxRate3 + d.TaxRate4 AS decimal(9,2)) AS tax_pct, " +
					"CAST(d.TaxAmount1 + d.TaxAmount2 + d.TaxAmount3 + d.TaxAmount4 AS decimal(18,2)) AS tax_amt, " +
					"CAST(d.FinalSaleAmount AS decimal(18,2)) AS line_amount, sp.SalesPersonName AS salesperson " +
					"FROM SaleDetail d " +
					"LEFT JOIN ProductMaster p ON p.ProductID = d.ProductID " +
					"LEFT JOIN WarehouseMaster w ON w.WarehouseID = d.WarehouseID " +
					"LEFT JOIN UnitMaster un ON un.UnitID = d.UnitID " +
					"LEFT JOIN SalesPersonMaster sp ON sp.SalesPersonID = d.SalesPersonID " +
					"WHERE d.SerialNumber = " + sn + " ORDER BY d.SrlNo"},
				{"payments", "SELECT pm.SrlNo AS line, m.MOPName AS mode, CAST(pm.Amount AS decimal(18,2)) AS amount, " +
					"CAST(pm.TenderAmount AS decimal(18,2)) AS tendered, CAST(pm.ReturnAmount AS decimal(18,2)) AS returned, " +
					"pm.DocumentNo AS doc_no, pm.BankName AS bank, pm.RefName AS ref " +
					"FROM SalePayment pm LEFT JOIN ModeOfPayment m ON m.MOPID = pm.MOPID " +
					"WHERE pm.SerialNumber = " + sn + " AND ISNULL(pm.IsDeleted,0) = 0 ORDER BY pm.SrlNo"},
			})
		},
	}
}

func salesByProductCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-product",
		Short:   "Top SKUs by value for a period (qty, value, and gross margin vs cost price)",
		Example: "  ary sales by-product --from 2026-08-01 -n 25",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d d.ProductID AS id, p.ProductName AS product, b.BrandName AS brand, "+
				"COUNT(DISTINCT d.SerialNumber) AS bills, CAST(SUM(d.Quantity) AS decimal(18,2)) AS qty, "+
				"CAST(SUM(d.FinalSaleAmount) AS decimal(18,2)) AS value, "+
				"CAST(SUM(d.Quantity * p.StandardCostPrice) AS decimal(18,2)) AS cost_at_std, "+
				"CAST(SUM(d.FinalSaleAmount) - SUM(d.Quantity * p.StandardCostPrice) AS decimal(18,2)) AS gross_margin "+
				"FROM SaleDetail d "+
				"JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber "+
				"LEFT JOIN ProductMaster p ON p.ProductID = d.ProductID "+
				"LEFT JOIN BrandMaster b ON b.BrandID = p.BrandID%s "+
				"GROUP BY d.ProductID, p.ProductName, b.BrandName ORDER BY value DESC",
				topN(app, 25), salesWhere(&f)+fAnd(fEqInt("d.WarehouseID", f.Warehouse)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse", "customer")
	return c
}

func salesByWarehouseCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-warehouse",
		Short:   "Sales split by counter / warehouse",
		Aliases: []string{"by-counter"},
		Example: "  ary sales by-warehouse --from 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT w.WarehouseName AS warehouse, COUNT(DISTINCT d.SerialNumber) AS bills, " +
				"CAST(SUM(d.Quantity) AS decimal(18,2)) AS qty, CAST(SUM(d.FinalSaleAmount) AS decimal(18,2)) AS value " +
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber " +
				"LEFT JOIN WarehouseMaster w ON w.WarehouseID = d.WarehouseID" + salesWhere(&f) +
				" GROUP BY w.WarehouseName ORDER BY value DESC"
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "customer")
	return c
}

func salesByCustomerCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-customer",
		Short:   "Top customers by value (walk-in counter bills grouped as one)",
		Example: "  ary sales by-customer --from 2026-04-01 -n 30",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d COALESCE(NULLIF(h.CustomerID,''), '(walk-in)') AS customer_id, "+
				"COALESCE(NULLIF(MAX(h.CompanyName),''), MAX(c.CustomerName), '(walk-in)') AS customer, "+
				"COUNT(*) AS bills, CAST(SUM(h.BillAmount) AS decimal(18,2)) AS bill_amount, "+
				"CAST(AVG(h.BillAmount) AS decimal(18,2)) AS avg_bill, "+
				"CONVERT(varchar(10), MAX(h.VoucherDate), 120) AS last_bill "+
				"FROM SaleHeader h LEFT JOIN CustomerMaster c ON c.CustomerID = h.CustomerID%s "+
				"GROUP BY COALESCE(NULLIF(h.CustomerID,''), '(walk-in)') ORDER BY bill_amount DESC",
				topN(app, 30), salesWhere(&f))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse")
	return c
}

func salesByStaffCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-staff",
		Short:   "Sales by salesperson, against their target",
		Aliases: []string{"by-salesperson"},
		Example: "  ary sales by-staff --from 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT COALESCE(sp.SalesPersonName, '(unassigned)') AS salesperson, " +
				"CAST(MAX(sp.Target) AS decimal(18,2)) AS target, COUNT(DISTINCT d.SerialNumber) AS bills, " +
				"CAST(SUM(d.FinalSaleAmount) AS decimal(18,2)) AS value, " +
				"CAST(SUM(d.SPCommAmt) AS decimal(18,2)) AS commission " +
				"FROM SaleDetail d JOIN SaleHeader h ON h.SerialNumber = d.SerialNumber " +
				"LEFT JOIN SalesPersonMaster sp ON sp.SalesPersonID = d.SalesPersonID" + salesWhere(&f) +
				" GROUP BY sp.SalesPersonName ORDER BY value DESC"
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "warehouse", "customer")
	return c
}

func salesPaymentsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "payment-mix",
		Short:   "Cash vs card vs UPI vs credit — collections by mode of payment",
		Aliases: []string{"payments", "mop"},
		Example: "  ary sales payment-mix --from 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			// The share is computed with a window over the grouped result, so the
			// period filter is written once and cannot drift between numerator and
			// denominator.
			q := "SELECT COALESCE(m.MOPName, '(unmapped)') AS mode, COUNT(*) AS tenders, " +
				"CAST(SUM(pm.Amount) AS decimal(18,2)) AS amount, " +
				"CAST(100.0 * SUM(pm.Amount) / NULLIF(SUM(SUM(pm.Amount)) OVER (), 0) AS decimal(9,2)) AS pct " +
				"FROM SalePayment pm JOIN SaleHeader h ON h.SerialNumber = pm.SerialNumber " +
				"LEFT JOIN ModeOfPayment m ON m.MOPID = pm.MOPID " +
				"WHERE ISNULL(pm.IsDeleted,0) = 0" +
				fAnd(fDateGE("h.VoucherDate", f.From), fDateLT("h.VoucherDate", f.To), fEqInt("h.LocationID", f.Location),
					fEqStr("h.CustomerID", f.Customer)) +
				" GROUP BY m.MOPName ORDER BY amount DESC"
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location", "customer")
	return c
}

func salesReturnsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "returns",
		Short:   "Sale returns — the only reversal ARY has (there is no bill cancellation)",
		Example: "  ary sales returns --from 2026-04-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d r.SerialNumber AS serial, CONVERT(varchar(16), r.VoucherDate, 120) AS date, "+
				"r.VchIDPrefix + CAST(r.VchNumber AS varchar(16)) AS doc_no, l.LocationName AS location, "+
				"COALESCE(NULLIF(r.CompanyName,''), c.CustomerName, '(walk-in)') AS customer, "+
				"CAST(r.QtyTotal AS decimal(18,2)) AS qty, CAST(r.BillAmount AS decimal(18,2)) AS amount, r.Narration AS narration "+
				"FROM SaleReturnHeader r "+
				"LEFT JOIN LocationMaster l ON l.LocationID = r.LocationID "+
				"LEFT JOIN CustomerMaster c ON c.CustomerID = r.CustomerID%s "+
				"ORDER BY r.VoucherDate DESC, r.SerialNumber DESC", topN(app, 50),
				fWhere(fDateGE("r.VoucherDate", f.From), fDateLT("r.VoucherDate", f.To), fEqInt("r.LocationID", f.Location)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location")
	return c
}

func salesNetCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "net",
		Short: "NET sales for a period: bills minus returns, in one row (quote this figure)",
		Long: "ARY has no bill cancellation, so gross sales overstate by the value of sale returns.\n" +
			"This subtracts SaleReturnHeader from SaleHeader over the same window and shows both\n" +
			"halves, so the netting is visible rather than assumed.",
		Example: "  ary sales net --from 2026-08-01 --to 2026-09-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			sw := fWhere(fDateGE("VoucherDate", f.From), fDateLT("VoucherDate", f.To), fEqInt("LocationID", f.Location))
			q := "SELECT s.bills, CAST(s.gross AS decimal(18,2)) AS gross_sales, r.returns_, " +
				"CAST(r.return_value AS decimal(18,2)) AS return_value, " +
				"CAST(s.gross - r.return_value AS decimal(18,2)) AS net_sales, " +
				"CAST(100.0 * r.return_value / NULLIF(s.gross,0) AS decimal(9,2)) AS return_pct FROM " +
				"(SELECT COUNT(*) AS bills, ISNULL(SUM(BillAmount),0) AS gross FROM SaleHeader" + sw + ") s CROSS JOIN " +
				"(SELECT COUNT(*) AS returns_, ISNULL(SUM(BillAmount),0) AS return_value FROM SaleReturnHeader" + sw + ") r"
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location")
	return c
}
