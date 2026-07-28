---
entity: ServiceCallProblemTypesService
domain: service-contracts
readable: false
methods: ["ServiceCallProblemTypesService_GetServiceCallProblemTypeList"]
rows_oil: null
---
# ServiceCallProblemTypesService
RPC helper that returns the list of service-call problem type codes.

## Operations
- ServiceCallProblemTypesService_GetServiceCallProblemTypeList

Entity sets are the read path in the CLI — query [[ServiceCallProblemTypes]] directly instead. Browse this service's operations with `./sapb1 ops ServiceCallProblemTypesService`.

## Connections
- Domain: [[service-contracts]]
- [[ServiceCallProblemTypes]] — the entity set this operation lists
