---
entity: CorrectionInvoiceReversalService
domain: sales-ar
readable: false
methods: ["CorrectionInvoiceReversalService_GetApprovalTemplates", "CorrectionInvoiceReversalService_HandleApprovalRequest"]
rows_oil: null
---
# CorrectionInvoiceReversalService
Approval-workflow RPC helper for correction-invoice reversal documents.
## Operations
- CorrectionInvoiceReversalService_GetApprovalTemplates
- CorrectionInvoiceReversalService_HandleApprovalRequest

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops CorrectionInvoiceReversalService`.
## Connections
- Domain: [[sales-ar]]
- [[CorrectionInvoiceReversal]] — the reversal documents the approvals run on
- [[ApprovalTemplates]] — approval templates applied to them
