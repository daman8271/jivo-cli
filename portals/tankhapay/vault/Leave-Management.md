---
tags: [tankhapay, section, leave-management]
---
# TankhaPay — Leave Management

The `/leave-mgmt` section is where a JIVO HR admin runs the whole absence lifecycle: define leave
**types** and **templates** (policies), assign templates to employees, seed and generate **opening
balances**, watch **live balances** per employee, review **leave applications** (approve/reject),
handle **comp-off**, **on-duty (OD)** and **WFH** requests, look at **gate-pass** records, and pull
**leave-taken history** and **leave-encashment** figures. The SPA routes under it are
`/leave-mgmt/{leave-type, leave-application, add-new-template, leave-settings, bulk-leave,
bulk-holiday, leave-details, leave-general-settings, leavepolicymaker}` (route table in
`chunk-870.f5a4063463b3d9e8.js`). Two Angular services carry almost all of it —
**`LeaveMgmtService`** (module `15242`, chunk-9673) and the shared **`ReportService`** /
**`AttendanceService`** / **`EmployeeService`** / **`ApprovalService`** / **`EmployeeLoginService`**
(module `16640`, chunk-7488) — every one of them calling `CallApiService.post_enc(payload, url)`,
i.e. AES-128-ECB-encrypted POST bodies exactly as in [[Encryption-Scheme]].

**54 endpoints** are inventoried for this section (`captures/sections/Leave-Management.tsv`):
**21 reads** (in scope) and **33 writes** (documented only). A few sibling writes bound by the same
`LeaveMgmtService` but inventoried under other sections — `master/leaveApplicationApproval` /
`master/leaveApplicationRejection` and `employer/saveLeaveTemplate` — are also listed below for
completeness. Every read was confirmed by reading its actual component call site in the JS corpus
(verified 2026-07-25).

## Section-specific gotchas (verified in the corpus)

1. **Two response shapes.** `CallApiService.post_enc` only encrypts the *request*; it does **not**
   decrypt the response. Most leave endpoints hand back `commonData` as already-usable JSON
   (`t.commonData`, `t.commonData.data`, `t.commonData[0]`). A minority come back **double-wrapped**
   and the component runs `JSON.parse(encrypterService.aesDecrypt(res.commonData))`. The "Returns"
   column marks these `aesDecrypt`. Get this wrong and you either JSON-parse ciphertext or
   AES-decrypt plaintext — both fail silently-ish.
2. **`action`-multiplexed endpoints.** Several paths are RPC-style: the same URL both reads and
   writes depending on the `action` string. `leaves/getLeaveTemplate` is the dangerous one — it
   serves `get_lead_type` / `get_template_with_settings_by_id` (reads) **and**
   `remove_template_by_id` / `set_default_template` (destructive writes). Only ever send the pinned
   read actions; the CLI must hardcode them, never accept `--action` from the user.
3. **`get`-prefixed writes.** `leave/getUpdateLeaveBalance` and `leave/getGenerateOpeningBalance`
   both start with `get` but mutate balances. They are WRITES. The path-regex heuristic in
   `captures/endpoints-raw.tsv` cannot see this — this note is the source of truth
   ([[Read-Only-Guardrails]]).
4. **Casing traps.** `leave/` and `leaves/` are two different route prefixes and both are live.
   Payload keys are inconsistent across endpoints: `accountId` vs `accountid` vs
   `customeraccountid` vs `account_id`; `empid` vs `emp_id` vs `empId`. Copy them exactly as listed.
5. **Account context** comes from the decoded JWT ([[Auth-and-Access]]): `tp_account_id=2719`,
   `geo_location_id=37` (sent as `p_geofenceid`), `ouIds="37,2211,38,40,31,1925"`,
   plus `product_type` from `localStorage`. Almost every payload stringifies these (`.toString()`).
6. **Date formats are not uniform.** `effective_dt` is `DD-MM-YYYY` (built as `"01-"+month+"-"+year`),
   `fromdate`/`todate` on the business API are `DD-MM-YYYY`, but the mobapi `get_Leave_appl_filter`
   call converts to `DD/MM/YYYY` (`val().split("-").join("/")`). `att_month`/`att_year` are plain ints.

