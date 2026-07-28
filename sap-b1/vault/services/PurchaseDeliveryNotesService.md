---
entity: PurchaseDeliveryNotesService
domain: purchasing
readable: false
methods: ["PurchaseDeliveryNotesService_GetApprovalTemplates", "PurchaseDeliveryNotesService_HandleApprovalRequest", "PurchaseDeliveryNotesService_Cancel2"]
rows_oil: null
---
# PurchaseDeliveryNotesService
RPC helper for goods-receipt-PO (purchase delivery note) approvals and cancellation.
## Operations
- PurchaseDeliveryNotesService_GetApprovalTemplates
- PurchaseDeliveryNotesService_HandleApprovalRequest
- PurchaseDeliveryNotesService_Cancel2

Entity sets are the read path in the CLI — read goods receipt rows through the [[PurchaseDeliveryNotes]] entity set (`./sapb1 query PurchaseDeliveryNotes`); browse this service's ops with `./sapb1 ops PurchaseDeliveryNotesService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseDeliveryNotes]] — the entity set whose documents this service approves/cancels
- [[ApprovalTemplates]] — approval templates fetched for the workflow
