# Spec: `dsr users` — portal users & permissions commands (read-only)

Domain: web/back-office identity & RBAC (`tbl_loginUser`, `tbl_roles`, `tbl_pageMaster`, `tbl_pagePermission`, `tbl_loginUserLog`, `tbl_loginUserStates`).
See `study/vault/portal-users-and-permissions.md` for the data model.

## Ergonomics (mirrors existing `query` / `count` / `peek` / `schema`)

- Command group: `dsr users <subcommand>` (a cobra parent registered via `init(){ register(newUsersCmd) }`, subcommands attached to it).
- Global flags already available and honoured unchanged: `--profile`, `--db`, `--json`, `--csv`, `--compact`, `--quiet`, `--limit`, `--timeout`, `--select`.
- Default output is the table renderer; `--json` for machine use. All queries go through `app.DB.Query` (SELECT-only guard stays in force).
- Shared local flags across the group:
  - `--all` — include soft-deleted accounts (default: only `deleted = 0`).
  - `--user <userName|UserID>` — resolve either form: numeric ⇒ `UserID`, else exact `userName`, else `UPPER(name) LIKE '%…%'`.
  - `--role <name|id>` — filter by `tbl_roles`.
  - `--page <pageName|id>` — filter by `tbl_pageMaster`.
  - `--from` / `--to` (`YYYY-MM-DD`) — date window, applied to the command's natural date column.
- **Never** select `tbl_loginUser.password`; the column is excluded from every SELECT below and should be rejected if passed via `--select`.

---

## 1. `dsr users list`

List portal login accounts with role, back-days and territory scope.

Flags: `--all`, `--role`, `--from/--to` (on `CreatedOn`), `--search <text>` (name/userName/email), `--limit`.

```sql
SELECT u.UserID, u.userName, u.name, u.email,
       r.role,
       u.backDaysAllowed,
       u.approvedStatus,
       u.CreatedBy, u.CreatedOn,
       u.deleted, u.deletedBy, u.deletionDate,
       (SELECT COUNT(*) FROM tbl_loginUserStates s WHERE s.Userid = u.UserID) AS stateScopes,
       (SELECT COUNT(*) FROM tbl_pagePermission pp
         WHERE pp.userId = u.UserID AND pp.readPermission = 1)               AS readablePages
FROM tbl_loginUser u
LEFT JOIN tbl_roles r ON r.Id = u.role
WHERE (@all = 1 OR u.deleted = 0)
  AND (@role IS NULL OR r.role = @role OR u.role = @roleId)
  AND (@search IS NULL OR UPPER(u.userName) LIKE @search
       OR UPPER(u.name) LIKE @search OR UPPER(u.email) LIKE @search)
  AND (@from IS NULL OR u.CreatedOn >= @from)
  AND (@to   IS NULL OR u.CreatedOn <  DATEADD(day, 1, @to))
ORDER BY u.deleted, r.role, u.userName;
```

## 2. `dsr users show --user <u>`

Full profile of one account: identity, role, back-days, approval, state scope list, and permission summary.

Flags: `--user` (required), `--json`.

```sql
-- header
SELECT u.UserID, u.userName, u.name, u.email, r.role, u.backDaysAllowed,
       u.approvedStatus, u.approvedBy, u.approvedOn,
       u.CreatedBy, u.CreatedOn, u.deleted, u.deletedBy, u.deletionDate, u.deleteReason
FROM tbl_loginUser u
LEFT JOIN tbl_roles r ON r.Id = u.role
WHERE u.UserID = @userId;

-- territory scope (-1 = ALL STATES)
SELECT s.stateId, COALESCE(st.state, CASE WHEN s.stateId = -1 THEN 'ALL STATES' END) AS state
FROM tbl_loginUserStates s
LEFT JOIN tbl_states st ON st.stateId = s.stateId
WHERE s.Userid = @userId
ORDER BY s.stateId;

-- permission summary
SELECT COUNT(*) AS pageRows,
       SUM(CASE WHEN readPermission   = 1 THEN 1 ELSE 0 END) AS canRead,
       SUM(CASE WHEN createPermission = 1 THEN 1 ELSE 0 END) AS canCreate,
       SUM(CASE WHEN updatePermission = 1 THEN 1 ELSE 0 END) AS canUpdate,
       SUM(CASE WHEN deletePermission = 1 THEN 1 ELSE 0 END) AS canDelete
FROM tbl_pagePermission WHERE userId = @userId;
```

## 3. `dsr users perms --user <u>`

