---
entity: Teams
domain: system-other-2
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# Teams
HR master of employee teams for grouping employees; not used in this database. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Teams --top 5
./sapb1 query Teams --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[EmployeesInfo]] via EmployeeRolesInTeam (TeamID)
