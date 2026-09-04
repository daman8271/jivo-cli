---
id: C-0079
date: 2026-09-04
author: Mahak
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# Freight GRPO lines carry a SAC code, and the API field is SACEntry

## Wrong
Built 40 freight GRPO drafts leaving the line SAC empty, then tried to fix it by patching SacEntry (the HANA column name). The Service Layer returned HTTP 204 on all 40 patches and silently ignored the property; DRF1.SacEntry stayed NULL.

## Right
Every JIVO freight GRPO line carries a SAC code, and it differs per book: Oil SACEntry 40 (OSAC 9965 FREIGHT, in use by all vendors since 2026-08-20, superseding entry 2 / 9967), Beverages SACEntry 3 (996812 freight, 242 of 242 lines since 1 Aug), Mart SACEntry -426 (00997136). The Service Layer property is SACEntry in capitals; SacEntry is only the HANA column and is dropped without error.

## Evidence
SELECT T1."SacEntry",COUNT(*) FROM OPDN T0 JOIN PDN1 T1 ON T0."DocEntry"=T1."DocEntry" WHERE T0."DocType"='S' AND T0."DocDate">='2026-08-20' GROUP BY T1."SacEntry" -> Oil 40 only (13 lines, 4 vendors); same over Bev since 1 Aug -> 3 only (242 lines). Field name from GET PurchaseDeliveryNotes(26395): DocumentLines[0].SACEntry = 40. Patching 'SacEntry' returned 204 x40 with no change; 'SACEntry' applied immediately.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO lines need SACEntry: Oil 40 (9965), Bev 3 (996812), Mart -426 (00997136). The API field is SACEntry, not SacEntry - a 204 does not mean it applied, so read DRF1.SacEntry back.
