---
entity: PurchaseReturnsService
domain: purchasing
readable: false
methods: ["PurchaseReturnsService_GetApprovalTemplates", "PurchaseReturnsService_HandleApprovalRequest", "PurchaseReturnsService_Cancel2"]
rows_oil: null
---
# PurchaseReturnsService
RPC helper for goods return (purchase return) approvals and cancellation.
## Operations
- PurchaseReturnsService_GetApprovalTemplates
- PurchaseReturnsService_HandleApprovalRequest
- PurchaseReturnsService_Cancel2

Entity sets are the read path in the CLI — read return rows through the [[PurchaseReturns]] entity set (`./sapb1 query PurchaseReturns`); browse this service's ops with `./sapb1 ops PurchaseReturnsService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseReturns]] — the entity set whose documents this service approves/cancels
- [[ApprovalTemplates]] — approval templates fetched for the workflow
