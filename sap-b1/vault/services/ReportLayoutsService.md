---
entity: ReportLayoutsService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# ReportLayoutsService
Manages print/report layouts (Crystal/PLD) per report type, including defaults and printer settings for document printing.

## Operations
- ReportLayoutsService_SetDefaultReport
- ReportLayoutsService_GetDefaultReport
- ReportLayoutsService_AddReportLayout
- ReportLayoutsService_UpdatePrinterSettings
- ReportLayoutsService_DeleteReportLayout
- ReportLayoutsService_GetReportLayout
- ReportLayoutsService_GetDefaultReportLayout
- ReportLayoutsService_GetReportLayoutList
- ReportLayoutsService_UpdateLanguageReport
- ReportLayoutsService_AddReportLayoutToMenu
- ReportLayoutsService_DeleteReportLayoutAndMenu

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops ReportLayoutsService`. The Set/Add/Update/Delete operations mutate layouts and are out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-2]]
- [[ReportTypes]] via ReportTypeCode — each layout belongs to a system report type
- [[Users]] via UserCode — default layouts can be set per user
