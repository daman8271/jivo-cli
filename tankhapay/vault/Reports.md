---
tags: [tankhapay, section, reports]
---
# Reports — Statutory, Compliance, Liability, Salary & Tax

The reporting heart of TankhaPay and the richest read section (46 reads, mostly `Report/*` on the
business backend). It covers the **statutory ECR** filings (EPF/ESI/LWF month-wise), **compliance**
flags, **liability & disbursement** reports, **bank** advice, **salary slips & verification**,
**tax** projection/summary, **investment** declaration/proof reports, **biometric attendance**
extracts, and a **dynamic-report** builder. Almost every read takes `year`/`month` +
`customerAccountId` + `GeoFenceId` and often unit/department filters. AES-encrypted POST
([[Encryption-Scheme]]); one JWT ([[Auth-and-Access]]). 46 reads, 13 writes (all mis-tagged rows the
extractor called READ but which mutate — reclassified out).

## Read endpoints (in-scope for the CLI)

| Command (`reports …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `liability-report` | business | `year`, `month`, `individualSearch`, `contractIdSearch`, `customerAccountId`, `GeoFenceId`, `unitParameterName`, `postOffered`, `postingDepartment` | employer liability report |
| `liability-report-combined` | business | year/month + ctx | combined liability |
| `detailed-liability-report-all-employees` | business | year/month + ctx | detailed liability, all employees |
| `detailed-liability-report-by-emp-code` | business | `year`, `month`, `empCode`, `customerAccountId`, `GeoFenceId` | detailed liability for one employee |
| `disbursment-report` | business | `year`, `month`, `individualSearch`, `contractIdSearch`, `customerAccountId`, `action`, `GeoFenceId`, `unitParameterName`, `postOffered`, `postingDepartment` | disbursement report |
| `prepayout-report` | business | `year`, `month`, `customerAccountId`, `GeoFenceId`, `statusFilter`, `unitParameterName`, `postOffered`, `postingDepartment` | pre-payout report |
| `employees-pay-summary` | business | `customerAccountId`, `fromDate`, `toDate`, `GeoFenceId`, `unitParameterName`, `postOffered`, `postingDepartment` | employees pay summary |
| `fetch-bank-report` | business | `customerAccountId`, `FromDate`, `ToDate`, `individualSearch`, `contractIdSearch`, `GeoFenceId` | bank payment advice |
| `displayepfecrreport-month-wise` | business | `year`, `month`, `customerAccountId`, `ReportType`, `GeoFenceId` | EPF ECR (month-wise) |
| `displayesicecrreport-month-wise` | business | `year`, `month`, `customerAccountId`, `ReportType`, `GeoFenceId` | ESI ECR (month-wise) |
| `displaylwfecrreport-month-wise` | business | `year`, `month`, `customerAccountId`, `lwfstate`, `GeoFenceId` | LWF ECR (month-wise) |
| `compliance-flag-report-for-business` | business | `compliancesFlag`, `filterStatus`, `customerAccountId`, `orgUnitId` | compliance-flag report |
| `download-compilance-report` | business | `year`, `month`, `customerAccountId`, `userId`, `productTypeId`, `compliancesFlag`, `GeoFenceId` | compliance report (download shape) |
| `salary-slip` | business | `productTypeId`, `empCodeString`, `isPayslipAdvance` | salary slip data |
| `salary-slip-url` | business | account ctx + emp | presigned salary-slip URL |
| `salary-verification-view` | business | `customerAccountId`, `productTypeId`, `GeoFenceId`, `unitParameterName`, `postOffered`, `postingDepartment` | salary verification view |
| `tax-projection` | business | `customerAccountId`, `financial_year`, `empCode`, `GeoFenceId` | tax projection |
| `tax-summary-result` | business | ctx + financial year | tax summary |
| `investment-report-result` | business | `customerAccountId`, `financialYear`, `filterStatus`, `empCode`, `GeoFenceId` | investment report |
| `investments-proof-details` | business | `customerAccountId`, `financialYear`, `empCode`, `GeoFenceId`, `geo_location_id` | investment proof details |
| `investment-declaration-date` | business | `customerAccountId`, `financialYear`, `GeoFenceId`, `geo_location_id` | declaration window |
| `investment-declaration-date-for-employee` | business | `customerAccountId`, `financialYear`, `empCode`, `GeoFenceId` | per-employee declaration window |
| `loan-report` | business | `customerAccountId`, `productTypeId` | loan report |
| `increment-report-business` | business | `productTypeId`, `customerAccountId`, `fromDate`, `toDate`, `action`, `empCode` | increment report |
| `expense-report-business` | business | ctx + date range | expense report |
| `rembursement-report-data` | business | ctx | reimbursement report |
| `month-wise-onboarding-details` | business | ctx | month-wise onboarding |
| `ac21-report` | business | ctx | AC-21 statutory register |
| `biometric-attendance-details` | business | ctx | biometric attendance extract |
| `biometric-employee-for-business` | business | ctx | biometric-enrolled employees |
| `manage-biometric-att` | business | `action`, `customeraccountid`, `emp_org_code`, `product_type`, `from_dt`, `to_dt`, `ou_ids` | biometric attendance (read `action`) |
| `daywisecheckcheckin-report` | business | `action`, `empcode`, `month`, `year`, `customeraccountid`, `post_offered`, `posting_department`, `unitparametername`, `search_keyword` | day-wise check-in/out |
| `hourly-summary-report` | business | `action`, `accountid`, `fromDate`, `toDate`, `emp_code`, `unitParameterName`, `postOffered`, `postingDepartment` | hourly summary |
| `tp-check-in-out-summary` | business | `fromDate`, `toDate`, `customerAccountId`, `productTypeId`, `flag`, `GeoFenceId`, `checkInOutMarkedType` | check-in/out summary |
| `tp-check-in-out-report-by-repo-manager` | business | ctx | check-in/out by reporting manager |
| `active-financial-years-to-close` | business | `customerAccountId` | FYs eligible to close |
| `dynamic-report-list` | business | ctx | saved dynamic reports |
| `dynamic-report-master` | business | `actionType`, `reportType` | dynamic-report master |
| `dynamic-report-filters` | business | `sourceDataType` | dynamic-report filters |
| `dynamic-report-data` | business | ctx + report id | dynamic-report rows |
| `report-fields` | business | `reportName`, `productTypeId`, `customerAccountId` | report field list |
| `master-dropdown` | business | `actionType`, `productTypeId`, `customerAccountId` | report dropdown master |
| `manage-report-columns-wfm` | business | `action`, `report_name`, `accountid`, `report_description`, `report_column_text`, `productTypeId` | report columns (read `action`) |
| `manage-audit-report-wfm` | business | `p_action`, `p_account_id`, `p_from_dt`, `p_to_dt` | audit report (WFM, `p_` params) |
| `pdf-btye-code` / `pdf-btye-code-portrait` | business | report id/params | render a report to PDF bytes (`Report/getPdfBtyeCode[Portrait]`) |

### Account context
`customerAccountId`/`customeraccountid`/`accountid`/`p_account_id` = **2719**; `GeoFenceId` /
`geo_location_id` = **37**; `productTypeId` from JWT. The rest are real report parameters —
`year`/`month` (or `fromDate`/`toDate`, note the mixed casing and the `p_` variants), `financialYear`
(`2025-2026`), `empCode`, `compliancesFlag`, `ReportType`, `statusFilter`, and the unit/department
multi-select filters (`unitParameterName`, `postOffered`, `postingDepartment`, `orgUnitId`) — supply
via `--set`.

## Write endpoints (documented, OUT OF SCOPE)

All 13 are rows the extractor mis-tagged READ but which mutate — reclassified and never wired
([[Read-Only-Guardrails]]):

```
Report/{CloseFinancialYear, SaveInvestmentDeclarationDate, SaveInvestmentDeclarationDateForIndividualEmp,
        SubmitBiometricForBusiness, SubmitBiometricForBusiness_bulk, SubmitEsicForBusiness, SubmitUanForBusiness,
        VerifyInvestmentProofDetails, deleteLiabilityReportApi, disburseLiability, reprocess_today_checkinout,
        sendSalaryPdf}, report/saveDynamicReport
```
`VerifyInvestmentProofDetails` is the Approve/Reject action on employee investment proofs;
`disburseLiability`/`sendSalaryPdf`/`reprocess_today_checkinout` all have real side effects.

## CLI command mapping

```
tankhapay-portal reports liability-report --set year=2026 --set month=7
tankhapay-portal reports displayepfecrreport-month-wise --set year=2026 --set month=7 --set ReportType=…
tankhapay-portal reports employees-pay-summary --set fromDate=… --set toDate=…
tankhapay-portal reports salary-slip --set empCodeString=…
tankhapay-portal reports tax-projection --set financial_year=2025-2026 --set empCode=…
tankhapay-portal reports compliance-flag-report-for-business --set compliancesFlag=… --set filterStatus=…
```
Add `--set GeoFenceId=@geo` on the many endpoints that key off `GeoFenceId`.

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
