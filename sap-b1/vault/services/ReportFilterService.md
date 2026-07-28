---
entity: ReportFilterService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# ReportFilterService
Returns saved filter definitions for tax reports used in statutory tax reporting.

## Operations
- ReportFilterService_GetTaxReportFilterList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops ReportFilterService`.

## Connections
- Domain: [[administration-setup-2]]
- [[SalesTaxCodes]] via tax code — tax report filters select on tax codes
