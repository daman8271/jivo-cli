---
entity: ApprovalTemplatesService
domain: administration-setup-1
readable: false
methods: [ApprovalTemplatesService_GetApprovalTemplateList]
rows_oil: null
---
# ApprovalTemplatesService
Lists approval templates that define which documents and originators trigger approval workflows.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[ApprovalTemplates]] — the template records this RPC lists (Code)
- [[ApprovalStages]] — each template chains one or more approval stages
- [[Users]] — originators covered by the template and approvers it routes to (UserID)
