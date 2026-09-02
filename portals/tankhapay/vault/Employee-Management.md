---
tags: [tankhapay, section, employee-management]
---
# Employee Management

The core people-data spine of the TankhaPay Business portal — the largest single section, and the one
every other module joins against. It is what an HR/payroll admin uses to **list, search and open the 593
employees**, read a single employee's full profile (basic / KYC / bank / salary structure / service book /
Form-16 / documents / assets / ESIC dependents), pull the candidate pipeline (people whose salary setup is
still pending, appointees, exited staff), and read the reference **masters** the employee screens depend on
(state Professional-Tax and LWF slabs, master salary structures, TDS payment purposes, letter templates,
min-wage days, exit-reason master, asset master). Key routes: the employee directory / grid
(`getCustomerEmployeeDetails`), the single-employee profile drawer (`getEmployeeProfile`,
`getTpCandidateDetails`, `GetTPSalaryStructure`, `GetServiceBookDetails`, `GetForm16Details`), the
document/letter-template masters, the asset register, and the live-tracking timeline. Everything below is
extracted from the production bundle (`main.7309d5d32824e620.js` + lazy chunks, captured 2026-07-25); every
call is an AES-encrypted POST — see [[Encryption-Scheme]].

> Endpoint constants live in bundle module `4245` (prefixes `u` = business, `w` = mobapi/`tp_employer_api`,
> `or` = `tpPay_api`). The service wrappers are `EmployeeService` / `EmployeemgmtService` (the giant
> `post_enc` wrapper class in `main.js`), `EmployeeManagementService` (document/letter/service-book/asset
> methods), `AttendanceService` (`getCandidateDetails`, `getTicketMaster`) and the crypto-map helper
> `getEncrypted_MapBody` (live-tracking body). Call sites are spread across the employee-list, employee-view
> and salary-setup chunks; the master reads are called from the org-settings and letter-template chunks.

## Read endpoints (in-scope for the CLI)

Backend column: **business** = `https://business.tankhapay.com/api/`, **mobapi** =
`https://mobapi.tankhapay.com/api/`, **tpPay** = `https://mobapi.tankhapay.com/` (one JWT authorizes all —
see [[Auth-and-Access]]). Unless a key is flagged *(AES)* it is sent **plaintext**; response is
`JSON.parse(aesDecrypt(commonData))` unless the Notes say `commonData` is consumed raw.

