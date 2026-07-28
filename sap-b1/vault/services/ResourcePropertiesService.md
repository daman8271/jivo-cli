---
entity: ResourcePropertiesService
domain: production-mrp
readable: false
methods: ["ResourcePropertiesService_GetList"]
rows_oil: null
---
# ResourcePropertiesService
RPC-style function service returning the list of resource property definitions.

## Operations
- ResourcePropertiesService_GetList

Entity sets are the read path in the CLI — query [[ResourceProperties]] directly instead. Browse this service's operations with `./sapb1 ops ResourcePropertiesService`.

## Connections
- Domain: [[production-mrp]]
- [[ResourceProperties]] — the entity set this operation lists
