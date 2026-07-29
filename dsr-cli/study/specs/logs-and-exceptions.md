# Spec: `dsr logs` — platform diagnostics & audit trail (read-only)

Domain: `tbl_apiexceptions` (8.54 M mobile/API trace + error rows), `hslog` (952 K free-text
developer/report-SQL log, **no key, no timestamp**), `tbl_AndroidConsoleActionLog` (48 rows,
structured back-office action audit). Portal menu: **Audit**.
See `study/vault/logs-and-exceptions.md` for the data model and every verified join.

## Ergonomics (mirrors the existing `query` / `count` / `peek` / `schema` commands)

- Command group: `dsr logs <subcommand>` (cobra parent registered via `init(){ register(newLogsCmd) }`).
- Global flags honoured unchanged: `--profile`, `--db`, `--json`, `--csv`, `--compact`, `--quiet`,
  `--limit`, `--timeout`, `--select`. Default output is the table renderer.
- All statements go through `app.DB.Query`; the SELECT-only guard stays in force.
- Shared local flags across the group:
  - `--from` / `--to` (`YYYY-MM-DD`) — inclusive-from / exclusive-to on the command's natural date
    column (`tbl_apiexceptions.timestamp`, `tbl_AndroidConsoleActionLog.performedOn`).
    **Default when neither is given: last 7 days** — see the safety note below.
  - `--salesperson <id|name>` — numeric ⇒ `tbl_salesperson.ID`, else `UPPER(PERSONNAME) LIKE '%…%'`
    resolved to a set of ids. Compared against `TRY_CAST(tbl_apiexceptions.personid AS int)`.
  - `--state <name|id>` — via `tbl_PersonState` (the real territory map; `tbl_salesperson.STATE` is dead).
  - `--user <userName|UserID>` — back-office actor, **`tbl_loginUser.UserID`** (console log only).
  - `--retailer <id>`, `--beat <id|name>` — console log / hslog only.
  - `--all-trace` — include the `Starting/Returning GetShopsData` breadcrumbs (default: excluded).
  - `--contains <text>` — substring filter on the log text.

### Safety notes the implementation must enforce

1. **`tbl_apiexceptions` is 8.54 M rows and the message column is `varchar(max)`.** Every subcommand
   MUST inject a `timestamp` (or `id`) bound. If the user passes neither `--from`/`--to` nor
   `--salesperson`, default to `timestamp >= DATEADD(day,-7,GETDATE())` and print the applied
   default to stderr unless `--quiet`. Raise the effective default `--timeout` for this group to 120 s.
2. **`personid` is `varchar(20)` and 7,080 rows contain truncated JSON** (`[{},{"pers`,
   `[{"personI`) — and **all of them are error rows**, so 93 % of the 7,609 real errors have no
   usable person. Always `TRY_CAST(... AS int)`; never `CAST`. Any command that filters or groups by
   salesperson must report the count of dropped/unattributable rows in its footer
   (e.g. `3,843 rows had an unparseable personid and were excluded`), otherwise
   `dsr logs sync`/`errors` will look reassuringly empty when things are actually broken.
3. **`performedBy` is a portal login user, not a salesperson.** Join `tbl_loginUser.UserID`.
   Id spaces collide (`89` = KIRPAL SINGH as a login user, "Naveen Kumar (WG)" as a salesperson) —
   a wrong join silently produces plausible-looking wrong names.
4. **These three tables have no `deleted` column**; the usual `deleted = 0` filter does not apply.
   Joins out to `tbl_retailers` / `tbl_salesperson` / `tbl_loginUser` / `tbl_beats` must be
   `LEFT JOIN` **without** a `deleted = 0` predicate — the point of an audit view is to show objects
   that were deleted afterwards. Surface the target's `deleted` flag as its own output column.
5. `hslog` has **no ordering guarantee**. Never present it as chronological. Physical order can be
   shown for debugging only, via `sys.fn_PhysLocFormatter(%%physloc%%)`.
6. `hslog.Text` rows reach **56 KB**. Truncate with `LEFT(Text, n)` for table output; emit the full
   text only under `--json` + an explicit `--full` flag.

---

## 1. `dsr logs errors`

Real API/mobile errors only — drops the 8.5 M `GetShopsData` breadcrumbs.

Flags: `--from/--to`, `--salesperson`, `--state`, `--contains`, `--limit`.

