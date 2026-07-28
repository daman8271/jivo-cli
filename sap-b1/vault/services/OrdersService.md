---
entity: OrdersService
domain: sales-ar
readable: false
methods: ["OrdersService_GetApprovalTemplates", "OrdersService_Preview", "OrdersService_HandleApprovalRequest"]
rows_oil: null
---
# OrdersService
Approval-workflow and posting-preview RPC helper for sales orders.
## Operations
- OrdersService_GetApprovalTemplates
- OrdersService_Preview
- OrdersService_HandleApprovalRequest

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[Orders]]). Browse this service's operations with `./sapb1 ops OrdersService`.
## Connections
- Domain: [[sales-ar]]
- [[Orders]] — the sales orders being previewed or approved
- [[ApprovalTemplates]] — approval templates applied to them
