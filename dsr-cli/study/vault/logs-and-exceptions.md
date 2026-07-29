# Subsystem: logs-and-exceptions

DB: `DSR_V6` (SQL Server). Every figure below was verified live on **2026-07-29** with the read-only `dsr` CLI.

Tables in scope: `tbl_apiexceptions`, `hslog`, `tbl_AndroidConsoleActionLog`.

---

## 1. Overview

This is the **platform diagnostics layer** of DSR — not business data. It is what you reach for when a
Sales Officer says "my app didn't sync", when a report screen times out, or when Accounts asks
"who approved / merged this retailer and when".

Three unrelated logs, three different eras and three different authors:

1. **`tbl_apiexceptions` — the mobile/API firehose (8.54 M rows).** The ASP.NET API writes here from
   two code paths: (a) a **breadcrumb trace** around the single heaviest endpoint, `GetShopsData`
   (the app's "download my shop list" sync), and (b) a **real catch-block** that dumps
   `Exception.Message`. 99.91 % of the table is breadcrumbs; only **7,609 rows in 27 months are
   actual errors**. Keyed by `personid` = the field person whose device made the call, so it doubles
   as a per-SO sync-activity log.
2. **`hslog` — the developer scratch log (952 K rows).** A single `nvarchar(max)` column named
   `Text`, **no id, no timestamp, no key** — a heap the .NET code and some triggers `INSERT` free-text
   into. It holds the **full SQL of the two big report screens** (that is the "raw report-SQL
   execution log"), plus stock-recalculation traces, retailer ids, item ids and trigger messages.
   Useful as forensic breadcrumbs; useless for time-series because nothing is timestamped.
3. **`tbl_AndroidConsoleActionLog` — the back-office console action log (48 rows).** Brand new
   (first row **2026-07-24 15:27**), added when the retailer approve/merge screen was rebuilt. This
   is the only *structured* audit trail in the DB: `module / action / entityId / details /
   performedBy / performedOn`. It is the table to grow if you want real admin auditing.

> **Big caveat up front:** none of these is an accounting-grade audit trail. Business-object edits are
> audited *in place* on the object itself (`CreatedBy`/`CreatedOn`/`updatedBy`/`deleted`/`deletedBy`/
> `deletionDate` columns on `tbl_retailers`, `tbl_SalesReport`, …). `tbl_AndroidConsoleActionLog`
> covers only retailer APPROVE/MERGE from 2026-07-24 onward.

---

## 2. Tables (live)

### 2.1 `tbl_apiexceptions` — mobile/API trace + exception log

- **Rows:** 8,543,577 · **PK:** `id` (int identity; `MIN=1`, `MAX=8,558,190` — ~14.6 K ids burned by
  rolled-back inserts, so `id` is *not* dense)
- **Window:** 2024-04-15 16:10 → 2026-07-29 19:04 (still writing; ~7–8.5 K rows/day)
- Only 4 columns:

| Column | Type | Meaning |
|---|---|---|
| `id` | `int` | PK, monotonically increasing → **safe proxy for chronological order** |
| `personid` | `varchar(20)` | the field person's id as **text** → `tbl_salesperson.ID`. 809 distinct numeric values, of which **6 no longer exist** in `tbl_salesperson` (hard-deleted staff) |
| `exception` | `varchar(max)` | the message. **Message only — no stack trace, no endpoint, no HTTP status** |
| `timestamp` | `datetime` | server time of the write. Never NULL, no `1899-12-30` sentinel here |

**No `deleted` column** — nothing is ever soft-deleted or purged here.

**Decoding `exception` (this is the enum that matters):**

| Pattern | Rows | Meaning |
|---|---|---|
| `Starting GetShopsData` | 4,268,269 | app began the shop-list sync for that `personid` |
| `Returning GetShopsData` | 4,267,689 | the same call returned. **`starts − returns = 580` calls that never came back** — those are the hung/timed-out syncs |
| `Object reference not set to an instance of an object.` | 3,843 | NullReferenceException; burst 2024-06-05 → 2025-05-15, then fixed |
| `There is not enough space on the disk.` | 2,832 | image-upload disk-full incident, 2025-05-12 → 2025-10-22 |
| `Exception of type System.Exception was thrown.` | 488 | app's generic hand-thrown error, 2024-06-10 → **2026-07-28 (still live)** |
| `Input string was not in a correct format.` | 287 | bad numeric parse from an app payload |
| `String or binary data would be truncated…` | 123 | 2024-08-26/27 only — a column too small for the posted value |
| `The process cannot access the file D:\LiveProject\DSRNew2\Upload…` | 15 | file lock on the upload folder (reveals the app root: `D:\LiveProject\DSRNew2`) |
| `Procedure or function AddSalesPersonAttendance expects parameter @latitude / @longitude` | 14 | attendance punches posted **without GPS** (Apr-2024) |
| `Cannot open database "dsrLive" requested by the login…` | 5 | 2026-02-03 — a component still pointing at the **old `dsrLive` database** |
| `Could not find a part of the path D:\LiveProject\DSRNew2-main\…` | 1 | stray build folder |
| `The conversion of the nvarchar value 10111010102510 overflowed…` | 1 | int overflow on a concatenated id |

**Total real errors = 7,609.** Everything else is the `GetShopsData` trace.

**Gotcha — corrupted `personid`, and most errors are therefore unattributable.**
7,080 rows have a non-numeric `personid` because the catch-block writes the **JSON request body**
into the `varchar(20)` column, where it is truncated. The only two values are `[{},{"pers` (3,669)
and `[{"personI` (3,411). Critically, **all 7,080 sit on error rows, none on breadcrumbs** — i.e.
**7,080 of the 7,609 real errors (93 %) cannot be tied to a person**:

| Message | Rows | Unattributable |
|---|---|---|
| `Object reference not set…` | 3,843 | 3,843 (100 %) |
| `There is not enough space on the disk.` | 2,832 | 2,317 (82 %) |
| `Exception of type System.Exception was thrown.` | 488 | 488 (100 %) |
| `Input string was not in a correct format.` | 287 | 287 (100 %) |
| `Procedure or function AddSalesPersonAttendance…` | 14 | **0** |

Only **529** real errors carry a usable `personId`. Always guard with `TRY_CAST(personid AS int)`,
and never report "errors per salesperson" without saying how many rows were dropped.

**Performance:** at 8.5 M rows a `GROUP BY LEFT(exception,…)` over the whole table is a full scan
(~2–4 min). Always bound with `timestamp >= …` or `id >= …`, and filter out the two `GetShopsData`
patterns first when hunting for real errors.

---

### 2.2 `hslog` — free-text developer / report-SQL log

- **Rows:** 952,322 · **PK: none** (a heap; single column `Text nvarchar(max)`)
- **No timestamp column.** Physical insert order can be *approximated* with
  `sys.fn_PhysLocFormatter(%%physloc%%)` (verified working), but SQL Server gives no ordering
  guarantee. Treat this table as a **bag of breadcrumbs**, not a time series.

Content breakdown (after `LTRIM` + stripping CR/LF, verified by classification query):

| Kind | Rows | What it is |
|---|---|---|
| `CS - <personId><retailerId> - Entry` | 497,756 | entry marker of the "CS" server routine, called per SO × shop |
| `CS - <personId><retailerId> - EXIT` | 183,404 | matching exit marker. **314,352 Entries have no EXIT** — the routine bailed out |
| free text (other) | 208,016 | see the sub-table below |
| report SQL (`SELECT …`) | 56,434 | the **complete SQL text** of the two big report screens, logged at execution time (length 2,129 → 56,406 chars) |
| numeric-only, 3–6 digits | 6,712 | bare **retailer ids** — 5,115 distinct values, **100 % of them exist in `tbl_retailers.Id`** |

The `CS - <n> - Entry/EXIT` id is a **string concatenation of `personId` and `retailerId`, not a single
number** — verified: `CS - 260716015` = person 2607 (CHANDAN PANDHI, SO) × retailer 16015 (Vicky
Karyana Store), and that pair has 39 rows in `tbl_SalesReport`; likewise `2655|122746` (55 rows) and
`71|139726` (5 rows). Because ids are variable-width the split is **ambiguous** — resolve it by
trying every split point and keeping the one where both halves exist in `tbl_salesperson.ID` /
`tbl_retailers.Id`.

Inside the 208 K free-text rows, the recurring shapes:

| Shape | Rows | Meaning |
|---|---|---|
| `new from urt1` | 11,138 | marker from the "update retailer" code path |
| `Data already exists in table - from trigger [ihx_prevent_duplicate_data]` | 1,363 | a **DB trigger** rejected a duplicate insert — the closest thing to a duplicate-submission alarm |
| `T2 <item name> <itemId>` | ~6 K rows across many SKUs | item-resolution trace; the trailing number is `tbl_item.Id` (e.g. `T2 1LTR Coldpress (20 pack) 293`, 897 rows) |
| `P nr2 distid=<distributorId> skuID=<itemId> date=<Mon dd yyyy h:mmAM> . logStock=<n> logPrimary=<n> stockFinal=<n>.` | thousands | **distributor stock recalculation trace** — the only place the before/after stock math is recorded. `distid` → `tbl_retailers.Id` (where type='Distributor'; there is no tbl_distributors table), `skuID` → `tbl_item.Id`, and the embedded `date` is the only usable timestamp in the whole table |
| `Tracing` | 488 | bare marker; the count coincides exactly with the 488 `Exception of type System.Exception was thrown.` rows in `tbl_apiexceptions` — same code path |

**The report SQL (56,434 rows) is two distinct reports:**

| Report | Rows | Fingerprint |
|---|---|---|
| Daily MIS / All-Sales dashboard | 39,966 | starts `\r\n    SELECT\r\n        /*── IDENTITY ──…` ; selects `state, zone, personid, employeeid, persontype, persongroup, personname, parentid, parentname`, then `todayTC / todayPC / todayCanolaSale / todayOliveSale / todayCommoditySale / todayPremiumSale / todaySpicesSale / todayTotalSale`, then `mtdTarget / mtdTotalSale / %ach`. Touches `tbl_salesreport`, `tbl_productssold`, `tbl_retailers`, `tbl_beat*` |
| Attendance audit report | 16,468 | starts `select sp.id, sp.persontype, sp.employeeid, sp.personname…`; joins `tbl_personstate`, `tbl_states`, `tbl_salespersonattendance`, `tbl_attendanceaudit`, `tbl_salesreport`, `vw_attendance`, `tbl_numbertable` |

Both texts **embed the literal filter values the user picked** (`sp.id = 29`,
`DATEADD(DAY, t.rownum - 1, '2025-07-01')`, `DATEDIFF(DAY, '2025-07-01','2025-07-14')`). That makes
`hslog` a de-facto record of *who ran what report for what period* — extract the literals with
`CHARINDEX`/`SUBSTRING`.

---

### 2.3 `tbl_AndroidConsoleActionLog` — back-office console action log

- **Rows:** 48 · **PK:** `id` (int identity; note a reseed — ids run 1…43 then jump to 1043…1047)
- **Window:** 2026-07-24 15:27 → 2026-07-29 15:54. Actively written.

| Column | Type | Meaning |
|---|---|---|
| `id` | `int` | PK |
| `module` | `varchar(30)` | object class. **Only value today: `Retailer`** (48/48) |
| `action` | `varchar(30)` | **`APPROVE` (37)**, **`MERGE` (11)** |
| `entityId` | `varchar(50)` | the object acted on, as text → `tbl_retailers.Id`. 44/48 resolve; 4 point at retailers since hard-deleted, and 9 of the resolved ones are now `deleted = 1` |
| `details` | `nvarchar(max)` | semicolon key=value bag: `Allow=<Allowed\|…>; [mergedWith=<retailerId>; ] beat=<beatId>`. `Allow=Allowed` on all 48 rows so far |
| `performedBy` | `int` | **→ `tbl_loginUser.UserID`, NOT `tbl_salesperson.ID`** (see §3 — this is the classic trap) |
| `performedByName` | `varchar(100)` | denormalized `tbl_loginUser.name` snapshot; **0 mismatches** against the live master today |
| `performedOn` | `datetime` | when the console action happened. Not nullable |

**No `deleted` column** — append-only.

Decoded `details` keys (all values verified to resolve):
- `Allow` — the approval verdict written by the un-approved-shops screen (`Allowed`).
- `mergedWith=<retailerId>` — present only on `MERGE` (11 rows); **all 11 targets exist in
  `tbl_retailers`**. Semantics: `entityId` (the newly-created duplicate) was merged into `mergedWith`.
- `beat=<beatId>` — **all 48 resolve to `tbl_beats.beatId`**; the beat the retailer was approved onto.

---

## 3. Linkages (verified live)

```
tbl_salesperson.ID  ──< tbl_apiexceptions.personid          (varchar! TRY_CAST; 809 distinct, 6 orphans)
                    ──< hslog "CS - <personId><retailerId>" (string concat — split by trial)

tbl_retailers.Id    ──< tbl_AndroidConsoleActionLog.entityId            (varchar! TRY_CAST; 44/48 resolve)
                    ──< tbl_AndroidConsoleActionLog details mergedWith= (11/11 resolve)
                    ──< hslog numeric-only rows                         (5,115/5,115 resolve)
                    ──< hslog "CS - …" right-hand half

tbl_loginUser.UserID ──< tbl_AndroidConsoleActionLog.performedBy        (48/48 resolve, 0 name mismatches)

tbl_beats.beatId    ──< tbl_AndroidConsoleActionLog details beat=       (48/48 resolve)

tbl_item.Id         ──< hslog "T2 <name> <itemId>" and "P nr2 … skuID=" (item id range 1–437)
tbl_retailers(type='Distributor') ──< hslog "P nr2 … distid=<id>"   (distributors are retailer rows, NOT a tbl_distributors table)
```

**The one join that will burn you:**
`tbl_AndroidConsoleActionLog.performedBy` is a **portal login user**, not a salesperson. Ids collide:
`performedBy = 89` is `tbl_loginUser` **KIRPAL SINGH**, while `tbl_salesperson.ID = 89` is
**Naveen Kumar (WG)**. Same for 71 (NANCY BIJJI vs MAHESH MALIK) and 90 (PRABHJOT SINGH vs Jaskirat
Singh). Always join to `tbl_loginUser.UserID`. Conversely `tbl_apiexceptions.personid` **is** a
salesperson (app-side), never a login user.

Other cross-subsystem notes:
- `tbl_apiexceptions` has **no `retailerId`, no `beatId`, no device/endpoint column** — the only
  dimension is the person. To reach a zone/state you must go
  `personid → tbl_salesperson.ID → tbl_personstate / tbl_states` (see `sales-person-master.md`,
  `geography-and-scoping.md`).
- Retailer approvals recorded here should be reconciled against the retailer row itself
  (`tbl_retailers.approvedStatus`/`updatedBy`) and against beat mapping (`tbl_BeatShopMap`).
- Distributor stock traces in `hslog` are the audit trail behind the distributor-stock tables; there
  is no structured equivalent.
- All three tables are **outside** the soft-delete convention — no `deleted` columns anywhere, so the
  usual `deleted = 0` filter does **not** apply here. It *does* apply to everything you join them to
  (`tbl_retailers`, `tbl_salesperson`, `tbl_loginUser`, `tbl_beats`) — and for audit work you almost
  always want `LEFT JOIN` without the filter, because the whole point is that the object may have
  been deleted afterwards.
- The `1899-12-30` empty-date sentinel does **not** occur in `tbl_apiexceptions.timestamp` or
  `tbl_AndroidConsoleActionLog.performedOn` (checked: both are dense and in-range).

---

## 4. Portal mapping

| Portal page | `tbl_pageMaster` | Tables |
|---|---|---|
| **AUDIT** (`../SALESREPORT/ALLSALES`, page id 18) | id 18 | **reads** `tbl_SalesReport`/`tbl_ProductsSold` etc.; **writes `hslog`** — the 39,966 `/*── IDENTITY ──*/` MIS SQL texts are this page's query, logged on every run |
| Attendance audit report (Salesperson > Attendance audit) | — | **writes `hslog`** — the 16,468 `select sp.id, sp.persontype…` texts |
| **UN-APPROVED SHOPS** (`/GEOLOCATION/UNAPPROVEDSALES`, page id 22) | id 22 | **writes `tbl_AndroidConsoleActionLog`** (`module='Retailer'`, `action='APPROVE'`/`'MERGE'`, `performedBy` = the logged-in `tbl_loginUser`); updates `tbl_retailers` + beat mapping |
| **APPROVAL DUPLICACY** (`/SalesReport/approvalduplicacy`, page id 32) | id 32 | duplicate-retailer merge screen — the `MERGE` rows with `mergedWith=` |
| Android app / API (all endpoints) | — | **writes `tbl_apiexceptions`**; `GetShopsData` (shop-list sync) writes the Start/Return breadcrumb pair |
| DB triggers (`ihx_prevent_duplicate_data`) + distributor stock recompute | — | **write `hslog`** |

No portal page currently *reads* `tbl_apiexceptions` or `hslog` — they are DBA/developer-only. That
is precisely the gap a `dsr` subcommand fills (see `study/specs/logs-and-exceptions.md`).

---

## 5. Ready-to-run SELECTs

```sql
-- 1) Real errors only (drops the 8.5M GetShopsData breadcrumbs), last 90 days
SELECT CAST(e.timestamp AS date)      AS d,
       LEFT(e.exception, 80)          AS message,
       COUNT(*)                       AS hits,
       COUNT(DISTINCT e.personid)     AS people
FROM tbl_apiexceptions e
WHERE e.timestamp >= DATEADD(day, -90, CAST(GETDATE() AS date))
  AND e.exception NOT LIKE 'Starting %'
  AND e.exception NOT LIKE 'Returning %'
GROUP BY CAST(e.timestamp AS date), LEFT(e.exception, 80)
ORDER BY d DESC, hits DESC;
```

```sql
-- 2) Hung shop-list syncs: a 'Starting GetShopsData' with no 'Returning' within 10 minutes
--    (bounded window — never run this unbounded over 8.5M rows)
WITH s AS (
  SELECT id, TRY_CAST(personid AS int) AS personId, timestamp
  FROM tbl_apiexceptions
  WHERE exception = 'Starting GetShopsData'
    AND timestamp >= DATEADD(day, -7, GETDATE())
)
SELECT s.id, s.personId, p.PERSONNAME, p.PERSONTYPE, s.timestamp AS startedAt
FROM s
LEFT JOIN tbl_salesperson p ON p.ID = s.personId
WHERE NOT EXISTS (
        SELECT 1 FROM tbl_apiexceptions r
        WHERE r.exception = 'Returning GetShopsData'
          AND r.personid  = CAST(s.personId AS varchar(20))
          AND r.timestamp >= s.timestamp
          AND r.timestamp <  DATEADD(minute, 10, s.timestamp))
ORDER BY s.timestamp DESC;
```

```sql
-- 3) Noisiest devices this month: sync volume + error count per field person
SELECT TRY_CAST(e.personid AS int)                                     AS personId,
       MAX(p.PERSONNAME)                                               AS personName,
       MAX(p.PERSONTYPE)                                               AS personType,
       SUM(CASE WHEN e.exception = 'Starting GetShopsData' THEN 1 ELSE 0 END)  AS syncs,
       SUM(CASE WHEN e.exception NOT LIKE 'Starting %'
                 AND e.exception NOT LIKE 'Returning %' THEN 1 ELSE 0 END)     AS errors,
       MAX(e.timestamp)                                                AS lastSeen
FROM tbl_apiexceptions e
LEFT JOIN tbl_salesperson p ON p.ID = TRY_CAST(e.personid AS int)
WHERE e.timestamp >= '2026-07-01' AND e.timestamp < '2026-08-01'
  AND TRY_CAST(e.personid AS int) IS NOT NULL     -- drops the 7,080 truncated-JSON rows
GROUP BY TRY_CAST(e.personid AS int)
ORDER BY errors DESC, syncs DESC;
```

```sql
-- 4) Console audit trail, decoded (who approved/merged which retailer, onto which beat)
SELECT a.id, a.performedOn, a.module, a.action,
       a.performedBy, u.userName, a.performedByName,
       a.entityId                                   AS retailerId,
       r.retailerName, r.deleted                    AS retailerDeletedNow,
       TRY_CAST(SUBSTRING(a.details, CHARINDEX('beat=', a.details) + 5, 20) AS int) AS beatId,
       b.beatName,
       CASE WHEN CHARINDEX('mergedWith=', a.details) > 0
            THEN TRY_CAST(SUBSTRING(a.details,
                   CHARINDEX('mergedWith=', a.details) + 11,
                   CHARINDEX(';', a.details + ';', CHARINDEX('mergedWith=', a.details))
                     - CHARINDEX('mergedWith=', a.details) - 11) AS int) END        AS mergedIntoRetailerId,
       a.details
FROM tbl_AndroidConsoleActionLog a
LEFT JOIN tbl_loginUser  u ON u.UserID  = a.performedBy          -- NOT tbl_salesperson
LEFT JOIN tbl_retailers  r ON r.Id      = TRY_CAST(a.entityId AS int)
LEFT JOIN tbl_beats      b ON b.beatId  = TRY_CAST(SUBSTRING(a.details, CHARINDEX('beat=', a.details) + 5, 20) AS int)
WHERE a.performedOn >= DATEADD(day, -30, GETDATE())
ORDER BY a.performedOn DESC;
```

```sql
-- 5) Which reports were run, and for what date window (report SQL archived in hslog)
SELECT CASE WHEN Text LIKE '%/*%IDENTITY%*/%' THEN 'MIS / All-Sales dashboard'
            WHEN Text LIKE '%tbl_attendanceaudit%' THEN 'Attendance audit'
            ELSE 'other report' END                                AS report,
       LEN(Text)                                                   AS sqlLength,
       -- first date literal embedded in the generated SQL = the period the user asked for
       CASE WHEN CHARINDEX('''20', Text) > 0
            THEN SUBSTRING(Text, CHARINDEX('''20', Text) + 1, 10) END AS firstDateLiteral,
       LEFT(Text, 120)                                             AS head
FROM hslog
WHERE LEN(Text) > 500
ORDER BY sqlLength DESC;
```

```sql
-- 6) hslog CS-routine markers that entered but never exited, resolved to person + retailer
--    (splits the concatenated id by trying every split point)
WITH cs AS (
  SELECT REPLACE(REPLACE(Text, 'CS - ', ''), ' - Entry', '') AS token
  FROM hslog WHERE Text LIKE 'CS - % - Entry'
),
split AS (
  SELECT c.token,
         TRY_CAST(LEFT(c.token, n.rownum)  AS int) AS personId,
         TRY_CAST(SUBSTRING(c.token, n.rownum + 1, 10) AS int) AS retailerId
  FROM cs c
  JOIN tbl_numbertable n ON n.rownum BETWEEN 1 AND LEN(c.token) - 1
)
SELECT TOP 200 s.token, s.personId, p.PERSONNAME, s.retailerId, r.retailerName
FROM split s
JOIN tbl_salesperson p ON p.ID = s.personId
JOIN tbl_retailers   r ON r.Id = s.retailerId
WHERE NOT EXISTS (SELECT 1 FROM hslog h WHERE h.Text = 'CS - ' + s.token + ' - EXIT')
ORDER BY s.personId;
```

```sql
-- 7) Distributor stock-recalculation trace (the only record of the before/after math)
SELECT Text
FROM hslog
WHERE Text LIKE 'P nr2 distid=%'
  AND Text LIKE '%distid=139259%'      -- swap in the distributor id
ORDER BY Text;
```
