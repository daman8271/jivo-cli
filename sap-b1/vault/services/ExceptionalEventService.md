---
entity: ExceptionalEventService
domain: administration-setup-1
readable: false
methods: [GetExceptionalEventList]
rows_oil: null
---
# ExceptionalEventService
Lists exceptional calendar events (holidays/closures) that override normal business availability, e.g. for service scheduling.

## Operations
- GetExceptionalEventList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops ExceptionalEventService`.

## Connections
- Domain: [[administration-setup-1]]
