---
entity: WebClientNotifications
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# WebClientNotifications
In-app notifications shown to users in the Web Client notification center; empty. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query WebClientNotifications --top 5
./sapb1 query WebClientNotifications --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[Users]] via UserId (notification recipient)
