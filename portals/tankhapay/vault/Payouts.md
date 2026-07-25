---
tags: [tankhapay, section, payouts]
---
# Payouts — Salary, Allowances, Imprest & Piece-rate

The money-out side of TankhaPay: how salary and allowances are computed, funded and disbursed, plus
the specialised payout tracks — **imprest** (petty-cash advances), **piece-rate** (per-unit
production pay), **allowance/bonus rules**, and **reimbursement claims**. This section is almost
entirely **writes** (33 of 44) because paying people is the whole point — the reads here only *view*
transactions, rules, eligibility and product masters. Routes: `payout(Api)/*`, `payrolling/*`,
`allowanceBonus/*`, `imprest/*`, `piece/*`, `ReimbursementClaims/*`. AES-encrypted POST
([[Encryption-Scheme]]); one JWT ([[Auth-and-Access]]).

> ⚠️ This section touches **real salary and real money**. Every `pay*`, `save*`, `bulk*`,
> `manual_transfer`, `paysalary`, `Disburse*` call is out of scope and never wired
> ([[Read-Only-Guardrails]]).

## Read endpoints (in-scope for the CLI)

| Command (`payouts …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `payout-transactions-details` | business | `customerAccountId`, `transactionId`, `productTypeId` | wallet/payout transaction detail |
| `all-reimbursement-claims` | tpPay | account ctx | all reimbursement claims (`ReimbursementClaims/GetAllReimbursementClaims`) |
| `allowance-bonus-rule-list` | business | account ctx | configured allowance/bonus rules |
| `eligible-employees` | business | account ctx + rule filter | employees eligible for an allowance/bonus |
| `employee-piece-report` | business | account ctx, `month`, `year` | piece-rate production/pay report |
| `piecerate-employees` | business | `actionType`, `customerAccountId` | employees on piece-rate |
| `product-details` | business | account ctx | piece-rate product master |
| `manage-master-products` | business | `action` (read), account ctx | piece-rate product listing (read `action`) |
| `imprest-master` | business | account ctx | imprest (advance) master config |
| `imprest-applications-filter` | business | account ctx + filters | imprest applications (filtered) |
| `ir-appl-by-account` | business | account ctx | imprest applications by account |

### Account context
`customerAccountId` = **2719**, `productTypeId` from the JWT. `transactionId`, `month`/`year`,
rule/product ids and imprest filters are supplied via `--set`. The wallet **balance/ledger** reads
(`account/getCustomerLedgerSummary`, `account/employer_latest_transaction`) live in [[Accounts-Taxes]].

## Write endpoints (documented, OUT OF SCOPE)

```
salary/payout : payoutApi/{paysalary, bulkPayout, manual_transfer, UpdateSalaryStatus, save_receivables,
    GenerateRequiredAmountPI, CalcReciebaleFromBaseAmount, GetVpaDetails, GetPaymentModeTypes,
    getStartingPaymentSubscription, get_employer_montly_subscription}, payout/{getMultiPayout, saveMultiPayout},
    hdfcPaymentStatus, CustomerTransactionsApi/getFundAddedTransactionsDetails
payroll setup : payrolling/{bulkIncrement, saveBulkSalaryStructure, saveBulkPreparedSalary,
    getSmartSalaryManagement, getSmartpayrollCandidates, fetchSmartSetupCandidates}
allowance/bonus: allowanceBonus/{SaveBonusVoucher, generateBonusVouchers, getAllowanceBonusAssignments},
    DearnessAllowance/SaveDearnessAllowanceData
imprest       : imprest/{approve_reject_application, approve_reject_application_by_id}
piece-rate    : piece/{createSalaryFromEarnings, saveEmployeeItemCreated, deleteEmployeeProduct, deleteProducts}
reimbursement : ReimbursementClaims/{AddEditReimbursementClaim, DeleteReimbursementClaim}, updateProductType
```
UNKNOWN (not wired): `ReimbursementClaims/ManageReimbursementClaim`, `TPSalaryBusiness/TaxCalculator`,
`allowanceBonus/manageAllowanceBonusRule`, `imprest/manage_imprest_applications`.

## CLI command mapping

```
tankhapay-portal payouts payout-transactions-details --set transactionId=…
tankhapay-portal payouts employee-piece-report --set month=7 --set year=2026
tankhapay-portal payouts imprest-applications-filter
tankhapay-portal payouts allowance-bonus-rule-list
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