## Read endpoints (in-scope for the CLI)

Backend key: **B** = `https://business.tankhapay.com/api/` (`tankhapay_api`),
**M** = `https://mobapi.tankhapay.com/api/` (`tp_employer_api`). See [[Backends-and-Environment]].

| Endpoint (path) | Backend | Request payload keys | Returns | Notes |
|---|---|---|---|---|
| `leaves/get_leave_types_by_account` | B | `action:"get_leave_type"`, `customeraccountid` | array of leave types; `typename` used to build report column headers | The lookup you call first — every balance grid is keyed by these type names. `ReportService`. |
| `leaves/get_employee_leave_balance` | B | `accountId`, `empid` | `commonData[0]` = one employee's balance object (`balance_txt` etc.) | Single-employee balance. `LeaveMgmtService`. Used by the employee leave tab. |
| `leaves/get_employee_leave_balance_el` | B | `empid` (`"0"` = all employees), `accountId`, `p_geofenceid`, `ouIds` | array of `{ employee_detail:{emp_name, cjcode, orgempcode, employee_photo}, emp_id, template_id, …per-type {type_name, cur_bal} }` | **The account-wide balance grid.** `p_geofenceid` = JWT `geo_location_id`, `ouIds` = JWT `ouIds`; both may be `""` for unfiltered. `ReportService`. |
| `leaves/get_Leave_appl_by_account_empid` | B | `action` (`get_Leave_appl_by_account` \| `get_Leave_appl_by_account_el` \| `get_Leave_appl_all_by_empid`), `accountId`, `fromdate`, `todate`, `approval_status`, `p_geofenceid`, `ouIds`, `postOffered`, `postingDepartment`, `unitParameterName`, `emp_id`/`empid` | array of leave applications (`emp_name`, `cjcode`, `orgempcode`, `leave_applid`, `leavetypename`, `fromdate`, `todate`, `approval_status`, `leave_days`, …) | The leave-application register. All three actions are reads. `empid` variant drops the date range and takes `empid` + `approval_status` only. |
| `leaves/getEmployeeleave_history` | B | `accountId`, `empid` *(basic form)*; a second call site adds `action:"get_leave_taken_history_by_emp_id"` + `productId` | array — that employee's leave-balance/template history | `EmployeeService`; shown on the employee profile "Leave" tab. Both forms are reads. |
| `leaves/get_leave_taken_history` | B | `action:"get_leave_taken_history"`, `accountId`, `att_month` (int), `att_year` (int), `emp_id`, `template_id` | array of that employee's leaves taken in the month | Drill-down from a row in the balance grid. `ReportService`. |
| `leaves/get_emp_monthly_leave_taken_history` | B | `action:"get_leave_taken_history"`, `accountId`, `att_month`, `att_year`, `emp_id` (`""`=all), `template_id` (`""`=all), `searchText`, `department_search`, `designation_search`, `ou_search` | month-wise leave-taken matrix across employees (component maps `Jan…Dec` columns) | Account-wide monthly report version of the row above. Filters are comma-joined id strings. |
| `leaves/get_tp_leave_temeplate` | B | `customeraccountid` | `commonData.data` = leave-template master list (`templateid`, template text) | Note the vendor's typo `temeplate`. Used for template dropdowns everywhere. `EmployeeService`. |
| `leaves/getLeaveTemplate` | B | **read actions only:** `action:"get_lead_type"` + `customeraccountid`; or `action:"get_template_with_settings_by_id"` + `customeraccountid` + `default_templateId` | `commonData.data` — leave-type master (`leavetype`, `leavecode`, `leave_days`, colour) / full template with settings | ⚠️ **Action-multiplexed with destructive actions** (`remove_template_by_id`, `set_default_template`). Pin the two read actions in code; never expose the action as a flag. |
| `leaves/get_leave_general_settings` | B | `accountId` | `commonData[0]` = `{ is_weekend_comp_off_auto:"Y"/"N", revert_approved_leave_within_days, … }` | **Reclassified READ** (heuristic said WRITE because of `set`/`general_settings`). The writer is the separate `upsert_leave_general_settings`. |
| `leave/get_leave_balance_by_account` | B | `accountId`, `att_month`, `att_year`, `template_id` | array — balances for the whole account for a template/period | Feeds the bulk-leave screen. Month/year are derived from the template's calendar (`Calender Year` → month 12 of prior year; `Financial Year` → month 4). `AttendanceService`. |
| `leave/getOpeningLeaveBalance` | B | `accountId`, `empid`, `effective_dt` (`"01-MM-YYYY"`) | `commonData.data[0]` = `{ rowid, emp_id, emp_name, mobile, orgempcode, intial_leave_bal_txt[], global_leave_bal_txt[] }`; also `msgcd` (`"1"` = ok) | Reads one employee's seeded opening balance. Read-only — the writers are `getGenerateOpeningBalance` / `getUpdateLeaveBalance`. `AttendanceService`. |
| `leave/get_comp_off_opening_balance` | B | `action:"get_comp_off_opening_balance"`, `accountId`, `fromdate` (`"01-01-YYYY"`), `approval_status:"All"` | array of employees with comp-off opening balances | Year-scoped; the screen re-calls it on year change. `AttendanceService`. |
| `leave/getCompOffRequest` | B | `action:"get_compoff_appl_filter"` + `accountid` + `emp_id` + `fromdate` + `todate` + `approval_status`; **or** `action:"get_compoff_appl_by_account"` + `accountid` + `fromdate` + `todate` + `approval_status` | comp-off request list (`approval_status` ∈ Pending/Approved/Rejected) | **`aesDecrypt`** — component does `JSON.parse(aesDecrypt(res.commonData))`. Note lowercase `accountid`. `EmployeeLoginService`. |
| `leave/get_od_appl_by_account` | B | `action:"get_od_appl_by_account"`, `accountId`, `fromdate`, `todate`, `approval_status`, `postOffered`, `postingDepartment`, `unitParameterName` | on-duty (OD) application list; component tallies Pending/Approved/Rejected | **`aesDecrypt`**. `ApprovalService` (module 85734). |
| `leave/get_gatepass_data` | B | `action:"get_gatepass_data"`, `accountId`, `emp_id`, `fromdate`, *(optional)* `productId` | gate-pass rows for that employee/date | Opened from a leave-detail panel; `accountId`/`emp_id` come from the selected row, not the JWT. `LeaveMgmtService`. |
| `leave/get_leave_encashment_details` | B | `customeraccountid` | array of employee leave-encashment records (component sums per employee) | **`aesDecrypt`**. `ReportService`. Read-only twin of the `save_leave_encashment` write. |
| `leave/get_leave_type_extension_list` | B | `action:"get_leave_type_extension_list"`, `accountid` (**not** stringified) | array of per-leave-type policy extensions (`past_date_check_yn/_day`, `future_date_check_yn/_day`, `monthly_maximum_allowed*`, `max_leaves_allowed_per_req*`, `max_leaves_allowed_without_doc*`, `exclude_weekends_holidays_yn`, `hide_after_doj_days*`, `remark`) | The leave-policy rulebook. `LeaveMgmtService`. |
| `leave/get_employee_list_for_generate_leave` | B | `accountId`, `template_id`, `effective_dt`, `generated_status` | employee list for the opening-balance generation screen (`emp_name`, `cjcode`, `mobile`, `orgempcode`) | **Reclassified READ** (heuristic said WRITE on `generate`). It only *lists* candidates; `generateBulkOpeningBalance` is the write. `AttendanceService`. |
| `leave/check_template_is_editable` | B | `accountId`, `template_id` | `commonData.msgcd` (`"1"` = template already assigned) + `message` | **Reclassified READ** — pure assignment-status probe (`GetTemplateAssignedStatus`), no mutation at the call site. Low CLI value; no command proposed. |
| `leave/get_Leave_appl_filter` | **M** | `accountId`, `empid`, `fromdate` (`DD/MM/YYYY`), `todate` (`DD/MM/YYYY`), `approval_status`, `productTypeId` | that employee's leave requests | **`aesDecrypt`**. The only leave read on **mobapi**; same bearer JWT works. `EmployeeLoginService`. |

