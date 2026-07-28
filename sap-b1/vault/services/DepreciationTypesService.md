---
entity: DepreciationTypesService
domain: fixed-assets
readable: false
methods: [DepreciationTypesService_GetList]
rows_oil: null
---
# DepreciationTypesService
POST-only RPC helper to enumerate depreciation calculation method (type) definitions.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[fixed-assets]]
- [[DepreciationTypePools]] — pools that bundle these depreciation types
- [[DepreciationAreas]] — areas where each depreciation type applies
