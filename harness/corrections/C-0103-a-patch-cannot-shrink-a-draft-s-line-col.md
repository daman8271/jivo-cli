---
id: C-0103
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [sap-api]
---

# A PATCH cannot shrink a draft's line collection

## Wrong
Tried to remove one line from draft 57460 by PATCHing the full shorter DocumentLines array; SAP kept the extra line and shifted the amounts onto it, taking the document from Rs 9,351 to Rs 10,051.

## Right
SAP merges DocumentLines by LineNum on a PATCH. Lines can be ADDED this way (including GRPO copies - BaseType/BaseEntry/BaseLine do link), but a line can never be removed, and a shorter array silently duplicates money. Adding lines takes a second identical PATCH to populate the amounts, and UnitPrice must never be sent on a service line - it makes SAP recompute LineTotal.

## Evidence
2026-09-19 on Drafts(57460): 8-line array sent three times, document stayed at 9 lines and DocTotal 10,051 with PriceBefDi shifted across lines. Sending UnitPrice on a service line drove LineTotal 983 -> 463.8777. Adding a GRPO line to Drafts(57456) worked: BaseType 20 / BaseEntry 26730 / BaseLine 0 linked, DocTotal 5,700.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
PATCHing a draft: you can ADD DocumentLines (GRPO copies link fine) but NEVER remove one - a shorter array leaves the extra line and duplicates money. Re-send the same PATCH to settle amounts. Never send UnitPrice on a service line.
