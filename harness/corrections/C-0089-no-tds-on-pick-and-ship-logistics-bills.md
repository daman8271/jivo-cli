---
id: C-0089
date: 2026-09-10
author: Daman 2026-09-02 (recorded on Divjot's box; recovered to main 2026-09-10)
area: accounts
severity: high
status: active
supersedes: 
tags: [tds]
---

# No TDS on Pick and Ship Logistics bills

## Wrong
Pick and Ship Logistics is TDS-liable, so A/P invoice lines get WTLiable tYES - taken from the vendor master (SubjectToWithholdingTax boYES, WTCode 1024) and from the posted precedent, which is tYES in all three books.

## Right
JIVO does not deduct TDS on Pick and Ship Logistics bills until further instructions (Daman, 2026-09-02). Set WTLiable tNO on every line and let SAP deduct nothing, even though the master flag and the recent precedent both say tYES. This is a standing policy decision, not a threshold question - it is not about 194Q/194C limits. Applies to all three books: Oil VENDA001661, Mart VENDA001018, Beverages VENDA001346 (one legal party, PAN AAQCP4145A). It does NOT extend to PICKALL (VENDA000854, PAN AMRPJ9382P, WTCode 1023) or PICKNPACK SOLUTIONS (PAN AAMCP7214N) - different parties despite similar names.

## Evidence
Policy asserted by Daman 2026-09-02 - not derivable from data. SAP state it overrides, read 2026-09-02: all three cards SubjectToWithholdingTax=boYES with WTCode 1024; last posted A/P invoices book WTLiable tYES (Oil 626084200 NCR-329, Mart 708264107 NCR-333, Bev 626089411 NCR-326) and Beverages shows live deductions under code 1024 (626079468 NCR-294 Rs 7 on Rs 394; 626079466 NCR-282 Rs 6 on Rs 328). Query: BusinessPartners contains(CardName,'PICK') + PurchaseInvoices by CardCode, all three company DBs. RECOVERED 2026-09-10 from Divjot's box, where it was recorded on 2026-09-02 and never reached main - an operator checkout has a read-only deploy key, so it sat there for 8 days.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Pick and Ship Logistics (PAN AAQCP4145A: Oil VENDA001661, Mart VENDA001018, Bev VENDA001346): book WTLiable tNO, no TDS, despite master WTCode 1024 and tYES precedent - Daman, until further notice.
