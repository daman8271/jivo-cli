---
entity: UserQueries
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 568
---
# UserQueries
The 568 saved SQL user queries in the Query Manager — a rich trove of this company's reporting logic and table usage. Live rows in JIVO_OIL_HANADB: 568.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserQueries --top 5
./sapb1 query UserQueries --count
./sapb1 query UserQueries --select "InternalKey,QueryDescription,QueryCategory" --top 10
# Every saved query that reads A/R invoices (OINV) — mine the company's reporting logic:
./sapb1 query UserQueries --filter "contains(Query,'OINV')" --select "InternalKey,QueryDescription" --top 30
```

## Key fields
| Field | Meaning |
|---|---|
| InternalKey | Query numeric id (key) |
| QueryDescription | Query display name |
| Query | The saved SQL text |
| QueryCategory | Owning category code |
| QueryType | Query type flag |
| MenuCaption | Menu entry caption |
| MenuUniqueID | Menu unique id |
| ParentMenuID | Parent menu node |
| EnableMenuEntry | Shown in menu yes/no |
| ProcedureName | Backing stored procedure |
| ProcedureAlias | Procedure alias |
| MenuPosition | Position in menu |

## Connections
- Domain: [[administration-setup-3]]
- [[QueryCategories]] via QueryCategory → Code
- [[QueryAuthGroups]] via the category's permission groups
