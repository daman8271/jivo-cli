# Geography & Scoping — DSR_V6 study

*Subsystem:* territory hierarchy (State → Zone → Area → SubArea) plus the three scoping maps that
restrict a **salesperson**, a **portal user** and an **item** to particular states.
*Portal:* Masters → Add Zone.
*Tables:* `tbl_states`, `tbl_zones`, `tbl_areas`, `tbl_subArea`, `tbl_PersonState`, `tbl_itemStates`, `tbl_loginUserStates`.
All facts below were verified live against `DSR_V6` with the read-only `dsr` CLI on 2026-07-29.

---

## 1. Overview

JIVO's field-sales org is sliced geographically. Everything else in DSR hangs off this slice:

- **The hierarchy** is 4 levels deep — `tbl_states` (21 rows, the marketing "states": DELHI/NCR,
  PUNJAB, …) → `tbl_zones` (178, city/district-level: GURGAON, JALANDHAR, AMRITSAR) →
  `tbl_areas` (1,636, the walkable locality: "SOUTH CITY - 2", "PHASE 9") → `tbl_subArea`
  (683, an optional 4th level that is essentially **unused in practice** — 110,354 of 113,673 live
  retailers have a blank `subArea`).
- **Retailers** are stamped with state/zone/area at creation (`tbl_retailers.state/zone/area` —
  note: *nvarchar columns holding the numeric ids*). **Beats** (daily routes) are built out of
  retailers, so a beat inherits its geography from its shops.
- **Every sale row** (`tbl_SalesReport`) carries both the geography **ids** and a **denormalised
  name snapshot** taken at sale time, so historical reports survive a later master rename.
- **The three scoping maps** are pure many-to-many join tables, all shaped `(Id, <ownerId>, stateId)`:
  - `tbl_PersonState` — which states a field person (SO/ASM/RSM/promoter) may sell in / see.
  - `tbl_loginUserStates` — which states a **web-portal** login sees (row-level security for the portal).
  - `tbl_itemStates` — in which states a SKU is sellable (JIVO does not sell every oil in every state).
  - Sentinel: **`stateId = -1` means "ALL STATES"** in all three maps (and in
    `tbl_salesperson.homeZone/homeArea`, where `-1` means "none/all"). Present in the data:
    4 rows in `tbl_PersonState`, 17 in `tbl_itemStates`, and whole-fleet rows in `tbl_loginUserStates`.

Business consequence: getting a state wrong silently hides SKUs from an SO's app, or hides a whole
region from a manager's portal. This subsystem is small in rows but high in blast radius.

---

## 2. Tables (live)

None of the four hierarchy tables has a `deleted` column — **geography is hard-deleted**, which is
why a handful of dangling ids exist (see §3, orphans). Only one declared FK exists in the whole DB
and it is here: `FK_tbl_zones_tbl_states (tbl_zones.stateId → tbl_states.stateId)`. Every other
relationship below is by convention, verified by join.

### `tbl_states` — top of the hierarchy · 21 rows · PK `stateId`

| column | type | meaning |
|---|---|---|
| `stateId` | int | PK. Referenced everywhere as `stateId`. **`-1` is a reserved "ALL" sentinel** and is *not* a row here. |
| `state` | nvarchar(100) | Display name. Marketing geography, not strictly political: `DELHI/NCR` is one "state"; spellings are as-entered (`ORISA`, `HIMANCHAL PRADESH`). |
| `short` | nvarchar(100) | 2-letter code — DL, PB, MH, GJ, WB, KA, AP, UP, HP, MP, RJ, OR, BR, HR, TG, CG, JK, AS, UT, KL, GA. Use this for compact output. |
| `SAPID` | nvarchar(120) | Intended SAP B1 link. **100% NULL — dead column.** Do not join SAP on it. |
| `Latitude`,`Longitude` | nvarchar(100) | State centroid as text, populated for all 21 (e.g. DELHI/NCR `28.7041 / 77.1025`). Used to centre the portal map. |