## Write endpoints (documented, OUT OF SCOPE)

Never wired into the CLI — no command, no flag, no code path ([[Read-Only-Guardrails]]).
`B` unless marked `M` (mobapi).

| Endpoint | What it does |
|---|---|
| `approveRejectLeave` | Approve/reject a leave application (top-level path, no `leave/` prefix). |
| `leaves/approved_leave_appl_by_applid` | Approve/reject one application: `{action, accountId, empid, approval_status, row_id, remark}`. |
| `leave/approved_od_appl_by_applid` | Approve/reject an on-duty application (also driven in a bulk loop): `{action, accountId, emp_id, row_id, approval_status, remarks}`. |
| `master/leaveApplicationApproval` / `master/leaveApplicationRejection` | Workflow-level approve / reject hooks bound in `LeaveMgmtService`. |
| `leaves/add_update_leave_type` | Create/update a leave type: `{customeraccountid, action, leavetypeid, leavecode, leavetypename, leave_ctg, leave_days, is_halfday_leave, gender, description}`. |
| `leave/manage_leave_type_extension_list` | **Reclassified WRITE** (TSV said READ). Writes the whole leave-policy extension row: `{action:"add"/"update"/"update_color", accountid, leave_type_code, remark, past_date_check_*, future_date_check_*, monthly_maximum_allowed*, max_leaves_allowed_per_req*, max_leaves_allowed_without_doc*, exclude_weekends_holidays_yn, hide_after_doj_days*}`. |
| `leaves/leave_type_enable_desable` | Enable/disable a leave type: `{action:"add_leave_type_enable"/"…_desable", customeraccountid, leavetypeid}`. |
| `leaves/addUpdateAttendanceType` | Create/update an attendance type. |
| `employer/saveLeaveTemplate` | Create a leave template (bound in `LeaveMgmtService` as `saveLeaveTemplate`). |
| `leaves/getLeaveTemplate` *(write actions)* | Same URL as the read above, but `action:"remove_template_by_id"` deletes a template and `action:"set_default_template"` changes the account default. **Destructive.** |
| `leaves/manageCustomerLeaveTemplate_hub` | Customer-level leave-template management. *(TSV UNKNOWN → WRITE.)* |
| `leaves/manageEmployeeLeaveTemplate_hub` | Assign a leave template to one employee: `{leaveTemplate[], customerAccountId, productTypeId, empId, templateId, effectiveDate}`. *(UNKNOWN → WRITE.)* |
| `leaves/bulkEmployeeLeaveTemplate_hub` | Same, for an array of employees (`empIdArray`). |
| `leaves/manage_global_config` | Global leave config write. No call site in the corpus → **out of scope, do not probe.** *(UNKNOWN → WRITE.)* |
| `leaves/upsert_leave_general_settings` | Writes the general leave settings read by `get_leave_general_settings`. |
| `leave/getGenerateOpeningBalance` | **Writes** despite the `get` prefix — generates an employee's opening balance, then the UI re-reads it. |
| `leave/getUpdateLeaveBalance` | **Writes** despite the `get` prefix: `{accountId, empid, leavebankid, leavetemplate_text}`. |
| `leave/generateBulkOpeningBalance` | Bulk-generate opening balances: `{accountId, empid[], effective_dt, generated_status}`. |
| `leave/updateBulkLeaveBalance` | Bulk-update balances: `{accountId, leavebankid, empid[], leavetemplate_text}`. |
| `leave/insert_update_global_leave_balance_by_empid` | Insert/update the global leave balance for an employee. |
| `leave/generate_leave_attendance_and_save` | Generates leave attendance rows and saves them. |
| `leave/manage_bulk_holiday_state` | Bulk holiday/state mapping. Has a read-looking action (`get_employee_by_empcode`) but is a `manage_` mutator — **kept out of scope**. |
| `leave/update_weekly_off_holiday_by_account` | `{p_account_id, p_year, p_month}` — rewrites weekly-off/holiday marking for a month. |
| `leave/manageCompOffRequest` | Create/update a comp-off request: `{action, accountid, comp_applid, emp_id, comp_off_applied_date, working_start_time, working_end_time, working_hours, compoff_description, remarks, attachment_url, createdby}`. *(UNKNOWN → WRITE.)* |
| `leave/manage_compoff_request` | Comp-off opening-balance insert: `{action:"insert_opening_balance", accountId, empId, comp_off_applied_date, todate, comp_off_days, remarks, compoff_description}`. *(UNKNOWN → WRITE.)* |
| `leave/bulkManageCompoff` | Bulk comp-off upload: `{accountId, records[]}`; returns `failedCount`/`failedRecords`. |
| `leaves/auto_apply_compoff` | Auto-raise comp-off for a date: `{selected_date, accountid, comp_off_for}`. |
| `leaves/auto_apply_compoff_appl` | Auto-apply comp-off applications. |
| `leave/uploadCompOffDocument` | Uploads the comp-off attachment (`{data, name}`) and returns `filePath`. |
| `leave/manageWfhApplication` | Create/update a work-from-home application. *(UNKNOWN → WRITE.)* |
| `leave/uploadWfhDocument` | Uploads the WFH attachment. |
| `leave/save_leave_encashment` | Saves leave-encashment records. |
| `M approveRejectCompOffRequest` | Approve/reject a comp-off request (mobapi). |
| `M approveRejectWfhRequest` | Approve/reject a WFH request (mobapi). |
| `M leave/apply_leave_appl` | Applies a leave on behalf of an employee: `{…leaveForm, fromdate, todate, productTypeId, accountId, empid, createdby}`. |
| `M leave/remove_applied_leave` | Cancels an applied leave: `{accountId, empid, leave_applid, remarks, productTypeId}`. |

