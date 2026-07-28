---
entity: InvoicesService
domain: sales-ar
readable: false
methods: ["InvoicesService_GetApprovalTemplates", "InvoicesService_HandleApprovalRequest", "InvoicesService_RequestApproveCancellation", "InvoicesService_Cancel2"]
rows_oil: null
---
# InvoicesService
Approval and cancellation RPC helper for A/R invoices.
## Operations
- InvoicesService_GetApprovalTemplates
- InvoicesService_HandleApprovalRequest
- InvoicesService_RequestApproveCancellation
- InvoicesService_Cancel2

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[Invoices]]). Browse this service's operations with `./sapb1 ops InvoicesService`.
## Connections
- Domain: [[sales-ar]]
- [[Invoices]] — the A/R invoices being approved or cancelled
- [[ApprovalTemplates]] — approval templates applied to them
