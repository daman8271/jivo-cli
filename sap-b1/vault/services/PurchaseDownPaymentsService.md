---
entity: PurchaseDownPaymentsService
domain: banking-payments
readable: false
methods: ["PurchaseDownPaymentsService_GetApprovalTemplates", "PurchaseDownPaymentsService_HandleApprovalRequest"]
rows_oil: null
---
# PurchaseDownPaymentsService
RPC service handling approval-workflow templates and requests for purchase (A/P) down-payment invoices.
## Operations
- `PurchaseDownPaymentsService_GetApprovalTemplates`
- `PurchaseDownPaymentsService_HandleApprovalRequest` — WRITE (approves/rejects), out of scope under the standing READ-ONLY rule

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. The read path in the CLI is the entity sets: query [[PurchaseDownPayments]] for the documents and [[ApprovalTemplates]] / [[ApprovalRequests]] for the workflow state. Browse this service's operations with `./sapb1 ops PurchaseDownPaymentsService`.
## Connections
- Domain: [[banking-payments]]
- [[PurchaseDownPayments]] — A/P down-payment invoices under approval
- [[ApprovalTemplates]] — approval-stage definitions this service resolves
- [[ApprovalRequests]] — pending approval requests it handles
