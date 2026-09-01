package cli

// Purchases — A/P invoices (OPCH/PCH1) and A/P credit notes (ORPC/RPC1).
//
// Same shape as `sales`: `gross` is GST-inclusive (DocTotal), `net` is net of
// GST, `purchases` is net of GST AND net of debit notes.

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newPurchasesCmd) }

func newPurchasesCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "purchases",
		Short:   "Purchases — summary, monthly, A/P bill list, one bill, by vendor/item, returns",
		Aliases: []string{"purchase", "ap"},
	}
	c.AddCommand(purchSummaryCmd(app), purchMonthlyCmd(app), purchBillsCmd(app), purchBillCmd(app),
		purchByVendorCmd(app), purchByItemCmd(app), purchReturnsCmd(app))
	return c
}

func purchWhere(f *domFilters, from, to string) string {
	return fWhere(
		fDateGE("h.DocDate", from),
		fDateLT("h.DocDate", to),
		fEqStr("h.CardCode", f.Party),
		fEqInt("h.BPLId", f.Branch),
		fLive("h.", f.IncludeCancelled),
		fOpen("h.", f.OpenOnly),
	)
}

func purchSummaryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "summary",
		Short:   "A/P bills, debit notes and net purchases for a period",
		Example: "  saphist purchases summary --fy 2021\n  saphist purchases summary --party VENDA000123 --year 2022",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				w := purchWhere(&f, from, to)
				return fmt.Sprintf(`SELECT
  (SELECT COUNT(*) FROM OPCH h%[1]s) AS bills,
  CAST((SELECT ISNULL(SUM(h.DocTotal),0) FROM OPCH h%[1]s) AS decimal(19,2)) AS gross_incl_gst,
  CAST((SELECT ISNULL(SUM(h.VatSum),0) FROM OPCH h%[1]s) AS decimal(19,2)) AS gst,
  CAST((SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM OPCH h%[1]s) AS decimal(19,2)) AS net_purchases,
  (SELECT COUNT(*) FROM ORPC h%[1]s) AS debit_notes,
  CAST((SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM ORPC h%[1]s) AS decimal(19,2)) AS net_returns,
  CAST((SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM OPCH h%[1]s)
     - (SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM ORPC h%[1]s) AS decimal(19,2)) AS purchases_net,
  (SELECT CONVERT(varchar(10),MIN(h.DocDate),120) FROM OPCH h%[1]s) AS first_bill,
  (SELECT CONVERT(varchar(10),MAX(h.DocDate),120) FROM OPCH h%[1]s) AS last_bill`, w)
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}

func purchMonthlyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "monthly",
		Short:   "Month-by-month A/P bills and net purchases",
		Example: "  saphist purchases monthly --fy 2021",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`WITH d AS (
  SELECT CONVERT(char(7), h.DocDate, 120) AS ym, 1 AS docs, h.DocTotal AS gross,
         h.DocTotal - h.VatSum AS net, 0.0 AS ret FROM OPCH h%[1]s
  UNION ALL
  SELECT CONVERT(char(7), h.DocDate, 120), 0, 0, 0, h.DocTotal - h.VatSum FROM ORPC h%[1]s)
SELECT TOP %[2]d ym AS month, SUM(docs) AS bills,
  CAST(SUM(gross) AS decimal(19,2)) AS gross_incl_gst,
  CAST(SUM(net) AS decimal(19,2)) AS net_purchases,
  CAST(SUM(ret) AS decimal(19,2)) AS net_returns,
  CAST(SUM(net) - SUM(ret) AS decimal(19,2)) AS purchases_net
FROM d GROUP BY ym ORDER BY ym`, purchWhere(&f, from, to), topN(app, 200))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}

func purchBillsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "bills",
		Short:   "List A/P invoices (newest first)",
		Aliases: []string{"list", "invoices"},
		Example: "  saphist purchases bills --party VENDA000123 -n 50\n  saphist purchases bills --fy 2020 --open",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  h.CardCode, h.CardName, h.NumAtCard AS vendor_ref, h.BPLName AS branch,
  CAST(h.DocTotal AS decimal(19,2)) AS gross_incl_gst, CAST(h.VatSum AS decimal(19,2)) AS gst,
  CAST(h.DocTotal - h.VatSum AS decimal(19,2)) AS net, CAST(h.PaidToDate AS decimal(19,2)) AS paid,
  h.DocStatus AS status, h.CANCELED AS cancelled
