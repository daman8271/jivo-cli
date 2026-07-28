---
entity: GoodsReturnRequestService
domain: purchasing
readable: false
methods: ["GoodsReturnRequestService_GetApprovalTemplates", "GoodsReturnRequestService_Preview", "GoodsReturnRequestService_HandleApprovalRequest"]
rows_oil: null
---
# GoodsReturnRequestService
RPC helper for goods-return-request approvals and journal preview before posting.
## Operations
- GoodsReturnRequestService_GetApprovalTemplates
- GoodsReturnRequestService_Preview
- GoodsReturnRequestService_HandleApprovalRequest

Entity sets are the read path in the CLI — read return-request rows through the [[GoodsReturnRequest]] entity set (`./sapb1 query GoodsReturnRequest`); browse this service's ops with `./sapb1 ops GoodsReturnRequestService`.
## Connections
- Domain: [[purchasing]]
- [[GoodsReturnRequest]] — the entity set whose documents this service approves/previews
- [[ApprovalTemplates]] — approval templates fetched for the workflow
