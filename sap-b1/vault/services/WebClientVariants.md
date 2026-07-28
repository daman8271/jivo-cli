---
entity: WebClientVariants
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 320
---
# WebClientVariants
Saved list-view/filter/chart variants for Web Client screens (columns, sorts, filters per user or system) — 320 variants. Live rows in JIVO_OIL_HANADB: 320.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientVariants --top 5
./sapb1 query WebClientVariants --count
./sapb1 query WebClientVariants --select "Guid,Name,ObjectName,UserId" --top 10
./sapb1 query WebClientVariants --filter "IsSystem eq 'tNO'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| Guid | Variant unique identifier (key) |
| Name | Variant display name |
| ObjectName | Screen/object it applies to |
| UserId | Owning SAP user |
| ViewId | View identifier |
| ViewType | View type (list/analytics) |
| SubViewType | Sub-view type |
| IsPublic | Shared with all users |
| IsSystem | System-delivered variant |
| Order | Display order |
| Version | Variant schema version |
| UserFilter | User-defined filter definition |
| SystemFilter | System filter definition |
| ConditionFilter | Condition filter definition |
## Connections
- Domain: [[system-other-2]]
- [[Users]] via UserId
