# Banking & Payments

Everything that moves money in SAP B1: customer receipts ([[IncomingPayments]]), outgoing vendor payments ([[VendorPayments]]), [[Deposits]], checks ([[ChecksforPayment]]), credit-card settlements, bill-of-exchange portfolios, and A/R+A/P down payments. Master/setup entities define the plumbing — [[HouseBankAccounts]], [[Banks]], [[PaymentTermsTypes]], [[PaymentBlocks]], [[CreditCards]] and payment-run wizard config. At JIVO this is a high-volume domain: ~14.2k vendor payments and ~13.8k incoming payments live in the oil DB, all joined to [[BusinessPartners]] via CardCode and to invoices through payment lines' DocEntry references.

Part of the [[00-SAP-B1-Atlas]] — 38 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[VendorPayments]] **(14,197 rows)** — Outgoing payments to vendors (cash/check/transfer) clearing open A/P invoices — the A/P mirror of IncomingPayments.
- [[IncomingPayments]] **(13,759 rows)** — Customer receipts (cash/check/transfer/card) clearing open A/R invoices — a core high-volume ledger.
- [[PaymentDrafts]] **(1,491 rows)** — Draft incoming/outgoing payments awaiting approval or posting, convertible via SaveDraftToDocument.
- [[Banks]] **(65 rows)** — Master catalog of banks (codes, SWIFT/IBAN, country, outgoing-check defaults) referenced by house bank accounts and business partner bank details; 65 banks defined.
- [[PaymentTermsTypes]] **(29 rows)** — Payment-terms definitions (net days, installments, credit limits, default price list) assigned to business partners.
- [[HouseBankAccounts]] **(5 rows)** — The company's own bank accounts with G/L mappings, check numbering, and payment-series defaults.
- [[CreditCards]] **(1 row)** — Master list of credit-card companies accepted for payment, each mapped to a clearing G/L account.
- [[BankChargesAllocationCodes]] — Master list of allocation codes that map bank charges/fees to G/L expense accounts on payments. Empty in JIVO_OIL_HANADB; key fields inferred from SAP B1 schema (live table returned no rows).
- [[BankPages]] — Imported external bank-statement rows (the 'bank pages' used in external reconciliation) matching bank movements to G/L accounts and business partners. Empty in JIVO_OIL_HANADB.
- [[BankStatements]] — Electronic bank statements imported for bank-statement processing and reconciliation. Empty in JIVO_OIL_HANADB (reconciliation evidently done outside BSP); key fields inferred from SAP B1 schema.
- [[BillOfExchangeTransactions]] — Bill-of-exchange transactions (drafts/promissory notes) tracking BOE lifecycle from generation to collection. Empty in JIVO_OIL_HANADB — BOE functionality unused; key fields inferred from schema.
- [[BOEDocumentTypes]] — Setup table of bill-of-exchange document type codes. Empty in JIVO_OIL_HANADB — BOE unused; key fields inferred from schema.
- [[BOEInstructions]] — Setup table of instruction codes sent to the bank with bills of exchange (e.g. collection/discount instructions). Empty in JIVO_OIL_HANADB; key fields inferred from schema.
- [[BOEPortfolios]] — Setup table of BOE portfolios grouping bills of exchange by bank and G/L account for collection/discounting. Empty in JIVO_OIL_HANADB; key fields inferred from schema.
- [[ChecksforPayment]] — Outgoing checks written to vendors/payees, tracking check number, bank, amount, and print status.
- [[CreditCardPayments]] — Setup table defining credit-card due-date/settlement schedules used when clearing card vouchers.
- [[CreditPaymentMethods]] — Setup of credit-card payment methods (installments, amount ranges) per card company.
- [[Deposits]] — Bank deposits of received checks/cash/credit vouchers into house bank accounts.
- [[DownPayments]] — A/R down-payment invoices billing customers in advance, later applied against final invoices.
- [[PaymentBlocks]] — Reason codes for blocking documents/partners from the payment wizard.
- [[PaymentReasonCodes]] — Localization reason codes attached to payments for bank-file/reporting purposes.
- [[PaymentRunExport]] — Read-only export records produced by Payment Wizard runs for bank-file generation.
- [[PurchaseDownPayments]] — A/P down-payment invoices for advances paid to vendors, later netted against final purchase invoices.
- [[WizardPaymentMethods]] — Payment methods used by the Payment Wizard (bank, file format, amount limits) for batch payment runs.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[BankChargesAllocationCodesService]] — RPC helper that returns the list of bank-charge allocation codes used to book bank fees on payments.
- [[BankStatementsService]] — RPC helper that lists imported bank statements for the bank-statement processing (BSP) workflow.
- [[BOEDocumentTypesService]] — RPC helper that lists bill-of-exchange document type definitions.
- [[BOEInstructionsService]] — RPC helper that lists bill-of-exchange bank instruction codes.
- [[BOELinesService]] — RPC helper that fetches an individual bill-of-exchange line for BOE management.
- [[BOEPortfoliosService]] — RPC helper that lists bill-of-exchange portfolios (groupings of BOEs by bank/status).
- [[CheckLinesService]] — RPC helper that retrieves individual check lines and lists valid (depositable) checks received from customers.
- [[DepositsService]] — RPC service for the deposits workflow: listing deposits and cancelling individual check rows within them.
- [[DownPaymentsService]] — RPC service handling approval-workflow templates and requests for sales (A/R) down-payment invoices.
- [[PaymentBlocksService]] — RPC helper that lists payment block reason codes used to hold documents from the payment wizard.
- [[PaymentCalculationService]] — RPC helper that computes the payable amount for a document (applying cash discounts and payment terms).
- [[PaymentReasonCodeService]] — RPC helper that lists payment reason codes attached to bank-transfer payments for regulatory reporting.
- [[PaymentTermsTypesService]] — RPC service that updates a payment-terms definition and propagates the change to linked business partners.
- [[PurchaseDownPaymentsService]] — RPC service handling approval-workflow templates and requests for purchase (A/P) down-payment invoices.
