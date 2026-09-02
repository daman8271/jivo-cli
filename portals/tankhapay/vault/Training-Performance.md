---
tags: [tankhapay, section, training-performance]
---
# Training & Performance (T&D / PMS)

TankhaPay's learning-and-appraisal module — the only section served primarily by the **`tnd`
backend** (`tnd.tankhapay.com/api/`), with the employee-facing pieces on **mobapi** (`tndApp/*`).
Covers **PMS** (performance-management config, methods, appraisal cycles, employee summaries),
**T&D** (training calendars, exam/feedback previews) and **branding**. Reads preview config,
cycles, summaries and answers; writes create/update PMS config and mark training attendance.
AES-encrypted POST ([[Encryption-Scheme]]); one JWT authorizes `tnd` too ([[Auth-and-Access]]).
8 reads, 8 writes.

## Read endpoints (in-scope for the CLI)

| Command (`training …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `getconfigdata` | tnd | account ctx | PMS configuration data |
| `getmethodslist` | tnd | account ctx | PMS appraisal methods |
| `emp-summary` | tnd | account ctx + `empCode` | employee performance summary |
| `emp-completed-cycle` | tnd | account ctx + `empCode` | employee's completed appraisal cycles |
| `branding-detail` | tnd | account ctx | T&D branding detail |
| `calender-records-by-employee` | mobapi | `action`, `customerAccountId`, `empCode`, `trainingId`, `fromDt`, `toDt`, `productTypeId` | training calendar for an employee |
| `preview-training-exam-answer` | mobapi | `customerAccountId`, `empCode`, `trainingId`, `productTypeId` | employee's training-exam answers |
| `preview-feedback-answer` | mobapi | `customerAccountId`, `empCode`, `trainingId`, `productTypeId` | employee's feedback answers |

### Account context
`customerAccountId` = **2719**, `productTypeId` from JWT. `empCode`, `trainingId`, `fromDt`/`toDt`
via `--set`. The `tnd` reads mostly need only account context; the `tndApp` (mobapi) reads are
per-employee/per-training.

## Write endpoints (documented, OUT OF SCOPE)

```
pms : pms/{saveupdateconfig, createupdateskillset, createskillsettag, createupdatefeedbackcat, uploadpmsfile}
t&d : tndApp/employeeTrainingMarkAttendance, recruit/saveJobPosting
util: TpayCareerWeb/GetCustomerAccIDByDomainName  (resolves an account from a careers domain — held out;
      it is an unauthenticated-style lookup with a write-shaped name, excluded rather than guessed)
```

## CLI command mapping

```
tankhapay-portal training getconfigdata           # PMS config (tnd backend)
tankhapay-portal training emp-summary --set empCode=…
tankhapay-portal training calender-records-by-employee --set empCode=… --set trainingId=… --set fromDt=… --set toDt=…
tankhapay-portal training preview-feedback-answer --set empCode=… --set trainingId=…
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]]
