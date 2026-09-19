---
id: C-0097
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [cash-voucher]
---

# Cash voucher: one A/P per PO, even across months

## Wrong
Split PO 220826165 into two A/P drafts because voucher 468's slip was 31-08 and 466's was 09-09, citing the 'never span a month' rule; same again on PO 220826164.

## Right
A cash-voucher A/P groups by PO, not by month. One entry per PO (the Rs 10,000 cap is the only thing that forces a second one). The document's posting/document date is the LATEST voucher date in the entry, and only the effective month (Dim2) varies line by line, taken from each voucher's own date.

## Evidence
Daman, 2026-09-19, on bunch 45939: '472 they should perform 1 entry only' and '468 and 466 should be 1 entry only'; 'while entering cash vouchers only the effective month is changed as on the voucher, the document date is the recent date from all of the vouchers'. Live: drafts 57462 (472 Aug + 473/475 Sep) and 57456 (468 Aug + 466 Sep).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Cash-voucher A/P: ONE entry per PO even if its vouchers fall in different months - DocDate = latest voucher date, Dim2 per line = that voucher's own month. Only the Rs 10,000 cap splits a PO.
