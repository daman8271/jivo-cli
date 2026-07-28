---
entity: DepreciationAreasService
domain: fixed-assets
readable: false
methods: [DepreciationAreasService_GetList]
rows_oil: null
---
# DepreciationAreasService
POST-only RPC helper to enumerate depreciation area definitions.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[fixed-assets]]
- [[DepreciationAreas]] — the entity set with the same data, readable directly
