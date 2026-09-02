---
tags: [tankhapay, meta, coverage, pages, source-of-truth]
---
# TankhaPay — Complete Page & Route Inventory (coverage map)

> **The "don't miss anything" guarantee.** Every route the Angular app defines (top-level page + every
> subpage/child route), extracted from the full JS corpus (main + 58 chunks). **325 routes**, grouped by
> the 14 study sections. Each section note ([[00-TankhaPay-Atlas]]) documents the READ endpoints behind
> these pages; the CLI wires a command for **every** READ endpoint so all page data is reachable.

Auth/legal/preview routes (login, logout, reset-password, terms, print/preview, etc.) carry no business
data and are out of read scope. Everything else maps to a section below.

## [[Dashboard]]  (6 routes)

`dashboard`  ·  `org-chart`  ·  `rf-inventory-dashboard`  ·  `summary-dashboard`  ·  `summary-dashboard-new`  ·  `welcome`

## [[Employee-Management]]  (49 routes)

`add-new-template`  ·  `asset-assignment`  ·  `asset-details`  ·  `asset-inventory`  ·  `asset-status`  ·  `asset_master`  ·  `birthday-template`  ·  `bulk-employee`  ·  `bulk-exit`  ·  `bulk-exit-upload`  ·  `bulk-suspend`  ·  `check-in/check-in-by-emp-code`  ·  `digilocker`  ·  `document-master`  ·  `documents`  ·  `edit-employee`  ·  `empcontract`  ·  `empl-help-and-support/empl-tickets`  ·  `employee-app-setting`  ·  `employee-att-status`  ·  `employee-daily-hour-wise`  ·  `employee-detail`  ·  `employee-details`  ·  `employee-leave-balance`  ·  `employee-log`  ·  `employee-mgmt`  ·  `employee-shift-mapping`  ·  `employee-sso/:accountid/:employeessoid`  ·  `employee/:empid`  ·  `employees`  ·  `empprobation`  ·  `exit-clearance-form`  ·  `exit-interview-ques`  ·  `full-and-final`  ·  `group-employer`  ·  `hr-letter`  ·  `kyc-details`  ·  `leave/employee-leave-balance`  ·  `list-employees`  ·  `meeting_report/meeting_by_emp-code`  ·  `onboarding`  ·  `probation-period`  ·  `reportingprobation`  ·  `rf-inventory-emp`  ·  `service-book`  ·  `single-employee`  ·  `travel-expense/:emp_code`  ·  `travel-request/:emp_code`  ·  `view-employee-detail/:empid`

## [[Attendance]]  (51 routes)

`att-data-payroll`  ·  `att-report`  ·  `att-reprocess`  ·  `attendance`  ·  `attendance-unit`  ·  `biometric_punches`  ·  `break-details`  ·  `bulk-attendance`  ·  `bulk-attendance-new`  ·  `bulk-lock-attendance`  ·  `check-in`  ·  `check-in-checkout`  ·  `custom-monthly-check-in-out-report`  ·  `daily-att-status`  ·  `daily-attendance`  ·  `daily-bio-matric-report`  ·  `daily-in-out-listing-report`  ·  `deviation-report`  ·  `device-settings`  ·  `dipole-timesheet`  ·  `face-checkin`  ·  `face-checkin-list`  ·  `face-register`  ·  `geofence-setting`  ·  `geofences/:geofencingid`  ·  `geofences/:geofencingid/:actiontype`  ·  `gps-internet-compliance-report`  ·  `in-out-time-report`  ·  `live`  ·  `live-tracking`  ·  `live-tracking-attendance-report`  ·  `live-tracking-exceptions-report`  ·  `live-tracking-report`  ·  `livetracking-report`  ·  `manage-early-late-att`  ·  `missed-punch`  ·  `missed-punch-approval`  ·  `missed-punch-report`  ·  `monthly-hour-summary`  ·  `monthly-hourly-attendance`  ·  `monthly-in-out-shift-report`  ·  `pre-attendance`  ·  `roster`  ·  `self-checkin`  ·  `shift-details`  ·  `shift-management`  ·  `shift-rotation`  ·  `shift-specific-settings`  ·  `smart-attendance`  ·  `sync-att`  ·  `time-line`

## [[Leave-Management]]  (21 routes)

`bulk-compoff-balance`  ·  `bulk-holiday`  ·  `bulk-leave`  ·  `comp-off-request-approval`  ·  `compoff`  ·  `daily-leave-report`  ·  `holiday-settings`  ·  `leave`  ·  `leave-application`  ·  `leave-details`  ·  `leave-encashment-report`  ·  `leave-general-settings`  ·  `leave-mgmt`  ·  `leave-settings`  ·  `leave-type`  ·  `leave/daily-leave-report`  ·  `leave/leave-booked-balance`  ·  `leavepolicymaker`  ·  `monthly-leave-taken-report`  ·  `wfh-request`  ·  `wfh-request-approval`

## [[Payouts]]  (55 routes)

