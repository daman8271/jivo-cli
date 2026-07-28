# Sales (A/R)

The order-to-cash spine and JIVO's busiest domain: [[Quotations]] (1.7k) → [[Orders]] (14.6k) → [[DeliveryNotes]] (2.8k) → [[Invoices]] (30.3k), with money closing via [[IncomingPayments]] (in [[banking-payments]]). Reverse flows run through [[Returns]] (2k), [[ReturnRequest]] and [[CreditNotes]] (6.4k); [[Drafts]] holds 47.1k staged documents. Surrounding it: [[SalesPersons]] (155 reps on every document), [[BlanketAgreements]], [[DunningLetters]]/[[DunningTerms]] for collections, the [[SalesOpportunities]] CRM pipeline with its setup tables, [[SalesForecast]], and US-style sales-tax config. Documents chain via DocumentLines.BaseEntry/BaseType and all join customers via CardCode.

Part of the [[00-SAP-B1-Atlas]] — 44 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[Drafts]] **(47,115 rows)** — Holds unfinished/pending marketing documents of any type (orders, invoices, etc.) saved as drafts before posting; 47k drafts in JIVO_OIL suggests heavy draft-approval workflow.
- [[Invoices]] **(30,306 rows)** — A/R invoices — the core customer billing documents (30.3k rows); end of the Orders→DeliveryNotes→Invoices sales chain and the primary revenue record.
- [[Orders]] **(14,583 rows)** — Customer sales orders (14.6k rows) — commitments to deliver goods, the starting document of the sales fulfilment chain.
- [[CreditNotes]] **(6,351 rows)** — A/R credit memos issued to customers to reverse invoiced value or returned goods.
- [[DeliveryNotes]] **(2,821 rows)** — Sales delivery notes recording goods shipped to customers (the Orders → DeliveryNotes → Invoices chain).
- [[Returns]] **(1,976 rows)** — Goods-return documents reversing deliveries back into stock (~2k rows), typically followed by A/R credit memos.
- [[Quotations]] **(1,690 rows)** — Sales quotations — price offers to customers that can be copied to sales orders; 1.7k issued.
- [[SalesPersons]] **(155 rows)** — Master list of 155 sales employees with commission settings, referenced by every sales document via SalesPersonCode.
- [[SalesTaxAuthorities]] **(40 rows)** — Tax-authority definitions (40 rows, GST jurisdictions/components) holding rates and posting accounts that combine into tax codes.
- [[ReturnRequest]] **(32 rows)** — Customer return-request documents (RMA-style pre-approval before a Return is posted); lightly used (32 rows).
- [[SalesForecast]] **(23 rows)** — Sales forecasts of item quantities per period feeding MRP planning; 23 forecasts defined.
- [[SalesTaxCodes]] **(23 rows)** — The 23 combined tax codes (jurisdiction stacks) applied on document lines to compute GST/tax on sales and purchases.
- [[SalesTaxAuthoritiesTypes]] **(18 rows)** — Categories of tax authorities (18 types, e.g. CGST/SGST/IGST levels) that group authorities for tax-code assembly.
- [[BlanketAgreements]] — Long-term customer sales agreements (blanket agreements) committing quantities or amounts over a date range; empty in JIVO_OIL_HANADB so fields listed from the SAP B1 standard schema.
- [[CorrectionInvoice]] — A/R correction invoices (localization feature to correct posted invoices without credit notes); unused in JIVO_OIL_HANADB so key fields come from the standard marketing-document schema.
- [[CorrectionInvoiceReversal]] — Reversal documents that undo posted A/R correction invoices; unused in JIVO_OIL_HANADB so key fields come from the standard marketing-document schema.
- [[DunningLetters]] — Stores generated dunning (payment-reminder) letters sent to customers with overdue invoices; unused in JIVO_OIL.
- [[DunningTerms]] — Setup for dunning rules (levels, intervals, fees) applied to overdue customers; unused in JIVO_OIL.
- [[SalesOpportunities]] — CRM pipeline records tracking potential deals through stages to won/lost; CRM module unused in JIVO_OIL (0 rows).
- [[SalesOpportunityCompetitorsSetup]] — Lookup list of competitor names attachable to sales opportunities; empty.
- [[SalesOpportunityInterestsSetup]] — Lookup list of interest ranges/areas for classifying sales opportunities; empty.
- [[SalesOpportunityReasonsSetup]] — Lookup list of win/loss reasons for closed sales opportunities; empty.
- [[SalesOpportunitySourcesSetup]] — Lookup list of lead sources (e.g. referral, web) for sales opportunities; empty.
- [[SalesStages]] — Defines pipeline stages (with closing percentages) for sales opportunities; empty since CRM is unused.
- [[SalesTaxInvoices]] — Localization-specific sales tax invoices issued separately from A/R invoices for tax reporting; unused here.
- [[SelfInvoices]] — Self-billing invoices the company issues on a vendor's behalf (reverse-charge scenarios); unused in JIVO_OIL.
- [[TaxInvoiceReport]] — Tax-invoice reporting documents for localization tax filings (report/cancel lifecycle); unused in JIVO_OIL.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[BlanketAgreementsService]] — RPC helper that returns the list of blanket sales agreements for pickers/lookups.
- [[CorrectionInvoiceReversalService]] — Approval-workflow RPC helper for correction-invoice reversal documents.
- [[CorrectionInvoiceService]] — Approval-workflow RPC helper for A/R correction invoices.
- [[CreditNotesService]] — Approval and cancellation RPC helper for A/R credit notes.
- [[DeliveryNotesService]] — Approval and cancellation RPC helper for sales delivery notes.
- [[DraftsService]] — RPC helper to run approvals on document drafts and convert a draft into a posted document.
- [[DunningTermsService]] — RPC helper returning the list of dunning terms used for overdue A/R reminder runs.
- [[InvoicesService]] — Approval and cancellation RPC helper for A/R invoices.
- [[OrdersService]] — Approval-workflow and posting-preview RPC helper for sales orders.
- [[QuotationsService]] — Approval-workflow RPC helper for sales quotations.
- [[ReturnRequestService]] — Approval-workflow and preview RPC helper for customer return requests.
- [[ReturnsService]] — Approval and cancellation RPC helper for goods-return documents.
- [[SalesOpportunityCompetitorsSetupService]] — RPC helper listing the competitor master values used on sales opportunities.
- [[SalesOpportunityInterestsSetupService]] — RPC helper listing the interest-level master values used on sales opportunities.
- [[SalesOpportunityReasonsSetupService]] — RPC helper listing win/loss reason master values used on sales opportunities.
- [[SalesOpportunitySourcesSetupService]] — RPC helper listing the lead/opportunity source master values used on sales opportunities.
- [[SelfInvoiceService]] — Approval and cancellation RPC helper for self-invoice (localization-specific) documents.
