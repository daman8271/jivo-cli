---
entity: SectionsService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# SectionsService
Lists India-localization TDS sections (Income Tax Act sections) used for withholding-tax classification.

## Operations
- SectionsService_GetSectionList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops SectionsService`.

## Connections
- Domain: [[administration-setup-2]]
- [[TaxInvoiceReport]] via TDS section code — statutory withholding-tax reporting groups by section