| Endpoint (path) | Backend | Request payload keys | Returns | Notes |
|---|---|---|---|---|
| `employee/getCustomerEmployeeDetails` | business | `customerAccountId`, `productTypeId`, `GeoFenceId`, `ouIds`, `department`, `designation`, `searchKeyword`, `employeesStatus` | the **main employee directory** rows | The primary list read. All keys plaintext; `ouIds` from `getAppliedOuIds()` (the JWT `ouIds`), `GeoFenceId` = `geo_location_id`. `JSON.parse(aesDecrypt(commonData))`. `department`/`designation` are ids or `""` for all. |
| `employee/getCandidateDetails` | business | `customerAccountId`, `productTypeId`, `searchKeyword` (`""`) | candidate rows: `emp_name`, `orgempcode`, `tpcode`, `emp_code`, `isactive` | Via `AttendanceService`. **Gotcha:** `commonData` is consumed **raw** (`n.commonData.map(...)`) — a plain array, no `aesDecrypt`. |
| `employee/getEmployeeProfile` | business | `customerAccountId` *(AES of `JSON.stringify(id)`)*, `empCode`, `productTypeId` *(AES)* | the employee **profile photo** (mime-sniffed base64) | `empCode` sent plaintext; the two ids AES field-encrypted. Response = `aesDecrypt(commonData)` → raw bytes rendered as `data:<mime>;base64,…`. |
| `employee/getTpCandidateDetails` | business | `empId` *(AES)*, `productTypeId` *(AES)* | full candidate view object: `basicDetails{…joiningStatus…}`, plus KYC/bank/salary sub-objects | **Gotcha:** `commonData` consumed **raw as an object** (`this.view_emp_data=t.commonData`), not decrypted. |
| `employee/GetTPSalaryStructure` | business | `customerAccountId`, `jsId`, `productTypeId` | the applied salary structure for a job-seeker (`jsId`) | `commonData` used **raw** (`this.salaryStructuredata=t.commonData`); `gross…` fields read off it. |
| `employee/getSalaryStructure` | business | `productTypeId` *(AES)*, `customerAccountId` *(AES)*, `empId` *(AES)*, `salaryMode` (`"Custom"`) | the salary structure detail for one employee | All three ids AES-encrypted; `salaryMode` plaintext. |
| `employee/getCandidatesWhoseSalarySetupIsPending` | business | `productTypeId` *(AES)*, `customerAccountId` *(AES)* | candidates with no salary set up yet | `JSON.parse(aesDecrypt(commonData))`. |
| `employee/getAppointeeDetails` | business | `customerAccountId` *(AES)*, `productTypeId` *(AES)*, `empCode` *(AES)*, `ecStatus` | appointee / appointment details for an employee | `ecStatus` from the route params (plaintext). |
| `employee/getEmployerEmployeeFromApi` | business | `pageNo`, `limit` (`20`), `customerAccountId` *(AES)* | paged list of employer employees pending CRM push | **Top-level** fields on the response: `totalRecords`, `pendingToPushInCRM`, `partiallyPushed` — read *outside* `commonData`. |
| `employee/getEmployerOUorGeoFenceDetails` | business | `customerAccountId`, `action` (e.g. org-unit / geo-fence selector), `orgUnitIds` (`""`) | the employer's org-unit / geo-fence tree | `JSON.parse(aesDecrypt(commonData))`. `action` is a string selector supplied by the caller. |
| `employee/getMasterSalaryStructure` | business | `customerAccountId` | master salary-structure templates | `JSON.parse(aesDecrypt(commonData))`. |
| `employee/getMasterTDS` | business | `actionType` (`"GetAllPaymentPurposes"`), `productTypeId` | TDS payment-purpose master | **Gotcha:** `commonData` consumed **raw** (`this.masterTDS=t.commonData`). |
| `employee/getMinWageDays` | business | *(empty object `{}`)* | min-wage-days value | `JSON.parse(aesDecrypt(commonData))`. |
| `employee/GetStateProfessionalTax` | business | `stateCode`, `productTypeId` | the Professional-Tax slab master for a state | `JSON.parse(aesDecrypt(commonData))`; `stateCode` from the state master. |
| `employee/getLWFRateByStateCode` | business | `stateCode` | Labour-Welfare-Fund rate for a state | `JSON.parse(aesDecrypt(commonData))`. |
| `employee/getTicketMaster` | business | `action` (`"PayrollProcessTypes"`), `productTypeId` | ticket/payroll-process type master | Via `AttendanceService`; `commonData` consumed **raw** then `.filter(...)`. |
| `employee/getLetterTemplateCategories` | business | `productTypeId` *(AES)*, `customerAccountId` *(AES)*, `letterTemplateCategoryId` (`""`) | letter-template categories | `JSON.parse(aesDecrypt(commonData))`. |
| `employee/getMasterLetters` | business | `productTypeId`, `customerAccountId`, `lettersType` (e.g. `"Appointment Letter"`), `letterId` | the letter master (one when `letterId` set, else list) | `JSON.parse(aesDecrypt(commonData))` when `letterId` is passed. |
| `employee/getLetterTemplateId` | business | payload passed as a prebuilt variable — **exact keys not resolved in bundle** | a letter template by id | Wrapper is `post_enc` (encrypted read); `JSON.parse(aesDecrypt(commonData))`. Payload object built upstream; keys not fully visible. |
| `employee/getMasterFieldsForTemplateType` | business | payload passed as a prebuilt variable — **exact keys not resolved in bundle** | merge-field master for a template type | Wrapper `post_enc`; `JSON.parse(aesDecrypt(commonData))`. |
| `employee/getTpMinMaxPerDayWages` | business | payload passed as a prebuilt variable — **exact keys not resolved in bundle** | per-day min/max wage bounds | Wrapper `post_enc`. |
| `employee/checkKYCnum` | business | `empId`, `productTypeId` *(AES)*, `doc_type` (`"pan"`) | KYC-number uniqueness/validity **status** | A **validation read** used as a precondition before a KYC write; returns `status` only. Read (no mutation) but not a display feed. |
| `employee/checkUniqueDetails` | business | `productTypeId` *(AES)*, `customerAccountId` *(AES)*, `postData` array `[{mobile, aadharCardNo, panCardNo, bankAccountNo, orgEmpCode}]` | which of the supplied identifiers already exist | Uniqueness validation for new-employee entry; `JSON.parse(aesDecrypt(commonData))`. |
| `employee/checkUniqueForActiveEmp` | business | `productType`, `customerAccountId`, `postData` | uniqueness check scoped to active employees | `JSON.parse(aesDecrypt(commonData))`. |
| `employee/get_dashboard_notifications_data` | business | `action` (read actions e.g. `"get_birthday_images_paths"`), `account_id`, `category` | dashboard notification / birthday-image config | **Action-multiplexed:** only the `get_*` actions are reads (see notes on the write sibling below). `commonData` consumed **raw**. |
| `GetDocumentMasterDetails` | business | `customerAccountId`, `productTypeId` | document-category master | **Gotcha:** `commonData` consumed **raw** (`this.document_master_data=t.commonData`). |
| `GetCandidateDocumentMasterDetails` | business | `customerAccountId`, `productTypeId`, `empId`, `is_employer` (`"Y"`) | per-candidate document master / upload state | `commonData` consumed **raw**. |
| `GetServiceBookDetails` | business | `empCode`, `action` (`"YearwiseServiceBook"`), `year` (`""`), `productTypeId`, `customerAccountId` | year-wise service-book history for an employee | All plaintext. |
| `GetForm16Details` | business | `customerAccountId`, `productTypeId`, `empCode`, `financialYear` | Form-16 record / URL for the employee & FY | **Gotcha:** `commonData` consumed **raw** (`this.GetForm16_data=t.commonData`). |
| `GetExitDetails` | business | `customerAccountId`, `productTypeId`, `empCode` | the exit record for one employee | All plaintext. |
| `TpCandidate/getExitEmployeeList` | business | **payload not found in bundle** (constant present, no call site) | list of exited employees | Wrapper present; call site not located in the captured chunks. |
| `getExitReasonMaster` | business | **payload not found in bundle** (constant present, no call site) | exit-reason master list | Read by name; no call site captured. |
| `getEmployeeMenu` | business | *(empty object `{}`)* | the role's employee-menu HTML | `commonData` is menu HTML, merged into `localStorage.activeUser` as `employeeMenuHtml`. |
| `get_asset_master` | business | `action` (`"get_asset_list"`), `account_id`, `pageindex`, `pagesize`, `keyword` | the asset master list | **Gotcha:** rows are nested under `.data` (`this.asset_list_data=t.data`), **not** `commonData`. |
| `get_asset_report` | business | `action` (`"get_assets_list_report"`), `account_id`, `page_index`, `page_size`, `search_keyword`, `from_dt`, `to_dt`, `assigned_location` | the asset assignment report | `from_dt`/`to_dt` are date strings; rows under `.data`. |
| `get_assets` | business | `action` (`"get_assigned_assets_list"`), `account_id`, `emp_code`, `page_index`, `page_size` | assets assigned to one employee | Rows under `.data`. |
| `TpLiveTrackingApi/GetEmployeeEventLiveTrackingDetails` | business | `productTypeId`, `customerAccountId`, `actionType`, `empCode`, `timelineDate`, `eventId`, `orgUnitId` (built by `getEncrypted_MapBody`) | GPS live-tracking timeline events for an employee/day | Body built by the crypto-map helper (whole body AES). A parallel copy of this API also lives at `businessprdapi.azurewebsites.net` — the CLI uses the `business` host. `timelineDate` is a date string. |
| `Insurance/GetCandidateEsicDependents` | mobapi | **payload not found in bundle** (no call site in business bundle) | ESIC dependents for a candidate | Employee/onboarding endpoint; not exercised by the business SPA. |
| `MasterApi/GetEsicRelationship` | mobapi | **payload not found in bundle** (no call site in business bundle) | ESIC relationship master (dependent relations) | Master lookup; no call site captured. |
| `employee/attendance/GetKYCBenifitsData` | tpPay | **payload not found in bundle** (no call site in business bundle) | KYC-linked benefits data | Wrapper uses **plain `post`** (not `post_enc`) — likely an unencrypted read on the `tpPay` host. |
| `mobile_api/employee/query/tickets` | tpPay | **payload not found in bundle** (mobile-app endpoint) | employee helpdesk ticket list | Reclassified UNKNOWN→READ. Belongs to the employee mobile app; not called by the business bundle. |
| `mobile_api/employee/query/type` | tpPay | **payload not found in bundle** (mobile-app endpoint) | helpdesk query-type master | Reclassified UNKNOWN→READ. |
| `mobile_api/employee/query/query_trail` | tpPay | **payload not found in bundle** (mobile-app endpoint) | message trail for one helpdesk query | Reclassified UNKNOWN→READ. Its `save_query`/`save_query_trail` siblings are writes (below). |

