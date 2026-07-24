package main

import "github.com/spf13/cobra"

func init() { registerSection(newContractsCmd) }

// newContractsCmd — Vendor Contracts, Margins & Incentives. JIVO reads the
// contract grid/summary, drills into one contract (details, activity log,
// state timeline, reviewers), reads item-level margin/incentive listings, and
// pulls the FBZ vendor-PV-margin listings + consolidated data/template files.
// Create/publish/review-submit/upload/edit are WRITES/EXPORTS → out of scope
// (guardrail-blocked). Host: fcc.zepto.co.in.
func newContractsCmd(app *App) *cobra.Command {
	H := hostFCC
	c := &cobra.Command{Use: "contracts", Short: "Vendor contracts, margins & incentives (read-only)"}
	c.AddCommand(
		// --- FBZ vendor PV-margin listings + files ---
		simpleGet(app, "contracts", "pv-margin-download", "FBZ PV-margin upload file download (DOWNLOAD_FBZ_UPLOAD_FILE)", H, "/api/v1/vendor-pv-margin/download"),
		simpleGet(app, "contracts", "pv-margin-status-config", "FBZ PV-margin status config (GET_FBZ_UPLOAD_STATUS)", H, "/api/v1/vendor-pv-margin/status-config"),
		queryGet(app, "contracts", "pv-vendor-filter", "FBZ vendor listing (GET_FBZ_VENDOR_LISTING; --query for filters)", H, "/api/v1/vendor-pv-margin/vendor/filter"),
		simpleGet(app, "contracts", "pv-vendor-download", "FBZ vendor download file (GET_FBZ_VENDOR_DOWNLOAD)", H, "/api/v1/vendor-pv-margin/vendor/download"),
		queryGet(app, "contracts", "pv-vendor-sku-list", "FBZ vendor SKU/PV listing (GET_FBZ_VENDOR_SKU_LISTING; --query)", H, "/api/v1/vendor-pv-margin/vendor/pv-list"),
		simpleGet(app, "contracts", "pv-vendor-sku-download", "FBZ vendor SKU/PV download file (GET_FBZ_VENDOR_SKU_DOWNLOAD)", H, "/api/v1/vendor-pv-margin/vendor/pv-list/download"),

		// --- Contract grid / summary / config ---
		queryGet(app, "contracts", "list", "Filtered contracts list (GET_FILTERED_CONTRACTS; --query for filters)", H, "/contractservice/api/v1/vendor-contract/get-filtered-contracts"),
		simpleGet(app, "contracts", "summary", "Contracts listing summary tiles (GET_CONTRACTS_SUMMARY)", H, "/contractservice/api/v1/vendor-contract/listing-summary"),
		simpleGet(app, "contracts", "pending-approval", "Contracts pending on approver (GET_APPROVAL_CONTRACTS)", H, "/contractservice/api/v1/vendor-contract/pending-on-approver"),
		simpleGet(app, "contracts", "static-config", "Contract static config / roles (GET_STATIC_CONFIG)", H, "/contractservice/api/v1/vendor-contract/static-config"),
		simpleGet(app, "contracts", "users", "Users for role (GET_USERS_FOR_ROLE)", H, "/contractservice/api/v1/vendor-contract/users"),
		queryGet(app, "contracts", "activity-logs", "All contract activity logs (GET_ALL_ACTIVITY_LOGS; --query)", H, "/contractservice/api/v1/vendor-contract/activity-log"),

		// --- One contract drill-down (contract id) ---
		getByID(app, "contracts", "get", "Contract detail by id (getContractDetails)", H, "/contractservice/api/v1/vendor-contract/%s", "contract_id"),
		getByID(app, "contracts", "activity-log", "Activity log for one contract (getActivityLogsByContractId)", H, "/contractservice/api/v1/vendor-contract/%s/activity-log", "contract_id"),
		getByID(app, "contracts", "amendment-reviewers", "Amendment reviewers for a contract (amendmentReviewers)", H, "/contractservice/api/v1/vendor-contract/%s/amendment-reviewers", "contract_id"),
		getByID(app, "contracts", "review", "Contract review view (reviewContract)", H, "/contractservice/api/v1/vendor-contract/%s/review", "contract_id"),
		getByID(app, "contracts", "state-timeline", "Contract state timeline (getContractStates)", H, "/contractservice/api/v1/vendor-contract/%s/state-timeline", "contract_id"),

		// --- Margin & incentive item listings ---
		queryGet(app, "contracts", "margin-details", "Global item margin details listing (LIST_ITEM_MARGIN_DETAILS_GLOBAL; --query)", H, "/contractservice/api/v1/margin-incentive/list-item-margin-details"),
		getByID(app, "contracts", "margin-details-by-contract", "Item margin details for one contract (listItemMarginDetailsForContract)", H, "/contractservice/api/v1/margin-incentive/%s/list-item-margin-details", "contract_id"),

		// --- Consolidated margin/incentive data + template downloads (contract id) ---
		getByID(app, "contracts", "download-margin-data", "Download consolidated contract margins (downloadConsolidatedContractMargins)", H, "/contractservice/api/v1/margin-and-incentive/%s/download-margin-data", "contract_id"),
		getByID(app, "contracts", "download-deq-data", "Download consolidated DeQ details (downloadConsolidatedDeqDetails)", H, "/contractservice/api/v1/margin-and-incentive/%s/download-deq-data", "contract_id"),
		getByID(app, "contracts", "download-on-invoice-data", "Download consolidated on-invoice data (downloadConsolidatedOnInvoiceData)", H, "/contractservice/api/v1/margin-and-incentive/%s/download-on-invoice-data", "contract_id"),
		getByID(app, "contracts", "download-stock-data", "Download consolidated RTV/stock data (downloadConsolidatedRtvData)", H, "/contractservice/api/v1/margin-and-incentive/%s/download-stock-data", "contract_id"),
		getByID(app, "contracts", "download-stock-correction-data", "Download consolidated stock-correction data (downloadConsolidatedStockCorrectionDetails)", H, "/contractservice/api/v1/margin-and-incentive/%s/download-stock-correction-data", "contract_id"),
		getByID(app, "contracts", "template-deq-details", "DeQ details template (downloadDeQDetailsTemplate)", H, "/contractservice/api/v1/margin-and-incentive/%s/deq-details-template", "contract_id"),
		getByID(app, "contracts", "template-margin-details", "Item margin details template (downloadMarginDetailsTemplate)", H, "/contractservice/api/v1/margin-and-incentive/%s/item-margin-details-template", "contract_id"),
		getByID(app, "contracts", "template-stock-details", "Item stock details template (downloadStockDetailsTemplate)", H, "/contractservice/api/v1/margin-and-incentive/%s/item-stock-details-template", "contract_id"),
		getByID(app, "contracts", "template-on-invoice-details", "On-invoice details template (downloadOnInvoiceDetailsTemplate)", H, "/contractservice/api/v1/margin-and-incentive/%s/on-invoice-details-template", "contract_id"),
		getByID(app, "contracts", "template-stock-correction-details", "Stock-correction details template (downloadStockCorrectionDetailsTemplate)", H, "/contractservice/api/v1/margin-and-incentive/%s/stock-correction-details-template", "contract_id"),
	)
	return c
}
