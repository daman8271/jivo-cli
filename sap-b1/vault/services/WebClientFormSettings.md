---
entity: WebClientFormSettings
domain: administration-setup-4
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WebClientFormSettings
Stores per-user form layout/personalization settings for the SAP B1 Web Client (empty in JIVO_OIL_HANADB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientFormSettings --top 5
./sapb1 query WebClientFormSettings --count
./sapb1 query WebClientFormSettings --select "UserId,ObjectName" --top 10
# Settings saved by one specific user (once the Web Client is in use):
./sapb1 query WebClientFormSettings --filter "UserId eq 1"
```

## Key fields
| Field | Meaning |
|---|---|
| — | Table empty in JIVO_OIL_HANADB; no field sample available (Web Client not personalized here) |

## Connections
- Domain: [[administration-setup-4]]
- [[Users]] via UserId — the user whose Web Client form settings these are
