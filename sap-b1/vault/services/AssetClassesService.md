---
entity: AssetClassesService
domain: fixed-assets
readable: true
methods: [AssetClassesService_GetList]
rows_oil: null
---
# AssetClassesService
RPC helper to enumerate asset class definitions.

## Operations
- `AssetClassesService_GetList` — lists asset class codes and descriptions

Entity sets are the read path in the CLI — read the master data via [[AssetClasses]]. Browse this service's operations with `./sapb1 ops AssetClassesService`.

## Connections
- Domain: [[fixed-assets]]
- [[AssetClasses]] — the entity set this service enumerates (Code)
