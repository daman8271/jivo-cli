---
entity: ProfitCentersService
domain: financials-accounting-1
readable: false
methods: ["ProfitCentersService_GetProfitCenterList"]
rows_oil: null
---
# ProfitCentersService
Lists profit/cost centers used in cost accounting to track revenues and expenses by business unit.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[ProfitCenters]] — the entity set counterpart holding the center records (query this instead)
- [[Dimensions]] — each center belongs to a dimension (InWhichDimension)
- [[DistributionRules]] — rules allocate amounts across these centers
- [[CostCenterTypes]] — classification of each center (CostCenterType)
