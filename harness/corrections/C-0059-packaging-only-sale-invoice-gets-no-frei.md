---
id: C-0059
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# Packaging-only sale invoice gets no freight GRPO line

## Wrong
Every sale invoice listed against a bilty gets a line on the freight GRPO.

## Right
An invoice whose Product Category block contains ONLY non-oil categories (TIN, CAPS, CARTON) is NOT entered on the freight GRPO at all. If the invoice carries any oil alongside the packaging, it IS entered, packaging rows and all — e.g. 626080101 (CANOLA 290 + TIN 0 + CAPS 0) is keyed, because the oil is what the freight is being paid for.

## Evidence
Daman 2026-08-31. Verified against history: of 3,218 distinct U_ARNO invoices on Oil freight GRPO lines (AcctCode 5670001, CANCELED='N', 365 days), 0 are packaging-only (no INV1 item with a non-empty OITM.U_Variety). Applied on bill DEL/260349 -> drafts 55594-55598.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO: skip a sale invoice whose Product Category block is only TIN/CAPS/CARTON; enter it if it has ANY oil, packaging rows included. Packaging rows are 0 litres so they never change U_UNE_LTS or Dim1.