### Account context these reads need
- `customerAccountId` / `account_id` = **`tp_account_id` = `2719`** (JWT `data` blob — [[Auth-and-Access]]). Some reads want it **plaintext** (`getCustomerEmployeeDetails`, masters, assets), others **AES field-encrypted** (`getEmployeeProfile`, `getSalaryStructure`, `getCandidatesWhoseSalarySetupIsPending`, `getAppointeeDetails`, `getEmployerEmployeeFromApi`, `checkUniqueDetails`, `getLetterTemplateCategories`). The per-endpoint column above is the source of truth — **do not assume**.
- `GeoFenceId` = **`geo_location_id` = `37`** — only `getCustomerEmployeeDetails` uses it.
- `ouIds` (`"37,2211,38,40,31,1925"`) — used by `getCustomerEmployeeDetails` via `getAppliedOuIds()`.
- `productTypeId` — from `localStorage.product_type` (also in the JWT); plaintext or AES per the column above.
- Real caller inputs: `empCode`/`empId`/`jsId`, `stateCode`, `financialYear`, `department`/`designation`, `searchKeyword`, `action`/`actionType`, pagination (`pageNo`/`page_index`/`pagesize`), asset date range (`from_dt`/`to_dt`).

### Two decrypt conventions in one section — do not mix them
Many employee reads return `commonData` as a **raw** JSON object/array that is consumed **without**
`aesDecrypt` (`getCandidateDetails`, `getTpCandidateDetails`, `GetTPSalaryStructure`, `getMasterTDS`,
`getTicketMaster`, `GetDocumentMasterDetails`, `GetCandidateDocumentMasterDetails`, `GetForm16Details`,
`get_dashboard_notifications_data`), and the three **asset** reads nest rows under **`.data`**, not
`commonData`. The rest follow the standard `JSON.parse(aesDecrypt(commonData))`. `getEmployeeProfile`
returns raw image bytes, not JSON. The client must branch on this per endpoint — see [[Encryption-Scheme]]
"Gotchas".

