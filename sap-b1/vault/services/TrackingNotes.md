---
entity: TrackingNotes
domain: system-other-2
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# TrackingNotes
Intrastat tracking notes for EU cross-border goods movement reporting; not applicable to this Indian company, empty. Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query TrackingNotes --top 5
./sapb1 query TrackingNotes --count
```
## Key fields
| Field | Meaning |
|---|---|
| — | Empty set; no fields sampled |
## Connections
- Domain: [[system-other-2]]
- [[Items]] via ItemCode on tracking-note lines
- [[BinLocations]] via bin allocation (AbsEntry)
