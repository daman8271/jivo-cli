# SAP Business One Service Layer — Inventory & Warehouse (part 2)

Reference for the **Inventory & Warehouse (part 2)** domain: 11 Service Layer
services covering price lists and special prices, serial-number details, stock
takings and stock transfers (posted + drafts), units of measurement (and their
groups), and warehouses (with their locations and bin sub-level codes).

**11 services total — all 11 are readable entities (each exposes a `GET`).** No
POST-only function services in this bucket, though two transfer entities also
carry POST action sub-operations (`Cancel`, `Close`, `SaveDraftToDocument`).

All descriptions, operations, and field names below come from the bundled
`catalog/services.json` and `raw/service-layer-api-reference.html` (paths shown at
`/b1s/v1/…` exactly as the reference documents them; the `sapb1` CLI handles the
version for you). Nothing here is invented — where the reference gives no field,
it says "query live `$metadata`". Where a one-line purpose extends beyond the
reference's terse text, it is marked *(inferred)*.

Legend:
- **readable ENTITY** — exposes `GET` (collection + by-id); queryable with OData `$select/$filter/$orderby` and the `sapb1 query` tool.
- **function/action Service** — POST-only RPC-style call; not OData-queryable.

> Tip: run `sapb1 fields <Entity>` for the exact field list your company DB returns.

---

## PriceLists

1. **Purpose:** Manages price lists in the Inventory module — an item can carry several prices, each based on a different price list (purchase, sales, distributor, and so on).
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET PriceLists` (collection)
   - `GET PriceLists(id)` (by-id)
   - `POST PriceLists`
   - `PATCH PriceLists(id)`
   - `DELETE PriceLists(id)`
4. **Fields (real):** `PriceListNo`, `RoundingMethod`, `GroupNum`, `BasePriceList`.

```
GET /b1s/v1/PriceLists?$select=PriceListNo,RoundingMethod,GroupNum,BasePriceList&$top=20
sapb1 query PriceLists --select PriceListNo,RoundingMethod,GroupNum,BasePriceList --top 20
```

---

## SerialNumberDetails

1. **Purpose:** Read/update the detail records of item serial numbers. *(inferred — reference text is terse: "This entity enables you to manipulate 'SerialNumberDetails'.")*
2. **Type:** readable ENTITY (note: `GET` + `PATCH` only — no create/delete).
3. **Operations:**
   - `GET SerialNumberDetails` (collection)
   - `GET SerialNumberDetails(id)` (by-id)
   - `PATCH SerialNumberDetails(id)`
4. **Fields (real):** `DocEntry`, `ItemCode`, `ItemDescription`.

```
GET /b1s/v1/SerialNumberDetails?$select=DocEntry,ItemCode,ItemDescription&$top=20
sapb1 query SerialNumberDetails --select DocEntry,ItemCode,ItemDescription --top 20
```

---

## SpecialPrices

1. **Purpose:** Manages a discount for a specific item in a specific price list — the discount can apply to one business partner or to all business partners.
2. **Type:** readable ENTITY (composite key: `CardCode` + `ItemCode`).
3. **Operations:**
   - `GET SpecialPrices` (collection)
   - `GET SpecialPrices(id)` (by-id)
   - `POST SpecialPrices`
   - `PATCH SpecialPrices(id)`
   - `DELETE SpecialPrices(id)`
4. **Fields (real):** `ItemCode`, `CardCode`, `Price`.

```
GET /b1s/v1/SpecialPrices?$select=ItemCode,CardCode,Price&$top=20
sapb1 query SpecialPrices --select ItemCode,CardCode,Price --top 20
```

---

## StockTakings

1. **Purpose:** Read/post stock-count (physical inventory) records per item and warehouse. *(inferred — reference text is terse: "This entity enables you to manipulate 'StockTakings'.")*
2. **Type:** readable ENTITY (composite key: `ItemCode` + `WarehouseCode`).
3. **Operations:**
   - `GET StockTakings` (collection)
   - `GET StockTakings(id)` (by-id)
   - `POST StockTakings`
   - `PATCH StockTakings(id)`
   - `DELETE StockTakings(id)`
4. **Fields (real):** `ItemCode`, `WarehouseCode`, `Counted`.

```
GET /b1s/v1/StockTakings?$select=ItemCode,WarehouseCode,Counted&$top=20
sapb1 query StockTakings --select ItemCode,WarehouseCode,Counted --top 20
```

---

## StockTransferDrafts

1. **Purpose:** Draft (unposted) inventory-transfer documents that can later be saved to a posted transfer. *(inferred — reference text is terse: "This entity enables you to manipulate 'StockTransferDrafts'.")*
2. **Type:** readable ENTITY (with POST action sub-operations).
3. **Operations:**
   - `GET StockTransferDrafts` (collection)
   - `GET StockTransferDrafts(id)` (by-id)
   - `POST StockTransferDrafts`
   - `PATCH StockTransferDrafts(id)`
   - `POST StockTransferDrafts(id)/Cancel`
   - `POST StockTransferDrafts(id)/Close`
   - `POST StockTransferDrafts(id)/SaveDraftToDocument`
4. **Fields (real):** `DocEntry`, `Series`, `Printed`.

```
GET /b1s/v1/StockTransferDrafts?$select=DocEntry,Series,Printed&$top=20
sapb1 query StockTransferDrafts --select DocEntry,Series,Printed --top 20
```

---

## StockTransfers

1. **Purpose:** Represents transfer records of items from one warehouse to another.
2. **Type:** readable ENTITY (with POST action sub-operations).
3. **Operations:**
   - `GET StockTransfers` (collection)
   - `GET StockTransfers(id)` (by-id)
   - `POST StockTransfers`
   - `PATCH StockTransfers(id)`
   - `DELETE StockTransfers(id)`
   - `POST StockTransfers(id)/Cancel`
   - `POST StockTransfers(id)/Close`
4. **Fields (real):** `DocEntry`, `Series`, `Printed` (header level; line-level source/target warehouse fields live on the transfer's lines collection — query live `$metadata`).

```
GET /b1s/v1/StockTransfers?$select=DocEntry,Series,Printed&$top=20
sapb1 query StockTransfers --select DocEntry,Series,Printed --top 20
```

---

## UnitOfMeasurementGroups

1. **Purpose:** Manages groups of units of measurement (the conversion sets an item's UoMs belong to). *(inferred — reference text is terse: "This entity enables you to manipulate 'UnitOfMeasurementGroups'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET UnitOfMeasurementGroups` (collection)
   - `GET UnitOfMeasurementGroups(id)` (by-id)
   - `POST UnitOfMeasurementGroups`
   - `PATCH UnitOfMeasurementGroups(id)`
   - `DELETE UnitOfMeasurementGroups(id)`
