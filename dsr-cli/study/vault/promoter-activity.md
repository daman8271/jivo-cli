# Subsystem: promoter-activity

DB: `DSR_V6` (SQL Server). All figures verified live on **2026-07-29** with the read-only `dsr` CLI.

---

## 1. Overview

JIVO runs two parallel field forces on the same DSR app/portal:

- **Sales Officers (SO)** — beat-based secondary billing (distributor → retailer). That flow lives in
  `tbl_SalesReport` / `tbl_ProductsSold`.
- **Promoters / Merchandisers** — people **stationed inside a store** (Metro, Reliance Smart Bazar,
  D-Mart, large GT counters) whose job is to push JIVO oil off the shelf, hand out samples, and report
  what the store had and what is left. This subsystem is their mirror-image flow.

The promoter workflow, table by table:

1. Promoter marks GPS attendance (shared table `tbl_salesPersonAttendance` — no separate promoter table).
2. Promoter opens the store from their **assigned shop list** (`tbl_promoterShopMap`).
3. Per store per day the app posts a visit: a header row in **`tbl_SalesReportPromoter`** plus one line
   per SKU in **`tbl_ProductsSoldPromoter`**. Lines carry **pieces sold + openingStock / closingStock /
   sampleStock**, not billing — there is **no rate, no invoice, no distributor** on the promoter side
   (`distId` is NULL on 100% of rows; `cost`/`totalCost` are legacy and mostly empty).
4. The raw JSON body the Android app posted is archived verbatim in **`tbl_PromoterAppSalesJsonLog`**
   (GPS lat/long, accuracy, battery, provider, item array). Logging was switched on **2026-07-24**, so
   this is a new debugging/forensics table, not history.
5. Reporting hierarchy: each promoter is mapped to a supervising SO in **`tbl_soPromoterMap`**.
6. HR/onboarding scans: **`tbl_promoterAadharCards`** and **`tbl_promoterResumes`** (filenames only).

Scale: **185,646 promoter visits** (2021-10-25 → 2026-07-29) over **542 promoters** and **522 stores**;
**362,553 product lines**. Current run-rate ≈ **1,736 visits in Jul-2026 to date**.

Person types that actually appear in this data (`tbl_salesperson.PERSONTYPE`):
`PROMOTER(MT)` (modern trade), `PROMOTER(GT)`, `PROMOTER(GTW)`, `PROMOTER(MTW)`, `MERCHANDISER`,
and a handful of `SO` rows (an SO occasionally files through the promoter screen).

---

## 2. Tables (live)

### 2.1 `tbl_SalesReportPromoter` — promoter visit header (one per promoter × store × submission)
- **Rows:** 185,646 (185,626 with `deleted = 0`) · **PK:** `salesId` (int, identity-like, max 207,626)
- Date span `date`: 2021-10-25 → 2026-07-29.

| Column | Meaning |
|---|---|
| `salesId` | PK; the "visit id" that `tbl_ProductsSoldPromoter.salesId` points at |
| `date` | business date of the visit (`date` type, no sentinel seen) |
| `personId` | the promoter → `tbl_salesperson.ID` (0 orphans) |
| `retailerId` | the store → `tbl_retailers.Id` (720 live rows point at retailers that no longer exist — hard-deleted stores; use LEFT JOIN) |
| `timestamp` | exact submission datetime from the device |
| `CreatedOn` / `CreatedBy` | server insert time; `CreatedBy` is the **personId as text** (nvarchar) |
| `status` | **single value in the whole table: `'DONE'`.** Not a real enum today — treat as "submitted" |
| `imagePath` | selfie/shelf photo filename, pattern `<personId>-<d>-<m>-<yyyy>-<HHmmss>.jpg`; empty string when no photo (75,580 of 185,628 rows have one) |
| `imagepath1`, `imagepath2` | extra photo slots — **100% NULL, unused** |
| `remarks` | present in schema but **never populated** (all empty) |
| `simNo` | SIM identifier captured by the app (61,362 non-NULL, often `''`) |
| `stateId`,`zoneId`,`areaId`,`subAreaId` | geography snapshot → `tbl_states.stateId`, `tbl_zones.zoneId`, `tbl_areas.areaId`, `tbl_subArea.subAreaId`. `subAreaId` is `-1`/NULL on almost all rows (only 2,427 real) |
| `distId` | **always NULL** — promoters are not tied to a distributor |
| `personName`,`retailerName`,`state`,`zone`,`area`,`subArea`,`distributor` | denormalized name snapshots written at submit time (handy, but stale vs. the masters; `distributor`/`subArea` mostly NULL) |
| `deleted`,`deletedBy`,`deletionDate` | soft delete — filter `deleted = 0` |

