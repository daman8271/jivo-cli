package main

import "github.com/spf13/cobra"

func init() { registerSection(newFBZCmd) }

// newFBZCmd — FBZ (Fulfilled-by-Zepto) fulfillment: vendor rebate portal,
// vendor debit-note (DN/CN) review, and packaging bag-barcode reads. JIVO reads
// the rebate grid/margins/reports (+ CSV/template downloads), the DN review
// listing/detail-file downloads/status-config, and bag-barcode config/list.
// Approve/reject/update/upload/batch and CSV-upload flows are WRITES/EXPORTS →
// out of scope (guardrail-blocked). Source: ../vault/vendor/FBZ-Fulfillment.md.
func newFBZCmd(app *App) *cobra.Command {
	H := hostFCC
	fbz := &cobra.Command{Use: "fbz", Short: "FBZ fulfillment: rebate, vendor debit-notes, bag-barcode"}
	fbz.AddCommand(
		// Rebate portal
		queryGet(app, "fbz", "rebate-list", "Rebate portal grid (GET_ALL_FBZ_REBATE; --query for filters)", H, "/api/v1/fbz/rebate/view-rebate-portal"),
		simpleGet(app, "fbz", "rebate-vendor-codes", "Rebate vendor-code filter list", H, "/api/v1/fbz/rebate/fetch-all-vendor-codes"),
		simpleGet(app, "fbz", "rebate-margin-details", "Rebate margin details", H, "/api/v1/fbz/rebate/fetch-rebate-margin-details"),
		simpleGet(app, "fbz", "rebate-reports", "Rebate reports (DOWNLOAD_REPORT)", H, "/api/v1/fbz/rebate/fetch-reports"),
		simpleGet(app, "fbz", "rebate-template", "Rebate CSV template download", H, "/api/v1/fbz/rebate/template-download"),
		getByID(app, "fbz", "rebate-csv", "Rebate CSV download by id", H, "/api/v1/fbz/rebate/%s/download-rebate-csv", "rebate_id"),
		// Vendor debit-note (DN/CN) review
		queryGet(app, "fbz", "dn-list", "DN/CN review listing (GET_DN_CN_REVIEW_LISTING; --query for filters)", H, "/api/v1/fbz/vendor-debit-note/filter"),
		simpleGet(app, "fbz", "dn-status-config", "DN/CN review status config", H, "/api/v1/fbz/vendor-debit-note/status-config"),
		getByID(app, "fbz", "dn-copy-download", "DN copy file download by id", H, "/api/v1/fbz/vendor-debit-note/%s/dn-copy/download", "dn_id"),
		getByID(app, "fbz", "dn-working-copy-download", "DN working-copy file download by id", H, "/api/v1/fbz/vendor-debit-note/%s/working-dn-copy/download", "dn_id"),
		// Packaging bag-barcode
		simpleGet(app, "fbz", "bag-barcode-config", "Bag-barcode config", H, "/api/v1/packaging/bag-barcode/config"),
		queryGet(app, "fbz", "bag-barcode-list", "Bag-barcode list (--query for filters)", H, "/api/v1/packaging/bag-barcode/list"),
		simpleGet(app, "fbz", "bag-barcode-download", "Bag-barcode file download", H, "/api/v1/packaging/bag-barcode/download"),
	)
	return fbz
}
