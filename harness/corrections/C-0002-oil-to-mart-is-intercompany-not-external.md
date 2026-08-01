---
id: C-0002
date: 2026-07-30
author: daman
area: all
severity: high
status: superseded
supersedes: 
tags: [intercompany]
---

# Oil to Mart is intercompany, not external sale

## Wrong
Added JIVO Oil and JIVO Mart turnover together to get a group figure.

## Right
Mart is Oil's single biggest customer, so the sum double-counts a stock transfer. May 2026: Rs18.12 Cr of Oil's Rs40.10 Cr turnover was billed to Mart.

## Evidence
May 2026: Rs18.12 Cr of Oil's Rs40.10 Cr turnover billed to CUSTA000606. Mart's books also carry JIVO MART branch cards (DL/PB/HR/KT/KR/RJ/UP) and a JIVO WELLNESS PVT LTD card needing the same treatment.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
JIVO Mart (CardCode CUSTA000606) is Oil's biggest customer — Oil+Mart double-counts the stock transfer. Report external (excluding CUSTA000606) alongside gross, and say which one you quoted.
