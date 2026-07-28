# Purchasing (A/P)

The procure-to-pay document chain: [[PurchaseRequests]] and [[PurchaseQuotations]] feed [[PurchaseOrders]], goods arrive on [[PurchaseDeliveryNotes]] (Goods Receipt PO), vendors bill via [[PurchaseInvoices]], and corrections flow through [[PurchaseCreditNotes]], [[PurchaseReturns]] and [[GoodsReturnRequest]]. [[LandedCosts]] allocates freight/customs onto imported stock (JIVO's imported-oil cost build-up — 522 documents live). Each document links [[BusinessPartners]] via CardCode, [[Items]] via line ItemCode, and its predecessor via BaseEntry/BaseType. JIVO's oil DB holds ~15.9k A/P invoices, ~11.2k GRPOs and ~4.2k purchase orders.

Part of the [[00-SAP-B1-Atlas]] — 24 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[PurchaseInvoices]] **(15,858 rows)** — A/P invoices — the legally binding vendor bills that create payables and drive vendor payments; the core purchasing ledger.
- [[PurchaseDeliveryNotes]] **(11,183 rows)** — Goods Receipt POs — records physical receipt of goods against purchase orders, updating inventory.
- [[PurchaseOrders]] **(4,168 rows)** — Purchase orders — commitments to vendors that start the procurement chain (PO → goods receipt → A/P invoice).
- [[PurchaseCreditNotes]] **(1,517 rows)** — A/P credit notes — vendor credits reversing purchase invoices for returns or price corrections.
- [[LandedCosts]] **(522 rows)** — Allocates import costs (freight, customs, insurance) onto received goods to compute true landed item cost — actively used for JIVO's oil imports.
- [[PurchaseReturns]] **(107 rows)** — Records goods returned to vendors (A/P return documents), reversing received quantities and vendor liability from purchase delivery notes.
- [[LandedCostsCodes]] **(24 rows)** — Master list of landed-cost types (freight, customs, agency charges, etc.) with allocation method and G/L account.
- [[CorrectionPurchaseInvoice]] — Localization document that corrects a posted A/P invoice (amount/tax/line fixes without a full credit-and-rebill).
- [[CorrectionPurchaseInvoiceReversal]] — Reverses a correction purchase invoice, restoring the original A/P invoice state.
- [[GoodsReturnRequest]] — Request document to return received goods to a vendor before the actual purchase return is posted (unused here).
- [[PurchaseQuotations]] — Vendor RFQ/quotation documents preceding purchase orders (unused here).
- [[PurchaseRequests]] — Internal purchase requisitions from employees that kick off procurement (unused here).
- [[PurchaseTaxInvoices]] — Localization-specific incoming tax invoice documents that record VAT/tax details for purchases separately from the A/P invoice (unused in JIVO_OIL_HANADB — 0 rows, so key fields are from standard SAP marketing-document schema, not live data).

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[CorrectionPurchaseInvoiceReversalService]] — RPC helper for correction-invoice reversal approval workflows (fetch templates, act on approval requests).
- [[CorrectionPurchaseInvoiceService]] — RPC helper handling approval workflow for correction purchase invoices.
- [[GoodsReturnRequestService]] — RPC helper for goods-return-request approvals and journal preview before posting.
- [[LandedCostsService]] — RPC helper that returns filtered lists of landed-cost documents.
- [[PurchaseCreditNotesService]] — RPC helper for A/P credit note approvals and alternate cancellation.
- [[PurchaseDeliveryNotesService]] — RPC helper for goods-receipt-PO (purchase delivery note) approvals and cancellation.
- [[PurchaseInvoicesService]] — RPC helper for A/P invoice approval workflow and alternate cancellation.
- [[PurchaseOrdersService]] — RPC helper for purchase order approval workflow.
- [[PurchaseQuotationsService]] — RPC helper for purchase quotation approval workflow.
- [[PurchaseRequestService]] — RPC helper for internal purchase request approval workflow.
- [[PurchaseReturnsService]] — RPC helper for goods return (purchase return) approvals and cancellation.
