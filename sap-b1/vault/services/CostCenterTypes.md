---
entity: CostCenterTypes
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CostCenterTypes
Classification types for cost centers/profit centers in cost accounting (unused in this DB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CostCenterTypes --top 5
./sapb1 query CostCenterTypes --count
./sapb1 fields CostCenterTypes   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query CostCenterTypes --filter "Name ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields CostCenterTypes` |

## Connections
- Domain: [[financials-accounting-1]]
- [[ProfitCenters]] via CostCenterType — profit centers can be classified by a type
- [[Dimensions]] via dimension assignment — types organize centers inside a cost dimension
