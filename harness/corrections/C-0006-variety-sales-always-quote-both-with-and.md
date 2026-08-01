---
id: C-0006
date: 2026-08-01
author: daman
area: sales
severity: high
status: active
supersedes: C-0004
tags: [variety, bom]
---

# Variety sales: always quote both with and without combo packs

## Wrong
Picked one treatment of combo packs and reported a single variety figure — sometimes counting a mixed pack wholly as olive, sometimes dropping it entirely — so the same question returned different totals on different days with no visible reason. In one conversation the olive figure moved between four values because the treatment changed silently mid-thread.

## Right
Daman's ruling 2026-08-01: give BOTH numbers, every time. Report the variety total INCLUDING combo packs and the total EXCLUDING them, label which is which, and let the reader choose. Never silently pick one, and never present a single number as the answer.

## Evidence
Combo SKUs carry one U_Sub_Group tag for a mixed pack (66 olive-tagged SALES BOM items in Oil, e.g. SL0000013 'EXTRA LIGHT 5 LTR + CANOLA 5 LTR'), so neither treatment is wrong and the split cannot be computed at line level. Live June-2026 olive via hana_sales_by_variety: Mart external Rs 9,53,17,126 of which combo packs Rs 59,00,087 (ex-combo Rs 8,94,17,039); Oil external Rs 3,64,46,055 with Rs 0 combo.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Variety sales (olive/canola/mustard...): ALWAYS quote both — including combo packs and excluding them — labelled. hana_sales_by_variety returns OF_WHICH_COMBO_PACKS; subtract it for the ex-combo figure. Never quote just one.
