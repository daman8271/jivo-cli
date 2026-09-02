---
id: C-0073
date: 2026-09-02
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [lookup, multi-company]
---

# Never say 'not found' after searching one company — search all three, then say what you searched

## Wrong
After looking up a GRPO (or invoice, draft, vendor, PO) in Oil only, the AI told the operator 'GRPO not found'. The operator reads that as SAP being broken or their paper being wrong, when the document simply lives in Mart or Beverages.

## Right
SAP is three separate books (Oil, Mart, Beverages) and a document exists in exactly one of them. Open GRPOs on 2026-09-02: Oil 405, Mart 33, Beverages 314 — an Oil-only search misses 347 of 752 (46%). A lookup is not finished until all three companies have been checked. If it is still missing, say exactly what was searched ('checked Oil, Mart and Beverages by bilty no. X, none has it') and offer the next step (search by vendor / date / amount), so the operator knows it is the paper or the keying, not the tool.

## Evidence
sapb1 query PurchaseDeliveryNotes --count --filter "DocumentStatus eq 'bost_Open'" --company <each>: Oil 405 / Mart 33 / Beverages 314 (2026-09-02). Companion facts: C-0030 (company comes off the paper), C-0061 (a bilty's invoice may live in another book), C-0031 (a login error is per-company too).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Never say 'not found' for a GRPO/invoice/draft/PO/vendor until ALL THREE companies (Oil, Mart, Beverages) are searched; then state exactly what was searched and offer a next step — never leave the operator thinking SAP or their paper is broken.
