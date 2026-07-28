---
entity: ActivityStatuses
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 2
---
# ActivityStatuses
Lookup of activity status values (e.g. Open/Closed) applied to CRM activities. Live rows in JIVO_OIL_HANADB: 2.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ActivityStatuses --top 5
./sapb1 query ActivityStatuses --count
./sapb1 query ActivityStatuses --select "StatusId,StatusName,StatusDescription" --top 10
# Look up one status by its name:
./sapb1 query ActivityStatuses --filter "StatusName eq 'Open'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| StatusId | Status numeric id (key) |
| StatusName | Short status name |
| StatusDescription | Longer status description |

## Connections
- Domain: [[business-partners-crm]]
- [[Activities]] via Status
