---
entity: EmployeeIDTypeService
domain: hr-resources
readable: false
methods: [EmployeeIDTypeService_GetList]
rows_oil: null
---
# EmployeeIDTypeService
RPC helper that returns the list of employee ID-document types (e.g. passport, PAN) defined in the system.

## Operations
- `EmployeeIDTypeService_GetList`

Function services are not directly queryable in the CLI — entity sets are the read path. Browse this service's operations with `./sapb1 ops EmployeeIDTypeService`; read the same data via the [[EmployeeIDType]] entity set.

## Connections
- Domain: [[hr-resources]]
- [[EmployeeIDType]] — the entity set whose rows this helper lists
