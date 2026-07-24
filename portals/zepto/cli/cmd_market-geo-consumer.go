package main

import "github.com/spf13/cobra"

func init() { registerSection(newInsightsCmd) }

// newInsightsCmd — Market, Geo & Consumer Insights (ads lane).
// Brand-analytics reads: hyperlocal geo-analytics scorecards/cards, market-share
// (GMV, share-of-voice, top-of-search, new-users), price/discount elasticity, and
// consumer persona (heat-maps, city data, overviews). All GET/read analytics —
// nothing here writes. coordinates/decode is skipped (not a clear read).
// Source: sections.json slug "market-geo-consumer" (host fcc.zepto.co.in).
func newInsightsCmd(app *App) *cobra.Command {
	H := hostFCC
	in := &cobra.Command{Use: "insights", Short: "Market, geo & consumer insights (analytics reads)"}
	in.AddCommand(
		// Geo-analytics hyperlocal scorecards / cards (--query for date/city filters)
		queryGet(app, "insights", "city-performance", "Hyperlocal city-level performance (GI_GET_HYPERLOCAL_CITY_PERFORMANCE)", H, "/api/v1/geo-analytics/city-level-performance"),
		queryGet(app, "insights", "fulfillment-scorecard", "Geo fulfillment scorecard", H, "/api/v1/geo-analytics/fulfillment-scorecard"),
		queryGet(app, "insights", "insights-card", "Hyperlocal insights card", H, "/api/v1/geo-analytics/hyperlocal-insights-card"),
		queryGet(app, "insights", "product-performance", "Hyperlocal product-level performance", H, "/api/v1/geo-analytics/product-level-performance"),
		queryGet(app, "insights", "sales-scorecard", "Geo sales scorecard", H, "/api/v1/geo-analytics/sales-scorecard"),
		queryGet(app, "insights", "slider-data", "Geo-analytics slider data", H, "/api/v1/geo-analytics/slider-data"),
		queryGet(app, "insights", "store-geofence", "Geo store geofence", H, "/api/v1/geo-analytics/store-geofence"),
		queryGet(app, "insights", "store-performance", "Hyperlocal store-level performance", H, "/api/v1/geo-analytics/store-level-performance"),
		queryGet(app, "insights", "store-locations", "Geo store locations", H, "/api/v1/geo-analytics/store-locations"),
		queryGet(app, "insights", "store-metrics", "Hyperlocal store metrics", H, "/api/v1/geo-analytics/store-metrics"),
		// Elasticity (brand-analytics-web)
		queryGet(app, "insights", "elasticity-discount-roi", "Elasticity: discount ROI", H, "/brand-analytics-web/api/v1/elasticity/discount-roi"),
		queryGet(app, "insights", "elasticity-inventory-pulse", "Elasticity: inventory pulse", H, "/brand-analytics-web/api/v1/elasticity/inventory-pulse"),
		queryGet(app, "insights", "elasticity-pack-size", "Elasticity: pack size over time", H, "/brand-analytics-web/api/v1/elasticity/pack-size-over-time"),
		queryGet(app, "insights", "elasticity-price-volume", "Elasticity: price vs volume", H, "/brand-analytics-web/api/v1/elasticity/price-volume"),
		queryGet(app, "insights", "elasticity-shopper-clock", "Elasticity: shopper clock", H, "/brand-analytics-web/api/v1/elasticity/shopper-clock"),
		queryGet(app, "insights", "elasticity-trial-to-loyalty", "Elasticity: trial to loyalty", H, "/brand-analytics-web/api/v1/elasticity/trial-to-loyalty"),
		// Geo-analytics (brand-analytics-web mirror)
		queryGet(app, "insights", "ba-city-performance", "BA geo: city-level performance", H, "/brand-analytics-web/api/v1/geo-analytics/city-level-performance"),
		queryGet(app, "insights", "ba-fulfillment-scorecard", "BA geo: fulfillment scorecard", H, "/brand-analytics-web/api/v1/geo-analytics/fulfillment-scorecard"),
		queryGet(app, "insights", "ba-insights-card", "BA geo: hyperlocal insights card", H, "/brand-analytics-web/api/v1/geo-analytics/hyperlocal-insights-card"),
		queryGet(app, "insights", "ba-product-performance", "BA geo: product-level performance", H, "/brand-analytics-web/api/v1/geo-analytics/product-level-performance"),
		queryGet(app, "insights", "ba-sales-scorecard", "BA geo: sales scorecard", H, "/brand-analytics-web/api/v1/geo-analytics/sales-scorecard"),
		queryGet(app, "insights", "ba-slider-data", "BA geo: slider data", H, "/brand-analytics-web/api/v1/geo-analytics/slider-data"),
		queryGet(app, "insights", "ba-store-geofence", "BA geo: store geofence", H, "/brand-analytics-web/api/v1/geo-analytics/store-geofence"),
		queryGet(app, "insights", "ba-store-performance", "BA geo: store-level performance", H, "/brand-analytics-web/api/v1/geo-analytics/store-level-performance"),
		queryGet(app, "insights", "ba-store-locations", "BA geo: store locations", H, "/brand-analytics-web/api/v1/geo-analytics/store-locations"),
		queryGet(app, "insights", "ba-store-metrics", "BA geo: store metrics", H, "/brand-analytics-web/api/v1/geo-analytics/store-metrics"),
		// Market share
		queryGet(app, "insights", "market-share-bill-penetration", "Market share: bill penetration", H, "/brand-analytics-web/api/v1/market-share/calculate-bill-penetration"),
		queryGet(app, "insights", "market-share-new-users", "Market share: new-users percentage (MARKET_SHARE_GET_NEW_USERS_PERCENTAGE)", H, "/brand-analytics-web/api/v1/market-share/get-new-users-percentage"),
		queryGet(app, "insights", "market-share-gmv-units", "Market share: GMV and units", H, "/brand-analytics-web/api/v1/market-share/gmv-and-units"),
		queryGet(app, "insights", "market-share-share-of-voice", "Market share: share of voice", H, "/brand-analytics-web/api/v1/market-share/share-of-voice"),
		queryGet(app, "insights", "market-share-top-of-search", "Market share: top of search", H, "/brand-analytics-web/api/v1/market-share/top-of-search"),
		// Consumer persona
		queryGet(app, "insights", "persona-city-data", "Persona: city data", H, "/brand-analytics-web/api/v1/persona/city-data"),
		queryGet(app, "insights", "persona-graph-configs", "Persona: graph configs", H, "/brand-analytics-web/api/v1/persona/graph-configs"),
		queryGet(app, "insights", "persona-graph-data", "Persona: graph data", H, "/brand-analytics-web/api/v1/persona/graph-data"),
		queryGet(app, "insights", "persona-heat-map", "Persona: heat map", H, "/brand-analytics-web/api/v1/persona/heat-map"),
		queryGet(app, "insights", "persona-heat-map-basket", "Persona: heat-map basket L3 category", H, "/brand-analytics-web/api/v1/persona/heat-map-basket-l3-category"),
		queryGet(app, "insights", "persona-list", "Persona: list", H, "/brand-analytics-web/api/v1/persona/list"),
		queryGet(app, "insights", "persona-overview", "Persona: overview", H, "/brand-analytics-web/api/v1/persona/overview"),
	)
	return in
}
