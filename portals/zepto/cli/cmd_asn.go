package main

import "github.com/spf13/cobra"

func init() { registerSection(newASNCmd) }

// newASNCmd — ASN (Advance Shipping Notices). JIVO tells Zepto what's inbound;
// this CLI reads the ASN grid/summary, drills into one ASN (items, attachments,
// linked GRN, settlement DN/CN info, CSV templates), and reads the facility /
// vendor filter lists. Create/upload/submit/cancel are WRITES/EXPORTS → out of
// scope (guardrail-blocked). Source: ../vault/vendor/*.md.
func newASNCmd(app *App) *cobra.Command {
	H := hostFCC
	asn := &cobra.Command{Use: "asn", Short: "Advance shipping notices (JIVO → Zepto inbound)"}
	asn.AddCommand(
		queryGet(app, "asn", "list", "ASN list grid (GET_ASN_LISTING; --query for filters)", H, "/api/v1/asn/filter"),
		queryGet(app, "asn", "summary-list", "ASN summary list (GET_ASN_SUMMARY_LIST)", H, "/api/v1/asn/list"),
		simpleGet(app, "asn", "facilities", "Facility / mother-hub filter list", H, "/api/v1/asn/user/mh-list"),
		simpleGet(app, "asn", "vendors", "Vendor filter list", H, "/api/v1/asn/user/vendor-list"),
		getByID(app, "asn", "get", "ASN detail by id", H, "/api/v1/asn/%s", "asn_id"),
		getByID(app, "asn", "items", "ASN line items", H, "/api/v1/asn/%s/items", "asn_id"),
		getByID(app, "asn", "attachments", "ASN document links", H, "/api/v1/asn/%s/attachments", "asn_id"),
		getByID(app, "asn", "grn-info", "GRN linked to an ASN", H, "/api/v1/asn/%s/grn-info", "asn_id"),
		getByID(app, "asn", "settlement-info", "Settlement DN/CN details", H, "/api/v1/asn/%s/settlement-info", "asn_id"),
		getByID(app, "asn", "csv-details", "Create-ASN CSV template details", H, "/api/v1/asn/%s/csv-details", "asn_id"),
		getByID(app, "asn", "failure-csv-details", "MRP cost-sheet failure CSV template", H, "/api/v1/asn/%s/failure-csv-details", "asn_id"),
		// Internal (grpc-vendor) listing — read-only grid
		queryGet(app, "asn", "internal-listing", "Internal ASN listing grid (INTERNAL_GET_ASN_LISTING)", H, "/vendor/api/v1/asn/listing"),
	)
	return asn
}
