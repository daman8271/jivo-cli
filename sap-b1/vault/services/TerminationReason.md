---
entity: TerminationReason
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# TerminationReason
HR lookup of employment termination reasons attached to employee records; empty. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TerminationReason --top 5
./sapb1 query TerminationReason --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[EmployeesInfo]] via TerminationReason field on the employee record