```sql
SELECT TOP (@limit)
       e.id,
       e.timestamp,
       TRY_CAST(e.personid AS int)          AS personId,
       p.PERSONNAME                         AS personName,
       p.PERSONTYPE                         AS personType,
       LEFT(e.exception, 400)               AS message
FROM tbl_apiexceptions e
LEFT JOIN tbl_salesperson p ON p.ID = TRY_CAST(e.personid AS int)
WHERE e.timestamp >= @from AND e.timestamp < DATEADD(day, 1, @to)
  AND e.exception NOT LIKE 'Starting %'
  AND e.exception NOT LIKE 'Returning %'
  AND (@personIds IS NULL OR TRY_CAST(e.personid AS int) IN (SELECT v FROM @personIds))
  AND (@stateId   IS NULL OR EXISTS (SELECT 1 FROM tbl_PersonState ps
                                     WHERE ps.personId = TRY_CAST(e.personid AS int)
                                       AND ps.stateId  = @stateId))
  AND (@contains  IS NULL OR e.exception LIKE @contains)
ORDER BY e.timestamp DESC;
```

## 2. `dsr logs summary`

Error taxonomy: how many of each distinct message, first/last seen, how many people hit it.
The fast triage view — 7,609 real errors exist in the whole 27-month history.

Flags: `--from/--to` (default: **all time** here, since the filtered set is small), `--group-len N`
(prefix length used to bucket messages, default 80), `--by day|message` (default `message`).

```sql
SELECT LEFT(e.exception, @groupLen)        AS message,
       COUNT(*)                            AS hits,
       COUNT(DISTINCT e.personid)          AS people,
       MIN(e.timestamp)                    AS firstSeen,
       MAX(e.timestamp)                    AS lastSeen
FROM tbl_apiexceptions e
WHERE e.exception NOT LIKE 'Starting %'
  AND e.exception NOT LIKE 'Returning %'
  AND (@from IS NULL OR e.timestamp >= @from)
  AND (@to   IS NULL OR e.timestamp <  DATEADD(day, 1, @to))
GROUP BY LEFT(e.exception, @groupLen)
ORDER BY hits DESC;
```

`--by day` variant swaps the grouping key for `CAST(e.timestamp AS date)` and keeps the same shape.

## 3. `dsr logs sync`

Shop-list sync (`GetShopsData`) activity per field person: how many syncs, how many errors, last
seen. Answers "did this SO's app actually talk to the server today?".

Flags: `--from/--to` (default last 7 days), `--salesperson`, `--state`, `--limit`.

```sql
SELECT TRY_CAST(e.personid AS int)                                          AS personId,
       MAX(p.PERSONNAME)                                                    AS personName,
       MAX(p.PERSONTYPE)                                                    AS personType,
       SUM(CASE WHEN e.exception = 'Starting GetShopsData'  THEN 1 ELSE 0 END) AS syncStarts,
       SUM(CASE WHEN e.exception = 'Returning GetShopsData' THEN 1 ELSE 0 END) AS syncReturns,
       SUM(CASE WHEN e.exception NOT LIKE 'Starting %'
                 AND e.exception NOT LIKE 'Returning %' THEN 1 ELSE 0 END)     AS errors,
       MIN(e.timestamp)                                                     AS firstSeen,
       MAX(e.timestamp)                                                     AS lastSeen
FROM tbl_apiexceptions e
LEFT JOIN tbl_salesperson p ON p.ID = TRY_CAST(e.personid AS int)
WHERE e.timestamp >= @from AND e.timestamp < DATEADD(day, 1, @to)
  AND TRY_CAST(e.personid AS int) IS NOT NULL
  AND (@personIds IS NULL OR TRY_CAST(e.personid AS int) IN (SELECT v FROM @personIds))
GROUP BY TRY_CAST(e.personid AS int)
ORDER BY errors DESC, syncStarts DESC;
```

## 4. `dsr logs hung`

Syncs that started and never returned (`syncStarts − syncReturns = 580` over the whole table).
The concrete "app hung / server timed out" list.

Flags: `--from/--to` (**hard-capped at 31 days** — this is a correlated-NOT-EXISTS scan),
`--window <minutes>` (match tolerance, default 10), `--salesperson`.

