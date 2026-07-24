package main

import "github.com/spf13/cobra"

func init() { registerSection(newKYCCmd) }

// newKYCCmd — KYC & Vendor Onboarding (VMS). Read-only surface over the vendor
// master / onboarding lifecycle: KYC + bank + contract + warehouse details,
// onboarding/lead filters & summaries, marketer + non-trade-vendor profiles,
// file/attachment reads, and the brand-analytics KYC dashboard metrics.
// All save/approve/reject/hold/invite/upload/update are WRITES/EXPORTS → out of
// scope (guardrail-blocked). Source: sections.json slug "kyc-onboarding".
func newKYCCmd(app *App) *cobra.Command {
	H := hostFCC
	kyc := &cobra.Command{Use: "kyc", Short: "KYC & vendor onboarding (VMS): profiles, contracts, bank/warehouse, onboarding status"}
	kyc.AddCommand(
		// brand-analytics KYC dashboard metrics (GET/READ)
		simpleGet(app, "kyc", "revenue-per-user", "Avg revenue per user (KYC_GET_REVENUE_PER_USER)", H, "/brand-analytics-web/api/v1/kyc/average-revenue-per-user"),
		simpleGet(app, "kyc", "brand-recall", "Brand recall metric (KYC_GET_BRANDS_RECALL)", H, "/brand-analytics-web/api/v1/kyc/brand-recall"),
		simpleGet(app, "kyc", "customer-penetration", "Customer penetration (KYC_GET_CUSTOMER_PENETRATION)", H, "/brand-analytics-web/api/v1/kyc/customer-penetration"),
		simpleGet(app, "kyc", "customer-retention", "Customer retention (KYC_GET_CUSTOMER_RETENTION)", H, "/brand-analytics-web/api/v1/kyc/customer-retention"),
		simpleGet(app, "kyc", "product-view-to-action", "Product view→action (KYC_GET_PRODUCT_VIEW_TO_ACTION)", H, "/brand-analytics-web/api/v1/kyc/product-view-to-action"),
		simpleGet(app, "kyc", "top-searched-keywords", "Top searched keywords (KYC_GET_TOP_SEARCHED_KEYWORDS)", H, "/brand-analytics-web/api/v1/kyc/top-searched-keywords"),

		// VMS attachments / files
		simpleGet(app, "kyc", "attachment", "Attachment content (GET_ATTACHMENT_CONTENT)", H, "/vms/api/v1/admin/attachment"),
		simpleGet(app, "kyc", "attachment-download", "Attachment pre-signed download URL (DOWNLOAD_ATTACHMENT)", H, "/vms/api/v1/admin/attachment/pre-signed-url"),
		getByID(app, "kyc", "file-get", "File by id (getFile)", H, "/vms/api/v1/files/%s", "file_id"),
		simpleGet(app, "kyc", "file-error", "Error file (GET_ERROR_FILE)", H, "/vms/api/v1/files/error"),
		queryGet(app, "kyc", "files-filter", "Files list grid (GET_FILES_LIST; --query for filters)", H, "/vms/api/v1/files/filter"),
		simpleGet(app, "kyc", "file-template", "Template file (GET_TEMPLATE_FILE)", H, "/vms/api/v1/files/template"),
		simpleGet(app, "kyc", "file-template-v2", "Template file v2 (GET_TEMPLATE_FILE_V2)", H, "/vms/api/v2/files/template"),

		// KYC / GSTIN
		simpleGet(app, "kyc", "kyc-fetch", "KYC details (GET_KYC_DETAILS)", H, "/vms/api/v1/admin/kyc/fetch"),
		simpleGet(app, "kyc", "gstin-details", "GSTIN details (GET_GSTIN_DETAILS)", H, "/vms/api/v1/kyc/gstin-details"),
		simpleGet(app, "kyc", "gstin-details-bff", "GSTIN details (bff path variant)", H, "/api/v1/kyc/gstin-details"), // TODO host-to-confirm

		// bank / contract / warehouse details (trade vendor)
		simpleGet(app, "kyc", "bank-details", "Bank details (GET_BANK_DETAILS)", H, "/vms/api/v1/admin/bank-details/fetch"),
		simpleGet(app, "kyc", "contract-details", "Contract/VRF details (GET_VRF_DETAILS)", H, "/vms/api/v1/admin/basic-details/contract-details"),
		simpleGet(app, "kyc", "fetch-contracts", "Contract details (GET_CONTRACT_DETAILS)", H, "/vms/api/v1/admin/basic-details/fetch-contracts"),
		simpleGet(app, "kyc", "warehouse-details", "Warehouse/vendor details (GET_VENDOR_DETAILS)", H, "/vms/api/v1/admin/warehouse-details/fetch"),

		// onboarding filters & summaries (trade vendor)
		queryGet(app, "kyc", "onboarding-filter", "Onboarding filtered list (GET_FILTERED_LIST; --query for filters)", H, "/vms/api/v1/admin/basic-details/onboarding-filter"),
		simpleGet(app, "kyc", "onboarding-summary", "Onboarding summary (GET_SUMMARY)", H, "/vms/api/v1/admin/basic-details/onboarding-summary"),

		// common config / lookups
		simpleGet(app, "kyc", "categories", "Category list (GET_CATGORIES)", H, "/vms/api/v1/admin/common/category"),
		simpleGet(app, "kyc", "lead-status-config", "Lead-status config (LEADS_STATUS_CONFIG)", H, "/vms/api/v1/admin/common/lead-status-config"),
		simpleGet(app, "kyc", "mappings", "Common mappings (GET_MAPPINGS)", H, "/vms/api/v1/admin/common/mappings"),
		simpleGet(app, "kyc", "onboarding-status-config", "Onboarding-status config (ONBOARDING_STATUS_CONFIG)", H, "/vms/api/v1/admin/common/onboarding-status-config"),
		simpleGet(app, "kyc", "vendor-attachments", "Vendor attachments (GET_VENDOR_ATTACHMENTS)", H, "/vms/api/v1/admin/common/vendor-attachments"),
		simpleGet(app, "kyc", "config", "Admin config (GET_CONFIG)", H, "/vms/api/v1/admin/config"),
		queryGet(app, "kyc", "distributor-filter", "Distributor list (GET_DISTRIBUTOR_LIST; --query for filters)", H, "/vms/api/v1/admin/distributor/filter"),

		// leads
		queryGet(app, "kyc", "lead-filter", "All leads grid (GET_ALL_LEADS; --query for filters)", H, "/vms/api/v1/admin/lead/filter"),
		simpleGet(app, "kyc", "lead-user-details", "Lead user details (GET_USER_DETAILS)", H, "/vms/api/v1/admin/lead/get-user-details"),
		simpleGet(app, "kyc", "lead-summary", "Lead summary (GET_SUMMARY)", H, "/vms/api/v1/admin/lead/summary"),
		simpleGet(app, "kyc", "user-lead", "Lead details for user (GET_LEAD_DETAILS)", H, "/vms/api/v1/admin/user/lead"),

		// marketer
		getByID(app, "kyc", "marketer-get", "Marketer details by id (getMarketerDetailsById)", H, "/vms/api/v1/admin/marketer/%s", "marketer_id"),
		queryGet(app, "kyc", "marketer-filter", "Marketer list (GET_MARKETER_LIST; --query for filters)", H, "/vms/api/v1/admin/marketer/filter"),
		queryGet(app, "kyc", "marketer-search", "Marketer search (SEARCH_MARKETER; --query for params)", H, "/vms/api/v1/admin/marketer/search"),

		// non-trade vendor (NTV)
		simpleGet(app, "kyc", "ntv-bank-details", "NTV bank details (GET_BANK_DETAILS)", H, "/vms/api/v1/admin/non-trade-vendor/bank-details/fetch"),
		simpleGet(app, "kyc", "ntv-contract-details", "NTV contract/VRF details (GET_VRF_DETAILS)", H, "/vms/api/v1/admin/non-trade-vendor/contract-details"),
		simpleGet(app, "kyc", "ntv-fetch-contracts", "NTV contract details (GET_CONTRACT_DETAILS)", H, "/vms/api/v1/admin/non-trade-vendor/fetch-contracts"),
		queryGet(app, "kyc", "ntv-onboarding-filter", "NTV onboarding filtered list (GET_FILTERED_LIST; --query)", H, "/vms/api/v1/admin/non-trade-vendor/onboarding-filter"),
		simpleGet(app, "kyc", "ntv-onboarding-status-config", "NTV onboarding-status config (ONBOARDING_STATUS_CONFIG)", H, "/vms/api/v1/admin/non-trade-vendor/onboarding-status-config"),
		simpleGet(app, "kyc", "ntv-onboarding-summary", "NTV onboarding summary (GET_SUMMARY)", H, "/vms/api/v1/admin/non-trade-vendor/onboarding-summary"),
		simpleGet(app, "kyc", "ntv-vendor-attachments", "NTV vendor attachments (GET_VENDOR_ATTACHMENTS)", H, "/vms/api/v1/admin/non-trade-vendor/vendor-attachments"),
		simpleGet(app, "kyc", "ntv-warehouse-details", "NTV warehouse/vendor details (GET_VENDOR_DETAILS)", H, "/vms/api/v1/admin/non-trade-vendor/warehouse-details/fetch"),
		simpleGet(app, "kyc", "ntv-approval-data", "NTV approval onboarding data (GET_APPROVAL_DATA)", H, "/vms/api/v1/admin/user/non-trade-vendor/approval-onboarding-data"),
		simpleGet(app, "kyc", "ntv-profile", "NTV vendor profile (GET_VENDOR_PROFILE)", H, "/vms/api/v1/admin/user/non-trade-vendor/profile"),
		simpleGet(app, "kyc", "ntv-review", "NTV unified review (UNIFIED_REVIEW)", H, "/vms/api/v1/admin/user/non-trade-vendor/review"),

		// vendor master (v2)
		queryGet(app, "kyc", "vendor-filter", "Vendor list grid v2 (--query for filters)", H, "/vms/api/v2/vendor/filter"),
	)
	return kyc
}
