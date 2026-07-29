# Spec: `dsr promoter` — read-only commands for the promoter-activity subsystem

Companion to `study/vault/promoter-activity.md`. Everything here is **SELECT-only** and passes through
the existing read-only guard + rolled-back transaction.

## Ergonomics (mirrors the existing CLI)

- Namespace: `dsr promoter <verb>` (keeps `query`/`count`/`peek`/`schema` untouched).
- Global flags already available and inherited: `--json`, `--compact`, `--csv`, `--select`, `-n/--limit`,
  `-q/--quiet`, `-d/--db`, `--timeout`. Default output is the same aligned table with the row-count footer.
- Shared local flags (same meaning in every subcommand below):

| Flag | Type | Default | Notes |
|---|---|---|---|
| `--from` | date `YYYY-MM-DD` | first day of current month | maps to `s.date >= @from` |
| `--to` | date `YYYY-MM-DD` | today | **inclusive**; emitted as `s.date <= @to` |
| `--promoter` | int or name substring | — | int → `s.personId = @p`; text → `p.PERSONNAME LIKE '%'+@p+'%'` |
| `--so` | int | — | supervising SO via `tbl_soPromoterMap.soId` |
| `--retailer` | int or name substring | — | int → `s.retailerId`; text → `r.retailerName LIKE` |
| `--state` / `--zone` / `--area` | int id or name | — | header snapshot ids `stateId/zoneId/areaId` (fall back to the `state/zone/area` text columns when a name is given) |
| `--item` | int or name substring | — | `d.productId` / `d.productName LIKE` |
| `--type` | string | `PROMOTER%` | `tbl_salesperson.PERSONTYPE` filter, e.g. `PROMOTER(MT)`, `MERCHANDISER` |
| `--include-deleted` | bool | false | drops the `deleted = 0` predicates (audit use only) |
| `--top` | int | 50 | applied as `SELECT TOP (@top)` on ranking commands |

All commands add `deleted = 0` on `tbl_SalesReportPromoter` / `tbl_ProductsSoldPromoter` /
`tbl_promoterShopMap` unless `--include-deleted`. Dates are bound as parameters, never string-concatenated.

---

## 1. `dsr promoter visits`
List promoter store visits (header level), newest first.

Flags: `--from --to --promoter --retailer --state --zone --area --type --with-photo --limit`
(`--with-photo` → `s.imagePath <> ''`).

```sql
SELECT TOP (@top)
       s.salesId, s.date, s.timestamp,
       s.personId, s.personName, p.PERSONTYPE,
       s.retailerId, COALESCE(r.retailerName, s.retailerName) AS retailer,
       s.state, s.zone, s.area,
       s.imagePath,
       (SELECT COUNT(*) FROM tbl_ProductsSoldPromoter d
         WHERE d.salesId = s.salesId AND d.deleted = 0)            AS lines_,
       (SELECT SUM(d.pieces) FROM tbl_ProductsSoldPromoter d
         WHERE d.salesId = s.salesId AND d.deleted = 0)            AS pieces
FROM tbl_SalesReportPromoter s
LEFT JOIN tbl_salesperson p ON p.ID = s.personId
LEFT JOIN tbl_retailers   r ON r.Id = s.retailerId
WHERE s.deleted = 0
  AND s.date >= @from AND s.date <= @to
  AND (@personId  IS NULL OR s.personId   = @personId)
  AND (@retailer  IS NULL OR s.retailerId = @retailer)
  AND (@zoneId    IS NULL OR s.zoneId     = @zoneId)
  AND (@areaId    IS NULL OR s.areaId     = @areaId)
  AND (@stateId   IS NULL OR s.stateId    = @stateId)
  AND (@type      IS NULL OR p.PERSONTYPE LIKE @type)
ORDER BY s.date DESC, s.salesId DESC;
```

## 2. `dsr promoter lines <salesId>`
Show the SKU lines of one visit (opening / sold / closing / samples) — the drill-down from `visits`.

Flags: `--json`, `--include-deleted`.

```sql
SELECT s.salesId, s.date, s.personName,
       COALESCE(r.retailerName, s.retailerName) AS retailer,
       d.Id AS lineId, d.productId,
       COALESCE(i.itemName, d.productName)      AS item,
       d.pieces, d.productQuantity AS packLitres, d.totalQuantity AS litres,
       d.openingStock, d.closingStock, d.sampleStock
FROM tbl_SalesReportPromoter s
JOIN tbl_ProductsSoldPromoter d ON d.salesId = s.salesId AND d.deleted = 0
LEFT JOIN tbl_item      i ON i.Id = d.productId
LEFT JOIN tbl_retailers r ON r.Id = s.retailerId
WHERE s.salesId = @salesId AND s.deleted = 0
ORDER BY d.Id;
```

## 3. `dsr promoter sales`
Aggregated promoter throughput — pieces and litres, grouped by whatever you ask for.

Flags: `--from --to --by {promoter|retailer|item|zone|area|state|date}` (default `promoter`),
plus all the filter flags, `--top`.

