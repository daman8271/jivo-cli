---
entity: BrazilMultiIndexers
domain: system-other-1
readable: true
methods: [GET, POST, DELETE]
rows_oil: 0
---
# BrazilMultiIndexers
Brazil-localization multi-value tax indexer assignments for items; irrelevant to this Indian DB (empty). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BrazilMultiIndexers --top 5
./sapb1 query BrazilMultiIndexers --count
./sapb1 query BrazilMultiIndexers --select "AbsEntry,Indexer,TypeCode" --top 10
# assignments for one indexer type
./sapb1 query BrazilMultiIndexers --filter "TypeCode eq 1" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal record key |
| Indexer | Assigned indexer value |
| TypeCode | Indexer type code |
## Connections
- Domain: [[system-other-1]]
- [[Items]] via Brazil fiscal indexer assignments — multi-value indexers on items
