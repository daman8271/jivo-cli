package main

import "github.com/spf13/cobra"

func init() { registerSection(newLedgerCmd) }

// newLedgerCmd — Ledger (Recon & Upload). JIVO reads its ledger-reconciliation
// state on Zepto's vendor portal: external-view status, the recon user context,
// recon workings (filter grid + closing balances), the statement details, and a
// bulk-download of the reconciled ledger. Upload/create/trigger-recon/sign-off
// and the EXPORT-classified listings are WRITES/exports → out of scope
// (guardrail-blocked). Source: ../vault/vendor/Ledger*.md.
func newLedgerCmd(app *App) *cobra.Command {
	H := hostFCC
	l := &cobra.Command{Use: "ledger", Short: "Ledger reconciliation reads (vendor recon state)"}
	l.AddCommand(
		simpleGet(app, "ledger", "external-view-status", "External-view toggle status (GET_EXTERNAL_VIEW_STATUS)", H, "/vendor/api/v1/ledger-recon/external-view/status"),
		simpleGet(app, "ledger", "recon-user-data", "Recon user context (GET_RECON_USER_DATA)", H, "/vendor/api/v1/ledger-recon/recon-user-data"),
		simpleGet(app, "ledger", "statement-details", "Recon statement details", H, "/vendor/api/v1/ledger-recon/statement/details"),
		simpleGet(app, "ledger", "closing-balances", "Recon working closing balances (GET_CLOSING_BALANCES)", H, "/vendor/api/v1/ledger-recon/working/closing-balances"),
		queryGet(app, "ledger", "workings", "Recon workings list grid (GET_RECON_WORKINGS_LISTING; --query for filters)", H, "/vendor/api/v1/ledger-recon/working/filter"),
	)
	return l
}
