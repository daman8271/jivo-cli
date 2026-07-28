---
entity: BrazilBeverageIndexers
domain: system-other-1
readable: true
methods: [GET, POST, DELETE]
rows_oil: 0
---
# BrazilBeverageIndexers
Brazil-localization lookup of beverage tax indexer codes for fiscal reporting; irrelevant to Indian localization (empty). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BrazilBeverageIndexers --top 5
./sapb1 query BrazilBeverageIndexers --count
./sapb1 query BrazilBeverageIndexers --select "AbsEntry,Code,Name" --top 10
# look up an indexer by its code
./sapb1 query BrazilBeverageIndexers --filter "Code eq '01'" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal record key |
| Code | Beverage indexer code |
| Name | Indexer description |
## Connections
- Domain: [[system-other-1]]
- [[Items]] via Brazil fiscal beverage fields — indexer referenced on item master
