package main

import "github.com/spf13/cobra"

func init() { registerSection(newBrandAnalyticsCmd) }

// newBrandAnalyticsCmd — Brand Analytics (ads lane): sales analytics, live
// monitor, fulfilment metrics, landing-page keyword insights, and the mobile
// subscription/access reads. All GET reads off the brand-analytics service on
// fcc.zepto.co.in. Landing-page write-shaped/opaque metrics without a read
// keyword are left out; guardrail blocks writes regardless.
// Source: captures/js/sections.json (slug "brand-analytics").
func newBrandAnalyticsCmd(app *App) *cobra.Command {
	H := hostFCC
	ba := &cobra.Command{Use: "brand-analytics", Short: "Brand analytics: sales, live-monitor & fulfilment reads (ads lane)"}
	ba.AddCommand(
		// Sales analytics
		simpleGet(app, "brand-analytics", "sa-overview", "Sales overview (SA_GET_SALES_OVERVIEW)", H, "/brand-analytics-web/api/v1/sales-analytics/sales-overview"),
		simpleGet(app, "brand-analytics", "sa-aov", "Average order value (SA_GET_AVERAGE_ORDER_VALUE)", H, "/brand-analytics-web/api/v1/sales-analytics/average-order-value"),
		simpleGet(app, "brand-analytics", "sa-asp", "Average selling price / unit (SA_GET_AVERAGE_SELLING_PRICE_PER_UNIT)", H, "/brand-analytics-web/api/v1/sales-analytics/average-selling-price"),
		simpleGet(app, "brand-analytics", "sa-offers", "Sales offers (SA_GET_OFFERS)", H, "/brand-analytics-web/api/v1/sales-analytics/offers"),
		simpleGet(app, "brand-analytics", "sa-product-performance", "Sales product performance", H, "/brand-analytics-web/api/v1/sales-analytics/product-performance"),
		// Live analytics (live monitor)
		simpleGet(app, "brand-analytics", "live-headers", "Live metric headers", H, "/brand-analytics-web/api/v1/live-analytics/metric-headers"),
		simpleGet(app, "brand-analytics", "live-orders", "Live order metrics", H, "/brand-analytics-web/api/v1/live-analytics/order-metrics"),
		simpleGet(app, "brand-analytics", "live-impressions", "Live impression metrics", H, "/brand-analytics-web/api/v1/live-analytics/impression-metrics"),
		simpleGet(app, "brand-analytics", "live-conversion", "Live conversion metrics", H, "/brand-analytics-web/api/v1/live-analytics/conversion-metrics"),
		queryGet(app, "brand-analytics", "live-product-list", "Live product list (--query for filters)", H, "/brand-analytics-web/api/v1/live-analytics/product-list"),
		// Fulfilment metrics
		simpleGet(app, "brand-analytics", "fulfilment-fill-rate", "Fulfilment fill rate (GET_FULFILMENT_FILL_RATE)", H, "/brand-analytics-web/api/v1/fulfilment/fill-rate"),
		simpleGet(app, "brand-analytics", "fulfilment-otif", "Fulfilment on-time-in-full (GET_FULFIMENT_ON_TIME_IN_FULL)", H, "/brand-analytics-web/api/v1/fulfilment/on-time-in-full"),
		simpleGet(app, "brand-analytics", "fulfilment-service-hours", "Fulfilment available-in-service-hours", H, "/brand-analytics-web/api/v1/fulfilment/available-in-service-hours"),
		// Landing page
		simpleGet(app, "brand-analytics", "top-keywords", "Top searched keywords", H, "/api/v1/landing-page/top-searched-keywords"),
		// Meta
		simpleGet(app, "brand-analytics", "last-updated", "Resource last-updated timestamps (GET_RESOURCE_LAST_UPDATED)", H, "/brand-analytics-web/api/v1/resource-last-updated"),
		// Mobile: subscription + access
		simpleGet(app, "brand-analytics", "mobile-user", "Mobile entity/access-management user (GET_ENTITY_DATA_FOR_MOBILE_APP)", H, "/brand-analytics-mobile/api/v1/access-management/user"),
		simpleGet(app, "brand-analytics", "mobile-subscription", "Mobile subscription user-details (GET_SUBSCRIPTION_DETAILS_MOBILE)", H, "/brand-analytics-mobile/api/v1/subscription/user-details"),
		simpleGet(app, "brand-analytics", "mobile-pricing", "Mobile subscription pricing-details (GET_PRICING_DETAILS_MOBILE)", H, "/brand-analytics-mobile/api/v1/subscription/pricing-details"),
		simpleGet(app, "brand-analytics", "mobile-visibility", "Mobile plan visibility-details (GET_PLAN_VISIBILITY_DETAILS_MOBILE)", H, "/brand-analytics-mobile/api/v1/subscription/visibility-details"),
	)
	return ba
}
