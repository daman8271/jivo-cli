# DSR subsystem — Beats & Routes

**Scope:** `tbl_beats`, `tbl_BeatShopMap`, `tbl_BeatAssign`, `beatShopLog`, `tbl_BeatShopMovementLog`
**Portal menu:** *Beats*
**DB:** SQL Server `DSR_V6`, schema `dbo`. Everything below verified live on 2026-07-29 with `./dsr query`.

---

## 1. Overview — what this does for JIVO

A **beat** is a named walking route owned by exactly one field person (SO / SR / Promoter / ASM). It is the unit of *journey planning* for JIVO's general-trade field force:

- **Who owns the route** — `tbl_beats.personId` → the salesperson.
- **Which shops are on the route** — `tbl_BeatShopMap` (beat ↔ retailer many-to-many).
- **When the route is to be walked** — `tbl_BeatAssign` (one row per beat per calendar date).
- **How the route changed over time** — `beatShopLog` (append-only membership trail) and `tbl_BeatShopMovementLog` (newer, richer audit of shop moves / beat re-assignments).

In practice most beats are named after a weekday ("MONDAY", "Saturday", "Kapurthala- FRIDAY3-6398"), so an SO has ~6 beats — one per working day — each holding the shops he must cover that day. Everything downstream (secondary sales in `tbl_SalesReport`, GPS attendance, retailer stock, coverage / productivity KPIs) is measured **against** the beat plan: *planned calls* come from here, *actual calls* come from the sales/attendance tables.

Beats are **plan-side only**: no sales, money or stock lives in these five tables.

---

## 2. Tables

### 2.1 `tbl_beats` — the beat master (route header)
Row count **4,882** (live `deleted=0`: **3,947**). PK `beatId` (identity).

| column | type | meaning |
|---|---|---|
| `beatId` | int PK | beat identifier, referenced everywhere else in this subsystem |
| `beatName` | nvarchar(100) | free text. Usually a weekday (`MONDAY`, `Friday`, `SATURDAY`, misspellings like `THURSHDAY`, `wenseday` exist) or a town (`Jalandhar`, `PATIALA`, `Andheri East`) or a channel (`B2B`, `DISTRIBUTOR`, `OFFICE`). Beats cloned in the portal get `-Copy` suffixes chained (`MONDAY-Copy-Copy-Copy-Copy`, 71 live rows share that exact name) — **beatName is NOT unique, never join on it.** |
| `personId` | int | owner field person → `tbl_salesperson.ID`. 28 beats point at a personId with no salesperson row (legacy). 727 distinct persons own at least one live beat. |
| `deleted` | int | soft-delete flag. `0` = live, `1` = deleted. **Always filter `deleted = 0`.** |
| `deletionDate` | date | `1899-12-30` = the empty-date sentinel (i.e. never deleted) |
| `deletedBy` | int | portal user who deleted → `tbl_loginUser.UserID` (`0` when not deleted) |
| `createdBy` | int | portal back-office user who created the beat → `tbl_loginUser.UserID` (verified: 3 = "BALJEET SINGH"/`jivo`, 71 = "NANCY BIJJI"/`Nancy`) — **not** a salesperson id |
| `createdOn` | date | creation date |

No enum/code columns beyond `deleted`.

### 2.2 `tbl_BeatShopMap` — beat ↔ shop membership (current state)
Row count **182,151** (live: **163,727**). PK column is `id` (identity) but it is **not declared** in `primary_keys.tsv` — treat `id` as the surrogate key and `(beatId, shopId)` as the logical key (176,782 distinct pairs, so there are duplicate rows).

| column | meaning |
|---|---|
| `id` | surrogate row id |
| `beatId` | → `tbl_beats.beatId`. **16,974 live rows point at a beatId that no longer exists in `tbl_beats` at all** — join with INNER JOIN when you want only real beats. |
| `shopId` | the retailer → `tbl_retailers.Id` (note the master column is `Id`, not `retailerId`). 78 live rows are orphans; 9 live rows have `shopId = 0` (junk). |
| `deleted` / `deletionDate` / `deletedBy` | soft-delete. `deleted=0` for live membership; `deletionDate`/`deletedBy` are NULL (not the 1899 sentinel) on live rows. |
| `createdBy` | portal user (`tbl_loginUser.UserID`) who added the shop to the beat |
| `createdOn` | date added |

