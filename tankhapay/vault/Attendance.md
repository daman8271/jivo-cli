---
tags: [tankhapay, section, attendance]
---
# Attendance, Shifts & Live-Tracking

The attendance engine of the TankhaPay Business portal — how an HR/payroll admin sees who was
present. It spans **daily/monthly attendance** (per-employee and employer-wide grids, today's live
count, consolidated unit views, arrears and manual-salary adjustments), **shifts & policies**
(shift masters, break/OT/on-duty settings, employee policy), **biometric & face punch** (device
config, punch data), and **live GPS tracking** for field staff (route distance, kilometres, live
positions). Reads live under `attendance/*`, `shift/*`, `device/*`, `livetrack(ing)/*`. Every call
is an AES-encrypted POST — see [[Encryption-Scheme]]; one JWT authorizes it — see [[Auth-and-Access]].

> Corpus: bundle module `4245` (endpoint constants) + the attendance/shift/live-track feature
> chunks. `37` reads are wired; `68` writes + `6` ambiguous (`manage*`, `inactiveAttendanceByIds`,
> `forgot_password`) are documented **out of scope** ([[Read-Only-Guardrails]]).

## Read endpoints (in-scope for the CLI)

Backend **business** = `business.tankhapay.com/api/`, **mobapi** = `mobapi.tankhapay.com/api/`.
Account-context params (`accountId`/`customerAccountId` = `2719`, `GeoFenceId`/`geo_location_id`
= `37`, `productTypeId`) are auto-filled from the JWT; the CLI injects the `accountId`/`geo`/`ouIds`
triple by default and the rest go via `--set`.

