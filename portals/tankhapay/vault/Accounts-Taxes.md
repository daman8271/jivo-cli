---
tags: [tankhapay, section, accounts-taxes]
---
# Accounts, Taxes & Investment Proof

The money-and-tax corner of the TankhaPay Business portal. It does two related jobs for an HR/payroll
admin. **(1) Accounts** — the employer's *prepaid wallet* with TankhaPay: current balance, the ledger of
top-ups and salary-payout debits, and the proforma invoice behind each transaction (routes `accounts`,
`account-twenty-one`). **(2) Taxes & Investment Proof** — the annual income-tax cycle for the 593
employees: which regime (old/new) each employee has locked in, their investment *declarations*, the
*proofs* (80C, Chapter VI-A, HRA/rent receipts, home-loan interest) they upload for the payroll team to
approve or reject, previous-employer income, and the quarterly/annual **TDS report** used for 24Q filing
(routes `Investment-Declaration`, `Proof-of-Investment`, `view-declaration`,
`declaration-submitted-report`, `tds`, `tds-report`, `income-tax-calculator`, `tax-summary-report`).
Everything below is extracted from the production bundle (`main.7309d5d32824e620.js` + lazy chunks,
captured 2026-07-25); every call is an AES-encrypted POST — see [[Encryption-Scheme]].

> Endpoint constants live in bundle module `4245`; the service wrappers are `EmployeeManagementService`
> (`chunk-6618`), `ReportService` (`main.js`), `AccountService` (module `36744`, `chunk-8710`/`chunk-6987`)
> and `BusinesSettingsService` (`main.js`, module `88646`). Call sites are in `chunk-4656` (proof /
> tax-projection screens), `chunk-7402` (TDS proof-verify screen), `chunk-6987` (declaration-submitted +
> TDS reports) and `chunk-8710` (accounts/wallet page).

## Read endpoints (in-scope for the CLI)

Backend column: **business** = `https://business.tankhapay.com/api/`, **mobapi** =
`https://mobapi.tankhapay.com/api/` (one JWT authorizes both — see [[Auth-and-Access]]).

