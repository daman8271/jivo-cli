# Subsystem: sales-person-master

**Portal menu:** Masters > Sales Person, Masters > App Users
**DB:** SQL Server `DSR_V6` (schema `dbo`)
**Tables in scope:** `tbl_salesperson`, `tbl_PersonType`, `tbl_PersonGroupMaster`, `tbl_hierarchy`, `tbl_salespersonLogs`, `tbl_dsrjwpl`
**Verified live:** 2026-07-29 (all counts / joins below run against production via `./dsr query`)

---

## 1. Overview

This is the **field workforce master** of JIVO's DSR (Daily Sales Report / SFA) system — the one record per human being who carries the DSR mobile app into the market.

Everything else in DSR hangs off it. A row in `tbl_salesperson` is simultaneously:

- **an HR record** — name, father/spouse, DOB, gender, marital status, Aadhaar/PAN, date of joining / exit + exit reason, source of hire, emergency contact, photo;
- **a payroll record** — salary vs ActualSalary, daily allowance, internet & mobile reimbursement, EPF/ESI/LWF opt-in + percentages + statutory numbers, bank name/branch/account/IFSC, CL (casual leave) entitlement;
- **an app-login record** — `userName` + encrypted `password`, GCM/FCM push id, `device`, `androidId`, `appVersion`, `lastLoginDate`;
- **a field-control record** — home lat/long and home State/Zone/Area (the geo-fence anchor used to validate GPS attendance), `distanceAllowed` (metres a person may stray), `startTime`/`endTime` working window, `weekOff`, `lockOffBeat` (may they sell outside their assigned beat?), `isSchemeMandatory`, `trackingTime`;
- **an org-chart node** — `PERSONTYPE` (SO / ASM / RSM / Promoter / Merchandiser …), `personGroup` (GT / MT / Olive / Wheatgrass / HORECA channel), `parent` + `parentType` (who they report to), `headState`/`headZone` (the territory they *head*, for managers), `distributor` (the distributor a promoter is parked at);
- **an approval record** — `approvedStatus` / `approvedBy` / `approvedOn`, because a newly created Sales Person is not usable until an admin approves it.

The four satellite tables are lookups and audit around it: `tbl_PersonType` and `tbl_PersonGroupMaster` are the dropdown masters for designation and channel-group; `tbl_salespersonLogs` is the field-level before/after audit trail of every create/edit on the Sales Person page; `tbl_dsrjwpl` maps a DSR person id to the JIVO Wellness Pvt Ltd (JWPL) HR employee code; `tbl_hierarchy` is a legacy flat "person → ASM" snapshot with the ASM's shared passcode.

**Scale (live 2026-07-29):** 1,809 person rows, of which **192 are live** (`deleted = 0`) and 1,617 soft-deleted (attrition — this is a promoter-heavy, high-churn field force).

---

## 2. Tables

### 2.1 `tbl_salesperson` — the field-workforce master (one row per SO / ASM / Promoter / …)

- **Rows:** 1,809 total · 192 live (`deleted = 0`) · 1,617 soft-deleted
- **PK:** none declared in the catalog, but `ID` (int) is unique — `COUNT(*) = COUNT(DISTINCT ID) = 1809`. Treat `ID` as the key; the rest of DSR references it as `personId` / `userId`.
- **Columns:** 82

**Identity & contact**

| Column | Notes |
|---|---|
| `ID` | de-facto PK. Referenced everywhere as `personId`. Max seen ~4927. |
| `PERSONNAME` | display name, free text, uppercase-ish, not unique, often trailing spaces — always `LTRIM(RTRIM())` before name matching. |
| `PERSONTYPE` | **stored as the text label, not an id** (e.g. `'SO'`, `'PROMOTER(MT)'`). Joins to `tbl_PersonType.PersonType`. 192/192 live rows match. |
| `CONTACTNO`, `EMAIL`, `ADDRESS` | contact; `CONTACTNO` frequently has embedded spaces (`' 84371 97726'`). |
| `employeeId` | JWPL HR code, e.g. `JWPL0238`. Populated on 621/1809 rows, has leading/trailing spaces, and **is not unique** (e.g. `JWPL2389` and `JWPL2528` appear 3× each — re-hires / duplicates). |
| `STATE` | **dead column** — every row is `''` or NULL. The real state mapping is the child table `tbl_PersonState`. Do not use. |

**App login / device**

