---
entity: UserDefaultGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# UserDefaultGroups
Reusable default-value profiles (default warehouse, BP, printing settings) assignable to users; none defined here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserDefaultGroups --top 5
./sapb1 query UserDefaultGroups --count
./sapb1 query UserDefaultGroups --select "Code,Name,Warehouse" --top 10
# Profiles that default to a given warehouse (if ever populated):
./sapb1 query UserDefaultGroups --filter "Warehouse eq '01'" --top 10
```
Set is empty here — confirm live field names with `./sapb1 fields UserDefaultGroups` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| Code | Defaults profile code (key) |
| Name | Profile display name |
| Warehouse | Default warehouse code |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[Users]] via defaults-group assignment on the user record
- [[Warehouses]] via default warehouse code
- [[BusinessPartners]] via default customer/vendor codes