## Write endpoints (documented, OUT OF SCOPE)

Never wired into the CLI — see [[Read-Only-Guardrails]]. These mutate live employee/payroll data (hire,
relieve, salary, KYC, documents, assets). The list includes **reclassified** rows: six former "READ" labels
and eighteen former "UNKNOWN" labels that the call sites / verbs prove are writes or side-effecting.

**Reclassified READ → WRITE (heuristic mislabels):**

| Endpoint | What it does |
|---|---|
| `employee/educationDetails` | Add/edit/**delete** an employee's education record. Call site is `updateEducationDetail("delete",…)` / save — an `action`-multiplexed mutation, not a read. |
| `employee/familyDetails` | Add/edit/delete a family-member record (same `action`-multiplexed save/delete pattern). |
| `employee/trainingDetails` | Add/edit/delete a training record (`{id, action, emp_code, customeraccountid}`; `deleteTrainingDetail` confirms it). |
| `employee/fetchEmployeesFromAPI` | Triggers a **server-side import/sync** of employees from the employer's upstream API (`{customerAccountId, pageNo}` → "Employee fetched successfully" → reload). Side-effecting; the pure read is `getEmployerEmployeeFromApi`. |
| `employee/manageTemplateRefNo` | `manage`-verb write on letter-template reference numbers (no read call site; trips the write denylist). |
| `employee/manage_dashboard_notifications_data` | Saves dashboard notification / birthday-wish config (`manage` write sibling of the `get_dashboard_notifications_data` read). |

**Reclassified UNKNOWN → WRITE:**

| Endpoint | What it does |
|---|---|
| `businessEmployeeSSOLogin` | SSO **token exchange** for the employee sub-portal — an auth mutation, not a data read. |
| `employee` (bare `/api/employee`) | Base employee resource with no read call site; ambiguous → out of scope. |
| `employee/CalcTPSalaryStructure` | Computes a TP salary structure during setup. Compute step in the salary-**setup** write flow; ambiguous → out of scope. |
| `employee/SetTpCandidateRestructureMode` | **Sets** a candidate into salary-restructure mode (state mutation). |
| `employee/calculateCandidateSalary` | Computes candidate salary during setup — intermediate write-flow step; ambiguous → out of scope. |
| `employee/calculateCandidateSalaryForExcel` | Same computation formatted for an Excel export; ambiguous → out of scope. |
| `employee/joinTpAttendanceCandidate` | Enrolls a candidate into TP attendance (mutation). |
| `employee/lockUnlockAdvice` | **Locks/unlocks** a payout advice. |
| `employee/manageCandidateAppointmentLetter` | Creates/updates a candidate appointment letter. |
| `employee/manageOrgEmpCodeDelhivery` | Assigns/updates org employee codes (Delhivery integration). |
| `employee/manage_salary_structure` | Creates/updates a salary structure. |
| `employee/rollback_employee_relieving` | **Rolls back** an employee relieving. |
| `employee/rollback_tp_employee_relieving_crm` | Rolls back a relieving in the CRM. |
| `employee/setupSalary` | Persists an employee's salary setup. |
| `employee/uspccalcgrossfromctc` | Server compute of gross-from-CTC in the salary-setup flow; ambiguous → out of scope. |
| `employee/uspccalcgrossfromctc_withoutconveyance` | Same, excluding conveyance; ambiguous → out of scope. |
| `employee/workExperience` | Add/edit/delete an employee work-experience record (`updateExperienceDetail` save/delete). |
| `employeeLoginByMob` | Employee mobile login/punch (Basic-auth). Auth mutation — never touched by the read CLI. |

**Already-WRITE in the inventory (documented for understanding):** employee CRUD & status
(`tp/add_new_employee`, `updateEmployeeDetails`, `updateActiveEmployeeDetails`,
`updateAttendanceEmployeeDetails`, `updateEmployeeStatus`, `updateJoiningStatus`, `updateTpBasicDetails`,
`updateTpBankDetails`, `updateTpKycDetails`, `updateAadharDetails`, `updateTDSExemption`,
`updateSalaryDaysOrDailyAllowanceRate`, `verify_emp_mobile`, `remove_employee`, `insert_profile_photo`,
`save_profile_photo`); CRM sync (`syncEmployeeDetails`, `updateSyncStatus`, `updateEmpDetailsOnCRM`,
`updateEmployeeDetailsThroughApiProcess`); salary (`SaveTpCandidateSalary`, `SaveBulkPreparedSalary`,
`createCustomSalaryStructure`, `saveCustomSalaryStructure`, `saveConsultantSalarySetup`,
`UpdateStatutoryCompliances`); documents & letters (`AddEditDocument`, `AddCatagoryDocumentName`,
`AddNewCatagory`, `EnableDisableCatagoryDocument`, `ChangeDocumentStatusAcceptReject`,
`assignDocumentToCandidate`, `AddCandidateLetters`, `addEditLetterCateogory`, `deleteLetterCtg`,
`addEditTemplate`, `deleteMasterTemplate`, `generateDocxPdfPreview`, `generateAndUploadDocxPdf`,
`generateReviewDocx`, `generateOnlyOfficeToken`, `manageCandidateAppointmentLetter`); Form-16 & TDS
(`AddEditForm16`, `AddEditForm16ByPanCard`); disciplinary & rewards (`AddEditDisciplinaryAction`,
`EditDisciplinaryAction`, `DeleteDisciplinaryAction`, `AddEditRewards`, `EditRewards`,
`DeleteRewardDetails`); exit / full-and-final (`AddEditExitDetails`, `saveExitFormMaster`,
`getExitFormMaster`, `getFullAndFinalDetailsWrapper`, `save_fnfSettlementData_wrapper`,
`reject_fnfSettlementData_wrapper`, `relieve_employee_and_change_flag`, `revertEmployeeExitProcess`,
`lock_and_upload_document`, `markExitFormSentToEmployee`, `saveExitQuestionnaire`,
`submitExitClearanceForm`, `sendEmailExitRemainder`); assets (`insert_update_assets`,
`insert_asset_location_category`, `remove_verify_assets`, `save_remove_confirm_release_asset`); tickets &
support (`createTicket`, `createSupportRequest`, `manage_payout_ticketing_workflow`); business setup reads
that are `manage`/`get_mst` writes (`get_mst_business_setup`, `get_mst_business_setup_dynamic`,
`getUpdateData` — heuristic-flagged writes); and mobile-side writes (`EmployeeSendApplink`,
`SaveEsicDependents`, `save_query`, `save_query_trail`, `GetFaceCheckInUserListing`).

> Note the `exitProcess/getExitFormMaster` and `exitProcess/getFullAndFinalDetailsWrapper` "get" names:
> the inventory flags them WRITE because they sit behind the FnF write wrappers; left out of scope rather
> than guessed, per [[Read-Only-Guardrails]].

## CLI command mapping

```
# ---- employee directory & profile ----
tankhapay-portal employees list [--dept …] [--designation …] \
        [--status Active] [--search …]                 # employee/getCustomerEmployeeDetails
tankhapay-portal employees candidates [--search …]     # employee/getCandidateDetails
tankhapay-portal employees pending-salary              # employee/getCandidatesWhoseSalarySetupIsPending
tankhapay-portal employees from-crm --page … [--limit] # employee/getEmployerEmployeeFromApi
tankhapay-portal employees profile --emp-code …        # employee/getEmployeeProfile        (photo)
tankhapay-portal employees view --emp-id …             # employee/getTpCandidateDetails      (full record)
tankhapay-portal employees appointee --emp-code …      # employee/getAppointeeDetails
tankhapay-portal employees salary-structure --emp-id … # employee/getSalaryStructure
tankhapay-portal employees tp-salary --js-id …         # employee/GetTPSalaryStructure
tankhapay-portal employees service-book --emp-code …   # GetServiceBookDetails
tankhapay-portal employees form16 --emp-code … --fy …  # GetForm16Details
tankhapay-portal employees exit-details --emp-code …   # GetExitDetails
tankhapay-portal employees exited                      # TpCandidate/getExitEmployeeList  (payload TBD)
tankhapay-portal employees documents --emp-id …        # GetCandidateDocumentMasterDetails
tankhapay-portal employees live-track --emp-code … \
        --date … [--event-id …]                        # TpLiveTrackingApi/GetEmployeeEventLiveTrackingDetails

# ---- org / geo units ----
tankhapay-portal org units [--action …]                # employee/getEmployerOUorGeoFenceDetails

# ---- reference masters ----
tankhapay-portal master salary-structures              # employee/getMasterSalaryStructure
tankhapay-portal master tds-purposes                   # employee/getMasterTDS
tankhapay-portal master min-wage-days                  # employee/getMinWageDays
tankhapay-portal master professional-tax --state …     # employee/GetStateProfessionalTax
tankhapay-portal master lwf --state …                  # employee/getLWFRateByStateCode
tankhapay-portal master ticket-types                   # employee/getTicketMaster
tankhapay-portal master exit-reasons                   # getExitReasonMaster            (payload TBD)
tankhapay-portal master documents                      # GetDocumentMasterDetails
tankhapay-portal master menu                           # getEmployeeMenu
tankhapay-portal letters categories                    # employee/getLetterTemplateCategories
tankhapay-portal letters list --type … [--letter-id …] # employee/getMasterLetters

# ---- assets ----
tankhapay-portal assets list [--search …]              # get_asset_master
tankhapay-portal assets report [--from --to] [--loc …] # get_asset_report
tankhapay-portal assets of-employee --emp-code …       # get_assets

# ---- validation helpers (read-only status lookups) ----
tankhapay-portal check kyc --emp-id … --doc-type pan   # employee/checkKYCnum
tankhapay-portal check unique --mobile … --pan … …     # employee/checkUniqueDetails
```

`accountId` (`2719`), `geo_location_id` (`37`), `ouIds` and `productTypeId` are always filled from the
cached JWT context — the CLI encrypts each per the endpoint's convention (see the read table) and never
asks for them. Endpoints whose payloads were not resolvable in the bundle (`getExitEmployeeList`,
`getExitReasonMaster`, `getLetterTemplateId`, `getMasterFieldsForTemplateType`, `getTpMinMaxPerDayWages`,
`getMaxEmpLimitByDep`, `getDepWiseOTReport`, `getuserIdcardWeb`, `employeeby_jsid`, the three
`Insurance`/`MasterApi`/`query` mobile reads) are wired only after a live capture confirms their keys —
never guessed.

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Pages-and-Routes]]

Sibling sections: [[Accounts-Taxes]] · [[Reports]] · [[Payouts]] · [[Masters-Config]] · [[Dashboard]] · [[Approvals]] · [[Attendance]] · [[Leave-Management]] · [[Org-User-Management]] · [[Recruit-ATS]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