`userName` (185 distinct across 192 live rows — 7 dupes), `password` (base64 of an encrypted blob, e.g. `GF1YTyle2c8BA5piIAm1MA==` — never print), `GcmId` (push token), `device`, `androidId`, `appVersion`, `lastLoginDate` (max 2026-07-29T17:35Z — this is the freshest activity signal on the table), `location` (last reported address string).

**Org / territory**

| Column | Meaning |
|---|---|
| `parent` (int) | reports-to → `tbl_salesperson.ID`. **Verified: 169/169 live rows with `parent > 0` resolve.** `0` / NULL = top of chain. |
| `parentType` | designation of the parent, denormalised. Distribution: ASM 799, SO 605, RSM 146, SR 11, CSM 6, ASE 5, MERCHANDISER 3, ZSM 2, NULL 232. Note `ZSM` appears here but **not** in `tbl_PersonType`. |
| `personGroup` | channel group → `tbl_PersonGroupMaster.GroupCode`. 188/192 live match (4 blank). Values in use: `Wheatgrass` 663, `GT` 628, `MT` 473, `''` 40, `HORECA` 3. |
| `distributor` (nvarchar) | the distributor this person is attached to. **Holds `tbl_retailers.Id` as a string** (`tbl_retailers` stores distributors too, `type = 'Distributor'`). `'-1'` = none. Cast to compare: `CAST(r.Id AS varchar(20)) = s.distributor`. |
| `distributorRequired` (bit) | must this person pick a distributor when booking? 59 rows true. |
| `homeState` / `homeZone` / `homeArea` (int) | where the person *lives* / is based → `tbl_states.stateId`, `tbl_zones.zoneId`, `tbl_areas.areaId`. `-1` = unset. Of 192 live: 159 have a valid state, 28 a valid zone, only 20 a valid area — **zone/area are sparsely maintained; don't build reports that assume they're set.** |
| `headState` / `headZone` (int) | the territory the person *heads* (managers). `-1` = unset; only 63 live rows have `headZone > 0`. Same lookup tables as home*. |

**Field-control / policy**

`homeLat`, `homeLong` (nvarchar, often `''`) — geo-fence anchor; `distanceAllowed` (metres the person may be from a retailer/home before attendance is flagged; typical 1000, some absurd 10000000); `startTime` / `endTime` (time — working window; the date part is the .NET zero-date `0001-01-01`, ignore it); `isLocationInWorkingHours` (bit); `lockOffBeat` (bit, 132 rows true — block sales outside the assigned beat); `weekOff` (nvarchar(8) — `'SUN'` 414, `'MON'` 53, `'WED'` 23, `'THU'` 22, `'TUE'` 19, `'FRI'` 12, **`'--SE'` 1116 = the truncated `--SELECT--` placeholder, i.e. unset**, NULL 150); `isSchemeMandatory` (bit, 2 rows); `trackingTime` (int — **0 on all 1,809 rows, effectively unused**); `dailyStatus` (NULL on every row — unused); `reportUom` (NULL on every row — unused).

**Payroll / statutory** — mostly *configured but not switched on* in this DB:

`salary` (>0 on 50 rows), `ActualSalary` (>0 on 36), `DailyAllowances`, `Internet`, `Mobile`, `isTaGiven` (travel allowance — **true on 0 rows**), `EPFGiven` / `ESIGiven` / `LWFeeGiven` / `CLGiven` (**all true on 0 rows**), `EPFPercentage` (default 12), `ESIPercentage` (default 1.75), `LWFeeAmount` (default 10), `CLCount`, `epfNo`, `esicNo`, `adharCardNo`, `PANno`, `bankName`, `bankAddress`, `bankAccNo` (populated on 48 rows), `ifscCode`. **Conclusion: DSR holds the payroll *fields* but JIVO does not run payroll here — treat these as reference/HR-capture only.**

**HR lifecycle**

`DOB`, `gender` (`Male` / `Female` / NULL), `maritalStatus` (`Married` / `Single` / **`'--SELECT--'` = unset, 1,554 rows**), `spouseName`, `anniversaryDate`, `fatherName`, `emergencyName`, `emergencyContact`, `dateOfJoining` (max 2026-07-08), `sourceOfHire`, `dateOfExit`, `exitReason` (free text, e.g. `LEFT THE JOB`), `image` (photo path), `remark`.

**Audit / soft-delete / approval**

