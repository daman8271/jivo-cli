---
tags: [tankhapay, section, dashboard]
---
# Dashboard

The landing screen an HR/payroll admin sees after login (`/dashboard`). It is a live workforce
snapshot for the account's 593 employees plus a compliance-onboarding tracker. Four widget clusters:
**(1) the tpay dashboard tiles** — today's employee list, attendance, birthdays, work anniversaries,
holidays, leave, and probation/contract-renewal due lists (`get_tpay_dashboard_data`, one call per
tile keyed on an `action`); **(2) the headcount + today's-attendance grids** (`get_employees_count_details`,
`get_today_attendence_reports`, routes `/dashboard`); **(3) the onboarding-assistant progress bar**
that walks a new employer through setup (`get_dashboard_status`, plus per-sub-user widget layout
`get_dashboard_setting_data`); and **(4) the Alerts / Notifications centre** — the alert-type master,
the configured-alert list, and the birthday/anniversary wish campaigns (routes under `/dashboard`
alerts + notification-template screens). Everything below is extracted from the production bundle
(`main.7309d5d32824e620.js` + lazy chunks, captured 2026-07-25); every call is an AES-encrypted POST
to the `business` backend — see [[Encryption-Scheme]].

> Endpoint constants live in bundle module `4245` (`u+"dashboard/…"` and a few bare `u+"…"` paths).
> Service wrappers: `LoginService` (`get_tpay_dashboard_data`, `get_dashboard_status`),
> `EmployeeManagementService` (`get_employees_count_details`), `AttendanceService`
> (`get_today_attendence_reports`), `BusinesSettingsService` (`get_alert_type_master`,
> `get_alerts_list`, `enable_desable_alert`) and `ReportService.GetDashboardSettingData`
> (= `get_dashboard_setting_data`). Call sites: the main dashboard component `chunk-8168`
> (tiles + headcount + attendance + wishes), the alerts screen `chunk-7166`, the notification-template
> screen `chunk-9985`, the dashboard-settings modal `chunk-484`, and `chunk-2223`/`chunk-2825` (which
> also read `get_tpay_dashboard_data` / `GetDashboardSettingData`).

## Read endpoints (in-scope for the CLI)

All seven are on the **business** backend (`https://business.tankhapay.com/api/`), all `post_enc`
(encrypted POST). One JWT authorizes the call — see [[Auth-and-Access]].

