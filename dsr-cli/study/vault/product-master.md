# DSR subsystem — Product Master (SKU catalogue)

**Portal menu:** Masters > Item
**DB:** `DSR_V6` (SQL Server)
**Tables in scope:** `tbl_item`, `tbl_itemType`, `tbl_UOMMaster`, `tbl_ItemGroupName`, `tbl_flavours`, `tbl_ItemImages`
*(all counts / decodes below were verified live with `./dsr query …` on 2026-07-29)*

---

## 1. Overview

This is the SKU catalogue every other DSR module hangs off. JIVO Wellness sells edible oils
(Canola, Mustard, Olive/Pomace/Extra Virgin, Soya, Sunflower, Rice Bran, Groundnut, Cotton Seed,
Sesame, Coconut), Desi Ghee, Spices/Chai, and a beverages line (Cola, Lemon, Jeera, Soda, Peach,
Wheatgrass). Each sellable pack — "1LTR EXTRA LIGHT", "869GM MUSTARD", "15 KG MUSTARD TIN",
"250ML Jeera PET" — is one row in `tbl_item`.

What the master controls:

- **What the field app shows.** Three independent visibility switches decide whether a SKU appears
  in the Sales Officer app (`visibleToSo`), the Promoter app (`visibleToPromoter`) and the
  retailer-facing app/portal (`isVisibleToRetailer`).
- **How quantities convert.** `piecesPerCase` is the bottles-per-carton factor. Secondary-sales
  rows downstream are captured in **pieces/bottles**, so any "cases sold" figure has to divide by
  this column (same trap flagged in the SAP vault: qty is per bottle, not per carton).
- **Tax + pricing metadata.** `gst`, `HSNCode`, `MRP`, `price` (mostly unpopulated — see caveats).
- **Scheme / loyalty behaviour.** `isScheme` marks combo & gift SKUs used by the scheme engine;
  `isRedeemable` + `cashRate` + `isCashback` mark SKUs redeemable against loyalty points.
- **Classification for reporting.** `itemType` → oil variant (Canola / Mustard / Olive …),
  `itemGroup` → pack-size bucket (1 LTR / 5 LTR / 15 LTR …), `tbl_flavours` → beverage flavour and
  glass-vs-PET packaging.
- **Artwork.** `tbl_ItemImages` (SKU photo shown in the app) and the legacy `imageBanner` column.

It is a small, hand-curated table (158 live SKUs) that drives ~47 M transaction rows.

---

## 2. Tables

### 2.1 `tbl_item` — the SKU master

| | |
|---|---|
| Rows | **333 total, 158 live** (`deleted = 0`) |
| PK | `Id` (int) |
| Soft delete | `deleted` (int, 0/1) + `deletedBy`, `deletionDate`, `deleteReason` |
| Audit | `CreatedBy` (person *name* string, e.g. `HS`, `NANCY BIJJI`, `Mukesh`), `CreatedOn` — live rows span 2022-05-31 → 2026-07-09 |

Meaningful columns:

