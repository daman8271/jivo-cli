---
entity: AssetGroupsService
domain: fixed-assets
readable: true
methods: [AssetGroupsService_GetList]
rows_oil: null
---
# AssetGroupsService
RPC helper to enumerate fixed-asset group definitions.

## Operations
- `AssetGroupsService_GetList` — lists asset group codes and descriptions

Entity sets are the read path in the CLI — read the master data via [[AssetGroups]]. Browse this service's operations with `./sapb1 ops AssetGroupsService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetGroups]] — the entity set this service enumerates (Code)