| Endpoint (path) | Backend | Request payload keys | Returns | Notes |
|---|---|---|---|---|
| `account/getCustomerLedgerSummary` | business | `productTypeId`, `customerAccountId` | object with `balance` — the employer's prepaid wallet balance (₹) | **Simplest read in the section.** Both values are **plaintext** here (`customerAccountId = tp_account_id` = `2719`; `productTypeId` from `localStorage.product_type`). Response is `JSON.parse(aesDecrypt(commonData))`. Called on `ngOnInit` of the accounts page. |
| `account/employer_latest_transaction` | business | `customeraccountid` *(AES-encrypted, note the all-lowercase key)*, `transaction_flag:"Latest"`, `status:"Paid"`, `transactiontype`, `tranmonth:""`, `datefrom`, `dateto`, `productTypeId` | `{data:[…]}` — wallet transaction rows: `trantime`, `operationtype`, `entrytype`, `status` (`Paid`/`Pending`/`Failed`/`Success`), `netamount`, `payment_method`, `transactionids` | Response is `JSON.parse(aesDecrypt(commonData)).data` — the array is nested under `data`, unlike most reads. `transactiontype` is the UI filter (`"All"` by default); `datefrom`/`dateto` are `DD/MM/YYYY` strings. |
| `get_tds_report_data` | business | `financialYear` (`"2025-2026"`), `reportType` (`Monthly`\|`Quarterly`\|`Annually`), `period` (month `1–12`, quarter `1–4`, or `"0"` when Annually), `customerAccountId` | employee TDS rows: `orgempcode`/`tpcode`, `emp_name`, `pancard`, `department`, `designation`, `orgunitname`, `grossearning`, `taxdeducted`, `tds_section` | All four values **plaintext**. `JSON.parse(aesDecrypt(commonData))`. Quarters are fiscal (Q1 = Apr–Jun). Financial years are generated client-side from 2020 upward. |
| `TpTaxesApi/GetCustomerWiseEmployeeRegimeDetails` | business | `customerAccountId` *(AES)*, `productTypeId` *(AES)*, `action:"Q1CEqHhXvK8wQNxoQ4DSszdyIuBhqSTFkc2cJ+oWPtQ="`, `unitParameterName`, `financialYear`, `postOffered`, `postingDepartment`, `regimeType` | declaration-submission rows: `emp_name`, `orgempcode`, `cjcode`, `regime_tye` *(sic)*, `posting_department`, `createdon` | Exposed as `ReportService.getDeclarationSubmittedReport` → the **Declaration Submitted Report** page. That `action` blob is itself AES-ECB ciphertext: it decrypts (same key `0123456789abcdef`) to the literal **`GetRegimeDetails`** — a neat confirmation of [[Encryption-Scheme]]. `unitParameterName` / `postingDepartment` / `postOffered` are comma-joined multi-select values (unit ids, `posting_department`, `post_offered`); send all of them, or `""`, for "no filter". `regimeType` is `""` for both. |
| `TpInvestmentProofApi/GetViewInvestmentsProof` | business | `customerAccountId`, `financialYear`, `empCode`, `GeoFenceId`, `headId`, `investmentId` (`"-9999"` when none) | uploaded-proof rows: `headtype`, `status` (`pending`/`Accepted`/`Rejected`), `documentpath`, `receipt_amount`, `receipt_number`, `interest_amount`, `is_fianncialyearcompleted` *(sic)*, `landlord_name`, `landlord_pan`, `landlord_address`, `landlord_city`, `landlord_state`, `lender_name`, `lender_pannumber1–4`, `loan_amount`, `loan_holder_name`, `loan_holder_type`, `loan_no`, `loan_sanction_date`, `loan_type`, `is_firsttymebuyer`, `isbefore01apr1999`, `name_of_owner`, `principal_amount`, `property_value`, `remarks` | **All params plaintext**, including `empCode` (the bare employee code — *not* the `CJHUB` composite used by the mobapi tax reads). `GeoFenceId` = `geo_location_id` from the JWT (`37`). **Gotcha:** the component consumes `resp.commonData` **directly** (`this.Inv_data = n.commonData`) with **no** `aesDecrypt` — this response's `commonData` is a plain array, not a ciphertext blob. Guard for both. `documentpath` may be a URL or a `data:` URI. |
| `TpTaxesApi/GetEmpRegimeAndTaxProjection` | mobapi | `empCode` *(AES of `<mobile>CJHUB<emp_code>CJHUB<dateofbirth>`)*, `financialYear`, `customerAccountId` *(AES)*, `productTypeId` *(AES)* | `{regimeDetails:{regimetype, declaration_or_proof, declarationmessage, final_submit_date}}` | The regime/declaration-window status for one employee. `declarationmessage` carries the open/close window as two `DD/MM/YYYY` dates, which the UI parses to decide whether declaration or proof entry is open. `JSON.parse(aesDecrypt(commonData))`. |
| `TpTaxesApi/GetHomeLoanDetails` | mobapi | `empCode` *(AES of the `CJHUB` composite)*, `financialYear`, `customerAccountId` *(AES)*, `productTypeId` *(AES)* | home-loan declaration: `loan_amount`, `loan_sanction_date`, `property_value`, `homeAddress`, `lender_name`, `is_firsttymebuyer`, `principal_on_borrowed_capital`, `interest_on_borrowed_capital`, `isbefore01apr1999`, `lender_pannumber1–4` | `JSON.parse(aesDecrypt(commonData))`; returns a single object (or nothing when the employee has no home-loan declaration). |
| `TpTaxesApi/getEmpRentDetails` | mobapi | `empCode` *(AES of the `CJHUB` composite)*, `financialYear`, `customerAccountId` *(AES)*, `productTypeId` *(AES)* | month-wise HRA/rent rows: `rent_year`, `rent_month`, `is_metro`, `rentpaid`, `landlordname`, `landlordpancard`, `address`, `no_of_child_under_cea`, `no_of_child_under_cha` | `JSON.parse(aesDecrypt(commonData))`. One row per month of the financial year. |

