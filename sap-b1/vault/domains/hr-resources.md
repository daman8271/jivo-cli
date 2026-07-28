# HR & Employees

The HR mini-module: [[EmployeesInfo]] is the employee master (17 employees with department, branch, position, bank and role assignments), supported by setup tables [[EmployeePosition]], [[EmployeeStatus]], [[EmployeeRolesSetup]], [[EmployeeIDType]] and movement history in [[EmployeeTransfers]]. Employees link to [[SalesPersons]], [[Departments]], [[Branches]] and [[Users]] across other domains. The five RPC services mirror the setup tables for writes.

Part of the [[00-SAP-B1-Atlas]] — 11 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[EmployeesInfo]] **(17 rows)** — The HR employee master data (OHEM): 17 employees with personal, org-assignment (department/branch/position), bank, cost and role details.
- [[EmployeeRolesSetup]] **(3 rows)** — Setup catalog of employee roles (e.g. sales employee, purchasing, technician) referenced by EmployeeRolesInfoLines on employee records; 3 roles defined.
- [[EmployeePosition]] **(1 row)** — Setup catalog of job positions/titles assignable to employees; only 1 position defined.
- [[EmployeeIDType]] — Setup catalog of identification-document types that can be recorded on an employee master record; empty in JIVO_OIL_HANADB.
- [[EmployeeStatus]] — Setup catalog of employment statuses (active, on leave, terminated) usable on employee records; empty in this company DB.
- [[EmployeeTransfers]] — Log of employee transfers between departments, branches, or positions; no transfer records exist in JIVO_OIL_HANADB.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[EmployeeIDTypeService]] — RPC helper that returns the list of employee ID-document types (e.g. passport, PAN) defined in the system.
- [[EmployeePositionService]] — RPC helper that returns the list of job positions defined for HR master data.
- [[EmployeeRolesSetupService]] — RPC helper that returns the configured employee roles (e.g. sales employee, technician) used to tag employees.
- [[EmployeeStatusService]] — RPC helper that returns the list of employment statuses (active, terminated, on leave) defined in setup.
- [[EmployeeTransfersService]] — RPC helper that returns the list of employee transfer records (department/branch/position moves).