The permission matrix for one user across the whole page catalogue (missing rows shown as denied).

Flags: `--user` (required), `--granted` (only rows with any bit set), `--readable` (only `readPermission = 1`).

```sql
SELECT p.id AS pageId,
       LTRIM(RTRIM(p.pageName)) AS pageName,
       LTRIM(RTRIM(p.pageUrl))  AS pageUrl,
       COALESCE(pp.readPermission,   CAST(0 AS bit)) AS [read],
       COALESCE(pp.createPermission, CAST(0 AS bit)) AS [create],
       COALESCE(pp.updatePermission, CAST(0 AS bit)) AS [update],
       COALESCE(pp.deletePermission, CAST(0 AS bit)) AS [delete],
       pp.createdBy AS grantedBy, pp.createdOn AS grantedOn
FROM tbl_pageMaster p
LEFT JOIN tbl_pagePermission pp ON pp.pageId = p.id AND pp.userId = @userId
WHERE p.DeletedOn IS NULL
  AND (@granted  = 0 OR COALESCE(pp.readPermission,0)+COALESCE(pp.createPermission,0)
                       +COALESCE(pp.updatePermission,0)+COALESCE(pp.deletePermission,0) > 0)
  AND (@readable = 0 OR pp.readPermission = 1)
ORDER BY p.id;
```

## 4. `dsr users page-access --page <p>`

Reverse lookup: who can reach a given portal page.

Flags: `--page` (required, name or id), `--all` (include deleted accounts), `--action read|create|update|delete` (default `read`).

```sql
SELECT u.UserID, u.userName, u.name, r.role,
       pp.readPermission, pp.createPermission, pp.updatePermission, pp.deletePermission,
       pp.createdBy AS grantedBy, pp.createdOn AS grantedOn,
       u.deleted
FROM tbl_pagePermission pp
JOIN tbl_pageMaster  p ON p.id = pp.pageId
JOIN tbl_loginUser   u ON u.UserID = pp.userId
LEFT JOIN tbl_roles  r ON r.Id = u.role
WHERE (p.id = @pageId OR UPPER(LTRIM(RTRIM(p.pageName))) = @pageName)
  AND (@all = 1 OR u.deleted = 0)
  AND ( (@action = 'read'   AND pp.readPermission   = 1)
     OR (@action = 'create' AND pp.createPermission = 1)
     OR (@action = 'update' AND pp.updatePermission = 1)
     OR (@action = 'delete' AND pp.deletePermission = 1) )
ORDER BY u.deleted, u.userName;
```

## 5. `dsr users pages`

The portal page catalogue (`tbl_pageMaster`) with how many live users can read each page.

Flags: `--search <text>`, `--all` (include `DeletedOn IS NOT NULL`).

```sql
SELECT p.id, LTRIM(RTRIM(p.pageName)) AS pageName, LTRIM(RTRIM(p.pageUrl)) AS pageUrl,
       COUNT(CASE WHEN u.deleted = 0 AND pp.readPermission = 1 THEN 1 END) AS liveReaders,
       COUNT(CASE WHEN pp.id IS NOT NULL THEN 1 END)                       AS permRows,
       p.createdOn, p.LastModifiedOn, p.LastAction
FROM tbl_pageMaster p
LEFT JOIN tbl_pagePermission pp ON pp.pageId = p.id
LEFT JOIN tbl_loginUser u       ON u.UserID = pp.userId
WHERE (@all = 1 OR p.DeletedOn IS NULL)
  AND (@search IS NULL OR UPPER(p.pageName) LIKE @search OR UPPER(p.pageUrl) LIKE @search)
GROUP BY p.id, p.pageName, p.pageUrl, p.createdOn, p.LastModifiedOn, p.LastAction
ORDER BY p.id;
```

## 6. `dsr users roles`

Role catalogue with live/total account counts. No flags beyond globals.

```sql
SELECT r.Id, r.role,
       COUNT(CASE WHEN u.deleted = 0 THEN 1 END) AS liveUsers,
       COUNT(u.UserID)                           AS totalUsers
FROM tbl_roles r
LEFT JOIN tbl_loginUser u ON u.role = r.Id
GROUP BY r.Id, r.role
ORDER BY r.Id;
```

## 7. `dsr users log`

App-Users change log (before → after) from `tbl_loginUserLog`.

Flags: `--user` (target account), `--by <userName|UserID>` (who made the change), `--action <Created|Modified|Deleted>`, `--from/--to` on `createdOn`, `--limit`.

