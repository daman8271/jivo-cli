package main

import "github.com/spf13/cobra"

func init() { registerSection(newPaymentsCmd) }

// newPaymentsCmd — Payments / settlements / ledger reads. JIVO reads invoice &
// credit-note grids and their summary tiles, payment advices, settlement/debit-
// note lists, and the vendor ledgers. Acknowledge is a WRITE → out of scope.
// Source: ../vault/vendor/Payments.md.
func newPaymentsCmd(app *App) *cobra.Command {
	H := hostFCC
	pay := &cobra.Command{Use: "payments", Short: "Payments, settlements & vendor ledger (read-only)"}
	pay.AddCommand(
		// Invoices
		queryGet(app, "payments", "invoice-list", "Invoice list grid (GET_INVOICE_LIST; --query for filters)", H, "/api/v1/payment/invoice/filter"),
		simpleGet(app, "payments", "invoice-summary", "Invoice summary tiles (GET_INVOICE_SUMMARY)", H, "/api/v1/payment/invoice/listing-stat"),
		// Ledger
		queryGet(app, "payments", "ledger-list", "Ledger list grid (--query for filters)", H, "/api/v1/payment/ledger/filter"),
		simpleGet(app, "payments", "ledger-summary", "Ledger summary tiles", H, "/api/v1/payment/ledger/summary"),
		// NTV / credit-note invoices
		queryGet(app, "payments", "ntv-invoice-list", "NTV credit-note invoice list grid (GET_INVOICE_CN_LIST)", H, "/api/v1/payment/ntv-invoice/filter"),
		simpleGet(app, "payments", "ntv-invoice-summary", "NTV credit-note invoice summary (GET_INVOICE_CN_SUMMARY)", H, "/api/v1/payment/ntv-invoice/listing-stat"),
		// Payment advice
		queryGet(app, "payments", "payment-advice-list", "Payment advice listing (GET_PAYMENT_ADVICE_LISTING)", H, "/api/v1/payment/payment-advice/filter"),
		simpleGet(app, "payments", "payment-advice-detail", "Payment advice reference detail (PAYMENT_ADVICE_DETAILS)", H, "/api/v1/payment/payment-advice/reference"),
		// Payment document
		getByID(app, "payments", "payment-doc", "Payment document by id (getPaymentDocById)", H, "/api/v1/payment/payment-doc/%s", "doc_id"),
		// RV invoices
		queryGet(app, "payments", "rv-invoice-list", "RV invoice list grid (GET_TOTAL_INVOICES)", H, "/api/v1/payment/rv-invoice/filter"),
		simpleGet(app, "payments", "rv-invoice-summary", "RV invoice summary tiles (GET_INVOICE_LISTING_STAT)", H, "/api/v1/payment/rv-invoice/listing-stat"),
		// Settlements / debit & credit notes
		queryGet(app, "payments", "rv-settlement-list", "RV settlement DN/CN list grid (GET_TOTAL_DN_CN)", H, "/api/v1/payment/rv-settlement/filter"),
		queryGet(app, "payments", "settlement-list", "Settlement DN/CN list grid (GET_DEBIT_AND_CREDIT_NOTE_LIST)", H, "/api/v1/payment/settlement/filter"),
		queryGet(app, "payments", "settlement-requested-list", "Requested DN/CN list grid (GET_REQUESTED_DEBIT_AND_CREDIT_NOTE_LIST)", H, "/api/v1/payment/settlement/requested-debit-note/filter"),
		simpleGet(app, "payments", "settlement-subtypes", "Settlement sub-type filter list (TYPE_FILTER_LIST)", H, "/api/v1/payment/settlement/sub-type-list"),
		// Vendor ledgers
		simpleGet(app, "payments", "ledger-zepto", "Zepto ledger listing (GET_ZEPTO_LEDGER_LISTING)", H, "/vendor/api/v1/payment/ledger/zepto"),
		queryGet(app, "payments", "rv-ledger-list", "RV ledger list grid (GET_RV_LEDGER_FILTER; --query for filters)", H, "/vendor/api/v1/payment/rv-ledger/filter"),
	)
	return pay
}
