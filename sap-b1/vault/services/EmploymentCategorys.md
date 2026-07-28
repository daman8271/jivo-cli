---
entity: EmploymentCategorys
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# EmploymentCategorys
HR lookup of employment categories (e.g. full-time, contract) assigned to employee master records. Live rows in JIVO_OIL_HANADB: 0 — the HR module's category list is unused here.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query EmploymentCategorys --top 5
./sapb1 query EmploymentCategorys --count
./sapb1 query EmploymentCategorys --select "AbsEntry,Name" --top 10
# Find a specific category by name (if any get defined):
./sapb1 query EmploymentCategorys --filter "contains(Name,'Contract')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Category numeric key |
| Name | Category display name |

## Connections
- Domain: [[system-other-1]]
- [[EmployeesInfo]] via EmploymentCategory — employee master records point at a category's AbsEntry