| Endpoint (path) | Backend | Request payload keys | Returns | Notes |
|---|---|---|---|---|
| `dashboard/get_tpay_dashboard_data` | business | `action` (one of `get_employee_list`, `get_employee_attendance`, `get_employee_birthday`, `get_employee_workanniversary`, `get_employee_holidays`, `get_employee_leave`, `get_probation_renewal_emplist`, `get_contract_renewal_emplist`), `accountId`, `geo_location_id`, `ouIds`; the birthday/anniversary actions also add `selectedDate` (from a `#FromDate`/`#FromDate1` field) | one dashboard tile's rows per `action` — employee list, today's attendance, upcoming birthdays / work anniversaries / holidays / leaves, and probation / contract-renewal due lists | **The main tile fetcher — one call per widget, switched by `action`.** Response is `JSON.parse(aesDecrypt(commonData))[0]` — decrypted **and** indexed at `[0]` (the payload is a single-element array whose `[0]` holds the rows). `accountId`/`geo_location_id`/`ouIds` are all **plaintext**. |
| `dashboard/get_employees_count_details` | business | `action:"get_employees_count_details"`, `accountId`, `p_ou_locationid` (= `geo_location_id`), `status_filter`, `ouIds`, `job_type`, `keyword`, `pagesize`, `pageindex` (0-based, `this.p-1`), `department_id`, `designantion_id` *(sic)*, `project`, `forotherpagefuncdesgid` | paginated headcount grid: employee rows + counts, filtered by unit/department/designation/project/status/job-type | **Gotcha:** response is consumed **raw** — `this.employees_count_details_data = t.commonData` with **no** `aesDecrypt`; `commonData` is already a plain array/object here, not a ciphertext blob. `pageindex` is 0-based. `status_filter`/`job_type`/`keyword` are the UI filters (`""` = no filter). |
| `dashboard/get_today_attendence_reports` | business | `action:"get_today_attendence_reports"`, `accountId`, `geo_location_id`, `productTypeId`, `att_date`, `ouIds`, `keyword`, `status` (the `filter_emp_val` dropdown), `pageindex` (0-based), `pagesize` | today's attendance rows for the account's employees | **Gotcha:** response consumed **raw** (`this.attendanceDetails_data = t.commonData`), no decrypt. `att_date` is built client-side as `d+"-"+m+"-"+yyyy` — a **`D-M-YYYY`** string with **non-zero-padded** day/month (e.g. `5-7-2026`), dash-separated. All ids plaintext. |
| `dashboard/get_dashboard_status` | business | `account_id` (note snake_case; = `tp_account_id`) | onboarding-assistant progress object — `commonData.onboarding_assistant…` (the setup-checklist / progress-bar state) | Drives the "complete your setup" progress bar. Response consumed **raw**: `this.progressData = t.commonData?.onboarding_assistant`, no decrypt. Only takes `account_id` — the simplest read in the section. |
| `get_dashboard_setting_data` | business | `action:"GET_DASHBOARD_SETTINGS"`, `customeraccountid` (= `tp_account_id`, all-lowercase key), `subuser_id` (JWT `sub_userid`) | the sub-user's saved dashboard-widget layout / settings object | Bare path (no `dashboard/` prefix). Exposed as `ReportService.GetDashboardSettingData` (module 4245 constant `Aa`, exported `Fg1`). Response consumed **raw**: `this.dashboard_settings = t.commonData`. Returns nothing/`null` when the sub-user has no saved layout. Per-sub-user, so it needs the JWT `sub_userid`, not just the account. |
| `dashboard/get_alert_type_master` | business | `action:"get_alert_type"`, `accountId`, `ouIds` | the alert-type master list (`alertMasterData`) — the catalogue of alert types configurable for the account | Alerts screen (`chunk-7166`). Response consumed **raw** (`this.alertMasterData = t.commonData`). `accountId`/`ouIds` plaintext. |
| `dashboard/get_alerts_list` | business | `action:"get_alerts_list"`, `accountId`, `alert_category` (the `selected_category` filter), `ouIds` *(a second call site uses `action:"get_all_employee_for_alert"` to list assignable employees)* | configured alerts (`alertListData`): each row has `id`, `alert_category`, `enable_status`, `assign_employee_type`, `assign_emplist` (a JSON string the UI `JSON.parse`s) | Response consumed **raw** (`this.alertListData = t.commonData`), then `assign_emplist` is `JSON.parse`d per row. A distinct notification-template screen (`chunk-9985`) reaches the same data via `EmployeeManagementService.getAllNotifications({customerAccountId, actionType:"get_alert", …})` — a different wrapper, same alert rows. |

### Account context these reads need
- `accountId` / `customeraccountid` / `account_id` = **`tp_account_id` = `2719`**, from the decoded JWT `data` blob ([[Auth-and-Access]]). Note the three different key spellings across endpoints.
- `geo_location_id` (also sent as `p_ou_locationid` by the headcount read) = **`37`**, same source.
- `ouIds` = **`"37,2211,38,40,31,1925"`** — the org-unit id list; used by `get_tpay_dashboard_data`, `get_employees_count_details`, `get_today_attendence_reports`, `get_alert_type_master`, `get_alerts_list`. The dashboard component may override with a `forotherpageouid` when drilling into one unit.
- `productTypeId` — from `localStorage.product_type`; only `get_today_attendence_reports` uses it in this section. **Plaintext** here (unlike the `TpTaxesApi` reads in [[Accounts-Taxes]]).
- `subuser_id` = JWT `sub_userid` — only `get_dashboard_setting_data` needs it (the layout is per sub-user).
- Everything is **plaintext** in this section — no field-level AES-encrypted ids (contrast the `mobapi/TpTaxesApi` reads in [[Accounts-Taxes]]).

### The undecrypted-`commonData` pattern dominates this section
Five of the seven reads (`get_employees_count_details`, `get_today_attendence_reports`,
`get_dashboard_status`, `get_dashboard_setting_data`, `get_alert_type_master`, `get_alerts_list`)
consume `t.commonData` **directly** — the server returns a plain (already-decrypted) JSON value in
`commonData`, not the usual base64 ciphertext blob. Only `get_tpay_dashboard_data` follows the
standard `JSON.parse(aesDecrypt(commonData))[0]` path. The CLI must **detect and handle both**: try to
base64-decode + AES-decrypt, and if that fails, treat `commonData` as already-plain JSON. See the same
quirk noted in [[Encryption-Scheme]] and [[Accounts-Taxes]].

