package main

import "github.com/spf13/cobra"

func init() { registerSection(newSubscriptionCmd) }

// newSubscriptionCmd — Subscription & Billing (platform lane, brand-analytics
// plan subscription + ads billing). Reads the user's current plan/subscription
// details, pricing tiers, and plan visibility. Actual subscribe/on-credit calls
// are WRITES → out of scope (guardrail-blocked). Source: sections.json
// slug "subscription-billing".
func newSubscriptionCmd(app *App) *cobra.Command {
	H := hostFCC
	sub := &cobra.Command{Use: "subscription", Short: "Plan subscription + billing details (brand-analytics)"}
	sub.AddCommand(
		// Generic (host-relative) subscription reads.
		simpleGet(app, "subscription", "pricing-details", "Subscription pricing tiers (GET_PRICING_DETAILS)", H, "/api/v1/subscription/pricing-details"),
		simpleGet(app, "subscription", "user-details", "Current user subscription details (GET_SUBSCRIPTION_DETAILS)", H, "/api/v1/subscription/user-details"),
		simpleGet(app, "subscription", "visibility-details", "Plan visibility details (GET_PLAN_VISIBILITY_DETAILS)", H, "/api/v1/subscription/visibility-details"),
		// Web-app subscription reads.
		simpleGet(app, "subscription", "pricing-details-web", "Subscription pricing tiers — web (GET_PRICING_DETAILS_WEB)", H, "/brand-analytics-web/api/v1/subscription/pricing-details"),
		simpleGet(app, "subscription", "user-details-web", "User subscription details — web (GET_SUBSCRIPTION_DETAILS_WEB)", H, "/brand-analytics-web/api/v1/subscription/user-details"),
		simpleGet(app, "subscription", "visibility-details-web", "Plan visibility details — web (GET_PLAN_VISIBILITY_DETAILS_WEB)", H, "/brand-analytics-web/api/v1/subscription/visibility-details"),
		// NOTE: subscribe/free-tier (POST) removed after review — POST to
		// subscribe/* is a subscription-enrolment WRITE (sibling of the
		// out-of-scope subscribe/on-credit), not a read. Out of scope.
	)
	return sub
}