| Column | Type | Meaning / verified reality |
|---|---|---|
| `Id` | int | PK. **This is the `productId` / `itemId` used everywhere downstream.** |
| `itemName` | nvarchar(100) | Display name, e.g. `1LTR EXTRA LIGHT`, `15 KG  MUSTARD TIN ` (note trailing/double spaces — always `LTRIM(RTRIM())` when matching). |
| `quantity` | float | Pack size in L/Kg. Mostly clean (`0.869` for 869 GM, `1` for 1 LTR, `4` for 4 LTR) but **not trustworthy**: `12KG SOYA` = 13, `4L Rice Bran` = 20, `13 Kg KIRPA DESI GHEE TIN` = 14.3. Treat as advisory; parse `itemName` if you need exact pack size. |
| `piecesPerCase` | int | Bottles/pouches per carton. Populated on all 158 live rows. **Use this to convert the piece-level sales rows into cases.** |
| `UOM` | int | FK → `tbl_UOMMaster.ID`. All 158 live rows = `1` = `PCS`. 0 broken refs. |
| `itemType` | int | FK → `tbl_itemType.Id` — the oil/beverage variant. 0 broken refs on live rows. |
| `itemGroup` | varchar(50) | Pack-size bucket. **Stores the group NAME as text, not the Id** — it joins `tbl_ItemGroupName.ItemGroupName`, *not* `.Id`. 123/158 live rows are NULL; values seen: `1 LTR`(17), `5 LTR`(4), `2 LTR`(3), `15 LTR`(2), `3 LTR`(1), `100 ML`(1), plus junk `COMMODITY`(2), `1`(4), `0`(1). Only 28 rows actually join to the master. |
| `itemCode` | nvarchar(100) | Sparse internal code (35/158 live). Numeric-ish strings (`852`, `969`, `435`). Not the SAP code. |
| `SAPID` | nvarchar(80) | **100 % NULL — 0 of 333 rows populated.** There is *no* live SAP item-code bridge in DSR; mapping DSR SKUs to SAP `Items` must be done by name. |
| `MRP` | float | 82/158 non-null but **only 3 rows are > 0** — effectively unused. |
| `price` | decimal(19,6) | 1/158 non-null — unused. |
| `gst` | decimal(19,6) | GST %: `5.00` (92 rows, oils), `12.00` (58, beverages), `18.00` (3), `0.00` (4), NULL (1). |
| `HSNCode` | varchar(20) | 156/158 non-null but only **6 rows hold a real HSN**; the rest are `'0'` or `''`. |
| `visibleToSo` | bit | Shown in the Sales-Officer app. 153/158 live rows = 1. |
| `visibleToPromoter` | bit | Shown in the Promoter app. 123/158. |
| `isVisibleToRetailer` | bit | Shown in the retailer-facing app. only 11/158. |
| `isScheme` | bit | Scheme / combo / giftpack SKU. 7 live rows (`Cola`, `Lemon`, `Orange`, `Wheatgrass Giftpack`, `Tonic Water Glass 200ml`, `4LTR Coldpress + Flask`). |
| `isRedeemable` | bit | Loyalty-redeemable SKU. **1** live row (`770 GM SOYA POUCH`). |
| `isCashback` | int | 93 rows = 0, 65 NULL — never set to anything but 0. Dormant. |
| `cashRate` | decimal(19,6) | Loyalty cash rate; `0.000000` on every live row. Dormant. |
| `status` | nchar(20) | Legacy active flag, **space-padded string**: `'True      '` (157) / `'False     '` (1). Compare with `LTRIM(RTRIM(status)) = 'True'`, never `status = 'True'`. |
| `state` | int | 0 on 157 live rows, NULL on 1. **Not a state/region id** — the real per-state SKU mapping lives in `tbl_itemStates` (see §3). Ignore this column. |
| `shortDescription`, `longDescription` | varchar | Boilerplate placeholders on old rows (`"This is short Description"`, `"a"`). |
| `imageBanner` | varchar(max) | Legacy single image URL (old `122.160.78.189:83` host). Superseded by `tbl_ItemImages`. |

### 2.2 `tbl_itemType` — product variant lookup

| | |
|---|---|
| Rows | **23, all live** (`deleted = 0` on every row) |
| PK | `Id` |
| Columns | `typeName` (nvarchar 40), `deleted` (bit), `createdBy/createdOn/deletedBy/deletedOn` (all NULL) |

Full decode (verified — note gaps at 10, 17, 23, 26, 27):

| Id | typeName | | Id | typeName |
|---|---|---|---|---|
| 1 | CANOLA | | 14 | Cotton Seed |
| 2 | Extra Light | | 15 | GroundNut |
| 3 | Wheatgrass | | 16 | Coconut |
| 4 | MUSTARD | | 18 | Rice Bran |
| 5 | Pomace | | 19 | OLIVE |
| 6 | Desi Ghee | | 20 | JEERA |
| 7 | GOLD | | 21 | SODA |
| 8 | Extra Virgin | | 22 | PEACH |
| 9 | SOYABEAN | | 24 | YELLOW MUSTARD |
| 11 | SUNFLOWER | | 25 | `SESAME OIL ` (trailing space) |
| 12 | Coffee | | 28 | Spices |
| 13 | Beverages | | | |

### 2.3 `tbl_UOMMaster` — unit of measure

