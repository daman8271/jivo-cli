package main

import "github.com/spf13/cobra"

func init() { registerSection(newRTVCmd) }

// newRTVCmd — Return-to-Vendor (RTV). Zepto raises RTVs for stock it sends back
// to JIVO; JIVO reads the RTV grid/summary, the facility filter list, drills
// into one RTV (detail/items/checklist), reads its packing slips, and the v2
// listing. Schedule/download-job are WRITES/file-jobs → out of scope
// (guardrail-blocked). Source: ../vault/vendor/RTV.md.
func newRTVCmd(app *App) *cobra.Command {
	H := hostFCC
	rtv := &cobra.Command{Use: "rtv", Short: "Return-to-vendor (Zepto → JIVO returns)"}
	rtv.AddCommand(
		queryGet(app, "rtv", "list", "RTV list grid (GET_RTV_LISTING; --query for filters)", H, "/api/v1/rtv/filter"),
		queryGet(app, "rtv", "list-v2", "RTV list grid v2 (GET_RTV_LISTING_V2; --query for filters)", H, "/vendor/api/v2/rtv/filter"),
		simpleGet(app, "rtv", "summary", "RTV summary tiles (GET_RTV_SUMMARY)", H, "/api/v1/rtv/listing-stat"),
		simpleGet(app, "rtv", "facilities", "Facility / mother-hub filter list", H, "/api/v1/rtv/user/mh-list"),
		getByID(app, "rtv", "get", "RTV detail by id (getRtvDetailsById)", H, "/vendor/api/v2/rtv/%s", "rtv_id"),
		getByID(app, "rtv", "items", "RTV line items (getRtvItemsById)", H, "/vendor/api/v2/rtv/%s/items", "rtv_id"),
		getByID(app, "rtv", "checklist", "RTV checklist (getRtvChecklistById)", H, "/vendor/api/v2/rtv/%s/checklist", "rtv_id"),
		getByID(app, "rtv", "packing-slips", "RTV packing slips (getPackingSlipsById)", H, "/vendor/api/v1/rtv/%s/list-packing-slips", "rtv_id"),
	)
	return rtv
}
