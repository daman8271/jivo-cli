---
entity: LandedCostsService
domain: purchasing
readable: false
methods: ["LandedCostsService_GetLandedCostList"]
rows_oil: null
---
# LandedCostsService
RPC helper that returns filtered lists of landed-cost documents.
## Operations
- LandedCostsService_GetLandedCostList

Entity sets are the read path in the CLI — read landed-cost rows through the [[LandedCosts]] entity set (`./sapb1 query LandedCosts`); browse this service's ops with `./sapb1 ops LandedCostsService`.
## Connections
- Domain: [[purchasing]]
- [[LandedCosts]] — the entity set this service lists
