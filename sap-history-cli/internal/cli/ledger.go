package cli

// General ledger — chart of accounts (OACT), journal entries (OJDT/JDT1),
// account ledgers and a trial balance.
//
// JDT1 is the single source of truth for every posting: documents, payments and
// manual journals all land here. Debit and Credit are separate columns; the
// signed movement is (Debit - Credit).

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newLedgerCmd) }

func newLedgerCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "ledger",
		Short:   "General ledger — accounts, one account's entries, trial balance, one journal entry",
		Aliases: []string{"gl", "accounts"},
	}
	c.AddCommand(ledgerAccountsCmd(app), ledgerAccountCmd(app), ledgerTrialCmd(app),
		ledgerJournalCmd(app), ledgerEntriesCmd(app))
	return c
}

func ledgerAccountsCmd(app *App) *cobra.Command {
	var f domFilters
	var postableOnly bool
	c := &cobra.Command{
		Use:     "chart",
		Short:   "Chart of accounts (--search by code or name)",
		Aliases: []string{"list"},
		Example: "  saphist ledger chart --search freight\n  saphist ledger chart --search 5100 --postable",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			var post string
			if postableOnly {
				post = "a.Postable = 'Y'"
			}
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d a.AcctCode, a.AcctName, a.Levels AS level,
  CASE a.Postable WHEN 'Y' THEN 'postable' ELSE 'title' END AS kind,
  a.ActType AS act_type, CAST(a.CurrTotal AS decimal(19,2)) AS balance, a.FatherNum AS parent
FROM OACT a%s ORDER BY a.AcctCode`, topN(app, 60),
					fWhere("("+fLike("a.AcctName", f.Search)+" OR "+fLike("a.AcctCode", f.Search)+")", post))
			})
		},
	}
	addDomFilters(c, &f, "search")
	c.Flags().BoolVar(&postableOnly, "postable", false, "only accounts you can post to (exclude title/summary rows)")
	return c
}

func ledgerAccountCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "account <AcctCode>",
		Short:   "One G/L account: every journal line with a running balance",
		Example: "  saphist ledger account 5100016 --fy 2021\n  saphist ledger account 5100016 --from 2021-04-01 --to 2021-07-01",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			code := db.Lit(args[0])
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				w := fWhere("j.Account = "+code, fDateGE("j.RefDate", from), fDateLT("j.RefDate", to))
				return fmt.Sprintf(`SELECT TOP %d CONVERT(varchar(10), j.RefDate, 120) AS date,
  j.TransId, j.Line_ID AS line, j.BaseRef AS doc_ref, j.TransType AS doc_type,
  j.ShortName AS contra, j.ContraAct AS contra_account,
  CAST(j.Debit AS decimal(19,2)) AS debit, CAST(j.Credit AS decimal(19,2)) AS credit,
  CAST(SUM(j.Debit - j.Credit) OVER (ORDER BY j.RefDate, j.TransId, j.Line_ID
       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS decimal(19,2)) AS running_balance,
  j.LineMemo, j.Ref1, j.Ref2
FROM JDT1 j%s ORDER BY j.RefDate, j.TransId, j.Line_ID`, topN(app, 500), w)
			})
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func ledgerTrialCmd(app *App) *cobra.Command {
	var f domFilters
	var nonZero bool
	c := &cobra.Command{
		Use:     "trial-balance",
		Short:   "Trial balance from JDT1 for a period: debits, credits and net movement per account",
		Aliases: []string{"tb"},
		Example: "  saphist ledger trial-balance --fy 2021 -n 200\n  saphist ledger trial-balance --from 2016-04-01 --to 2017-04-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			if from == "" && to == "" {
				return Usagef("a trial balance needs a period: pass --fy, --year, or --from/--to")
			}
			var having string
			if nonZero {
				having = " HAVING SUM(j.Debit - j.Credit) <> 0"
			}
			return runBooks(app, from, to, func(b Book) string {
				w := fWhere(fDateGE("j.RefDate", from), fDateLT("j.RefDate", to), fEqStr("j.Account", f.Account))
				return fmt.Sprintf(`SELECT TOP %d j.Account AS acct_code, MAX(a.AcctName) AS acct_name,
  COUNT(*) AS lines,
  CAST(SUM(j.Debit) AS decimal(19,2)) AS debit,
  CAST(SUM(j.Credit) AS decimal(19,2)) AS credit,
  CAST(SUM(j.Debit - j.Credit) AS decimal(19,2)) AS net_movement
FROM JDT1 j LEFT JOIN OACT a ON a.AcctCode = j.Account%s
GROUP BY j.Account%s ORDER BY ABS(SUM(j.Debit - j.Credit)) DESC`, topN(app, 100), w, having)
			})
		},
	}
	addDomFilters(c, &f, "date", "account")
	c.Flags().BoolVar(&nonZero, "non-zero", false, "hide accounts whose net movement is zero")
	return c
}

func ledgerJournalCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "journal <TransId>",
		Short:   "One journal entry: header and every line, both sides",
		Aliases: []string{"je"},
		Example: "  saphist ledger journal 184233",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := db.Lit(args[0])
			from, to := f.dates()
			b, err := findInBooks(app, from, to, "SELECT COUNT(*) FROM OJDT WHERE TransId = "+id)
			if err != nil {
				return err
			}
			if !app.Flags.Quiet && !app.Flags.JSON && !app.Flags.CSV && !app.Flags.Compact {
				fmt.Printf("book %s — %s (%s)\n\n", b.Key, b.DB, b.Company)
			}
			return runSections(app, b.DB, []section{
				{"header", `SELECT TOP 1 TransId, Number, CONVERT(varchar(10),RefDate,120) AS ref_date,
  CONVERT(varchar(10),DueDate,120) AS due_date, CONVERT(varchar(10),TaxDate,120) AS tax_date,
  TransType AS source_type, BaseRef AS source_doc, Memo, Ref1, Ref2,
  CAST(LocTotal AS decimal(19,2)) AS total, CreatedBy, CONVERT(varchar(16),CreateDate,120) AS created
FROM OJDT WHERE TransId = ` + id},
				{"lines", `SELECT j.Line_ID AS line, j.Account, a.AcctName, j.ShortName AS bp_or_acct,
  CAST(j.Debit AS decimal(19,2)) AS debit, CAST(j.Credit AS decimal(19,2)) AS credit,
  j.LineMemo, j.ContraAct AS contra_account, j.Ref1, j.Ref2
FROM JDT1 j LEFT JOIN OACT a ON a.AcctCode = j.Account WHERE j.TransId = ` + id + ` ORDER BY j.Line_ID`},
			})
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func ledgerEntriesCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "entries",
		Short:   "List journal entries for a period (headers only)",
		Example: "  saphist ledger entries --fy 2021 -n 50",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				w := fWhere(fDateGE("RefDate", from), fDateLT("RefDate", to), fLike("Memo", f.Search))
				return fmt.Sprintf(`SELECT TOP %d TransId, Number, CONVERT(varchar(10),RefDate,120) AS ref_date,
  TransType AS source_type, BaseRef AS source_doc, Memo,
  CAST(LocTotal AS decimal(19,2)) AS total, CreatedBy
FROM OJDT%s ORDER BY RefDate DESC, TransId DESC`, topN(app, 40), w)
			})
		},
	}
	addDomFilters(c, &f, "date", "search")
	return c
}
