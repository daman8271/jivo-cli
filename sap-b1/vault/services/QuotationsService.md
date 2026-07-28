---
entity: QuotationsService
domain: sales-ar
readable: false
methods: ["QuotationsService_GetApprovalTemplates", "QuotationsService_HandleApprovalRequest"]
rows_oil: null
---
# QuotationsService
Approval-workflow RPC helper for sales quotations.
## Operations
- QuotationsService_GetApprovalTemplates
- QuotationsService_HandleApprovalRequest

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[Quotations]]). Browse this service's operations with `./sapb1 ops QuotationsService`.
## Connections
- Domain: [[sales-ar]]
- [[Quotations]] — the sales quotations the approvals run on
- [[ApprovalTemplates]] — approval templates applied to them
