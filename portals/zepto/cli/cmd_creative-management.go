package main

import "github.com/spf13/cobra"

func init() { registerSection(newCreativeCmd) }

// newCreativeCmd — Creative Management (ads lane, ads-bff). Reads the ad-creative
// building blocks used when composing a campaign: the inventory ad-unit details
// and the campaign-asset bundle/format config. Banner create + banner-generation
// exports are WRITES/EXPORTS → out of scope (guardrail-blocked).
// Source: sections.json slug "creative-management" (host fcc.zepto.co.in).
func newCreativeCmd(app *App) *cobra.Command {
	H := hostFCC
	creative := &cobra.Command{Use: "creative", Short: "Ad creative management (inventory ad-units + asset bundle config)"}
	creative.AddCommand(
		queryGet(app, "creative", "inventory-details", "Inventory ad-unit details (GET_INVENTORY_AD_UNITS; --query for filters)", H, "/api/v1/creative-management/inventory/details"),
		simpleGet(app, "creative", "bundle-config", "Campaign asset formats / bundle config (GET_CAMPAIGN_ASSETS_FORMATS)", H, "/api/v1/creative-management/bundle-config"),
	)
	return creative
}