> There are **no lat/long columns on the header**. Promoter GPS lives in
> `tbl_salesPersonAttendance` (attendance punch) and, since 2026-07-24, in the raw JSON log.

Ignore the backup twin `tbl_salesreportpromoter_bak`.

### 2.2 `tbl_ProductsSoldPromoter` — promoter visit lines (SKU level)
- **Rows:** 362,553 (362,502 live) · **PK:** `Id`

| Column | Meaning |
|---|---|
| `Id` | PK of the line. Beware: on 94,122 old rows `Id` happens to equal `salesId` — coincidence of a legacy load, **never join on `Id`** |
| `salesId` | FK → `tbl_SalesReportPromoter.salesId` (60 live orphan lines; use INNER JOIN for reporting) |
| `productId` | FK → `tbl_item.Id` (only 3 orphans). 313,544 lines are on items flagged `tbl_item.visibleToPromoter = 1`; 48,960 on older/unflagged items |
| `productName` | denormalized item name snapshot (case varies: `1LTR + 1LTR Coldpress` vs `1LTR + 1LTR COLDPRESS`) |
| `pieces` | **units sold in the store that day** — the primary volume metric |
| `productQuantity` | pack size in litres for one piece (e.g. `1LTR Extra Light` = 1, `1LTR + 1LTR Coldpress` = 2, a 200 ml SKU = 0.2) |
| `totalQuantity` | `pieces × productQuantity` = litres sold (verified on sample rows) |
| `openingStock`, `closingStock`, `sampleStock` | in-store stock count and samples given, **added 2023-12-06** — NULL on the 111,844 lines older than that, populated on 250,709 lines |
| `cost`, `totalCost` | legacy price fields, populated on only 48,362 lines (2021→2026-07-17) — **do not use for revenue** |
| `deleted`,`deletedBy`,`deletionDate`,`CreatedBy`,`CreatedOn` | audit/soft delete |

Top SKUs by line count: `5LTR Coldpress + 1LTR Olive` (29,593), `1LTR Extra Light` (25,437),
`5LTR Pomace` (20,924), `1LTR + 1LTR Coldpress` (18,350), `5LTR Coldpress` (17,287) — i.e. this
subsystem is dominated by the **olive-oil modern-trade push**.

### 2.3 `tbl_PromoterAppSalesJsonLog` — raw promoter-app payload archive
- **Rows:** 316 · **PK:** `id` · Window: **2026-07-24 13:50 → now**, 63 promoters. New instrumentation.
- `personId` → `tbl_salesperson.ID`; `createdOn` = server receipt time.
- `imageName` matches `tbl_SalesReportPromoter.imagePath` — **174 of 316 payloads map to a saved
  header**; the rest are retries/failed posts, which is exactly why this log exists.
