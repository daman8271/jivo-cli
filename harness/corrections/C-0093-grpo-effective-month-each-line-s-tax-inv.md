---
id: C-0093
date: 2026-09-17
author: Daman (with Mahak)
area: accounts
severity: high
status: active
supersedes: C-0045
tags: [grpo]
---

# GRPO effective month = each line's TAX INVOICE month, never the bilty

## Wrong
Freight GRPO Dim2 was taken from the bilty/dispatch date: the Oil freight skill, GRPO-Playbook and Transport-Bill-Playbook said so, and the Oil and Mart build scripts stamped ONE hand-typed month on every line of a bill. C-0045 read the month off the bilty paper. Tanker (bulk oil) GRPOs left Dim2 blank.

## Right
On EVERY GRPO, Effective Month (CostingCode2, MM-YYYY) = the month of that line's TAX INVOICE date. Freight GRPO: the JIVO sale invoice on the line (U_ARNO), decided per line, so one bilty can carry two months. Tanker / goods GRPO: the supplier's tax invoice date (TaxDate). Posting date and document date stay on the bill / bilty. The printed Invoice Date equals OINV.DocDate.

## Evidence
Ruled by Daman with Mahak (USER19 GRPO desk), 2026-09-17. HANA 2026-09-17: freight GRPO lines (PDN1 AcctCode 5670001, posted without a draft, Jun-Aug 2026) where U_BiltyDate month <> OINV.DocDate month of U_ARNO: keyed invoice month 223, bilty month 19 (Oil 64/6, Mart 51/7, Bev 108/6). USER19 drafts 25 Aug-16 Sep (ODRF ObjType 20 DocType S): 103 lines used the bilty month (Oil 59, Mart 38, Bev 6), 53 of those GRPOs already posted with Dim2 unchanged. Printed 'Invoice Date' = OINV.DocDate on 25/25 PDFs pulled from mail (Oil 12, Mart 9, Bev 4).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Every GRPO: Dim2 (Effective Month) = MM-YYYY of EACH LINE's tax invoice date - freight: the sale invoice in U_ARNO; tanker/goods: supplier's TaxDate. Never the bilty date.
