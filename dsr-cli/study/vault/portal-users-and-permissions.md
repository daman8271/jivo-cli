# Subsystem: portal-users-and-permissions

**DB:** `DSR_V6` (SQL Server) · **Portal menu:** *Masters > App Users*, *Masters > Permissions*
**Tables:** `tbl_loginUser`, `tbl_roles`, `tbl_pageMaster`, `tbl_pagePermission`, `tbl_loginUserLog` (+ closely-coupled `tbl_loginUserStates`)
All counts/values below were verified live with `./dsr query` on 2026-07-29.

---

## 1. Overview

This is the **back-office identity layer** of DSR — who can log into the *web portal* and what they are allowed to do there.

It is NOT the field-app identity. Field Sales Officers / Promoters log into the Android app with credentials stored in `tbl_salesperson` (`userName`/`password` there). `tbl_loginUser` is a **separate namespace** for HO / MIS / IT / Accounts / call-centre staff who open the DSR website to view reports, approve shops, upload primary sales, maintain masters, etc.

The model is deliberately simple:

- `tbl_loginUser` = one row per portal account (name, userName, encrypted password, a coarse `role`, a back-dating allowance).
- `tbl_roles` = 5 coarse role labels; the role is essentially a *label* — it does **not** by itself grant screens.
- `tbl_pageMaster` = the catalogue of portal screens (32 live pages, each with an MVC `pageUrl`).
- `tbl_pagePermission` = **the real authorisation table**: one row per (user × page) with 4 CRUD bits. This is what the portal checks.
- `tbl_loginUserStates` = territory scoping: which states a portal user may see (`stateId = -1` means ALL).
- `tbl_loginUserLog` = audit trail of App-Users edits (before/after of name, userName, email, role, back-days, states). Brand new — only 1 row, written 2026-07-29.

Practical consequences: permissions are **per-user, not per-role**, so onboarding a user means copying ~32 permission rows; and because `tbl_pagePermission` rows are never removed when a user is soft-deleted, 487 of the 736 permission rows belong to deleted users.

---

## 2. Tables

### 2.1 `tbl_loginUser` — portal login accounts
Rows: **87 total, 22 live** (`deleted = 0`). PK: `UserID` (int).

| Column | Meaning |
|---|---|
| `UserID` | PK, referenced by `tbl_pagePermission.userId`, `tbl_loginUserStates.Userid`, `tbl_loginUserLog.userId` / `changedBy`. |
| `name` | Display name of the person, e.g. `BALJEET SINGH`. |
| `userName` | Login handle. **Unique across all 87 rows** (verified: 87 distinct / 87 rows) — including deleted ones, so handles are never recycled. |
| `password` | Encrypted, base64 (`vTvLZwWHN2lKMi10XNFBcg==`) — fixed-width blocks, symmetric cipher, **never print it**. |
| `email` | Contact / notification address. |
| `role` | FK → `tbl_roles.Id`. 0 orphans. |
| `backDaysAllowed` | How many days back this user may post/edit dated entries (seen: 0, 25, 150). Drives the *CHANGE BACKDATE* page. |
| `approvedStatus` | 1 = approved (84 rows), 2 = rejected/not-approved (3 rows, all also `deleted=1`). No 0 present. |
| `approvedBy`, `approvedOn` | Who/when approved — both NULL in current data (feature added but unused). |
| `CreatedBy` (name string), `CreatedOn` | Creation audit. Range **2021-09-20 → 2026-07-29**. `CreatedBy` holds a *name/handle string*, not a `UserID`. |
| `deleted` (0/1), `deletedBy` (name string), `deletionDate`, `deleteReason` | Soft delete. Deletion dates run 2021-09-28 → 2026-06-11. **Always filter `deleted = 0` for live accounts.** |

Live role mix: ADMINISTRATOR 12, VIEWER 6, USER 2, CALLER 2.

### 2.2 `tbl_roles` — role labels
Rows: **5**. PK: `Id`. Only two columns (`Id`, `role`), no permission columns — confirming roles are labels, not permission sets.

| Id | role |
|---|---|
| 1 | ADMINISTRATOR |
| 2 | USER |
| 3 | VIEWER |
| 4 | SUPER ADMIN |
| 5 | CALLER |

### 2.3 `tbl_pageMaster` — catalogue of portal screens
Rows: **32** (ids 1–33, id 28 missing; none deleted — `DeletedOn` NULL everywhere). PK: `id`.