- `rawJson` is a JSON **array of one object**, with `items` as a **doubly-encoded JSON string**:
  ```json
  [{"location":"121, Najafgarh Road Industrial Area, Delhi Division, 110015",
    "personId":2871,"shopId":148567,"timeStamp":"07/24/2026",
    "latitude":28.6577943,"longitude":77.144699,"simNo":null,"address":"",
    "battery":81,"GpsEnabled":"GPS","accuracy":17.19,"speed":0.026,
    "provider":"GPS","altitude":183.2,
    "items":"[{\"itemId\":278,\"sampleStock\":0,\"itemPieces\":1,\"itemQuantity\":5}]"}]
  ```
  Field mapping into the tables: `shopId` → `retailerId`, `itemId` → `productId`,
  `itemPieces` → `pieces`, `itemQuantity` → `productQuantity`, `sampleStock` → `sampleStock`.
  This is the **only place promoter GPS per sale is stored**.

### 2.4 `tbl_promoterShopMap` — which stores a promoter is allowed to work
- **Rows:** 1,423 (1,418 with `deleted = 0`), 725 distinct promoters · **no PK** (heap; treat
  `promoterId + retailerId` as the logical key)
- `promoterId` → `tbl_salesperson.ID` (types: PROMOTER(MT) 772, PROMOTER(GT) 465, PROMOTER(GTW) 166,
  SO 17, PROMOTER(MTW) 2); `retailerId` → `tbl_retailers.Id` (0 orphans).
- Only 994 of the live mappings have ever produced a visit — the rest are stale or not-yet-started assignments.

### 2.5 `tbl_soPromoterMap` — supervising SO for each promoter
- **Rows:** 48 · **PK:** `id`
- `soId` → `tbl_salesperson.ID` (all 48 are `PERSONTYPE = 'SO'`); `promoterId` → `tbl_salesperson.ID`
  (2 point at deleted/missing persons).
- `MapedOn` / `MapedBy` (note the single-p spelling) are audit fields, **NULL on the sampled rows**.
- Sparse: covers only a fraction of the 894 promoter records — do not assume every promoter has an SO.

### 2.6 `tbl_promoterAadharCards` — onboarding ID scan
- **Rows:** 49 · **no PK** · `promoterId` → `tbl_salesperson.ID`, `imgUri` = filename on the portal's
  upload store (e.g. `47-20-8-121-1632121282490.jpg`, or an original WhatsApp name). No Aadhaar number
  is stored — image reference only.

### 2.7 `tbl_promoterResumes` — onboarding resume scan
- **Rows:** 49 · **no PK** · same shape: `promoterId` + `imgUri`.

---

## 3. Linkages (verified)

```
tbl_salesperson.ID ─┬─< tbl_SalesReportPromoter.personId          (0 orphans)
                    ├─< tbl_promoterShopMap.promoterId
                    ├─< tbl_soPromoterMap.promoterId / .soId      (0 SO orphans)
                    ├─< tbl_promoterAadharCards.promoterId
                    ├─< tbl_promoterResumes.promoterId
                    ├─< tbl_PromoterAppSalesJsonLog.personId
                    └─< tbl_salesPersonAttendance.personId        (shared with SO force)

tbl_retailers.Id ───┬─< tbl_SalesReportPromoter.retailerId        (720 live rows orphaned)
                    └─< tbl_promoterShopMap.retailerId            (0 orphans)

tbl_SalesReportPromoter.salesId ──< tbl_ProductsSoldPromoter.salesId   (60 orphan lines)
tbl_item.Id ──────────────────────< tbl_ProductsSoldPromoter.productId (3 orphans)

tbl_SalesReportPromoter.imagePath  ==  tbl_PromoterAppSalesJsonLog.imageName   (174/316 match)

geography snapshot on the header:
  stateId  -> tbl_states.stateId
  zoneId   -> tbl_zones.zoneId
  areaId   -> tbl_areas.areaId
  subAreaId-> tbl_subArea.subAreaId      (-1 / NULL on ~99% of rows)
  distId   -> unused (always NULL)
```

Cross-subsystem notes:
- **No `beatId`.** Promoters do not walk beats; they sit in one store. Any beat analysis must go through
  `tbl_promoterShopMap` → `tbl_retailers` → `tbl_BeatShopMap` if you need a beat label.
