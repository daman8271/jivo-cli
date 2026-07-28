---
entity: ActivityLocations
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH]
rows_oil: 1
---
# ActivityLocations
Lookup of meeting/activity locations selectable on CRM activities. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ActivityLocations --top 5
./sapb1 query ActivityLocations --count
./sapb1 query ActivityLocations --select "Code,Name" --top 10
# Look up a location by name fragment:
./sapb1 query ActivityLocations --filter "contains(Name,'Office')" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Location numeric code (key) |
| Name | Location display name |

## Connections
- Domain: [[business-partners-crm]]
- [[Activities]] via Location
