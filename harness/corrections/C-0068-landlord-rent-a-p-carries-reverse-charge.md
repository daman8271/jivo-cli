---
id: C-0068
date: 2026-09-01
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [rent]
---

# Landlord rent A/P carries reverse-charge RCGSG@18, not Exampt

## Wrong
Assumed a rent invoice showing no GST columns is tax-exempt, and would have keyed the line with TaxCode Exampt like other no-GST service bills.

## Right
JIVO rent A/P lines carry TaxCode RCGSG@18 — reverse charge on rent from an unregistered landlord. It does not inflate the document: DocTotal stays the printed rent and VatSum is 0; JIVO pays that GST to the government separately. Account 5660002 RENT, Dim3 SERVICES, Dim4/Dim5 empty, no TDS at JIVO's rent levels (194I bites at Rs 2.4 L/yr).

## Evidence
JIVO_MART posted PurchaseInvoices 8709 (BHUPENDER KAUR - RENT, 01-03-2026, Rs 20,000): line AccountCode 5660002, TaxCode RCGSG@18, CostingCode CANOLA / 03-2026 / SERVICES, CostingCode4+5 null, WTLiable tNO, WithholdingTaxDataCollection empty; header DocTotal 20000, VatSum 0. Same shape on the sibling landlords 8708 and 8701. Applied 2026-09-01 to drafts 40119/40120/40121, all read back DocTotal = printed total with VatSum 0.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Rent A/P lines: AccountCode 5660002, TaxCode RCGSG@18 (reverse charge, NOT Exampt), Dim3 SERVICES, Dim4/Dim5 empty; DocTotal = printed rent and VatSum = 0.
