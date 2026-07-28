---
entity: PurchaseRequestService
domain: purchasing
readable: false
methods: ["PurchaseRequestService_GetApprovalTemplates", "PurchaseRequestService_HandleApprovalRequest"]
rows_oil: null
---
# PurchaseRequestService
RPC helper for internal purchase request approval workflow.
## Operations
- PurchaseRequestService_GetApprovalTemplates
- PurchaseRequestService_HandleApprovalRequest

Entity sets are the read path in the CLI — read requisition rows through the [[PurchaseRequests]] entity set (`./sapb1 query PurchaseRequests`); browse this service's ops with `./sapb1 ops PurchaseRequestService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseRequests]] — the entity set whose documents this service approves
- [[ApprovalTemplates]] — approval templates fetched for the workflow
