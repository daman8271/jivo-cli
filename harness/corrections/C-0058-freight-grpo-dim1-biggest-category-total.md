---
id: C-0058
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: C-0048
tags: [grpo]
---

# Freight GRPO Dim1: biggest category TOTAL, not the biggest single row

## Wrong
Dim1 (Variety) on a freight GRPO line = the single Product Category row with the most litres (C-0048).

## Right
Sum the Litre column PER CATEGORY in the sale invoice's Product Category block, then take the category with the biggest total. Rows of the same category at different pack sizes are ADDED, not kept separate. On invoice 626070718: CANOLA 2,000 + 800 = 2,800 beats SUNFLOWER 2,000 and OLIVE 700 + 800 = 1,500, so Dim1 = CANOLA. The old row-wise reading ties CANOLA and SUNFLOWER at 2,000 and picks wrong.

## Evidence
Daman 2026-08-31, on Oil AR invoice 626070718 (Product Category block: CANOLA 2,000 / OLIVE 700 / OLIVE 800 / CANOLA 800 / SUNFLOWER 2,000, Total 6,300). Keyed into draft 55594 line 0 as CostingCode=CANOLA. This closes GRPO-Playbook open question 1a.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO Dim1: sum the Litre column per category in the invoice's Product Category block and take the biggest TOTAL; same category at two pack sizes is added, never treated as separate rows.
