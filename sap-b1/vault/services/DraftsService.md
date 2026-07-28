---
entity: DraftsService
domain: sales-ar
readable: false
methods: ["DraftsService_GetApprovalTemplates", "DraftsService_HandleApprovalRequest", "DraftsService_SaveDraftToDocument"]
rows_oil: null
---
# DraftsService
RPC helper to run approvals on document drafts and convert a draft into a posted document.
## Operations
- DraftsService_GetApprovalTemplates
- DraftsService_HandleApprovalRequest
- DraftsService_SaveDraftToDocument

Function service, not an entity set — entity sets are the read path in the CLI (read the drafts via [[Drafts]]). Browse this service's operations with `./sapb1 ops DraftsService`.
## Connections
- Domain: [[sales-ar]]
- [[Drafts]] — the draft documents being approved or posted
- [[Orders]] — a target document type a sales-order draft posts into
- [[Invoices]] — a target document type an invoice draft posts into
- [[ApprovalTemplates]] — approval templates applied to drafts
