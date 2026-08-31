---
id: C-0060
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# U_UNE_LTS is the printed Total of the Litre column — never computed, never Gross Wt

## Wrong
Litres for a freight GRPO line can be worked out from the invoice lines (pack size x pieces), or read off the bilty's weight.

## Right
Read the 'Total' figure in the Litre column of the sale invoice PDF's Product Category block and key that. Do not compute it and do not take Gross Wt (that is packaging-inclusive: 6,300 L ships as 6,257.83 kg). The invoice PDFs live in the logistics@jivo.in mailbox; find one by the invoice number the bilty gives you.

## Evidence
Daman 2026-08-31. Cross-checked on 12 invoices of ABHIMAN bill DEL/260349: printed Total equals the sum of the category rows on all 12, and category-row count equals litre-row count on all 12. Computing from INV1 pack sizes reproduces the keyed value on only 67% of Oil freight lines (GRPO-Playbook fallback measurement, 2026-08-27).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO U_UNE_LTS = the printed Total of the Litre column in the sale invoice's Product Category block. Never the Gross Wt column, never computed from pack sizes.
