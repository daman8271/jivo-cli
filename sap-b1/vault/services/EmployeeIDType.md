---
entity: EmployeeIDType
domain: hr-resources
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# EmployeeIDType
Setup catalog of identification-document types that can be recorded on an employee master record; empty in JIVO_OIL_HANADB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmployeeIDType --top 5
./sapb1 query EmployeeIDType --count
./sapb1 query EmployeeIDType --select "AbsEntry,Name,Description" --top 10
# find a specific document type once any are defined
./sapb1 query EmployeeIDType --filter "Name eq 'Passport'"
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal entry key |
| Name | ID-document type name |
| Description | Longer type description |

## Connections
- Domain: [[hr-resources]]
- [[EmployeesInfo]] via EmployeeIDInfoLines.IDType — employee ID documents reference this type
