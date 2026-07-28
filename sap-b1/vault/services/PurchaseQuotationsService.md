---
entity: PurchaseQuotationsService
domain: purchasing
readable: false
methods: ["PurchaseQuotationsService_GetApprovalTemplates", "PurchaseQuotationsService_HandleApprovalRequest"]
rows_oil: null
---
# PurchaseQuotationsService
RPC helper for purchase quotation approval workflow.
## Operations
- PurchaseQuotationsService_GetApprovalTemplates
- PurchaseQuotationsService_HandleApprovalRequest

Entity sets are the read path in the CLI — read quotation rows through the [[PurchaseQuotations]] entity set (`./sapb1 query PurchaseQuotations`); browse this service's ops with `./sapb1 ops PurchaseQuotationsService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseQuotations]] — the entity set whose documents this service approves
- [[ApprovalTemplates]] — approval templates fetched for the workflow
