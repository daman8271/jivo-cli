---
entity: ServiceCallSolutionStatusService
domain: service-contracts
readable: false
methods: ["ServiceCallSolutionStatusService_GetServiceCallSolutionStatusList"]
rows_oil: null
---
# ServiceCallSolutionStatusService
RPC helper that returns the list of knowledge-base solution status codes.

## Operations
- ServiceCallSolutionStatusService_GetServiceCallSolutionStatusList

Entity sets are the read path in the CLI — query [[ServiceCallSolutionStatus]] directly instead. Browse this service's operations with `./sapb1 ops ServiceCallSolutionStatusService`.

## Connections
- Domain: [[service-contracts]]
- [[ServiceCallSolutionStatus]] — the entity set this operation lists
- [[KnowledgeBaseSolutions]] — solutions that carry these status codes