- **Attendance is shared.** "Masters > Promoter Attendance" reads `tbl_salesPersonAttendance` filtered to
  promoter person types (Jul-2026: PROMOTER(MT) 2,245, PROMOTER(GT) 1,650, MERCHANDISER 72 punches).
- **Separate from SO sales.** `tbl_SalesReportPromoter` / `tbl_ProductsSoldPromoter` never mix with
  `tbl_SalesReport` / `tbl_ProductsSold`; the id spaces overlap and are unrelated. Never UNION them
  without a source tag.

---

## 4. Portal mapping

| Portal page | Tables read | Tables written |
|---|---|---|
| **Masters > Promoter Attendance** | `tbl_salesPersonAttendance` joined to `tbl_salesperson` (PERSONTYPE LIKE 'PROMOTER%' / MERCHANDISER); geography masters for the filters | — (punches come from the app) |
| **Sales Entry (Promoter)** | `tbl_SalesReportPromoter` + `tbl_ProductsSoldPromoter`, joined to `tbl_salesperson`, `tbl_retailers`, `tbl_item`; filters by state/zone/area + date range | soft-delete edits (`deleted`, `deletedBy`, `deletionDate`) |
| Promoter master / mapping screens (Masters > Salesperson, promoter tab) | `tbl_promoterShopMap`, `tbl_soPromoterMap`, `tbl_promoterAadharCards`, `tbl_promoterResumes` | mapping insert/soft-delete, document upload (filename into `imgUri`) |
| Promoter Android app (write path) | posts the JSON in §2.3 → server inserts header + lines and archives the payload in `tbl_PromoterAppSalesJsonLog` | all three sales tables |

---

## 5. Ready-to-run SELECTs

```sql
-- 1) Promoter visits per day, last 30 days
SELECT s.date, COUNT(*) AS visits, COUNT(DISTINCT s.personId) AS promoters,
       COUNT(DISTINCT s.retailerId) AS stores
FROM tbl_SalesReportPromoter s
WHERE s.deleted = 0
  AND s.date >= DATEADD(day, -30, CAST(GETDATE() AS date))
GROUP BY s.date
ORDER BY s.date DESC;
```

```sql
-- 2) Litres pushed per promoter for a month (pieces x pack size)
SELECT s.personId, MAX(s.personName) AS promoter,
       COUNT(DISTINCT s.salesId)      AS visits,
       SUM(d.pieces)                  AS pieces,
       SUM(d.totalQuantity)           AS litres
FROM tbl_SalesReportPromoter s
JOIN tbl_ProductsSoldPromoter d ON d.salesId = s.salesId AND d.deleted = 0
WHERE s.deleted = 0 AND s.date >= '2026-07-01' AND s.date < '2026-08-01'
GROUP BY s.personId
ORDER BY litres DESC;
```

```sql
-- 3) SKU mix in modern trade for a date range (live item master name)
SELECT d.productId, MAX(i.itemName) AS item,
       SUM(d.pieces) AS pieces, SUM(d.totalQuantity) AS litres,
       SUM(ISNULL(d.sampleStock,0)) AS samples
FROM tbl_ProductsSoldPromoter d
JOIN tbl_SalesReportPromoter s ON s.salesId = d.salesId AND s.deleted = 0
LEFT JOIN tbl_item i ON i.Id = d.productId
WHERE d.deleted = 0 AND s.date >= '2026-07-01' AND s.date < '2026-08-01'
GROUP BY d.productId
ORDER BY litres DESC;
```

```sql
-- 4) In-store stock position on the latest visit per store (stock fields exist only after 2023-12-06)
WITH last_visit AS (
  SELECT s.retailerId, MAX(s.salesId) AS salesId
  FROM tbl_SalesReportPromoter s
  WHERE s.deleted = 0 AND s.date >= '2026-07-01'
  GROUP BY s.retailerId
)
SELECT s.retailerId, s.retailerName, s.date, d.productName,
       d.openingStock, d.pieces AS sold, d.closingStock, d.sampleStock
FROM last_visit lv
JOIN tbl_SalesReportPromoter  s ON s.salesId = lv.salesId
JOIN tbl_ProductsSoldPromoter d ON d.salesId = s.salesId AND d.deleted = 0
WHERE d.closingStock IS NOT NULL
ORDER BY s.retailerName, d.productName;
```

