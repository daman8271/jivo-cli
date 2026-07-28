---
entity: Dimensions
domain: financials-accounting-1
readable: true
methods: [GET, PATCH]
rows_oil: 5
---
# Dimensions
The five cost-accounting dimensions that profit centers and distribution rules are organized under for multidimensional P&L analysis. Live rows in JIVO_OIL_HANADB: 5.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Dimensions --top 5
./sapb1 query Dimensions --count
./sapb1 query Dimensions --select "DimensionCode,DimensionName,IsActive" --top 10
# Only the dimensions actually switched on:
./sapb1 query Dimensions --filter "IsActive eq 'tYES'"
```

## Key fields
| Field | Meaning |
|---|---|
| DimensionCode | Dimension number (key, 1-5) |
| DimensionName | Dimension display name |
| DimensionDescription | Longer description |
| IsActive | Active for posting flag |

## Connections
- Domain: [[financials-accounting-1]]
- [[ProfitCenters]] via InWhichDimension — every profit/cost center lives in one dimension
- [[DistributionRules]] via InWhichDimension — distribution rules are scoped per dimension
- [[CostElements]] via Dimension — cost elements analyze expenses inside a dimension
