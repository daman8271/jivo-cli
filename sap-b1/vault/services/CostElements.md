---
entity: CostElements
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CostElements
Cost accounting elements that map G/L expense accounts into cost-accounting analysis (unused here). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CostElements --top 5
./sapb1 query CostElements --count
./sapb1 fields CostElements   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query CostElements --filter "CostElementCode ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields CostElements` |

## Connections
- Domain: [[financials-accounting-1]]
- [[ChartOfAccounts]] via mapped account Code — cost elements group expense accounts for analysis
- [[Dimensions]] via Dimension — each cost element belongs to a cost-accounting dimension
