---
entity: ResourceGroupsService
domain: production-mrp
readable: false
methods: ["ResourceGroupsService_GetList"]
rows_oil: null
---
# ResourceGroupsService
RPC-style function service returning the list of production resource groups.

## Operations
- ResourceGroupsService_GetList

Entity sets are the read path in the CLI — query [[ResourceGroups]] directly instead. Browse this service's operations with `./sapb1 ops ResourceGroupsService`.

## Connections
- Domain: [[production-mrp]]
- [[ResourceGroups]] — the entity set this operation lists
