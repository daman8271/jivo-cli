---
id: C-0013
date: 2026-08-12
author: Karanpreet Singh (GST manager), via Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [gst]
---

# HSN blank is not a defect - service lines carry SAC instead

## Wrong
Reported '157 invoice lines carry no HSN code, Rs 4.94 Cr, these lines cannot be reported correctly in GSTR-1' and printed it into a PDF prepared for a chartered accountant. The check looked only at INV1.HsnEntry, saw blanks, and called them defects.

## Right
HsnEntry and SacEntry are mutually exclusive on INV1: goods lines carry an HSN code and no SAC, service lines carry a SAC and no HSN. A blank HsnEntry on a service line is correct GST treatment, not a defect. Verified live on Oil from 1 Nov 2025: 19,735 lines HSN-only (Rs 351.52 Cr), 154 lines SAC-only (Rs 3.86 Cr), ZERO lines with both, and only 3 lines (Rs 1.07 Cr) with neither. The real defect population is 3 lines, not 157.

## Evidence
SELECT CASE WHEN IFNULL(L."HsnEntry",0)>0 AND IFNULL(L."SacEntry",0)>0 THEN 'BOTH' WHEN IFNULL(L."HsnEntry",0)>0 THEN 'HSN only' WHEN IFNULL(L."SacEntry",0)>0 THEN 'SAC only' ELSE 'NEITHER' END AS BUCKET, COUNT(*), ROUND(SUM(L."LineTotal")/10000000,2) FROM "JIVO_OIL_HANADB"."INV1" L JOIN "JIVO_OIL_HANADB"."OINV" H ON H."DocEntry"=L."DocEntry" WHERE H."CANCELED"='N' AND H."DocDate">='2025-11-01' GROUP BY 1 -- returns HSN only 19735/351.52Cr, SAC only 154/3.86Cr, NEITHER 3/1.07Cr, BOTH no rows

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
INV1: HsnEntry and SacEntry are mutually exclusive - goods carry HSN, services carry SAC. A blank HsnEntry is only a defect if SacEntry is also empty. Never flag missing HSN without checking SAC.
