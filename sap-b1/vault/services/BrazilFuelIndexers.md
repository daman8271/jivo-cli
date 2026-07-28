---
entity: BrazilFuelIndexers
domain: system-other-1
readable: true
methods: [GET, POST, DELETE]
rows_oil: 0
---
# BrazilFuelIndexers
Brazil-localization lookup of fuel tax indexer codes (ANP) for fiscal documents; irrelevant here (empty). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BrazilFuelIndexers --top 5
./sapb1 query BrazilFuelIndexers --count
./sapb1 query BrazilFuelIndexers --select "AbsEntry,Code,Name" --top 10
# look up an ANP fuel code
./sapb1 query BrazilFuelIndexers --filter "Code eq '320102001'" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal record key |
| Code | ANP fuel code |
| Name | Indexer description |
## Connections
- Domain: [[system-other-1]]
- [[Items]] via Brazil fiscal fuel fields — indexer referenced on item master
