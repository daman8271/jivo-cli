---
entity: AccountSegmentations
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# AccountSegmentations
Defines the segment structure (name/size) of a segmented G/L account code (unused in this DB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AccountSegmentations --top 5
./sapb1 query AccountSegmentations --count
./sapb1 fields AccountSegmentations   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query AccountSegmentations --filter "Name ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields AccountSegmentations` |

## Connections
- Domain: [[financials-accounting-1]]
- [[AccountSegmentationCategories]] via segment number — each segment position carries its own value list
- [[ChartOfAccounts]] via account Code structure — segments define how segmented G/L codes are composed
