---
entity: TSRExceptionalEvents
domain: system-other-2
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# TSRExceptionalEvents
Technical Security Report exceptional events log (fiscal/audit compliance, e.g. Portugal SAF-T); empty. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TSRExceptionalEvents --top 5
./sapb1 query TSRExceptionalEvents --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
