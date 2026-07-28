# SAP Business One Service Layer — Inventory & Warehouse (Part 1)

Grounded from the local Service Layer API reference (`raw/service-layer-api-reference.html`) and `catalog/services.json`. Operations below are copied verbatim from the catalog — none invented. Field names for read entities are the REAL fields that appear in the doc's own example payloads / `$select` lists; where the doc exposes no scalar fields, the entry says "query live `$metadata`".

This domain has **40 services**: 20 RPC-style function/action services (suffix `…Service`) and 20 readable OData entities. Endpoint host in examples is `https://localhost:50000`; version shown as `/b1s/v1/` (the Service Layer also serves `/b1s/v1/`). CLI examples use the read-only `sapb1` CLI.

Convention notes:
- `GET Entity` = list; `GET Entity(id)` = single row; `POST Entity` = create; `PATCH Entity(id)` = update; `DELETE Entity(id)` = delete; `POST Entity(id)/Action` = bound action.
- `…Service_GetList` / `…Service_Get*` are RPC methods invoked via POST (a few also accept GET); they are NOT OData entity reads.

---

## AlternativeItemsService
(1) Manage alternative/substitute items defined for an item. (inferred from name; ops confirm add/update/delete/get by `OriginalItem`)
(2) function/action Service
(3) Operations:
- POST `AlternativeItemsService_AddItem` (payload `OriginalItem`)
- POST `AlternativeItemsService_UpdateItem`
- POST `AlternativeItemsService_DeleteItem`
- POST `AlternativeItemsService_GetItem` (payload `OriginalItemParams`)

## BarCodesService
(1) RPC list of bar codes across items/UoMs. (inferred)
(2) function/action Service (read-list RPC)
(3) Operations:
- GET `BarCodesService_GetList`
- POST `BarCodesService_GetList`

## BinLocationAttributesService
(1) RPC list of bin-location attributes (warehouse-bin attribute definitions). (inferred)
(2) function/action Service
(3) Operations:
- POST `BinLocationAttributesService_GetList`

## BinLocationFieldsService
(1) RPC list of bin-location sublevel field definitions. (inferred)
(2) function/action Service
(3) Operations:
- POST `BinLocationFieldsService_GetList`

## BinLocationsService
(1) RPC list of warehouse bin locations. (inferred)
(2) function/action Service
(3) Operations:
- POST `BinLocationsService_GetList`

## CashFlowLineItemsService
(1) RPC list of cash-flow line items (cash-flow report line master). (inferred)
(2) function/action Service
(3) Operations:
- POST `CashFlowLineItemsService_GetCashFlowLineItemList`

## DashboardPackagesService
(1) Import a dashboard package into the company. (grounded: payload `DashboardPackageImportParams`)
(2) function/action Service
(3) Operations:
- POST `DashboardPackagesService_ImportDashboardPackage` (payload `DashboardPackageImportParams`)

## IntegrationPackagesConfigureService
(1) RPC list of integration-package configuration records. (inferred)
(2) function/action Service
(3) Operations:
- POST `IntegrationPackagesConfigureService_GetList`

## InventoryCountingsService
(1) RPC list of inventory-counting documents. (inferred)
(2) function/action Service
(3) Operations:
- POST `InventoryCountingsService_GetList`

## InventoryGenEntryService
(1) Approval helpers for Goods Receipts (inventory general entries). (grounded: `GetApprovalTemplates` takes payload `Document`)
(2) function/action Service
(3) Operations:
- POST `InventoryGenEntryService_GetApprovalTemplates` (payload `Document`)
- POST `InventoryGenEntryService_HandleApprovalRequest`

## InventoryGenExitService
(1) Approval helpers for Goods Issues (inventory general exits). (grounded: mirrors GenEntry approval flow)
(2) function/action Service
(3) Operations:
- POST `InventoryGenExitService_GetApprovalTemplates`
- POST `InventoryGenExitService_HandleApprovalRequest`

## InventoryOpeningBalancesService
(1) RPC list of inventory opening-balance documents. (inferred)
(2) function/action Service
(3) Operations:
- POST `InventoryOpeningBalancesService_GetList`

## InventoryPostingsService
(1) List inventory postings and set their copy option. (grounded: `SetCopyOption` payload `InventoryPostingCopyOption`)
(2) function/action Service
(3) Operations:
- POST `InventoryPostingsService_GetList`
- POST `InventoryPostingsService_SetCopyOption` (payload `InventoryPostingCopyOption`)

