package main

import "github.com/spf13/cobra"

func init() { registerSection(newReceivablesCmd) }

// newReceivablesCmd — Receivables / non-trade & receivable vendors (VMS). JIVO
// reads the receivable-vendor list, the non-trade-vendor list, and a vendor's
// KYC details. Approve/reject/update vendor are WRITES → out of scope
// (guardrail-blocked). Source: ../vault/vendor/Receivables.md.
func newReceivablesCmd(app *App) *cobra.Command {
	H := hostFCC
	rv := &cobra.Command{Use: "receivables", Short: "Receivable & non-trade vendors (VMS reads)"}
	rv.AddCommand(
		postRead(app, "receivables", "list", "Receivable-vendor list (GET_RECEIVABLE_VENDORS; POST-to-read)", H, "/vms/api/v1/receivable-vendor/filter", ""),
		queryGet(app, "receivables", "non-trade-list", "Non-trade-vendor list (GET_NON_TRADE_VENDORS; --query for filters)", H, "/vms/api/v1/non-trade-vendor/filter"),
		simpleGet(app, "receivables", "kyc", "Non-trade-vendor KYC details (GET_KYC_DETAILS)", H, "/vms/api/v1/non-trade-vendor/kyc"),
	)
	return rv
}
