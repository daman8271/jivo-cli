---
entity: ApprovalRequestsService
domain: administration-setup-1
readable: false
methods: [ApprovalRequestsService_GetApprovalRequestList, ApprovalRequestsService_GetOpenApprovalRequestList, ApprovalRequestsService_GetAllApprovalRequestsList]
rows_oil: null
---
# ApprovalRequestsService
Retrieves pending and historical document approval requests routed through SAP B1 approval workflows.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[ApprovalRequests]] — the approval request records these RPCs list (Code)
- [[ApprovalTemplates]] — the template that spawned each request (ApprovalTemplatesID)
- [[Users]] — originators and approvers on each request (UserID)
