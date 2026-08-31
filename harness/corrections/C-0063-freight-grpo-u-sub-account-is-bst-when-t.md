---
id: C-0063
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# Freight GRPO U_Sub_Account is BST when the sale invoice is JIVO-to-JIVO

## Wrong
U_Sub_Account on a freight GRPO line is always SALES.

## Right
It is SALES only when the goods went to an outside customer. When JIVO raised the sale invoice AND the customer on it is JIVO WELLNESS or JIVO MART, the line's U_Sub_Account is BST. Decide it per LINE off that line's U_ARNO invoice, not per document — one bilty can carry both. Oil customer cards that take BST: CUSTA000001/2/3/4 (JIVO WELLNESS -DL/-HR/-PB/-HP), CUSTA001099 (WELLNESS DL ISD), CUSTA000606 + CUSTA000827 + CUSTA001113 (JIVO MART). Beverages uses the same codes; Mart's book uses CUSTA000001 and CUSTA000827/874/875/876/877/878/926.

## Evidence
Daman 2026-08-31. In Oil, 121 of 122 BST freight lines are billed to a JIVO card (CUSTA000003 x89, CUSTA000001 x26, CUSTA000002 x3, VENDA000003 x3); a BST invoice bills the JIVO branch and ships onward to a third party (626010780 -> CUSTA000003, ShipTo SAI DORAHA). Past keying is inconsistent and the SALES ones on JIVO cards are wrong: CUSTA000003 has 416 SALES vs 89 BST, and JIVO MART CUSTA000606 has 204 SALES and 0 BST — Daman confirmed Mart counts as BST.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO: U_Sub_Account = BST when the line's sale invoice is billed to JIVO WELLNESS or JIVO MART; SALES for any outside customer. Decide per line from U_ARNO, never per document.
