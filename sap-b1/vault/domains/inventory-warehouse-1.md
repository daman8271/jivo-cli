# Inventory & Warehouse (part 1)

Core inventory master data and stock-movement documents (part 1 of 2 — see [[inventory-warehouse-2]]). The center of gravity is [[Items]] (2,264 SKUs) with its classification masters ([[ItemGroups]], [[ItemProperties]], [[BarCodes]], [[PackagesTypes]]) and bin-location topology ([[BinLocations]] and friends). Stock moves through [[InventoryGenEntries]] / [[InventoryGenExits]] (goods receipt/issue, ~7.9k each), [[InventoryTransferRequests]], [[PickLists]] (3.6k), [[InventoryCountings]] and [[InventoryOpeningBalances]]. [[BatchNumberDetails]] (17.3k) is the batch-traceability backbone for oil lots. Everything joins on ItemCode + WhsCode.

Part of the [[00-SAP-B1-Atlas]] — 40 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[BatchNumberDetails]] **(17,257 rows)** — Master records of batch numbers per item with manufacturing/expiry dates and status — the traceability backbone for batch-managed oil stock (17,257 batches live).
- [[InventoryGenEntries]] **(7,892 rows)** — Goods Receipt documents that increase stock without a purchase order — e.g. production output or manual stock additions; heavily used (7.9k docs).
- [[InventoryGenExits]] **(7,765 rows)** — Goods Issue documents that decrease stock without a sales order — e.g. raw-material consumption, write-offs, samples; heavily used (7.8k docs).
- [[PickLists]] **(3,598 rows)** — Warehouse pick-and-pack lists (3.6k) that allocate and track picking of ordered items ahead of delivery.
- [[Items]] **(2,264 rows)** — The item master — 2,264 SKUs of oils/materials with stock, pricing, tax, UoM, and warehouse settings; the backbone of all inventory and sales documents.
- [[InventoryTransferRequests]] **(1,282 rows)** — Requests to move stock between warehouses (e.g. plant to depot), later fulfilled by actual StockTransfers; 1.3k requests in use.
- [[ItemProperties]] **(64 rows)** — The 64 checkbox-style item property flags (Properties 1–64) used to tag and filter items in reports and pricing.
- [[CashFlowLineItems]] **(31 rows)** — Read-only hierarchy of cash-flow statement line items used to classify postings for cash-flow reporting.
- [[BinLocationFields]] **(14 rows)** — Configures the sublevel/segment field structure used to compose bin location codes in bin-managed warehouses.
- [[ItemGroups]] **(10 rows)** — Categorizes items into 10 groups (e.g. finished goods vs raw material) and sets their default G/L account determination and planning parameters.
- [[IntegrationPackagesConfigure]] **(3 rows)** — Configuration switches for SAP B1 integration framework packages (enable/disable integration scenarios).
- [[BarCodes]] — Entity set of item barcodes mapping scannable codes to items and UoMs (empty in JIVO_OIL_HANADB, so fields inferred from SAP B1 standard schema).
- [[BarCodesService]] — RPC-style list access to item barcode records (companion to the BarCodes entity set).
- [[BinLocationAttributes]] — Defines attribute codes that can be tagged onto warehouse bin locations for classification (empty — bin management not used in JIVO_OIL).
- [[BinLocations]] — Master data of individual bin storage locations within warehouses (empty — JIVO_OIL warehouses are not bin-managed).
- [[InventoryCountings]] — Physical stock-count documents recording counted vs system quantities before posting differences (unused in JIVO_OIL).
- [[InventoryCycles]] — Defines recurring cycle-count schedules that drive periodic inventory counting alerts (unused).
- [[InventoryOpeningBalances]] — Documents that load initial on-hand stock quantities and values at go-live (empty — opening stock loaded another way).
- [[InventoryPostings]] — Posts the stock differences found by inventory countings into stock and G/L (unused).
- [[ItemImages]] — Attachment-style endpoint to fetch or replace the picture stored on an item master record (keyed by ItemCode, no collection listing).
- [[PackagesTypes]] — Master list of packaging types (box, pallet, etc.) referenced when packing delivery documents (unused).

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[AlternativeItemsService]] — Manages alternative/substitute item mappings so a replacement item can be offered when the original is unavailable.
- [[BinLocationAttributesService]] — Lists the definable attribute dimensions used to classify warehouse bin locations.
- [[BinLocationFieldsService]] — Lists the field/segment definitions that make up bin location codes in bin-managed warehouses.
- [[BinLocationsService]] — RPC list access to warehouse bin locations (the physical storage slots inside bin-enabled warehouses).
- [[CashFlowLineItemsService]] — Lists the cash flow line item categories used to classify postings for cash flow statement reporting.
- [[DashboardPackagesService]] — Imports analytics dashboard packages into the B1 cockpit (admin utility, not business data).
- [[IntegrationPackagesConfigureService]] — Lists/configures integration framework packages installed on the system (admin utility).
- [[InventoryCountingsService]] — RPC list access to physical inventory counting documents used for stock-take reconciliation.
- [[InventoryGenEntryService]] — Handles approval workflow steps for Goods Receipt (inventory general entry) documents.
- [[InventoryGenExitService]] — Handles approval workflow steps for Goods Issue (inventory general exit) documents.
- [[InventoryOpeningBalancesService]] — RPC list access to inventory opening balance documents that seed initial stock quantities and values.
- [[InventoryPostingsService]] — RPC access to inventory posting documents that book count differences after a stock take.
- [[InventoryTransferRequestsService]] — Handles approval workflow steps for inventory transfer request documents between warehouses.
- [[PickListsService]] — Closes pick lists and updates released stock allocations in the warehouse pick-and-pack process.
- [[StockTransferDraftService]] — Handles approval workflow steps for stock transfer draft documents.
- [[StockTransferService]] — Handles approval workflow steps for posted inter-warehouse stock transfer documents.
- [[UnitOfMeasurementGroupsService]] — RPC list access to UoM groups that define conversion rules between base and alternate units for items.
- [[UnitOfMeasurementsService]] — RPC list access to the master list of units of measure (e.g. litre, carton, piece).
- [[WarehouseSublevelCodesService]] — Lists sublevel codes used to structure bin location hierarchies within bin-managed warehouses.
