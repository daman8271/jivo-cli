---
id: C-0011
date: 2026-08-04
author: Daman (OMS rescrape 2026-08-04)
area: all
severity: high
status: active
supersedes: 
tags: [oms, sap, orders]
---

# OMS raises orders into Oil and Beverages only — zero Mart, ever

## Wrong
Assumed OMS's SAP coverage is uniform: because the sap/ mirror serves all three companies (parties 1172/1247/939 matching OCRD exactly in Oil/Bev/Mart), assumed OMS also transacts for Mart.

## Right
OMS's READ mirror covers all three SAP companies, but its TRANSACTIONAL path reaches only Oil and Beverages. Mart OQUT has zero rows all-time; the OMS document-number band holds 288 Oil + 476 Beverages + 0 Mart; Mart's all-time max ORDR.DocNum is below the OMS band entirely; and OMS's own category_sales has no MART row at all (313/313 top parties are OIL or BEV). So 'OMS shows Mart parties' is true and 'OMS raises Mart orders' is false. This is the mirror image of ecom, where the SAP layer is Mart-only (C-0008).

## Evidence
HANA cross-check 2026-08-04: Mart OQUT = 0 rows all-time; OMS DocNum band = 288 Oil + 476 Bev + 0 Mart; Mart max ORDR.DocNum below the band; OMS category_sales has no MART row. Mirror-vs-HANA identity: sap parties 1172/1247/939 = OCRD CardType='C' exactly. Full working: oms-cli/research/studies/study-sap.md and refutation-orders-sap.md.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
OMS reads all 3 SAP companies but raises orders only into Oil and Beverages — Mart order/quotation count from OMS is always zero. Do not read Mart parties appearing in OMS as Mart business.
