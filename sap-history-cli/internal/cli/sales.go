package cli

// Sales — A/R invoices (OINV/INV1) and A/R credit notes (ORIN/RIN1).
//
// TURNOVER is defined the way JIVO's Accounts team defines it (see the repo's
// CLAUDE.md, which is the settled definition for the live system too):
//
//	turnover = SUM(OINV.DocTotal - OINV.VatSum) - SUM(ORIN.DocTotal - ORIN.VatSum)
//	           by DocDate, excluding cancelled documents
//
// `gross` columns are GST-inclusive (DocTotal); `net` columns are net of GST;
// `turnover` is net of GST AND net of returns. Amounts are INR (DocTotal is in
// document currency — JIVO's old books are effectively all INR; use
// `--select` with DocCur on the invoice list if you need to prove it).

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newSalesCmd) }

func newSalesCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "sales",
		Short:   "Sales — turnover summary, monthly/yearly, invoice list, one invoice, by party/item/branch, returns",
		Aliases: []string{"sale", "revenue"},
	}
	c.AddCommand(salesSummaryCmd(app), salesMonthlyCmd(app), salesYearlyCmd(app), salesInvoicesCmd(app),
		salesInvoiceCmd(app), salesByPartyCmd(app), salesByItemCmd(app), salesByBranchCmd(app),
		salesReturnsCmd(app))
	return c
}

// salesWhere filters OINV/ORIN (alias h).
func salesWhere(f *domFilters, from, to string) string {
	return fWhere(
		fDateGE("h.DocDate", from),
		fDateLT("h.DocDate", to),
		fEqStr("h.CardCode", f.Party),
		fEqInt("h.BPLId", f.Branch),
		fLive("h.", f.IncludeCancelled),
		fOpen("h.", f.OpenOnly),
	)
}

func salesSummaryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "summary",
		Short: "Invoices, credit notes and TURNOVER (net of GST, net of returns) for a period",
		Example: "  saphist sales summary --fy 2016\n" +
			"  saphist sales summary --from 2018-04-01 --to 2020-04-01     # spans both books\n" +
			"  saphist sales summary --year 2022 --branch 3",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				inv := salesWhere(&f, from, to)
				return fmt.Sprintf(`SELECT
  (SELECT COUNT(*) FROM OINV h%[1]s) AS invoices,
  CAST((SELECT ISNULL(SUM(h.DocTotal),0) FROM OINV h%[1]s) AS decimal(19,2)) AS gross_incl_gst,
  CAST((SELECT ISNULL(SUM(h.VatSum),0) FROM OINV h%[1]s) AS decimal(19,2)) AS gst,
  CAST((SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM OINV h%[1]s) AS decimal(19,2)) AS net_sales,
  (SELECT COUNT(*) FROM ORIN h%[1]s) AS credit_notes,
  CAST((SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM ORIN h%[1]s) AS decimal(19,2)) AS net_returns,
  CAST((SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM OINV h%[1]s)
     - (SELECT ISNULL(SUM(h.DocTotal - h.VatSum),0) FROM ORIN h%[1]s) AS decimal(19,2)) AS turnover,
  (SELECT CONVERT(varchar(10),MIN(h.DocDate),120) FROM OINV h%[1]s) AS first_invoice,
  (SELECT CONVERT(varchar(10),MAX(h.DocDate),120) FROM OINV h%[1]s) AS last_invoice`, inv)
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}

func salesMonthlyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "monthly",
		Short:   "Month-by-month invoices, net sales, returns and turnover",
		Example: "  saphist sales monthly --fy 2021\n  saphist sales monthly --from 2014-11-01 --to 2024-10-02",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`WITH d AS (
  SELECT CONVERT(char(7), h.DocDate, 120) AS ym, 1 AS docs, h.DocTotal AS gross, h.VatSum AS gst,
         h.DocTotal - h.VatSum AS net, 0.0 AS ret FROM OINV h%[1]s
  UNION ALL
  SELECT CONVERT(char(7), h.DocDate, 120), 0, 0, 0, 0, h.DocTotal - h.VatSum FROM ORIN h%[1]s)
SELECT TOP %[2]d ym AS month, SUM(docs) AS invoices,
  CAST(SUM(gross) AS decimal(19,2)) AS gross_incl_gst,
  CAST(SUM(net) AS decimal(19,2)) AS net_sales,
  CAST(SUM(ret) AS decimal(19,2)) AS net_returns,
  CAST(SUM(net) - SUM(ret) AS decimal(19,2)) AS turnover
FROM d GROUP BY ym ORDER BY ym`, salesWhere(&f, from, to), topN(app, 200))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}

func salesYearlyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "yearly",
		Short:   "Indian financial year (Apr-Mar) invoices, net sales, returns and turnover",
		Aliases: []string{"fy"},
		Example: "  saphist sales yearly\n  saphist sales yearly --book all",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				// FY label: Apr-Dec belongs to that year, Jan-Mar to the previous one.
				fy := "CAST(YEAR(h.DocDate) - CASE WHEN MONTH(h.DocDate) < 4 THEN 1 ELSE 0 END AS varchar(4))"
				return fmt.Sprintf(`WITH d AS (
  SELECT %[3]s AS fy, 1 AS docs, h.DocTotal AS gross, h.DocTotal - h.VatSum AS net, 0.0 AS ret FROM OINV h%[1]s
  UNION ALL
  SELECT %[3]s, 0, 0, 0, h.DocTotal - h.VatSum FROM ORIN h%[1]s)
SELECT TOP %[2]d fy + '-' + RIGHT(CAST(CAST(fy AS int) + 1 AS varchar(4)),2) AS financial_year,
  SUM(docs) AS invoices,
  CAST(SUM(gross) AS decimal(19,2)) AS gross_incl_gst,
  CAST(SUM(net) AS decimal(19,2)) AS net_sales,
  CAST(SUM(ret) AS decimal(19,2)) AS net_returns,
  CAST(SUM(net) - SUM(ret) AS decimal(19,2)) AS turnover
FROM d GROUP BY fy ORDER BY fy`, salesWhere(&f, from, to), topN(app, 30), fy)
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}

func salesInvoicesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "invoices",
		Short:   "List A/R invoices (newest first)",
		Aliases: []string{"list"},
		Example: "  saphist sales invoices --fy 2020 -n 50\n  saphist sales invoices --party CUSTA000606",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  h.CardCode, h.CardName, h.NumAtCard AS their_ref, h.BPLName AS branch,
  CAST(h.DocTotal AS decimal(19,2)) AS gross_incl_gst, CAST(h.VatSum AS decimal(19,2)) AS gst,
  CAST(h.DocTotal - h.VatSum AS decimal(19,2)) AS net, h.DocStatus AS status, h.CANCELED AS cancelled
FROM OINV h%s ORDER BY h.DocDate DESC, h.DocNum DESC`, topN(app, 40), salesWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled", "open")
	return c
}

func salesInvoiceCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "invoice <DocNum>",
		Short:   "One A/R invoice: header, lines and the journal it posted — found in whichever book holds it",
		Example: "  saphist sales invoice 12345",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			num := db.Lit(args[0])
			from, to := f.dates()
			b, err := findInBooks(app, from, to, "SELECT COUNT(*) FROM OINV WHERE DocNum = "+num)
			if err != nil {
				return err
			}
			if !app.Flags.Quiet && !app.Flags.JSON && !app.Flags.CSV && !app.Flags.Compact {
				fmt.Printf("book %s — %s (%s)\n\n", b.Key, b.DB, b.Company)
			}
			return runSections(app, b.DB, []section{
				{"header", `SELECT TOP 1 h.DocEntry, h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  CONVERT(varchar(10),h.DocDueDate,120) AS due_date, h.CardCode, h.CardName, h.NumAtCard AS their_ref,
  h.BPLId, h.BPLName AS branch, h.Series, h.DocCur,
  CAST(h.DocTotal AS decimal(19,2)) AS gross_incl_gst, CAST(h.VatSum AS decimal(19,2)) AS gst,
  CAST(h.DocTotal - h.VatSum AS decimal(19,2)) AS net, CAST(h.PaidToDate AS decimal(19,2)) AS paid,
  h.DocStatus AS status, h.CANCELED AS cancelled, h.Comments, h.JrnlMemo, h.TransId AS journal_transid
FROM OINV h WHERE h.DocNum = ` + num},
				{"lines", `SELECT l.LineNum, l.ItemCode, l.Dscription AS description, l.Quantity,
  CAST(l.Price AS decimal(19,4)) AS price, CAST(l.LineTotal AS decimal(19,2)) AS line_total,
  CAST(l.VatSum AS decimal(19,2)) AS gst, l.VatGroup, l.WhsCode AS warehouse, l.AcctCode AS gl_account