Full list (stateId → short): 1 DL, 2 PB, 3 MH, 4 GJ, 5 WB, 6 KA, 7 AP, 8 UP, 9 HP, 10 MP, 11 RJ,
12 OR, 13 BR, 14 HR, 15 TG, 16 CG, 17 JK, 18 AS, 19 UT, 20 KL, 21 GA.

### `tbl_zones` — city / district under a state · 178 rows · PK `zoneId`

| column | type | meaning |
|---|---|---|
| `zoneId` | int | PK. |
| `zone` | nvarchar(100) | Name (`ADAMPUR`, `Agra`, `Agra  1`). Casing/whitespace is dirty; **4 (stateId, zone) pairs are duplicated** — match on id, never on name. |
| `stateId` | int | → `tbl_states.stateId`. The only declared FK in the database. |
| `SAPID` | nvarchar(120) | 174/178 NULL, the other 4 are the **empty string** — effectively dead. |
| `Latitude`,`Longitude` | nvarchar(100) | **All NULL** in practice — zones are not geocoded. |

Spread is very uneven: PUNJAB 59 zones, HARYANA 41, UP 19, DELHI/NCR 12.

### `tbl_areas` — the operating locality (beat-sized) · 1,636 rows · PK `areaId`

| column | type | meaning |
|---|---|---|
| `areaId` | int | PK. |
| `area` | nvarchar(100) | Name (`PHASE 9`, `SOUTH CITY - 2`, `AMRITSAR`). **26 (zoneId, area) pairs are duplicated.** |
| `zoneId` | int | → `tbl_zones.zoneId`. 6 rows point at zone 151, which no longer exists. |
| `Latitude`,`Longitude` | nvarchar(100) | All NULL in practice. |

DELHI/NCR alone holds 605 areas across 12 zones; PUNJAB 337.

### `tbl_subArea` — optional 4th level · 683 rows · PK `subAreaId`

| column | type | meaning |
|---|---|---|
| `subAreaId` | int | PK. |
| `subArea` | nvarchar(max) | Name. Never blank in the master (0 empty rows) — but almost nothing *uses* it. |
| `areaId` | int | → `tbl_areas.areaId`. 6 dangling ids (158, 162, 163, 423, 429, 637). |

Rows 1..N largely mirror `tbl_areas` 1:1 by name (`PHASE 9`→`PHASE 9`), i.e. it was seeded from areas
and then abandoned. **Treat sub-area as cosmetic**: 97% of live retailers and effectively all recent
sales rows carry `subArea = NULL`.

### `tbl_PersonState` — salesperson → states they cover · 1,937 rows · PK `Id`

