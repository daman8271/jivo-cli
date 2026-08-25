---
id: C-0030
date: 2026-08-25
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [company]
---

# The paper names the company; no name means Oil

## Wrong
Treated the company as ambiguous and asked which SAP company an entry belonged to, or defaulted to Oil without reading the marking printed on the PO/bill.

## Right
JIVO's own POs and bills carry the company on their face — PO 826228022 prints 'ONLY FOR BEVERAGES' in the header and carries CardCode VENDA001062, which exists only in JIVO_BEVERAGES_HANADB (Oil's CHANCHAL CHEMICALS TRADING is a different code, VENDA001306). When the paper carries no such marking, the entry is Oil.

## Evidence
sapb1 query PurchaseOrders --company JIVO_BEVERAGES_HANADB --filter "DocNum eq 826228022" -> DocEntry 4075, CardCode VENDA001062, DocTotal 24780, BPLID 2. Same vendor name in Oil is VENDA001306 (CurrentAccountBalance 0); Mart has no such vendor. PDF header: 'ONLY FOR BEVERAGES', GSTIN 06AACCJ4223F1Z0.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Read the company off the PO/bill itself (e.g. 'ONLY FOR BEVERAGES' in the header, and the printed CardCode) and use that company; if the paper names none, it is Oil.
