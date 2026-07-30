# Source map — jsap-cli (JSAP platform)

Agent: jsap-cli source-mapper. Date: 2026-07-30.
Repo dir: `/Users/damanpreetsingh/jivo-cli/jsap-cli`
App: **JSAP**, `http://103.89.45.75:5001` (ASP.NET Core; `.AspNetCore.Session` cookie).
Same host as the DSR portal/SQL Server box (103.89.45.75), **different host from SAP HANA**.

## Headline

Despite the name, JSAP is **not** mostly a SAP window. Of 13 command groups / 146 commands,
only **3 groups (~30 commands)** return SAP-sourced rows. The other **10 groups (~116
commands)** are governance/workflow data that exists nowhere in SAP B1: tickets, tasks,
employee hierarchy + salary, Document Hub, inventory-audit physical counts, bill
verification, IT/MoM dashboards, QC parameter templates, and JSAP's own user/permission model.

The one genuinely interesting case is **budget approvals**: the approval *trail* originates
in JSAP but is physically stored in **custom tables created inside the SAP HANA company
schemas** (`js_budget_approval_workflow`, `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`, …). Those are
**not SAP B1 objects** — a `sapb1` / Service-Layer user cannot see them; only direct HANA SQL can.

## Runtime / auth

- Pure Python 3 stdlib (`urllib`), no deps. `jsap/client.py` exposes exactly two data verbs:
  `get()` (GET) and `read_post()` (POST-to-read, refused unless the URL leaf starts with a
  read verb). No write path exists. `tests/test_readonly.py` enforces it.
- Auth: `POST /api/auth/Login` → `POST /websession/set` → `POST /websession/updateSelectedCompany`;
  session cookie cached in `~/.jsap/session.json` (1 h TTL, 0600). Creds from repo `.env`
  (`JSAP_URL`/`JSAP_USERNAME`/`JSAP_PASSWORD`). Live identity used for this audit: user 68 `nirmalkaur`.
- Company scope: **1 = JIVO OIL, 2 = JIVO BEVERAGE** (note: JSAP has no Mart; company id 2
  means Beverage here but Mart in factory-cli — a known collision).

## Command group → concrete backing source

