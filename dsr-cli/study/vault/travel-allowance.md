# Travel Allowance (TA)

## 1. Overview
The Travel-Allowance subsystem reimburses field staff (Sales Officers / Promoters) for the
distance they cover on their daily beats. JIVO stores a **per-person per-km rate**, the
**km distance from each person's home to each retailer** (and back), a **fixed km matrix
between areas/places**, a **catalog of travel modes** (Bus/Bike/Car), and a **saved daily
TA report** giving the day's route, distance, computed amount and approval status.

The economics are simple: `TA amount = distance (km) × person rate (₹/km)`, summed over the
day, capped/approved by a manager. New tables (`tbl_TA_*`, created May-2026, rate-driven,
km sourced from home→shop and area→area matrices) supersede the older free-text
`TAReprotSave` daily report (data back to 2022). The two coexist during migration.

## 2. Tables

### tbl_TA_TravelMode  — 4 rows — PK: TravelModeId
Lookup of travel modes. Seed values: 1=Bus, 2=Bike, 3=Car (4th row unseen, likely
"Own/Walk" or "Auto"). `TravelMode` (nvarchar) = label; `IsActive` (bit) soft-enable.
Referenced by `tbl_TA_PersonRetailerKm.TravelModeId`.

### tbl_TA_PersonRate  — 11 rows — PK: Id
Per-salesperson reimbursement rate in ₹/km, effective-dated.
- `PersonId` → salesperson.
- `Rate` decimal(10,2) — ₹ per km (sample: 2.00).
- `EffectiveFrom` / `EffectiveTo` (date) — validity window; `EffectiveTo` null = still current.
  Note the **1899/2019-12-31 sentinel**: superseded rows carry `EffectiveTo` = `2019-12-31`
  (an "empty/closed" marker) together with `IsActive = 0`.
- `IsActive` (bit) — current rate flag. `CreatedBy/On`, `UpdatedBy/On` audit.

### tbl_TA_PersonRetailerKm  — 305 rows — PK: Id
Distance (km) between a person's home and a specific retailer, one row per person×retailer.
- `PersonId` → salesperson; `RetailerId` → retailer/shop.
- `HomeToShopKm`, `ShopToHomeKm` decimal(10,2) — outbound / return distance (usually equal in samples).
- `TravelModeId` → tbl_TA_TravelMode (1=Bus in samples).
- `IsActive` (bit, not-null), `CreatedBy/On`, `UpdatedBy/On` audit.
This is the km lookup used to auto-compute a beat's distance from the shops visited.

### tbl_TA_PlaceKm  — 3 rows — PK: Id
Fixed km between two areas/places (area-to-area distance matrix), used when TA is computed
by area rather than by individual shop.
- `FromAreaId`, `ToAreaId` → area/place ids (join to the area/place master; same ids appear
  in `TAReprotSave.FromAreaId/ToAreaId`).
- `FixedKm` decimal(10,2) — agreed distance for that leg (e.g. 60, 30, 35 km).
- `IsActive` (bit), audit cols. Note row 2: From=To=839 with 30 km = intra-area local running.

### TAReprotSave  — 24 rows — PK: Id  (legacy, note the misspelling "Reprot")
Older saved **daily TA report** — one row per person per day. All money/number fields are
stored as **nvarchar strings**, so cast before arithmetic.
- `personid` → salesperson; `Date` — free-text visit date ("5/2/2022 12:00:00 AM").
- `Area` — free-text beat towns visited ("PHAGWARA, GORAYA").
- `distance` — km covered; `Rate` — ₹/km; `Amount` — day's TA (distance×rate);
  `TotalAmount` — running/period total; `ApproveAmount` — sanctioned cap (e.g. 5000).
- `status` (int) — approval state, 0 = pending/unapproved in samples.
- `FirstShopId` / `LastShopId` → first & last retailer of the beat; `TotalShops` — shops visited.
- `FromAreaId` / `ToAreaId` → area ids (link to tbl_TA_PlaceKm legs); `Remarks`.
- `ApprovedBy` / `ApprovedOn` — approval audit (null = not yet approved);
  `createdBy/createddate`, `LastUpdatedBy/LastUpdatedDate` audit.

## 3. Linkages
- `PersonId` / `personid` / `createdBy` / `ApprovedBy` → **tbl_salesperson.personId** (staff & approver).
- `RetailerId` / `FirstShopId` / `LastShopId` → **tbl_retailers.retailerId** (shops).
- `TravelModeId` → **tbl_TA_TravelMode.TravelModeId**.
- `FromAreaId` / `ToAreaId` (in tbl_TA_PlaceKm & TAReprotSave) → area/place master (area id space).
- Daily amount ties the pieces together: `tbl_TA_PersonRetailerKm` (km) × `tbl_TA_PersonRate.Rate`
  (₹/km) → computed TA; `TAReprotSave` is the persisted per-day result of that computation.
