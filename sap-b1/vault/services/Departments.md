---
entity: Departments
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 7
---
# Departments
Simple lookup of company departments (7 at JIVO) assigned to employees and users for HR/organizational grouping. Live rows in JIVO_OIL_HANADB: 7.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Departments --top 5
./sapb1 query Departments --count
./sapb1 query Departments --select "Code,Name,Description" --top 10
# find a department by name fragment
./sapb1 query Departments --filter "contains(Name,'Sales')" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Department key |
| Name | Department name |
| Description | Department description |
## Connections
- Domain: [[system-other-1]]
- [[EmployeesInfo]] via Department — employees assigned to the department
- [[Users]] via Department — users grouped by department
