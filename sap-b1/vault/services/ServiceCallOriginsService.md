---
entity: ServiceCallOriginsService
domain: service-contracts
readable: false
methods: ["ServiceCallOriginsService_GetServiceCallOriginList"]
rows_oil: null
---
# ServiceCallOriginsService
RPC helper that returns the list of service-call origin codes (how a call was reported).

## Operations
- ServiceCallOriginsService_GetServiceCallOriginList

Entity sets are the read path in the CLI — query [[ServiceCallOrigins]] directly instead. Browse this service's operations with `./sapb1 ops ServiceCallOriginsService`.

## Connections
- Domain: [[service-contracts]]
- [[ServiceCallOrigins]] — the entity set this operation lists
