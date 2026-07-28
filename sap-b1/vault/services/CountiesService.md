---
entity: CountiesService
domain: administration-setup-1
readable: false
methods: [CountiesService_GetCountyList]
rows_oil: null
---
# CountiesService
Lists county master data used in addresses for certain localizations.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Counties]] — the county records this RPC lists (AbsEntry)
- [[States]] — each county belongs to a state (State)
- [[Countries]] — each county belongs to a country (Country)