| column | type | meaning |
|---|---|---|
| `Id` | int | PK, identity. |
| `personId` | int | → `tbl_salesperson.ID` (note the master's PK is upper-case `ID`). |
| `stateId` | int | → `tbl_states.stateId`, or **`-1` = all states** (4 rows). |

1,811 distinct persons appear (most now soft-deleted); average 1.07 states per person, max 22
(a national RSM/admin). Of the **192 live** (`deleted=0`) salespersons, **10 have no scope row at
all** — those people see nothing state-filtered, a genuine data-hygiene finding. Person types in the
master: SO 77, PROMOTER(MT) 45, PROMOTER(GT) 42, ASM 17, RSM 4, SR 2, MERCHANDISER 2,
PROMOTER(GTW) 2, ASE 1.

### `tbl_loginUserStates` — portal login → states visible · 1,394 rows · PK `id`

| column | type | meaning |
|---|---|---|
| `id` | int | PK. |
| `Userid` | int | → `tbl_loginUser.UserID` (mixed casing: `Userid` here, `UserID` there). 4 rows dangle. |
| `stateId` | int | → `tbl_states.stateId`, or **`-1` = all states** (super-admin style access). |

This is the portal's row-level security. `tbl_loginUser.role` decodes via `tbl_roles`:
1 ADMINISTRATOR, 2 USER, 3 VIEWER, 4 SUPER ADMIN, 5 CALLER. A dormant twin table
`tbl_userStateMap (id, userId, stateId)` exists with **0 rows** — ignore it.

### `tbl_itemStates` — SKU → states where it is sellable · 2,112 rows · PK `Id`

| column | type | meaning |
|---|---|---|
| `Id` | int | PK. |
| `itemId` | int | → `tbl_item.Id`. 4 rows dangle (items hard-removed). |
| `stateId` | int | → `tbl_states.stateId`, or **`-1` = all states** (17 rows). |

169 distinct items mapped across 22 distinct state values (21 real + `-1`). Beware the decoy:
`tbl_item.state` (int) exists but is **`0` for every live item** — dead column. The real item→state
scoping lives only here. `tbl_itemstates_bak` (1,972 rows) is a backup — ignore.

---

## 3. Linkages (verified)

Within the subsystem (verified by anti-join; orphan counts in brackets):

```
tbl_states.stateId  ←  tbl_zones.stateId            [0 orphans, declared FK]
tbl_zones.zoneId    ←  tbl_areas.zoneId             [6 orphan rows → missing zone 151]
tbl_areas.areaId    ←  tbl_subArea.areaId           [6 orphan rows]
tbl_states.stateId  ←  tbl_PersonState.stateId      [4 rows, all the -1 sentinel]
tbl_states.stateId  ←  tbl_loginUserStates.stateId  [-1 sentinel only]
tbl_states.stateId  ←  tbl_itemStates.stateId       [-1 sentinel only]
```

Out to the rest of DSR:

| from | to | note |
|---|---|---|
| `tbl_PersonState.personId` | `tbl_salesperson.ID` | 12 orphan rows (deleted people). |
| `tbl_loginUserStates.Userid` | `tbl_loginUser.UserID` | 4 orphan rows. |
| `tbl_itemStates.itemId` | `tbl_item.Id` | 4 orphan rows. |
| `tbl_retailers.state / .zone / .area / .subArea` | `tbl_states.stateId` / `tbl_zones.zoneId` / `tbl_areas.areaId` / `tbl_subArea.subAreaId` | ⚠️ **These four columns are `nvarchar` holding the integer id as text** ("1", "116", "793"). Always `TRY_CAST(r.state AS int) = s.stateId`. 0 non-numeric values among 113,673 live retailers, so the cast is safe. |
| `tbl_salesperson.homeState / homeZone / homeArea` | `stateId` / `zoneId` / `areaId` | int columns, `-1` = unset. Used for TA/distance-from-home, not for scoping. `tbl_salesperson.STATE` (nvarchar) is **empty for all 192 live persons** — dead column, do not use. |
| `tbl_SalesReport.stateId / zoneId / areaId / subAreaId` | the four masters | plus denormalised **name** snapshots in `tbl_SalesReport.state / zone / area / subArea` (e.g. `state='DELHI/NCR', zone='GURGAON', area='South City - 2'`). Same pattern in `tbl_SalesReportPromoter` and `tbl_SalesReportTemp`. |
| `tbl_beats.beatId` / `.personId` | beats carry **no** geography of their own — a beat's territory is implied by its shops via `tbl_BeatShopMap.beatId → tbl_beats.beatId`, `tbl_BeatShopMap.shopId → tbl_retailers.Id` (filter `deleted=0`). |

Verified example (live join through the string-id columns):

```
PUNJAB / AMRITSAR / AMRITSAR      6,820 retailers
WEST BENGAL / KOLKATA / NORTH     4,442
PUNJAB / HOSHIARPUR / HOSHIARPUR  3,454
```

Ignore `_bak` / `_temp` / `_dup` twins: `tbl_itemstates_bak`, `tbl_salesreport_bak`,
`tbl_salesreport_dupshop`, `tbl_salesreportpromoter_bak`, `tbl_userStateMap` (0 rows),
`tbl_resourceState` (0 rows), `tbl_zoneAreaLog` (0 rows), `tbl_AssignCaller_Sonu`, `TempTable`.

---

## 4. Portal mapping

| Portal page | Reads | Writes |
|---|---|---|
| **Masters → Add Zone** | `tbl_states` (state dropdown), `tbl_zones`, `tbl_areas`, `tbl_subArea` | creates/renames/deletes zones, areas, sub-areas (hard delete — no `deleted` flag). Audit table `tbl_zoneAreaLog (stateId, stateName, zone, area, action, addedBy, addedByName, createdOn)` exists but is **empty**, so master changes are currently untracked. |
| **Masters** (parent menu) | gated by `tbl_pageMaster` id 21 `MASTERS` → `tbl_pagePermission` per role | — |
| **App Users** (`/LOGIN/INDEX`, page id 3) | `tbl_loginUser`, `tbl_roles` | `tbl_loginUserStates` — the "states this user can see" multiselect. |
| **Sales Person** (`/SALESPERSON/INDEX`, page id 6) | `tbl_states`, `tbl_zones`, `tbl_areas` | `tbl_PersonState` (state coverage) and `tbl_salesperson.homeState/homeZone/homeArea`. |
| **Item** (`/ITEM/CREATE`, page id 27) | `tbl_states` | `tbl_itemStates` — the per-SKU state availability multiselect. |
| **Retailer** (`/RETAILER/INDEX`, page id 10) | all four hierarchy tables as cascading dropdowns | writes the id-as-text into `tbl_retailers.state/zone/area/subArea`. |
| **Reports** (SO Reports, Beat Reports, Location Reports, Audit) | filter dropdowns come from the hierarchy; the report grid filters on `tbl_SalesReport.stateId/zoneId/areaId` and is further clipped by the caller's `tbl_loginUserStates`. | — |

---

## 5. Ready-to-run SELECTs

```sql
-- 1. The whole hierarchy, one row per area (sub-area optional)
SELECT s.stateId, s.state, s.short, z.zoneId, z.zone, a.areaId, a.area,
       sa.subAreaId, sa.subArea
FROM tbl_states s
JOIN tbl_zones z  ON z.stateId = s.stateId
JOIN tbl_areas a  ON a.zoneId  = z.zoneId
LEFT JOIN tbl_subArea sa ON sa.areaId = a.areaId
ORDER BY s.state, z.zone, a.area;
```

```sql
-- 2. Live retailer footprint per state/zone (string-id columns need TRY_CAST)
SELECT s.short, s.state, z.zone, COUNT(*) AS retailers
FROM tbl_retailers r
JOIN tbl_states s ON s.stateId = TRY_CAST(r.state AS int)
JOIN tbl_zones  z ON z.zoneId  = TRY_CAST(r.zone  AS int)
WHERE r.deleted = 0
GROUP BY s.short, s.state, z.zone
ORDER BY retailers DESC;
```

```sql
-- 3. State coverage of every live field person (-1 = ALL STATES)
SELECT p.ID AS personId, p.PERSONNAME, p.PERSONTYPE,
       COALESCE(st.state, CASE WHEN ps.stateId = -1 THEN '*** ALL STATES ***' END) AS state
FROM tbl_salesperson p
LEFT JOIN tbl_PersonState ps ON ps.personId = p.ID
LEFT JOIN tbl_states st      ON st.stateId  = ps.stateId
WHERE p.deleted = 0
ORDER BY p.PERSONNAME, state;
```

```sql
-- 4. Hygiene: live salespeople with NO state scope at all (they fall out of state-filtered views)
SELECT p.ID, p.PERSONNAME, p.PERSONTYPE
FROM tbl_salesperson p
WHERE p.deleted = 0
  AND NOT EXISTS (SELECT 1 FROM tbl_PersonState ps WHERE ps.personId = p.ID)
ORDER BY p.PERSONTYPE, p.PERSONNAME;
```

```sql
-- 5. SKU availability matrix — which live items are sellable in a given state
--    (an item with stateId = -1 is sellable everywhere)
DECLARE @stateId int = 2;  -- PUNJAB
SELECT i.Id AS itemId, i.itemName, i.itemCode, i.MRP
FROM tbl_item i
WHERE i.deleted = 0
  AND EXISTS (SELECT 1 FROM tbl_itemStates x
              WHERE x.itemId = i.Id AND x.stateId IN (@stateId, -1))
ORDER BY i.itemName;
```

```sql
-- 6. Portal users and what geography they can see (-1 = everything)
SELECT u.UserID, u.name, r.role,
       SUM(CASE WHEN us.stateId = -1 THEN 1 ELSE 0 END) AS hasAllStates,
       COUNT(us.id) AS stateRows,
       STRING_AGG(st.short, ',') AS states
FROM tbl_loginUser u
LEFT JOIN tbl_roles r           ON r.Id = u.role
LEFT JOIN tbl_loginUserStates us ON us.Userid = u.UserID
LEFT JOIN tbl_states st          ON st.stateId = us.stateId
WHERE u.deleted = 0
GROUP BY u.UserID, u.name, r.role
ORDER BY u.UserID;
```

```sql
-- 7. Master-data orphans (geography is hard-deleted, so these accumulate)
SELECT 'area->zone'    AS link, COUNT(*) n FROM tbl_areas a       LEFT JOIN tbl_zones z ON z.zoneId = a.zoneId WHERE z.zoneId IS NULL
UNION ALL SELECT 'subArea->area',  COUNT(*) FROM tbl_subArea sa   LEFT JOIN tbl_areas a ON a.areaId = sa.areaId WHERE a.areaId IS NULL
UNION ALL SELECT 'personState->person', COUNT(*) FROM tbl_PersonState ps LEFT JOIN tbl_salesperson p ON p.ID = ps.personId WHERE p.ID IS NULL
UNION ALL SELECT 'itemState->item', COUNT(*) FROM tbl_itemStates x LEFT JOIN tbl_item i ON i.Id = x.itemId WHERE i.Id IS NULL
UNION ALL SELECT 'userState->user', COUNT(*) FROM tbl_loginUserStates l LEFT JOIN tbl_loginUser u ON u.UserID = l.Userid WHERE u.UserID IS NULL;
```

```sql
-- 8. Visits by territory for a window — uses the ids, shows the snapshot names.
--    NOTE: sr.totalPrice is 0 on most rows; real value lives in tbl_ProductsSold. Trust `visits`.
SELECT sr.stateId, MAX(sr.state) AS stateName, sr.zoneId, MAX(sr.zone) AS zoneName,
       COUNT(*) AS visits, SUM(sr.totalPrice) AS headerValue
FROM tbl_SalesReport sr
WHERE sr.deleted = 0
  AND sr.date >= '2026-07-01' AND sr.date < '2026-08-01'   -- 1753-01-01 / 1899-12-30 are sentinels
GROUP BY sr.stateId, sr.zoneId
ORDER BY visits DESC;
```

---

## 6. Traps

1. `tbl_retailers.state/zone/area/subArea` are **text columns holding ids** — a `JOIN ... ON r.state = s.stateId` silently fails or errors; use `TRY_CAST`.
2. `stateId = -1` means **ALL STATES**, not "unknown". Any `IN (@state)` filter over the scope maps must be `IN (@state, -1)`.
3. `tbl_salesperson.STATE` (nvarchar) and `tbl_item.state` (int, always 0) are **dead columns**. Real scoping = `tbl_PersonState` / `tbl_itemStates`.
4. `SAPID` on `tbl_states` and `tbl_zones` is NULL/empty — there is **no** working geography link to SAP B1 today.
5. Hierarchy tables have **no soft-delete**; deletions are physical, so joins from history can dangle. Prefer `LEFT JOIN` when reporting over old sales.
6. Sub-area is effectively unused — do not build reports that require it.
7. Zone and area **names are not unique** (4 and 26 duplicate pairs). Group by id, label by name.
8. `tbl_SalesReport.date` min is `1753-01-01` (SQL Server datetime floor used as a junk/sentinel value); `1899-12-30` is the empty-date sentinel elsewhere in DSR. Always bound date ranges.