`deleted` (0 = live, 1 = deleted — **there is no other value**), `deletedBy`, `deletionDate`, `CreatedBy`, `CreatedOn`, `approvedStatus`, `approvedBy`, `approvedOn`.

**`approvedStatus` decode (verified distinct values — only two exist):**

| Value | Rows | Meaning |
|---|---|---|
| `1` | 1,010 | pending / not approved (`approvedBy`, `approvedOn` NULL) |
| `3` | 799 | approved (`approvedBy` = admin name e.g. `IT`, `approvedOn` set) |

### 2.2 `tbl_PersonType` — designation lookup (the Person Type dropdown)

- **Rows:** 13 · **PK:** `Id`
- `PersonType` (label stored on `tbl_salesperson.PERSONTYPE`) and `PersonTypeCode` (same string, differing only in case for `MERCHANDISER`/`Merchandiser`).

| Id | PersonType | Live people |
|---|---|---|
| 1 | ASM (Area Sales Manager) | 17 |
| 2 | CSM | 0 |
| 3 | PROMOTER(GT) | 42 |
| 4 | PROMOTER(MT) | 45 |
| 5 | RSM (Regional Sales Manager) | 4 |
| 6 | SO (Sales Officer) | 77 |
| 7 | SR (Sales Representative) | 2 |
| 8 | MERCHANDISER | 2 |
| 9 | PROMOTER(MTW) | 0 |
| 10 | PROMOTER(GTW) | 2 |
| 11 | NSM (National Sales Manager) | 0 |
| 12 | SUPERVISOR | 0 |
| 13 | ASE | 1 |

**Gotcha:** `tbl_salesperson.PERSONTYPE` contains two values that are *not* in this lookup — `PROMOTER(Wheatgrass)` (18 rows, all deleted) and, via `parentType`, `ZSM`. Left-join, don't inner-join, if you need every row.

### 2.3 `tbl_PersonGroupMaster` — channel/brand group lookup

- **Rows:** 6 · **PK:** `id`
- `GroupCode` is what `tbl_salesperson.personGroup` stores; `GroupName` is the display label.

| id | GroupCode | GroupName |
|---|---|---|
| 1 | GT | GT (General Trade) |
| 2 | MT | MT (Modern Trade) |
| 3 | GTO GT | Olive |
| 4 | MTO MT | Olive |
| 5 | Wheatgrass | Wheatgrass |
| 7 | HORECA | HORECA |

(id 6 is missing — deleted at some point.) Note `tbl_salesperson.personGroup` actually stores plain `GT`/`MT`/`Wheatgrass`/`HORECA` — the `GTO GT` / `MTO MT` olive codes are not used on any live person row.

### 2.4 `tbl_hierarchy` — legacy ASM reporting snapshot

- **Rows:** 117 · **PK:** none. **Columns:** 3 — `personname`, `asm`, `passcode`
- 83 distinct `personname`, 22 distinct `asm`, **22 distinct `passcode`** → *passcode is 1:1 with the ASM*, i.e. it is the ASM's shared login/verification passcode (format: 10 digits + 2 letters, e.g. `914215182AD`), repeated on every subordinate row.
- Matched by name against `tbl_salesperson`: 113/120 rows resolve, but **only 45 point at a currently-live person** — this table is **stale**. It has no id columns, no timestamps and no soft-delete, so it is a flat text snapshot, not the live org chart.
- **The live reporting chain is `tbl_salesperson.parent` / `parentType`, not this table.** Use `tbl_hierarchy` only for the ASM passcode or for historical reconciliation.

### 2.5 `tbl_salespersonLogs` — field-level edit audit for the Sales Person page

- **Rows:** 3 (feature only went live 2026-07-25 — `createdOn` spans 2026-07-25 → 2026-07-29). Expect this to grow.
- **PK:** `Id`
- `personId` → `tbl_salesperson.ID`; `action` ∈ {`Created`, `Modified`}; `changedBy` → **`tbl_loginUser.UserID`** (verified: id 91 = `JASHANDEEP KAUR`), `changedByName` denormalised; `createdOn` timestamp.
- The body is 16 **previous*/modified*** pairs, all stored as strings, covering exactly the fields the portal form exposes: `EmployeeId`, `Name`, `ContactNo`, `UserName`, `PersonType`, `States`, `WeekOff`, `HeadState`, `HeadZone`, `HomeState`, `HomeZone`, `HomeArea`, `DistanceAllowed`, `Group`, `ParentType`, `Parent`, `DateOfJoining` — plus `passwordChanged` (`'Yes'`/`'No'`, the password value itself is never logged).
- On `action = 'Created'` every `previous*` is NULL. Numeric-ish fields (`modifiedParent`, `modifiedHeadZone`, …) are the **ids as text** — cast before joining, and `-1`/`'-1'` still means unset.

