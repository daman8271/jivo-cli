---
entity: QueryAuthGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 23
---
# QueryAuthGroups
Authorization groups that control which users may run which saved user-query categories. Live rows in JIVO_OIL_HANADB: 23.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query QueryAuthGroups --top 5
./sapb1 query QueryAuthGroups --count
./sapb1 query QueryAuthGroups --select "AuthGroupId,AuthGroupCode,AuthGroupDes" --top 10
# Find an auth group by (partial) description:
./sapb1 query QueryAuthGroups --filter "contains(AuthGroupDes,'Admin')" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AuthGroupId | Group numeric id (key) |
| AuthGroupCode | Group short code |
| AuthGroupDes | Group description |
| CategoryGroupCollection | Query categories this group can run |

## Connections
- Domain: [[administration-setup-3]]
- [[QueryCategories]] via CategoryGroupCollection → category Code
- [[Users]] via query-group assignment on the user record
