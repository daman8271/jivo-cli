package cli

// Business partners — customers and vendors (OCRD), their balances, and their
// ledger statement (JDT1).
//
// LEDGER BALANCE = OCRD.Balance. POSITIVE = DEBIT (the party owes JIVO, or JIVO
// holds an advance against them); NEGATIVE = CREDIT (JIVO owes them). Same
// convention as the live system.
//
// Name search is a real server-side LIKE here — unlike the live Service Layer,
// where toupper()/tolower() are unsupported and names have to be matched in
// code. On this SQL Server the default collation is case-insensitive, so
// `party search jindal` finds JINDAL, Jindal and jindal alike.

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newPartyCmd) }

func newPartyCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "party",
		Short:   "Business partners — search by name, master card, balance, statement, open documents",
		Aliases: []string{"bp", "partner", "customer", "vendor"},
	}
	c.AddCommand(partySearchCmd(app), partyShowCmd(app), partyStatementCmd(app),
		partyBalancesCmd(app), partyOpenCmd(app))
	return c
}

// partyType maps --type to the OCRD.CardType letter.
func partyType(s string) (string, error) {
	switch s {
	case "":
		return "", nil
	case "customer", "c", "C":
		return "C", nil
	case "vendor", "supplier", "s", "S":
		return "S", nil
	case "lead", "l", "L":
		return "L", nil
	}
	return "", Usagef("unknown --type %q (customer | vendor | lead)", s)
}

func partySearchCmd(app *App) *cobra.Command {
	var typ string
	c := &cobra.Command{
		Use:     "search <text>",
		Short:   "Find partners whose CardCode or name contains the text (both books)",
		Example: "  saphist party search jindal\n  saphist party search 'oil mill' --type vendor",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ct, err := partyType(typ)
			if err != nil {
				return err
			}
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d CardCode, CardName,
  CASE CardType WHEN 'C' THEN 'customer' WHEN 'S' THEN 'vendor' WHEN 'L' THEN 'lead' ELSE CardType END AS type,
  CAST(Balance AS decimal(19,2)) AS balance, LicTradNum AS gstin, City, Country, Phone1,
  CASE WHEN validFor = 'N' THEN 'inactive' ELSE 'active' END AS state
FROM OCRD%s ORDER BY CardName`, topN(app, 40),
					fWhere("("+fLike("CardName", args[0])+" OR "+fLike("CardCode", args[0])+")", fEqStr("CardType", ct)))
			})
		},
	}
	c.Flags().StringVar(&typ, "type", "", "customer | vendor | lead")
	return c
}

func partyShowCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "show <CardCode>",
		Short:   "One partner's master card and balances, in every book that has it",
		Example: "  saphist party show CUSTA000606",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			code := db.Lit(args[0])
			return runBooks(app, "", "", func(b Book) string {
				return `SELECT TOP 1 CardCode, CardName,
  CASE CardType WHEN 'C' THEN 'customer' WHEN 'S' THEN 'vendor' WHEN 'L' THEN 'lead' ELSE CardType END AS type,
  CAST(Balance AS decimal(19,2)) AS balance,
  CAST(OrdersBal AS decimal(19,2)) AS open_orders, CAST(DNotesBal AS decimal(19,2)) AS open_deliveries,
  LicTradNum AS gstin, GroupCode, Currency, CreditLine AS credit_limit,
  Address, City, County AS district, Country, ZipCode, Phone1, Cellular, E_Mail,
  CASE WHEN validFor = 'N' THEN 'inactive' ELSE 'active' END AS state,
  CONVERT(varchar(10), CreateDate, 120) AS created
FROM OCRD WHERE CardCode = ` + code
			})
		},
	}
	return c
}

func partyStatementCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "statement <CardCode>",
		Short:   "Ledger statement: every journal line against the partner, with a running balance",
		Aliases: []string{"ledger"},
		Example: "  saphist party statement CUSTA000606 --fy 2021\n  saphist party statement VENDA000123 --from 2020-04-01 --to 2021-04-01",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			code := db.Lit(args[0])
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				w := fWhere("j.ShortName = "+code, fDateGE("j.RefDate", from), fDateLT("j.RefDate", to))
				return fmt.Sprintf(`SELECT TOP %d CONVERT(varchar(10), j.RefDate, 120) AS date,
  j.TransId, j.Line_ID AS line, j.BaseRef AS doc_ref, j.TransType AS doc_type, j.Ref1, j.Ref2,
  CAST(j.Debit AS decimal(19,2)) AS debit, CAST(j.Credit AS decimal(19,2)) AS credit,
  CAST(SUM(j.Debit - j.Credit) OVER (ORDER BY j.RefDate, j.TransId, j.Line_ID
       ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS decimal(19,2)) AS running_balance,
  j.LineMemo
FROM JDT1 j%s ORDER BY j.RefDate, j.TransId, j.Line_ID`, topN(app, 500), w)
			})
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func partyBalancesCmd(app *App) *cobra.Command {
	var typ string
	var owing string
	c := &cobra.Command{
		Use:     "balances",
		Short:   "Partner balances, biggest first (positive = they owe JIVO, negative = JIVO owes them)",
		Example: "  saphist party balances --type customer -n 25\n  saphist party balances --owing jivo --type vendor",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			ct, err := partyType(typ)
			if err != nil {
				return err
			}
			var dir, order string
			switch owing {
			case "":
				order = "ABS(Balance) DESC"
			case "them", "customer", "debtors":
				dir, order = "Balance > 0", "Balance DESC"
			case "jivo", "us", "creditors":
				dir, order = "Balance < 0", "Balance ASC"
			default:
				return Usagef("unknown --owing %q (them | jivo)", owing)
			}
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d CardCode, CardName,
  CASE CardType WHEN 'C' THEN 'customer' WHEN 'S' THEN 'vendor' ELSE CardType END AS type,
  CAST(Balance AS decimal(19,2)) AS balance,
  CASE WHEN Balance > 0 THEN 'DEBIT (owes JIVO)' WHEN Balance < 0 THEN 'CREDIT (JIVO owes)' ELSE '-' END AS side,
  LicTradNum AS gstin, City
FROM OCRD%s ORDER BY %s`, topN(app, 25), fWhere("Balance <> 0", fEqStr("CardType", ct), dir), order)
			})
		},
	}
	c.Flags().StringVar(&typ, "type", "", "customer | vendor | lead")
	c.Flags().StringVar(&owing, "owing", "", "them = debtors (they owe JIVO) | jivo = creditors (JIVO owes them)")
	return c
}

func partyOpenCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "open <CardCode>",
		Short:   "Documents still open for one partner (A/R invoices, A/P bills, orders)",
		Example: "  saphist party open CUSTA000606",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			code := db.Lit(args[0])
			from, to := f.dates()
			return runBooks(app, from, to, func(b Book) string {
				w := func(tbl string) string {
					return fWhere("h.CardCode = "+code, "h.DocStatus = 'O'", "ISNULL(h.CANCELED,'N') = 'N'",
						fDateGE("h.DocDate", from), fDateLT("h.DocDate", to))
				}
				return fmt.Sprintf(`SELECT TOP %[1]d doc_type, DocNum, doc_date, due_date,
  CAST(total AS decimal(19,2)) AS total, CAST(paid AS decimal(19,2)) AS paid,
  CAST(total - paid AS decimal(19,2)) AS balance_due
FROM (
  SELECT 'A/R invoice' AS doc_type, h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
         CONVERT(varchar(10),h.DocDueDate,120) AS due_date, h.DocTotal AS total, h.PaidToDate AS paid
  FROM OINV h%[2]s
  UNION ALL
  SELECT 'A/P invoice', h.DocNum, CONVERT(varchar(10),h.DocDate,120), CONVERT(varchar(10),h.DocDueDate,120),
         h.DocTotal, h.PaidToDate FROM OPCH h%[3]s
  UNION ALL
  SELECT 'sales order', h.DocNum, CONVERT(varchar(10),h.DocDate,120), CONVERT(varchar(10),h.DocDueDate,120),
         h.DocTotal, h.PaidToDate FROM ORDR h%[4]s
  UNION ALL
  SELECT 'purchase order', h.DocNum, CONVERT(varchar(10),h.DocDate,120), CONVERT(varchar(10),h.DocDueDate,120),
         h.DocTotal, h.PaidToDate FROM OPOR h%[5]s
) x ORDER BY doc_date DESC`, topN(app, 100), w("OINV"), w("OPCH"), w("ORDR"), w("OPOR"))
			})
		},
	}
	addDomFilters(c, &f, "date")
	return c
}
