---
entity: ResourcesService
domain: production-mrp
readable: false
methods: ["ResourcesService_GetList"]
rows_oil: null
---
# ResourcesService
RPC-style function service returning the list of production resources (machines/labor).

## Operations
- ResourcesService_GetList

Entity sets are the read path in the CLI — query [[Resources]] directly instead. Browse this service's operations with `./sapb1 ops ResourcesService`.

## Connections
- Domain: [[production-mrp]]
- [[Resources]] — the entity set this operation lists
