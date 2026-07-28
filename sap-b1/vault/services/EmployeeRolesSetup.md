---
entity: EmployeeRolesSetup
domain: hr-resources
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# EmployeeRolesSetup
Setup catalog of employee roles (e.g. sales employee, purchasing, technician) referenced by EmployeeRolesInfoLines on employee records; 3 roles defined. Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmployeeRolesSetup --top 5
./sapb1 query EmployeeRolesSetup --count
./sapb1 query EmployeeRolesSetup --select "TypeID,Name,Description" --top 10
# find a role by name
./sapb1 query EmployeeRolesSetup --filter "Name eq 'Sales Employee'"
```

## Key fields
| Field | Meaning |
|---|---|
| TypeID | Internal role type key |
| Name | Role name |
| Description | Longer role description |

## Connections
- Domain: [[hr-resources]]
- [[EmployeesInfo]] via EmployeeRolesInfoLines.RoleID — employees tagged with this role
- [[SalesPersons]] via role usage — sales-employee role links HR records to sales employees