| | |
|---|---|
| Rows | **2** |
| PK | `ID` (capital D — unlike every other table's `Id`) |
| Columns | `UOMName`, `deleted` (bit), audit columns (all NULL) |

Decode: `1 = PCS`, `2 = '2'` (garbage row, unused). Every live item uses UOM 1. Effectively a
vestigial lookup — treat all quantities as pieces.

### 2.4 `tbl_ItemGroupName` — pack-size group lookup

| | |
|---|---|
| Rows | **6** |
| PK | `Id` |
| Columns | `ItemGroupName` only — **no `deleted` column** |

Values: `1 = 1 LTR`, `2 = 2 LTR`, `3 = 3 LTR`, `4 = 5 LTR`, `5 = 15 LTR`, `6 = 100 ML`.

⚠ `tbl_item.itemGroup` holds the **name**, so join on `g.ItemGroupName = i.itemGroup`
(28 live items match). Joining on `Id` returns nothing.

### 2.5 `tbl_flavours` — beverage flavour / packaging attributes

| | |
|---|---|
| Rows | **43** (40 point at live items, 3 at deleted items; 0 orphans) |
| PK | `Id` |
| Grain | one row per beverage SKU |

| Column | Meaning |
|---|---|
| `itemid` | → `tbl_item.Id` (verified: 0 orphans) |
| `flavours` | varchar(30) — `Cola`, `Lemon`, `Jeera (24 pack)`, `Orange`, … |
| `itemtype` | varchar(30) — **the item-type Id stored as a string**: `'3'` (Wheatgrass, 24 rows) and `'13'` (Beverages, 19 rows). Cast to int to join `tbl_itemType.Id`. |
| `options` | varchar(7) — packaging: `PET` (25) / `GLASS` (18). |

No `deleted` column — liveness comes from the parent item.

### 2.6 `tbl_ItemImages` — SKU artwork

| | |
|---|---|
| Rows | **158 total, 153 live** (`deleted = 0`) |
| PK | `imageId` |
| Columns | `productId` (→ `tbl_item.Id`), `imageURL` (varchar max), `deleted` (int) |

153 live rows over 152 distinct products, so ~1 image per SKU (one SKU has 2). **1 live orphan**:
`imageId = 119`, `productId = 395` (`770SOYAPOUCH.jpg`) — the item row no longer exists.
URLs are on the portal host, e.g.
`http://dsr.jivocanola.com/Uploads/SKUPics/EXTRA%20LIGHT%202LTR.jpg`.

---

## 3. Linkages (verified)

The DB declares **no foreign keys at all** (`foreign_keys.tsv` is empty) — every relationship below
is convention-only and was confirmed by running the join.

Inside the subsystem:

| From | To | Verified |
|---|---|---|
| `tbl_item.itemType` | `tbl_itemType.Id` | 0 broken refs on 158 live items |
| `tbl_item.UOM` | `tbl_UOMMaster.ID` | 0 broken refs |
| `tbl_item.itemGroup` (**text**) | `tbl_ItemGroupName.ItemGroupName` | 28 live matches; join by Id yields 0 |
| `tbl_flavours.itemid` | `tbl_item.Id` | 43/43 match, 0 orphans |
| `tbl_flavours.itemtype` (**text**) | `tbl_itemType.Id` | values `'3'`,`'13'` |
| `tbl_ItemImages.productId` | `tbl_item.Id` | 152/153 live match, 1 orphan (`productId 395`) |

Out to other subsystems — `tbl_item.Id` is referenced as `productId` or `itemId`:

| Table | Column | Subsystem | Verified |
|---|---|---|---|
| `tbl_ProductsSold` | `productId` | SO secondary sales (line items) | 685 540 rows / 259 distinct products; orphans are **only sentinels** `0` (34 122) and `-1` (12), plus 2 stray rows (ids 37, 395). It also **denormalises** `productName`, `productQuantity`, `itemType`, `isScheme`, `UOM` at sale time — those are point-in-time snapshots and can drift from `tbl_item`; join back to `tbl_item` for current attributes. Its `deleted` column is **NULL** on live rows (use `ISNULL(deleted,0)=0`). |
| `tbl_ProductsSoldPromoter` | `productId` | Promoter sales |  |
| `tbl_SchemeProductsSold` | `productId` | Scheme/free-goods lines | 423 761 rows, 36 orphans |
| `tbl_retailerStock` | `itemId` | Retailer stock audit | 585 602 rows, 129 orphans |
| `tbl_distStockProducts`, `tbl_distPrimaryProducts`, `tbl_distorders.itemid` | | Distributor stock & orders | |
| `tbl_primary_sales.itemid`, `tbl_monthlystock.itemid`, `tbl_stockLedger.productId` | | Primary sales / stock ledger | |
| `tbl_returnItem.itemId` | | Returns | |
| `tbl_CC_OrderDetails.productId` | | Call-centre orders | |
| `ActualItemSold.ProductId`, `ActualItemSoldSuper.ProductId` | | Reporting views/tables | |
| `tbl_itemStates.itemId` | | **Per-state SKU availability**: `(Id, itemId, stateId)` where `stateId` → `tbl_states.stateId`. This — not `tbl_item.state` — is how a SKU is restricted to regions. Sales-person state mapping is the parallel `tbl_PersonState(personId, stateId)`. |

Note the sentinel `productId = 0 / -1` rows: **always** inner-join or filter `productId > 0` when
aggregating sales by SKU, or you silently carry 34 k unattributable lines.

There is **no `SAPID` bridge** (column is 100 % NULL), so reconciling DSR secondary sales against
SAP B1 `Items` currently requires name matching.

---

## 4. Portal mapping

| Portal page | Reads | Writes |
|---|---|---|
| **Masters > Item** (list / add / edit SKU) | `tbl_item` + `tbl_itemType`, `tbl_UOMMaster`, `tbl_ItemGroupName` for dropdowns | `tbl_item`; delete sets `deleted=1`, `deletedBy`, `deletionDate`, `deleteReason` |
| Masters > Item — image upload | `tbl_ItemImages` | `tbl_ItemImages` (URLs under `/Uploads/SKUPics/`) |
| Masters > Item — state mapping | `tbl_itemStates`, `tbl_states` | `tbl_itemStates` |
| Masters > Item Type / UOM / Item Group (lookup maintenance) | `tbl_itemType`, `tbl_UOMMaster`, `tbl_ItemGroupName` | same |
| Beverage flavour setup | `tbl_flavours` | `tbl_flavours` |
| **Consumers (read-only):** SO app & Promoter app SKU lists (filtered by `visibleToSo` / `visibleToPromoter` / `isVisibleToRetailer` and by `tbl_itemStates`), Sales entry screens, Scheme setup, Retailer-stock capture, Distributor stock/orders, and every sales report that groups by variant or pack size | `tbl_item` (+ lookups) | — |

*(All `dsr` access is read-only; the write column above describes what the web portal does.)*

---

## 5. Ready-to-run SELECTs

**1. Live SKU catalogue, fully decoded**
```sql
SELECT i.Id,
       LTRIM(RTRIM(i.itemName))              AS itemName,
       t.typeName                            AS variant,
       COALESCE(g.ItemGroupName, i.itemGroup) AS packGroup,
       u.UOMName                             AS uom,
       i.piecesPerCase, i.quantity, i.gst, i.MRP,
       i.visibleToSo, i.visibleToPromoter, i.isVisibleToRetailer,
       i.isScheme, i.isRedeemable, i.CreatedBy, i.CreatedOn
FROM tbl_item i
LEFT JOIN tbl_itemType      t ON t.Id = i.itemType
LEFT JOIN tbl_UOMMaster     u ON u.ID = i.UOM
LEFT JOIN tbl_ItemGroupName g ON g.ItemGroupName = i.itemGroup   -- name, not Id
WHERE i.deleted = 0
ORDER BY t.typeName, i.itemName;
```

**2. SKU count and app visibility by variant**
```sql
SELECT t.typeName,
       COUNT(*)                                              AS skus,
       SUM(CASE WHEN i.visibleToSo = 1 THEN 1 ELSE 0 END)    AS in_so_app,
       SUM(CASE WHEN i.visibleToPromoter = 1 THEN 1 ELSE 0 END) AS in_promoter_app,
       SUM(CASE WHEN i.isVisibleToRetailer = 1 THEN 1 ELSE 0 END) AS in_retailer_app
FROM tbl_item i
JOIN tbl_itemType t ON t.Id = i.itemType
WHERE i.deleted = 0
GROUP BY t.typeName
ORDER BY skus DESC;
```

**3. Scheme / redeemable SKUs (the ones the scheme + loyalty engines use)**
```sql
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, t.typeName,
       i.isScheme, i.isRedeemable, i.isCashback, i.cashRate, i.piecesPerCase
FROM tbl_item i
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE i.deleted = 0 AND (i.isScheme = 1 OR i.isRedeemable = 1)
ORDER BY i.isScheme DESC, i.Id;
```

**4. Beverage SKUs with flavour + packaging**
```sql
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName,
       f.flavours, f.options AS packaging, t.typeName
FROM tbl_flavours f
JOIN tbl_item     i ON i.Id = f.itemid
LEFT JOIN tbl_itemType t ON t.Id = TRY_CAST(f.itemtype AS int)
WHERE i.deleted = 0
ORDER BY f.options, f.flavours;
```

**5. Catalogue hygiene — live SKUs missing an image, HSN or pieces-per-case**
```sql
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName,
       CASE WHEN im.productId IS NULL THEN 'no image' ELSE '' END           AS img_gap,
       CASE WHEN i.HSNCode IS NULL OR i.HSNCode IN ('', '0') THEN 'no HSN' ELSE '' END AS hsn_gap,
       CASE WHEN ISNULL(i.piecesPerCase, 0) = 0 THEN 'no pcs/case' ELSE '' END        AS ppc_gap,
       CASE WHEN i.itemGroup IS NULL THEN 'no pack group' ELSE '' END       AS grp_gap
FROM tbl_item i
LEFT JOIN (SELECT DISTINCT productId FROM tbl_ItemImages WHERE deleted = 0) im
       ON im.productId = i.Id
WHERE i.deleted = 0
  AND (im.productId IS NULL
       OR i.HSNCode IS NULL OR i.HSNCode IN ('', '0')
       OR ISNULL(i.piecesPerCase, 0) = 0
       OR i.itemGroup IS NULL)
ORDER BY i.Id;
```

**6. Secondary sales by SKU, converted to cases (last 90 days)** — the join everyone actually wants
```sql
SELECT i.Id, LTRIM(RTRIM(i.itemName)) AS itemName, t.typeName,
       SUM(ps.pieces)                                     AS pieces,
       CAST(SUM(ps.pieces) * 1.0 / NULLIF(i.piecesPerCase, 0) AS decimal(18,2)) AS cases
FROM tbl_ProductsSold ps
JOIN tbl_SalesReport sr ON sr.salesId = ps.salesId AND sr.deleted = 0
JOIN tbl_item        i  ON i.Id = ps.productId       -- inner join drops productId 0/-1 sentinels
LEFT JOIN tbl_itemType t ON t.Id = i.itemType
WHERE ISNULL(ps.deleted, 0) = 0     -- tbl_ProductsSold.deleted is NULL on live rows, not 0
  AND ps.productId > 0
  AND sr.date >= DATEADD(day, -90, CAST(GETDATE() AS date))
  AND sr.date > '1900-01-01'                        -- 1899-12-30 empty-date sentinel
GROUP BY i.Id, i.itemName, t.typeName, i.piecesPerCase
ORDER BY pieces DESC;
```
*(`tbl_ProductsSold` is the line-item child of `tbl_SalesReport` via `salesId`; quantity is in
`pieces`. See the secondary-sales vault for the rest of that table.)*

**7. Which SKUs are enabled in which states**
```sql
SELECT s.state, COUNT(*) AS skus
FROM tbl_itemStates ist
JOIN tbl_item   i ON i.Id = ist.itemId AND i.deleted = 0
JOIN tbl_states s ON s.stateId = ist.stateId
GROUP BY s.state
ORDER BY skus DESC;
```

---

## 6. Caveats to carry forward

1. **`SAPID` is empty on all 333 rows** — no SAP item bridge; match to SAP B1 `Items` by name.
2. **`itemGroup` joins by name, not Id**, and is NULL on 78 % of live SKUs.
3. **`MRP`/`price`/`HSNCode`/`cashRate`/`isCashback` are effectively unpopulated** — do not build
   pricing or tax reports on them; GST % is the one tax field that is real.
4. **`status` is space-padded `nchar(20)`** — always trim before comparing. `deleted = 0` is the
   authoritative liveness test.
5. **`quantity` is unreliable pack size**; `piecesPerCase` is reliable and is the case-conversion key.
6. **`tbl_item.state` is not a region** — use `tbl_itemStates`.
7. **Sentinel `productId` 0 / -1** in downstream sales tables; filter or inner-join.
