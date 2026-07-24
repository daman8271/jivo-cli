package main

import "github.com/spf13/cobra"

func init() { registerSection(newStockCmd) }

// newStockCmd — Stock & Inventory (brand-analytics stock-view). JIVO reads
// availability and on-hand inventory rolled up at city / product / store level
// plus the top-line summary tiles. All GET reads; no writes in this section.
func newStockCmd(app *App) *cobra.Command {
	H := hostFCC
	stock := &cobra.Command{Use: "stock", Short: "Stock & inventory availability (brand-analytics stock-view)"}
	stock.AddCommand(
		// Availability views
		simpleGet(app, "stock", "availability", "Raw stock availability feed", H, "/api/v1/inventory/availability"),
		queryGet(app, "stock", "avail-city", "Availability by city (--query for filters)", H, "/brand-analytics-web/api/v1/stock-view/availability/city-level-performance"),
		queryGet(app, "stock", "avail-product", "Availability by product (--query for filters)", H, "/brand-analytics-web/api/v1/stock-view/availability/product-level-performance"),
		queryGet(app, "stock", "avail-store", "Availability by store (--query for filters)", H, "/brand-analytics-web/api/v1/stock-view/availability/store-level-performance"),
		simpleGet(app, "stock", "avail-summary", "Availability summary tiles", H, "/brand-analytics-web/api/v1/stock-view/availability/summary"),
		// Inventory views
		queryGet(app, "stock", "inv-city", "Inventory by city (--query for filters)", H, "/brand-analytics-web/api/v1/stock-view/inventory/city-level-performance"),
		queryGet(app, "stock", "inv-product", "Inventory by product (--query for filters)", H, "/brand-analytics-web/api/v1/stock-view/inventory/product-level-performance"),
		queryGet(app, "stock", "inv-store", "Inventory by store (--query for filters)", H, "/brand-analytics-web/api/v1/stock-view/inventory/store-level-performance"),
		simpleGet(app, "stock", "inv-summary", "Inventory summary tiles", H, "/brand-analytics-web/api/v1/stock-view/inventory/summary"),
	)
	return stock
}
