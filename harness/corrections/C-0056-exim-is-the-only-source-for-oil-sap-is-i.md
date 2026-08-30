---
id: C-0056
date: 2026-08-30
author: Daman
area: all
severity: high
status: active
supersedes: C-0051
tags: [stock]
---

# EXIM is the ONLY source for oil — SAP is incomplete, not merely different

## Wrong
Recorded EXIM as the preferred source for oil while still describing SAP's raw-material balances as a parallel view of the same stock. That leaves the door open to using SAP as a fallback when EXIM is unreachable, or to reconciling the two.

## Right
Daman, 2026-08-30: 'Only trust EXIM. Some things are in EXIM which are not in SAP.' SAP does not hold a partial or lagging copy of the oil position - it is MISSING items outright, so it can never be a fallback and there is nothing to reconcile. Verified: EXIM's tank master carries grades that have no SAP item at all, including POMACE 2B, CANOLA 2B, EXTRA LIGHT 2B, GROUNDNUT 2B, EXTRA VIRGIN 2B, COCONUT OIL 2B and SESAME 2 - a search of every SAP raw-material item returns no '2B' code. If EXIM is down, the answer is 'I cannot see the oil', never a number from SAP.

## Evidence
Live 2026-08-30. EXIM 'exim tank get-item-wise-summary' returns 20 tank oils incl. RM00P02 POMACE 2B, RM00CN2 CANOLA 2B, RM0EL02 EXTRA LIGHT 2B, RMGNR02 GROUNDNUT 2B, RM0EV02 EXTRA VIRGIN 2B, RM00CCNT2B COCONUT OIL 2B, 'RM00SESM 2' SESAME 2. SAP: SELECT ItemCode,ItemName FROM JIVO_OIL_HANADB.OITM JOIN OITB WHERE ItmsGrpNam='RAW MATERIAL' AND ItemName LIKE '%2B%' returns ZERO rows. Totals also disagree: EXIM tanks 904,300 L vs SAP BH-LO 675,471 L. Ruling by Daman 2026-08-30, strengthening C-0051.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
EXIM is the ONLY source for oil quantity, tanks and grades. SAP is MISSING oil items entirely (no 2B grades exist there) - it is never a fallback and never a cross-check. EXIM down = say so, do not quote SAP.
