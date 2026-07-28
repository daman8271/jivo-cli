---
entity: CorrectionInvoiceService
domain: sales-ar
readable: false
methods: ["CorrectionInvoiceService_GetApprovalTemplates", "CorrectionInvoiceService_HandleApprovalRequest"]
rows_oil: null
---
# CorrectionInvoiceService
Approval-workflow RPC helper for A/R correction invoices.
## Operations
- CorrectionInvoiceService_GetApprovalTemplates
- CorrectionInvoiceService_HandleApprovalRequest

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops CorrectionInvoiceService`.
## Connections
- Domain: [[sales-ar]]
- [[CorrectionInvoice]] — the correction invoices the approvals run on
- [[ApprovalTemplates]] — approval templates applied to them
