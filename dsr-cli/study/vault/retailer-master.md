# DSR subsystem — Retailer Master (Outlet master)

Portal: **Masters > Retailers**
DB: `DSR_V6` (SQL Server), schema `dbo`. Everything below verified against the live DB on 2026-07-29 with the read-only `dsr` CLI.

---

## 1. Overview

This is JIVO's **outlet master** — the universe of shops the field force sells into. Every Sales Officer (SO) / Promoter visit, every secondary-sale line, every scheme/gift, every geo-ping and every target in DSR hangs off a row in `tbl_retailers`.

A "retailer" row is not only a kirana shop. `tbl_retailers.type` carries three kinds of trade partner:

| `type` | rows | meaning |
|---|---|---|
| `Shop` | 126,306 | retail outlet the SO/promoter visits on a beat |
| `Distributor` | 1,062 | distributor / super-stockist (also lives here, mapped to shops via `tbl_distributorShopMap.distId`) |
| `Modern Store` | 27 | modern-trade outlet |

The subsystem covers four jobs:

1. **The master record** — name, ERP id, address, geo-coordinates, GST/PAN/TIN, shop type/category, app login credentials, and a set of rolling-sale-stat columns (`lastMonthSale`, `threeMonthAvg`, `sixMonthAvg`, `BestSale`, `target`) that were designed as a denormalised cache but are **NULL on every live row** — see the warning in §2.
2. **Feedback** — free-text notes captured against an outlet (`tbl_retailerFeedbacks`); barely used (6 rows, all blank text).
3. **The modification audit trail** — `tbl_retailersModifiedLog` stores a full before/after pair of ~24 fields every time a back-office user edits an outlet (6,359 edits, 2021-09-24 → 2026-07-28).
4. **The geo-fence ("hedge") correction & merge workflow** — field-captured GPS on outlets is noisy, so DSR keeps: a log of every re-hedge (`tbl_RetailerHedgeLog`), a full pre-correction snapshot of the master (`tbl_retailer_originalhedge`), a set of Google-resolved coordinates (`tbl_retailer_googlehedge`), and a log of duplicate outlets merged into a surviving one (`tbl_mergeRetailerHedgeLog`). Geo-fencing matters because SO attendance/visit validation compares the phone's GPS to the outlet's stored lat/long.

**Note on "hedge":** in this codebase *hedge* consistently means *geo-fence / stored coordinates*, not a financial hedge.

---

## 2. Live tables

### `tbl_retailers` — the outlet master
- **Rows:** 127,395 (113,673 live `deleted=0`, 13,719 soft-deleted, 3 NULL)
- **PK:** `Id` (int, identity). **Every child table joins on this**, under the names `retailerId` / `shopId` / `id`.
- **Created:** 2021-09-17 → live (max `CreatedOn` = today). `CreatedOn`/`deletionDate` use the **1899-12-30 empty-date sentinel** on ~11.5k legacy rows.

Meaningful columns:

