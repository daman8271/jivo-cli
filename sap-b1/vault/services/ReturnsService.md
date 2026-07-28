---
entity: ReturnsService
domain: sales-ar
readable: false
methods: ["ReturnsService_GetApprovalTemplates", "ReturnsService_HandleApprovalRequest", "ReturnsService_Cancel2"]
rows_oil: null
---
# ReturnsService
Approval and cancellation RPC helper for goods-return documents.
## Operations
- ReturnsService_GetApprovalTemplates
- ReturnsService_HandleApprovalRequest
- ReturnsService_Cancel2

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[Returns]]). Browse this service's operations with `./sapb1 ops ReturnsService`.
## Connections
- Domain: [[sales-ar]]
- [[Returns]] — the goods-return documents being approved or cancelled
- [[ApprovalTemplates]] — approval templates applied to them