```sql
WITH s AS (
  SELECT e.id, TRY_CAST(e.personid AS int) AS personId, e.personid AS personidRaw, e.timestamp
  FROM tbl_apiexceptions e
  WHERE e.exception = 'Starting GetShopsData'
    AND e.timestamp >= @from AND e.timestamp < DATEADD(day, 1, @to)
)
SELECT TOP (@limit)
       s.id, s.personId, p.PERSONNAME AS personName, p.PERSONTYPE AS personType,
       s.timestamp AS startedAt
FROM s
LEFT JOIN tbl_salesperson p ON p.ID = s.personId
WHERE NOT EXISTS (SELECT 1
                  FROM tbl_apiexceptions r
                  WHERE r.exception = 'Returning GetShopsData'
                    AND r.personid  = s.personidRaw
                    AND r.timestamp >= s.timestamp
                    AND r.timestamp <  DATEADD(minute, @window, s.timestamp))
  AND (@personIds IS NULL OR s.personId IN (SELECT v FROM @personIds))
ORDER BY s.timestamp DESC;
```

## 5. `dsr logs console`

The back-office action audit trail, **fully decoded** — who approved or merged which retailer, onto
which beat, and whether that retailer still exists.

Flags: `--from/--to` (default: all 48 rows), `--user`, `--retailer`, `--beat`, `--action APPROVE|MERGE`,
`--module` (only `Retailer` exists today), `--limit`.

```sql
SELECT TOP (@limit)
       a.id,
       a.performedOn,
       a.module,
       a.action,
       a.performedBy,
       u.userName,
       a.performedByName,
       TRY_CAST(a.entityId AS int)                                      AS retailerId,
       r.retailerName,
       r.deleted                                                        AS retailerDeletedNow,
       TRY_CAST(SUBSTRING(a.details, CHARINDEX('beat=', a.details) + 5, 20) AS int) AS beatId,
       b.beatName,
       CASE WHEN CHARINDEX('mergedWith=', a.details) > 0
            THEN TRY_CAST(SUBSTRING(a.details,
                   CHARINDEX('mergedWith=', a.details) + 11,
                   CHARINDEX(';', a.details + ';', CHARINDEX('mergedWith=', a.details))
                     - CHARINDEX('mergedWith=', a.details) - 11) AS int) END        AS mergedIntoRetailerId,
       a.details
FROM tbl_AndroidConsoleActionLog a
LEFT JOIN tbl_loginUser u ON u.UserID = a.performedBy            -- NOT tbl_salesperson
LEFT JOIN tbl_retailers r ON r.Id     = TRY_CAST(a.entityId AS int)
LEFT JOIN tbl_beats     b ON b.beatId = TRY_CAST(SUBSTRING(a.details, CHARINDEX('beat=', a.details) + 5, 20) AS int)
WHERE (@from     IS NULL OR a.performedOn >= @from)
  AND (@to       IS NULL OR a.performedOn <  DATEADD(day, 1, @to))
  AND (@userId   IS NULL OR a.performedBy = @userId)
  AND (@retailer IS NULL OR TRY_CAST(a.entityId AS int) = @retailer
                         OR a.details LIKE '%mergedWith=' + CAST(@retailer AS varchar(20)) + '%')
  AND (@beat     IS NULL OR a.details LIKE '%beat=' + CAST(@beat AS varchar(20)) + '%')
  AND (@action   IS NULL OR a.action = @action)
  AND (@module   IS NULL OR a.module = @module)
ORDER BY a.performedOn DESC;
```

*(Verified live: 48/48 rows resolve on `performedBy`, `beat=`, and every `mergedWith=`; 44/48 on
`entityId` — 4 retailers were hard-deleted after the action, which is exactly why the LEFT JOIN.)*

## 6. `dsr logs reports`

