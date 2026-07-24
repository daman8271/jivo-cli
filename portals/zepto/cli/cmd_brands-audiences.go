package main

import "github.com/spf13/cobra"

func init() { registerSection(newBrandsCmd) }

// newBrandsCmd — Brands & Audiences (ads lane). Read the brand catalogue,
// parent-brand hierarchy, subcategory / targeting-option pick-lists, and the
// brand + campaign analytics surfaces (metadata / metrics / summary). Audience
// save, report downloads, smart-nudge writes are WRITES/EXPORTS → out of scope
// (guardrail-blocked). All endpoints live on fcc.zepto.co.in under /ads-bff.
// Source: ../vault (brands-audiences section, ads-bff BFF).
func newBrandsCmd(app *App) *cobra.Command {
	H := hostFCC
	b := &cobra.Command{Use: "brands", Short: "Brands & audiences catalogue + analytics (ads)"}
	b.AddCommand(
		// Brand catalogue + pick-lists
		queryGet(app, "brands", "list", "Brands list (GET_BRANDS_LIST_DATA; --query for filters)", H, "/ads-bff/api/v1/brands"),
		simpleGet(app, "brands", "subcategories", "Brand subcategory list (GET_SUBCATEGOEIES_LIST)", H, "/ads-bff/api/v1/brands/subcategory"),
		simpleGet(app, "brands", "targeting-options", "Brand targeting / L3-category options (GET_BRAND_CATEGORIES)", H, "/ads-bff/api/v1/brands/targeting-options"),
		// Parent-brand hierarchy
		queryGet(app, "brands", "parent-brands", "Parent-brand list (GET_PARENT_BRANDS_LIST; --query for filters)", H, "/ads-bff/api/v1/parent-brand"),
		getByID(app, "brands", "parent-brand-users", "Approver / user options for a parent brand", H, "/ads-bff/api/v1/parent-brand/%s/users", "parent_brand_id"),
		// Brand analytics
		simpleGet(app, "brands", "analytics-metadata", "Brand analytics header metadata (GET_HEADERS_DATA)", H, "/api/v1/brands/analytics/metadata"),
		simpleGet(app, "brands", "analytics-summary", "Brand analytics details-tab summary (DETAILS_TAB_SUMMARY)", H, "/api/v1/brands/analytics/summary"),
		queryGet(app, "brands", "analytics-metrics", "Brand analytics metrics (GET_BRAND_METRICS; --query for range)", H, "/api/v1/brands/analytics/metrics"),
		queryGet(app, "brands", "analytics-metrics-tabular", "Brand analytics metrics tabular (GET_BRAND_TABULAR_DATA)", H, "/api/v1/brands/analytics/metrics/tabular"),
		// Campaign analytics (brand scope)
		simpleGet(app, "brands", "campaigns-analytics-metadata", "Campaign analytics metadata (GET_CAMPAIGN_METRICS_DATA)", H, "/api/v1/brands/campaigns/analytics/metadata"),
		queryGet(app, "brands", "campaigns-analytics-metrics", "Campaign analytics metrics (GET_CAMPAIGN_METRICS)", H, "/api/v1/brands/campaigns/analytics/metrics"),
		queryGet(app, "brands", "campaigns-analytics-metrics-tabular", "Campaign analytics metrics tabular (GET_CAMPAIGN_TABULAR_DATA)", H, "/api/v1/brands/campaigns/analytics/metrics/tabular"),
	)
	return b
}