### 2.6 `tbl_dsrjwpl` — DSR person → JWPL HR employee-code map

- **Rows:** 317 · **PK:** none declared; `id` is unique (317/317), `jwplcode` is not (307 distinct).
- **`id` IS `tbl_salesperson.ID`** — verified: all 317 rows resolve against `tbl_salesperson.ID` (id range 11–2430).
- `jwplcode` is the JIVO Wellness employee code (`JWPL####`). It agrees with `tbl_salesperson.employeeId` on **282 of 317** rows — so this table is an **independent/legacy code map that has drifted** from the `employeeId` column now maintained on the master. When the two disagree, `tbl_salesperson.employeeId` is the one the portal edits (and the one logged in `tbl_salespersonLogs`).

---

## 3. Linkages (all verified with a live query)

### Inside the subsystem

| From | To | Join | Evidence |
|---|---|---|---|
| `tbl_salesperson.parent` | `tbl_salesperson.ID` | `p.ID = s.parent` | 169/169 live rows with `parent > 0` resolve |
| `tbl_salesperson.PERSONTYPE` | `tbl_PersonType.PersonType` | string equality | 192/192 live rows match |
| `tbl_salesperson.personGroup` | `tbl_PersonGroupMaster.GroupCode` | string equality | 188/192 live rows match |
| `tbl_salespersonLogs.personId` | `tbl_salesperson.ID` | int | all 3 rows resolve |
| `tbl_dsrjwpl.id` | `tbl_salesperson.ID` | int | **317/317** |
| `tbl_hierarchy.personname` / `.asm` | `tbl_salesperson.PERSONNAME` | `UPPER(LTRIM(RTRIM(...)))` — **name matching, fragile** | 113/120 and 119/120 |

### Out to other subsystems

| From | To | Join | Evidence |
|---|---|---|---|
| `tbl_salesperson.homeState`, `.headState` | `tbl_states.stateId` | int (`-1` = unset) | 159/192 live have a valid homeState |
| `tbl_salesperson.homeZone`, `.headZone` | `tbl_zones.zoneId` | int (`-1` = unset) | 28/192 live |
| `tbl_salesperson.homeArea` | `tbl_areas.areaId` | int (`-1` = unset) | 20/192 live |
| `tbl_salesperson.distributor` | `tbl_retailers.Id` (rows with `type = 'Distributor'`) | `CAST(r.Id AS varchar(20)) = s.distributor`; `'-1'` = none | spot-verified (e.g. person 55 → retailer 9748 `OM PRAKASH MAHAJAN & COMPANY`, type `Distributor`) |
| `tbl_PersonState.personId` | `tbl_salesperson.ID` | int — **the real multi-state territory map** (1,937 rows / 1,811 persons / 22 states); `tbl_PersonState.stateId` → `tbl_states.stateId` | 182 of the 192 live persons have ≥1 state row |
| `tbl_beats.personId` | `tbl_salesperson.ID` | int | 3,920 / 3,947 live beats resolve |
| `tbl_salesPersonAttendance.personId` | `tbl_salesperson.ID` | int (426k rows; `status` e.g. `EOD`) | spot-verified against latest rows |
| `tbl_salesPersonMontlhyTarget.userId` | `tbl_salesperson.ID` | int — **note the column is `userId`, not `personId`**, and the table name is misspelled `Montlhy` | spot-verified |
| `tbl_salesPersonMontlhyStock.*`, `tbl_TA_PersonRetailerKm.*`, `tbl_AttendanceAudit.*`, `tbl_loginUserStates` | `tbl_salesperson.ID` | int `personId` (out of scope here) | — |
| `tbl_salespersonLogs.changedBy` | **`tbl_loginUser.UserID`** (portal admin, *not* a salesperson) | int | id 91 = `JASHANDEEP KAUR`, role 1 |

**Do not confuse the two user tables:** `tbl_loginUser` (87 rows) = *web portal* back-office logins; `tbl_salesperson` (1,809) = *mobile app* field users. `tbl_salespersonLogs.changedBy` points at the former.

---

## 4. Portal mapping