```sql
-- --by promoter (swap the GROUP BY key for the other modes)
SELECT TOP (@top)
       s.personId                        AS keyId,
       MAX(s.personName)                 AS keyName,
       COUNT(DISTINCT s.salesId)         AS visits,
       COUNT(DISTINCT s.retailerId)      AS stores,
       SUM(d.pieces)                     AS pieces,
       SUM(d.totalQuantity)              AS litres,
       SUM(ISNULL(d.sampleStock, 0))     AS samples
FROM tbl_SalesReportPromoter s
JOIN tbl_ProductsSoldPromoter d ON d.salesId = s.salesId AND d.deleted = 0
LEFT JOIN tbl_salesperson p ON p.ID = s.personId
WHERE s.deleted = 0
  AND s.date >= @from AND s.date <= @to
  AND (@personId IS NULL OR s.personId   = @personId)
  AND (@retailer IS NULL OR s.retailerId = @retailer)
  AND (@zoneId   IS NULL OR s.zoneId     = @zoneId)
  AND (@itemId   IS NULL OR d.productId  = @itemId)
  AND (@type     IS NULL OR p.PERSONTYPE LIKE @type)
GROUP BY s.personId
ORDER BY litres DESC;
```
Group-key swaps: `--by retailer` → `s.retailerId` / `MAX(s.retailerName)`; `--by item` →
`d.productId` / `MAX(d.productName)`; `--by zone|area|state` → `s.zoneId|s.areaId|s.stateId`;
`--by date` → `s.date` (ordered ascending by date instead of litres).

## 4. `dsr promoter stock`
Latest in-store stock position per store × SKU from the most recent visit in the window.
Only meaningful for dates ≥ 2023-12-06 (stock columns did not exist before).

Flags: `--from --to --retailer --promoter --item --zone --top`.

```sql
WITH last_visit AS (
  SELECT s.retailerId, MAX(s.salesId) AS salesId
  FROM tbl_SalesReportPromoter s
  WHERE s.deleted = 0 AND s.date >= @from AND s.date <= @to
    AND (@retailer IS NULL OR s.retailerId = @retailer)
    AND (@zoneId   IS NULL OR s.zoneId     = @zoneId)
  GROUP BY s.retailerId
)
SELECT TOP (@top)
       s.retailerId, COALESCE(r.retailerName, s.retailerName) AS retailer,
       s.date AS lastVisit, s.personName AS promoter,
       COALESCE(i.itemName, d.productName) AS item,
       d.openingStock, d.pieces AS sold, d.closingStock, d.sampleStock
FROM last_visit lv
JOIN tbl_SalesReportPromoter  s ON s.salesId = lv.salesId
JOIN tbl_ProductsSoldPromoter d ON d.salesId = s.salesId AND d.deleted = 0
LEFT JOIN tbl_item      i ON i.Id = d.productId
LEFT JOIN tbl_retailers r ON r.Id = s.retailerId
WHERE d.closingStock IS NOT NULL
  AND (@itemId IS NULL OR d.productId = @itemId)
ORDER BY retailer, item;
```

## 5. `dsr promoter coverage`
Mapped-store coverage: which assigned stores were / were not worked in the window.

Flags: `--from --to --promoter --so --zone --missed` (default shows both; `--missed` shows gaps only).

```sql
SELECT p.ID AS promoterId, p.PERSONNAME AS promoter, p.PERSONTYPE,
       m.retailerId, COALESCE(r.retailerName, '(deleted store)') AS retailer,
       so.PERSONNAME AS supervisingSo,
       v.visits, v.lastVisit
FROM tbl_promoterShopMap m
JOIN tbl_salesperson p  ON p.ID = m.promoterId
LEFT JOIN tbl_retailers r ON r.Id = m.retailerId
LEFT JOIN tbl_soPromoterMap sp ON sp.promoterId = p.ID
LEFT JOIN tbl_salesperson   so ON so.ID = sp.soId
OUTER APPLY (
  SELECT COUNT(*) AS visits, MAX(s.date) AS lastVisit
  FROM tbl_SalesReportPromoter s
  WHERE s.deleted = 0 AND s.personId = m.promoterId
    AND s.retailerId = m.retailerId
    AND s.date >= @from AND s.date <= @to
) v
WHERE m.deleted = 0 AND p.deleted = 0
  AND (@personId IS NULL OR m.promoterId = @personId)
  AND (@soId     IS NULL OR sp.soId      = @soId)
  AND (@missedOnly = 0 OR v.visits = 0)
ORDER BY p.PERSONNAME, retailer;
```

## 6. `dsr promoter roster`
Promoter master list: type, contact, supervising SO, mapped-store count, onboarding docs on file.

Flags: `--type --so --with-docs` (`--with-docs` → only rows having Aadhaar or resume),
`--include-deleted`.