Live coverage picture: **115,878 distinct shops** are on at least one live beat; **21,335 shops sit on more than one beat** (legitimately — one shop per weekday-beat is common, but it is also the main source of double-counting); **2,808 live retailers are on no beat at all** (uncovered universe).

Ignore `tbl_beatshopmap_bak` (145,303 rows) and `tbl_BeatShopMapTemp` (0 rows) — backup/scratch.

### 2.3 `tbl_BeatAssign` — the beat calendar (which beat is walked on which day)
Row count **144,341**, spanning `beatDate` **2021-09-28 → 2026-07-29** (i.e. maintained to today). PK `id`. Covers 3,773 distinct beats.

| column | meaning |
|---|---|
| `id` | PK |
| `beatId` | → `tbl_beats.beatId`. 15,941 rows reference beats that no longer exist. |
| `beatDate` | date the beat is scheduled to be walked. **This, not `beatName`, is the authoritative "day of the beat".** |
| `createdBy` | mostly NULL (only 982 of 144,341 rows are set, all = 71 / "NANCY BIJJI" → `tbl_loginUser.UserID`) — historic rows were bulk-inserted |
| `createdOn` | datetime, usually NULL for the same reason |

Semantics verified: for weekday-named beats the assigned dates match the name (e.g. beats named `TUESDAY` have 4,933 assignments and every one falls on a Tuesday). But it is a *free calendar*, not a rule: beats named `MONDAY-Copy-Copy-Copy-Copy` are assigned across all 6 working days, and `B2B` beats are assigned Mon/Wed/Sat. **2,514 (beatId, beatDate) pairs are duplicated** — always `DISTINCT` or `GROUP BY` before counting planned days. Recent volume: 2,032 assignment rows in the last 30 days.

### 2.4 `beatShopLog` — append-only shop↔beat membership trail (legacy)
Row count **260,659**, `createdOn` **2021-09-17 → 2026-07-28**. **No PK, no deleted flag.** 3 columns only.

| column | meaning |
|---|---|
| `beatId` | beat the shop was placed on. **1,829 rows use the sentinel `beatId = -1`** ("no beat"): all 1,576 shops carrying a `-1` row are currently mapped to a live beat, so `-1` marks a beat-less moment (shop created / imported before beat assignment), **not** a removal. |
| `shopId` | → `tbl_retailers.Id`. 120,516 distinct shops seen. |
| `createdOn` | datetime of the event. Values cluster on odd times (18:30, 21:00) — these are IST midnights/dates written through a UTC conversion; treat as a *date*, not a wall clock. |

Rows are written in bulk and are frequently exact triplicate duplicates (same beat, shop, timestamp). Compared with `tbl_BeatShopMap`: the log holds **221,593 distinct (beat, shop) pairs vs 176,782 in the map, of which 48,772 exist only in the log** — those are memberships that were later hard-deleted from the map. So this table is the *only* record of some historical route composition. Use it for "when did shop X join beat Y / which beats has this shop ever been on"; use `tbl_BeatShopMap` for "where is it now".

### 2.5 `tbl_BeatShopMovementLog` — modern beat/shop movement audit
Row count **2** — brand new, first rows written **2026-07-28**. PK `id`. This is the replacement audit trail the portal now writes when a beat is re-assigned or a shop is moved.

| column | meaning |
|---|---|
| `id` | PK |
| `action` | varchar(20) code. Distinct values today: **`REASSIGN`** only (2 rows). Column is sized for other verbs (expect `ADD` / `REMOVE` / `MOVE`-style values as the portal feature rolls out) — re-check `SELECT DISTINCT action` before relying on it. |
| `shopId` | shop moved → `tbl_retailers.Id`. NULL for whole-beat re-assignments. |
| `fromBeatId` / `toBeatId` | source / destination beat → `tbl_beats.beatId`. For `REASSIGN` only `toBeatId` is populated (the beat that changed owner). |
| `personId` | the salesperson the beat was reassigned **to** → `tbl_salesperson.ID` (verified: 28 = "ARUN KUMAR GUPTA", SO) |
| `details` | human-readable nvarchar(max), e.g. `"Beat 92 reassigned to person 28"` |
| `performedBy` | portal user → `tbl_loginUser.UserID` (71 = "NANCY BIJJI") |
| `performedOn` | datetime of the change |