4. **Fields (real):** `AbsEntry`, `Code`, `Name`.

```
GET /b1s/v1/UnitOfMeasurementGroups?$select=AbsEntry,Code,Name&$top=20
sapb1 query UnitOfMeasurementGroups --select AbsEntry,Code,Name --top 20
```

---

## UnitOfMeasurements

1. **Purpose:** Manages individual units of measurement (each UoM definition). *(inferred — reference text is terse: "This entity enables you to manipulate 'UnitOfMeasurements'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET UnitOfMeasurements` (collection)
   - `GET UnitOfMeasurements(id)` (by-id)
   - `POST UnitOfMeasurements`
   - `PATCH UnitOfMeasurements(id)`
   - `DELETE UnitOfMeasurements(id)`
4. **Fields (real):** `AbsEntry`, `Code`, `Name`.

```
GET /b1s/v1/UnitOfMeasurements?$select=AbsEntry,Code,Name&$top=20
sapb1 query UnitOfMeasurements --select AbsEntry,Code,Name --top 20
```

---

## WarehouseLocations

1. **Purpose:** Defines the geographical locations of warehouses.
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET WarehouseLocations` (collection)
   - `GET WarehouseLocations(id)` (by-id)
   - `POST WarehouseLocations`
   - `PATCH WarehouseLocations(id)`
   - `DELETE WarehouseLocations(id)`
4. **Fields (real):** `Code`, `Name`, `LSTVATNumber`.

```
GET /b1s/v1/WarehouseLocations?$select=Code,Name,LSTVATNumber&$top=20
sapb1 query WarehouseLocations --select Code,Name,LSTVATNumber --top 20
```

---

## Warehouses

1. **Purpose:** Represents the information of warehouses in the Inventory module.
2. **Type:** readable ENTITY (key: `WarehouseCode`, e.g. `Warehouses('w001')`).
3. **Operations:**
   - `GET Warehouses` (collection)
   - `GET Warehouses(id)` (by-id)
   - `POST Warehouses`
   - `PATCH Warehouses(id)`
   - `DELETE Warehouses(id)`
4. **Fields (real):** `WarehouseCode`, `Street`, `ZipCode`, `StockInflationOffsetAccount`.

```
GET /b1s/v1/Warehouses?$select=WarehouseCode,Street,ZipCode,StockInflationOffsetAccount&$top=20
sapb1 query Warehouses --select WarehouseCode,Street,ZipCode,StockInflationOffsetAccount --top 20
```

---

## WarehouseSublevelCodes

1. **Purpose:** Manages the bin/sub-level codes that subdivide a warehouse into storage sub-levels. *(inferred — reference text is terse: "This entity enables you to manipulate 'WarehouseSublevelCodes'.")*
2. **Type:** readable ENTITY.
3. **Operations:**
   - `GET WarehouseSublevelCodes` (collection)
   - `GET WarehouseSublevelCodes(id)` (by-id)
   - `POST WarehouseSublevelCodes`
   - `PATCH WarehouseSublevelCodes(id)`
   - `DELETE WarehouseSublevelCodes(id)`
4. **Fields (real):** `WarehouseSublevel`, `Code`, `Description`.

```
GET /b1s/v1/WarehouseSublevelCodes?$select=WarehouseSublevel,Code,Description&$top=20
sapb1 query WarehouseSublevelCodes --select WarehouseSublevel,Code,Description --top 20
```
