---
id: C-0081
date: 2026-09-04
author: Mahak
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# One bilty can carry both Oil and Beverages invoices - it becomes two GRPOs

## Wrong
Treated a transporter's bilty as belonging to one company book, so the whole bilty's freight was going onto one GRPO.

## Right
A single bilty can carry sale invoices from two books at once - the LR reads 'CARTON OIL AND WATER'. Beverages is (BEVERAGE UNIT) JIVO WELLNESS PVT LTD, the same legal entity as Oil in a separate company DB, so one bill made out to JIVO WELLNESS legitimately covers both. Pro-rate that bilty's whole freight on litres across EVERY invoice on it, then key the Oil lines as an Oil GRPO and the Bev line as its own Beverages GRPO. Sum of the Oil drafts is then short of the bill footer by exactly the Bev share. Beverages constants differ: PICK and SHIP is VENDA001346 (not VENDA001661), SalesPersonCode 52 (not 115), ItemDescription and Dim1 are DRINKS or WATER.

## Evidence
Reproduced to the rupee on three posted mixed bilties: NCR-4073 Oil 11355 + Bev 132 over 981 L and 11.4 L; NCR-3992 Oil 18107 + Bev 188; NCR-3997 Oil 12484 + Bev 189. Invoice location check: SELECT DocNum FROM <db>.OINV WHERE DocNum IN (...) run over all three books shows the split.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A bilty can carry Oil AND Beverages invoices ('CARTON OIL AND WATER'): pro-rate its freight on litres across all its invoices, then key one GRPO per book - Bev under VENDA001346, SlpCode 52, Dim1 WATER/DRINKS.
