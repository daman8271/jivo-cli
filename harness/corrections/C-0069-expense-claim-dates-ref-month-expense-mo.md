---
id: C-0069
date: 2026-09-02
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [expense-claims]
---

# Expense-claim dates: ref month = expense month, posting = 1st of NEXT month, document date = the expense date

## Wrong
Dated employee expense claims by the APPROVER's sign-off date — put DocDate = TaxDate = 31-08-2026 and built NumAtCard as 'AUG 26/8890' for a claim whose only expense was a Bullet service on 27-07-2026.

## Right
The expense drives all three fields, never the approval signature. Vendor ref (NumAtCard) = '<EXPENSE MONTH> YY/<total>'. Document date (TaxDate) = the expense date on the paper (the last one when a sheet spans days). Posting date (DocDate) = the 1st of the month AFTER the expense month, which also selects that month's numbering series. So a 27-07-2026 expense is 'JUL 26/8890', document date 27-07-2026, posting date 01-08-2026.

## Evidence
Daman, 2026-09-01, correcting draft 55799. Confirmed in the books: JIVO_OIL posted A/P ORGV000029/ORGV000033 — 'MAY 26/14551' DocDate 2026-06-01 TaxDate 2026-05-31; 'APR 26/22663' and 'APR 26/28176' both DocDate 2026-05-01; 'JUN 26/33885/32451' DocDate 2026-08-01 TaxDate 2026-07-09. Applied to drafts 55798/55799/55800/55804/55805 and read back. Oil BPL-1 series: Jul-26 3335, Aug-26 3336, Sep-26 3337 (3337 accepted a 2026-09-01 DocDate, 3338 refused with [SAP -10] 10000521).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Employee expense claims: NumAtCard = '<EXPENSE MONTH> YY/<total>', TaxDate = the expense date on the paper, DocDate = the 1st of the following month (and pick that month's series). Never date them by the approver's signature.