```sql
-- 5) Coverage gap: mapped stores a promoter has NOT visited this month
SELECT m.promoterId, p.PERSONNAME, m.retailerId, r.retailerName
FROM tbl_promoterShopMap m
JOIN tbl_salesperson p ON p.ID = m.promoterId
LEFT JOIN tbl_retailers r ON r.Id = m.retailerId
WHERE m.deleted = 0 AND p.deleted = 0
  AND NOT EXISTS (
    SELECT 1 FROM tbl_SalesReportPromoter s
    WHERE s.deleted = 0 AND s.personId = m.promoterId
      AND s.retailerId = m.retailerId AND s.date >= '2026-07-01')
ORDER BY p.PERSONNAME, r.retailerName;
```

```sql
-- 6) Promoter roster with supervising SO + onboarding docs on file
SELECT p.ID AS promoterId, p.PERSONNAME, p.PERSONTYPE, p.CONTACTNO,
       so.ID AS soId, so.PERSONNAME AS soName,
       CASE WHEN a.promoterId IS NULL THEN 0 ELSE 1 END AS hasAadhaar,
       CASE WHEN rs.promoterId IS NULL THEN 0 ELSE 1 END AS hasResume,
       (SELECT COUNT(*) FROM tbl_promoterShopMap m
        WHERE m.deleted = 0 AND m.promoterId = p.ID) AS mappedStores
FROM tbl_salesperson p
LEFT JOIN tbl_soPromoterMap  sp ON sp.promoterId = p.ID
LEFT JOIN tbl_salesperson    so ON so.ID = sp.soId
LEFT JOIN tbl_promoterAadharCards a  ON a.promoterId  = p.ID
LEFT JOIN tbl_promoterResumes     rs ON rs.promoterId = p.ID
WHERE p.deleted = 0 AND p.PERSONTYPE LIKE 'PROMOTER%'
ORDER BY p.PERSONNAME;
```

```sql
-- 7) Raw app payloads that never became a saved visit (post failures, last 7 days)
SELECT l.id, l.createdOn, l.personId, l.imageName
FROM tbl_PromoterAppSalesJsonLog l
LEFT JOIN tbl_SalesReportPromoter s ON s.imagePath = l.imageName
WHERE s.salesId IS NULL
  AND l.createdOn >= DATEADD(day, -7, GETDATE())
ORDER BY l.createdOn DESC;
```

### Caveats to carry into every query
- Always `deleted = 0` on `tbl_SalesReportPromoter`, `tbl_ProductsSoldPromoter`, `tbl_promoterShopMap`
  (the other four tables have no `deleted` column).
- `1899-12-30` is the empty-date sentinel elsewhere in DSR; not observed in these tables, but guard
  `date`/`CreatedOn` filters with `> '1900-01-01'` if you aggregate blindly.
- Use `totalQuantity` (litres) or `pieces` for volume — **never `cost`/`totalCost`** (73% empty, legacy).
- `openingStock`/`closingStock`/`sampleStock` are NULL before 2023-12-06; wrap in `ISNULL(...,0)` only
  when you have already restricted the date range, else you will read "0 stock" as a fact.
- 720 live headers reference deleted retailers — use LEFT JOIN to `tbl_retailers` in listings.
- `status` is `'DONE'` for every row; do not build filters on it.
- Performance: the "latest visit per store" CTE (query 4) sorts across `tbl_retailers` (large) and takes
  ~30-60 s — run it with `dsr --timeout 120s query ...`, or drop the `ORDER BY` when scripting.
