# Subsystem: targets-and-sales-aggregates

## 1. Overview
This subsystem holds the **planning (targets) and precomputed sales rollup (aggregate)** layer of JIVO's DSR SFA. It answers "what should each Sales Officer / Promoter and each retailer sell this month/today, and how are they tracking against it?"

Two halves:
- **Targets** — monthly value/box targets per salesperson (`tbl_salesPersonMontlhyTarget`), per-SKU-category targets (`tbl_categoryWiseTargets`), per-retailer monthly targets (`tbl_retailerMonthlyTarget`), and daily/derived targets (`todayTarget`, `tbl_productiveTarget`, `tbl_visitTarget`). These drive the app's "achievement %" dashboards and the field rep's daily goal card.
- **Sales aggregates** — precomputed retailer sales rollups (`tbl_retailerMonthlySale` monthly totals, `retailerLastSale` last-sale snapshot) so the app doesn't have to re-sum raw order lines every time it shows a retailer's history or the "due to buy" list.

Targets are set at the start of a month (mostly by SO/admin); aggregates are refreshed by batch jobs from the transactional sales tables.

## 2. Tables

### tbl_salesPersonMontlhyTarget — 581 rows — PK `id`
Monthly sales target per field person (note the misspelling "Montlhy").
- `userId` — the salesperson (→ tbl_salesperson.personId). Named `userId` here, not personId.
- `month` — target month (day-of-month varies in samples, e.g. 2021-10-20; treat as the month bucket).
- `target` (bigint) — value target in INR (e.g. 22000).
- `targetBoxes` (int) — box/carton target (e.g. 1100).
- `personType` — role the target applies to: `SO` (Sales Officer) seen in samples; also likely Promoter/other roles.

### tbl_categoryWiseTargets — 2200 rows — PK `id`
Monthly target broken out per product **category/brand-line** for one person.
- `personId` — salesperson (→ tbl_salesperson.personId).
- `date` — target month (1st-of-month in samples, e.g. 2024-05-01).
- One int column **per JIVO product category**, value = target in that category (units/boxes): `canola, gold, olive, mustard, sunflower, soyabean, cottonseed, wheatgrass, naturalmineralwater, plainsoda, flavouredsoda, spices, extraLight, pomace, extraVirgin, riceBran, desiGhee, groundnut, yellowMustard, sesameOil, coffee, jeera, coconut`. `0` = target set to zero; `null` = category not targeted (newer categories like ghee/coffee/spices are largely null in older rows).

### tbl_retailerMonthlyTarget — 59 rows — PK `id`
Monthly sell-in target for an individual retailer (set by the visiting SO).
- `retailerId` — → tbl_retailers.retailerId.
- `month` — target month (1st-of-month).
- `target` (decimal 19,6) — target quantity/value (small values like 3–10 in samples → likely boxes).
- `createdById` / `modifiedBy` — salesperson personId who set/edited it (→ tbl_salesperson.personId).
- `createdBy` (nvarchar) — free-text source label, e.g. "Sales Person".
- `createdOn` / `modifiedOn` / `timeStamp` — audit datetimes.
- No `deleted` column; low row count suggests light usage of this feature.

