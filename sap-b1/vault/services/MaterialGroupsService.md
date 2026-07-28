---
entity: MaterialGroupsService
domain: administration-setup-1
readable: false
methods: [GetMaterialGroupList]
rows_oil: null
---
# MaterialGroupsService
Lists material groups (localization-specific item classification, e.g. for Indian excise/GST) used to categorize items for tax purposes.

## Operations
- GetMaterialGroupList

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops MaterialGroupsService`.

## Connections
- Domain: [[administration-setup-1]]
- [[Items]] via the item's material group assignment — groups classify items for statutory/tax reporting
