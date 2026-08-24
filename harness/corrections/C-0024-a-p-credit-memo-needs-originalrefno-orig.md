---
id: C-0024
date: 2026-08-24
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [sap-writes]
---

# A/P Credit Memo needs OriginalRefNo + OriginalRefDate from the CN paper

## Wrong
Built an A/P credit memo draft with totals/base links correct but left OriginalRefNo/OriginalRefDate null

## Right
The vendor CN's printed 'Original Invoice No. & Date' box maps to Drafts.OriginalRefNo (full number as printed, e.g. RPL/1164/2026-27) and OriginalRefDate — the Tax-section fields; every posted JIVO A/P CN carries them

## Evidence
query PurchaseCreditNotes CardCode VENDA000517 top 5: all carry OriginalRefNo RPL/NNNN/YYYY-YY + OriginalRefDate; draft 55128 patched 2026-08-24, corrected by Daman

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P credit-memo drafts: always set OriginalRefNo (original invoice no. exactly as printed on the CN) and OriginalRefDate — SAP silently accepts null but Accounts/GST require them.
