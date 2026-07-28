---
entity: DeterminationCriteriasService
domain: administration-setup-1
readable: false
methods: [DeterminationCriteriasService_GetList]
rows_oil: null
---
# DeterminationCriteriasService
Lists advanced G/L account determination criteria rules that drive automatic account assignment on postings.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[ChartOfAccounts]] — rules resolve to a target G/L account (AccountCode)
- [[Warehouses]] — warehouse is a common determination criterion (WarehouseCode)
- [[ItemGroups]] — item group is a common determination criterion (ItemGroupCode)