| Column | Meaning |
|---|---|
| `pageName` | Screen label shown on the Permissions grid, e.g. `SO REPORTS`, `BEATS`, `ITEM`. |
| `pageUrl` | ASP.NET MVC route, e.g. `/SALESREPORT/SOATTENDANCE`. **Dirty data:** some values carry a leading tab (`\t/LOGIN/INDEX`, `\t/SALESPERSON/INDEX`) and some use `../` prefixes — trim before comparing. |
| `createdBy` / `createdOn`, `LastModifyBy` / `LastModifiedOn`, `DeletedBy` / `DeletedOn`, `LastAction` | Audit columns; **all NULL in production** (pages were seeded directly). `LastAction` would hold `Created`/`Modified`/`Deleted`. |

The catalogue is effectively the portal's sitemap. Sample: ADD PAGE, PERMISSION, APP USERS, CHANGE BACKDATE, EMAIL PREFERENCE, SALES PERSON, TARGETS, ORGANIZATIONAL CHART, TRAVELLING ALLOWANCE, RETAILER, CALL CENTER, TESTING, HR APPROVAL PORTAL, MIS EMP APPROVAL PORTAL, FILE UPLOADER, SO REPORTS, DIST/SUPER, AUDIT, BEATS, SALES ENTRY, MASTERS, UN-APPROVED SHOPS, ANDROID CONSOLE, Primary Sales Upload, Promoter Attendance, Unapproved Stock, ITEM, PROMOTER REPORTS, LOCATION REPORTS, BEAT REPORTS, APPROVAL DUPLICACY, SO ATTENDANCE.

Note several distinct pages share `pageUrl = /LOGIN/INDEX` (APP USERS, CHANGE BACKDATE, EMAIL PREFERENCE, MASTERS) — they are tabs/actions on one screen, so **join permissions on `pageId`, never on `pageUrl`**.

### 2.4 `tbl_pagePermission` — the actual ACL (user × page × CRUD)
Rows: **736**, covering **61 distinct users**. PK: `id`. No duplicate `(userId, pageId)` pairs (verified) — it behaves like a unique key even though it isn't declared.

| Column | Meaning |
|---|---|
| `userId` | FK → `tbl_loginUser.UserID`. 0 orphans. |
| `pageId` | FK → `tbl_pageMaster.id`. 0 orphans. |
| `createPermission` / `readPermission` / `updatePermission` / `deletePermission` | `bit`. The portal gates the page on `readPermission`; the other three gate buttons. |
| `createdOn` (2021-09-14 → 2026-07-29), `createdBy` | Audit. `createdBy` is a **userName string** (5 distinct grantors, e.g. `satbir`), not a UserID. There is no `modifiedOn` — rows are rewritten on save. |

Bit-combination distribution (all 736 rows):

| C | R | U | D | rows | reading |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 541 | full access |
| 0 | 0 | 0 | 0 | 123 | row exists but page denied |
| 0 | 1 | 0 | 0 | 54 | read-only |
| 1 | 1 | 1 | 0 | 7 | no delete |
| 0 | 1 | 1 | 1 | 4 | |
| 1 | 1 | 0 | 0 | 3 | |
| 1 | 0 | 0 | 0 | 2 | create without read (bad data) |
| 0 | 1 | 1 | 0 | 2 | |

Hygiene facts worth knowing: **487 of 736 rows belong to soft-deleted users** (never cleaned up), and **6 of the 22 live users have zero permission rows** (they can authenticate but see nothing, or are handled as SUPER ADMIN in code).

### 2.5 `tbl_loginUserLog` — App-Users change log
Rows: **1** (feature just switched on; the single row is `createdOn = 2026-07-29`). PK: `Id`.

Paired before/after columns: `previousName`/`modifiedName`, `previousUserName`/`modifiedUserName`, `previousEmail`/`modifiedEmail`, `previousRole`/`modifiedRole`, `previousBackDays`/`modifiedBackDays`, `previousStates`/`modifiedStates`.

| Column | Meaning |
|---|---|
| `userId` | The account that was changed → `tbl_loginUser.UserID`. |
| `action` | Only value present: `Created`. Expect `Modified` / `Deleted` as the code exercises more paths — treat as an open enum. |
| `previous*` / `modified*` | Stored as **strings**, even for numeric fields: `modifiedRole = "1"` is a `tbl_roles.Id`, `modifiedBackDays = "0"` is `backDaysAllowed`. On `Created` all `previous*` are NULL. |
| `previousStates` / `modifiedStates` | **CSV of `stateId`s**, e.g. `-1,2,1,3,...` — mirrors `tbl_loginUserStates` for that user; `-1` = ALL states. |
| `changedBy` (int → `UserID`), `changedByName` | Who made the edit. Note this one is an **int UserID**, unlike the `createdBy`/`deletedBy` name-strings elsewhere. |
| `createdOn` | When. |

