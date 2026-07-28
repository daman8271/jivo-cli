---
entity: WebClientListviewFilters
domain: administration-setup-4
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WebClientListviewFilters
Stores saved list-view filter definitions users create in the SAP B1 Web Client (empty in JIVO_OIL_HANADB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientListviewFilters --top 5
./sapb1 query WebClientListviewFilters --count
./sapb1 query WebClientListviewFilters --select "UserId,ObjectName" --top 10
# Saved filters belonging to one specific user (once the Web Client is in use):
./sapb1 query WebClientListviewFilters --filter "UserId eq 1"
```

## Key fields
| Field | Meaning |
|---|---|
| — | Table empty in JIVO_OIL_HANADB; no field sample available (no Web Client list-view filters saved) |

## Connections
- Domain: [[administration-setup-4]]
- [[Users]] via UserId — the user who saved the list-view filter
