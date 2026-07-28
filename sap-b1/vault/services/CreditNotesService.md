---
entity: CreditNotesService
domain: sales-ar
readable: false
methods: ["CreditNotesService_GetApprovalTemplates", "CreditNotesService_HandleApprovalRequest", "CreditNotesService_RequestApproveCancellation", "CreditNotesService_Cancel2"]
rows_oil: null
---
# CreditNotesService
Approval and cancellation RPC helper for A/R credit notes.
## Operations
- CreditNotesService_GetApprovalTemplates
- CreditNotesService_HandleApprovalRequest
- CreditNotesService_RequestApproveCancellation
- CreditNotesService_Cancel2

Function service, not an entity set — entity sets are the read path in the CLI (read the documents via [[CreditNotes]]). Browse this service's operations with `./sapb1 ops CreditNotesService`.
## Connections
- Domain: [[sales-ar]]
- [[CreditNotes]] — the credit memos being approved or cancelled
- [[ApprovalTemplates]] — approval templates applied to them
