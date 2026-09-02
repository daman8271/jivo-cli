---
tags: [tankhapay, section, recruit-ats]
---
# Recruitment / ATS — Candidates, Offer Letters & Flexi-salary

TankhaPay's applicant-tracking side: **candidates**, **offer-letter templates**, and the
candidate-facing **flexi-salary / salary-slip** reads used when onboarding. The extractor could only
positively classify **3** endpoints as reads; most of the ATS surface (`recruit/all*`) came back
**UNKNOWN** (see below) and the payout-style `Consultant/*` and `Customer*` endpoints are writes.
Routes: `TpCandidateAPI/*`, `recruit/*`, `Consultant/*`. AES-encrypted POST ([[Encryption-Scheme]]).

## Read endpoints (in-scope for the CLI)

| Command (`recruit …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `tp-flexi-salary` | mobapi | `empCode`, `customerAccountId`, `month`, `year`, `productTypeId` | candidate flexi-salary breakdown |
| `tp-voucher-details` | business | `customerAccountId`, `productTypeId` | candidate voucher details |
| `salary-slip-url` | mobapi | `productTypeId`, `empCodeString` | presigned salary-slip URL(s) (`TpCandidateAPI/GetSalarySlipURL`) |

### Account context
`customerAccountId` = **2719**, `productTypeId` from JWT; `empCode`/`empCodeString`, `month`, `year`
via `--set`.

## Candidate/template reads classified UNKNOWN (not wired — see [[Read-Only-Guardrails]])

The extractor could not confirm READ vs WRITE for these from the call sites, so — per the
fail-closed policy — they are **not** wired. They are almost certainly reads (candidate/template
listings) and are the natural next batch to promote if a live capture confirms them:

```
recruit/{allCandidates, allTemplates, allTemplateType, allTemplateFields, allTemplateFieldName,
         letterTEmplateById, candidateActions, offerLetterActions, templateActions, mapTPCode}
TpCandidateAPI/CalcTpFlexiSalaryComponents
```

## Write endpoints (documented, OUT OF SCOPE)

```
Consultant/{ConsultantPayout, AddEditConsultantPayoutDetails, DeleteConsultantPayoutRecord, GetConsultantPayoutDetails}
TpCandidateAPI/{CustomerPayoutDetails, CustomerPayoutSummary, SaveTpFlexiSalaryComponents, sendCustumFCM}
recruit/saveEmailJson
```
(`Consultant/GetConsultantPayoutDetails` and `TpCandidateAPI/CustomerPayout*` read like reads but the
extractor flagged them WRITE/side-effecting — held out deliberately rather than guessed.)

## CLI command mapping

```
tankhapay-portal recruit tp-flexi-salary --set empCode=… --set month=7 --set year=2026
tankhapay-portal recruit salary-slip-url --set empCodeString=…
tankhapay-portal recruit tp-voucher-details
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Masters-Config]] · [[Org-User-Management]] · [[Broadcast-Visitor-Help]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
