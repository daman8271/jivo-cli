---
entity: NFModelsService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# NFModelsService
Lists Brazil-localization Nota Fiscal document models used to classify fiscal documents.

## Operations
- NFModelsService_GetList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops NFModelsService`. Brazil localization — not expected to carry data in an India (JIVO_OIL) company database.

## Connections
- Domain: [[administration-setup-2]]
- [[NotaFiscalCFOP]] via fiscal-document classification — CFOP codes used alongside NF models
- [[NotaFiscalUsage]] via fiscal-document classification — NF usage codes used alongside NF models
