package main

import "github.com/spf13/cobra"

func init() { registerSection(newInvoicingCmd) }

// newInvoicingCmd — Invoicing (self-invoice / non-trade + off-invoice rules).
// Reads the self-invoice list/summary, drills into one invoice
// (details/documents), reads off-invoice rule config/tracking/templates, plus
// lookup helpers (entity names, GSTIN state). Create/submit/cancel/draft/upload
// and file-remove are WRITES → out of scope (guardrail-blocked).
// Source: ../vault/vendor/Invoicing.md.
func newInvoicingCmd(app *App) *cobra.Command {
	H := hostFCC
	inv := &cobra.Command{Use: "invoicing", Short: "Self-invoice + off-invoice rule reads (vendor)"}
	inv.AddCommand(
		// Self-invoice (non-trade)
		queryGet(app, "invoicing", "list", "Self-invoice list (GET_INVOICE_LIST; --query for filters)", H, "/invoice/api/v1/self-invoice/non-trade/list"),
		simpleGet(app, "invoicing", "summary", "Self-invoice summary tiles (GET_INVOICE_SUMMARY)", H, "/invoice/api/v1/self-invoice/non-trade/summary"),
		getByID(app, "invoicing", "detail", "Self-invoice detail by id", H, "/invoice/api/v1/self-invoice/non-trade/%s/details", "invoice_id"),
		getByID(app, "invoicing", "documents", "Self-invoice document S3 links by id", H, "/invoice/api/v1/self-invoice/non-trade/%s/documents", "invoice_id"),
		simpleGet(app, "invoicing", "entity-names", "Entity-name lookup list", H, "/invoice/api/v1/self-invoice/non-trade/entity-names"),
		simpleGet(app, "invoicing", "gstin-state", "GSTIN → state lookup", H, "/invoice/api/v1/self-invoice/non-trade/gstin-state"),
		// Off-invoice rules
		simpleGet(app, "invoicing", "off-invoice-config", "Off-invoice rule config (GET_OFF_INVOICE_CONFIG)", H, "/contractservice/api/v1/off-invoice/off-invoice-rules/get-config"),
		simpleGet(app, "invoicing", "off-invoice-template", "Off-invoice rules download template", H, "/contractservice/api/v1/off-invoice/off-invoice-rules/template"),
		getByID(app, "invoicing", "off-invoice-tracking", "Off-invoice rule tracking by id", H, "/contractservice/api/v1/off-invoice/off-invoice-rules/%s/tracking", "rule_id"),
		getByID(app, "invoicing", "off-invoice-details-template", "Off-invoice details template by contract", H, "/contractservice/api/v1/margin-and-incentive/%s/off-invoice-details-template", "contract_id"),
	)
	return inv
}
