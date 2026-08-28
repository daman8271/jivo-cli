package cli

// Accounting — AccountMaster (ledgers), TransactionMaster/Child (vouchers and
// their double entry), and RefMaster (bill-wise outstanding).
//
// Notes (verified live 2026-08-27):
//   - TransactionChild.ToBy is the side flag; DebitAmount/CreditAmount carry the
//     figures, so the balance is SUM(Debit) - SUM(Credit): POSITIVE = DEBIT.
//   - AccountMaster.DebitAmount/CreditAmount are the OPENING balances.
//   - RefMaster (582,298 rows) is the bill-wise reference ledger — one row per
//     document reference per account, with a DueDate. That is what makes
//     outstanding and ageing possible; it also has its own IsDeleted.
//   - TransactionMaster has IsDeleted; every read filters it.
//   - Accounting is live to today even while the sale feed is paused for a
//     physical audit, so this module is the freshest thing in the database.

import (
	"fmt"

	"github.com/spf13/cobra"

	"ary/internal/db"
)

func init() {
	register(newAccountsCmd)
	register(newLedgerCmd)
}

func newAccountsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "accounts",
		Short:   "Ledger master — accounts, groups, balances, outstanding, ageing",
		Aliases: []string{"account", "parties"},
	}
	c.AddCommand(accountsListCmd(app), accountsGetCmd(app), accountsGroupsCmd(app),
		accountsOutstandingCmd(app), accountsAgeingCmd(app))
	return c
}

func accountsListCmd(app *App) *cobra.Command {
	var f domFilters
	var group int
	c := &cobra.Command{
		Use:     "list",
		Short:   "List ledger accounts with their group, GSTIN, credit terms and opening balance",
		Example: "  ary accounts list --search \"jivo\"\n  ary accounts list --group 12 -n 50",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d a.AccountID AS id, a.AccountName AS account, g.GroupName AS group_, "+
				"a.GSTINNo AS gstin, a.PANNo AS pan, a.CreditDays AS credit_days, "+
				"CAST(a.CreditLimit AS decimal(18,2)) AS credit_limit, "+
				"CAST(a.DebitAmount - a.CreditAmount AS decimal(18,2)) AS opening_balance, "+
				"a.Phone AS phone, a.IsActive AS active "+
				"FROM AccountMaster a LEFT JOIN GroupMaster g ON g.GroupID = a.GroupID%s "+
				"ORDER BY a.AccountName", topN(app, 50),
				fWhere(fLike("a.AccountName", f.Search), fEqInt("a.GroupID", group), fActive("a.", f.ActiveOnly)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "active")
	c.Flags().IntVar(&group, "group", 0, "filter by GroupID (see `ary accounts groups`)")
	return c
}

func accountsGetCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <AccountID>",
		Short:   "One account: master row, computed balance, and open bill-wise references",
		Example: "  ary accounts get 1",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := db.Lit(args[0])
			return runSections(app, []section{
				{"master", "SELECT a.AccountID AS id, a.AccountName AS account, g.GroupName AS group_, " +
					"a.GSTINNo AS gstin, a.PANNo AS pan, a.CreditDays AS credit_days, " +
					"CAST(a.CreditLimit AS decimal(18,2)) AS credit_limit, a.Address1 AS address, a.Phone AS phone, " +
					"a.EMail AS email, a.IsActive AS active " +
					"FROM AccountMaster a LEFT JOIN GroupMaster g ON g.GroupID = a.GroupID WHERE a.AccountID = " + id},
				{"balance", "SELECT CAST(a.DebitAmount - a.CreditAmount AS decimal(18,2)) AS opening_balance, " +
					"CAST(ISNULL(t.dr,0) AS decimal(18,2)) AS debits, CAST(ISNULL(t.cr,0) AS decimal(18,2)) AS credits, " +
					"CAST(a.DebitAmount - a.CreditAmount + ISNULL(t.dr,0) - ISNULL(t.cr,0) AS decimal(18,2)) AS balance_dr_positive, " +
					"t.vouchers " +
					"FROM AccountMaster a LEFT JOIN (SELECT c.AccountID, SUM(c.DebitAmount) dr, SUM(c.CreditAmount) cr, " +
					"COUNT(DISTINCT c.SerialNumber) vouchers FROM TransactionChild c " +
					"JOIN TransactionMaster m ON m.SerialNumber = c.SerialNumber AND ISNULL(m.IsDeleted,0) = 0 " +
					"GROUP BY c.AccountID) t ON t.AccountID = a.AccountID WHERE a.AccountID = " + id},
				{"open references", "SELECT TOP 50 r.RefName AS reference, CONVERT(varchar(10), r.RefDate, 120) AS ref_date, " +
					"CONVERT(varchar(10), r.DueDate, 120) AS due_date, " +
					"CAST(SUM(r.DebitAmount - r.CreditAmount) AS decimal(18,2)) AS balance " +
					"FROM RefMaster r WHERE ISNULL(r.IsDeleted,0) = 0 AND r.AccountID = " + id +
					" GROUP BY r.RefName, r.RefDate, r.DueDate HAVING SUM(r.DebitAmount - r.CreditAmount) <> 0 " +
					"ORDER BY r.RefDate DESC"},
			})
		},
	}
}

func accountsGroupsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "groups",
		Short: "Account groups (the chart-of-accounts tree) with account counts",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := "SELECT g.GroupID AS id, g.GroupName AS group_, pg.GroupName AS parent_group, " +
				"gt.GroupTypeName AS group_type, " +
				"(SELECT COUNT(*) FROM AccountMaster a WHERE a.GroupID = g.GroupID) AS accounts, g.IsActive AS active " +
				"FROM GroupMaster g " +
				"LEFT JOIN GroupMaster pg ON pg.GroupID = g.ParentGroupID " +
				"LEFT JOIN GroupTypeMaster gt ON gt.GroupTypeID = g.GroupTypeID " +
				"ORDER BY g.GroupName"
			return runSelect(app, q)
		},
	}
}

func accountsOutstandingCmd(app *App) *cobra.Command {
	var f domFilters
	var minAmt float64
	c := &cobra.Command{
		Use:   "outstanding",
		Short: "Bill-wise outstanding per account from RefMaster (positive = they owe ARY)",
		Long: "Built from RefMaster, the bill-wise reference ledger, so it is document-level rather\n" +
			"than a single master figure. Positive balance = DEBIT = the party owes ARY; negative =\n" +
			"ARY owes them (a supplier, or a customer advance).",
		Example: "  ary accounts outstanding -n 40\n  ary accounts outstanding --min-amount 50000",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d r.AccountID AS id, a.AccountName AS account, g.GroupName AS group_, "+
				"COUNT(DISTINCT r.RefName) AS open_refs, "+
				"CAST(SUM(r.DebitAmount - r.CreditAmount) AS decimal(18,2)) AS balance, "+
				"CONVERT(varchar(10), MIN(r.RefDate), 120) AS oldest_ref, "+
				"CONVERT(varchar(10), MAX(r.RefDate), 120) AS newest_ref "+
				"FROM RefMaster r "+
				"LEFT JOIN AccountMaster a ON a.AccountID = r.AccountID "+
				"LEFT JOIN GroupMaster g ON g.GroupID = a.GroupID "+
				"WHERE ISNULL(r.IsDeleted,0) = 0%s "+
				"GROUP BY r.AccountID, a.AccountName, g.GroupName "+
				"HAVING ABS(SUM(r.DebitAmount - r.CreditAmount)) >= %.2f "+
				"ORDER BY balance DESC", topN(app, 40),
				fAnd(fLike("a.AccountName", f.Search), fEqInt("r.AccountID", f.Account)), minAmt)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "search", "account")
	c.Flags().Float64Var(&minAmt, "min-amount", 1, "ignore balances smaller than this in absolute value")
	return c
}

