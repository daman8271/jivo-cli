# distributor-stock

DB: SQL Server `DSR_V6`, schema `dbo`. Subsystem #12 of the DSR model. All relationships below are
convention-only (the schema declares essentially no FKs) — join defensively and always bound date ranges.

## 1. Overview

Distributors and super-stockists are the tier that supplies retailers. This subsystem is where the field
force **declares and reconciles what stock a distributor is holding**, so the company can judge sell-in vs
sell-out and reorder pressure. A Sales Officer (or promoter) visiting a distributor snaps the distributor's
current stock as a dated, GPS-tagged **header** (`tbl_distributorStock`) with per-SKU **lines**
(`tbl_distStockProducts`), optionally attaching a photo of the physical bill/stock sheet
(`tbl_distributorBills`). A running **stock ledger** (`tbl_stockLedger`) records every box movement
(Opening / in / out) per distributor per SKU so a live on-hand can be derived. A separate monthly
snapshot table (`tbl_monthlystock`) holds the per-distributor, per-item closing boxes/quantity used for
month-end reporting. `tbl_distributorShopMap` records which retail shops belong under which distributor.
(The broader subsystem also contains `tbl_distorders` and `tbl_distmappings`, out of scope here.)

Distributors are **not** a separate master — they live in `tbl_retailers` (which holds Shop / Distributor /
Modern Store in one table). So `distId` throughout this subsystem points at `tbl_retailers.retailerId`.

## 2. Tables

### tbl_distributorStock — 18,767 rows · PK `distStockId`
Header: one row per stock-declaration visit to one distributor on one date.
- `distStockId` — PK, referenced by the line/bill/ledger tables.
- `distId` — the distributor outlet → `tbl_retailers.retailerId`.
- `distName`, `distAddress` — denormalised copy of the distributor's name/address at capture time.
- `personId` — who captured it → `tbl_salesperson.personId`; `personName` denormalised.
- `personType` — role string, e.g. `"SalesPerson"` (vs promoter).
- `stockDate` — datetime of capture (real timestamp; watch `1899-12-30`/`1900-01-01` empty sentinels).
- `lotitude`, `longitude` — GPS of the capture (note the misspelling `lotitude` = latitude), text.
- `remarks` — free text, usually empty.
- `ApprovedStatus` — int approval flag (`1` = approved in samples); `ApprovedBy` — approver, e.g. `"System"`.
- `deleted` / `deletedby` / `deletedOn` — soft-delete (filter `deleted = 0`; empty `deletedOn` = `1900-01-01`).

### tbl_distStockProducts — 255,106 rows · PK none declared (keyed by `distStockId` + `productId`)
Line items: the per-SKU quantities inside one stock header.
- `distStockId` — parent header → `tbl_distributorStock.distStockId`.
- `productId` — SKU → `tbl_item.itemId`; `productName` denormalised (e.g. `"1LTR Soyabean Pouch"`).
- `productQuantity` — pack size / units-per-pack for that SKU line (e.g. 15 for 15LTR, 1 for 1LTR).
- `productMrp` — MRP per unit (int, often null); `totalMrp` — line MRP value (float, often null).
- `boxes` — number of cases/boxes counted.
- `totalPieces` / `totalQuantity` — pieces on hand (boxes × pieces-per-case); frequently equal.
- `deleted` / `deletedBy` / `deletedOn` — soft-delete, but **usually null here** (treat `null` as live;
  filter `(deleted = 0 OR deleted IS NULL)`).

### tbl_distributorBills — 8,750 rows · PK `id` (per columns.tsv; not in primary_keys.tsv)
Photo attachments for a stock/primary declaration.
- `id` — row id.
- `stockId` — the parent id → `tbl_distributorStock.distStockId` (when `stockType` is stock).
- `stockType` — which flow the bill belongs to: `"stock"` (distributor stock) or `"primary"` (primary sale
  upload). Decode: filter `stockType = 'stock'` to tie to this subsystem.
- `billUrl` — filename of the uploaded bill image (e.g. `47-20-8-121-1632122436743.jpg`), served from the
  bills image store; the prefix looks like `person-dd-mm-yy-epoch`.

### tbl_stockLedger — 21,751 rows · PK `ledgerId`
Running box-movement ledger — the auditable source for deriving live on-hand per distributor per SKU.
- `ledgerId` — PK.
- `distId` — distributor → `tbl_retailers.retailerId`.
- `distStockId` — the originating stock header → `tbl_distributorStock.distStockId`.
- `productId` — SKU → `tbl_item.itemId`.
- `boxes` — signed/quantity of boxes moved for this entry.
- `movementType` — text reason, e.g. `"Opening"` (also expect inbound/primary and outbound/secondary types).
- `referenceId` — id of the source document driving the movement (order/sale row); nullable.
- `uploadedBy` — actor string, e.g. `"System"`; `createdOn` — datetime.
- `deleted` — soft-delete (filter `deleted = 0`).

### tbl_monthlystock — 6,141 rows · PK none declared (keyed by `distid` + `stockdate` + `itemid`)
Month-end closing snapshot per distributor per SKU. (`tbl_monthlystock_bak`, 1,732 rows, is an archive twin.)
- `id` — surrogate row id (not declared PK).
- `distid` — distributor → `tbl_retailers.retailerId`.
- `stockdate` — **date only, first of the month** (e.g. `2023-11-01` = the November snapshot).
- `itemid` — SKU → `tbl_item.itemId`.
- `boxes` / `quantity` — decimal closing boxes and quantity (often `0.00`).
- No delete columns — treat every row as live.