| Portal page | Reads | Writes |
|---|---|---|
| **Masters > Sales Person** (list / add / edit / delete / approve) | `tbl_salesperson` (grid + form), `tbl_PersonType` (Person Type dropdown), `tbl_PersonGroupMaster` (Group dropdown), `tbl_salesperson` again for the Reporting-To (`parent`) picker filtered by `parentType`, `tbl_states`/`tbl_zones`/`tbl_areas` for Home/Head geo dropdowns, `tbl_retailers` (`type='Distributor'`) for the Distributor picker | `tbl_salesperson` (insert/update; delete = `deleted=1` + `deletedBy` + `deletionDate`; approve = `approvedStatus=3` + `approvedBy` + `approvedOn`) and one audit row into `tbl_salespersonLogs` per save |
| **Masters > Sales Person > (multi-state territory)** | `tbl_PersonState` | `tbl_PersonState` |
| **Masters > App Users** | `tbl_salesperson` (`userName`, `password`, `device`, `appVersion`, `GcmId`, `lastLoginDate`, `approvedStatus`) — the app-credential view of the same rows | `tbl_salesperson` (credential/approval columns) + `tbl_salespersonLogs.passwordChanged` |
| **Sales Person edit-history / audit view** | `tbl_salespersonLogs` joined to `tbl_loginUser` for the editor's name | — |
| Legacy / batch | `tbl_dsrjwpl` (HR code map, used by JWPL payroll-side exports), `tbl_hierarchy` (old ASM passcode sheet) | rarely written |

---

## 5. Example queries (ready to run)

All are `SELECT`-only and already apply the `deleted = 0` and `-1`-sentinel caveats.

```sql
-- 1. Live field force by designation and channel group, with head-count and last app login
SELECT  s.PERSONTYPE,
        ISNULL(NULLIF(s.personGroup,''),'(unset)') AS personGroup,
        COUNT(*)                                   AS people,
        MAX(s.lastLoginDate)                       AS lastAppLogin
FROM    dbo.tbl_salesperson s
WHERE   ISNULL(s.deleted,0) = 0
GROUP BY s.PERSONTYPE, ISNULL(NULLIF(s.personGroup,''),'(unset)')
ORDER BY people DESC;
```

```sql
-- 2. Full live roster with reporting parent, home state and attached distributor
SELECT  s.ID, LTRIM(RTRIM(s.PERSONNAME)) AS personName, s.PERSONTYPE, s.personGroup,
        LTRIM(RTRIM(s.employeeId))       AS jwplCode,
        s.parentType,
        LTRIM(RTRIM(p.PERSONNAME))       AS reportsTo,
        st.state                         AS homeState,
        z.zone                           AS homeZone,
        r.retailerName                   AS distributorName,
        s.weekOff, s.distanceAllowed, s.dateOfJoining, s.lastLoginDate
FROM        dbo.tbl_salesperson s
LEFT JOIN   dbo.tbl_salesperson p ON p.ID = s.parent AND s.parent > 0
LEFT JOIN   dbo.tbl_states     st ON st.stateId = s.homeState AND s.homeState > 0
LEFT JOIN   dbo.tbl_zones      z  ON z.zoneId  = s.homeZone  AND s.homeZone  > 0
LEFT JOIN   dbo.tbl_retailers  r  ON CAST(r.Id AS varchar(20)) = s.distributor
                                  AND s.distributor NOT IN ('-1','0','')
WHERE   ISNULL(s.deleted,0) = 0
ORDER BY s.PERSONTYPE, personName;
```

```sql
-- 3. Pending approvals — Sales Person records created but never approved (approvedStatus 1)
SELECT  s.ID, LTRIM(RTRIM(s.PERSONNAME)) AS personName, s.PERSONTYPE,
        s.CreatedBy, s.CreatedOn, s.dateOfJoining
FROM    dbo.tbl_salesperson s
WHERE   ISNULL(s.deleted,0) = 0
  AND   s.approvedStatus = 1
  AND   s.CreatedOn <> '1899-12-30'      -- empty-date sentinel
ORDER BY s.CreatedOn DESC;
```

