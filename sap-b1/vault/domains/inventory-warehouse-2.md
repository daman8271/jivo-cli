# Inventory & Warehouse (part 2)

Continuation of the inventory domain (part 2 of 2 — see [[inventory-warehouse-1]]): the warehouse network itself ([[Warehouses]] — 58 depots — plus [[WarehouseLocations]] and [[WarehouseSublevelCodes]]), pricing masters ([[PriceLists]], [[SpecialPrices]]), physical-count reconciliation ([[StockTakings]], 126.8k rows), executed movements ([[StockTransfers]], 11.7k, with [[StockTransferDrafts]] at 47.1k), serial-number traceability ([[SerialNumberDetails]]) and units of measure ([[UnitOfMeasurements]], [[UnitOfMeasurementGroups]]).

Part of the [[00-SAP-B1-Atlas]] — 11 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[StockTakings]] **(126,820 rows)** — Physical inventory count records (counted quantities per item per warehouse, with custom box/litre fields) used to reconcile book stock during stock takes.
- [[StockTransferDrafts]] **(47,115 rows)** — Draft (unposted) inter-warehouse stock transfer documents awaiting approval or conversion to actual StockTransfers.
- [[StockTransfers]] **(11,668 rows)** — Posted inventory transfer documents moving stock between warehouses (the core inter-branch/depot movement document).
- [[Warehouses]] **(58 rows)** — Warehouse master defining each stock location's address, G/L account determination, bin-location settings, and branch assignment (58 depots in JIVO oil DB).
- [[SpecialPrices]] **(22 rows)** — Customer/item-specific special price agreements that override standard price lists with discounts and validity periods.
- [[PriceLists]] **(10 rows)** — Defines the company's price lists (base list, factor, currency, validity) used to price items across sales and purchasing documents.
- [[WarehouseLocations]] **(5 rows)** — Location master for warehouses carrying Indian statutory/tax identity (GSTIN, PAN, state) plus custom e-way-bill/transport credentials per location.
- [[UnitOfMeasurementGroups]] **(4 rows)** — Groups of units of measure with conversion definitions to a base UoM, assigned to items for multi-UoM handling (e.g., bottle/box/litre).
- [[UnitOfMeasurements]] **(4 rows)** — Master catalog of individual units of measure with physical dimensions (volume, weight, size) referenced by UoM groups and items.
- [[SerialNumberDetails]] — Master records of individual item serial numbers (manufacturer/internal serial, status, expiry) for serial-managed inventory; empty in JIVO_OIL_HANADB.
- [[WarehouseSublevelCodes]] — Sublevel code values used to build bin-location hierarchies inside bin-enabled warehouses; unused (0 rows) in JIVO_OIL_HANADB.
