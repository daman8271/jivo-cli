---
entity: BrazilFuelIndexersService
domain: administration-setup-1
readable: false
methods: [BrazilFuelIndexersService_GetList]
rows_oil: null
---
# BrazilFuelIndexersService
Lists Brazil-specific fuel tax indexer codes for fiscal compliance (irrelevant to an Indian localization DB).

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[BrazilFuelIndexers]] — the indexer code records this RPC lists (AbsEntry)