Report executions archived in `hslog` — which report screen was run and for what date window
(the generated SQL embeds the user's literal filters).

Flags: `--kind mis|attendance|other`, `--contains <text>`, `--full` (emit whole SQL, JSON only),
`--limit`.

```sql
SELECT TOP (@limit)
       CASE WHEN h.Text LIKE '%/*%IDENTITY%*/%'        THEN 'mis'
            WHEN h.Text LIKE '%tbl_attendanceaudit%'   THEN 'attendance'
            ELSE 'other' END                                        AS report,
       LEN(h.Text)                                                  AS sqlLength,
       CASE WHEN CHARINDEX('''20', h.Text) > 0
            THEN SUBSTRING(h.Text, CHARINDEX('''20', h.Text) + 1, 10) END AS firstDateLiteral,
       CASE WHEN CHARINDEX('sp.id = ', h.Text) > 0
            THEN TRY_CAST(SUBSTRING(h.Text, CHARINDEX('sp.id = ', h.Text) + 8, 8) AS int) END AS filteredPersonId,
       CASE WHEN @full = 1 THEN h.Text ELSE LEFT(h.Text, 300) END    AS sqlText
FROM hslog h
WHERE LEN(h.Text) > 500
  AND (@kind     IS NULL OR
       (@kind = 'mis'        AND h.Text LIKE '%/*%IDENTITY%*/%') OR
       (@kind = 'attendance' AND h.Text LIKE '%tbl_attendanceaudit%'))
  AND (@contains IS NULL OR h.Text LIKE @contains)
ORDER BY LEN(h.Text) DESC;
```

*(Live shape: 56,434 report texts — 39,966 `mis`, 16,468 `attendance`.)*

## 7. `dsr logs trace`

Grep the `hslog` free-text breadcrumbs: `CS - <personId><retailerId> - Entry/EXIT`, bare retailer ids,
`T2 <item> <itemId>`, `new from urt1`, and the `ihx_prevent_duplicate_data` trigger rejections.

Flags: `--contains <text>` (required unless `--kind` given), `--kind cs|retailer|item|trigger|other`,
`--limit`.

```sql
SELECT TOP (@limit)
       LEFT(h.Text, 400) AS text,
       COUNT(*)          AS hits
FROM hslog h
WHERE LEN(h.Text) <= 500                       -- excludes the report SQL, handled by `logs reports`
  AND (@kind IS NULL OR
       (@kind = 'cs'       AND h.Text LIKE 'CS - %') OR
       (@kind = 'retailer' AND h.Text NOT LIKE '%[^0-9]%') OR
       (@kind = 'item'     AND h.Text LIKE 'T2 %') OR
       (@kind = 'trigger'  AND h.Text LIKE 'Data already exists in table - from trigger%'))
  AND (@contains IS NULL OR h.Text LIKE @contains)
GROUP BY LEFT(h.Text, 400)
ORDER BY hits DESC;
```

## 8. `dsr logs cs`

The `CS` routine markers, resolved to real people and shops, with the **Entry-without-EXIT** flag
(497,756 Entries vs 183,404 EXITs — 314,352 unmatched).

Flags: `--salesperson`, `--retailer`, `--unmatched-only` (default true), `--limit`.

```sql
WITH cs AS (
  SELECT REPLACE(REPLACE(h.Text, 'CS - ', ''), ' - Entry', '') AS token
  FROM hslog h
  WHERE h.Text LIKE 'CS - % - Entry'
),
split AS (                                    -- the id is personId||retailerId; try every split
  SELECT c.token,
         TRY_CAST(LEFT(c.token, n.rownum)          AS int) AS personId,
         TRY_CAST(SUBSTRING(c.token, n.rownum + 1, 10) AS int) AS retailerId
  FROM cs c
  JOIN tbl_numbertable n ON n.rownum BETWEEN 1 AND LEN(c.token) - 1
)
SELECT TOP (@limit)
       s.token, s.personId, p.PERSONNAME AS personName,
       s.retailerId, r.retailerName, r.deleted AS retailerDeletedNow,
       COUNT(*)                                AS entries
FROM split s
JOIN tbl_salesperson p ON p.ID = s.personId    -- INNER: only splits where BOTH halves resolve
JOIN tbl_retailers   r ON r.Id = s.retailerId
WHERE (@personIds IS NULL OR s.personId   IN (SELECT v FROM @personIds))
  AND (@retailer  IS NULL OR s.retailerId = @retailer)
  AND (@unmatchedOnly = 0
       OR NOT EXISTS (SELECT 1 FROM hslog x WHERE x.Text = 'CS - ' + s.token + ' - EXIT'))
GROUP BY s.token, s.personId, p.PERSONNAME, s.retailerId, r.retailerName, r.deleted
ORDER BY entries DESC;
```

Implementation note: the split is trial-and-error, so a token *can* in principle yield two valid
(person, retailer) pairs. Emit a `ambiguous` boolean column when `COUNT(*) OVER (PARTITION BY token)`
after the joins is > 1, rather than silently picking one. On a 200-token sample every token resolved
uniquely (e.g. `260716015` → person 2607 CHANDAN PANDHI × retailer 16015 Vicky Karyana Store).

## 9. `dsr logs stock-trace`

Parse the distributor stock-recalculation breadcrumbs — the only record of the before/after stock math.

Flags: `--distributor <id>`, `--item <id>`, `--limit`.

```sql
-- NOTE: the text is "skuID= 326" — there is a SPACE after the '=', so a naive
-- SUBSTRING+TRY_CAST returns NULL. LTRIM then cut at the next space (verified).
WITH t AS (
  SELECT h.Text,
         TRY_CAST(SUBSTRING(h.Text, CHARINDEX('distid=', h.Text) + 7,
                  CHARINDEX(' ', h.Text + ' ', CHARINDEX('distid=', h.Text))
                    - CHARINDEX('distid=', h.Text) - 7) AS int)                       AS distributorId,
         LTRIM(SUBSTRING(h.Text, CHARINDEX('skuID=', h.Text) + 6, 20))                AS skuTail
  FROM hslog h
  WHERE h.Text LIKE 'P nr2 distid=%'
)
SELECT TOP (@limit)
       t.distributorId,
       TRY_CAST(LEFT(t.skuTail, CHARINDEX(' ', t.skuTail + ' ') - 1) AS int)          AS itemId,
       i.itemName,
       t.Text                                                                          AS trace
FROM t
LEFT JOIN tbl_item i
       ON i.Id = TRY_CAST(LEFT(t.skuTail, CHARINDEX(' ', t.skuTail + ' ') - 1) AS int)
WHERE 1 = 1
  AND (@distributor IS NULL OR t.distributorId = @distributor)
  AND (@item        IS NULL OR t.Text LIKE '%skuID= ' + CAST(@item AS varchar(20)) + ' %');
```

Line format (verified):
`P nr2 distid=139259 skuID= 325 date=Jul 14 2025  1:17PM . logStock=287 logPrimary=500 stockFinal=463.`
The embedded `date=` is the only timestamp available anywhere in `hslog`; parse it client-side
(`Mon d yyyy  h:mmtt`) rather than in T-SQL.

## 10. `dsr logs stats`

One-shot health snapshot of the whole diagnostics layer — the "is anything on fire" command.

Flags: none (or `--from/--to` to scope the error counts).

```sql
SELECT
  (SELECT COUNT(*)      FROM tbl_apiexceptions)                                        AS apiRowsTotal,
  (SELECT MIN(timestamp) FROM tbl_apiexceptions)                                       AS apiFirst,
  (SELECT MAX(timestamp) FROM tbl_apiexceptions)                                       AS apiLast,
  (SELECT COUNT(*) FROM tbl_apiexceptions
    WHERE timestamp >= DATEADD(day,-1,GETDATE())
      AND exception NOT LIKE 'Starting %' AND exception NOT LIKE 'Returning %')        AS errors24h,
  (SELECT COUNT(*) FROM tbl_apiexceptions
    WHERE timestamp >= DATEADD(day,-1,GETDATE())
      AND exception = 'Starting GetShopsData')                                          AS syncs24h,
  (SELECT COUNT(DISTINCT personid) FROM tbl_apiexceptions
    WHERE timestamp >= DATEADD(day,-1,GETDATE()))                                       AS activeDevices24h,
  (SELECT COUNT(*) FROM hslog)                                                          AS hslogRows,
  (SELECT COUNT(*) FROM tbl_AndroidConsoleActionLog)                                    AS consoleRows,
  (SELECT MAX(performedOn) FROM tbl_AndroidConsoleActionLog)                            AS consoleLast;
```

*(Baseline on 2026-07-29: apiRowsTotal 8,543,577 · window 2024-04-15 → now · ~7–8.5 K rows/day ·
hslogRows 952,322 · consoleRows 48 since 2026-07-24.)*

---

## Output conventions

- Table output truncates any log text at 120 chars with an ellipsis; `--json` gives the full field
  unless the row exceeds 4 KB, in which case it is truncated and a `truncated: true` key is added
  (only `--full` lifts this).
- Timestamps render as `2006-01-02 15:04:05` local, matching the other command groups.
- Every command prints the effective date window in the footer (suppressed by `--quiet`) so a user
  never mistakes a 7-day default for all-time.
- Nothing in this group selects `tbl_loginUser.password` or `tbl_salesperson.password`; reject those
  if passed via `--select`.