## Write endpoints (documented, OUT OF SCOPE)

Never wired into the CLI — see [[Read-Only-Guardrails]]. Four of these are mislabeled `READ` in the
raw TSV (`captures/endpoints-raw.tsv`) because the read-regex matched `get`/`insert`-lookalikes; the
call sites prove they mutate. The section notes are the source of truth, per [[Read-Only-Guardrails]].

| Endpoint | What it does |
|---|---|
| `business · dashboard/enable_desable_alert` | **Reclassified READ → WRITE.** Toggles an alert on/off and assigns employees to it. Call site (`chunk-7166`) sends `{action:"enable_desable_alert", accountId, alerttypeid, assign_employee_type, assign_emplist, alert_category, enable_status}`, fired from the enable/disable toggle switch and the "assign employees" popup — `enable_status` is flipped `"Y"`↔`"N"`. A configuration mutation, not a read. |
| `business · dashboard/insert_birthday_wishes` | **Reclassified READ → WRITE.** Inserts a birthday-wish campaign record. Call site sends `{action:"insert_bithday_wishes"` *(sic)* `, accountid, emp_id, birthday_date, notification_ctg:"birthday-wish"}` from the "publish campaign" button. Mutates + triggers a notification. |
| `business · dashboard/insert_workanniversary_wishes` | **Reclassified READ → WRITE.** Same as above for work anniversaries (`action:"insert_workanniversary_wishes"`, `accountid`, `emp_id`, `birthday_date`). |
| `business · dashboard/send_wishes_email` | **Reclassified READ → WRITE.** Actually emails the wish. `LoginService.sendWishesEmail({name, gender, email_to, email_cc, subject, body, image_url, …})` — sends real email (and a sibling `sendWishesWhatsApp`). Squarely a `send` write. |
| `business · insert_update_dashboard_setting_data` | Saves/updates a sub-user's dashboard-widget layout. Exposed as `ReportService.addUpdateDashboardSetting` (module 4245 constant `sr`); call site (`chunk-484`) sends `{action:"save_dashboard_setting"` or `"update_dashboard_setting", customeraccountid, subuser_id, …}`. Correctly labeled WRITE in the TSV. |

## CLI command mapping

```
tankhapay-portal dashboard tiles --tile employee_list        # dashboard/get_tpay_dashboard_data (action=get_employee_list)
tankhapay-portal dashboard tiles --tile attendance           #   action=get_employee_attendance
tankhapay-portal dashboard tiles --tile birthdays [--date …] #   action=get_employee_birthday    (selectedDate)
tankhapay-portal dashboard tiles --tile anniversaries [--date …] # action=get_employee_workanniversary
tankhapay-portal dashboard tiles --tile holidays             #   action=get_employee_holidays
tankhapay-portal dashboard tiles --tile leave                #   action=get_employee_leave
tankhapay-portal dashboard tiles --tile probation-renewals   #   action=get_probation_renewal_emplist
tankhapay-portal dashboard tiles --tile contract-renewals    #   action=get_contract_renewal_emplist
tankhapay-portal dashboard headcount [--status …] [--dept …] \
        [--designation …] [--project …] [--job-type …] \
        [--keyword …] [--page N] [--size N]                  # dashboard/get_employees_count_details
tankhapay-portal dashboard attendance --date DD-M-YYYY \
        [--status …] [--keyword …] [--page N] [--size N]     # dashboard/get_today_attendence_reports
tankhapay-portal dashboard onboarding-status                 # dashboard/get_dashboard_status
tankhapay-portal dashboard settings                          # get_dashboard_setting_data (needs subuser_id)
tankhapay-portal dashboard alert-types                       # dashboard/get_alert_type_master
tankhapay-portal dashboard alerts [--category …]             # dashboard/get_alerts_list
```

`accountId`/`customeraccountid`/`account_id`, `geo_location_id` (a.k.a. `p_ou_locationid`), `ouIds`,
`productTypeId` and `subuser_id` are always filled from the cached JWT context, never asked for. The
`--date` on `attendance` takes the portal's own `D-M-YYYY` (non-padded) shape; the CLI normalizes to it.

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Sibling sections: [[Accounts-Taxes]] · [[Reports]] · [[Payouts]] · [[Employee-Management]] · [[Masters-Config]] · [[Approvals]] · [[Attendance]] · [[Leave-Management]] · [[Org-User-Management]] · [[Recruit-ATS]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
</content>
</invoke>
