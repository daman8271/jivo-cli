---
entity: PurchaseCreditNotesService
domain: purchasing
readable: false
methods: ["PurchaseCreditNotesService_GetApprovalTemplates", "PurchaseCreditNotesService_HandleApprovalRequest", "PurchaseCreditNotesService_Cancel2"]
rows_oil: null
---
# PurchaseCreditNotesService
RPC helper for A/P credit note approvals and alternate cancellation.
## Operations
- PurchaseCreditNotesService_GetApprovalTemplates
- PurchaseCreditNotesService_HandleApprovalRequest
- PurchaseCreditNotesService_Cancel2

Entity sets are the read path in the CLI — read credit note rows through the [[PurchaseCreditNotes]] entity set (`./sapb1 query PurchaseCreditNotes`); browse this service's ops with `./sapb1 ops PurchaseCreditNotesService`.
## Connections
- Domain: [[purchasing]]
- [[PurchaseCreditNotes]] — the entity set whose documents this service approves/cancels
- [[ApprovalTemplates]] — approval templates fetched for the workflow