| Group | Cmds | Endpoint prefix | Concrete backing source | Bucket |
|---|---|---|---|---|
| `documents` (SAP half: `po grpo apdraft gr sapfile`) | 5 | `/api/DocumentDispatch/Get{PO,GRPO,ApDraft,GR}` | **SAP HANA directly** — rows carry `databaseName: JIVO_OIL_HANADB / JIVO_BEVERAGES_HANADB` + `docEntry/docNum/cardCode/cardName/docDate/docTotal`. Verified against `OPOR`, `ODRF`, `OPDN`. `sapfile` streams SAP attachments (`OATC`/`ATC1`, 76k/129k rows). | **M** |
| `documents` (dispatch half: `docs rejected pending history bundleid file`) | 6 | `/api/DocumentDispatch/Get{UserDocuments,RejectedDataByUserId,RecieverPendingData,RecieverActionData,LastBundleId}` | JSAP app DB (physical courier bundles between branches ↔ HO). **All returned HTTP-500 "Internal server error" at audit time.** No such table anywhere in HANA. | **N** |
| `bpmaster` | 14 | `/api/BPmaster/*` | SAP `OCRD` + `CRD1` + SAP UDTs. `cards` returns `cardCode/cardName/address/state/gstRegnNo`; `chains` returns `u_Chain` (SAP `@CHAIN`, 46 rows), `maingroups` → `@MAIN_GROUP`, `payterms` → `OCTG`, `pricelists` → `OPLN`, `banks` → `ODSC`, `countries/states` → `OCRY/OCST`. | **M** |
| `reports` (budget approval) | 7 | `/api/auth/GetAllBudgetInsight`, `/api/auth/get{pending,approved,rejected}budgetwithdetails`, `/api/auth/GetBudgetApprovalFlow`, `/api/Reports/GetBudgetByCompany` | JSAP workflow rows keyed to **SAP draft documents**: `objType 18` (A/P Invoice), `docEntry` → `ODRF`. Trail stored in HANA custom tables `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` (29,212 rows), `js_budget_approval_workflow` (86), `tbl_Draft_Approvals` (1,440), `jsDocEntries` (535). | **F** |
| `dashboards` (Budget/Avtar: `ledgers budgetheads budgetdata`) | 3 | `/api/Dashboard/GetUniqueAccounts`, `GetUniqueBudgets`, `getBudgetDataByBranch` | SAP GL: `acctName` values verified 3/3 in `JIVO_OIL_HANADB."OACT"` (1,424 accounts). Amounts by `branch`(OIL/BEVERAGE) × `currentMonth`. Budget-head dimension is JSAP's own. | **M** (amount+account) / **N** (budget head) |
| `dashboards` (IT / Task / Client / MoM: 14 cmds) | 14 | `/api/Dashboard/{GetSummary,GetMaster,stats,status-distribution,employee-stats,trend,list,projects,employees,details,GetDashboardMaster,GetDashboardByCompany,GetDashboardProject,GetAllMoM}` | JSAP app DB. Live: `itmaster` → `[]`, `mom` → `[]`, `clients` → single TOTAL row. No HANA counterpart. | **N** |
| `inventory` (audit sessions + report) | 12 | `/api/InventoryAudit/*`, `/api/ItemMaster/GetGroup` | **Hybrid.** Session/lot/physical count is JSAP-native (`sessionId`, `lotNumber`, `roleInSession`, `physicalQty`, `diffQty`, `createdByUsername`). Joined to SAP masters (`itemCode FG0000004` verified in `OITM`; `warehouse DL-EC`; `subGroupName` = `OITM.U_Sub_Group`). Dropdown feeds (`units/locations/warehouses/groups/subgroups`) are SAP masters → M. | **N** (counts) / **M** (masters) |
| `users` | 12 | `/api/auth/get{roles,states,branches,budgets,subBudgets,approvals,varieties,reports,departments,usernotregisterincompany}`, `/UserManagement/AllUsers` (HTML scrape), `/api/Permission/GetUserEffectivePermissions` | JSAP app DB — its own identity + permission model. `users budgets` returns 15 heads vs SAP `@BUDGET` = **1 row**, so not sourced from SAP. `list` is scraped from server-rendered HTML. | **N** |
| `qc` | 2 | `/api/QC/GetFormStructureV2`, `GetFormStructure` | JSAP app DB. QC *template*: formId 5, thresholds (min 1/max 10/pass 7.5/randomBoxCheck 5), 7 mandatory doc flags, 10 parameter→sub-parameter rows, `isImageMandatory`. SAP's separate `@QC_O` UDO (6 rows, Oct-2025) is a **different** object and is not served here. | **N** |
| `tasks` | 7 | `/api/Task/{GetAllTasks,GetDashboard,GetTaskDetails,GetProgressUpdates}` (POST-reads), `/TaskWeb/{GetTeamMembers,GetHierarchyTree}` | JSAP app DB. GUID `taskId`, `percentComplete`, progress-update log, employee-hierarchy scoping. No HANA table matches `%TASK%`. | **N** |
| `tickets` | 11 | `/api/Tickets/*` (mostly POST-reads) | JSAP app DB. Helpdesk: projects (JSAP, DSR, …), status/priority, timeline, comments (incl. internal notes), attachments. No HANA table matches `%TICKET%`. | **N** |
| `hierarchy` | 24 | `/api/Hierarchy/*`, `/HierarchyWeb/*` | JSAP app DB. HO org tree (227 flat rows), employee salary/DOJ/designation, custom fields, audit logs, salary sessions, Sales H1→H4 chain (`empCode JWPL1802`, state, `groupName`, `designation ASM`). SAP `OHEM` has only **17 rows (Oil) / 15 (Bev)** — the SAP *users*, not the org. | **N** |
| `bills` | 14 | `/Maker/*`, `/Checker/*`, `/InvoicePayment/*`, `/PaymentChecker/*`, `/Admin/*` | **Not JIVO SAP at all.** 998 vouchers, 100 distinct accounts — Baru Sahib / Akal institutional supply (bakery, dairy, garments, footwear, toys). Only 6/100 account names exist in SAP `OCRD` across all 3 schemas, and those are generic-name coincidences. Bill line items (`Mattress Single`, `Gs Pillow`, `Amul Butter`) → **0 matches** in `OITM` in any schema; `Ary Warehouse` → **0 matches** in `OWHS`. | **N** (see caveat) |
| `dochub` | 10 | `/DocumentHub/*` | JSAP app DB + its own file store (`storedFileName` GUIDs, versions, activity log, `isConfidential`+`pinCode`, backup snapshots `DH-2026…`). Company-agnostic. | **N** |
| `meta` | 4 | `/api/auth/getcompanies`, `getdepartments`, `/api/Permission/GetUserEffectivePermissions` | JSAP app DB. | **N** |

