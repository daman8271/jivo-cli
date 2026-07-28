---
entity: ServiceCallProblemSubTypesService
domain: service-contracts
readable: false
methods: ["ServiceCallProblemSubTypesService_GetServiceCallProblemSubTypeList"]
rows_oil: null
---
# ServiceCallProblemSubTypesService
RPC helper that returns the list of service-call problem sub-type codes.

## Operations
- ServiceCallProblemSubTypesService_GetServiceCallProblemSubTypeList

Entity sets are the read path in the CLI — query [[ServiceCallProblemSubTypes]] directly instead. Browse this service's operations with `./sapb1 ops ServiceCallProblemSubTypesService`.

## Connections
- Domain: [[service-contracts]]
- [[ServiceCallProblemSubTypes]] — the entity set this operation lists
