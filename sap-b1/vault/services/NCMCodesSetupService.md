---
entity: NCMCodesSetupService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# NCMCodesSetupService
Lists Brazil-localization NCM (Mercosur nomenclature) commodity codes assigned to items for fiscal classification.

## Operations
- NCMCodesSetupService_GetNCMCodeSetupList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops NCMCodesSetupService`. Brazil localization — not expected to carry data in an India (JIVO_OIL) company database.

## Connections
- Domain: [[administration-setup-2]]
- [[Items]] via the item's NCM code — fiscal commodity classification per item