FROM INV1 l JOIN OINV h ON h.DocEntry = l.DocEntry WHERE h.DocNum = ` + num + ` ORDER BY l.LineNum`},
				{"journal", `SELECT j.Line_ID, j.Account, j.ShortName, a.AcctName,
  CAST(j.Debit AS decimal(19,2)) AS debit, CAST(j.Credit AS decimal(19,2)) AS credit, j.LineMemo
FROM JDT1 j JOIN OINV h ON h.TransId = j.TransId LEFT JOIN OACT a ON a.AcctCode = j.Account
WHERE h.DocNum = ` + num + ` ORDER BY j.Line_ID`},
			})
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func salesByPartyCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-party",
		Short:   "Turnover by customer (net of GST, net of returns), biggest first",
		Aliases: []string{"by-customer"},
		Example: "  saphist sales by-party --fy 2021 -n 25",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`WITH d AS (
  SELECT h.CardCode, h.CardName, 1 AS docs, h.DocTotal - h.VatSum AS net, 0.0 AS ret FROM OINV h%[1]s
  UNION ALL
  SELECT h.CardCode, h.CardName, 0, 0, h.DocTotal - h.VatSum FROM ORIN h%[1]s)
SELECT TOP %[2]d CardCode, MAX(CardName) AS card_name, SUM(docs) AS invoices,
  CAST(SUM(net) AS decimal(19,2)) AS net_sales, CAST(SUM(ret) AS decimal(19,2)) AS net_returns,
  CAST(SUM(net) - SUM(ret) AS decimal(19,2)) AS turnover
FROM d GROUP BY CardCode ORDER BY turnover DESC`, salesWhere(&f, from, to), topN(app, 25))
			})
		},
	}
	addDomFilters(c, &f, "date", "branch", "cancelled")
	return c
}

func salesByItemCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-item",
		Short:   "Sales by item: quantity and line value (invoice lines, net of returns lines)",
		Example: "  saphist sales by-item --fy 2021 -n 25\n  saphist sales by-item --item FG0000123 --year 2022",
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
  FROM INV1 l JOIN OINV h ON h.DocEntry = l.DocEntry%[1]s
  UNION ALL
  SELECT l.ItemCode, l.Dscription, -l.Quantity, -l.LineTotal
  FROM RIN1 l JOIN ORIN h ON h.DocEntry = l.DocEntry%[1]s)
SELECT TOP %[2]d ItemCode, MAX(nm) AS description,
  CAST(SUM(qty) AS decimal(19,3)) AS qty_net, CAST(SUM(val) AS decimal(19,2)) AS value_net
FROM d GROUP BY ItemCode ORDER BY value_net DESC`, where, topN(app, 25))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "item", "branch", "warehouse", "cancelled")
	return c
}

func salesByBranchCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "by-branch",
		Short:   "Turnover by branch (BPLId) — the 'new' book only; the 'old' book has no branches",
		Example: "  saphist sales by-branch --fy 2022",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`WITH d AS (
  SELECT ISNULL(h.BPLId,0) AS bpl, h.BPLName AS nm, 1 AS docs, h.DocTotal - h.VatSum AS net, 0.0 AS ret FROM OINV h%[1]s
  UNION ALL
  SELECT ISNULL(h.BPLId,0), h.BPLName, 0, 0, h.DocTotal - h.VatSum FROM ORIN h%[1]s)
SELECT bpl AS bpl_id, MAX(nm) AS branch, SUM(docs) AS invoices,
  CAST(SUM(net) AS decimal(19,2)) AS net_sales, CAST(SUM(ret) AS decimal(19,2)) AS net_returns,
  CAST(SUM(net) - SUM(ret) AS decimal(19,2)) AS turnover
FROM d GROUP BY bpl ORDER BY turnover DESC`, salesWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "cancelled")
	return c
}

func salesReturnsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "returns",
		Short:   "List A/R credit notes (sales returns)",
		Aliases: []string{"credit-notes"},
		Example: "  saphist sales returns --fy 2021 -n 50",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  h.CardCode, h.CardName, h.BPLName AS branch,
  CAST(h.DocTotal AS decimal(19,2)) AS gross_incl_gst, CAST(h.VatSum AS decimal(19,2)) AS gst,
  CAST(h.DocTotal - h.VatSum AS decimal(19,2)) AS net, h.CANCELED AS cancelled, h.Comments
FROM ORIN h%s ORDER BY h.DocDate DESC, h.DocNum DESC`, topN(app, 40), salesWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled")
	return c
}