| Command (`attendance …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `att-master-list` | business | `action`, `customeraccountid`, `unit_id`, `department_id` | attendance master rows |
| `attendance-punch-data` | business | `customerAccountId`, `fromDate`, `toDate` | raw punch in/out records |
| `break-details` | business | account ctx | configured break windows |
| `business-device` | business | `action`, `account_id` | registered biometric devices |
| `calendar` | business | `action`, `employer_id`, `month`, `year` | month attendance calendar |
| `check-advance-for-associate` | business | account ctx + `empCode` | advance eligibility for an associate |
| `check-expense-limit` | business | account ctx | expense-claim limit config |
| `checkin-checkout-report` | business | date range | check-in/out report rows |
| `custom-month-attendance` | business | `month`, `year` | custom-period attendance |
| `employee-kilometers` | business | `action`, `customeraccountid`, `month`, `year` | field-staff km totals |
| `employee-kilometers-day-wise` | business | account ctx, `month`, `year`, `empCode` | per-day km for one employee |
| `employee-list-for-live-tracking` | business | `action`, `customeraccountid`, `live_tracking_status` | employees enrolled in live tracking |
| `employee-policy-details` | business | `actionType`, `customerAccountId` | attendance policy per employee |
| `employees-for-ledger` | business | `customerAccountId`, `searchKeyword` | employees for ledger entry |
| `employer-month-attendance` | business | `customerAccountId`, `month`, `year` | employer-wide month grid |
| `employer-month-attendance-for-excel` | business | `customerAccountId`, `month`, `year`, `GeoFenceId`, `attendanceSource`, `productTypeId`, `action`, `postOffered` | month grid (Excel shape) |
| `employer-today-attendance` | business | `customeraccountid`, `productTypeId`, `att_date`, `emp_name`, `status`, `GeoFenceId` | today's attendance list |
| `employer-today-attendance-new` | business | as above (newer variant) | today's attendance (v2) |
| `employer-today-required-attendance` | business | `…`, `approval_status`, `pageNo`, `pageLimit`, `GeoFenceId` | today's required-attendance list (paged) |
| `fetch-arear-by-month-year-emp-code` | business | `customerAccountId`, `month`, `year`, `empCode` | arrear rows for one employee |
| `fetch-attendancefrom-client` | business | `from_date`, `to_date` | attendance pulled from client system |
| `live-tracking-data-mobile` | mobapi | account ctx + `empCode` | live-tracking positions (mobile) |
| `live-tracking-get-route-distance` | mobapi | route points | computed route distance |
| `live-tracking-reports` | business | date range | live-tracking report rows |
| `manage-deviation-salary-details` | business | `action`, `customerAccountId`, `month`, `year`, `productTypeId`, `empCode`, `amount` | deviation-salary view (read `action`) |
| `manual-salary-info` | business | `customerAccountId`, `month`, `year`, `searchKeyword` | manual-salary entries |
| `master-list` | business | account ctx | attendance master list |
| `master-shift` / `master-shift-2` | business | account ctx | shift masters (`attendance/get_master_shift`, `shift/getMasterShift`) |
| `month-dates-days` | business | `employer_id`, `month`, `year` | calendar dates/day-types for a month |
| `monthly-attendance` | business | `emp_code`, `month`, `year`, `productTypeId`, `customerAccountId` | one employee's month attendance |
| `shift-details` | business | account ctx | shift definitions |
| `tea-allowance-rate` | business | account ctx | tea-allowance rate master |
| `timesheet-data` | business | `action`, `accountid`, `fromdate`, `todate`, `pagesize`, `pageindex`, `keyword_search`, `approval_status` | timesheet grid (paged) |
| `unit-consolidated-attendance` | business | `customeraccountid`, `empCode`, `attYear`, `attMonth` | consolidated per-unit attendance |
| `unit-today-attendance` | business | `customeraccountid`, `att_date`, `emp_name`, `approval_status`, `productTypeId`, `attendanceSource`, `unitParameterName`, `postingDepartment`, `postOffered` | today's attendance for a unit |
| `view-arrear-details` | business | `action`, `customerAccountId`, `month`, `year`, `empCode`, `batchId` | arrear detail rows |

### Account context these reads need
`customerAccountId`/`customeraccountid`/`accountid`/`account_id`/`employer_id` all = **`tp_account_id` 2719**;
`GeoFenceId` = **`geo_location_id` 37**; `productTypeId` from the JWT. Month/year, `empCode`, date
ranges and `approval_status` are real filters the caller supplies (mostly via `--set`). Note the
inconsistent casing across endpoints — send the exact key each one wants.

## Write endpoints (documented, OUT OF SCOPE)

Never wired — [[Read-Only-Guardrails]]. 68 writes + 6 ambiguous. These mutate live attendance, salary
and devices:

```
punch/attendance saves : attendance/{TpCheckInOut, save_monthly_attendance(_bulk), save_excel_bulk_att(_new),
    saveManualSalaryInfo, saveBulkManualSalaryInfo, saveUnitConsolidatedAttendance, saveBulkDeviationSalaryDetails,
    updateDeleteCheckIn, updateManualTDS, verifyArrear, rejectManualSalary, activePunchAttendanceByIds,
    att_file_upload, bulk_deduction_upload, bulkLedgerEntry, SaveTpVoucher}
reprocess/kafka       : attendance/{reProcessEmployeeAttendance(Advance), kafka_reProcessEmployeeAttendance},
    kafka_process_att_punches_hub, process_att_punches_hub, office/syncattpunch, saveAttendancefromClient
shifts/settings       : attendance/{create_new_shift, create_new_break, create_shift_rotation,
    create_employee_shift_mapping, create_general_settings, create_shift_specific_settings, create_bulk_advice,
    save_onduty_settings, saveUpdateOtrule, saveEditOtRules, generate_payment_advice, manageBulkAdvices,
    manage_missed_punch_att, enable_disable_status, delete_department, delete_designation, delete_orgunit,
    deleteSingleConsolidatedAttendance}, shift/{saveUpdateShiftDetail, updateShiftPolicyDetails}
devices/face/biometric: device/{insert_business_device, update_business_device_by_id, manage_biometric_punch_config,
    remove_biometric_punch_config}, FaceApi/{markAttendance, registerFace}, approveRejectFaceRegister,
    TpCandidateAPIController/syncBioMatricCheckInOutData
live tracking         : livetrack/{update_live_tracking, live_tracking_save_route_distance}
approvals/deviation   : TpBusinessAPI/approveRejectMissedPunchAttendance, approveRejectMissPunch,
    TpCandidateCheckInOut/{CalculateDeviationFines, UpdateDeviationFines}
```

Also WRITE-classed reads that *look* like reads but the extractor flagged as mutating/side-effecting
(held out): `attendance/{getAttendancePunchDetails, get_missed_punch_att, get_att_import_header,
get_approved_days, get_shift_specific_settings}`, `device/get_biometric_punch_config`,
`TpCandidateAPIController/GetTpCheckInOutSummaryDetailReport`. Ambiguous `manage*` /
`inactiveAttendanceByIds` / `forgot_password` are UNKNOWN and not wired.

## CLI command mapping

```
tankhapay-portal attendance employer-today-attendance                 # today's list
tankhapay-portal attendance employer-month-attendance --set month=7 --set year=2026
tankhapay-portal attendance monthly-attendance --set emp_code=… --set month=7 --set year=2026
tankhapay-portal attendance timesheet-data --set fromdate=… --set todate=… --set pagesize=50 --set pageindex=0
tankhapay-portal attendance unit-consolidated-attendance --set empCode=… --set attMonth=7 --set attYear=2026
tankhapay-portal attendance master-shift        # shift master
tankhapay-portal attendance employee-kilometers --set month=7 --set year=2026   # live-tracking km
```
`--set customerAccountId=@accountId` / `--set GeoFenceId=@geo` when an endpoint uses those exact keys.

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
