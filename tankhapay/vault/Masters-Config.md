---
tags: [tankhapay, section, masters-config]
---
# Masters & Configuration

The reference-data and setup layer that every other section reads from: **generic masters**
(`master/*`, `MasterApi/*` — departments, designations, units, salary structure, holidays,
travel/ESI dispensary masters), the **form-builder** (`formbuilder/*` — custom forms + workflow
requests), **email/notification templates** (`emailTemplates/*`), **minimum-wages** master
(`minimum-wages/*`), **HR policies** (`policy/*`) and the **business-settings** page. Reads fetch all
this master data; writes create/edit departments, designations, units, holidays, forms, templates
and wages. AES-encrypted POST ([[Encryption-Scheme]]); one JWT ([[Auth-and-Access]]). 33 reads,
28 writes (incl. 14 mis-tagged `save*`/`insert*`/`update*` reclassified to write).

## Read endpoints (in-scope for the CLI)

| Command (`masters …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `master` | business | `actionType`, `productTypeId` | generic master (`MasterApi/GetMaster`) |
| `master-data` | business | account ctx | master data bundle |
| `all-state` | business | account ctx | states master (`master/getAll_state`) |
| `all-holiday-state` | business | `action`, `account_id` | holiday states |
| `manage-holidays-master` | business | `action`, `account_id`, `calender_year` | holidays master (read `action`) |
| `manage-holiday-state-unit-master` | business | `action`, `customeraccountid`, `ou_unit_id`, `state_unit_name` | holiday state-unit master |
| `manage-tp-master` | business | `action`, `account_id` | TP master (read `action`) |
| `dept-wise-employees` | business | `action`, `customerAccountId`, `departmentid`, `desgid` | employees by dept/designation |
| `tpay-emp-details` | business | `actionType`, `customerAccountId`, `empCode` | TPay employee master detail |
| `unit-salary-structure-data` | business | account ctx | unit salary-structure master |
| `calculation-basis` | business | `encrypted` field | salary calculation-basis master |
| `attendance-only` | business | `attendanceOnly`, `customerAccountId`, `id` | attendance-only config |
| `contractrenewal` | business | account ctx | contract-renewal master |
| `travel-master` | mobapi | `actionType`, `customerAccountId`, `empCode`, `productTypeId` | travel master |
| `min-wage-category-by-state` | business | `minWagesStateName`, `productTypeId`, `customerAccountId` | min-wage categories for a state |
| `getminwagemasterlist` | business | `state`, `category`, `fromDate`, `toDate` | minimum-wage master list |
| `getwagescategories` | business | account ctx | wage categories |
| `state-esi-dispensaries` | mobapi | account ctx | ESI dispensaries by state |
| `hr-policy-list` | mobapi | `customerAccountId`, `empCode`, `productTypeId`, `keyId` | HR policy documents |
| `reimbursement-claim` | business | `recipient_mobile`, `amount`, `status` | reimbursement-claim master |
| `leave-application-approval` | business | `recipient_mobile`, `from_date`, `to_date`, `cancelledBy` | leave-approval master text |
| `leave-application-rejection` | business | `recipient_mobile`, `from_date`, `to_date`, `cancelledBy` | leave-rejection master text |
| `form-builder-wrapper` | business | account ctx | form-builder definitions |
| `form-builder-wrapper-public` | business | `customerAccountId`, `id`, `actionType`, `md5CustomerAccountId` | public form-builder wrapper |
| `form-fields-wrapper` | business | account ctx | form fields |
| `master-field-list-wrapper` | business | account ctx | master field list for forms |
| `preview-list-wrapper` | business | account ctx | form preview list |
| `pending-workflow-requests-wrapper` | business | account ctx | pending form-workflow requests |
| `notification-master-wrapper` | business | account ctx | notification master |
| `all-notifications-wrapper` | business | account ctx | all notification templates |
| `faq-category` | mobapi | `category_cd` | FAQ categories |
| `show-bus-setting-page` | business | `action`, `account_id` | business-settings page data |
| `use-session` | business | `action`, `customerAccountId`, `session_id` | session read |

### Account context
`account_id`/`customeraccountid`/`customerAccountId` = **2719**, `productTypeId` from JWT. `actionType`
/`action` picks the read mode on the many `manage_*`/`MasterApi` endpoints; `departmentid`, `desgid`,
`empCode`, `calender_year`, state/category via `--set`. `calculation-basis` wants a pre-encrypted
`encrypted` field — see [[Encryption-Scheme]].

## Write endpoints (documented, OUT OF SCOPE)

```
masters (RECLASSIFIED read→write) : master/{saveDepartmentDirect, saveDepartmentUnit, saveDesignation,
    saveDesignationUnit, saveOrUpdateFunctionalDesignation, saveUpdateUnit, saveCustomSalaryStructure_unit,
    insertLetterHead, bulk_insert_holiday_master, mapEmployee, sendWhatsAppWish, updateEmployeesOUandGeoFencingId,
    update_employer_mobile_email, update_employer_mobile_email_hub}
form-builder : formbuilder/{create_formbuilder_wrapper, save_formbuilder_wrapper, save_formPreview_wrapper,
    updateWorkflowRequestWrapper, update_notify_status_wrapper}
templates    : emailTemplates/{sendReportsMail, generate_email_template_ai, getWorkflowApproverEmailsWrapper}
min-wages    : minimum-wages/{saveminwagemaster, editminwagemaster, addwagescategory}
policy       : policy/{save_attendance_remark_setting, get_attendance_remark_setting}, AddNewCatagory
```
UNKNOWN (not wired — `manage*`/`publish`/`parse`): `emailTemplates/manage_notification_wrapper`,
`formbuilder/publish_form`, `manage_birthday_email_template`, `minimum-wages/parseminwagedocument`,
`policy/{manageEmpAppSettings, managePolicy, manageProjects, manageResources, managevendors}`.

## CLI command mapping

```
tankhapay-portal masters master --set actionType=…
tankhapay-portal masters dept-wise-employees --set departmentid=… --set desgid=…
tankhapay-portal masters getminwagemasterlist --set state=… --set category=…
tankhapay-portal masters hr-policy-list --set empCode=…
tankhapay-portal masters show-bus-setting-page --set action=…
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
