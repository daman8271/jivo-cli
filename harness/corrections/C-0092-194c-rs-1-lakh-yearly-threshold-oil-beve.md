---
id: C-0092
date: 2026-09-12
author: Divjot 2026-09-12
area: accounts
severity: high
status: active
supersedes: 
tags: [tds, 194c, ap-draft]
---

# 194C Rs 1 lakh yearly threshold: Oil + Beverages count together, Mart counts alone

## Wrong
Treated the 194C Rs 1,00,000-a-year aggregate as ambiguous between per-company-book and per-PAN-across-all-three-books, and took ap-cont's table at face value where it says Mart carries no TDS at all (WTSum 0, WTLiable tNO).

## Right
The Rs 1,00,000 yearly aggregate is counted per DEDUCTOR, and JIVO has two: Oil and Beverages are one legal entity (JIVO WELLNESS (P) LIMITED, GSTIN 06AACCJ4223F1Z0) so their purchases from one PAN are TOTALLED TOGETHER, and JIVO MART PVT LTD stands alone with its own count from zero. The Rs 30,000 single-bill test stays per bill in whichever book it lands. Mart DOES deduct: WTCode 1023 at 1 percent, same code as Oil.

## Evidence
Divjot 2026-09-12 asked directly: 'WE TOTAL BVG + OIL COMBINED AND MART IS SEPARATE.' Measured live the same day, FY26-27 (DocDate ge 2026-04-01, Cancelled tNO). PRABHAKAR SHUKLA PAN MNNPS2203M: Oil VENDA001564 Rs 27,28,428 gross / Rs 27,284 TDS (1% on every bill incl. the Rs 27,300 one, card ThresholdOverlook tYES); Bev VENDA001252 Rs 2,64,189 / Rs 2,643; Mart VENDA001034 nil posted but draft 40210 Rs 42,250 carries WTCode 1023 Rs 423 (approved 2026-09-10) while draft 40297 Rs 44,850 carries WTData [] - the Mart-deducts-nothing reading is what produced that miss. NAHIM PAN DPYPA3165J: Oil VENDA001714 Rs 2,21,500, first bill Rs 12,500 (13-Jun) TDS 0, second Rs 1,13,500 (01-Jul) TDS Rs 1,135 - Oil counted alone crossed Rs 1L there; Mart VENDA001035 nil and card SubjectToWithholdingTax boNO, so its Rs 20,500 Aug bill (draft 40446) correctly takes no TDS under the separate-Mart count. PAN sweep over 5,203 supplier cards (Oil 2,247 / Mart 1,250 / Bev 1,706): exactly one card per PAN per book, no hidden duplicates.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
194C Rs 1L/yr aggregate: total Oil + Beverages TOGETHER (one entity, JIVO WELLNESS) and JIVO MART separately from zero. Rs 30,000 test is per bill. Mart deducts too, WTCode 1023 at 1%.