```sql
-- 4. ASM span-of-control: each live manager and the live people reporting to them
SELECT  m.ID                              AS managerId,
        LTRIM(RTRIM(m.PERSONNAME))        AS manager,
        m.PERSONTYPE                      AS managerType,
        COUNT(c.ID)                       AS directReports
FROM        dbo.tbl_salesperson m
LEFT JOIN   dbo.tbl_salesperson c ON c.parent = m.ID AND ISNULL(c.deleted,0) = 0
WHERE   ISNULL(m.deleted,0) = 0
  AND   m.PERSONTYPE IN ('ASM','RSM','NSM','ASE','SUPERVISOR','CSM')
GROUP BY m.ID, m.PERSONNAME, m.PERSONTYPE
ORDER BY directReports DESC;
```

```sql
-- 5. Multi-state territory coverage (the real map — tbl_salesperson.STATE is dead)
SELECT  st.state,
        COUNT(DISTINCT s.ID) AS livePeople
FROM        dbo.tbl_PersonState ps
JOIN        dbo.tbl_salesperson s  ON s.ID = ps.personId
JOIN        dbo.tbl_states      st ON st.stateId = ps.stateId
WHERE   ISNULL(s.deleted,0) = 0
GROUP BY st.state
ORDER BY livePeople DESC;
```

```sql
-- 6. Edit audit: what actually changed on the Sales Person page, and who changed it
SELECT  l.createdOn, l.action, l.personId,
        LTRIM(RTRIM(s.PERSONNAME))  AS personNow,
        u.name                      AS changedBy,
        l.previousName + ' -> ' + l.modifiedName            AS nameChange,
        l.previousPersonType + ' -> ' + l.modifiedPersonType AS typeChange,
        l.previousParent + ' -> ' + l.modifiedParent         AS parentChange,
        l.passwordChanged
FROM        dbo.tbl_salespersonLogs l
LEFT JOIN   dbo.tbl_salesperson s ON s.ID = l.personId
LEFT JOIN   dbo.tbl_loginUser   u ON u.UserID = l.changedBy
WHERE   l.createdOn >= '2026-07-01'
ORDER BY l.createdOn DESC;
```

```sql
-- 7. JWPL code reconciliation: where the legacy map disagrees with the master employeeId
SELECT  j.id AS personId, LTRIM(RTRIM(s.PERSONNAME)) AS personName,
        j.jwplcode                  AS jwplMapCode,
        LTRIM(RTRIM(s.employeeId))  AS masterEmployeeId,
        CASE WHEN ISNULL(s.deleted,0)=0 THEN 'live' ELSE 'deleted' END AS status
FROM        dbo.tbl_dsrjwpl j
JOIN        dbo.tbl_salesperson s ON s.ID = j.id
WHERE   ISNULL(LTRIM(RTRIM(s.employeeId)),'') <> j.jwplcode
ORDER BY j.id;
```

---

## 6. Traps to remember

1. **`deleted = 1` dominates.** 89% of `tbl_salesperson` is soft-deleted. Any head-count, target or attendance report that forgets `ISNULL(deleted,0)=0` will be ~9× too big.
2. **`-1` is the "unset" sentinel** for `homeState/homeZone/homeArea/headState/headZone` and `distributor = '-1'`. `1899-12-30` is the empty-date sentinel (83 rows on `CreatedOn`); `0001-01-01` shows up as the date part of `startTime`/`endTime`.
3. **`'--SE'`** in `weekOff` and **`'--SELECT--'`** in `maritalStatus` are un-chosen dropdown placeholders, not data. `weekOff` is nvarchar(**8**) so the placeholder is truncated.
4. **`PERSONTYPE` and `personGroup` are stored as text**, not ids — always trim, and `LEFT JOIN` the lookups (`PROMOTER(Wheatgrass)` and `ZSM` exist in data but not in `tbl_PersonType`).
5. **`employeeId` is not unique and has whitespace**; `tbl_dsrjwpl` should be joined on `id = tbl_salesperson.ID`, never on the code.
6. **`tbl_salesperson.STATE` is empty on all 1,809 rows** — use `tbl_PersonState`.
7. **Payroll flags are all off** (`EPFGiven`, `ESIGiven`, `LWFeeGiven`, `CLGiven`, `isTaGiven` = 0 rows true) and `trackingTime`, `reportUom`, `dailyStatus` are entirely unused. Don't report on them as if they were live.
8. **`tbl_hierarchy` is stale** (only 45/120 rows point at a live person) — the live chain is `parent`/`parentType`.
9. **Never select or print `password`** (encrypted base64) or `tbl_hierarchy.passcode` (plaintext ASM passcode) into any output.
10. **`tbl_salesPersonMontlhyTarget` uses `userId`**, not `personId`, and the table name is misspelled (`Montlhy`).
