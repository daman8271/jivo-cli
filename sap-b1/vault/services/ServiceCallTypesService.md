---
entity: ServiceCallTypesService
domain: service-contracts
readable: false
methods: ["ServiceCallTypesService_GetServiceCallTypeList"]
rows_oil: null
---
# ServiceCallTypesService
RPC helper that returns the list of service-call type codes.

## Operations
- ServiceCallTypesService_GetServiceCallTypeList

Entity sets are the read path in the CLI — query [[ServiceCallTypes]] directly instead. Browse this service's operations with `./sapb1 ops ServiceCallTypesService`.

## Connections
- Domain: [[service-contracts]]
- [[ServiceCallTypes]] — the entity set this operation lists