func accountsAgeingCmd(app *App) *cobra.Command {
	var asOf string
	c := &cobra.Command{
		Use:   "ageing",
		Short: "Ageing of open references into 0-30 / 31-60 / 61-90 / 91-180 / 180+ buckets",
		Long: "Ages each open RefMaster reference by its RefDate against --as-of (default today).\n" +
			"Only accounts with a non-zero net balance appear. This is a document-date ageing, not a\n" +
			"due-date ageing — the DueDate column is populated unevenly.",
		Example: "  ary accounts ageing\n  ary accounts ageing --as-of 2026-08-01 -n 30",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ref := "GETDATE()"
			if asOf != "" {
				ref = db.Lit(asOf)
			}
			bucket := func(lo, hi int) string {
				cond := fmt.Sprintf("DATEDIFF(day, r.RefDate, %s) >= %d", ref, lo)
				if hi > 0 {
					cond += fmt.Sprintf(" AND DATEDIFF(day, r.RefDate, %s) <= %d", ref, hi)
				}
				return "CAST(SUM(CASE WHEN " + cond + " THEN r.DebitAmount - r.CreditAmount ELSE 0 END) AS decimal(18,2))"
			}
			q := fmt.Sprintf("SELECT TOP %d r.AccountID AS id, a.AccountName AS account, "+
				"%s AS d0_30, %s AS d31_60, %s AS d61_90, %s AS d91_180, %s AS d180_plus, "+
				"CAST(SUM(r.DebitAmount - r.CreditAmount) AS decimal(18,2)) AS total "+
				"FROM RefMaster r LEFT JOIN AccountMaster a ON a.AccountID = r.AccountID "+
				"WHERE ISNULL(r.IsDeleted,0) = 0 AND r.RefDate > '1901-01-01' "+
				"GROUP BY r.AccountID, a.AccountName "+
				"HAVING ABS(SUM(r.DebitAmount - r.CreditAmount)) >= 1 ORDER BY total DESC",
				topN(app, 30), bucket(0, 30), bucket(31, 60), bucket(61, 90), bucket(91, 180), bucket(181, 0))
			return runSelect(app, q)
		},
	}
	c.Flags().StringVar(&asOf, "as-of", "", "age against this date instead of today (YYYY-MM-DD)")
	return c
}

func newLedgerCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "ledger",
		Short:   "Accounting vouchers — list, one voucher's double entry, an account's statement, trial balance",
		Aliases: []string{"vouchers", "journal"},
	}
	c.AddCommand(ledgerVouchersCmd(app), ledgerVoucherCmd(app), ledgerStatementCmd(app), ledgerTrialCmd(app))
	return c
}

func ledgerVouchersCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "list",
		Short:   "List accounting vouchers (newest first) with their debit total",
		Example: "  ary ledger list --from 2026-08-20\n  ary ledger list -n 30",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d m.SerialNumber AS serial, CONVERT(varchar(16), m.VoucherDate, 120) AS date, "+
				"ISNULL(m.VchIDPrefix,'') + CAST(m.VchNumber AS varchar(16)) AS doc_no, v.VoucherName AS voucher, "+
				"l.LocationName AS location, m.Narration AS narration, "+
				"CAST((SELECT SUM(c.DebitAmount) FROM TransactionChild c WHERE c.SerialNumber = m.SerialNumber) AS decimal(18,2)) AS debit_total, "+
				"u.UserName AS entered_by, CONVERT(varchar(16), m.RecordDateTime, 120) AS entered_at "+
				"FROM TransactionMaster m "+
				"LEFT JOIN VoucherMaster v ON v.VoucherID = m.VoucherID "+
				"LEFT JOIN LocationMaster l ON l.LocationID = m.LocationID "+
				"LEFT JOIN UserMaster u ON u.UserID = m.UserID "+
				"WHERE ISNULL(m.IsDeleted,0) = 0%s "+
				"ORDER BY m.VoucherDate DESC, m.SerialNumber DESC", topN(app, 40),
				fAnd(fDateGE("m.VoucherDate", f.From), fDateLT("m.VoucherDate", f.To), fEqInt("m.LocationID", f.Location)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date", "location")
	return c
}

func ledgerVoucherCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:     "get <SerialNumber>",
		Short:   "One voucher: header plus its full double entry",
		Example: "  ary ledger get 1111478",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			sn := db.Lit(args[0])
			return runSections(app, []section{
				{"header", "SELECT m.SerialNumber AS serial, CONVERT(varchar(16), m.VoucherDate, 120) AS date, " +
					"ISNULL(m.VchIDPrefix,'') + CAST(m.VchNumber AS varchar(16)) AS doc_no, v.VoucherName AS voucher, " +
					"l.LocationName AS location, m.Narration AS narration, u.UserName AS entered_by, " +
					"CONVERT(varchar(16), m.RecordDateTime, 120) AS entered_at, m.IsDeleted AS is_deleted " +
					"FROM TransactionMaster m " +
					"LEFT JOIN VoucherMaster v ON v.VoucherID = m.VoucherID " +
					"LEFT JOIN LocationMaster l ON l.LocationID = m.LocationID " +
					"LEFT JOIN UserMaster u ON u.UserID = m.UserID WHERE m.SerialNumber = " + sn},
				{"entries", "SELECT c.SrlNo AS line, a.AccountName AS account, " +
					"CAST(c.DebitAmount AS decimal(18,2)) AS debit, CAST(c.CreditAmount AS decimal(18,2)) AS credit, " +
					"cc.CostCenterName AS cost_center, c.Narration AS narration " +
					"FROM TransactionChild c " +
					"LEFT JOIN AccountMaster a ON a.AccountID = c.AccountID " +
					"LEFT JOIN CostCenterMaster cc ON cc.CostCenterID = c.CostCenterID " +
					"WHERE c.SerialNumber = " + sn + " ORDER BY c.SrlNo"},
			})
		},
	}
}