`Advance`  ·  `Advance-Payment`  ·  `Reimbursement`  ·  `Reimbursement-Payment`  ·  `advance-payout`  ·  `allowance-bonus`  ·  `arrear-report`  ·  `arrear-salary`  ·  `bonus-disbursement`  ·  `bonus-report`  ·  `bulk-salary`  ·  `bulk-salary-correction`  ·  `bulk-salary-custom`  ·  `consultant_payment`  ·  `d-incentive`  ·  `disbursement-report`  ·  `fetch-bank-report`  ·  `imprest-reimburse-approval`  ·  `imprest-request`  ·  `liability-report`  ·  `loan_outstanding_report`  ·  `make-payment`  ·  `master-meal-voucher`  ·  `master_voucher_type`  ·  `meal-voucher-details`  ·  `multiple-payout`  ·  `pay-summary`  ·  `pay-summary/advance-slip/:id`  ·  `pay-summary/consultant-invoice/:id`  ·  `pay-summary/multiple-salary-slip`  ·  `pay-summary/salary-slip/:id`  ·  `pay_consultant`  ·  `payment`  ·  `payout`  ·  `payout-details/:id`  ·  `payout-disbursement`  ·  `payouts`  ·  `payrolling`  ·  `piece`  ·  `proof_of_reimbursement`  ·  `reimbursement`  ·  `report_payment`  ·  `revise-salary/:id`  ·  `salary-computation`  ·  `salary-correction`  ·  `salary-management`  ·  `salary-stucture`  ·  `salary-verification`  ·  `setup-salary`  ·  `starting-balance`  ·  `tankhapay-ai`  ·  `tea-allowance`  ·  `voucher`  ·  `voucher/add-new-voucher`  ·  `voucher_report`

## [[Approvals]]  (8 routes)

`approval`  ·  `approval-workflow`  ·  `onduty-applications`  ·  `travel`  ·  `travel-expense`  ·  `travel-request`  ·  `workflow-approval`  ·  `workflowapproval`

## [[Accounts-Taxes]]  (23 routes)

`Investment-Declaration`  ·  `Proof-of-Investment`  ·  `account-twenty-one`  ·  `accounts`  ·  `declaration-submitted-report`  ·  `designation`  ·  `epf-ecr`  ·  `epf-summary`  ·  `esi-dependent`  ·  `esi-ecr`  ·  `esi-summary`  ·  `esic_report`  ·  `function-designation`  ·  `income-tax-calculator`  ·  `investments`  ·  `lwf-report`  ·  `public/applform/:accountid`  ·  `recruit`  ·  `tax-summary-report`  ·  `tds`  ·  `tds-report`  ·  `uan_report`  ·  `view-declaration`

## [[Reports]]  (15 routes)

`all_visitor_report`  ·  `annual-report`  ·  `audit-log-report`  ·  `billing-report`  ·  `dept-wise-ot-report`  ·  `dsr-da-report`  ·  `dynamic-report`  ·  `expenses-report`  ·  `increment-report`  ·  `meeting_report`  ·  `monthly_check_inout_report`  ·  `rembursement-report`  ·  `report`  ·  `reportingcontract`  ·  `reports`

## [[Recruit-ATS]]  (3 routes)

`applications`  ·  `public/wtl-form/:token`  ·  `registration-approved`

## [[Masters-Config]]  (24 routes)

`business-settings`  ·  `d-performance`  ·  `department`  ·  `form`  ·  `form/public/:token`  ·  `formbuilder`  ·  `general-settings`  ·  `hr-policy`  ·  `item-rate-master`  ·  `letterhead`  ·  `master-configuration`  ·  `minimum-wages`  ·  `notification-builder`  ·  `notification-settings`  ·  `performance`  ·  `policies`  ·  `policy/:id`  ·  `project-master`  ·  `unit-parameter-listing`  ·  `unit-parameter-listing/:id`  ·  `unit-parameter-settings`  ·  `unit-parameter-settings/:orgid`  ·  `vendor-master`  ·  `view-minimum-wages`

## [[Org-User-Management]]  (9 routes)

`company-details`  ·  `compliance`  ·  `mgmt`  ·  `new-role/:id`  ·  `organization-unit`  ·  `products`  ·  `profile`  ·  `roles`  ·  `user`

## [[Broadcast-Visitor-Help]]  (15 routes)

`all_visitor`  ·  `broadcaster`  ·  `card_wise_visitor`  ·  `faq`  ·  `faqs`  ·  `help-and-support`  ·  `manage-card`  ·  `new-card`  ·  `new_visitor`  ·  `notification`  ·  `notifications`  ·  `notificationsArchive`  ·  `tickets`  ·  `update_visitor`  ·  `visitor`

## [[Contract-Labour-Inventory]]  (3 routes)

`contract-labour`  ·  `contract-renewal`  ·  `inventory`

## [[Training-Performance]]  (8 routes)

`budget`  ·  `feedback`  ·  `pms`  ·  `pms-team-specific`  ·  `survey-management`  ·  `tnd`  ·  `training`  ·  `training-details/:trainingid`

##  Misc/Auth/Legal  (35 routes)

`adult-workers-register`  ·  `billing`  ·  `bulk-deduction`  ·  `bulk-open-balance`  ·  `bulk-upload-pan`  ·  `callback`  ·  `change-password`  ·  `create`  ·  `daily-entry`  ·  `dsr-da`  ·  `edit/:id`  ·  `forgot-password`  ·  `generate-advice`  ·  `generate-password/:id/:non`  ·  `juspayres`  ·  `letter-listing/:id`  ·  `login`  ·  `logout`  ·  `make-payments`  ·  `mobile`  ·  `ot_rules/:id`  ·  `ot_rules_listing`  ·  `path`  ·  `preview-pdf/:id`  ·  `preview/:id`  ·  `previewList`  ·  `privacy-policy`  ·  `reset-password/:id/:non`  ·  `signup`  ·  `sso-login/:ssouid/:emplyrssoid`  ·  `tagged-untagged`  ·  `terms-of-use`  ·  `thank-u`  ·  `vistors_summary`  ·  `workflows`

---
**Total: 325 routes across 14 sections + auth/legal.** Endpoint backing: 726 API endpoints (322 READ / 333 WRITE / 71 to-confirm) in `captures/endpoints-raw.tsv`. See [[TankhaPay-Endpoints]] for the master endpoint index and [[Read-Only-Guardrails]] for why writes are documented but never wired.