### todayTarget — 3751 rows — PK `id`
Per-person **daily** target snapshot (the field rep's goal-for-today card).
- `personId` — salesperson (→ tbl_salesperson.personId).
- `today` — the target date.
- `targetBoxes` / `targetLiters` / `targetShops` (all float) — today's box, litre and shop-visit goals. Values can be `0` (no target loaded) and even **negative** `targetLiters` (e.g. -332.87 — appears to be a pro-rated/remaining figure = monthly target minus month-to-date sale, so overshoot goes negative).

### tbl_productiveTarget — 10 rows — PK `personId` (implicit; no id col)
Target for **productive calls** (visits that result in a sale) per person.
- `personId` → tbl_salesperson.personId.
- `target` (float) — productive-visit target for the period.
- `targetDate` — the period (1st-of-month in samples).
- `createdOn` — when set. Very sparsely populated (10 rows).

### tbl_visitTarget — 2 rows — PK `personId` (implicit; no id col)
Target number of **retailer visits** per person. Same shape as tbl_productiveTarget: `personId, target, targetDate, createdOn`. Barely used (2 rows) — visit goals mostly ride in `todayTarget.targetShops` instead.

### retailerLastSale — 40173 rows — PK `retailerId`
One-row-per-retailer snapshot of their **most recent sale** (drives "not bought recently / due to visit" logic).
- `retailerId` → tbl_retailers.retailerId (one row per retailer; ~matches the retailer master size).
- `lastSale` (float) — value/qty of the last sale (`0` = never sold in samples).
- `lastSaleDate` — date of that sale (`null` = never purchased).
- `avgLastYear` (float) — average sale over the last year (baseline for target-setting / decline detection); often null.

### tbl_retailerMonthlySale — 55534 rows — PK `id`
Precomputed **monthly sales total per retailer** (the aggregate that backs retailer history charts and target-vs-actual).
- `retailerId` → tbl_retailers.retailerId.
- `saleMonth` — month bucket (1st-of-month; history goes back to 2015).
- `sale` (float) — total sale for that retailer in that month (value or qty). `0` = no sales that month. Large sequential `id` values (86M+) indicate an identity carried over from a bigger source table.

## 3. Linkages
- **Salesperson** — `tbl_salesPersonMontlhyTarget.userId`, `tbl_categoryWiseTargets.personId`, `todayTarget.personId`, `tbl_productiveTarget.personId`, `tbl_visitTarget.personId`, `tbl_retailerMonthlyTarget.createdById/modifiedBy` → `tbl_salesperson.personId`.
- **Retailer** — `tbl_retailerMonthlyTarget.retailerId`, `retailerLastSale.retailerId`, `tbl_retailerMonthlySale.retailerId` → `tbl_retailers.retailerId`.
- **Product category** — `tbl_categoryWiseTargets` columns map to JIVO product categories in `tbl_item` (by U_TYPE / category grouping, not a hard FK); no itemId column.
- **Monthly keying** — target/aggregate rows key on **person (or retailer) + month bucket**: join actuals to targets on `salesperson/retailer` + `month(targetDate/month/saleMonth)`.
- No `deleted` / soft-delete columns exist on any of these tables (they're derived/planning tables); the 1899-12-30 sentinel and `deleted=0` caveats apply when you **join out** to `tbl_salesperson` / `tbl_retailers`.

## 4. Portal mapping
- **Target Setting / Assign Targets** page → writes `tbl_salesPersonMontlhyTarget`, `tbl_categoryWiseTargets`, `tbl_retailerMonthlyTarget`.
- **Salesperson Dashboard / Achievement report** (target vs actual, achievement %) → reads `tbl_salesPersonMontlhyTarget` + `tbl_categoryWiseTargets` vs sales.
- **Daily plan / "Today's target" card** in the SO mobile app → `todayTarget` (boxes/liters/shops), plus `tbl_productiveTarget` and `tbl_visitTarget` for productive-call & visit KPIs.
- **Retailer profile / history** and **"retailers due to buy"** beat lists → `retailerLastSale` and `tbl_retailerMonthlySale`; retailer-level target line → `tbl_retailerMonthlyTarget`.

## Proposed dsr commands

### `dsr target person`
Monthly value/box target for a salesperson (with per-category breakdown).
Flags: `--salesperson <personId>` (required), `--month YYYY-MM`.
```sql
SELECT t.userId, t.month, t.target, t.targetBoxes, t.personType,
       c.canola, c.gold, c.olive, c.mustard, c.sunflower, c.soyabean
FROM tbl_salesPersonMontlhyTarget t
LEFT JOIN tbl_categoryWiseTargets c
  ON c.personId = t.userId AND c.date = t.month
WHERE t.userId = @person
  AND (@month IS NULL OR t.month = @month);
-- join to tbl_salesperson (deleted=0) for the name
```

### `dsr target today`
The daily box/litre/shop goal card for a rep on a given day.
Flags: `--salesperson <personId>` (required), `--date YYYY-MM-DD` (default today).
```sql
SELECT personId, today, targetBoxes, targetLiters, targetShops
FROM todayTarget
WHERE personId = @person AND today = @date;
-- targetLiters can be negative (remaining after MTD sales)
```

### `dsr retailer sales`
Monthly sales history + last-sale snapshot for a retailer.
Flags: `--retailer <retailerId>` (required), `--from YYYY-MM`, `--to YYYY-MM`.
```sql
SELECT s.retailerId, s.saleMonth, s.sale,
       l.lastSale, l.lastSaleDate, l.avgLastYear
FROM tbl_retailerMonthlySale s
LEFT JOIN retailerLastSale l ON l.retailerId = s.retailerId
WHERE s.retailerId = @retailer
  AND (@from IS NULL OR s.saleMonth >= @from)
  AND (@to   IS NULL OR s.saleMonth <= @to)
ORDER BY s.saleMonth;
-- lastSaleDate NULL = retailer never purchased
```

### `dsr retailer dormant`
Retailers with no recent sale (candidates to re-visit) for a beat/salesperson.
Flags: `--days N` (default 30), `--retailer` / (join to beat via tbl_retailers).
```sql
SELECT l.retailerId, l.lastSale, l.lastSaleDate, l.avgLastYear
FROM retailerLastSale l
JOIN tbl_retailers r ON r.retailerId = l.retailerId AND r.deleted = 0
WHERE l.lastSaleDate IS NULL
   OR l.lastSaleDate < DATEADD(day, -@days, CAST(GETDATE() AS date))
ORDER BY l.lastSaleDate;
```

### `dsr retailer target-vs-actual`
Retailer monthly target against actual monthly sale.
Flags: `--retailer <retailerId>`, `--month YYYY-MM`.
```sql
SELECT t.retailerId, t.month, t.target AS target_qty,
       s.sale AS actual_sale
FROM tbl_retailerMonthlyTarget t
LEFT JOIN tbl_retailerMonthlySale s
  ON s.retailerId = t.retailerId AND s.saleMonth = t.month
WHERE (@retailer IS NULL OR t.retailerId = @retailer)
  AND (@month IS NULL OR t.month = @month);
```
