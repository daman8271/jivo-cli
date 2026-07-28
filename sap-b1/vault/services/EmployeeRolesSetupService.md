---
entity: EmployeeRolesSetupService
domain: hr-resources
readable: false
methods: [EmployeeRolesSetupService_GetEmployeeRoleSetupList]
rows_oil: null
---
# EmployeeRolesSetupService
RPC helper that returns the configured employee roles (e.g. sales employee, technician) used to tag employees.

## Operations
- `EmployeeRolesSetupService_GetEmployeeRoleSetupList`

Function services are not directly queryable in the CLI — entity sets are the read path. Browse this service's operations with `./sapb1 ops EmployeeRolesSetupService`; read the same data via the [[EmployeeRolesSetup]] entity set.

## Connections
- Domain: [[hr-resources]]
- [[EmployeeRolesSetup]] — the entity set whose rows this helper lists
