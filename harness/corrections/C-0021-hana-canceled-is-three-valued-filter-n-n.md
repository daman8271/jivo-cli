---
id: C-0021
date: 2026-08-21
author: Daman (accounts-dashboard build)
area: all
severity: high
status: active
supersedes: 
tags: [cancelled]
---

# HANA CANCELED is three-valued — filter ='N', never <>'Y'

## Wrong
Excluded cancelled documents in HANA SQL by writing "CANCELED" <> 'Y' (or omitting the filter), assuming the flag is a two-valued Y/N.

## Right
In the HANA tables the flag has THREE values: 'N' = live, 'Y' = the cancelled original, and 'C' = the system-generated cancellation mirror SAP posts to reverse it. Y and C always appear as exact matching pairs carrying the same value, so a <>'Y' test keeps every mirror and double-counts. Measured live on Oil 2026-08-21: OINV 30,387 'N' (1045.62 Cr) plus 320 'Y' and 320 'C' at 37.27 Cr each; OPCH 16,101 'N' plus 113+113 at 15.96 Cr each; OPDN 10,640 'N' plus 473+473 at 94.63 Cr each; ORDN 1,817 'N' plus 107+107 at 0.49 Cr each. Same pattern in Mart and Beverages. Always test CANCELED='N' positively. Note the Service Layer differs: it exposes only Cancelled 'tYES'/'tNO', so the documented OData filter Cancelled eq 'tNO' is already correct and is not affected.

## Evidence
SELECT "CANCELED", COUNT(*), SUM(CAST("DocTotal" AS DOUBLE)) FROM JIVO_OIL_HANADB.OPDN GROUP BY "CANCELED" -- 2026-08-21 returns N 10640/784.64Cr, Y 473/94.63Cr, C 473/94.63Cr. Repeat for OINV, OPCH, ORDN, ORPD, ORIN, ORPC.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
HANA "CANCELED" is three-valued: 'N' live, 'Y' cancelled original, 'C' its system mirror. Always filter CANCELED='N' - a <>'Y' test keeps the mirrors and double-counts (Oil OPDN +94.63 Cr).
