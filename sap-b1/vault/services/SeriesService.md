---
entity: SeriesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# SeriesService
Manages document numbering series (including electronic-document series): creation, per-user/global defaults, and attachment to document types.

## Operations
- SeriesService_AddSeries
- SeriesService_RemoveSeries
- SeriesService_AttachSeriesToDocument
- SeriesService_UnattachSeriesFromDocument
- SeriesService_SetDefaultSeriesForAllUsers
- SeriesService_SetDefaultSeriesForCurrentUser
- SeriesService_SetDefaultSeriesForUser
- SeriesService_UpdateSeries
- SeriesService_GetDefaultSeries
- SeriesService_GetDocumentSeries
- SeriesService_GetSeries
- SeriesService_GetDocumentChangedMenuName
- SeriesService_ChangeDocumentMenuName
- SeriesService_GetElectronicSeries
- SeriesService_AddElectronicSeries
- SeriesService_RemoveElectronicSeries
- SeriesService_UpdateElectronicSeries
- SeriesService_GetDefaultElectronicSeries
- SeriesService_SetDefaultElectronicSeries

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops SeriesService`. The Add/Remove/Update/Set/Attach/Change operations mutate numbering setup and are out of scope under our READ-ONLY rule.

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] via UserCode — default series can be set per user or for all users
- [[Invoices]] via Series field — invoice numbering draws from these series
- [[Orders]] via Series field — sales order numbering draws from these series
