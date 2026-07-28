---
entity: ServiceGroupsService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# ServiceGroupsService
Lists service groups (e.g., India SAC service accounting code groupings) used to classify service-type items for taxation.

## Operations
- ServiceGroupsService_GetServiceGroupList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops ServiceGroupsService`.

## Connections
- Domain: [[administration-setup-2]]
- [[Items]] via service group assignment — service-type items are classified into these groups for taxation
