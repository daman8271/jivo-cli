---
id: C-0010
date: 2026-08-04
author: Daman (OMS rescrape 2026-08-04)
area: all
severity: high
status: active
supersedes: 
tags: [oms, hana, sap]
---

# OMS hana branch = SAP company selector (OIL|BEVERAGE), never Mart

## Wrong
Treated /api/hana/* results as one dataset and quoted OMS HANA figures without naming a branch; assumed OMS could reach all three SAP companies like the sap mirror does.

## Right
Every /api/hana/ endpoint REQUIRES ?branch= and it picks a whole SAP company database: OIL=JIVO_OIL_HANADB, BEVERAGE=JIVO_BEVERAGES_HANADB. There is no MART branch. The two return different data for the same call (all-customers 1172 vs 1247 rows, fg-items 443 oils/tea vs 336 mineral water, open-parties 58 vs 31), and 298 of 1165 shared CardCodes are a DIFFERENT PARTY in each company (CUSTA001041 = HIMJYOTI TRADERS in Oil, RAKESH KUMAR in Bev). Card and item codes are branch-local, so joining across branches silently mixes two companies.

## Evidence
Live 2026-08-04: bare GET /api/hana/all-customers/ -> 400 {"error":"branch is required and must be one of: OIL, BEVERAGE"} on all 14 endpoints. ?branch=OIL vs ?branch=BEVERAGE row counts: all-customers 1172/1247, fg-items 443/336, open-parties 58/31, freight-masters 11/10. Full evidence: oms-cli/research/evidence/probe-branch.jsonl and research/studies/study-hana.md.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
OMS /api/hana/* requires branch=OIL|BEVERAGE (no MART); it selects the SAP company DB. Never quote an OMS HANA figure without its branch, and never join card/item codes across branches.
