---
id: C-0042
date: 2026-08-27
author: measured 2026-08-27 (Daman GRPO session)
area: accounts
severity: high
status: superseded
supersedes: 
tags: [grpo]
---

# Freight GRPO Dim2 is the sale invoice's month

## Wrong
Assumed Dim2 (Effective Month) on a freight GRPO follows the GRPO's own posting date or the bilty date.

## Right
On a freight/service GRPO, Dim2 (CostingCode2 / OcrCode2) is the month of JIVO's OWN SALE INVOICE — the one named in the line's U_ARNO. Measured on 205 Oil PICK & SHIP lines: Dim2 equals the sale invoice's month on 193, and where the sale month and the GRPO month disagree Dim2 follows the sale invoice every time. Proof case: GRPO 25886 is dated 2026-08-03 but carries Dim2 07-2026, because its sale invoice 626070769 is dated 2026-07-31.

## Evidence
SELECT L."OcrCode2" DIM2, TO_VARCHAR(I."DocDate",'MM-YYYY') SALE_MONTH, TO_VARCHAR(H."DocDate",'MM-YYYY') GRPO_MONTH, COUNT(*) FROM "JIVO_OIL_HANADB"."PDN1" L JOIN "JIVO_OIL_HANADB"."OPDN" H ON H."DocEntry"=L."DocEntry" LEFT JOIN "JIVO_OIL_HANADB"."OINV" I ON TO_VARCHAR(I."DocNum")=L."U_ARNO" WHERE H."CANCELED"='N' AND H."DocType"='S' AND H."CardCode"='VENDA001661' GROUP BY 1,2,3 ORDER BY 4 DESC;  -- DIM2=SALE_MONTH on 193 of 205, incl. 11 rows where GRPO_MONTH differs

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
On a freight/service GRPO, Dim2 (Effective Month) = the month of JIVO's own sale invoice in U_ARNO, not the GRPO's or the bilty's month — 193 of 205 lines; where they disagree Dim2 follows the invoice.
