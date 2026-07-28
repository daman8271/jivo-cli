---
entity: DeliveryNotesService
domain: sales-ar
readable: false
methods: ["DeliveryNotesService_GetApprovalTemplates", "DeliveryNotesService_HandleApprovalRequest", "DeliveryNotesService_Cancel2"]
rows_oil: null
---
# DeliveryNotesService
Approval and cancellation RPC helper for sales delivery notes.
## Operations
- DeliveryNotesService_GetApprovalTemplates
- DeliveryNotesService_HandleApprovalRequest
- DeliveryNotesService_Cancel2

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[DeliveryNotes]]). Browse this service's operations with `./sapb1 ops DeliveryNotesService`.
## Connections
- Domain: [[sales-ar]]
- [[DeliveryNotes]] — the delivery documents being approved or cancelled
- [[ApprovalTemplates]] — approval templates applied to them
