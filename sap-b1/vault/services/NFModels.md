---
entity: NFModels
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# NFModels
Brazil localization Nota Fiscal model codes for fiscal document types. Live rows in JIVO_OIL_HANADB: 0 — unused in this India database.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query NFModels --top 5
./sapb1 query NFModels --count
./sapb1 query NFModels --select "AbsEntry,Code,Description" --top 10
# Look up the NF-e electronic invoice model (would be Code 55, if this were a Brazil DB):
./sapb1 query NFModels --filter "Code eq '55'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Model record key |
| Code | Nota Fiscal model code |
| Description | Model description text |

## Connections
- Domain: [[system-other-1]]
