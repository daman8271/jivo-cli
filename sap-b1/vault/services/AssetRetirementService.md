---
entity: AssetRetirementService
domain: fixed-assets
readable: true
methods: [AssetRetirementService_Cancel, AssetRetirementService_GetList]
rows_oil: null
---
# AssetRetirementService
RPC helper to list and cancel asset retirement (disposal/sale/scrap) documents.

## Operations
- `AssetRetirementService_Cancel` — cancels a retirement document (write — out of scope under the read-only rule)
- `AssetRetirementService_GetList` — lists retirement documents

Entity sets are the read path in the CLI — read the documents via [[AssetRetirement]]. Browse this service's operations with `./sapb1 ops AssetRetirementService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetRetirement]] — the entity set this service lists and cancels (DocEntry)
