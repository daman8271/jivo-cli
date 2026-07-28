---
entity: ApprovalStagesService
domain: administration-setup-1
readable: false
methods: [ApprovalStagesService_GetApprovalStageList]
rows_oil: null
---
# ApprovalStagesService
Lists the defined approval stages (who must approve, how many approvers) used in approval templates.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[ApprovalStages]] — the stage definition records this RPC lists (Code)
- [[ApprovalTemplates]] — templates chain these stages into a workflow
- [[Users]] — the approvers assigned to each stage (UserID)
