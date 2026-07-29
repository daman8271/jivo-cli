package cli

// Domain commands for the e-commerce marketplace channel (Amazon / Flipkart):
// online invoices, returns and settlement payouts. See domain.go for the shared
// helper conventions. These are append-only load tables — they carry NO
// `deleted` column, so fLive() is intentionally NOT applied here (validity is
// tracked via filename / loadingid instead).

import (
	"fmt"

	"github.com/spf13/cobra"
)

func init() { register(newEcomCmd) }

func newEcomCmd(app *App) *cobra.Command {
	c := &cobra.Command{
		Use:     "ecom",
		Short:   "E-commerce marketplace channel — sales, returns, settlements (Amazon/Flipkart)",
		Aliases: []string{"marketplace", "online"},
	}
	c.AddCommand(
		ecomSalesCmd(app),
		ecomReturnsCmd(app),
		ecomSettlementsCmd(app),
		ecomCountCmd(app),
	)
	return c
}

// ecomSalesCols is the friendly column set for the online sales register.
const ecomSalesCols = "CAST(Invoice_Date AS date) AS inv_date, Invoice_Number, Order_Id, " +
	"Sku, Asin, Quantity, ship_to_state, fulfillment_channel, " +
	"principal_amount, invoice_amount, total_tax_amount, Transaction_Type"

func ecomSalesCmd(app *App) *cobra.Command {
	var f domFilters
	var sku, state string
	c := &cobra.Command{
		Use:     "sales",
		Short:   "Online marketplace sales register (tbl_ecom_sales), by Invoice_Date",
		Example: "  dsr ecom sales --from 2026-07-01 --to 2026-08-01\n  dsr ecom sales --sku SUNFLOWER-OIL-5L-FBA -n 50 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fDateGE("Invoice_Date", f.From),
				fDateLT("Invoice_Date", f.To),
				fEqStr("Sku", sku),
				fEqStr("ship_to_state", state),
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_ecom_sales%s ORDER BY Invoice_Date DESC",
				topN(app, 100), ecomSalesCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	c.Flags().StringVar(&sku, "sku", "", "filter by marketplace Sku (exact)")
	c.Flags().StringVar(&state, "state", "", "filter by ship-to state")
	return c
}

// ecomReturnsCols is the friendly column set for the returns register.
const ecomReturnsCols = "date AS return_date, order_id, sku, sale_bom, sale_bom_descr, qty, condition, filename"

func ecomReturnsCmd(app *App) *cobra.Command {
	var f domFilters
	var sku, cond string
	c := &cobra.Command{
		Use:     "returns",
		Short:   "Marketplace returns by SKU/BOM & condition (tbl_ecom_returns), by date",
		Example: "  dsr ecom returns --from 2026-07-01 --to 2026-08-01\n  dsr ecom returns --condition OK --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fDateGE("date", f.From),
				fDateLT("date", f.To),
				fEqStr("sku", sku),
				fEqStr("condition", cond),
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_ecom_returns%s ORDER BY date DESC",
				topN(app, 100), ecomReturnsCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	c.Flags().StringVar(&sku, "sku", "", "filter by return sku (exact)")
	c.Flags().StringVar(&cond, "condition", "", "filter by item condition (e.g. OK)")
	return c
}

// ecomSettlementsCols is the friendly column set for settlement payouts.
const ecomSettlementsCols = "settlement_id, sstartdate, senddate, depositdate, currency, totalamt"

func ecomSettlementsCmd(app *App) *cobra.Command {
	var f domFilters
	c := &cobra.Command{
		Use:     "settlements",
		Short:   "Marketplace settlement payouts deposited to bank (tbl_payments_hdr), by depositdate",
		Example: "  dsr ecom settlements --from 2026-04-01 --to 2026-08-01 --json",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			where := fWhere(
				fDateGE("depositdate", f.From),
				fDateLT("depositdate", f.To),
			)
			q := fmt.Sprintf("SELECT TOP %d %s FROM tbl_payments_hdr%s ORDER BY depositdate DESC",
				topN(app, 100), ecomSettlementsCols, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	return c
}

func ecomCountCmd(app *App) *cobra.Command {
	var f domFilters
	var table string
	c := &cobra.Command{
		Use:     "count",
		Short:   "Count rows in an ecom table (sales|returns|settlements) over a date range",
		Example: "  dsr ecom count --table returns --from 2026-07-01 --to 2026-08-01",
		Args:    cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			var tbl, datecol string
			switch table {
			case "", "sales":
				tbl, datecol = "tbl_ecom_sales", "Invoice_Date"
			case "returns":
				tbl, datecol = "tbl_ecom_returns", "date"
			case "settlements":
				tbl, datecol = "tbl_payments_hdr", "depositdate"
			default:
				return Usagef("--table must be one of sales|returns|settlements, got %q", table)
			}
			where := fWhere(
				fDateGE(datecol, f.From),
				fDateLT(datecol, f.To),
			)
			q := fmt.Sprintf("SELECT COUNT(*) AS rows FROM %s%s", tbl, where)
			return runSelect(app, q)
		},
	}
	addDomFilters(c, &f, "date")
	c.Flags().StringVar(&table, "table", "sales", "which table to count: sales|returns|settlements")
	return c
}