### Account context these reads need
- `customerAccountId` / `customeraccountid` = **`tp_account_id` = `2719`**, from the decoded JWT `data` blob ([[Auth-and-Access]]).
- `GeoFenceId` = **`geo_location_id` = `37`**, same source. Only `GetViewInvestmentsProof` uses it in this section.
- `productTypeId` — read from `localStorage.product_type` in the SPA; it is also present in the JWT context. Encrypt it for the `TpTaxesApi` reads, send plaintext for `getCustomerLedgerSummary` / `employer_latest_transaction`.
- `ouIds` (`"37,2211,38,40,31,1925"`) is **not** used by this section; the declaration report filters by `unitParameterName` (unit ids from `GetGeoFencing` / master dropdowns) instead.
- Everything else is a real parameter the caller must supply: `financialYear` (`"2025-2026"`), `empCode`, date ranges, `reportType`/`period`, `headId`/`investmentId`.

### Two encryption conventions in one section — do not mix them
The `business` **account/report** reads take **plaintext** ids. The `mobapi` **TpTaxesApi** reads take the
same ids **AES-ECB-encrypted with the body key** (i.e. double-encrypted: field-level AES *inside* the
already-AES-encrypted `{"encrypted": …}` envelope). `GetViewInvestmentsProof` is plaintext despite being a
`TpInvestmentProofApi` path. Get this wrong and the API returns an empty/zero result rather than an error.

### The `CJHUB` employee key
The `TpTaxesApi` per-employee reads do **not** take a bare employee code. They take
`aesEncrypt(mobile + "CJHUB" + emp_code + "CJHUB" + dateofbirth)`. The CLI must therefore resolve an
employee's `mobile` and `dateofbirth` (from [[Employee-Management]] reads) before it can call them.

### Sibling reads that live in other sections
The tax screens also call, via `ReportService`: `Report/GetInvestmentsProofDetails` (all proofs for an
employee — same response shape and same *undecrypted* `commonData` quirk as `GetViewInvestmentsProof`),
`Report/GetTaxProjectionApi` (`taxByMonth`, `taxprojection`, `totalincome`, `totalsaving`,
`chaptersixcomp`, `us80ccomp`, `flexiAllowances`), `Report/TaxSummaryResultApi`,
`Report/InvestmentReportResultApi` and `Report/GetInvestmentDeclarationDate`. Those are documented in
[[Reports]]; the `account/*` wallet siblings `getPayoutTransactionsDetails` and
`CustomerTransactionsApi/getFundAddedTransactionsDetails` are in [[Payouts]].

## Write endpoints (documented, OUT OF SCOPE)

Never wired into the CLI — see [[Read-Only-Guardrails]]. These touch live payroll and real money.

