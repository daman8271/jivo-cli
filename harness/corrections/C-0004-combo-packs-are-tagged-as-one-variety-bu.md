---
id: C-0004
date: 2026-08-01
author: daman
area: sales
severity: medium
status: superseded
supersedes: 
tags: [variety, bom]
---

# Combo packs are tagged as one variety but contain several

## Wrong
Summed variety sales straight off OITM.U_Sub_Group, which credits a combo pack's entire value to one variety — e.g. SL0000013 'EXTRA LIGHT 5 LTR + CANOLA 5 LTR' and FG0000079 'EXTRA LIGHT OLIVE 1 LTR + MUSTARD KACHI GHANI 1 LTR' are both tagged OLIVE, so canola and mustard revenue lands in the olive line.

## Right
U_Sub_Group is still the right field (never name-match), but a combo SKU carries ONE tag for a mixed pack and cannot be split at line level. Report combo packs as a separate line, or state that they are counted whole in the tagged variety.

## Evidence
Oil OITM where U_Sub_Group='OLIVE': 106 FINISHED, 66 SALES BOM, 10 RAW MATERIAL, 3 SEMI FINISHED (HANA, 2026-07-31). Combos confirmed tagged OLIVE: SL0000013, SL0000014, SL0000025, SL0000039, SL0000056, SL0000131, FG0000079. Latent, not yet biting: June-2026 olive revenue was 100% FINISHED (Rs 11.55 Cr), SALES BOM contributed Rs 0.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Variety totals from OITM.U_Sub_Group over-credit combo packs: 66 olive-tagged SKUs are ItmsGrpNam='SALES BOM' bundling olive with canola/mustard. Split SALES BOM out, or say it is counted whole.
