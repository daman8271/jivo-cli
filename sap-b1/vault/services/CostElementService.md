---
entity: CostElementService
domain: financials-accounting-1
readable: false
methods: ["CostElementService_GetCostElementList"]
rows_oil: null
---
# CostElementService
Lists cost elements that map G/L expense accounts into cost accounting for allocation to cost centers.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[CostElements]] — the entity set counterpart holding the cost element records (query this instead)
- [[ChartOfAccounts]] — the G/L expense accounts each cost element maps (AccountCode)
- [[ProfitCenters]] — cost centers receiving allocated cost element amounts