func ledgerStatementCmd(app *App) *cobra.Command {
	var f domFilters
	var days int
	c := &cobra.Command{
		Use:   "statement",
		Short: "An account's statement for a window: opening balance, then every line with a running balance",
		Long: "The party ledger — built from TransactionChild joined to its voucher, so it includes journal\n" +
			"entries, not just sale and purchase documents. Debit-positive.\n\n" +
			"It is WINDOWED on purpose: the busiest accounts here carry over half a million lines\n" +
			"(Cash 561,552; Sales A/C 1,088,340), and a running balance across all of them cannot be\n" +
			"computed inside a query timeout. Without --from it uses the last --days (default 90), and\n" +
			"the opening section carries every earlier line, so the running balance is still correct.",
		Example: "  ary ledger statement --account 1\n" +
			"  ary ledger statement --account 1 --from 2026-08-01 --to 2026-09-01\n" +
			"  ary ledger statement --account 2072 --days 7",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			if f.Account == 0 {
				return Usagef("give --account <AccountID> (find it with `ary accounts list --search <name>`)")
			}
			// Resolve the window. --from wins; otherwise the last --days.
			from := f.From
			fromExpr := db.Lit(from)
			if from == "" {
				fromExpr = fmt.Sprintf("CAST(DATEADD(day, -%d, GETDATE()) AS date)", days)
			}
			acct := fmt.Sprintf("%d", f.Account)
			toClause := fAnd(fDateLT("m.VoucherDate", f.To))

			// Opening = master opening + every posted line strictly BEFORE the window.
			opening := "(SELECT CAST(a.DebitAmount - a.CreditAmount AS decimal(18,2)) FROM AccountMaster a WHERE a.AccountID = " + acct + ")" +
				" + ISNULL((SELECT SUM(c2.DebitAmount - c2.CreditAmount) FROM TransactionChild c2 " +
				"JOIN TransactionMaster m2 ON m2.SerialNumber = c2.SerialNumber AND ISNULL(m2.IsDeleted,0) = 0 " +
				"WHERE c2.AccountID = " + acct + " AND m2.VoucherDate < " + fromExpr + "), 0)"

			return runSections(app, []section{
				{"opening", "SELECT a.AccountName AS account, " + fromExpr + " AS window_from, " +
					"CAST(" + opening + " AS decimal(18,2)) AS opening_balance_dr_positive " +
					"FROM AccountMaster a WHERE a.AccountID = " + acct},
				{"lines", fmt.Sprintf("SELECT TOP %d CONVERT(varchar(10), m.VoucherDate, 120) AS date, "+
					"ISNULL(m.VchIDPrefix,'') + CAST(m.VchNumber AS varchar(16)) AS doc_no, v.VoucherName AS voucher, "+
					"CAST(c.DebitAmount AS decimal(18,2)) AS debit, CAST(c.CreditAmount AS decimal(18,2)) AS credit, "+
					"CAST(%s + SUM(c.DebitAmount - c.CreditAmount) OVER (ORDER BY m.VoucherDate, m.SerialNumber, c.SrlNo "+
					"ROWS UNBOUNDED PRECEDING) AS decimal(18,2)) AS running_balance, "+
					"COALESCE(NULLIF(c.Narration,''), m.Narration) AS narration "+
					"FROM TransactionChild c "+
					"JOIN TransactionMaster m ON m.SerialNumber = c.SerialNumber AND ISNULL(m.IsDeleted,0) = 0 "+
					"LEFT JOIN VoucherMaster v ON v.VoucherID = m.VoucherID "+
					"WHERE c.AccountID = %s AND m.VoucherDate >= %s%s "+
					"ORDER BY m.VoucherDate, m.SerialNumber, c.SrlNo",
					topN(app, 200), opening, acct, fromExpr, toClause)},
			})
		},
	}
	addDomFilters(c, &f, "date", "account")
	c.Flags().IntVar(&days, "days", 90, "window length in days when --from is not given")
	return c
}

func ledgerTrialCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:   "trial",
		Short: "Trial-balance style rollup by account group (opening + movement)",
		Long: "Groups the movement in TransactionChild by account group and adds AccountMaster's\n" +
			"opening balances. Debit-positive. Use --from/--to to bound the movement; the opening\n" +
			"column is always the master opening, so a bounded window is movement-only arithmetic.",
		Example: "  ary ledger trial --from 2026-04-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			q := fmt.Sprintf("SELECT TOP %d g.GroupName AS group_, COUNT(DISTINCT a.AccountID) AS accounts, "+
				"CAST(SUM(a.DebitAmount - a.CreditAmount) AS decimal(18,2)) AS opening, "+
				"CAST(ISNULL(SUM(t.dr),0) AS decimal(18,2)) AS debits, "+
				"CAST(ISNULL(SUM(t.cr),0) AS decimal(18,2)) AS credits, "+
				"CAST(ISNULL(SUM(t.dr),0) - ISNULL(SUM(t.cr),0) AS decimal(18,2)) AS movement "+
				"FROM AccountMaster a "+
				"LEFT JOIN GroupMaster g ON g.GroupID = a.GroupID "+
				"LEFT JOIN (SELECT c.AccountID, SUM(c.DebitAmount) dr, SUM(c.CreditAmount) cr "+
				"FROM TransactionChild c JOIN TransactionMaster m ON m.SerialNumber = c.SerialNumber "+
				"AND ISNULL(m.IsDeleted,0) = 0%s GROUP BY c.AccountID) t ON t.AccountID = a.AccountID "+
				"GROUP BY g.GroupName ORDER BY ABS(ISNULL(SUM(t.dr),0) - ISNULL(SUM(t.cr),0)) DESC",
				topN(app, 60), fAnd(fDateGE("m.VoucherDate", f.From), fDateLT("m.VoucherDate", f.To)))
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}
