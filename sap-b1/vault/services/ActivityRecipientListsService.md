---
entity: ActivityRecipientListsService
domain: business-partners-crm
readable: true
methods: [ActivityRecipientListsService_GetList]
rows_oil: null
---
# ActivityRecipientListsService
Function service returning the list of activity recipient distribution lists.

## Operations
- `ActivityRecipientListsService_GetList` (GET) — enumerate recipient distribution lists
- `ActivityRecipientListsService_GetList` (POST) — same list via POST invocation

Entity sets are the read path in the CLI — read the master data via [[ActivityRecipientLists]]. Browse this service's operations with `./sapb1 ops ActivityRecipientListsService`.

## Connections
- Domain: [[business-partners-crm]]
- [[ActivityRecipientLists]] — the entity set this service enumerates (Code)