---

## 3. Linkages (actual join columns — verified)

Inside the subsystem:

```
tbl_beats.beatId  ←  tbl_BeatShopMap.beatId          (1 : N shops)
tbl_beats.beatId  ←  tbl_BeatAssign.beatId           (1 : N calendar dates)
tbl_beats.beatId  ←  beatShopLog.beatId              (history; -1 = none)
tbl_beats.beatId  ←  tbl_BeatShopMovementLog.fromBeatId / .toBeatId
```

Out to other subsystems:

| from | to | notes |
|---|---|---|
| `tbl_beats.personId` | `tbl_salesperson.ID` | beat owner. `tbl_salesperson.PERSONTYPE` ∈ ASM, CSM, PROMOTER(GT/MT/MTW/GTW), RSM, SO, SR, MERCHANDISER, NSM, SUPERVISOR, ASE, NSM (see `tbl_PersonType`). Filter `tbl_salesperson.deleted=0`. |
| `tbl_BeatShopMap.shopId`, `beatShopLog.shopId`, `tbl_BeatShopMovementLog.shopId` | `tbl_retailers.Id` | **column on the master is `Id`**. `tbl_retailers.type` ∈ `Shop` (112,757), `Distributor` (893), `Modern Store` (23). Geography for filters lives on the retailer: `state`, `zone`, `area`, `subArea`. |
| `tbl_beats.createdBy` / `deletedBy`, `tbl_BeatShopMap.createdBy` / `deletedBy`, `tbl_BeatAssign.createdBy`, `tbl_BeatShopMovementLog.performedBy` | `tbl_loginUser.UserID` | back-office portal users (`name`, `userName`, `role`) — *not* salespersons |
| `tbl_BeatShopMap.shopId` + `tbl_beats.personId` + `tbl_BeatAssign.beatDate` | `tbl_SalesReport (retailerId, personId, date)` | **the coverage join.** `tbl_SalesReport` has **no `beatId`** — actual-vs-plan must be reconstructed through (person, retailer, date). Verified working: for 2026-07-28, beat 192 (PARUL GILL) had 293 planned shops and 32 visited. |
| same, promoters | `tbl_SalesReportPromoter` | promoter calls; promoters also have their own map `tbl_promoterShopMap` (1,423 rows) which is **separate from beats** |
| `tbl_beats.personId` | `tbl_salesPersonAttendance.personId` (+ `retailerId`) | GPS punch-in / in-market attendance for the day a beat is assigned |
| `tbl_retailersModifiedLog.previousBeats` / `.modifiedBeats` | (text) | free-text snapshot of a retailer's beats when the retailer record was edited — useful cross-check, not a join key |

**No declared foreign keys exist in `DSR_V6` for any of these tables** (the DB has exactly 1 FK overall), which is why orphan `beatId`s (16,974 map rows, 15,941 assign rows) and `shopId = 0` rows exist. Use INNER JOINs to the masters whenever the number must be trustworthy.

Ignore: `tbl_beats_bak`, `tbl_beatshopmap_bak`, `tbl_BeatShopMapTemp`, `tbl_userDayBeat` (0 rows, dead).

---

## 4. Portal mapping