```sql
SELECT l.Id, l.createdOn, l.action,
       l.userId, tu.userName AS targetUser,
       l.changedBy, l.changedByName,
       l.previousName,     l.modifiedName,
       l.previousUserName, l.modifiedUserName,
       l.previousEmail,    l.modifiedEmail,
       l.previousRole,     l.modifiedRole,        -- strings holding tbl_roles.Id
       pr.role AS previousRoleName, mr.role AS modifiedRoleName,
       l.previousBackDays, l.modifiedBackDays,
       l.previousStates,   l.modifiedStates       -- CSV of stateId, -1 = ALL
FROM tbl_loginUserLog l
LEFT JOIN tbl_loginUser tu ON tu.UserID = l.userId
LEFT JOIN tbl_roles pr ON TRY_CAST(l.previousRole AS int) = pr.Id
LEFT JOIN tbl_roles mr ON TRY_CAST(l.modifiedRole AS int) = mr.Id
WHERE (@userId IS NULL OR l.userId    = @userId)
  AND (@byId   IS NULL OR l.changedBy = @byId)
  AND (@action IS NULL OR l.action    = @action)
  AND (@from   IS NULL OR l.createdOn >= @from)
  AND (@to     IS NULL OR l.createdOn <  DATEADD(day, 1, @to))
ORDER BY l.createdOn DESC, l.Id DESC;
```

## 8. `dsr users audit`

One-shot RBAC hygiene report — the four findings that actually exist in the data today.

Flags: `--check stale|orphan|noperms|blank|all` (default `all`), `--json`.

```sql
-- a) permission rows still attached to soft-deleted accounts (487 rows today)
SELECT 'stale-perms' AS finding, u.UserID, u.userName, u.deletionDate, COUNT(*) AS rows
FROM tbl_pagePermission pp JOIN tbl_loginUser u ON u.UserID = pp.userId
WHERE u.deleted = 1
GROUP BY u.UserID, u.userName, u.deletionDate

UNION ALL
-- b) live accounts with zero permission rows (6 today)
SELECT 'no-perms', u.UserID, u.userName, NULL, 0
FROM tbl_loginUser u
WHERE u.deleted = 0
  AND NOT EXISTS (SELECT 1 FROM tbl_pagePermission pp WHERE pp.userId = u.UserID)

UNION ALL
-- c) all-zero permission rows (123 today) — row present but page denied
SELECT 'blank-perm-row', u.UserID, u.userName, NULL, COUNT(*)
FROM tbl_pagePermission pp JOIN tbl_loginUser u ON u.UserID = pp.userId
WHERE pp.readPermission = 0 AND pp.createPermission = 0
  AND pp.updatePermission = 0 AND pp.deletePermission = 0
GROUP BY u.UserID, u.userName

UNION ALL
-- d) state scopes pointing at a non-existent user (4 today)
SELECT 'orphan-state-scope', s.Userid, NULL, NULL, COUNT(*)
FROM tbl_loginUserStates s
WHERE NOT EXISTS (SELECT 1 FROM tbl_loginUser u WHERE u.UserID = s.Userid)
GROUP BY s.Userid
ORDER BY 1, 6 DESC;
```

## 9. `dsr users scope`

Territory scope per portal user (which states they may see).

Flags: `--user`, `--state <name|id>` (reverse: who can see this state), `--all`.

```sql
SELECT u.UserID, u.userName, u.name, r.role,
       s.stateId,
       COALESCE(st.state, CASE WHEN s.stateId = -1 THEN 'ALL STATES' END) AS state
FROM tbl_loginUserStates s
JOIN tbl_loginUser u ON u.UserID = s.Userid
LEFT JOIN tbl_roles  r  ON r.Id = u.role
LEFT JOIN tbl_states st ON st.stateId = s.stateId
WHERE (@all = 1 OR u.deleted = 0)
  AND (@userId IS NULL OR u.UserID = @userId)
  AND (@stateId IS NULL OR s.stateId IN (@stateId, -1))
ORDER BY u.userName, s.stateId;
```

---

## Implementation notes

- Resolve `--user` / `--page` / `--role` / `--state` to ids in a small helper before the main query, so the SELECTs stay parameterised (`sql.Named`) and injection-free — same pattern as `lookupTable` in `internal/cli/peek.go`.
- `bit` columns render as `true/false` in `--json`; for table output render as `Y`/`-` for a readable matrix in `users perms`.
- Everything here is `SELECT`-only; the group must never gain a write path (RULE 0).
- Suppress `password` unconditionally, including when the user passes `--select password`.
