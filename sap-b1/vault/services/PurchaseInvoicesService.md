---
entity: PurchaseInvoicesService
domain: purchasing
readable: false
methods: ["PurchaseInvoicesService_GetApprovalTemplates", "PurchaseInvoicesService_HandleApprovalRequest", "PurchaseInvoicesService_Cancel2"]
rows_oil: null
---
# PurchaseInvoicesService
RPC helper for A/P invoice approval workflow and alternate cancellation.
## Operations
- PurchaseInvoicesService_GetApprovalTemplates
- PurchaseInvoicesService_HandleApprovalRequest
- PurchaseInvoicesService_Cancel2

Entity sets are the read path in the CLI — read A/P invoice rows through the [[PurchaseInvoices]] entity set (`./sapb1 query PurchaseInvoices`); browse this service's ops with `./sapb1 ops PurchaseInvoicesService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseInvoices]] — the entity set whose documents this service approves/cancels
- [[ApprovalTemplates]] — approval templates fetched for the workflow