## InventoryTransferRequestsService
(1) Approval helpers for inventory transfer requests. (grounded: `GetApprovalTemplates` takes payload `StockTransfer`)
(2) function/action Service
(3) Operations:
- POST `InventoryTransferRequestsService_GetApprovalTemplates` (payload `StockTransfer`)
- POST `InventoryTransferRequestsService_HandleApprovalRequest`

## PickListsService
(1) Close a pick list and update its released allocation. (grounded: both take payload `PickList`)
(2) function/action Service
(3) Operations:
- POST `PickListsService_Close` (payload `PickList`)
- POST `PickListsService_UpdateReleasedAllocation` (payload `PickList`)

## StockTransferDraftService
(1) Approval helpers for stock-transfer draft documents. (grounded: mirrors StockTransfer approval flow)
(2) function/action Service
(3) Operations:
- POST `StockTransferDraftService_GetApprovalTemplates`
- POST `StockTransferDraftService_HandleApprovalRequest`

## StockTransferService
(1) Approval helpers for stock-transfer documents. (grounded)
(2) function/action Service
(3) Operations:
- POST `StockTransferService_GetApprovalTemplates`
- POST `StockTransferService_HandleApprovalRequest`

## UnitOfMeasurementGroupsService
(1) RPC list of unit-of-measurement groups. (inferred)
(2) function/action Service
(3) Operations:
- POST `UnitOfMeasurementGroupsService_GetList`

## UnitOfMeasurementsService
(1) RPC list of units of measurement. (inferred)
(2) function/action Service
(3) Operations:
- POST `UnitOfMeasurementsService_GetList`

## WarehouseSublevelCodesService
(1) RPC list of warehouse bin sublevel codes. (inferred)
(2) function/action Service
(3) Operations:
- POST `WarehouseSublevelCodesService_GetList`

---

## BarCodes
(1) Bar codes assigned to items and their units of measure.
(2) readable ENTITY
(3) Operations:
- GET `BarCodes(id)` · GET `BarCodes` · POST `BarCodes` · PATCH `BarCodes(id)` · DELETE `BarCodes(id)`
(4) Fields: `AbsEntry`, `ItemNo`, `UoMEntry`, `Barcode`, `FreeText`
```
GET /b1s/v1/BarCodes?$select=AbsEntry,ItemNo,Barcode&$top=20
sapb1 query BarCodes --select AbsEntry,ItemNo,Barcode --top 20
```

## BatchNumberDetails
(1) Batch-number master details for batch-managed items.
(2) readable ENTITY (no create/delete; PATCH only)
(3) Operations:
- GET `BatchNumberDetails(id)` · GET `BatchNumberDetails` · PATCH `BatchNumberDetails(id)`
(4) Fields: `DocEntry`, `ItemCode`, `ItemDescription`, `Status`
```
GET /b1s/v1/BatchNumberDetails?$select=DocEntry,ItemCode,ItemDescription,Status&$top=20
sapb1 query BatchNumberDetails --select DocEntry,ItemCode,ItemDescription,Status --top 20
```

## BinLocationAttributes
(1) Attribute definitions applied to warehouse bin locations.
(2) readable ENTITY
(3) Operations:
- GET `BinLocationAttributes(id)` · GET `BinLocationAttributes` · POST `BinLocationAttributes` · PATCH `BinLocationAttributes(id)` · DELETE `BinLocationAttributes(id)`
(4) Fields: `AbsEntry`, `Code`, `Attribute`

## BinLocationFields
(1) Sublevel field definitions used to build bin-location codes.
(2) readable ENTITY (no create/delete; PATCH only)
(3) Operations:
- GET `BinLocationFields(id)` · GET `BinLocationFields` · PATCH `BinLocationFields(id)`
(4) Fields: `AbsEntry`, `FieldNumber`, `FieldType`, `DefaultFieldName`

## BinLocations
(1) Warehouse bin locations (individual storage bins).
(2) readable ENTITY
(3) Operations:
- GET `BinLocations(id)` · GET `BinLocations` · POST `BinLocations` · PATCH `BinLocations(id)` · DELETE `BinLocations(id)`
(4) Fields: `AbsEntry`, `Warehouse`, `BinCode`, `Description`, `Sublevel1`, `Inactive`
```
GET /b1s/v1/BinLocations?$select=AbsEntry,Warehouse,BinCode,Description&$top=20
sapb1 query BinLocations --select AbsEntry,Warehouse,BinCode,Description --top 20
```