### 2.6 `tbl_loginUserStates` — territory scope (adjacent, same screen)
Rows: **1,394**. PK: `id`. Columns `Userid` (→ `tbl_loginUser.UserID`, 4 orphan rows) and `stateId` (→ `tbl_states.stateId`; **`-1` = ALL states**, a sentinel with no row in `tbl_states`). Edited on the same App Users form, which is why its snapshot lives in `tbl_loginUserLog.*States`.

---

## 3. Linkages (verified)

Inside the subsystem — all confirmed by LEFT JOIN orphan counts:

```
tbl_loginUser.role        -> tbl_roles.Id                 (0 orphans)
tbl_pagePermission.userId -> tbl_loginUser.UserID         (0 orphans)
tbl_pagePermission.pageId -> tbl_pageMaster.id            (0 orphans)
tbl_loginUserStates.Userid-> tbl_loginUser.UserID         (4 orphans)
tbl_loginUserStates.stateId-> tbl_states.stateId          (-1 = ALL, no row)
tbl_loginUserLog.userId    -> tbl_loginUser.UserID
tbl_loginUserLog.changedBy -> tbl_loginUser.UserID
tbl_loginUserLog.modifiedRole / previousRole  -> tbl_roles.Id  (as a STRING)
tbl_loginUserLog.modifiedStates/previousStates-> CSV of tbl_states.stateId
```

Outward links — **weaker than they look, read this before joining**:

- **There is NO `personId` / salesperson foreign key on `tbl_loginUser`.** Portal identity and field identity are separate. `tbl_salesperson` also has a `userName` column and 54 rows match `tbl_loginUser.userName`, but the match is **not trustworthy**: `userName='sandeep'` maps to two salespersons (`ID` 561 "SANDEEP NIRMAL", `ID` 2771 "SANDEEP DUGGAL (PB)") while the portal account's `name` is "SANDEEP SHARMA"; `userName='jivo'` maps to salesperson "JIVOWELNESS". Treat a userName match as a *hint*, never as a join for reporting. (`tbl_salesperson` PK is `ID`, not `personId`.)
- **Audit strings, not keys.** `tbl_loginUser.CreatedBy`/`deletedBy`, `tbl_pageMaster.createdBy`/`LastModifyBy`/`DeletedBy` and `tbl_pagePermission.createdBy` are free-text names/handles. They are usually a `tbl_loginUser.name` or `userName` but casing varies (`BALJEET SINGH`, `satbir`, `LUCKY`) — match with `UPPER(...)` and expect misses. Only `tbl_loginUserLog.changedBy` is a real int FK.
- **Territory scope** (`tbl_loginUserStates.stateId` → `tbl_states.stateId`) is the one hard link out of the subsystem; `tbl_states` is the same state master used by retailers/beats/salespersons.
- `tbl_pageMaster.pageUrl` links to portal controllers, not to any table.

---

## 4. Portal mapping

| Portal page | `tbl_pageMaster` row | Tables read / written |
|---|---|---|
| **Masters > App Users** (`/LOGIN/INDEX`) | id 3 `APP USERS` | reads/writes `tbl_loginUser`; role dropdown from `tbl_roles`; state checkboxes write `tbl_loginUserStates`; every save appends `tbl_loginUserLog`. Soft-delete sets `deleted/deletedBy/deletionDate/deleteReason`. |
| Masters > App Users → *Change Backdate* tab | id 4 `CHANGE BACKDATE` | updates `tbl_loginUser.backDaysAllowed` (logged in `tbl_loginUserLog.*BackDays`). |
| Masters > App Users → *Email Preference* | id 5 `EMAIL PREFERENCE` | `tbl_loginUser.email`. |
| **Masters > Permissions** (`/PERMISSION/PERMISSION`) | id 2 `PERMISSION` | grid of `tbl_pageMaster` × 4 checkboxes for the chosen `tbl_loginUser`; saves `tbl_pagePermission`. |
| Masters > Permissions > **Add Page** (`/PERMISSION/ADDPAGE`) | id 1 `ADD PAGE` | inserts/edits `tbl_pageMaster`. |
| Masters (menu container) | id 21 `MASTERS` | gates the whole Masters menu. |
| *Every other portal page* | ids 6–33 | on load, the portal looks up `tbl_pagePermission` for `(session UserID, pageId)` and requires `readPermission = 1`. |

