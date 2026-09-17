---
id: C-0045
date: 2026-08-27
author: measured 2026-08-27, reconciling C-0038 (Daman)
area: accounts
severity: high
status: superseded
supersedes: C-0042
tags: [grpo]
---

# Freight GRPO Dim2 is the Invoice DT printed on the bilty

## Wrong
C-0042 said Dim2 = the month of the sale invoice found via U_ARNO, which implied querying SAP's AR invoice to set it — the exact thing C-0038 forbids. The GRPO playbook meanwhile said Dim2 = the bilty's own date.

## Right
Both were off. The bilty prints its own 'Invoice DT' alongside the Invoice No., so the month is read off the paper with no SAP lookup — C-0038 is satisfied. Measured on 407 Oil freight lines carrying both a bilty date and a reachable invoice: Dim2 equals the INVOICE month on 389 (95.6%) but the BILTY's own date month on only 318 (78.1%). They diverge when a truck loads just after a month end — GRPO 25886 has bilty date 2026-08-03 yet Dim2 07-2026, because its invoice was dated 2026-07-31. So use the Invoice DT field on the bilty, not the bilty date, and never query OINV.

## Evidence
SELECT SUM(CASE WHEN L."OcrCode2"=TO_VARCHAR(L."U_BiltyDate",'MM-YYYY') THEN 1 ELSE 0 END) DIM2_EQ_BILTY, SUM(CASE WHEN L."OcrCode2"=TO_VARCHAR(I."DocDate",'MM-YYYY') THEN 1 ELSE 0 END) DIM2_EQ_INVOICE, COUNT(*) FROM "JIVO_OIL_HANADB"."PDN1" L JOIN "JIVO_OIL_HANADB"."OPDN" H ON H."DocEntry"=L."DocEntry" JOIN "JIVO_OIL_HANADB"."OINV" I ON TO_VARCHAR(I."DocNum")=L."U_ARNO" WHERE H."CANCELED"='N' AND H."DocType"='S' AND L."AcctCode"='5670001' AND L."U_BiltyDate" IS NOT NULL AND L."OcrCode2"<>'';  -- 318 / 389 / 407.  (The OINV join is the AUDIT, not the entry method.)

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO Dim2 = the month of the 'Invoice DT' PRINTED ON THE BILTY (389/407 lines), not the bilty's own date (318/407). Read it off the paper — never query the AR invoice (C-0038).
