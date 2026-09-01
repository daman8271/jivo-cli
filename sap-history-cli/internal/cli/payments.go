package cli

// Payments — incoming receipts (ORCT) and outgoing payments (OVPM).
//
// The cancel flag on payments is `Canceled` (one L), not the documents'
// `CANCELED`. SQL Server's default collation is case-insensitive so one
// spelling would work for both, but the queries here use each table's own.

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newPaymentsCmd) }

func newPaymentsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "payments",
		Short:   "Payments — money in (receipts), money out (vendor payments), one payment",
		Aliases: []string{"payment", "pay"},
	}
	c.AddCommand(payInCmd(app), payOutCmd(app), payShowCmd(app), paySummaryCmd(app))
	return c
}

func payWhere(f *domFilters, from, to string) string {
	return fWhere(
		fDateGE("h.DocDate", from),
		fDateLT("h.DocDate", to),
		fEqStr("h.CardCode", f.Party),
		payLive(f.IncludeCancelled),
	)
}

func payLive(includeCancelled bool) string {
	if includeCancelled {
		return ""
	}
	return "ISNULL(h.Canceled,'N') = 'N'"
}

const payCols = `h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date, h.CardCode, h.CardName,
  CAST(h.DocTotal AS decimal(19,2)) AS total,
  CAST(h.CashSum AS decimal(19,2)) AS cash, CAST(h.CheckSum AS decimal(19,2)) AS cheque,
  CAST(h.TrsfrSum AS decimal(19,2)) AS bank_transfer, h.TrsfrRef AS transfer_ref,
  h.Canceled AS cancelled, h.Ref1, h.Ref2, h.Comments, h.TransId AS journal_transid`

func payInCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "in",
		Short:   "Incoming payments / receipts from customers",
		Aliases: []string{"incoming", "receipts"},
		Example: "  saphist payments in --fy 2021 -n 50\n  saphist payments in --party CUSTA000606",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d %s FROM ORCT h%s ORDER BY h.DocDate DESC, h.DocNum DESC`,
					topN(app, 40), payCols, payWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "cancelled")
	return c
}

func payOutCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "out",
		Short:   "Outgoing payments to vendors",
		Aliases: []string{"outgoing", "vendor"},
		Example: "  saphist payments out --fy 2021 -n 50\n  saphist payments out --party VENDA000123",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d %s FROM OVPM h%s ORDER BY h.DocDate DESC, h.DocNum DESC`,
					topN(app, 40), payCols, payWhere(&f, from, to))
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "cancelled")
	return c
}

func paySummaryCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "summary",
		Short:   "Money in and money out for a period, with the cash/cheque/transfer split",
		Example: "  saphist payments summary --fy 2021",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				w := payWhere(&f, from, to)
				return fmt.Sprintf(`SELECT
  (SELECT COUNT(*) FROM ORCT h%[1]s) AS receipts,
  CAST((SELECT ISNULL(SUM(h.DocTotal),0) FROM ORCT h%[1]s) AS decimal(19,2)) AS money_in,
  CAST((SELECT ISNULL(SUM(h.CashSum),0) FROM ORCT h%[1]s) AS decimal(19,2)) AS in_cash,
  CAST((SELECT ISNULL(SUM(h.CheckSum),0) FROM ORCT h%[1]s) AS decimal(19,2)) AS in_cheque,
  CAST((SELECT ISNULL(SUM(h.TrsfrSum),0) FROM ORCT h%[1]s) AS decimal(19,2)) AS in_transfer,
  (SELECT COUNT(*) FROM OVPM h%[1]s) AS payments,
  CAST((SELECT ISNULL(SUM(h.DocTotal),0) FROM OVPM h%[1]s) AS decimal(19,2)) AS money_out,
  CAST((SELECT ISNULL(SUM(h.CashSum),0) FROM OVPM h%[1]s) AS decimal(19,2)) AS out_cash,
  CAST((SELECT ISNULL(SUM(h.CheckSum),0) FROM OVPM h%[1]s) AS decimal(19,2)) AS out_cheque,
  CAST((SELECT ISNULL(SUM(h.TrsfrSum),0) FROM OVPM h%[1]s) AS decimal(19,2)) AS out_transfer`, w)
			})
		},
	}
	addDomFilters(c, &f, "date", "party", "cancelled")
	return c
}

func payShowCmd(app *App) *cobra.Command {
	var f domFilters
	var out bool
	c := &cobra.Command{
		Use:     "show <DocNum>",
		Short:   "One payment: header, what it was applied to, and the journal it posted",
		Example: "  saphist payments show 4521\n  saphist payments show 4521 --out",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			num := db.Lit(args[0])
			tbl, lines := "ORCT", "RCT2"
			if out {
				tbl, lines = "OVPM", "VPM2"
			}
			from, to := f.dates()
			b, err := findInBooks(app, from, to, "SELECT COUNT(*) FROM "+tbl+" WHERE DocNum = "+num)
			if err != nil {
				return err
			}
			if !app.Flags.Quiet && !app.Flags.JSON && !app.Flags.CSV && !app.Flags.Compact {
				fmt.Printf("book %s — %s (%s)\n\n", b.Key, b.DB, b.Company)
			}
			return runSections(app, b.DB, []section{
				{"header", `SELECT TOP 1 h.DocEntry, ` + payCols + ` FROM ` + tbl + ` h WHERE h.DocNum = ` + num},
				{"applied to", `SELECT l.InvType AS doc_type, l.DocEntry AS applied_doc_entry,
  CAST(l.SumApplied AS decimal(19,2)) AS applied, CAST(l.AppliedSys AS decimal(19,2)) AS applied_sys
FROM ` + lines + ` l JOIN ` + tbl + ` h ON h.DocEntry = l.DocNum WHERE h.DocNum = ` + num},
				{"journal", `SELECT j.Line_ID, j.Account, a.AcctName, j.ShortName,
  CAST(j.Debit AS decimal(19,2)) AS debit, CAST(j.Credit AS decimal(19,2)) AS credit, j.LineMemo
FROM JDT1 j JOIN ` + tbl + ` h ON h.TransId = j.TransId LEFT JOIN OACT a ON a.AcctCode = j.Account
WHERE h.DocNum = ` + num + ` ORDER BY j.Line_ID`},
			})
		},
	}
	addDomFilters(c, &f, "date")
	c.Flags().BoolVar(&out, "out", false, "look in outgoing payments (OVPM) instead of receipts (ORCT)")
	return c
}
