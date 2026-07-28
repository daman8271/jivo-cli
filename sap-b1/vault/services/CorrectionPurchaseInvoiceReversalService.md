---
entity: CorrectionPurchaseInvoiceReversalService
domain: purchasing
readable: false
methods: ["CorrectionPurchaseInvoiceReversalService_GetApprovalTemplates", "CorrectionPurchaseInvoiceReversalService_HandleApprovalRequest"]
rows_oil: null
---
# CorrectionPurchaseInvoiceReversalService
RPC helper for correction-invoice reversal approval workflows (fetch templates, act on approval requests).
## Operations
- CorrectionPurchaseInvoiceReversalService_GetApprovalTemplates
- CorrectionPurchaseInvoiceReversalService_HandleApprovalRequest

Entity sets are the read path in the CLI — read reversal rows through the [[CorrectionPurchaseInvoiceReversal]] entity set (`./sapb1 query CorrectionPurchaseInvoiceReversal`); browse this service's ops with `./sapb1 ops CorrectionPurchaseInvoiceReversalService`.
## Connections
- Domain: [[purchasing]]
- [[CorrectionPurchaseInvoiceReversal]] — the entity set whose documents this service approves
- [[ApprovalTemplates]] — approval templates fetched for the workflow
