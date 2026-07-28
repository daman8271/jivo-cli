---
entity: AssetDepreciationGroupsService
domain: fixed-assets
readable: true
methods: [AssetDepreciationGroupsService_GetList]
rows_oil: null
---
# AssetDepreciationGroupsService
RPC helper to enumerate asset depreciation group definitions.

## Operations
- `AssetDepreciationGroupsService_GetList` — lists depreciation group codes and descriptions

Entity sets are the read path in the CLI — read the master data via [[AssetDepreciationGroups]]. Browse this service's operations with `./sapb1 ops AssetDepreciationGroupsService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetDepreciationGroups]] — the entity set this service enumerates (Code)
