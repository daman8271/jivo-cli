---
entity: ReturnRequestService
domain: sales-ar
readable: false
methods: ["ReturnRequestService_GetApprovalTemplates", "ReturnRequestService_Preview", "ReturnRequestService_HandleApprovalRequest"]
rows_oil: null
---
# ReturnRequestService
Approval-workflow and preview RPC helper for customer return requests.
## Operations
- ReturnRequestService_GetApprovalTemplates
- ReturnRequestService_Preview
- ReturnRequestService_HandleApprovalRequest

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[ReturnRequest]]). Browse this service's operations with `./sapb1 ops ReturnRequestService`.
## Connections
- Domain: [[sales-ar]]
- [[ReturnRequest]] — the return-request documents being previewed or approved
- [[Returns]] — the goods-return documents a request becomes downstream
- [[ApprovalTemplates]] — approval templates applied to them
