---
entity: WebClientPreferences
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WebClientPreferences
Per-user Web Client preference settings (formats, defaults); none stored. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientPreferences --top 5
./sapb1 query WebClientPreferences --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[Users]] via UserId (preference owner)
