---
id: C-0084
date: 2026-09-04
author: Mahak
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# CSD invoices print no Litre block and their Quantity is in CASES

## Wrong
Assumed every AR invoice carries the Product Category / Litre block that C-0060 says to read, and that INV1.Quantity is in pieces (C-0001). On CSD invoices parse_invoices.py returns 'no Product Category block found' and reading Quantity as pieces undercounts litres ~16x.

## Right
Sales to CUSTA000636 THE AREA MANAGER CANTEEN STORE DEPARTMENT print on a different template with no Product Category block and no Litre column, and OINV.U_UNE_TOTL is 0 there too. On those invoices INV1.Quantity is CASES, not pieces. Litres = cases x pcs-per-case x bottle size, where pcs-per-case comes from the item name ('... 1 LTR 20 PCS (CSD)') or, when the name omits it, the printed PKM/SLED column - OITM.SalPackUn is unmaintained and reads 20 for a 4-pack. Category is OITM.U_Sub_Group, which is where REFINED OIL resolves to CANOLA.

## Evidence
Method reproduces six already-keyed GRPO litre values exactly: 626080259=16, 626080269=56, 626080271=32, 626080272=909, 626080225=1064, 626080282=912. OITM.SalPackUn is wrong on FG0000399 (says 20, is 4) and FG0000397 (says 12, is 24). REFINED OIL FG0000013/16/20 all carry U_Sub_Group='CANOLA' and 20 L per case.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
CSD invoices (CUSTA000636) have no Litre block and INV1.Quantity is CASES, not pieces: litres = cases x pcs/case (item name, else the printed PKM column) x bottle size. Dim1 from OITM.U_Sub_Group.
