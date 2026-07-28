---
entity: ServiceCallStatusService
domain: service-contracts
readable: false
methods: ["ServiceCallStatusService_GetServiceCallStatusList"]
rows_oil: null
---
# ServiceCallStatusService
RPC helper that returns the list of service-call status codes.

## Operations
- ServiceCallStatusService_GetServiceCallStatusList

Entity sets are the read path in the CLI — query [[ServiceCallStatus]] directly instead. Browse this service's operations with `./sapb1 ops ServiceCallStatusService`.

## Connections
- Domain: [[service-contracts]]
- [[ServiceCallStatus]] — the entity set this operation lists