FROM OPCH h%s ORDER BY h.DocDate DESC, h.DocNum DESC`, topN(app, 40), purchWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled", "open")
	return c
}

func purchBillCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "bill <DocNum>",
		Short:   "One A/P invoice: header, lines and the journal it posted",
		Example: "  saphist purchases bill 8123",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			num := db.Lit(args[0])
			from, to := f.dates()
			b, err := findInBooks(app, from, to, "SELECT COUNT(*) FROM OPCH WHERE DocNum = "+num)
			if err != nil {
				return err
			}
			if !app.Flags.Quiet && !app.Flags.JSON && !app.Flags.CSV && !app.Flags.Compact {
				fmt.Printf("book %s — %s (%s)\n\n", b.Key, b.DB, b.Company)
			}
			return runSections(app, b.DB, []section{
				{"header", `SELECT TOP 1 h.DocEntry, h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  CONVERT(varchar(10),h.DocDueDate,120) AS due_date, h.CardCode, h.CardName, h.NumAtCard AS vendor_ref,
  h.BPLId, h.BPLName AS branch, h.Series, h.DocCur,
  CAST(h.DocTotal AS decimal(19,2)) AS gross_incl_gst, CAST(h.VatSum AS decimal(19,2)) AS gst,
  CAST(h.DocTotal - h.VatSum AS decimal(19,2)) AS net, CAST(h.PaidToDate AS decimal(19,2)) AS paid,
  h.DocStatus AS status, h.CANCELED AS cancelled, h.Comments, h.JrnlMemo, h.TransId AS journal_transid
FROM OPCH h WHERE h.DocNum = ` + num},
				{"lines", `SELECT l.LineNum, l.ItemCode, l.Dscription AS description, l.Quantity,
  CAST(l.Price AS decimal(19,4)) AS price, CAST(l.LineTotal AS decimal(19,2)) AS line_total,
  CAST(l.VatSum AS decimal(19,2)) AS gst, l.VatGroup, l.WhsCode AS warehouse, l.AcctCode AS gl_account
FROM PCH1 l JOIN OPCH h ON h.DocEntry = l.DocEntry WHERE h.DocNum = ` + num + ` ORDER BY l.LineNum`},
				{"journal", `SELECT j.Line_ID, j.Account, j.ShortName, a.AcctName,
  CAST(j.Debit AS decimal(19,2)) AS debit, CAST(j.Credit AS decimal(19,2)) AS credit, j.LineMemo
FROM JDT1 j JOIN OPCH h ON h.TransId = j.TransId LEFT JOIN OACT a ON a.AcctCode = j.Account
WHERE h.DocNum = ` + num + ` ORDER BY j.Line_ID`},
			})
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func purchByVendorCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-vendor",
		Short:   "Net purchases by vendor, biggest first",
		Example: "  saphist purchases by-vendor --fy 2021 -n 25",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`WITH d AS (
  SELECT h.CardCode, h.CardName, 1 AS docs, h.DocTotal - h.VatSum AS net, 0.0 AS ret FROM OPCH h%[1]s
  UNION ALL
  SELECT h.CardCode, h.CardName, 0, 0, h.DocTotal - h.VatSum FROM ORPC h%[1]s)
SELECT TOP %[2]d CardCode, MAX(CardName) AS card_name, SUM(docs) AS bills,
  CAST(SUM(net) AS decimal(19,2)) AS net_purchases, CAST(SUM(ret) AS decimal(19,2)) AS net_returns,
  CAST(SUM(net) - SUM(ret) AS decimal(19,2)) AS purchases_net
FROM d GROUP BY CardCode ORDER BY purchases_net DESC`, purchWhere(&f, from, to), topN(app, 25))
			})
		},
	}
	addDomFilters(c, &f, "date", "branch", "cancelled")
	return c
}

func purchByItemCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-item",
		Short:   "Purchases by item: quantity and line value",
		Example: "  saphist purchases by-item --fy 2021 -n 25",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				where := fWhere(fDateGE("h.DocDate", from), fDateLT("h.DocDate", to),
					fEqStr("h.CardCode", f.Party), fEqInt("h.BPLId", f.Branch),
					fEqStr("l.ItemCode", f.Item), fEqStr("l.WhsCode", f.Warehouse),
					fLive("h.", f.IncludeCancelled))
				return fmt.Sprintf(`WITH d AS (
  SELECT l.ItemCode, l.Dscription AS nm, l.Quantity AS qty, l.LineTotal AS val
  FROM PCH1 l JOIN OPCH h ON h.DocEntry = l.DocEntry%[1]s
  UNION ALL
  SELECT l.ItemCode, l.Dscription, -l.Quantity, -l.LineTotal
  FROM RPC1 l JOIN ORPC h ON h.DocEntry = l.DocEntry%[1]s)
SELECT TOP %[2]d ItemCode, MAX(nm) AS description,
  CAST(SUM(qty) AS decimal(19,3)) AS qty_net, CAST(SUM(val) AS decimal(19,2)) AS value_net
FROM d GROUP BY ItemCode ORDER BY value_net DESC`, where, topN(app, 25))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "item", "branch", "warehouse", "cancelled")
	return c
}

func purchReturnsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "returns",
		Short:   "List A/P credit notes (purchase returns / debit notes)",
		Aliases: []string{"debit-notes"},
		Example: "  saphist purchases returns --fy 2021",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  h.CardCode, h.CardName, h.BPLName AS branch,
  CAST(h.DocTotal AS decimal(19,2)) AS gross_incl_gst, CAST(h.VatSum AS decimal(19,2)) AS gst,
  CAST(h.DocTotal - h.VatSum AS decimal(19,2)) AS net, h.CANCELED AS cancelled, h.Comments
FROM ORPC h%s ORDER BY h.DocDate DESC, h.DocNum DESC`, topN(app, 40), purchWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}
