package cli

// Items and stock — OITM (item master), OITW (per-warehouse stock), and the
// inventory movement behind them.
//
// Quantities are in the item's inventory UoM. As in the live system, a "20 PCS"
// in an item name is carton configuration, NOT a multiplier — INV1.Quantity is
// already in pieces (correction C-0001).

import (
	"fmt"

	"github.com/spf13/cobra"

	"saphist/internal/db"
)

func init() { register(newItemsCmd) }

func newItemsCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "items",
		Short:   "Items — search, one item, closing stock by warehouse, movement history",
		Aliases: []string{"item", "stock"},
	}
	c.AddCommand(itemsSearchCmd(app), itemsShowCmd(app), itemsStockCmd(app), itemsMovementCmd(app))
	return c
}

func itemsSearchCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "search <text>",
		Short:   "Find items whose code or name contains the text",
		Example: "  saphist items search mustard\n  saphist items search 'olive 1 ltr'",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d i.ItemCode, i.ItemName, g.ItmsGrpNam AS item_group,
  CAST(i.OnHand AS decimal(19,3)) AS on_hand, i.InvntItem AS stock_item,
  i.SellItem AS sold, i.PrchseItem AS bought,
  CAST(i.LastPurPrc AS decimal(19,4)) AS last_purchase_price,
  CONVERT(varchar(10), i.LastPurDat, 120) AS last_purchase_date
FROM OITM i LEFT JOIN OITB g ON g.ItmsGrpCod = i.ItmsGrpCod%s ORDER BY i.ItemCode`, topN(app, 40),
					fWhere("("+fLike("i.ItemName", args[0])+" OR "+fLike("i.ItemCode", args[0])+")"))
			})
		},
	}
	addDomFilters(c, &f, "search")
	return c
}

func itemsShowCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "show <ItemCode>",
		Short:   "One item's master card",
		Example: "  saphist items show FG0000123",
		Args:    cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			code := db.Lit(args[0])
			return runBooks(app, "", "", func(b Book) string {
				return `SELECT TOP 1 i.ItemCode, i.ItemName, i.FrgnName, g.ItmsGrpNam AS item_group,
  CAST(i.OnHand AS decimal(19,3)) AS on_hand, CAST(i.IsCommited AS decimal(19,3)) AS committed,
  CAST(i.OnOrder AS decimal(19,3)) AS on_order,
  i.InvntItem AS stock_item, i.SellItem AS sold, i.PrchseItem AS bought,
  i.BuyUnitMsr AS buy_uom, i.NumInBuy AS per_buy_unit, i.SalUnitMsr AS sell_uom, i.NumInSale AS per_sale_unit,
  i.CodeBars AS barcode, i.DfltWH AS default_warehouse, i.CardCode AS preferred_vendor,
  CAST(i.LastPurPrc AS decimal(19,4)) AS last_purchase_price,
  CONVERT(varchar(10), i.LastPurDat, 120) AS last_purchase_date,
  CONVERT(varchar(10), i.CreateDate, 120) AS created
FROM OITM i LEFT JOIN OITB g ON g.ItmsGrpCod = i.ItmsGrpCod WHERE i.ItemCode = ` + code
			})
		},
	}
	return c
}

func itemsStockCmd(app *App) *cobra.Command {
	var f domFilters
	var nonZero bool
	c := &cobra.Command{
		Use:   "stock",
		Short: "Closing stock by item and warehouse, AS THE BOOK WAS CLOSED (OITW is a snapshot, not a date query)",
		Long: "OITW.OnHand is the balance frozen at the moment the book stopped being posted to —\n" +
			"2019-08 for the 'old' book, 2024-10 for the 'new' one. It is NOT an as-at-date figure.\n" +
			"For stock movement between two dates use `saphist items movement`.",
		Example: "  saphist items stock --item FG0000123\n  saphist items stock --warehouse 01 --non-zero -n 100",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			var nz string
			if nonZero {
				nz = "w.OnHand <> 0"
			}
			return runBooks(app, "", "", func(b Book) string {
				return fmt.Sprintf(`SELECT TOP %d w.ItemCode, i.ItemName, w.WhsCode AS warehouse, h.WhsName AS warehouse_name,
  CAST(w.OnHand AS decimal(19,3)) AS on_hand, CAST(w.IsCommited AS decimal(19,3)) AS committed,
  CAST(w.OnOrder AS decimal(19,3)) AS on_order, CAST(w.AvgPrice AS decimal(19,4)) AS avg_cost,
  CAST(w.OnHand * w.AvgPrice AS decimal(19,2)) AS stock_value
FROM OITW w LEFT JOIN OITM i ON i.ItemCode = w.ItemCode LEFT JOIN OWHS h ON h.WhsCode = w.WhsCode%s
ORDER BY stock_value DESC`, topN(app, 60),
					fWhere(fEqStr("w.ItemCode", f.Item), fEqStr("w.WhsCode", f.Warehouse), nz))
			})
		},
	}
	addDomFilters(c, &f, "item", "warehouse")
	c.Flags().BoolVar(&nonZero, "non-zero", false, "hide rows with zero on-hand")
	return c
}

func itemsMovementCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "movement",
		Short:   "Inventory movement for a period: bought, sold, returned, per item",
		Example: "  saphist items movement --item FG0000123 --fy 2021\n  saphist items movement --fy 2021 -n 30",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			from, to := f.dates()
			if from == "" && to == "" {
				return Usagef("movement needs a period: pass --fy, --year, or --from/--to")
			}
			return runBooks(app, from, to, func(b Book) string {
				w := func(alias string) string {
					return fWhere(fDateGE(alias+".DocDate", from), fDateLT(alias+".DocDate", to),
						fEqStr("l.ItemCode", f.Item), fEqStr("l.WhsCode", f.Warehouse),
						"ISNULL("+alias+".CANCELED,'N') = 'N'")
				}
				return fmt.Sprintf(`WITH m AS (
  SELECT l.ItemCode, l.Quantity AS sold, 0.0 AS sales_ret, 0.0 AS bought, 0.0 AS purch_ret
  FROM INV1 l JOIN OINV h ON h.DocEntry = l.DocEntry%[1]s
  UNION ALL SELECT l.ItemCode, 0, l.Quantity, 0, 0 FROM RIN1 l JOIN ORIN h ON h.DocEntry = l.DocEntry%[1]s
  UNION ALL SELECT l.ItemCode, 0, 0, l.Quantity, 0 FROM PCH1 l JOIN OPCH h ON h.DocEntry = l.DocEntry%[1]s
  UNION ALL SELECT l.ItemCode, 0, 0, 0, l.Quantity FROM RPC1 l JOIN ORPC h ON h.DocEntry = l.DocEntry%[1]s)
SELECT TOP %[2]d m.ItemCode, MAX(i.ItemName) AS item_name,
  CAST(SUM(m.bought) AS decimal(19,3)) AS bought,
  CAST(SUM(m.purch_ret) AS decimal(19,3)) AS purchase_returns,
  CAST(SUM(m.sold) AS decimal(19,3)) AS sold,
  CAST(SUM(m.sales_ret) AS decimal(19,3)) AS sales_returns,
  CAST(SUM(m.bought - m.purch_ret - m.sold + m.sales_ret) AS decimal(19,3)) AS net_movement
FROM m LEFT JOIN OITM i ON i.ItemCode = m.ItemCode
GROUP BY m.ItemCode ORDER BY ABS(SUM(m.sold)) DESC`, w("h"), topN(app, 40))
			})
		},
	}
	addDomFilters(c, &f, "date", "item", "warehouse")
	return c
}
