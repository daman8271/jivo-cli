---
entity: TSRExceptionalEventService
domain: administration-setup-2
readable: false
methods: ["TSRExceptionalEventService_GetList"]
rows_oil: null
---
# TSRExceptionalEventService
Returns exceptional events (holidays/absence exceptions) for time sheet recording (TSR).

## Operations
- TSRExceptionalEventService_GetList

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops TSRExceptionalEventService
```

## Connections
- Domain: [[administration-setup-2]]
- [[EmployeesInfo]] — employees whose time sheets these exceptional events apply to
