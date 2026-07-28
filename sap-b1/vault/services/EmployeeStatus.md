---
entity: EmployeeStatus
domain: hr-resources
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# EmployeeStatus
Setup catalog of employment statuses (active, on leave, terminated) usable on employee records; empty in this company DB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmployeeStatus --top 5
./sapb1 query EmployeeStatus --count
./sapb1 query EmployeeStatus --select "StatusID,Name,Description" --top 10
# find a status by name once any are defined
./sapb1 query EmployeeStatus --filter "Name eq 'Active'"
```

## Key fields
| Field | Meaning |
|---|---|
| StatusID | Internal status key |
| Name | Status name |
| Description | Longer status description |

## Connections
- Domain: [[hr-resources]]
- [[EmployeesInfo]] via StatusOfEmployee — employee records carry this status