### tbl_distributorShopMap — 28 rows · PK `Id`
Which retail shops sit under which distributor (distributor→shop coverage map). Sparse (only 28 rows).
- `Id` — PK.
- `distId` — distributor → `tbl_retailers.retailerId`.
- `shopId` — the retail outlet → `tbl_retailers.retailerId`.
- `deleted` / `deletedBy` / `deletionDate` — soft-delete (filter `deleted = 0`).

## 3. Linkages

- `personId` (`tbl_distributorStock`) → `tbl_salesperson.personId` — the SO/promoter who captured the stock.
- `distId` / `distid` (all six tables) → `tbl_retailers.retailerId` — distributors live in the retailer
  master (outlet type = Distributor). `distName`/`distAddress` are denormalised copies.
- `shopId` (`tbl_distributorShopMap`) → `tbl_retailers.retailerId` — the covered retail outlet.
- `productId` / `itemid` (`tbl_distStockProducts`, `tbl_stockLedger`, `tbl_monthlystock`) → `tbl_item.itemId`.
- `distStockId` — internal spine: `tbl_distributorStock` (header) ← `tbl_distStockProducts`,
  `tbl_stockLedger`, and `tbl_distributorBills.stockId` (lines / ledger / photo).
- `referenceId` (`tbl_stockLedger`) → source doc in primary-sales / field-sales / `tbl_distorders`.
- Monthly rows key on `distid` + `stockdate` (month-first) + `itemid` (parallels the person+month/year
  convention used elsewhere in DSR, but keyed on distributor not person).

## 4. Portal mapping

| Portal page | Reads | Writes |
|---|---|---|
| **Distributor Stock** (list / view stock declarations, drill to SKU lines + bill photo) | `tbl_distributorStock` + `tbl_distStockProducts` (lines), `tbl_distributorBills` (`stockType='stock'`), joined to `tbl_retailers`/`tbl_salesperson`/`tbl_item` for names | approve sets `ApprovedStatus`/`ApprovedBy`; delete sets `deleted=1`, `deletedby`, `deletedOn` |
| **Stock Ledger / Distributor On-hand report** | `tbl_stockLedger` (sum boxes by dist+SKU, `movementType`) | ledger rows written by stock/order/sale events |
| **Monthly Stock report** | `tbl_monthlystock` (per-month closing by distributor + item) | month-end snapshot job |
| **Distributor → Shop mapping** | `tbl_distributorShopMap` joined to `tbl_retailers` | map/unmap sets `deleted` |

## Proposed dsr commands

- **`dsr dist-stock`** — list distributor stock declarations (headers) in a window.
  Flags: `--from`, `--to`, `--salesperson <personId>`, `--distributor <distId>`, `--approved`.
  ```sql
  SELECT ds.distStockId, ds.stockDate, ds.distId, ds.distName,
         ds.personId, ds.personName, ds.ApprovedStatus
  FROM tbl_distributorStock ds
  WHERE ds.deleted = 0
    AND ds.stockDate BETWEEN @from AND @to        -- exclude 1899-12-30/1900-01-01 sentinels
    AND (@distId    IS NULL OR ds.distId   = @distId)
    AND (@personId  IS NULL OR ds.personId = @personId)
    AND (@approvedOnly = 0 OR ds.ApprovedStatus = 1)
  ORDER BY ds.stockDate DESC;
  ```

- **`dsr dist-stock-lines`** — SKU-level stock inside one declaration (or a distributor).
  Flags: `--stock-id <distStockId>` (or `--distributor`), `--from`, `--to`.
  ```sql
  SELECT p.distStockId, p.productId, p.productName,
         p.boxes, p.totalPieces, p.totalQuantity, p.totalMrp
  FROM tbl_distStockProducts p
  JOIN tbl_distributorStock ds ON ds.distStockId = p.distStockId AND ds.deleted = 0
  WHERE (p.deleted = 0 OR p.deleted IS NULL)        -- lines usually have NULL delete flags
    AND (@stockId IS NULL OR p.distStockId = @stockId)
    AND (@distId  IS NULL OR ds.distId     = @distId)
    AND (@from    IS NULL OR ds.stockDate BETWEEN @from AND @to)
  ORDER BY p.distStockId, p.productName;
  ```

- **`dsr dist-onhand`** — derive live on-hand boxes per distributor × SKU from the ledger.
  Flags: `--distributor <distId>`, `--item <productId>`, `--as-of <date>`.
  ```sql
  SELECT l.distId, l.productId, SUM(l.boxes) AS onHandBoxes
  FROM tbl_stockLedger l
  WHERE l.deleted = 0
    AND (@distId IS NULL OR l.distId    = @distId)
    AND (@itemId IS NULL OR l.productId = @itemId)
    AND (@asOf   IS NULL OR l.createdOn <= @asOf)
  GROUP BY l.distId, l.productId
  ORDER BY l.distId, l.productId;
  ```

- **`dsr monthly-stock`** — month-end closing stock per distributor × item.
  Flags: `--month <YYYY-MM>`, `--distributor <distId>`, `--item <itemId>`.
  ```sql
  SELECT m.distid, m.stockdate, m.itemid, m.boxes, m.quantity
  FROM tbl_monthlystock m
  WHERE (@month IS NULL OR m.stockdate = DATEFROMPARTS(@year, @mon, 1))  -- snapshot dated month-first
    AND (@distId IS NULL OR m.distid  = @distId)
    AND (@itemId IS NULL OR m.itemid  = @itemId)
  ORDER BY m.stockdate DESC, m.distid, m.itemid;
  ```

- **`dsr dist-shops`** — retail shops mapped under a distributor.
  Flags: `--distributor <distId>`.
  ```sql
  SELECT dsm.distId, dsm.shopId
  FROM tbl_distributorShopMap dsm
  WHERE dsm.deleted = 0
    AND (@distId IS NULL OR dsm.distId = @distId)
  ORDER BY dsm.distId, dsm.shopId;
  ```
