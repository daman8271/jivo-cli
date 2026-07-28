---
entity: AccountSegmentationCategories
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# AccountSegmentationCategories
Value lists for each account-segment position when segmented chart of accounts is used (empty here — segmentation not in use). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AccountSegmentationCategories --top 5
./sapb1 query AccountSegmentationCategories --count
./sapb1 fields AccountSegmentationCategories   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query AccountSegmentationCategories --filter "Name ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields AccountSegmentationCategories` |

## Connections
- Domain: [[financials-accounting-1]]
- [[AccountSegmentations]] via segment number — each category value belongs to one defined segment position
- [[ChartOfAccounts]] via segmented account Code — categories compose the segments of segmented G/L codes
