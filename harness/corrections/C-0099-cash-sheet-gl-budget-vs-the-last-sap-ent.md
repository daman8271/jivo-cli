---
id: C-0099
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [cash-voucher]
---

# Cash sheet GL/Budget vs the last SAP entry

## Wrong
Took Budget 'Factory' for voucher 464 (bank charges Rs 708) from the cash sheet's Budget column, although the identical Rs 708 bank-charge line on the same imprest card a month earlier carried FACT_COM.

## Right
The cash sheet's GL and Budget columns are the operator's working note, not the authority. Where they disagree with the last entry booked on that card for that account, the last SAP entry wins.

## Evidence
Daman, 2026-09-19, asked which wins for voucher 464: 'last SAP entry wins.' Precedent: OPCH 50620 dt 2026-08-04, ORGV000465, AcctCode 5610003, Rs 708.00, OcrCode3 FACT_COM.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Cash sheet's GL/Budget column vs the last SAP entry on that card for that account: the LAST SAP ENTRY WINS. Check it before keying; the sheet's column is a working note, not the authority.
