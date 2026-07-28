---
entity: QueryService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# QueryService
Executes ad-hoc cross-entity queries (Service Layer query API) via POST, returning arbitrary result sets.

## Operations
- QueryService_PostQuery

Function service — there is no entity set to `./sapb1 query` here. Its single operation is POST-based, so even though it is semantically a read, it is out of scope under our standing READ-ONLY rule (no POST against the SAP server). Entity sets are the read path in the CLI (`./sapb1 query <EntitySet>`); browse this service's catalogued operations with `./sapb1 ops QueryService`.

## Connections
- Domain: [[administration-setup-2]]
- [[UserQueries]] via saved query definitions — user-authored queries this API can execute
