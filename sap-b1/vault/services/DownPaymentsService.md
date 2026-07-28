---
entity: DownPaymentsService
domain: banking-payments
readable: false
methods: ["DownPaymentsService_GetApprovalTemplates", "DownPaymentsService_HandleApprovalRequest"]
rows_oil: null
---
# DownPaymentsService
RPC service handling approval-workflow templates and requests for sales (A/R) down-payment invoices.
## Operations
- `DownPaymentsService_GetApprovalTemplates`
- `DownPaymentsService_HandleApprovalRequest` — WRITE (approves/rejects), out of scope under the standing READ-ONLY rule

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity sets: query [[DownPayments]] for the documents and [[ApprovalTemplates]] / [[ApprovalRequests]] for the workflow state. Browse this service's operations with `./sapb1 ops DownPaymentsService`.
## Connections
- Domain: [[banking-payments]]
- [[DownPayments]] — A/R down-payment invoices under approval
- [[ApprovalTemplates]] — approval-stage definitions this service resolves
- [[ApprovalRequests]] — pending approval requests it handles
