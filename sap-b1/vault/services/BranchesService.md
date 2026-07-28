---
entity: BranchesService
domain: administration-setup-1
readable: false
methods: [BranchesService_GetBranchList]
rows_oil: null
---
# BranchesService
Lists company branches used in multi-branch accounting and document segregation.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[Branches]] — the branch records this RPC lists (Code)
- [[BusinessPlaces]] — branches map to business places for statutory reporting (BPLID)
- [[Warehouses]] — warehouses are assigned to branches (BusinessPlaceID)
