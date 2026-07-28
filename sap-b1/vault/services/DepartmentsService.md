---
entity: DepartmentsService
domain: administration-setup-1
readable: false
methods: [DepartmentsService_GetDepartmentList]
rows_oil: null
---
# DepartmentsService
Lists company departments used to classify employees and users.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Departments]] — the department records this RPC lists (Code)
- [[EmployeesInfo]] — employees are assigned a department (Department)
- [[Users]] — users carry a department classification (Department)
