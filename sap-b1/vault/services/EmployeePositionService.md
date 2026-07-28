---
entity: EmployeePositionService
domain: hr-resources
readable: false
methods: [EmployeePositionService_GetList]
rows_oil: null
---
# EmployeePositionService
RPC helper that returns the list of job positions defined for HR master data.

## Operations
- `EmployeePositionService_GetList`

Function services are not directly queryable in the CLI — entity sets are the read path. Browse this service's operations with `./sapb1 ops EmployeePositionService`; read the same data via the [[EmployeePosition]] entity set.

## Connections
- Domain: [[hr-resources]]
- [[EmployeePosition]] — the entity set whose rows this helper lists
