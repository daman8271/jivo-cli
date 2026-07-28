---
entity: TargetGroupsService
domain: administration-setup-2
readable: false
methods: ["TargetGroupsService_GetList"]
rows_oil: null
---
# TargetGroupsService
Returns the list of CRM campaign target groups defined in the system.

## Operations
- TargetGroupsService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI; for the actual target-group rows read [[TargetGroups]] instead. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops TargetGroupsService
```

## Connections
- Domain: [[administration-setup-2]]
- [[TargetGroups]] — the entity set holding the target-group rows this service lists
