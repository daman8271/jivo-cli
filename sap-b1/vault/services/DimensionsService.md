---
entity: DimensionsService
domain: financials-accounting-1
readable: false
methods: ["DimensionsService_GetDimensionList"]
rows_oil: null
---
# DimensionsService
Returns the cost accounting dimensions (up to 5) along which profit centers and distribution rules are organized.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[Dimensions]] — the entity set counterpart holding the dimension records (query this instead)
- [[ProfitCenters]] — profit/cost centers assigned to a dimension (InWhichDimension)
- [[DistributionRules]] — distribution rules scoped per dimension (InWhichDimension)
