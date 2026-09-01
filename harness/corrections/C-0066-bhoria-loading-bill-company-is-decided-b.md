---
id: C-0066
date: 2026-09-01
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [loading-bills]
---

# BHORIA loading bill company is decided by product, not letterhead

## Wrong
Keyed the water FG loading bill (48634, 01-14 Aug) into JIVO_OIL because the bill is addressed to JIVO WELLNESS (P) LIMITED with the Oil GSTIN — same header as the oil loading bill.

## Right
Water loading bills go to JIVO_BEVERAGES, oil loading bills to JIVO_OIL, even though BHORIA addresses every bill to JIVO WELLNESS (P) LIMITED / GSTIN 06AACCJ4223F1Z0. Bev has its own parallel fortnightly BHORIA trail: same CardCode VENDA000281, same account 5670002, but Dim1 WATER and TDS code 1230 (vs Oil Dim1 CANOLA, TDS 1023).

## Evidence
JIVO_BEVERAGES PurchaseInvoices CardCode VENDA000281: DocEntry 13670 (64229, 03-08-26, line Dim1 WATER, WT 1230), 13368 (44219), 13092 (43937) — fortnightly water-loading trail; Oil's parallel trail (49636/49170) is all oil loading, Dim1 CANOLA, WT 1023. Water bill 48634 re-keyed as Bev draft 15816 on 2026-09-01 after Daman's correction.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
BHORIA loading bills (VENDA000281, letterhead always JIVO WELLNESS): key by PRODUCT loaded — water → Beverages (Dim1 WATER, TDS 1230), oil → Oil (Dim1 CANOLA, TDS 1023).
