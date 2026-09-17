---
id: C-0095
date: 2026-09-17
author: Daman (with Mahak)
area: accounts
severity: high
status: active
supersedes: C-0060
tags: [grpo]
---

# Freight GRPO litres come from the tax invoice only

## Wrong
Litres were taken from one source only: Oil read the printed PDF total (and on CSD invoices with no printed total the AI multiplied by the '16 PCS' in the item name - 15 lines, e.g. 626090164 keyed 192 L for 12 bottles); Mart and Beverages were calculated from item names with no cross-check.

## Right
Litres come from the TAX INVOICE only, in all three books: the Total of the Litre column printed on the invoice (take page 2's Total when the table runs over). An invoice that prints no litre table (CSD / institutional) is calculated = quantity x bottle size, quantity being bottles, never x the 'N PCS' carton size ('1 LTR 16 PCS' x 2 = 2 L). An invoice with only cartons/caps gets no GRPO. The dispatch sheet is not a litre source.

## Evidence
Mahak (USER19 GRPO desk) via Daman 2026-09-17: printed total yes; CSD has none -> calculate; '1 LTR 16 PCS' qty 2 = 2 L; cartons-only -> no GRPO; page 2 total; Mart/Bev: Mahak used the dispatch sheet but it is 'sometimes wrong'; Daman ruled 17 Sept: invoices only, drop the dispatch sheet as a litre source. Reader checked on real PDFs: Oil 4 tables + 8 CSD with none, Mart 9 (= posted litres of GRPO 2009264540 exactly), Bev 4. HANA: 15 USER19 Oil draft lines 3-16 Sep had litres = qty x size x PCS (drafts 56002/56003/56004/56011/56013 posted as 2026086913-919; 56658/57123/57244/57245/57246 still drafts). Calculation vs hand-keyed Jun-Aug: Mart 153/168 (91%), Bev 694/782 (89%), Oil 398/692 (58%; +20% not calculable: GMS pouches, KG tins). Bundles: Mart sums both halves (33/35), Oil sums only COMBO (135/188). Enforced in .claude/skills/jivo-oil-freight-grpo/bin/freight_checks.py (all three builders).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO litres: the Litre Total printed on the tax invoice (page 2's if it runs over); no litre table (CSD) = qty x bottle size, never x 'N PCS'. Never the dispatch sheet.
