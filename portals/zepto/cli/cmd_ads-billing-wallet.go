package main

import "github.com/spf13/cobra"

func init() { registerSection(newWalletCmd) }

// newWalletCmd — Ads billing + wallet (ads-bff lane). JIVO's ads account reads
// its billing grid/summary/details, downloads billing bulk exports, inspects a
// file-job, and reads wallet balance + transfer asset-limits. Invoice generation,
// payment initiation, wallet transfers, CSV/presigned uploads and save-key are
// WRITES/EXPORTS → out of scope (guardrail-blocked). Source: ads-bff chunks.
func newWalletCmd(app *App) *cobra.Command {
	H := hostFCC
	w := &cobra.Command{Use: "wallet", Short: "Ads billing + wallet (ads-bff: billing, invoices-read, balance)"}
	w.AddCommand(
		// Billing reads
		queryGet(app, "wallet", "list", "Billing data grid (GET_BILLING_DATA; --query for filters)", H, "/ads-bff/api/v1/billing"),
		simpleGet(app, "wallet", "summary", "Billing summary tiles (GET_BILLING_SUMMARY)", H, "/ads-bff/api/v1/billing/summary"),
		simpleGet(app, "wallet", "details", "Billing details (GET_BILLING_DETAILS)", H, "/ads-bff/api/v1/billing-details"),
		simpleGet(app, "wallet", "vendor-code", "Billing vendor code (GET_VENDOR_CODE)", H, "/ads-bff/api/v1/billing-code"),
		simpleGet(app, "wallet", "bulk-download", "Billing bulk export download (BILLING_BULK_DOWNLOAD)", H, "/ads-bff/api/v1/billing/bulk-download"),
		simpleGet(app, "wallet", "table-metadata", "Billing management table metadata (GET_TABLE_METADATA)", H, "/ads-bff/api/v1/layout/config/billing_management_table_metadata"),
		// File-job read
		getByID(app, "wallet", "file-job-view", "File-job detail by id (getBulkDataList)", H, "/ads-bff/api/v1/file-job/view/%s", "job_id"),
		// User / wallet reads
		simpleGet(app, "wallet", "user-details", "Booking user details (GET_BOOKING_USER_DETAILS)", H, "/ads-bff/api/v1/users/details"),
		queryGet(app, "wallet", "wallet-details", "Wallet balance/details (getWalletDetails; --query for params)", H, "/ads-bff/api/v1/wallet/details"),
		queryGet(app, "wallet", "asset-limits", "Wallet transfer asset-limits (getWalletAssetLimits)", H, "/ads-bff/api/v1/wallet/transfer/asset-limits"),
		simpleGet(app, "wallet", "wallet-details-alt", "Wallet details (WALLET_DETAILS legacy path)", H, "/api/v1/wallet/details"),
		simpleGet(app, "wallet", "s3-presigned-url", "Wallet S3 presigned URL (read)", H, "/api/v1/wallet/s3/presigned-url"),
	)
	return w
}
