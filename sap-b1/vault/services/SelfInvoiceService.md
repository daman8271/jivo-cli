---
entity: SelfInvoiceService
domain: sales-ar
readable: false
methods: ["SelfInvoiceService_GetApprovalTemplates", "SelfInvoiceService_HandleApprovalRequest", "SelfInvoiceService_Cancel2"]
rows_oil: null
---
# SelfInvoiceService
Approval and cancellation RPC helper for self-invoice (localization-specific) documents.
## Operations
- SelfInvoiceService_GetApprovalTemplates
- SelfInvoiceService_HandleApprovalRequest
- SelfInvoiceService_Cancel2

Function service, not an entity set — entity sets are the read path in the CLI. Browse this service's operations with `./sapb1 ops SelfInvoiceService`.
## Connections
- Domain: [[sales-ar]]
- [[Invoices]] — the closest readable A/R invoice documents in the same family
- [[ApprovalTemplates]] — approval templates applied to self-invoices
