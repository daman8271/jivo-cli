---
id: C-0022
date: 2026-08-21
author: Daman (accounts-dashboard build)
area: accounts
severity: medium
status: active
supersedes: 
tags: [grpo]
---

# C-0017 is a posting rule, not a safe assumption when reading GRPO history

## Wrong
Treated C-0017 (A/P invoice DocDate = gate-in date = the GRPO's DocDate) as a property of the data, and inferred a receipt date from an A/P invoice's posting date when reading history.

## Right
C-0017 remains correct as the rule for how to POST a new A/P invoice. It is not a description of what is already in the books. Measured live 2026-08-21 by matching every A/P invoice to its base GRPO via PCH1.BaseEntry/BaseLine: the invoice DocDate equals the GRPO DocDate on only 51.47% of Oil pairs (5,266 of 10,232), 84.22% of Mart and 21.23% of Beverages. Average lag in Oil is 14.1 days, median 0. The practice is tightening in Oil and Mart (Oil by month 2025 ~48%, 2026-06 57.6%, 2026-07 77.0%) but Beverages runs at 9-19% and does not follow it. 28 Oil pairs (0.3%) even carry an invoice dated BEFORE its GRPO. Beware recency bias in the newest months: only 23.1% of Oil's Aug-26 GRPOs are invoiced yet, so recent percentages are computed on the fast-billed minority and 2026-06 is the last trustworthy month. TaxDate behaves as documented: against the GRPO DocDate it is equal 3,109 / before 3,102 / after 4,031, consistent with it carrying the vendor's own invoice date.

## Evidence
Join OPCH to PCH1 to OPDN on PCH1.BaseType=20 and BaseEntry/BaseLine, both sides CANCELED='N' (see C-0021), then compare OPCH.DocDate to OPDN.DocDate. 2026-08-21: Oil 5266/10232 same-day = 51.47%, avg lag 14.1d, median 0; Mart 84.22%; Bev 21.23%.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
C-0017 is how to POST, not what the books contain: A/P DocDate equals its GRPO DocDate on only 51% of Oil pairs, 84% Mart, 21% Bev. Never infer a gate-in date from an existing A/P invoice.