## CLI command mapping

Proposed read-only subcommands for `tankhapay-portal` (each fills `accountId`/`p_geofenceid`/`ouIds`
from the decoded JWT unless overridden by a flag):

- `leave types` → `leaves/get_leave_types_by_account`
- `leave templates` → `leaves/get_tp_leave_temeplate`
- `leave template-master` → `leaves/getLeaveTemplate` *(action pinned to `get_lead_type`)*
- `leave template show --template-id` → `leaves/getLeaveTemplate` *(action pinned to `get_template_with_settings_by_id`)*
- `leave policy` → `leave/get_leave_type_extension_list`
- `leave settings` → `leaves/get_leave_general_settings`
- `leave balance --emp-id` → `leaves/get_employee_leave_balance`
- `leave balance-all [--ou-ids] [--geo]` → `leaves/get_employee_leave_balance_el` (`empid=0`)
- `leave balance-account --month --year --template-id` → `leave/get_leave_balance_by_account`
- `leave opening-balance --emp-id --month --year` → `leave/getOpeningLeaveBalance`
- `leave generate-candidates --template-id --effective-dt --status` → `leave/get_employee_list_for_generate_leave`
- `leave applications --from --to [--status] [--dept] [--desg] [--ou]` → `leaves/get_Leave_appl_by_account_empid` (`get_Leave_appl_by_account`)
- `leave applications-emp --emp-id [--status]` → `leaves/get_Leave_appl_by_account_empid` (`get_Leave_appl_all_by_empid`)
- `leave applications-mob --emp-id --from --to [--status]` → `M leave/get_Leave_appl_filter`
- `leave history --emp-id` → `leaves/getEmployeeleave_history`
- `leave taken --emp-id --month --year --template-id` → `leaves/get_leave_taken_history`
- `leave taken-monthly --month --year [--search] [--dept] [--desg] [--ou]` → `leaves/get_emp_monthly_leave_taken_history`
- `leave compoff requests --from --to [--status] [--emp-id]` → `leave/getCompOffRequest`
- `leave compoff opening --year` → `leave/get_comp_off_opening_balance`
- `leave od --from --to [--status] [--dept] [--desg] [--ou]` → `leave/get_od_appl_by_account`
- `leave gatepass --emp-id --account-id --date` → `leave/get_gatepass_data`
- `leave encashment` → `leave/get_leave_encashment_details`

---

[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]]

Sibling sections: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
