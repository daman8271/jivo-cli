package main

import "github.com/spf13/cobra"

func init() { registerSection(newEngagementCmd) }

// newEngagementCmd — Engagement (Survey, Rewards & Zepto Square), an "ads"-lane
// section. Reads Zepto Square leaderboard/order stats, survey lists + per-survey
// detail/checklist/config, and the survey analytics dashboard (metrics, graphs,
// response download). Survey/reward creation, upsert and approval writes (PUT /
// create consts) are WRITES → out of scope (guardrail-blocked).
// Source: sections.json slug "engagement".
func newEngagementCmd(app *App) *cobra.Command {
	eng := &cobra.Command{Use: "engagement", Short: "Survey, rewards & Zepto Square reads (ads lane)"}
	eng.AddCommand(
		// Zepto Square — order/ranking stats (auth-backend)
		simpleGet(app, "engagement", "city-leaderboard", "Zepto Square city leaderboard/ranking (GET_CITY_RANKING)", hostAuth, "/api/v1/zepto-square/city-leaderboard"),
		queryGet(app, "engagement", "city-level-stats", "Zepto Square city-level order stats (GET_CITY_LEVEL_ORDERS; --query)", hostAuth, "/api/v1/zepto-square/city-level-stats"),
		simpleGet(app, "engagement", "india-level-stats", "Zepto Square India-level order counts (GET_ORDER_COUNTS)", hostAuth, "/api/v1/zepto-square/india-level-stats"),
		queryGet(app, "engagement", "product-level-stats", "Zepto Square product-level stats (GET_PRODUCT_LEVEL_STATS; --query)", hostAuth, "/api/v1/zepto-square/product-level-stats"),
		// Survey list + detail
		queryGet(app, "engagement", "list", "Survey list for brand (GET_SURVEYS_FOR_BRAND; --query)", hostFCC, "/survey/api/v1/survey/list"),
		queryGet(app, "engagement", "view-all", "View all surveys (VIEW_ALL_SURVEYS; --query)", hostFCC, "/survey/api/v1/survey/view-all"),
		getByID(app, "engagement", "get", "Survey detail by id (getSurveyDetails)", hostFCC, "/survey/api/v1/survey/%s", "survey_id"),
		getByID(app, "engagement", "checklist", "Survey-creation checklist by id (getSurveyChecklist)", hostFCC, "/survey/api/v1/survey-creation/%s/checklist", "survey_id"),
		simpleGet(app, "engagement", "config", "Survey-creation config (GET_SURVEY_CONFIG)", hostFCC, "/survey/api/v1/survey-creation/config"),
		// Approvals
		queryGet(app, "engagement", "approvals-list", "Created surveys pending approval (GET_CREATED_SURVEYS; --query)", hostFCC, "/survey/api/v1/approvals/list"),
		simpleGet(app, "engagement", "approvals-review", "Approval review detail (REVIEW_APPROVAL)", hostFCC, "/survey/api/v1/approvals/review"),
		// Survey analytics dashboard
		queryGet(app, "engagement", "analytics-metrics", "Survey dashboard summary metrics (GET_DASHBOARD_SUMMARY; --query)", hostFCC, "/survey/api/v1/survey-analytics/metrics"),
		queryGet(app, "engagement", "analytics-graph-data", "Survey dashboard graph data (GET_DASHBOARD_GRAPH_DATA; --query)", hostFCC, "/survey/api/v1/survey-analytics/graph-data"),
		simpleGet(app, "engagement", "analytics-graph-config", "Survey dashboard graph config (GET_DASHBOARD_GRAPH_CONFIG)", hostFCC, "/survey/api/v1/survey-analytics/graph-details"),
		queryGet(app, "engagement", "download-responses", "Download survey responses (DOWNLOAD_SURVEY_RESPONSES; --query)", hostFCC, "/survey/api/v1/survey-analytics/download-responses"),
	)
	return eng
}
