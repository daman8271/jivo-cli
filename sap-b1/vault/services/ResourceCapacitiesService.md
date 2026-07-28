---
entity: ResourceCapacitiesService
domain: production-mrp
readable: false
methods: ["ResourceCapacitiesService_GetList", "ResourceCapacitiesService_GetListWithFilter"]
rows_oil: null
---
# ResourceCapacitiesService
RPC-style function service to fetch lists of resource capacity records, optionally filtered.

## Operations
- ResourceCapacitiesService_GetList
- ResourceCapacitiesService_GetListWithFilter

Entity sets are the read path in the CLI — query [[ResourceCapacities]] directly instead. Browse this service's operations with `./sapb1 ops ResourceCapacitiesService`.

## Connections
- Domain: [[production-mrp]]
- [[ResourceCapacities]] — the entity set these operations list
- [[Resources]] — resources whose capacity is listed
