---
entity: AttributeGroupsService
domain: administration-setup-1
readable: true
methods: [AttributeGroupsService_GetList]
rows_oil: null
---
# AttributeGroupsService
Lists attribute groups used to classify resources/assets for grouping and reporting.

## Operations
- `AttributeGroupsService_GetList` (GET)
- `AttributeGroupsService_GetList` (POST)

Function (RPC) service — not an entity set, so `./sapb1 query` does not apply here. Entity sets are the read path in the CLI: query [[AttributeGroups]] for the same attribute group records. Browse this service's operations with `./sapb1 ops AttributeGroupsService`.

## Connections
- Domain: [[administration-setup-1]]
- [[AttributeGroups]] — the entity set counterpart holding the attribute group records (query this instead)
