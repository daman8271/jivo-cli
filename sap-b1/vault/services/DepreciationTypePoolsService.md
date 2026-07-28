---
entity: DepreciationTypePoolsService
domain: fixed-assets
readable: true
methods: [DepreciationTypePoolsService_GetList]
rows_oil: null
---
# DepreciationTypePoolsService
RPC helper to enumerate depreciation type pool definitions.

## Operations
- `DepreciationTypePoolsService_GetList` — lists depreciation type pool codes and descriptions

Entity sets are the read path in the CLI — read the master data via [[DepreciationTypePools]]. Browse this service's operations with `./sapb1 ops DepreciationTypePoolsService`.

## Connections
- Domain: [[fixed-assets]]
- [[DepreciationTypePools]] — the entity set this service enumerates (Code)
