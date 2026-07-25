---
tags: [tankhapay, section, org-user-management]
---
# Org & User Management — Hierarchy, Geo-fencing, Users, Roles & Employer Profile

The administrative backbone of the portal: the **org hierarchy** (`orgchart/*`), **geo-fencing**
(work locations / `Business/GetGeoFencing`), **users, roles, privileges and module access**
(`user-mgmt/*`), the **employer profile** and its statutory identity (EPF/ESI/social-security,
`employer/*` + `Business/*`), plus **billing/invoice** and **DSRDA** master data. Reads expose the
whole access-control + org picture; writes create users/roles, edit the profile, and — critically —
the whole **OTP / login / password** machinery, all out of scope. AES-encrypted POST
([[Encryption-Scheme]]); one JWT ([[Auth-and-Access]]). 25 reads, 54 writes.

## Read endpoints (in-scope for the CLI)

| Command (`org …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `employer-profile` | business | `customeraccountid`, `productTypeId` | the employer's own profile |
| `switch-employer-profile-data` | business | account ctx | data for switching employer profile |
| `employer-status` | mobapi | `employer_mobile` | employer onboarding status |
| `employer-aggreement` | mobapi | `productTypeId` | employer agreement |
| `customer-invoice-details` | business | `baseAmount`, `noOfEmployees`, `customerAccountId` | invoice/pricing detail |
| `employer-social-security-details` | business | `customerAccountId`, `socialSecurityType` | EPF/ESI social-security config |
| `all-users` | business | account ctx | all portal users |
| `roles` | business | `customerAccountId` | roles |
| `role-by-id` | business | `roleid` | one role |
| `privilege` | business | `profileid` | a profile's privileges |
| `modules` | business | account ctx | app modules |
| `url-access-right-global` | business | `roleid` | global URL access rights for a role |
| `geo-fencing` | business | account ctx | geo-fence (work location) list |
| `geo-fencing-2` | business | `customerAccountId`, `action` | geo-fence list (user-mgmt variant) |
| `geo-fencing-for-particular-id` | business | `customerAccountId`, `action`, `geoFenceId` | one geo-fence |
| `tp-hierarchy` | business | `action`, `account_id` | org hierarchy tree |
| `all-state` | mobapi | account ctx | states master |
| `all-district` | mobapi | `state_code`, `tpAccountId` | districts for a state |
| `area-of-work` | business | account ctx | area-of-work master |
| `reasons-of-leaving` | business | `customerAccountId`, `productTypeId`, `exitTypeId` | exit reasons master |
| `jivo-dsrda-data` | business | `account_id`, `month`, `year` | JIVO DSR/DA data |
| `process-biomatric-data` | business | `action`, `account_id`, `from_date`, `to_date` | biometric sync data (read) |
| `last-sync-stataus` | business | account ctx | last data-sync status |
| `month-dates-days-for-date-range` | business | date range | calendar dates/days for a range |
| `tp-alerts` | business | account ctx | TP alerts (`TpAlertsApi/getTpAlerts`) |

### Account context
`customeraccountid`/`account_id`/`tpAccountId` = **2719**, `productTypeId` from JWT; `roleid`,
`profileid`, `geoFenceId`, `state_code`, `month`/`year` via `--set`.

## Write endpoints (documented, OUT OF SCOPE)

```
users/roles : user-mgmt/{saveUser, saveRole, deleteRole, registerSubUser, savePrivilege, addSubmodule}
profile     : employer/{updateEmployerProfile, saveLeaveTemplate, setDefaultBillingAddress,
    profilePhotoUpload, signature_img_upload, uploadBirthdayImg, file_upload, getEmployerProfile_allAddress},
    update_employer_logo_path, updateEmployerBillingCompany, updateVerficationStatus
statutory   : Business/{UpdateEmployerEpfDetails, UpdateEmployerEsiDetails, DisableStatutoryCompliance,
    SaveGeoFencing, updateEmployeeOuIds, updateEmployeesGeoFenceIds, sendLetterMail(2)}
auth/OTP    : send_OTP, verify_OTP, verify_OTP_enc, verify_user_otp (RECLASSIFIED read→write),
    employer_login_otp_send, employer_register, otp_send_mobile_email_update, otp_verify_mobile_email_update,
    changepassword, reset_password, forgotpassword_send_sms, gst_verify_without_otp
payments    : jusPaySessionOrder, jusPayOrderResponse, JusPaymanageCard, validate_paymentlink_by_orderid,
    employer/employerStartingPaymentset
misc        : budget/{addUpdateBudget, insertBudgetDetail}, outSider/{SaveJivoDsrDaData, RemoveJivoDsrDaData},
    insert_activity_logs, call_sync_attn_data, saveLocationTransferHistory, welcomeSendMail,
    internal/sendFirebaseNotification, enable_desable_remove_work_flow, manage_process_biomatric_data,
    employer/CheckPayrollRunStatus
```
UNKNOWN / auth (not wired): `login`, `direct_login`, `admin/busSSOSignOn`, `superset/accessToken`,
`is_url_expired`, `orgchart/manage_tp_hierarchy`, `manage_background_verification`.

## CLI command mapping

```
tankhapay-portal org employer-profile
tankhapay-portal org all-users
tankhapay-portal org roles ; tankhapay-portal org role-by-id --set roleid=…
tankhapay-portal org geo-fencing
tankhapay-portal org tp-hierarchy --set action=… ; tankhapay-portal org all-district --set state_code=…
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
