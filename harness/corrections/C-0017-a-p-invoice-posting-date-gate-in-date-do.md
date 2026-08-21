---
id: C-0017
date: 2026-08-21
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [ap-invoice]
---

# A/P invoice posting date = gate-in date, doc date = vendor invoice date

## Wrong
Assumed an A/P invoice could be posted on today's date or on the vendor's invoice date.

## Right
JIVO posts an A/P invoice on the gate-in date: DocDate = the date on the JIVO gate stamp, which is also the GRPO's DocDate. TaxDate (document date) carries the vendor's invoice date. Due date then follows the vendor's payment terms from there.

## Evidence
Daman, 2026-08-21: 'posting date should be the gate in date'. Verified on Oil: every Aug-26 Frystal/SSY A/P invoice has DocDate equal to its base GRPO's DocDate and TaxDate equal to the vendor invoice date, e.g. PurchaseInvoices 48986 DocDate 2026-08-01 = PurchaseDeliveryNotes 25326 DocDate, TaxDate 2026-07-31 = NINV/26-27/0792 date; draft 54906 DocDate 2026-08-08 (gate 08-Aug) TaxDate 2026-08-07. Query: sapb1 query PurchaseInvoices --filter "CardCode eq 'VENDA000601' and DocDate ge '2026-08-01'" --select DocEntry,DocDate,TaxDate,NumAtCard

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P invoice DocDate (posting) = gate-in date = the GRPO's DocDate; TaxDate = vendor's invoice date. Never post on today's date or on the vendor's date.
