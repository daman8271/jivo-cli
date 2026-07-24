package main

import "github.com/spf13/cobra"

func init() { registerSection(newCampaignsCmd) }

// newCampaignsCmd — Ads: campaigns, booking & keywords (lane=ads, ads-bff).
// JIVO reads the campaign grid, booking list/metrics/metadata/owners, keyword +
// booking config, campaign review checklists, agent chat sessions, and the ads
// playground search. Create/edit/duplicate/approve/reject/submit + keyword
// mutations are WRITES → out of scope (guardrail-blocked). Source: ../vault/ads/.
func newCampaignsCmd(app *App) *cobra.Command {
	H := hostFCC // all ads-bff endpoints live on fcc.zepto.co.in
	c := &cobra.Command{Use: "campaigns", Short: "Ads campaigns, booking & keywords (ads-bff)"}
	c.AddCommand(
		// campaigns
		queryGet(app, "campaigns", "list", "Campaign grid (GET_TABLE_DATA; --query for filters)", H, "/ads-bff/api/v1/campaigns"),
		getByID(app, "campaigns", "debug", "Campaign debug detail by id", H, "/api/v1/campaigns/debug/%s", "campaign_id"),
		queryGet(app, "campaigns", "reviews", "Campaign review checklist (GET_CAMPAIGN_REVIEW_CHECKLIST; --query ids=..)", H, "/ads-bff/api/v1/campaigns/reviews"),
		queryGet(app, "campaigns", "reviews-2", "Campaign reviews (alt path; --query ids=..)", H, "/api/v1/campaigns/reviews"),
		// booking
		queryGet(app, "campaigns", "booking-list", "Booking list (LIST_BOOKINGS; --query for filters)", H, "/ads-bff/api/v1/booking"),
		simpleGet(app, "campaigns", "booking-download", "Booking list for download (LIST_BOOKINGS_FOR_DOWNLOAD)", H, "/ads-bff/api/v1/booking/download"),
		simpleGet(app, "campaigns", "booking-metrics", "Booking expense/summary metrics (GET_SUMMARY_METRIC)", H, "/ads-bff/api/v1/booking/expense-metrics"),
		simpleGet(app, "campaigns", "booking-metadata", "Booking metadata (GET_METADATA)", H, "/ads-bff/api/v1/booking/metadata"),
		simpleGet(app, "campaigns", "booking-owners", "Booking owners list (GET_OWNERS_LIST)", H, "/ads-bff/api/v1/booking/owner"),
		simpleGet(app, "campaigns", "booking-terms", "Booking approval terms & conditions config", H, "/api/v1/layout/config/booking_approval_terms_and_conditions"),
		// keywords / playground
		simpleGet(app, "campaigns", "keyword-config", "Keyword config (KEYWORD_CONFIG)", H, "/api/v1/keyword/config"),
		queryGet(app, "campaigns", "playground-search", "Ads playground search (--query for params)", H, "/api/v1/playground/search"),
		// agent chat sessions
		simpleGet(app, "campaigns", "jarvis-sessions", "Jarvis-agent chat sessions (GET_SESSIONS)", H, "/ads-bff/api/v1/agents/jarvis-agent/sessions"),
		simpleGet(app, "campaigns", "kam-sessions", "KAM-agent chat sessions (GET_SESSIONS)", H, "/ads-bff/api/v1/agents/kam-agent/sessions"),
	)
	return c
}
