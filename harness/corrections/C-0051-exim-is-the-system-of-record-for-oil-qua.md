---
id: C-0051
date: 2026-08-29
author: Daman
area: all
severity: high
status: superseded
supersedes: 
tags: [units, stock]
---

# EXIM is the system of record for oil quantities, never SAP

## Wrong
Treated SAP's BH-LO / BH-PC / BH-GJ raw-material balances as the truth for how much loose oil JIVO holds, and presented the EXIM-vs-SAP gap as an open question to be resolved later.

## Right
EXIM is the record for oil. Daman's ruling 2026-08-29: 'we need to listen to exim in terms of oil always.' Bulk oil quantity, tank capacity and tank utilisation come from EXIM tank monitoring (exim.jivo.in/stock/tank-monitoring). SAP's raw-material warehouse balances are book stock and disagree materially. The two cannot be reconciled: they share no item code at all — EXIM uses RM00CN / RM0MKG / RM00POM, SAP uses RM0000001-RM0000066, with zero overlap. Never net one against the other or use SAP to 'check' an EXIM figure.

## Evidence
Live 2026-08-29: 'exim/exim tank get-summary --agent' = 904,300 L in 1,351,500 L of tank capacity across 32 tanks. SAP 'SELECT WhsCode,ItemCode,OnHand FROM JIVO_OIL_HANADB.OITW JOIN OITM/OITB WHERE ItmsGrpNam=RAW MATERIAL' = BH-LO 675,471 L (EXIM +33.9%), BH-LO+BH-PC+BH-GJ 966,789 L (EXIM -6.5%). Item-code intersection between the two sets is empty; e.g. SAP RM0000066 PEANUT OIL 230,875 L in BH-LO vs EXIM groundnut 55,000 L in tanks. Ruling by Daman 2026-08-29.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Oil quantity, tank capacity and utilisation ALWAYS come from EXIM (exim/exim tank get-summary), never SAP. EXIM and SAP share no oil item code - never net or cross-check them.
