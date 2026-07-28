---
tags: [tankhapay, section, approvals]
---
# Approvals — Vouchers, Travel, Meal & Approval Hierarchy

The approval workbench: advance/loan **vouchers**, **travel** requests & expense claims, **meal**
vouchers, **reimbursement** claims for the employer, and the **approval hierarchy/master** that
routes them. The reads here list what is pending/approved and the master data behind it; the writes
approve/reject/disburse. Routes: `approval/*`, `travel/*`, `meal/*`, plus top-level
`getApprovalRequestByActionType` / `getMasterListingOfApproval`. AES-encrypted POST
([[Encryption-Scheme]]); one JWT ([[Auth-and-Access]]). 19 reads, 15 writes.

> Rich, well-parameterised reads — most take a `fromDt`/`toDt` window + a `statusFilter` and return
> per-employee rows. The **approve/reject/disburse** actions are out of scope ([[Read-Only-Guardrails]]).

## Read endpoints (in-scope for the CLI)

| Command (`approvals …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `all-reimbursement-claims-for-employer` | business | `fromDate`, `toDate`, `filterStatus`, `orgUnitId`, `productTypeId`, `customerAccountId` | reimbursement claims to approve |
| `approval-request-by-action-type` | business | `customerAccountId`, `empCode`, `productTypeId`, `approvalId`, `fromDt`, `toDt`, `statusFilter`, `actionType` | pending approvals of a type |
| `master-listing-of-approval` | business | `customerAccountId`, `empCode`, `productTypeId`, `approvalId`, `fromDt`, `toDt`, `statusFilter` | approval master listing |
| `emp-approval-hierarchy` | business | account ctx | employee approval hierarchy |
| `emp-approval-list-data` | business | account ctx | approval list data |
| `manage-approval-master` | business | `action`, `accountid`, `department_id`, `designation_id`, `hierarchy_types` | approval master (read `action`) |
| `latest-salary-period-by-account` | business | `action`, `customeraccountid`, `emp_codes` | latest salary period |
| `canditate-details-for-voucher` | business | `productTypeId`, `customerAccountId`, `searchKeyword`, `searchType`, `year`, `month` | candidates for a voucher |
| `voucher-details` | business | `fromDate`, `toDate`, `deductionId`, `transactionType`, `ledgerType`, `searchKeyword`, `productTypeId`, `subLedgerName`, `customerAccountId` | voucher detail rows |
| `master-ledger-name` | business | `transactionType`, `productTypeId`, `customerAccountId` | ledger-name master |
| `sub-ledger-name` | business | `ledgerName` | sub-ledger names |
| `transaction-type` | business | `productTypeId`, `customerAccountId` | transaction-type master |
| `all-travel-request-summary` | business | `travelId`, `customerAccountId`, `fromDt`, `toDt`, `statusFilter`, `productTypeId`, `postOffered`, `postingDepartment`, `unitParameterName` | travel requests |
| `all-travel-expense-details` | business | `travelId`, `customerAccountId`, `fromDt`, `toDt`, `expFilterStatus`, `productTypeId`, `postOffered`, `postingDepartment` | travel expense claims |
| `travel-summary` | mobapi | `customerAccountId`, `empCode`, `productTypeId`, `travelId`, `fromDt`, `toDt`, `statusFilter` | one employee's travel summary |
| `travel-expense-details` | mobapi | `customerAccountId`, `empCode`, `productTypeId`, `travelId`, `fromDt`, `toDt`, `expFilterStatus` | one employee's travel expenses |
| `master-meal-voucher` | business | `actionType`, `customerAccountId` | meal-voucher master |
| `detail-meal-voucher` | business | `actionType`, `customerAccountId`, `monthYear` | meal-voucher detail |
| `manage-master-meal-voucher` | business | account ctx (read `action`) | meal-voucher master listing |

### Account context
`customerAccountId` = **2719**, `productTypeId` from JWT; `fromDt`/`toDt` are `DD/MM/YYYY`, `statusFilter`
/`expFilterStatus` are the UI status chips (`Pending`/`Approved`/`Rejected`/`All`). Supply via `--set`.

## Write endpoints (documented, OUT OF SCOPE)

```
vouchers : approval/{SaveVoucher, SaveAdvanceAndLoanVoucher, RejectVoucher, DisburseVoucher,
    RecordVoucherPayment, SaveOtherLedgerName, SaveOtherLedgerCustomerSpecific}
approval : insert_update_approval_template, submitApprovalFeedbackForm
travel   : travel/{saveTravelDetails, updateTravelExpenseDetails, updateTravelReqExpStatus},
    approveTravelRequest, approveRejectTravelExpense, approveRejectOnduty (mobapi)
```

## CLI command mapping

```
tankhapay-portal approvals all-reimbursement-claims-for-employer --set fromDate=… --set toDate=… --set filterStatus=Pending
tankhapay-portal approvals all-travel-request-summary --set fromDt=… --set toDt=… --set statusFilter=Pending
tankhapay-portal approvals voucher-details --set fromDate=… --set toDate=…
tankhapay-portal approvals detail-meal-voucher --set monthYear=Jul-2026
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