| Portal page (menu **Beats**) | Reads | Writes |
|---|---|---|
| Beats → *Beat list / Add Beat* | `tbl_beats` + shop counts from `tbl_BeatShopMap`, owner name from `tbl_salesperson` | `tbl_beats` (`createdBy`/`createdOn`, soft-delete via `deleted`/`deletionDate`/`deletedBy`) |
| Beats → *Map shops to beat / Beat shops* | `tbl_BeatShopMap` joined to `tbl_retailers` (filters by `state`/`zone`/`area`) | `tbl_BeatShopMap`, plus a row in `beatShopLog` per shop added |
| Beats → *Copy / clone beat* | `tbl_beats`, `tbl_BeatShopMap` | new `tbl_beats` row named `<name>-Copy` + bulk `tbl_BeatShopMap` inserts (source of the `-Copy-Copy-…` names and the triplicate `beatShopLog` rows) |
| Beats → *Beat assignment / Beat calendar* | `tbl_BeatAssign` | `tbl_BeatAssign` (`createdBy` = logged-in portal user; historic rows were bulk-loaded with NULL) |
| Beats → *Reassign beat / Move shop* (new, live since 2026-07-28) | `tbl_beats`, `tbl_BeatShopMap` | `tbl_beats.personId` update **+** `tbl_BeatShopMovementLog` audit row |
| Retailer master (Retailers menu) | reads beats for the shop | writes `tbl_BeatShopMap` and `tbl_retailersModifiedLog.previousBeats/modifiedBeats` |
| Reports → *Beat coverage / SO productivity* | joins all of the above to `tbl_SalesReport` / `tbl_salesPersonAttendance` | read-only |

---

## 5. Ready-to-run queries

All are read-only and apply the `deleted = 0` / date-sentinel caveats.

**(a) Live beats of one salesperson, with shop counts**
```sql
SELECT b.beatId, b.beatName, s.PERSONNAME, s.PERSONTYPE,
       COUNT(DISTINCT m.shopId) AS shops
FROM tbl_beats b
JOIN tbl_salesperson s ON s.ID = b.personId AND s.deleted = 0
LEFT JOIN tbl_BeatShopMap m ON m.beatId = b.beatId AND m.deleted = 0 AND m.shopId > 0
WHERE b.deleted = 0 AND s.PERSONNAME LIKE '%RAM SINGH%'
GROUP BY b.beatId, b.beatName, s.PERSONNAME, s.PERSONTYPE
ORDER BY shops DESC;
```

**(b) Shops on a given beat, with geography**
```sql
SELECT r.Id AS shopId, r.retailerName, r.type, r.state, r.zone, r.area, r.subArea,
       m.createdOn AS addedOn
FROM tbl_BeatShopMap m
JOIN tbl_retailers r ON r.Id = m.shopId AND r.deleted = 0
WHERE m.beatId = 192 AND m.deleted = 0
ORDER BY r.area, r.retailerName;
```

**(c) Beat plan for a date — which beats are scheduled, whose, how many shops**
```sql
SELECT a.beatDate, b.beatId, b.beatName, s.PERSONNAME, s.PERSONTYPE,
       COUNT(DISTINCT m.shopId) AS planned_shops
FROM (SELECT DISTINCT beatId, beatDate FROM tbl_BeatAssign) a   -- dedupe: 2,514 dup pairs
JOIN tbl_beats b       ON b.beatId = a.beatId AND b.deleted = 0
JOIN tbl_salesperson s ON s.ID = b.personId  AND s.deleted = 0
LEFT JOIN tbl_BeatShopMap m ON m.beatId = b.beatId AND m.deleted = 0 AND m.shopId > 0
WHERE a.beatDate = '2026-07-28'
GROUP BY a.beatDate, b.beatId, b.beatName, s.PERSONNAME, s.PERSONTYPE
ORDER BY planned_shops DESC;
```

**(d) Beat coverage — planned vs actually visited (the KPI query)**
```sql
SELECT b.beatId, b.beatName, s.PERSONNAME,
       COUNT(DISTINCT m.shopId) AS planned,
       COUNT(DISTINCT CASE WHEN sr.retailerId IS NOT NULL THEN m.shopId END) AS visited
FROM (SELECT DISTINCT beatId, beatDate FROM tbl_BeatAssign) a
JOIN tbl_beats b        ON b.beatId = a.beatId AND b.deleted = 0
JOIN tbl_salesperson s  ON s.ID = b.personId
JOIN tbl_BeatShopMap m  ON m.beatId = b.beatId AND m.deleted = 0 AND m.shopId > 0
LEFT JOIN tbl_SalesReport sr
       ON sr.retailerId = m.shopId
      AND sr.personId   = b.personId
      AND CAST(sr.date AS date) = a.beatDate
      AND sr.deleted = 0
WHERE a.beatDate BETWEEN '2026-07-01' AND '2026-07-28'
GROUP BY b.beatId, b.beatName, s.PERSONNAME
ORDER BY planned - COUNT(DISTINCT CASE WHEN sr.retailerId IS NOT NULL THEN m.shopId END) DESC;
```

