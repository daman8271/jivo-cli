---
entity: EmployeeTransfersService
domain: hr-resources
readable: false
methods: [EmployeeTransfersService_GetEmployeeTransferList]
rows_oil: null
---
# EmployeeTransfersService
RPC helper that returns the list of employee transfer records (department/branch/position moves).

## Operations
- `EmployeeTransfersService_GetEmployeeTransferList`

Function services are not directly queryable in the CLI — entity sets are the read path. Browse this service's operations with `./sapb1 ops EmployeeTransfersService`; read the same data via the [[EmployeeTransfers]] entity set.

## Connections
- Domain: [[hr-resources]]
- [[EmployeeTransfers]] — the entity set whose rows this helper lists