## CashFlowLineItems
(1) Cash-flow report line-item master records.
(2) readable ENTITY (GET only)
(3) Operations:
- GET `CashFlowLineItems(id)` · GET `CashFlowLineItems`
(4) Fields: `LineItemID`, `LineItemName`, `ActiveLineItem`

## IntegrationPackagesConfigure
(1) Integration-package configuration records.
(2) readable ENTITY
(3) Operations:
- GET `IntegrationPackagesConfigure(id)` · GET `IntegrationPackagesConfigure` · POST `IntegrationPackagesConfigure` · PATCH `IntegrationPackagesConfigure(id)` · DELETE `IntegrationPackagesConfigure(id)`
(4) Fields: `AbsEntry`, `Code`, `Name`, `IsEnable`

## InventoryCountings
(1) Inventory-counting documents (physical count worksheets) with a bound Close action.
(2) readable ENTITY
(3) Operations:
- GET `InventoryCountings(id)` · GET `InventoryCountings` · POST `InventoryCountings` · PATCH `InventoryCountings(id)` · DELETE `InventoryCountings(id)` · POST `InventoryCountings(id)/Close`
(4) Fields: `DocumentEntry`, `DocumentNumber`, `Series`, `InventoryCountingLines` (line: `ItemCode`, `WarehouseCode`)
```
GET /b1s/v1/InventoryCountings?$select=DocumentEntry,DocumentNumber,Series&$top=20
sapb1 query InventoryCountings --select DocumentEntry,DocumentNumber,Series --top 20
```

## InventoryCycles
(1) Inventory cycle-count schedule definitions.
(2) readable ENTITY
(3) Operations:
- GET `InventoryCycles(id)` · GET `InventoryCycles` · POST `InventoryCycles` · PATCH `InventoryCycles(id)` · DELETE `InventoryCycles(id)`
(4) Fields: `CycleCode`, `CycleName`, `Frequency`

## InventoryGenEntries
(1) Goods Receipt documents (inventory general entries) with Close/Cancel/Reopen/CreateCancellationDocument actions.
(2) readable ENTITY (no DELETE)
(3) Operations:
- GET `InventoryGenEntries(id)` · GET `InventoryGenEntries` · POST `InventoryGenEntries` · PATCH `InventoryGenEntries(id)` · POST `InventoryGenEntries(id)/Close` · POST `InventoryGenEntries(id)/Cancel` · POST `InventoryGenEntries(id)/Reopen` · POST `InventoryGenEntries(id)/CreateCancellationDocument`
(4) Fields: `DocEntry`, `DocNum`, `DocDate`, `DocumentLines` (line: `ItemCode`, `Quantity`, `UnitPrice`, `CostingCode`)
```
GET /b1s/v1/InventoryGenEntries?$select=DocEntry,DocNum,DocDate&$top=20
sapb1 query InventoryGenEntries --select DocEntry,DocNum,DocDate --top 20
```

## InventoryGenExits
(1) Goods Issue documents (inventory general exits) with Close/Cancel/Reopen/CreateCancellationDocument actions.
(2) readable ENTITY (no DELETE)
(3) Operations:
- GET `InventoryGenExits(id)` · GET `InventoryGenExits` · POST `InventoryGenExits` · PATCH `InventoryGenExits(id)` · POST `InventoryGenExits(id)/Close` · POST `InventoryGenExits(id)/Cancel` · POST `InventoryGenExits(id)/Reopen` · POST `InventoryGenExits(id)/CreateCancellationDocument`
(4) Fields: `DocEntry`, `DocNum`, `DocDate`, `DocumentLines` (line: `ItemCode`, `Quantity`, `CostingCode`)
```
GET /b1s/v1/InventoryGenExits?$select=DocEntry,DocNum,DocDate&$top=20
sapb1 query InventoryGenExits --select DocEntry,DocNum,DocDate --top 20
```

## InventoryOpeningBalances
(1) Inventory opening-balance documents (initial stock quantities/values).
(2) readable ENTITY (no DELETE)
(3) Operations:
- GET `InventoryOpeningBalances(id)` · GET `InventoryOpeningBalances` · POST `InventoryOpeningBalances` · PATCH `InventoryOpeningBalances(id)`
(4) Fields: `DocumentEntry`, `PostingDate`, `DocumentDate`, `DocumentNumber`, `InventoryOpeningBalanceLines`

## InventoryPostings
(1) Inventory posting documents (stock count posting / recount results).
(2) readable ENTITY
(3) Operations:
- GET `InventoryPostings(id)` · GET `InventoryPostings` · POST `InventoryPostings` · PATCH `InventoryPostings(id)` · DELETE `InventoryPostings(id)`
(4) Fields: `DocumentEntry`, `DocumentNumber`, `Series`

