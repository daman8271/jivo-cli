---
entity: BinLocationAttributes
domain: inventory-warehouse-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# BinLocationAttributes
Defines attribute codes that can be tagged onto warehouse bin locations for classification (empty — bin management not used in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BinLocationAttributes --top 5
./sapb1 query BinLocationAttributes --count
./sapb1 query BinLocationAttributes --select "AbsEntry,Code,Description" --top 10
# Look up one attribute by its code (if any are ever defined):
./sapb1 query BinLocationAttributes --filter "Code eq 'ZONE'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| Code | Attribute code |
| Description | Attribute description text |

## Connections
- Domain: [[inventory-warehouse-1]]
- [[BinLocations]] via the Attribute slots on each bin record