```sql
SELECT p.ID AS promoterId, p.PERSONNAME AS promoter, p.PERSONTYPE,
       p.CONTACTNO, p.STATE,
       sp.soId, so.PERSONNAME AS supervisingSo,
       (SELECT COUNT(*) FROM tbl_promoterShopMap m
         WHERE m.deleted = 0 AND m.promoterId = p.ID)        AS mappedStores,
       CASE WHEN a.promoterId  IS NULL THEN 0 ELSE 1 END     AS hasAadhaar,
       a.imgUri                                              AS aadhaarFile,
       CASE WHEN rs.promoterId IS NULL THEN 0 ELSE 1 END     AS hasResume,
       rs.imgUri                                             AS resumeFile,
       (SELECT MAX(s.date) FROM tbl_SalesReportPromoter s
         WHERE s.deleted = 0 AND s.personId = p.ID)          AS lastVisit
FROM tbl_salesperson p
LEFT JOIN tbl_soPromoterMap      sp ON sp.promoterId = p.ID
LEFT JOIN tbl_salesperson        so ON so.ID = sp.soId
LEFT JOIN tbl_promoterAadharCards a ON a.promoterId  = p.ID
LEFT JOIN tbl_promoterResumes    rs ON rs.promoterId = p.ID
WHERE (@includeDeleted = 1 OR p.deleted = 0)
  AND p.PERSONTYPE LIKE @type
ORDER BY p.PERSONNAME;
```

## 7. `dsr promoter attendance`
Promoter GPS attendance punches (shared `tbl_salesPersonAttendance`, filtered to promoter types) —
the "Masters > Promoter Attendance" page as a CLI.

Flags: `--from --to --promoter --type --status`.

```sql
SELECT a.id, a.timeStamp, a.personId, p.PERSONNAME AS promoter, p.PERSONTYPE,
       a.status, a.retailerId, r.retailerName,
       a.latitude, a.longitude, a.accuracy, a.address, a.imagePath, a.simNo
FROM tbl_salesPersonAttendance a
JOIN tbl_salesperson p ON p.ID = a.personId
LEFT JOIN tbl_retailers r ON r.Id = a.retailerId
WHERE p.PERSONTYPE LIKE @type          -- default 'PROMOTER%'
  AND a.timeStamp >= @from AND a.timeStamp < DATEADD(day, 1, @to)
  AND (@personId IS NULL OR a.personId = @personId)
  AND (@status   IS NULL OR a.status   = @status)
ORDER BY a.timeStamp DESC;
```

## 8. `dsr promoter applog`
Raw promoter-app payloads (GPS, battery, item array) — debugging/forensics. Data starts 2026-07-24.

Flags: `--from --to --promoter --unmatched` (payloads with no saved visit), `--raw` (print `rawJson`
verbatim instead of the parsed columns).

```sql
SELECT TOP (@top)
       l.id, l.createdOn, l.personId, p.PERSONNAME AS promoter, l.imageName,
       CASE WHEN s.salesId IS NULL THEN 0 ELSE 1 END AS savedVisit,
       s.salesId,
       JSON_VALUE(l.rawJson, '$[0].shopId')    AS shopId,
       JSON_VALUE(l.rawJson, '$[0].latitude')  AS latitude,
       JSON_VALUE(l.rawJson, '$[0].longitude') AS longitude,
       JSON_VALUE(l.rawJson, '$[0].accuracy')  AS accuracy,
       JSON_VALUE(l.rawJson, '$[0].battery')   AS battery,
       JSON_VALUE(l.rawJson, '$[0].provider')  AS provider,
       JSON_VALUE(l.rawJson, '$[0].items')     AS itemsJson
FROM tbl_PromoterAppSalesJsonLog l
LEFT JOIN tbl_salesperson p ON p.ID = l.personId
LEFT JOIN tbl_SalesReportPromoter s ON s.imagePath = l.imageName
WHERE l.createdOn >= @from AND l.createdOn < DATEADD(day, 1, @to)
  AND (@personId    IS NULL OR l.personId = @personId)
  AND (@unmatched = 0 OR s.salesId IS NULL)
ORDER BY l.createdOn DESC;
```
`items` is a nested JSON **string** (`itemId`, `itemPieces`, `itemQuantity`, `sampleStock`); expose it
raw and let the caller `OPENJSON` it, or add `--explode-items` that wraps it in
`CROSS APPLY OPENJSON(JSON_VALUE(l.rawJson,'$[0].items'))`.

---

## Implementation notes
- Reuse the existing renderer used by `query`/`peek` so `--json/--csv/--select/-n` behave identically.
- Every command should print the resolved date window in the footer (unless `-q`) — promoter data has
  hard capability boundaries (stock ≥ 2023-12-06, app log ≥ 2026-07-24) and silently empty output is
  the most likely user confusion.
- Name/id dual flags: resolve names with a small `LIKE` lookup against `tbl_salesperson` /
  `tbl_retailers` / `tbl_item` and error with the candidate list if more than one match.
- Never `UNION` these tables with `tbl_SalesReport`/`tbl_ProductsSold` — different id spaces, different
  business meaning (promoter = in-store push, SO = secondary billing).
- `promoter stock` is the slow one (the last-visit CTE joins the large `tbl_retailers` and sorts on the
  store name): give it a default `--timeout 120s` override and prefer ordering by `retailerId` unless
  the caller explicitly asks for name order.