## InventoryTransferRequests
(1) Inventory transfer request documents with Cancel/Close/SaveDraftToDocument actions.
(2) readable ENTITY (no DELETE)
(3) Operations:
- GET `InventoryTransferRequests(id)` · GET `InventoryTransferRequests` · POST `InventoryTransferRequests` · PATCH `InventoryTransferRequests(id)` · POST `InventoryTransferRequests(id)/Cancel` · POST `InventoryTransferRequests(id)/Close` · POST `InventoryTransferRequests(id)/SaveDraftToDocument`
(4) Fields: `DocEntry`, `Series`, `StockTransferLines` (line: `ItemCode`, `Quantity`, `WarehouseCode`)
```
GET /b1s/v1/InventoryTransferRequests?$select=DocEntry,Series&$top=20
sapb1 query InventoryTransferRequests --select DocEntry,Series --top 20
```

## ItemGroups
(1) Item group master (default G/L accounts and defaults per item group).
(2) readable ENTITY
(3) Operations:
- GET `ItemGroups(id)` · GET `ItemGroups` · POST `ItemGroups` · PATCH `ItemGroups(id)` · DELETE `ItemGroups(id)`
(4) Fields: `GroupName`, `MinimumOrderQuantity`, `Alert`, `PriceDifferencesAccount`, `StockInflationAdjustAccount`
```
GET /b1s/v1/ItemGroups?$select=Number,GroupName&$top=20
sapb1 query ItemGroups --select Number,GroupName --top 20
```
(Note: the group primary key is `Number`; confirm via live `$metadata`.)

## ItemImages
(1) Item image binary — a stream/media entity attached to an `Item`.
(2) readable ENTITY (stream entity; GET(id)/PATCH/DELETE only, no collection GET)
(3) Operations:
- GET `ItemImages(id)` · PATCH `ItemImages(id)` · DELETE `ItemImages(id)`
(4) Fields: stream/media content — no scalar `$select` fields; query live `$metadata`.

## ItemProperties
(1) Item property definitions (the 64 item property flags/labels).
(2) readable ENTITY
(3) Operations:
- GET `ItemProperties(id)` · GET `ItemProperties` · POST `ItemProperties` · PATCH `ItemProperties(id)` · DELETE `ItemProperties(id)`
(4) Fields: `Number`, `PropertyName`
```
GET /b1s/v1/ItemProperties?$select=Number,PropertyName&$top=20
sapb1 query ItemProperties --select Number,PropertyName --top 20
```

## Items
(1) Item master data (products, materials, and services).
(2) readable ENTITY (has a bound Cancel action)
(3) Operations:
- GET `Items(id)` · GET `Items` · POST `Items` · PATCH `Items(id)` · DELETE `Items(id)` · POST `Items(id)/Cancel`
(4) Fields: `ItemCode`, `ItemName`, `ForeignName`, `ItemType`
```
GET /b1s/v1/Items?$select=ItemCode,ItemName,ForeignName&$top=20
sapb1 query Items --select ItemCode,ItemName,ForeignName --top 20
```

## PackagesTypes
(1) Package-type master (shipping package dimensions and weights).
(2) readable ENTITY
(3) Operations:
- GET `PackagesTypes(id)` · GET `PackagesTypes` · POST `PackagesTypes` · PATCH `PackagesTypes(id)` · DELETE `PackagesTypes(id)`
(4) Fields: `Code`, `Type`, `Length1`, `Height1`, `Weight1`, `VolumeUnit`
```
GET /b1s/v1/PackagesTypes?$select=Code,Type,Length1,Weight1&$top=20
sapb1 query PackagesTypes --select Code,Type,Length1,Weight1 --top 20
```

## PickLists
(1) Pick-and-pack pick lists, with a bound GetReleasedAllocation action.
(2) readable ENTITY (also supports PUT replace)
(3) Operations:
- GET `PickLists(id)` · GET `PickLists` · POST `PickLists` · PATCH `PickLists(id)` · PUT `PickLists(id)` · POST `PickLists(id)/GetReleasedAllocation`
(4) Fields: `AbsoluteEntry`, `Name`, `OwnerCode`, `PickDate`, `ObjectType`, `PickListsLines`
```
GET /b1s/v1/PickLists?$select=AbsoluteEntry,Name,OwnerCode,PickDate&$top=20
sapb1 query PickLists --select AbsoluteEntry,Name,OwnerCode,PickDate --top 20
```