**(e) Uncovered universe — live retailers on no live beat**
```sql
SELECT r.state, r.zone, COUNT(*) AS unmapped_shops
FROM tbl_retailers r
WHERE r.deleted = 0 AND r.type = 'Shop'
  AND NOT EXISTS (SELECT 1 FROM tbl_BeatShopMap m
                  WHERE m.shopId = r.Id AND m.deleted = 0)
GROUP BY r.state, r.zone
ORDER BY unmapped_shops DESC;
```

**(f) One shop's full beat history (map + legacy log + new audit)**
```sql
SELECT 'log' AS src, l.createdOn AS whenOn,
       CAST(l.beatId AS varchar(20)) AS beat, NULL AS note
FROM beatShopLog l WHERE l.shopId = 51982        -- beatId = -1 means "no beat at that moment"
UNION ALL
SELECT 'map', CAST(m.createdOn AS datetime), CAST(m.beatId AS varchar(20)),
       CASE WHEN m.deleted = 1 THEN 'removed ' + CONVERT(varchar(10), m.deletionDate, 120) ELSE 'live' END
FROM tbl_BeatShopMap m WHERE m.shopId = 51982
UNION ALL
SELECT 'move', v.performedOn,
       CONCAT(ISNULL(CAST(v.fromBeatId AS varchar(20)),'-'), '->', ISNULL(CAST(v.toBeatId AS varchar(20)),'-')),
       v.details
FROM tbl_BeatShopMovementLog v WHERE v.shopId = 51982
ORDER BY whenOn;
```

**(g) Shops sitting on more than one live beat (double-count risk)**
```sql
SELECT m.shopId, r.retailerName, COUNT(DISTINCT m.beatId) AS beats,
       STRING_AGG(CAST(m.beatId AS varchar(20)), ',') AS beatIds
FROM tbl_BeatShopMap m
JOIN tbl_retailers r ON r.Id = m.shopId AND r.deleted = 0
WHERE m.deleted = 0
GROUP BY m.shopId, r.retailerName
HAVING COUNT(DISTINCT m.beatId) > 3
ORDER BY beats DESC;
```

---

## 6. Traps, in one list

1. `beatName` is not unique and is riddled with `-Copy` chains and misspellings — **never** key on it; derive the day from `tbl_BeatAssign.beatDate`.
2. Orphan `beatId`s are everywhere (16,974 map rows, 15,941 assign rows) — INNER JOIN to `tbl_beats`.
3. `tbl_BeatAssign` has 2,514 duplicate `(beatId, beatDate)` pairs — dedupe before counting planned days.
4. `tbl_BeatShopMap` has duplicate `(beatId, shopId)` rows and 9 rows with `shopId = 0` — use `COUNT(DISTINCT shopId)` and `shopId > 0`.
5. Retailer master key is `tbl_retailers.Id`, **not** `retailerId`.
6. `deletionDate = '1899-12-30'` in `tbl_beats` means "never deleted"; in `tbl_BeatShopMap` the same idea is expressed as NULL.
7. `beatShopLog.beatId = -1` = "no beat", not "removed".
8. There is no `beatId` on `tbl_SalesReport` — coverage is reconstructed via (personId, retailerId, date).
9. `createdBy` / `deletedBy` / `performedBy` are portal users (`tbl_loginUser.UserID`), never salespersons.
10. `tbl_BeatShopMovementLog` has only 2 rows (feature shipped 2026-07-28) — do not build reports that assume history in it yet.
