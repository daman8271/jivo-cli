---
entity: EmployeePosition
domain: hr-resources
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# EmployeePosition
Setup catalog of job positions/titles assignable to employees; only 1 position defined. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmployeePosition --top 5
./sapb1 query EmployeePosition --count
./sapb1 query EmployeePosition --select "PositionID,Name,Description" --top 10
# look up a position by its internal ID
./sapb1 query EmployeePosition --filter "PositionID eq 1"
```

## Key fields
| Field | Meaning |
|---|---|
| PositionID | Internal position key |
| Name | Position/title name |
| Description | Longer position description |

## Connections
- Domain: [[hr-resources]]
- [[EmployeesInfo]] via Position — employees assigned this job position