| Column | Notes |
|---|---|
| `Id` | PK, the retailer id used everywhere else |
| `erpId` | external ERP code, e.g. `FO_Jivo_89241120`. Populated on 12,095 rows only |
| `SAPID` | **always empty in this DB** (0 non-blank rows) — SAP linkage is not populated here |
| `type` | enum: `Shop` / `Distributor` / `Modern Store` (see table above) |
| `retailerName`, `address`, `pincode`, `location` | outlet identity/address |
| `contactNo`, `mobileNo`, `contactPerson`, `email` | contacts. `mobileNo` is frequently the placeholder `1234567891` |
| `state`, `zone`, `area`, `subArea` | **numeric ids stored as nvarchar** → `tbl_states.stateId`, `tbl_zones.zoneId`, `tbl_areas.areaId`, `tbl_subArea.subAreaId`. Always `TRY_CAST(... AS int)` before joining. `subArea` is usually `-1`/NULL (only 360 rows resolve) |
| `ShopType` | free-text-ish enum, dominated by `newShop` (107,666 — the app's default when an SO creates an outlet), then `General Store` 12,068, `GROCERY` 4,403, `''` 1,198, `DISTRIBUTOR` 1,044, `BAKERY` 378, `Modern Store` 151, `Confectionery Store` 126, `RURAL` 113, `Kirana` 76, plus a long dirty tail (`Grocery store`, `Retailer`, `Wholesaler`, `CHEMIST`, …). Not a clean lookup — do not group on it without normalising |
| `category` | outlet grading: `A` 55,535 · `B` 42,557 · `C` 15,544 · `D` 1,829 · NULL/blank ~11.9k |
| `groupType` | channel: `GT` 107,454 · `MT` 6,469 · `Horeca` 1,581 · NULL/blank ~11.9k. Matches `tbl_RetailerGroup.GroupName` **by name** for GT/MT; `Horeca` is not in that lookup |
| `latitude`, `longitude` | nvarchar decimal degrees — the geo-fence. Only **1** live row has neither |
| `GSTNum`, `PAN`, `TIN_NO`, `VAT_NO`, `CST_NO` | tax ids. `GSTNum` non-blank on only 34 rows |
| `userName`, `password`, `otp`, `otpExpiration`, `refreshToken`, `isTempPassword`, `isFirstLogin` | retailer-app credentials. **`password` is encrypted/base64 — never print it** |
| `appVersion`, `deviceId`, `device`, `gcmId` | retailer-app device/push info |
| `imagePath`, `QRCode` | shop photo filename, QR payload |
| `BestSale`, `lastVisitDate`, `lastVisitStatus`, `lastVisitSale`, `lastMonthSale`, `lastMonthSaleBoxes`, `threeMonthAvg`, `sixMonthAvg`, `target` | intended as denormalised rolling sale stats — **⚠️ all of them are NULL on every one of the 113,673 live rows** (verified column by column). The feature was never switched on. **Never report from these**; get sales from `tbl_SalesReport` / `tbl_retailerMonthlySale` / `retailerLastSale` and targets from `tbl_retailerMonthlyTarget` |
| `feedback` | inline note column; **empty on every row** — feedback actually lives in `tbl_retailerFeedbacks` |
| `deleted`, `deletedBy`, `deletionDate`, `deleteReason` | soft delete. Filter `deleted = 0` for live rows. `deleteReason` top values: NULL 10,974, `No longer needed` 2,570, `Duplicate` 175 |
| `CreatedBy` | *who kind*, not an id: `SO` 115,172 (created from the field app), `0` 11,504 (legacy import), `3` 585, `BACKEND` 134 |
| `createdById` | int → `tbl_salesperson.ID` (114,229 of 115,305 non-null values resolve) |
| `updatedBy` | last editor (numeric-as-string user id, or a name on legacy rows) |
| `dob` | shop owner's birthday (used for greetings) |

### `tbl_RetailerGroup` — channel lookup
- **Rows:** 2. **PK:** `GroupId`. Columns: `GroupId`, `GroupName` → `1 = GT`, `2 = MT`.
- Joined to `tbl_retailers.groupType` **by name**, not by id (and `Horeca` exists in the master but not here).

### `tbl_retailerFeedbacks` — outlet feedback notes
- **Rows:** 6. **No PK.** Columns: `retailerId`, `feedback` (nvarchar(max) — blank in all 6 rows), `userId`, `createdOn` (2022-02-10 → 2025-11-15).
- `retailerId` → `tbl_retailers.Id`. `userId` is ambiguous: all 6 values resolve in **both** `tbl_loginUser.UserID` and `tbl_salesperson.ID`; given this is a back-office screen, read it as `tbl_loginUser.UserID`.
- Effectively an unused feature — do not build reports on it.

### `tbl_retailersModifiedLog` — before/after edit audit
- **Rows:** 6,359. **PK:** `Id`. Range `CreatedOn` 2021-09-24 → 2026-07-28.
- Column pattern: `previousX` / `modifiedX` for `Type, RetailerName, ContactNo, Address, State, Zone, Area, SubArea, ContactPerson, MobileNo, ShopType, Category, latitude, longitude, Email, Pincode, Location, UserName, Password, ImagePath, Distributor, Beats`.
  - `previousDistributor` / `modifiedDistributor` and `previousBeats` / `modifiedBeats` are **text snapshots** of the mapping at edit time (often NULL), not ids.
  - `previousPassword`/`modifiedPassword` — encrypted, never display.
- Who: `retailerId` → `tbl_retailers.Id` (12 of 6,359 orphaned); `transcationBy` → `tbl_salesperson.ID` (**all 6,359 resolve**); `updatedBy` (string) resolves in `tbl_loginUser.UserID` for only 1,828 rows — treat `transcationBy` as the reliable actor; `createdById` mirrors the retailer's creator.
- Many rows are no-ops (every previous == modified) — filter on the field you care about.

### `tbl_RetailerHedgeLog` — geo-fence correction log
- **Rows:** 9,918. **PK:** `Id`. Range 2021-11-02 → 2026-07-22.
- `retailerId` → `tbl_retailers.Id` (2 orphans). `latitude`, `longitude` = the coordinates set by that correction. `createdBy` (string) → `tbl_loginUser.UserID` (**all 9,918 resolve**), `createdOn` = when.
- One row per re-hedge event; the master row holds only the latest value, so this is the history.

### `tbl_mergeRetailerHedgeLog` — duplicate-outlet merge log
- **Rows:** 76. **PK:** `Id`. Range 2025-05-24 → 2025-08-29.
- `mainRetailerId` = surviving outlet, `deleteRetailerId` = duplicate that was retired. Verified: **all 76 `deleteRetailerId` rows are `deleted=1`** in the master, and 74 of 76 `mainRetailerId` rows are live.
- `updatedBy` (string) → `tbl_loginUser.UserID` (all 76 resolve; also resolve in `tbl_salesperson.ID` — back-office screen ⇒ loginUser), `updatedOn`.

### `tbl_retailer_googlehedge` — Google-resolved coordinates
- **Rows:** 51,067. **No declared PK**; `id` **is the retailer id** → `tbl_retailers.Id` (0 orphans).
- `latitude`, `longitude` as `numeric(19,14)`. 39,129 of 51,067 exactly equal the master's current coordinates ⇒ this batch was largely applied to the master; the remaining ~12k are proposals that were not (or have since been re-hedged).

### `tbl_retailer_originalhedge` — pre-correction snapshot of the master
- **Rows:** 46,233. **PK:** `Id` = `tbl_retailers.Id` (0 orphans). Column list is an exact clone of `tbl_retailers` (58 cols).
- It is the **before** image taken ahead of the bulk geo-correction: 39,617 of 46,233 rows now differ from the master on `latitude`; only 6,616 are unchanged. Use it to answer "what was this shop's coordinate before we fixed it".
- Not a live-maintained table — read-only history. Its `deleted`/`CreatedOn` columns reflect the state at snapshot time.

---

## 3. Linkages (verified)

Everything keys off **`tbl_retailers.Id`**.

Within the subsystem:
```
tbl_retailerFeedbacks.retailerId      -> tbl_retailers.Id
tbl_retailersModifiedLog.retailerId   -> tbl_retailers.Id      (12/6359 orphan)
tbl_RetailerHedgeLog.retailerId       -> tbl_retailers.Id      (2/9918 orphan)
tbl_mergeRetailerHedgeLog.mainRetailerId / .deleteRetailerId -> tbl_retailers.Id
tbl_retailer_googlehedge.id           -> tbl_retailers.Id      (0 orphan)
tbl_retailer_originalhedge.Id         -> tbl_retailers.Id      (0 orphan)
tbl_retailers.groupType               -> tbl_RetailerGroup.GroupName   (by NAME, GT/MT only)
```

Geography (string columns — cast first):
```
TRY_CAST(tbl_retailers.state   AS int) -> tbl_states.stateId    (127,395 / 127,395 resolve)
TRY_CAST(tbl_retailers.zone    AS int) -> tbl_zones.zoneId      (127,383 resolve)
TRY_CAST(tbl_retailers.area    AS int) -> tbl_areas.areaId      (127,175 resolve)
TRY_CAST(tbl_retailers.subArea AS int) -> tbl_subArea.subAreaId (only 360 resolve; mostly -1/NULL)
tbl_zones.stateId -> tbl_states.stateId ; tbl_areas.zoneId -> tbl_zones.zoneId ; tbl_subArea.areaId -> tbl_areas.areaId
```

People:
```
tbl_retailers.createdById       -> tbl_salesperson.ID   (114,229 / 115,305 resolve)
tbl_retailersModifiedLog.transcationBy -> tbl_salesperson.ID  (6359/6359)
tbl_RetailerHedgeLog.createdBy (string)      -> tbl_loginUser.UserID (9918/9918)
tbl_mergeRetailerHedgeLog.updatedBy (string) -> tbl_loginUser.UserID (76/76)
```
⚠️ `tbl_salesperson`'s PK is **`ID`**, not `personId`. `personId` is the *foreign-key* name used in child tables such as `tbl_beats.personId`.

Out to other subsystems (all on `tbl_retailers.Id`):
```
tbl_BeatShopMap.shopId        -> tbl_retailers.Id   (182,151 rows, 210 orphan)  ; .beatId -> tbl_beats.beatId ; tbl_beats.personId -> tbl_salesperson.ID
tbl_distributorShopMap.distId -> tbl_retailers.Id where type='Distributor' (28/28 verified)
tbl_distributorShopMap.shopId -> tbl_retailers.Id
tbl_SalesReport.retailerId / tbl_SalesReportPromoter.retailerId -> tbl_retailers.Id   (200k-row sample: 53 orphan)
tbl_geoLocation.retailerId, tbl_salesPersonAttendance.retailerId,
tbl_retailerStock.*, tbl_retailerMonthlySale.retailerId, tbl_retailerMonthlyTarget.retailerId,
tbl_GiftMapwithRetailer.retailerId, tbl_saveGift.retailerId, tbl_RetailerItemRate.retailerId,
tbl_promoterShopMap.retailerId, tbl_reatilerApprovedLog.retailerId, tbl_shelfImages.shopId,
tbl_TA_PersonRetailerKm.RetailerId, beatShopLog.shopId
```
Ignore `*_bak`, `*_temp`, `*_dup`, `Sheet1$`, `TempTable`, `new`, `bakupdistributorshop` — scratch/backup.

---

## 4. Portal mapping

| Portal page | Tables |
|---|---|
| Masters > Retailers (list / search / export) | `tbl_retailers` (+ `tbl_states`/`tbl_zones`/`tbl_areas` for the filter dropdowns, `tbl_RetailerGroup` for the channel dropdown) |
| Masters > Retailers > Add / Edit outlet | writes `tbl_retailers`, appends before/after row to `tbl_retailersModifiedLog` |
| Masters > Retailers > Delete (with reason) | sets `deleted=1`, `deletedBy`, `deletionDate`, `deleteReason` on `tbl_retailers` |
| Retailer modification / audit report | `tbl_retailersModifiedLog` (joined to `tbl_salesperson` via `transcationBy`) |
| Retailer feedback view | `tbl_retailerFeedbacks` |
| Geo-fence (hedge) correction screen — "update shop location" | writes `tbl_retailers.latitude/longitude`, appends `tbl_RetailerHedgeLog`; reference coordinates offered from `tbl_retailer_googlehedge`; pre-correction state preserved in `tbl_retailer_originalhedge` |
| Duplicate-outlet merge screen | appends `tbl_mergeRetailerHedgeLog`, soft-deletes the duplicate in `tbl_retailers` |
| Beat mapping / Distributor mapping screens (adjacent menus) | read `tbl_retailers`, write `tbl_BeatShopMap` / `tbl_distributorShopMap` |
| Mobile SO app "Add new shop" | inserts `tbl_retailers` with `CreatedBy='SO'`, `ShopType='newShop'`, `createdById=<salesperson ID>` |

---

## 5. Example queries

All use real column names. Remember: `deleted = 0` for live rows; `CreatedOn > '1900-01-01'` to skip the 1899-12-30 sentinel.

**1. Live outlet counts by state / channel / grade**
```sql
SELECT s.state, r.groupType, r.category, COUNT(*) AS outlets
FROM tbl_retailers r
JOIN tbl_states s ON s.stateId = TRY_CAST(r.state AS int)
WHERE r.deleted = 0 AND r.type = 'Shop'
GROUP BY s.state, r.groupType, r.category
ORDER BY s.state, r.groupType, r.category;
```

**2. Outlets created by the field force in a date window, with the SO who created them**
```sql
SELECT r.Id, r.retailerName, r.ShopType, r.category, z.zone, p.PERSONNAME AS created_by_so, r.CreatedOn
FROM tbl_retailers r
LEFT JOIN tbl_salesperson p ON p.ID = r.createdById
LEFT JOIN tbl_zones z       ON z.zoneId = TRY_CAST(r.zone AS int)
WHERE r.deleted = 0
  AND r.CreatedOn >= '2026-04-01' AND r.CreatedOn < '2026-08-01'
ORDER BY r.CreatedOn DESC;
```

**3. Data-quality: live outlets missing geo-fence, GST or a real mobile number**
```sql
SELECT COUNT(*) AS live_outlets,
       SUM(CASE WHEN ISNULL(r.latitude,'')  = '' OR ISNULL(r.longitude,'') = '' THEN 1 ELSE 0 END) AS no_geo,
       SUM(CASE WHEN ISNULL(r.GSTNum,'')    = '' THEN 1 ELSE 0 END)                                AS no_gst,
       SUM(CASE WHEN ISNULL(r.erpId,'')     = '' THEN 1 ELSE 0 END)                                AS no_erp_id,
       SUM(CASE WHEN ISNULL(r.mobileNo,'') IN ('', '1234567891') THEN 1 ELSE 0 END)                AS placeholder_mobile
FROM tbl_retailers r
WHERE r.deleted = 0;
```

**4. Geo-fence correction history for one outlet (log + original snapshot + Google proposal + current)**
(the `dsr` guard allows only `SELECT`/`WITH`, so the retailer id is inlined via a CTE rather than `DECLARE`)
```sql
WITH t AS (SELECT 31318 AS rid)
SELECT 'current' AS src, CAST(r.latitude AS nvarchar(50)) AS lat, CAST(r.longitude AS nvarchar(50)) AS lon,
       CAST(NULL AS nvarchar(30)) AS whenAt, CAST(NULL AS nvarchar(100)) AS byUser
FROM tbl_retailers r JOIN t ON r.Id = t.rid
UNION ALL
SELECT 'original', o.latitude, o.longitude, NULL, NULL
FROM tbl_retailer_originalhedge o JOIN t ON o.Id = t.rid
UNION ALL
SELECT 'google', CAST(g.latitude AS nvarchar(50)), CAST(g.longitude AS nvarchar(50)), NULL, NULL
FROM tbl_retailer_googlehedge g JOIN t ON g.id = t.rid
UNION ALL
SELECT 'hedgeLog', h.latitude, h.longitude, CONVERT(nvarchar(30), h.createdOn, 120), u.name
FROM tbl_RetailerHedgeLog h
JOIN t ON h.retailerId = t.rid
LEFT JOIN tbl_loginUser u ON u.UserID = TRY_CAST(h.createdBy AS int)
ORDER BY whenAt;
```

**5. Who edited outlets, and which fields actually changed (real edits only)**
```sql
SELECT m.CreatedOn, m.retailerId, r.retailerName, p.PERSONNAME AS actor,
       CASE WHEN ISNULL(m.previousRetailerName,'') <> ISNULL(m.modifiedRetailerName,'') THEN 'name; ' ELSE '' END +
       CASE WHEN ISNULL(m.previousAddress,'')      <> ISNULL(m.modifiedAddress,'')      THEN 'address; ' ELSE '' END +
       CASE WHEN ISNULL(m.previouslatitude,'')     <> ISNULL(m.modifiedlatitude,'')     THEN 'geo; ' ELSE '' END +
       CASE WHEN ISNULL(m.previousCategory,'')     <> ISNULL(m.modifiedCategory,'')     THEN 'category; ' ELSE '' END +
       CASE WHEN ISNULL(m.previousZone,'')         <> ISNULL(m.modifiedZone,'')         THEN 'zone; ' ELSE '' END AS changed
FROM tbl_retailersModifiedLog m
LEFT JOIN tbl_retailers   r ON r.Id = m.retailerId
LEFT JOIN tbl_salesperson p ON p.ID = m.transcationBy
WHERE m.CreatedOn >= '2026-01-01'
  AND (ISNULL(m.previousRetailerName,'') <> ISNULL(m.modifiedRetailerName,'')
    OR ISNULL(m.previousAddress,'')      <> ISNULL(m.modifiedAddress,'')
    OR ISNULL(m.previouslatitude,'')     <> ISNULL(m.modifiedlatitude,'')
    OR ISNULL(m.previousCategory,'')     <> ISNULL(m.modifiedCategory,'')
    OR ISNULL(m.previousZone,'')         <> ISNULL(m.modifiedZone,''))
ORDER BY m.CreatedOn DESC;
```

**6. Duplicate merges — surviving vs retired outlet**
```sql
SELECT g.Id, g.updatedOn, u.name AS merged_by,
       g.mainRetailerId,   m.retailerName AS survivor,   m.deleted AS survivor_deleted,
       g.deleteRetailerId, d.retailerName AS duplicate,  d.deleteReason
FROM tbl_mergeRetailerHedgeLog g
LEFT JOIN tbl_retailers m ON m.Id = g.mainRetailerId
LEFT JOIN tbl_retailers d ON d.Id = g.deleteRetailerId
LEFT JOIN tbl_loginUser u ON u.UserID = TRY_CAST(g.updatedBy AS int)
ORDER BY g.updatedOn DESC;
```

**7. Live outlets mapped to a beat, with the owning SO**
(don't select the rolling-stat columns — they are NULL everywhere; join `tbl_SalesReport` for real sales)
```sql
SELECT b.beatName, sp.PERSONNAME AS so, r.Id, r.retailerName, r.category, r.groupType, r.ShopType
FROM tbl_BeatShopMap bs
JOIN tbl_beats       b  ON b.beatId = bs.beatId AND ISNULL(b.deleted,0) = 0
JOIN tbl_retailers   r  ON r.Id = bs.shopId AND r.deleted = 0
LEFT JOIN tbl_salesperson sp ON sp.ID = b.personId
WHERE ISNULL(bs.deleted,0) = 0
  AND b.beatName = 'REPLACE_ME'
ORDER BY r.retailerName;
```
