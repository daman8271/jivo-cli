package main

import "github.com/spf13/cobra"

func init() { registerSection(newCatalogCmd) }

// newCatalogCmd — Catalog & Catalog Health. JIVO reads its SKU catalog-health
// dashboard (attribute/ruleset scores, per-PVID attributes), searches the
// category hierarchy, and reads the SKU-onboarding side (drafts, list, skus,
// template, failed-download). Uploads/exports/send-to-vendor are WRITES → out of
// scope (guardrail-blocked). Ads-bff catalog product endpoints were UNKNOWN with
// non-reading paths → skipped. Source: catalog section (lane vendor).
func newCatalogCmd(app *App) *cobra.Command {
	H := hostFCC
	c := &cobra.Command{Use: "catalog", Short: "Catalog & catalog-health reads (SKU health scores, onboarding drafts)"}
	c.AddCommand(
		// Catalog-health dashboard
		simpleGet(app, "catalog", "attribute-view", "Catalog-health attribute view (GET_ATTRIBUTE_VIEW)", H, "/vendor/api/v1/catalog-health-dashboard/attribute-view"),
		getByID(app, "catalog", "l4-values", "All attributes for a PVID (getAllAttibutesForPvId)", H, "/vendor/api/v1/catalog-health-dashboard/get-l4-values/%s", "pv_id"),
		simpleGet(app, "catalog", "sku-rule-scores", "SKU rule scores (GET_SKU_RULE_SCORES)", H, "/vendor/api/v1/catalog-health-dashboard/sku-rule-scores"),
		simpleGet(app, "catalog", "sku-ruleset-overview", "SKU ruleset-score overview (GET_SKU_RULESET_SCORE_OVERVIEW)", H, "/vendor/api/v1/catalog-health-dashboard/sku-ruleset-score/overview"),
		simpleGet(app, "catalog", "sku-ruleset-scores", "SKU ruleset scores (GET_PRODUCT_SCORES)", H, "/vendor/api/v1/catalog-health-dashboard/sku-ruleset-scores"),
		queryGet(app, "catalog", "attributes-by-pv-id", "Suggestion attributes by PVID (GET_ATTRIBUTES_BY_PV_ID; --query)", H, "/vendor/api/v1/catalog-health-dashboard/suggestions/get-attributes-by-pv-id"),
		// Category hierarchy
		queryGet(app, "catalog", "category-search", "Search category hierarchy (SEARCH_CATEGORIES; --query)", H, "/vendor/api/v1/catalog/category-hierarchy/search"),
		// SKU onboarding reads
		simpleGet(app, "catalog", "failed-download", "Failed-rows download (FAILED_DOWNLOAD)", H, "/vendor/api/v1/catalog/failed-download"),
		simpleGet(app, "catalog", "drafts", "SKU-onboarding drafts (GET_DRAFTS)", H, "/vendor/api/v1/catalog/sku-onboarding/drafts"),
		queryGet(app, "catalog", "sku-onboarding-list", "SKU-onboarding list grid (SKU_ONBOARDING_LIST; --query)", H, "/vendor/api/v1/catalog/sku-onboarding/list"),
		simpleGet(app, "catalog", "presigned-url", "SKU-onboarding presigned URL (PRESIGNED_URL; classified READ_FILE)", H, "/vendor/api/v1/catalog/sku-onboarding/presigned-url"),
		queryGet(app, "catalog", "skus", "SKU-onboarding SKUs (GET_SKUS; --query)", H, "/vendor/api/v1/catalog/sku-onboarding/skus"),
		simpleGet(app, "catalog", "template", "SKU-onboarding CSV template (GET_CSV_TEMPLATE)", H, "/vendor/api/v1/catalog/sku-onboarding/template"),
	)
	return c
}
