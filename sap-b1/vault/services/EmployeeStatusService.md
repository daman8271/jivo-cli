---
entity: EmployeeStatusService
domain: hr-resources
readable: false
methods: [EmployeeStatusService_GetList]
rows_oil: null
---
# EmployeeStatusService
RPC helper that returns the list of employment statuses (active, terminated, on leave) defined in setup.

## Operations
- `EmployeeStatusService_GetList`

Function services are not directly queryable in the CLI — entity sets are the read path. Browse this service's operations with `./sapb1 ops EmployeeStatusService`; read the same data via the [[EmployeeStatus]] entity set.

## Connections
- Domain: [[hr-resources]]
- [[EmployeeStatus]] — the entity set whose rows this helper lists
