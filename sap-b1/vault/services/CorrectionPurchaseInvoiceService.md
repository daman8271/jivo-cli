---
entity: CorrectionPurchaseInvoiceService
domain: purchasing
readable: false
methods: ["CorrectionPurchaseInvoiceService_GetApprovalTemplates", "CorrectionPurchaseInvoiceService_HandleApprovalRequest"]
rows_oil: null
---
# CorrectionPurchaseInvoiceService
RPC helper handling approval workflow for correction purchase invoices.
## Operations
- CorrectionPurchaseInvoiceService_GetApprovalTemplates
- CorrectionPurchaseInvoiceService_HandleApprovalRequest

Entity sets are the read path in the CLI — read correction-invoice rows through the [[CorrectionPurchaseInvoice]] entity set (`./sapb1 query CorrectionPurchaseInvoice`); browse this service's ops with `./sapb1 ops CorrectionPurchaseInvoiceService`.
## Connections
- Domain: [[purchasing]]
- [[CorrectionPurchaseInvoice]] — the entity set whose documents this service approves
- [[ApprovalTemplates]] — approval templates fetched for the workflow