---

## 5. Example queries (read-only)

```sql
-- 1. Live portal accounts with role, back-dating allowance and territory count
SELECT u.UserID, u.userName, u.name, u.email,
       r.role, u.backDaysAllowed, u.approvedStatus,
       (SELECT COUNT(*) FROM tbl_loginUserStates s WHERE s.Userid = u.UserID) AS states,
       u.CreatedOn
FROM tbl_loginUser u
LEFT JOIN tbl_roles r ON r.Id = u.role
WHERE u.deleted = 0
ORDER BY r.role, u.userName;
```

```sql
-- 2. Full permission matrix for ONE live user (readable page list)
SELECT p.id AS pageId, LTRIM(RTRIM(p.pageName)) AS pageName, LTRIM(RTRIM(p.pageUrl)) AS pageUrl,
       pp.readPermission, pp.createPermission, pp.updatePermission, pp.deletePermission,
       pp.createdBy AS grantedBy, pp.createdOn
FROM tbl_pageMaster p
LEFT JOIN tbl_pagePermission pp
       ON pp.pageId = p.id
      AND pp.userId = (SELECT UserID FROM tbl_loginUser WHERE userName = 'dilpreet' AND deleted = 0)
WHERE p.DeletedOn IS NULL
ORDER BY p.id;   -- NULL / readPermission=0 => page hidden
```

```sql
-- 3. Who can open a given page (live users only)
SELECT u.UserID, u.userName, u.name, r.role,
       pp.createPermission, pp.updatePermission, pp.deletePermission
FROM tbl_pagePermission pp
JOIN tbl_loginUser u ON u.UserID = pp.userId AND u.deleted = 0
LEFT JOIN tbl_roles r ON r.Id = u.role
JOIN tbl_pageMaster p ON p.id = pp.pageId
WHERE LTRIM(RTRIM(p.pageName)) = 'SO REPORTS'
  AND pp.readPermission = 1
ORDER BY u.userName;
```

```sql
-- 4. Hygiene: permission rows still attached to deleted accounts (487 today)
SELECT u.UserID, u.userName, u.deletionDate, u.deletedBy, COUNT(*) AS stale_perm_rows
FROM tbl_pagePermission pp
JOIN tbl_loginUser u ON u.UserID = pp.userId
WHERE u.deleted = 1
GROUP BY u.UserID, u.userName, u.deletionDate, u.deletedBy
ORDER BY stale_perm_rows DESC;
```

```sql
-- 5. Live users with NO permissions at all (6 today) — can log in, see nothing
SELECT u.UserID, u.userName, u.name, r.role
FROM tbl_loginUser u
LEFT JOIN tbl_roles r ON r.Id = u.role
WHERE u.deleted = 0
  AND NOT EXISTS (SELECT 1 FROM tbl_pagePermission pp WHERE pp.userId = u.UserID)
ORDER BY u.userName;
```

```sql
-- 6. Territory scope per live user (-1 = ALL states)
SELECT u.userName, u.name,
       CASE WHEN MAX(CASE WHEN s.stateId = -1 THEN 1 ELSE 0 END) = 1
            THEN 'ALL STATES' ELSE NULL END AS allFlag,
       COUNT(*) AS scopeRows
FROM tbl_loginUser u
JOIN tbl_loginUserStates s ON s.Userid = u.UserID
WHERE u.deleted = 0
GROUP BY u.userName, u.name
ORDER BY u.userName;
```

```sql
-- 7. App Users change log (before -> after), newest first
SELECT l.Id, l.createdOn, l.action,
       l.userId, u.userName AS targetUser, l.changedByName,
       l.previousName, l.modifiedName,
       l.previousRole, l.modifiedRole,          -- strings holding tbl_roles.Id
       l.previousBackDays, l.modifiedBackDays,
       l.previousStates, l.modifiedStates       -- CSV of stateId, -1 = ALL
FROM tbl_loginUserLog l
LEFT JOIN tbl_loginUser u ON u.UserID = l.userId
ORDER BY l.createdOn DESC;
```

**Caveats to keep applying:** filter `deleted = 0` on `tbl_loginUser` (only 22 of 87 are live); `tbl_pageMaster` rows are live when `DeletedOn IS NULL`; trim `pageName`/`pageUrl` (leading tabs); never select or display `tbl_loginUser.password`; `1899-12-30` is the empty-date sentinel elsewhere in DSR — in these tables empty dates are plain NULL, so test `IS NULL` **and** `> '1900-01-01'` when in doubt.