## The split you asked for

**SAP-document half (~30 commands):**
`documents po|grpo|apdraft|gr|sapfile` · all 14 `bpmaster` · `inventory units|locations|warehouses|groups|subgroups` ·
`dashboards ledgers|budgetheads|budgetdata` · the `docEntry`/`objType` spine of all 7 `reports` commands.

**Workflow / governance half (~116 commands):**
`tickets` (11) · `tasks` (7) · `hierarchy` (24) · `dochub` (10) · `bills` (14) · `users` (12) ·
`dashboards` IT/Task/Client/MoM (14) · `qc` (2) · `meta` (4) · `documents` dispatch half (6) ·
`inventory` session/count half (7) · the approval-trail layer of `reports`.

## Live verifications performed (commands + results)

1. **`jsap documents po` == SAP `OPOR`.**
   `./jsap-cli documents po --json` → row `{databaseName: JIVO_OIL_HANADB, docEntry: 4993, docNum: 525226675, cardCode: ORGV000296, docTotal: 2040}`.
   `hana-sql "SELECT DocEntry,DocNum,CardCode,DocDate,DocTotal FROM JIVO_OIL_HANADB.OPOR WHERE DocEntry IN (4993,10802,7134)"` → exact match on all 3, all fields.
   **Filtered mirror, not full:** JSAP returns 3,441 POs (2,722 Oil + 719 Bev) vs SAP `OPOR` 4,191 Oil + 1,113 Bev.
   GRPO: JSAP 10,626 (7,123 Oil + 3,503 Bev) vs `OPDN` 11,248 Oil + 4,533 Bev.

2. **Budget approval chain, end to end (the single most useful finding).**
   `jsap reports approved --userId 69 --month 07-2026` → `{budgetId: 15849, objType: 18, company: OIL, docEntry: 51648, objectName: "A/P INVOICE", cardCode: VENDA000869, totalAmount: 393750, approvalStatus: A, approvalDate: 07/08/2026}`.
   - `OPCH` DocEntry 51648 → **does not exist**.
   - `ODRF` (drafts) DocEntry 51648 → exists, ObjType 18, CardCode VENDA000869, DocTotal **425250**.
   - `OPCH WHERE CardCode='VENDA000869'` → DocEntry **47577**, DocNum 626074104, **`draftKey` = 51648**, DocTotal 425250.
   - `jsap reports flow 15849` → one stage `"factory oil v5 1"`, assignedTo Jasbir Singh, actionStatus A, 07/08/2026 11:56:49.
   ⇒ SAP draft → JSAP approval → posted SAP A/P Invoice. **F, confirmed.**
   ⚠️ **Amount divergence:** JSAP reports `totalAmount 393750`; SAP holds `DocTotal 425250` (difference 31,500 = exactly 8 % of 393,750). JSAP is showing a pre-something base, SAP the gross. Do not treat JSAP budget amounts as SAP document totals.

