package main

import (
	"encoding/json"
	"fmt"
	"net/url"

	"github.com/spf13/cobra"
)

func newPaymentsCmd(app *App) *cobra.Command {
	pay := &cobra.Command{
		Use:   "payments",
		Short: "Invoice payments, UTR settlements, fees & charges",
	}
	pay.AddCommand(
		newPaymentsInvoicesCmd(app),
		newPaymentsInvoiceDetailsCmd(app),
		newPaymentsGRNCmd(app),
		newPaymentsUTRCmd(app),
		newPaymentsAggregateCmd(app),
		newPaymentsChargesCmd(app),
		newPaymentsChargeCmd(app),
		newPOFacetCmd(app, "charges-summary", "Fees & charges summary tiles", "/v1/charges-summary/"),
		newPOFacetCmd(app, "charges-stats", "Fees & charges stat totals", "/v1/charges-stats/"),
		newPOFacetCmd(app, "charges-filters", "Charges filter options", "/v1/charges/filters/"),
		newPaymentsAdviceCmd(app),
		newPaymentsInvoiceDownloadCmd(app),
	)
	return pay
}

// jsonBody merges the given pairs into a filters body, or returns the raw
// override if set.
func filtersBody(raw string, filters map[string]any) []byte {
	if raw != "" {
		return []byte(raw)
	}
	b, _ := json.Marshal(map[string]any{"filters": filters})
	return b
}

func newPaymentsInvoicesCmd(app *App) *cobra.Command {
	var status, from, to, body string
	c := &cobra.Command{
		Use:   "invoices",
		Short: "Invoice/payment list (tabs: paid|upcoming|all|last_1_month)",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if status != "" {
				f["status"] = status
			}
			if from != "" {
				f["from"] = from
			}
			if to != "" {
				f["to"] = to
			}
			return app.postJSON("payments invoices", "/v2/invoice/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&status, "status", "", "paid|upcoming|all|last_1_month")
	c.Flags().StringVar(&from, "from", "", "start date YYYY-MM-DD")
	c.Flags().StringVar(&to, "to", "", "end date YYYY-MM-DD")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body (overrides filters)")
	return c
}

func newPaymentsInvoiceDetailsCmd(app *App) *cobra.Command {
	var invoiceID, orderNumber, body string
	c := &cobra.Command{
		Use:   "invoice-details",
		Short: "Payment breakdown for an invoice (amounts/deductions/net_payable)",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if invoiceID != "" {
				f["invoice_id"] = invoiceID
			}
			if orderNumber != "" {
				f["order_number"] = orderNumber
			}
			return app.postJSON("payments invoice-details", "/v1/invoice/details/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&invoiceID, "invoice-id", "", "invoice id")
	c.Flags().StringVar(&orderNumber, "order-number", "", "order number")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newPaymentsGRNCmd(app *App) *cobra.Command {
	var invoiceID, body string
	c := &cobra.Command{
		Use:   "grn",
		Short: "GRN line items behind an invoice",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if invoiceID != "" {
				f["invoice_id"] = invoiceID
			}
			return app.postJSON("payments grn", "/v1/invoice/grn-details/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&invoiceID, "invoice-id", "", "invoice id")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newPaymentsUTRCmd(app *App) *cobra.Command {
	var invoiceID, body string
	c := &cobra.Command{
		Use:   "utr",
		Short: "UTR / bank settlement reference per invoice",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if invoiceID != "" {
				f["invoice_id"] = invoiceID
			}
			return app.postJSON("payments utr", "/v1/utr/invoices/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&invoiceID, "invoice-id", "", "invoice id")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newPaymentsAggregateCmd(app *App) *cobra.Command {
	var from, to, body string
	c := &cobra.Command{
		Use:   "aggregate",
		Short: "Aggregated invoice/payment totals (headline payout)",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if from != "" {
				f["from"] = from
			}
			if to != "" {
				f["to"] = to
			}
			return app.postJSON("payments aggregate", "/v1/aggregated-invoice-data/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&from, "from", "", "start date YYYY-MM-DD")
	c.Flags().StringVar(&to, "to", "", "end date YYYY-MM-DD")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newPaymentsChargesCmd(app *App) *cobra.Command {
	var gran, from, to, status, body string
	c := &cobra.Command{
		Use:   "charges",
		Short: "Fees & charges list",
		RunE: func(cmd *cobra.Command, args []string) error {
			f := map[string]any{}
			if gran != "" {
				f["granularity"] = gran
			}
			if from != "" {
				f["from"] = from
			}
			if to != "" {
				f["to"] = to
			}
			if status != "" {
				f["status"] = status
			}
			return app.postJSON("payments charges", "/v1/charges/", filtersBody(body, f))
		},
	}
	c.Flags().StringVar(&gran, "gran", "", "monthly|weekly|daily")
	c.Flags().StringVar(&from, "from", "", "start date YYYY-MM-DD")
	c.Flags().StringVar(&to, "to", "", "end date YYYY-MM-DD")
	c.Flags().StringVar(&status, "status", "", "disputed|waived|pending")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}

func newPaymentsChargeCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "charge <id>",
		Short: "Single charge detail",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.getJSON("payments charge", "/v1/charges/"+url.PathEscape(args[0]))
		},
	}
}

func newPaymentsAdviceCmd(app *App) *cobra.Command {
	var from, to, out string
	c := &cobra.Command{
		Use:   "advice",
		Short: "Payment-advice remittance ZIP",
		RunE: func(cmd *cobra.Command, args []string) error {
			if out == "" {
				out = "blinkit-payment-advice.zip"
			}
			path := fmt.Sprintf("/v1/vendor-reports/?start_date=%s&end_date=%s&download=zip",
				url.QueryEscape(from), url.QueryEscape(to))
			return runFileDownload(app, "payments advice", "GET", path, nil, out)
		},
	}
	c.Flags().StringVar(&from, "from", "", "start date YYYY-MM-DD")
	c.Flags().StringVar(&to, "to", "", "end date YYYY-MM-DD")
	c.Flags().StringVar(&out, "out", "", "output zip path")
	return c
}

func newPaymentsInvoiceDownloadCmd(app *App) *cobra.Command {
	var invoiceID, out, body string
	c := &cobra.Command{
		Use:   "invoice-download",
		Short: "Download a single invoice PDF (POST-to-read, no state change)",
		RunE: func(cmd *cobra.Command, args []string) error {
			if out == "" {
				out = "blinkit-invoice.pdf"
			}
			var b []byte
			if body != "" {
				b = []byte(body)
			} else {
				b, _ = json.Marshal(map[string]any{"invoice_id": invoiceID})
			}
			return runFileDownload(app, "payments invoice-download", "POST", "/v1/invoice/download/", b, out)
		},
	}
	c.Flags().StringVar(&invoiceID, "invoice-id", "", "invoice id")
	c.Flags().StringVar(&out, "out", "", "output PDF path")
	c.Flags().StringVar(&body, "body", "", "raw JSON request body")
	return c
}
