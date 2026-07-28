---
entity: PurchaseOrdersService
domain: purchasing
readable: false
methods: ["PurchaseOrdersService_GetApprovalTemplates", "PurchaseOrdersService_HandleApprovalRequest"]
rows_oil: null
---
# PurchaseOrdersService
RPC helper for purchase order approval workflow.
## Operations
- PurchaseOrdersService_GetApprovalTemplates
- PurchaseOrdersService_HandleApprovalRequest

Entity sets are the read path in the CLI — read PO rows through the [[PurchaseOrders]] entity set (`./sapb1 query PurchaseOrders`); browse this service's ops with `./sapb1 ops PurchaseOrdersService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseOrders]] — the entity set whose documents this service approves
- [[ApprovalTemplates]] — approval templates fetched for the workflow
