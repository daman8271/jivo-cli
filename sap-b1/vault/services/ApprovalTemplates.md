---
entity: ApprovalTemplates
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 93
---
# ApprovalTemplates
Templates that wire together documents, originating users, stages, and trigger conditions to define when and how approval workflows fire. Live rows in JIVO_OIL_HANADB: 93.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ApprovalTemplates --top 5
./sapb1 query ApprovalTemplates --count
./sapb1 query ApprovalTemplates --select "Code,Name,IsActive,UseTerms" --top 10
# Only the templates that actually fire today:
./sapb1 query ApprovalTemplates --filter "IsActive eq 'tYES'" --top 10
```
The catalog also exposes POST action ops (`GetApprovalTemplate`, `RemoveApprovalTemplate`) — out of scope under our read-only rule.

## Key fields
| Field | Meaning |
|---|---|
| Code | Template numeric key |
| Name | Template display name |
| IsActive | Template enabled flag |
| IsActiveWhenUpdatingDocuments | Fires on document updates |
| UseTerms | Conditional-terms trigger enabled |
| Remarks | Free-text template remarks |
| ApprovalTemplateDocuments | Covered document types collection |
| ApprovalTemplateStages | Ordered stages collection |
| ApprovalTemplateUsers | Originating users collection |
| ApprovalTemplateTerms | Trigger condition terms |
| ApprovalTemplateQueries | Trigger user-query conditions |

## Connections
- Domain: [[administration-setup-3]]
- [[ApprovalStages]] via ApprovalTemplateStages.ApprovalStageCode — stages chained by this template
- [[Users]] via ApprovalTemplateUsers.UserID — originators whose documents trigger it
