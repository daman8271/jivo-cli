---
entity: BrazilNumericIndexers
domain: system-other-1
readable: true
methods: [GET, POST, DELETE]
rows_oil: 0
---
# BrazilNumericIndexers
Brazil-localization numeric tax indexer values used in fiscal calculations; irrelevant here (empty). Live rows in JIVO_OIL_HANADB: 0.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BrazilNumericIndexers --top 5
./sapb1 query BrazilNumericIndexers --count
./sapb1 query BrazilNumericIndexers --select "AbsEntry,Value,TypeCode" --top 10
# values for one indexer type
./sapb1 query BrazilNumericIndexers --filter "TypeCode eq 1" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal record key |
| Value | Numeric indexer value |
| TypeCode | Indexer type code |
## Connections
- Domain: [[system-other-1]]
- [[Items]] via Brazil fiscal indexer values — numeric indexers used by items
