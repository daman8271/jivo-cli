---
id: C-0008
date: 2026-08-03
author: damanpreetsingh (ecom rescrape 2026-08-03)
area: all
severity: high
status: active
supersedes: 
tags: [ecom, sap]
---

# ecom's SAP mirror is JIVO MART, not Oil or the group

## Wrong
Read /api/sap/* figures from the ecom app (ecom-cli 'sap' commands, MCP ecom_sap) as JIVO group or Oil numbers, because Oil is the default company everywhere else in this toolkit.

## Right
The ecom app mirrors JIVO_MART_HANADB only. Verified by row count against all three company databases on 2026-08-03: sap items 1,349 = Mart OITM (Oil 2,270, Beverages 2,192); sap distributors 1,247 = Mart OCRD CardType='S'; sap sales-invoices 25,157 = Mart OINV; sap inventory-overview 47,908 = Mart OITW. DocEntry 37594 exists in Mart and in no other company. Only 'sap sales-analysis --source oil' reaches Oil; Beverages is unreachable from ecom entirely - no parameter, no endpoint.

## Evidence
Live GET of each ecom sap endpoint 2026-08-03 vs HANA counts per company: SELECT COUNT(*) FROM <company>.OITM / OCRD WHERE CardType='S' / OINV / OITW across JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB. Reproduced independently by an adversarial verifier. Full record: ecom-cli/research/studies/study-sap.md and verdict-sap-reports-shipment-uploads.jsonl.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
ecom /api/sap/* (ecom-cli 'sap', MCP ecom_sap) is JIVO_MART only - never Oil, never group. Only 'sales-analysis --source oil' reaches Oil; Beverages is unreachable from ecom.
