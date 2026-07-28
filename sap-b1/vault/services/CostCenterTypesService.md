---
entity: CostCenterTypesService
domain: financials-accounting-1
readable: false
methods: ["CostCenterTypesService_GetCostCenterTypeList"]
rows_oil: null
---
# CostCenterTypesService
Returns the catalog of cost center types used to classify cost centers in cost accounting.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[financials-accounting-1]]
- [[CostCenterTypes]] — the entity set counterpart holding the type records (query this instead)
- [[ProfitCenters]] — cost centers classified by these types (CostCenterType)
- [[Dimensions]] — the dimensions along which typed cost centers are organized
