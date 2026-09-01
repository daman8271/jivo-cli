package cli

// Orders — sales orders (ORDR) and purchase orders (OPOR), plus deliveries
// (ODLN) and goods receipt POs (OPDN), which is where an operator usually looks
// when reconciling what was ordered against what actually moved.

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newOrdersCmd) }

func newOrdersCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "orders",
		Short:   "Orders and movements — sales orders, purchase orders, deliveries, goods receipt POs",
		Aliases: []string{"order"},
	}
	c.AddCommand(ordersSalesCmd(app), ordersPurchaseCmd(app), ordersDeliveriesCmd(app),
		ordersReceiptsCmd(app), ordersShowCmd(app))
	return c
}

func ordersDocList(app *App, f *domFilters, table, label string) func(b Book) string {
	from, to := f.dates()
	return func(b Book) string {
		w := fWhere(fDateGE("h.DocDate", from), fDateLT("h.DocDate", to),
			fEqStr("h.CardCode", f.Party), fEqInt("h.BPLId", f.Branch),
			fLive("h.", f.IncludeCancelled), fOpen("h.", f.OpenOnly))
		return fmt.Sprintf(`SELECT TOP %d h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  CONVERT(varchar(10),h.DocDueDate,120) AS due_date, h.CardCode, h.CardName, h.NumAtCard AS their_ref,
  CAST(h.DocTotal AS decimal(19,2)) AS total, CAST(h.VatSum AS decimal(19,2)) AS gst,
  h.DocStatus AS status, h.CANCELED AS cancelled, h.Comments
FROM %s h%s ORDER BY h.DocDate DESC, h.DocNum DESC`, topN(app, 40), table, w)
	}
}

func ordersSubCmd(app *App, use, short, table string, aliases ...string) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     use,
		Short:   short,
		Aliases: aliases,
		Example: "  saphist orders " + use + " --fy 2021 --open -n 50",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			return runBooks(app, from, to, ordersDocList(app, &f, table, use))
		},
	}
	addDomFilters(c, &f, "date", "party", "branch", "cancelled", "open")
	return c
}

func ordersSalesCmd(app *App) *cobra.Command {
	return ordersSubCmd(app, "sales", "Sales orders (ORDR)", "ORDR", "so")
}

func ordersPurchaseCmd(app *App) *cobra.Command {
	return ordersSubCmd(app, "purchase", "Purchase orders (OPOR)", "OPOR", "po")
}

func ordersDeliveriesCmd(app *App) *cobra.Command {
	return ordersSubCmd(app, "deliveries", "Deliveries / goods issued to customers (ODLN)", "ODLN", "delivery")
}

func ordersReceiptsCmd(app *App) *cobra.Command {
	return ordersSubCmd(app, "receipts", "Goods receipt POs — what vendors actually delivered (OPDN)", "OPDN", "grpo")
}

func ordersShowCmd(app *App) *cobra.Command {
	var f domFilters
	var table string
	c := &cobra.Command{
		Use:     "show <DocNum>",
		Short:   "One order or movement document: header and lines (--table ORDR|OPOR|ODLN|OPDN)",
		Example: "  saphist orders show 5120 --table OPOR",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			lineTbl, ok := map[string]string{"ORDR": "RDR1", "OPOR": "POR1", "ODLN": "DLN1", "OPDN": "PDN1"}[table]
			if !ok {
				return Usagef("--table must be one of ORDR, OPOR, ODLN, OPDN (got %q)", table)
			}
			num := db.Lit(args[0])
			from, to := f.dates()
			b, err := findInBooks(app, from, to, "SELECT COUNT(*) FROM "+table+" WHERE DocNum = "+num)
			if err != nil {
				return err
			}
			if !app.Flags.Quiet && !app.Flags.JSON && !app.Flags.CSV && !app.Flags.Compact {
				fmt.Printf("book %s — %s (%s)\n\n", b.Key, b.DB, b.Company)
			}
			return runSections(app, b.DB, []section{
				{"header", `SELECT TOP 1 h.DocEntry, h.DocNum, CONVERT(varchar(10),h.DocDate,120) AS doc_date,
  CONVERT(varchar(10),h.DocDueDate,120) AS due_date, h.CardCode, h.CardName, h.NumAtCard AS their_ref,
  h.BPLName AS branch, CAST(h.DocTotal AS decimal(19,2)) AS total, CAST(h.VatSum AS decimal(19,2)) AS gst,
  h.DocStatus AS status, h.CANCELED AS cancelled, h.Comments
FROM ` + table + ` h WHERE h.DocNum = ` + num},
				{"lines", `SELECT l.LineNum, l.ItemCode, l.Dscription AS description, l.Quantity,
  l.OpenQty AS open_qty, CAST(l.Price AS decimal(19,4)) AS price,
  CAST(l.LineTotal AS decimal(19,2)) AS line_total, l.WhsCode AS warehouse, l.LineStatus AS status
FROM ` + lineTbl + ` l JOIN ` + table + ` h ON h.DocEntry = l.DocEntry
WHERE h.DocNum = ` + num + ` ORDER BY l.LineNum`},
			})
		},
	}
	addDomFilters(c, &f, "date")
	c.Flags().StringVar(&table, "table", "ORDR", "ORDR (sales order) | OPOR (purchase order) | ODLN (delivery) | OPDN (goods receipt PO)")
	return c
}