| Endpoint | What it does |
|---|---|
| `business · TpTaxesApi/SaveEmpRegime` | Locks an employee's tax regime (old/new) for a financial year. Payload includes `finalSubmit:"Y"` — irreversible for the employee. |
| `business · TpTaxesApi/SaveEmpInvestmentDeclaration` | Saves an employee's declared investment amount for one head (`investmentDetail` JSON array + `parentSeniorCitizen` / `disabilityMoreThan80` / `employeeWithSevereDisability` flags). |
| `business · TpTaxesApi/SavePreviousIncomeDetail` | Records previous-employer income for the FY (`grossEarning`, `basic`, `hra`, `tds`, `pf`, `vpf`, `insurance`). Feeds the TDS computation. |
| `business · TpInvestmentProofApi/Save80cComponents` | Uploads an 80C proof document (`documentBase64`, `receiptNumber`, `receiptDate`, `receiptAmount`). |
| `business · TpInvestmentProofApi/saveCH6ProofDetails` | Same, for Chapter VI-A heads (80D/80DD/80U …). |
| `business · TpInvestmentProofApi/saveHraProof` | Uploads an HRA/rent proof (`tenureId`, `fromDate`/`toDate`, `rentAmount`, `landLordName`/`landLordAddress`/`landLordPan`, `documentBase64`). |
| `business · TpInvestmentProofApi/saveHomeLoanDetails` | Uploads a home-loan interest/principal proof with lender PANs and property details. |
| `business · TpInvestmentProofApi/editProofDetails` | Edits the accepted receipt amount on an already-uploaded proof (the TDS team's "Edit Amount" popup). Confirmed a write from its `saveReceiptAmountDetails()` call site. |
| `business · account/PaymentPerformaInvoice` | Proforma invoice for a wallet transaction (`transaction_id`, `transaction_flag`, `status`) → `invoiceno`, `pinumber`, GST breakup, `netamountreceived`. **Ambiguous:** the call site only *reads* the invoice for display, but the name implies invoice generation and it trips the `pay`/`generate` verb denylist. Held out of scope deliberately rather than guessed. |
| `business · refresh_account_details` | **Reclassified READ → WRITE.** Really `BusinesSettingsService.RefreshMaterializedViewByApi({action})` — it forces a **server-side materialized-view refresh** (`action` ∈ `"tpay-business-account"`, `"tpay-business-account-tds"`, `"users-refresh"`). Fired right after compliance / payout-setting saves. A side-effecting maintenance call on shared infrastructure, not a data read. |
| `business · redis/deleteAllCacheKeysForAccount` | Flushes every Redis cache key for `customerAccountId`. Destructive to shared cache state. |
| `mobapi · TpTaxesApi/SaveEmpInvestment` | Saves an employee investment entry (mobile/self-service path). |
| `mobapi · TpTaxesApi/SaveEmpRentDetails` | Saves the month-wise rent array (`rentDetail` JSON: `rent_year`, `rent_month`, `is_metro`, `rentpaid`, `landlordname`, `landlordpancard`, `address`). |
| `mobapi · TpTaxesApi/SaveHomeLoan` | Saves the home-loan declaration read back by `GetHomeLoanDetails`. |

Also out of scope and reachable from these screens (owned by [[Reports]]):
`Report/VerifyInvestmentProofDetails` — the **Approve/Reject** action on an employee's uploaded proofs.
Nothing in the CLI may ever reach it.

## CLI command mapping

```
tankhapay-portal accounts summary                        # account/getCustomerLedgerSummary  — wallet balance
tankhapay-portal accounts transactions --from --to \
                                       --type All        # account/employer_latest_transaction
tankhapay-portal taxes tds-report --fy 2025-2026 \
        --report-type Quarterly --period 1               # get_tds_report_data
tankhapay-portal taxes declarations --fy 2025-2026 \
        [--units …] [--departments …] [--designations …] \
        [--regime …]                                     # TpTaxesApi/GetCustomerWiseEmployeeRegimeDetails
tankhapay-portal taxes proofs --emp-code … --fy … \
        [--head-id …] [--investment-id …]                # TpInvestmentProofApi/GetViewInvestmentsProof
tankhapay-portal taxes regime --emp-code … --fy …        # TpTaxesApi/GetEmpRegimeAndTaxProjection  (mobapi)
tankhapay-portal taxes home-loan --emp-code … --fy …     # TpTaxesApi/GetHomeLoanDetails            (mobapi)
tankhapay-portal taxes rent --emp-code … --fy …          # TpTaxesApi/getEmpRentDetails             (mobapi)
```

`--emp-code` on the three `mobapi` commands takes the plain employee code; the CLI resolves
`mobile`/`dateofbirth` and builds the encrypted `CJHUB` composite itself. `accountId`, `geo_location_id`
and `productTypeId` are always filled from the cached JWT context, never asked for.

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Sibling sections: [[Reports]] · [[Payouts]] · [[Employee-Management]] · [[Masters-Config]] · [[Dashboard]] · [[Approvals]] · [[Attendance]] · [[Leave-Management]] · [[Org-User-Management]] · [[Recruit-ATS]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
