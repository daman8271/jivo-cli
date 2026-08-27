---
id: C-0048
date: 2026-08-27
author: Daman / Gurcharan
area: accounts
severity: high
status: active
supersedes: C-0046
tags: [grpo]
---

# Freight GRPO: pick the biggest single PRODUCT by litres, and split the money litre-wise

## Wrong
Derived the variety on a freight GRPO line as 'the oil type with the most litres on the invoice, adding up all lines of that oil'. On invoice 626080289 that gives OLIVE (5-LTR 400 L + 1-LTR 320 L = 720 L), so the keyed SOYABEAN (600 L) was written up as an operator exception.

## Right
Confirmed by the transport desk 2026-08-27, direct from Gurcharan: (1) when one invoice carries several products, the variety is the SINGLE PRODUCT with the maximum litres — not the oil type summed across pack sizes. SOYABEAN 600 L is the largest single product on 626080289, which is why GRPO 26081 line 3 is SOYABEAN even though olive totals 720 L across two rows. (2) The bilty's total freight is divided across the invoice lines LITRE-WISE, in proportion to each invoice's litres — verified on 1,120 of 1,253 multi-line Oil freight GRPOs (89.4%) with every line within the rounding tolerance; round to whole rupees and let the LAST line absorb the difference so the document ties to the bilty exactly. Still open, and it only bites when one oil appears twice at different pack sizes: whether those two rows are added or kept separate.

## Evidence
Stated by Daman 2026-08-27 relaying the transport desk (USER19 GURCHARAN, 3,298 of 3,887 Oil freight GRPOs). Worked example: AR invoice 626080289 Product Category block prints OLIVE 400 / OLIVE 320 / CANOLA 300 / SOYABEAN 600, Total 1620; GRPO 26081 line 3 keyed SOYABEAN. Litre-wise split re-measured on Price vs U_UNE_LTS across 1,253 multi-line Oil freight GRPOs (AcctCode 5670001, CANCELED='N'): 84.9% every line within Rs 1, 89.4% within rounding tolerance. 26081: 5320/3220 = Rs 1.65217/L -> 1652.17/991.30/2676.52 keyed 1652/991/2677.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO variety = the single PRODUCT with the most litres on that invoice (NOT the oil type summed across pack sizes). Split the bilty's freight across invoices litre-wise; last line takes the rounding.
