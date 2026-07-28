---
entity: BrazilStringIndexers
domain: system-other-1
readable: true
methods: [GET, POST, DELETE]
rows_oil: 0
---
# BrazilStringIndexers
Brazil-localization string tax indexer values for fiscal documents; irrelevant here (empty). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BrazilStringIndexers --top 5
./sapb1 query BrazilStringIndexers --count
./sapb1 query BrazilStringIndexers --select "AbsEntry,Value,TypeCode" --top 10
# values for one indexer type
./sapb1 query BrazilStringIndexers --filter "TypeCode eq 1" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal record key |
| Value | String indexer value |
| TypeCode | Indexer type code |
## Connections
- Domain: [[system-other-1]]
- [[Items]] via Brazil fiscal indexer values — string indexers used by items
