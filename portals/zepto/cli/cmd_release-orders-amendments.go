package main

import "github.com/spf13/cobra"

func init() { registerSection(newReleaseOrdersCmd) }

// newReleaseOrdersCmd — Release Orders & Amendment Requests (vendor lane).
// JIVO reads the amendment-request list, drills into one request's review,
// and sees which requests are pending on a reviewer. Bulk-submit / file-upload /
// upload-artifact and the ${e} release-order fetches (UNKNOWN, no read marker)
// are WRITES/EXPORTS or unconfirmed → out of scope (guardrail-blocked).
// Source: sections.json slug "release-orders-amendments".
func newReleaseOrdersCmd(app *App) *cobra.Command {
	H := hostFCC
	ro := &cobra.Command{Use: "release-orders", Short: "Release orders & amendment requests (vendor)"}
	ro.AddCommand(
		queryGet(app, "release-orders", "list", "Amendment-requests list grid (AMENDMENT_REQUESTS_LIST; --query for filters)", H, "/contractservice/api/v1/amendment-requests/list"),
		simpleGet(app, "release-orders", "pending-on-reviewer", "Amendment requests pending on a reviewer", H, "/contractservice/api/v1/amendment-requests/pending-on-reviewer"),
		getByID(app, "release-orders", "review", "Amendment-request review detail by id", H, "/contractservice/api/v1/amendment-requests/%s/review", "amendment_id"),
		simpleGet(app, "release-orders", "presigned-url", "Release-order S3 presigned download URL (READ_FILE)", H, "/api/v1/release-order/s3/presigned-url"),
	)
	return ro
}
