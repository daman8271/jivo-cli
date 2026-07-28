---
entity: ActivityTypes
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# ActivityTypes
Lookup of user-defined activity type categories (call, meeting, task subtypes). Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ActivityTypes --top 5
./sapb1 query ActivityTypes --count
./sapb1 query ActivityTypes --select "Code,Name" --top 10
# Find a type category by name fragment:
./sapb1 query ActivityTypes --filter "contains(Name,'Call')" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Type numeric code (key) |
| Name | Type display name |

## Connections
- Domain: [[business-partners-crm]]
- [[Activities]] via ActivityType
