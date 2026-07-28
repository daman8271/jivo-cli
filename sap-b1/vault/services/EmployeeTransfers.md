---
entity: EmployeeTransfers
domain: hr-resources
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# EmployeeTransfers
Log of employee transfers between departments, branches, or positions; no transfer records exist in JIVO_OIL_HANADB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmployeeTransfers --top 5
./sapb1 query EmployeeTransfers --count
./sapb1 query EmployeeTransfers --select "AbsEntry,EmployeeID,TransferDate,ToDepartment" --top 10
# transfer history for one employee, once records exist
./sapb1 query EmployeeTransfers --filter "EmployeeID eq 1"
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal transfer entry key |
| EmployeeID | Employee being transferred |
| TransferDate | Date of the transfer |
| FromDepartment | Department before transfer |
| ToDepartment | Department after transfer |
| FromBranch | Branch before transfer |
| ToBranch | Branch after transfer |
| FromPosition | Position before transfer |
| ToPosition | Position after transfer |

## Connections
- Domain: [[hr-resources]]
- [[EmployeesInfo]] via EmployeeID — the employee the transfer belongs to
- [[Departments]] via FromDepartment/ToDepartment — source and target departments
- [[EmployeePosition]] via FromPosition/ToPosition — source and target positions