3. **JSAP writes into the SAP HANA schemas.** `SELECT TABLE_NAME FROM SYS.TABLES WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND (TABLE_NAME LIKE 'js%' OR 'JS%' OR 'tbl%')`:
   | table | rows |
   |---|---|
   | `JS_SYNC_BUDGET_APPROVAL_WORKFLOW` | 29,212 |
   | `tbl_Draft_Approvals` | 1,440 |
   | `jsDocEntries` | 535 |
   | `tbl_Draft_Approval` | 161 |
   | `js_budget_approval_workflow` | 86 |
   | `jsDocumentAttachments` | 36 |
   | `tbl_customerLimit` | 35 |
   | `tbl_SAPRight` | 2 |
   | `JSBUDGETSTATUSWORKFLOW` | 0 |
   `js_budget_approval_workflow` columns: `docEntry, status, currentStageId, userName, stageId, stageName, approvalId, createdBy, createdOn, company, rejectid, description, currentTemplateId, currentStagePriority, nextStageId, nextStageName, objType, lineNum, visOrder, docId, currentStageApprovers, nextStageUsers, updateDate, BUDGET, SUB_BUDGET, budgetId`.
   Sample row from `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`: `docEntry 10852, status P, stageName "ote legal beve v6 1", userName Arshdeep Singh, company 2, BUDGET OTE, budgetId 15846`.
   **Note:** the Oil schema holds rows for `company=2` (Beverage) too — one cross-company workflow table living in the Oil DB.
   (`JST1` matched the LIKE but is a genuine SAP TDS/withholding table, not JSAP.)

4. **HANA holds no JSAP workflow objects beyond those.** `SELECT SCHEMA_NAME,TABLE_NAME FROM SYS.TABLES WHERE SCHEMA_NAME LIKE 'JIVO%' AND (TABLE_NAME LIKE '%TICKET%' OR '%TASK%' OR '%HIERARCH%' OR '%DOCHUB%' OR '%MOM%' OR '%BILL%' OR '%DISPATCH%' OR '%INVENTORYAUDIT%' OR '%STOCKCOUNT%')` → only `@UTL_ST_INTREWBILL` (an e-way-bill UDT). **Zero** tables for tickets/tasks/hierarchy/dochub/dispatch/stock-count.
   Schemas on the HANA box: `JIVO_OIL_HANADB` (3,111 tables), `JIVO_BEVERAGES_HANADB` (3,087), `JIVO_MART_HANADB` (3,046), `TEST_OIL_15122025` (3,112 — a copy), plus `SYS*`. **No JSAP schema exists on HANA.**

5. **Physical stock counts never reach SAP.** `jsap inventory report KAMALPREET19` returns per-item `systemQty / physicalQty / diffQty / diffValue / diffLitre` for lot `KAMALPREET19`, session 2, warehouse DL-EC. SAP inventory-counting tables: `OINC = 0`, `OIQR = 0`, `ODPS = 0` in `JIVO_OIL_HANADB`. Nothing is posted back. (`OWTQ` = 1,289 but that is stock-transfer requests, unrelated.)

6. **Bill verification is a different company's books.** `jsap bills admin --json` → 998 vouchers, 100 distinct `accountName`s. Pulled all 8,503 `OCRD.CardName` values from the 3 SAP schemas and normalised-matched: **6/100** exact hits (Bharat Traders, Durga Trading Co., Harjas Enterprises, Hygienic Milk, K.Mark Shawls, Nirmal Kaur - Director) — generic names, not evidence of sourcing. Line items from voucher 973 (`Gs Pillow`, `Mattress Single`, `Amul Butter 100 Gm`, warehouse `Ary Warehouse`, tax `Input Gst 5%(Exclu)`) → `OITM` LIKE '%MATTRESS%' OR '%PILLOW%' = **0** in all three schemas; `OWHS` LIKE '%ARY%' = 0. Account list is Baru Sahib / Akal institutional (bakery, dairy, catering, garments, footwear, toys). `bills summary` → totalBills 971, pendingMaker 41, approvedChecker 851, totalPaid 435.

7. **Employee hierarchy dwarfs SAP's.** `jsap hierarchy flat` = 227 rows with salary/DOJ/designation/dept; `jsap hierarchy sales` = H1–H4 chain rows with state/group/designation. SAP `OHEM` = **17 rows (Oil), 15 (Bev)** — and those 17 are the SAP licence holders / budget approvers (Avtar Singh, Jasbir Singh, Gurvinderjeet, Arshdeep, Gurpreet, Karanpreet, Ravinder, Nirmal Kaur…). `OSLP` = 155.

