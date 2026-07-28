---
entity: ApprovalStages
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 26
---
# ApprovalStages
Defines the stages of approval workflows — who the approvers are and how many approvals each stage requires. Live rows in JIVO_OIL_HANADB: 26.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ApprovalStages --top 5
./sapb1 query ApprovalStages --count
./sapb1 query ApprovalStages --select "Code,Name,NoOfApproversRequired" --top 10
# Stages that need more than one approver:
./sapb1 query ApprovalStages --filter "NoOfApproversRequired gt 1" --top 10
```
The catalog also exposes POST action ops (`GetApprovalStage`, `RemoveApprovalStage`) — out of scope under our read-only rule.

## Key fields
| Field | Meaning |
|---|---|
| Code | Stage numeric key |
| Name | Stage display name |
| NoOfApproversRequired | Approvals needed to pass |
| Remarks | Free-text stage remarks |
| ApprovalStageApprovers | Approver users collection |

## Connections
- Domain: [[administration-setup-3]]
- [[ApprovalTemplates]] via ApprovalTemplateStages.ApprovalStageCode — templates that chain this stage
- [[Users]] via ApprovalStageApprovers.UserID — the approver users per stage
