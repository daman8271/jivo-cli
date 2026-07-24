package main

import "github.com/spf13/cobra"

func init() { registerSection(newPOCmd) }

// newPOCmd — Purchase Orders + GRN. Zepto raises POs to JIVO; JIVO reads the PO
// grid/summary, drills into one PO (items/checklist/attachments/logs/linked
// ASN+GRN), and reads the downstream GRN (what the hub received).
// Scheduling/cancel/acknowledge are WRITES → out of scope (guardrail-blocked).
// Source: ../vault/vendor/Purchase-Orders.md.
func newPOCmd(app *App) *cobra.Command {
	H := hostFCC
	po := &cobra.Command{Use: "po", Short: "Purchase orders + GRN (Zepto → JIVO inbound)"}
	po.AddCommand(
		queryGet(app, "po", "list", "PO list grid (GET_PO_LISTING; --query for filters)", H, "/api/v1/po/filter"),
		simpleGet(app, "po", "summary", "PO summary tiles (GET_PO_SUMMARY)", H, "/api/v1/po/listing-stat"),
		simpleGet(app, "po", "scheduled", "Scheduled-PO summary", H, "/api/v1/po/scheduled"),
		simpleGet(app, "po", "ib-capacity", "Inbound-capacity slots", H, "/api/v1/po/ib-capacity"),
		simpleGet(app, "po", "facilities", "Facility / mother-hub filter list", H, "/api/v1/po/user/mh-list"),
		simpleGet(app, "po", "vendors", "Vendor filter list", H, "/api/v1/po/user/vendor-list"),
		getByID(app, "po", "get", "PO detail by id", H, "/api/v1/po/%s", "po_id"),
		getByID(app, "po", "items", "PO line items", H, "/api/v1/po/%s/items", "po_id"),
		getByID(app, "po", "checklist", "PO pre-dispatch checklist", H, "/api/v1/po/%s/checklist", "po_id"),
		getByID(app, "po", "attachments", "PO document links", H, "/api/v1/po/%s/attachments", "po_id"),
		getByID(app, "po", "logs", "PO activity / state-change log", H, "/api/v1/po/%s/logs", "po_id"),
		getByID(app, "po", "asn", "ASN linked to a PO", H, "/api/v1/po/%s/asn", "po_id"),
		getByID(app, "po", "grn", "GRN linked to a PO", H, "/api/v1/po/%s/grn", "po_id"),
		// GRN (goods receipt) reads
		queryGet(app, "po", "grn-list", "GRN list grid (GET_GRN_LISTING)", H, "/api/v1/grn/filter"),
		simpleGet(app, "po", "grn-facilities", "GRN facility filter list", H, "/api/v1/grn/user/mh-list"),
		simpleGet(app, "po", "grn-vendors", "GRN vendor filter list", H, "/api/v1/grn/user/vendor-list"),
		getByID(app, "po", "grn-get", "GRN detail by id", H, "/api/v1/grn/%s", "grn_id"),
		getByID(app, "po", "grn-items", "GRN line items", H, "/api/v1/grn/%s/items", "grn_id"),
		getByID(app, "po", "grn-asn", "ASN behind a GRN", H, "/api/v1/grn/%s/asn-info", "grn_id"),
	)
	return po
}
