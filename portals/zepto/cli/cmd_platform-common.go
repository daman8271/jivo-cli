package main

import "github.com/spf13/cobra"

func init() { registerSection(newPlatformCmd) }

// newPlatformCmd — Platform-Common: shared layout/config, commons lookups, files,
// contract-service common data, and vendor/support plumbing that every module
// leans on. Read-only: config/metadata reads, filter/search lookups, and
// pre-signed / download-template file reads. All write endpoints (feedback,
// impersonation, publish-events, ticket create, bulk-job create, uploads,
// user updates) are out of scope and guardrail-blocked.
// Hosts: auth-backend.zepto.co.in (hostAuth) + fcc.zepto.co.in (hostFCC).
func newPlatformCmd(app *App) *cobra.Command {
	A := hostAuth
	H := hostFCC
	p := &cobra.Command{Use: "platform", Short: "Platform-common: layout/config, commons lookups, files, contracts, support"}
	p.AddCommand(
		// --- auth-backend commons ---
		simpleGet(app, "platform", "chat-token", "Sendbird chat user token", A, "/api/v1/chat/sendbird/user/token"),
		queryGet(app, "platform", "brand-category-map", "Brand → category mapping (--query for filters)", A, "/api/v1/commons/brand-category-mapping"),
		queryGet(app, "platform", "brand-l3-category-map", "Brand → L3-category mapping (--query for filters)", A, "/api/v1/commons/brand-l3-category-mapping"),
		queryGet(app, "platform", "presigned-url", "Commons pre-signed download URL (--query for key)", A, "/api/v1/commons/config/get-pre-signed-url"),
		simpleGet(app, "platform", "learning-center", "All learning-center content", A, "/api/v1/commons/config/learning-center/all"),
		queryGet(app, "platform", "learning-center-by-submodule", "Learning content by sub-module (--query)", A, "/api/v1/commons/config/learning-center/get-by-subModule"),
		queryGet(app, "platform", "manufacturer-list", "Manufacturer lookup list (--query)", A, "/api/v1/commons/manufacturer-list"),
		simpleGet(app, "platform", "mh-list", "Mother-hub list", A, "/api/v1/commons/mh-list"),
		queryGet(app, "platform", "search-customers-vendors", "Search customers + vendors (--query)", A, "/api/v1/commons/search-customers-and-vendors"),
		postRead(app, "platform", "search-customers-vendors-post", "Search customers + vendors (POST body)", A, "/api/v1/commons/search-customers-and-vendors", ""),
		queryGet(app, "platform", "search-vendors", "Search vendors (--query)", A, "/api/v1/commons/search-vendors"),
		postRead(app, "platform", "search-vendors-post", "Search vendors (POST body)", A, "/api/v1/commons/search-vendors", ""),
		queryGet(app, "platform", "search-vendors-v2", "Search vendors v2 (--query)", A, "/api/v1/commons/search-vendors-v2"),
		postRead(app, "platform", "search-vendors-v2-post", "Search vendors v2 (POST body)", A, "/api/v1/commons/search-vendors-v2", ""),
		simpleGet(app, "platform", "status-config", "Status configuration map", A, "/api/v1/commons/status-config"),
		simpleGet(app, "platform", "user-mh-list", "User's mother-hub filter list", A, "/api/v1/commons/user/mh-list"),
		simpleGet(app, "platform", "user-vendor-list", "User's vendor filter list", A, "/api/v1/commons/user/vendor-list"),

		// --- ads-bff layout config ---
		simpleGet(app, "platform", "ads-campaign-modal-image-map", "Create-campaign modal subtype image map", H, "/ads-bff/api/v1/layout/config/create_campaign_modal_subtype_image_map"),
		simpleGet(app, "platform", "ads-jarvis-ui-config", "Jarvis-AI UI config", H, "/ads-bff/api/v1/layout/config/jarvis_ai_ui_config"),
		simpleGet(app, "platform", "ads-kam-ui-config", "KAM-AI UI config", H, "/ads-bff/api/v1/layout/config/kam_ai_ui_config"),
		simpleGet(app, "platform", "ads-payment-status-config", "Payment-confirmation modal status config", H, "/ads-bff/api/v1/layout/config/payment_confirmation_modal_status_config"),
		simpleGet(app, "platform", "ads-pricing-metadata", "Pricing-page metadata", H, "/ads-bff/api/v1/layout/config/pricing_page_metadata"),
		simpleGet(app, "platform", "ads-approvals-table-meta", "User-approvals table metadata", H, "/ads-bff/api/v2/layout/table/user_approvals_table_meta"),
		queryGet(app, "platform", "ads-users", "Ads-BFF user table data (--query)", H, "/ads-bff/api/v2/users"),

		// --- fcc /api/v1 commons + config + files ---
		queryGet(app, "platform", "brand-metrics-summary", "Admin brands metrics summary (--query)", H, "/api/v1/admin/brands/metrics/summary"),
		queryGet(app, "platform", "search-ntv", "Search NTV entities (--query)", H, "/api/v1/commons/search-ntv"),
		simpleGet(app, "platform", "config", "Root config blob", H, "/api/v1/config"),
		simpleGet(app, "platform", "config-data", "Config data", H, "/api/v1/config/get-configdata"),
		queryGet(app, "platform", "file-download", "File-job download-file (--query for key)", H, "/api/v1/file-job/download-file"),
		simpleGet(app, "platform", "city-list", "City filter list", H, "/api/v1/filter/city-list"),

		// --- fcc /api/v1/layout/config/* (templated + fixed) ---
		getByID(app, "platform", "layout-config", "Layout config by key", H, "/api/v1/layout/config/%s", "config_key"),
		simpleGet(app, "platform", "layout-adcreative-placement-map", "Ad-creative section config × placement-type map", H, "/api/v1/layout/config/AdCreativeSectionConfigXPlacementTypeMap"),
		simpleGet(app, "platform", "layout-new-creative-form", "New creative form details", H, "/api/v1/layout/config/NewCreativeFormDetails"),
		simpleGet(app, "platform", "layout-ads-banner-config", "Ads banner config", H, "/api/v1/layout/config/ads-banner-config"),
		simpleGet(app, "platform", "layout-ads-feature-metadata", "Ads feature metadata", H, "/api/v1/layout/config/ads-feature-metadata"),
		simpleGet(app, "platform", "layout-ads-brand-analytics-config", "Ads brand-analytics config", H, "/api/v1/layout/config/ads_brand_analytics_config"),
		simpleGet(app, "platform", "layout-campaign-forecast-review", "Campaign forecast review config", H, "/api/v1/layout/config/campaign_forecast_review_config"),
		simpleGet(app, "platform", "layout-campaign-review-detail-form", "Campaign review detail form", H, "/api/v1/layout/config/campain-review-detail-from"),
		simpleGet(app, "platform", "layout-category-popup-config", "Category popup config", H, "/api/v1/layout/config/category-popup-config"),
		simpleGet(app, "platform", "layout-dcm-trackers-config", "DCM trackers FE config", H, "/api/v1/layout/config/dcm_trackers_fe_config"),
		simpleGet(app, "platform", "layout-gamification-freq-caps", "Gamification frequency caps", H, "/api/v1/layout/config/gamification_frequency_caps"),
		simpleGet(app, "platform", "layout-hyperlocal-defaults", "Hyperlocal default values", H, "/api/v1/layout/config/hyperlocal_default_values"),
		simpleGet(app, "platform", "layout-keywords-config", "Keywords layout config", H, "/api/v1/layout/config/keywords-layout-config"),
		simpleGet(app, "platform", "layout-nonendemic-creative-form", "Non-endemic creative form details", H, "/api/v1/layout/config/nonEndemicCreativeFormDetails"),
		simpleGet(app, "platform", "layout-pagewise-placements", "Page-wise placements", H, "/api/v1/layout/config/pagewise-placements"),
		simpleGet(app, "platform", "layout-quick-edit-form-meta", "Quick-edit form metadata", H, "/api/v1/layout/config/quick_edit_form_metadata"),
		simpleGet(app, "platform", "layout-quick-edit-nudge-meta", "Quick-edit nudge metadata", H, "/api/v1/layout/config/quick_edit_nudge_metadata"),
		simpleGet(app, "platform", "layout-review-checklist", "Review checklist config", H, "/api/v1/layout/config/review-checklist"),
		simpleGet(app, "platform", "layout-reward-template-path", "Reward-creation template download path", H, "/api/v1/layout/config/reward_creation_template_download_path"),
		simpleGet(app, "platform", "layout-smart-nudge-meta", "Smart-nudge metadata", H, "/api/v1/layout/config/smart_nudge_metadata"),
		simpleGet(app, "platform", "layout-smart-nudge-subheaders", "Smart-nudge sub-headers", H, "/api/v1/layout/config/smart_nudge_sub_headers"),
		simpleGet(app, "platform", "layout-summary-metrics-meta", "Summary metrics metadata", H, "/api/v1/layout/config/summaryMetricsMeta"),
		simpleGet(app, "platform", "layout-swap-strategy-meta", "Swap-strategy metadata", H, "/api/v1/layout/config/swap_strategy_metadata"),
		simpleGet(app, "platform", "layout-version-enforcer", "Version-enforcer config", H, "/api/v1/layout/config/version-enforcer"),
		simpleGet(app, "platform", "layout-campaign-review-table-meta", "Campaign-review table metadata", H, "/api/v1/layout/table/campaign-review-table-meta"),
		queryGet(app, "platform", "log-details", "Log details (--query)", H, "/api/v1/log-details"),

		// --- brand-analytics-web ---
		simpleGet(app, "platform", "ba-enhancement-config", "Brand-analytics enhancement config", H, "/brand-analytics-web/api/v1/common/enhancement-config"),
		queryGet(app, "platform", "recon-inventory-city-listing", "Inventory reconciliation — city-level listing (--query)", H, "/brand-analytics-web/api/v1/reconciliation/inventory/city-level-listing"),
		queryGet(app, "platform", "recon-inventory-summary", "Inventory reconciliation — summary (--query)", H, "/brand-analytics-web/api/v1/reconciliation/inventory/summary"),
		queryGet(app, "platform", "recon-inventory-vendor-listing", "Inventory reconciliation — vendor-level listing (--query)", H, "/brand-analytics-web/api/v1/reconciliation/inventory/vendor-level-listing"),

		// --- client file ---
		getByID(app, "platform", "file-presigned-url", "Client file pre-signed URL by file id", H, "/client/api/v1/file/%s/get-presigned-url", "file_id"),

		// --- contractservice ---
		queryGet(app, "platform", "contract-attachment", "Contract attachment content (--query)", H, "/contractservice/api/v1/attachment"),
		queryGet(app, "platform", "contract-attachment-presigned-url", "Contract attachment pre-signed URL (--query)", H, "/contractservice/api/v1/attachment/pre-signed-url"),
		simpleGet(app, "platform", "contract-bulk-template", "Contract bulk-job template download", H, "/contractservice/api/v1/bulk-jobs/download-template"),
		queryGet(app, "platform", "contract-bulk-jobs", "Contract bulk-job list (--query)", H, "/contractservice/api/v1/bulk-jobs/list"),
		queryGet(app, "platform", "fbz-margins", "FBZ margins (--query)", H, "/contractservice/api/v1/common/fbz-margins"),
		simpleGet(app, "platform", "fbz-payment-terms", "FBZ payment terms", H, "/contractservice/api/v1/common/fbz-payment-terms"),
		queryGet(app, "platform", "brands-of-manufacturer", "Brands of a manufacturer (--query)", H, "/contractservice/api/v1/common/get-brands-of-manufacturer"),
		queryGet(app, "platform", "categories-of-manufacturer", "Categories of a manufacturer (--query)", H, "/contractservice/api/v1/common/get-categories-of-manufacturer"),
		queryGet(app, "platform", "subcategories-of-manufacturer", "Sub-categories of a manufacturer (--query)", H, "/contractservice/api/v1/common/get-subcategories-of-manufacturer"),
		queryGet(app, "platform", "contract-manufacturer-list", "Contract-service manufacturer/distributor search (--query)", H, "/contractservice/api/v1/common/manufacturer-list"),
		queryGet(app, "platform", "contract-vendor-details", "Contract-service vendor details by code (--query)", H, "/contractservice/api/v1/common/vendor-details"),
		queryGet(app, "platform", "contract-vendor-list", "Contract-service vendor search (--query)", H, "/contractservice/api/v1/common/vendor-list"),

		// --- relay config ---
		simpleGet(app, "platform", "relay-config", "Relay config", H, "/relay/api/v1/config"),
		simpleGet(app, "platform", "relay-config-data", "Relay feature-flag config data", H, "/relay/api/v1/config/get-configdata"),

		// --- vendor support / bulk-job ---
		queryGet(app, "platform", "vendor-attachment-presigned-url", "Vendor attachment pre-signed URL (--query)", H, "/vendor/api/v1/attachment/get-presigned-url"),
		simpleGet(app, "platform", "vendor-attachment-template", "Vendor attachment template", H, "/vendor/api/v1/attachment/get-template"),
		queryGet(app, "platform", "vendor-bulk-jobs", "Vendor bulk-ticket jobs (--query)", H, "/vendor/api/v1/bulk-job"),
		getByID(app, "platform", "vendor-bulk-report", "Vendor bulk-job report download by job id", H, "/vendor/api/v1/bulk-job/%s/download-report", "job_id"),
		simpleGet(app, "platform", "vendor-bulk-template", "Vendor bulk-ticket template download", H, "/vendor/api/v1/bulk-job/download-template"),
		queryGet(app, "platform", "vendor-search-ntv", "Vendor search NTV (--query)", H, "/vendor/api/v1/commons/search-ntv"),
		postRead(app, "platform", "vendor-search-ntv-post", "Vendor search NTV (POST body)", H, "/vendor/api/v1/commons/search-ntv", ""),
		simpleGet(app, "platform", "vendor-config", "Vendor meta-info / config load", H, "/vendor/api/v1/config/load"),
		queryGet(app, "platform", "vendor-document-download", "Vendor util document download (--query)", H, "/vendor/api/v2/util/document-download"),
	)
	return p
}
