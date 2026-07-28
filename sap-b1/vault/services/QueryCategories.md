---
entity: QueryCategories
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 37
---
# QueryCategories
Categories used to organize saved user queries and gate access to them via permission groups. Live rows in JIVO_OIL_HANADB: 37.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query QueryCategories --top 5
./sapb1 query QueryCategories --count
./sapb1 query QueryCategories --select "Code,Name,Permissions" --top 10
# Find a category by (partial) name, e.g. anything sales-related:
./sapb1 query QueryCategories --filter "contains(Name,'Sales')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Category numeric code (key) |
| Name | Category display name |
| Permissions | Auth-group permission mask |

## Connections
- Domain: [[administration-setup-3]]
- [[UserQueries]] via QueryCategory → Code
- [[QueryAuthGroups]] via Permissions / CategoryGroupCollection