- Beat context: a person's visited shops come from the DSR beat/attendance subsystem
  (personId + date → shops), then priced through these TA tables.

## 4. Portal mapping
- **Travel Allowance / TA Report** page — lists daily TA per salesperson, amount and approval
  (backed by `TAReprotSave`, and the new `tbl_TA_*` computation for post-May-2026 data).
- **TA Masters / Settings** (admin) — Person Rate master (`tbl_TA_PersonRate`),
  Person↔Retailer Km (`tbl_TA_PersonRetailerKm`), Place/Area Km matrix (`tbl_TA_PlaceKm`),
  Travel Mode master (`tbl_TA_TravelMode`).
- **TA Approval** — manager screen setting `status`/`ApprovedBy`/`ApprovedOn`.

## 5. Proposed dsr commands

### ta-report
Daily travel-allowance rows for a person over a date range (legacy saved report).
Flags: `--salesperson <personId>` `--from` `--to` `--status <0|1>`
```sql
SELECT Id, personid, Date, Area, distance, Rate, Amount, TotalAmount,
       ApproveAmount, TotalShops, status, ApprovedBy, ApprovedOn
FROM TAReprotSave
WHERE personid = @person
  AND TRY_CONVERT(datetime, Date) >= @from
  AND TRY_CONVERT(datetime, Date) <  @to
ORDER BY TRY_CONVERT(datetime, Date);
-- Date/number cols are nvarchar strings: TRY_CONVERT before comparing/summing.
```

### ta-rates
Current (or history of) per-person km rate.
Flags: `--salesperson <personId>` `--active-only`
```sql
SELECT Id, PersonId, Rate, EffectiveFrom, EffectiveTo, IsActive
FROM tbl_TA_PersonRate
WHERE (@person IS NULL OR PersonId = @person)
  AND (@activeOnly = 0 OR IsActive = 1)
ORDER BY PersonId, EffectiveFrom DESC;
-- Closed rows carry EffectiveTo = '2019-12-31' sentinel + IsActive=0; treat NULL EffectiveTo as open.
```

### ta-retailer-km
Home↔shop distance table for a person (basis of beat distance).
Flags: `--salesperson <personId>` `--retailer <retailerId>`
```sql
SELECT k.Id, k.PersonId, k.RetailerId, k.HomeToShopKm, k.ShopToHomeKm,
       m.TravelMode
FROM tbl_TA_PersonRetailerKm k
LEFT JOIN tbl_TA_TravelMode m ON m.TravelModeId = k.TravelModeId
WHERE k.IsActive = 1
  AND (@person IS NULL OR k.PersonId = @person)
  AND (@retailer IS NULL OR k.RetailerId = @retailer)
ORDER BY k.PersonId, k.RetailerId;
```

### ta-place-km
Fixed area-to-area distance matrix.
Flags: `--from-area <id>` `--to-area <id>`
```sql
SELECT Id, FromAreaId, ToAreaId, FixedKm, IsActive
FROM tbl_TA_PlaceKm
WHERE IsActive = 1
  AND (@fromArea IS NULL OR FromAreaId = @fromArea)
  AND (@toArea   IS NULL OR ToAreaId   = @toArea);
```

### ta-estimate
Estimate a person's TA for one date = beat distance × current rate.
Flags: `--salesperson <personId>` `--date`
```sql
SELECT r.PersonId,
       SUM(k.HomeToShopKm + k.ShopToHomeKm)              AS total_km,
       (SELECT TOP 1 Rate FROM tbl_TA_PersonRate
         WHERE PersonId = r.PersonId AND IsActive = 1
           AND EffectiveFrom <= @date
           AND (EffectiveTo IS NULL OR EffectiveTo >= @date)
         ORDER BY EffectiveFrom DESC)                    AS rate_per_km
FROM tbl_TA_PersonRetailerKm k
JOIN (/* shops visited by @person on @date from beat/attendance subsystem */) r
     ON r.RetailerId = k.RetailerId AND r.PersonId = k.PersonId
WHERE k.IsActive = 1 AND k.PersonId = @person
GROUP BY r.PersonId;
-- amount = total_km * rate_per_km; ignore 1899/2019-12-31 sentinel rows when picking rate.
```
