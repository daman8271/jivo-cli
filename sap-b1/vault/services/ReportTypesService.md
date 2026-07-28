---
entity: ReportTypesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# ReportTypesService
Lists the system report types (e.g., AR Invoice, Sales Order) to which print layouts can be assigned.

## Operations
- ReportTypesService_GetReportTypeList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops ReportTypesService`.

## Connections
- Domain: [[administration-setup-2]]
- [[ReportLayoutsService]] via ReportTypeCode — layouts are assigned per report type