8. **Budget dashboard accounts are SAP GL.** `jsap dashboards ledgers` → `ADVERTISEMENT`, `AGENCY CHARGES EXPORT`, `SALES CANOLA @ 5 %`, `4 ROW MAGNETIC BEND CHAIN CONVEYOR-FA0000037`. `OACT` lookup → 5640001 ADVERTISEMENT, 5300006 AGENCY CHARGES EXPORT, 4110001 SALES CANOLA @ 5 %. 3/3 exact.

9. **BP master is SAP.** `jsap bpmaster cards` → `CUSTA001085 / A K ENTERPRISES / DL / 07BEOPK6760G2Z4`; `OCRD` Oil = 3,390 rows. `bpmaster chains` returns a `u_Chain` field; SAP `@CHAIN` UDT has 46 rows with the same values (ACADEMIES, DISTRIBUTOR, SUPER STOCKIST, …). `inventory subgroups` returns `u_Sub_Group` = SAP `OITM.U_Sub_Group` / `@ITEM_SUBGRP` (51 rows).

10. **Tickets / tasks / dochub are unambiguously native.** `tickets all` → ticketId 13, projectName "JSAP", title "Entry Not Visible in JSAP", fromUserName Ishwendra S, ageDays 154. `tasks list` → GUID taskId, assignedTo "Nirmal Didi", percentComplete, CRITICAL priority. `dochub hub` → fileId 48 `June-26.pdf`, storedFileName `d0eec9a8036448efa421ca974751c314.pdf`, versionNumber 1, uploadedBy Kamaljeet.

## What I could not determine (stated plainly)

- **JSAP's own application database was never inspected.** I only ever spoke to the HTTP API.
  It is almost certainly SQL Server on 103.89.45.75 (same box as DSR's `DSR_V6`), but I had no
  credentials for that instance and did not try to obtain any. Every "N" ruling for
  tickets/tasks/hierarchy/dochub/bills/dispatch therefore rests on (a) code evidence for the
  endpoint and (b) **live negative evidence that no such table exists anywhere in HANA** — which
  is the claim that actually matters for "is this covered by SAP?", but it does not tell you
  which physical DB holds it.
- **Origin of the bill-verification vouchers.** Certain: they are not in SAP. Uncertain: whether
  makers key them into JSAP or they are imported from a third-party accounting package. The field
  shapes (`serialNumber "17115.0015"`, `hsnsacid`, `margin`, `mrp`, `taxName "Input Gst 5%(Exclu)"`,
  `warehouseName`) look like a Marg/Busy-style purchase-invoice export rather than hand entry.
- **`documents` dispatch half was down.** `docs`, `rejected`, `pending`, `history`, `bundleid` all
  returned HTTP 500 "Internal server error" throughout the audit. Classified on code + negative
  HANA evidence only; I never saw a row.
- **`dashboards itmaster`, `dashboards mom`, `dashboards clients` returned empty.** Endpoints are
  live but hold no data, so I confirmed the *endpoint* but not the *content*.
- **Direction/latency of `JS_SYNC_BUDGET_APPROVAL_WORKFLOW`.** The name says "SYNC". I did not
  establish whether JSAP writes it directly or a job syncs it from the app DB, nor its lag.
- **Overlap with other systems.** JSAP's Sales H1–H4 hierarchy and DSR's salesperson tree look
  like they cover the same people; TankhaPay also holds employees. I did not cross-check those —
  out of scope here, but a likely duplicate-source finding for whoever consolidates.

## Warnings for downstream consumers

- **Do not tell an Accounts user "JSAP budget approvals are in SAP".** They are in the SAP
  *HANA database* but not in the SAP *B1 object model*. `sapb1`/Service-Layer queries will not
  find `budgetId`, stage names, approvers, or rejections. Only `hana-sql` reaches them.
- **JSAP budget `totalAmount` ≠ SAP `DocTotal`** (see verification 2). Never mix them in one number.
- **`documents po/grpo/apdraft/gr` are a filtered subset of SAP**, roughly 65–95 % of the
  underlying tables depending on object. Never use them for a completeness count — go to HANA.
- `documents bundleid` has a `mode=update` variant that mutates a counter; the CLI hardcodes
  `mode=select`. Do not hand-craft that URL.
- `dochub download` may append an activity-log row server-side (a read with a side effect).
  Prefer `dochub preview`.
