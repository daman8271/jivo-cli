---
entity: TerminationReasonService
domain: administration-setup-2
readable: false
methods: ["TerminationReasonService_GetList"]
rows_oil: null
---
# TerminationReasonService
Returns the list of employee termination reasons used in HR master data.

## Operations
- TerminationReasonService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI; for the actual termination-reason rows read [[TerminationReason]] instead. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops TerminationReasonService
```

## Connections
- Domain: [[administration-setup-2]]
- [[TerminationReason]] — the entity set holding the termination-reason rows this service lists
- [[EmployeesInfo]] — employee master records that reference a termination reason on exit
