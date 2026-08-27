---
id: C-0044
date: 2026-08-27
author: measured 2026-08-27 (Daman GRPO session)
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# add-draft on a GRPO posts it live — no approval template catches it

## Wrong
Assumed the C-0034 A/P rule generalises, i.e. that sapb1 add-draft submits a GRPO for approval and you then verify WddStatus='W'. Separately claimed no approval template covers GRPO at all.

## Right
Both wrong. 38 templates cover TransType 20 in Oil and 20 are ACTIVE — but every active one is query-conditioned (Conds='Y'), which SAP skips for Service Layer and DI API documents, and the only two Always templates for GRPO (WtmCode 29, 88) are inactive. Across the whole Oil book only TransType 15 (Delivery, template 67) and TransType 18 (A/P invoice, template 103 'API AP AUTO') have an active Always template; nobody built the GRPO equivalent. So add-draft on a GRPO does not submit — SAP posts it LIVE with no approver. Confirmed by outcome: item GRPOs show 4,815 real OWDD approval requests, while service GRPOs show 0 on 3,923 documents. C-0034 is the A/P-invoice rule and does not extend to ObjType 20.

## Evidence
SELECT T."Active",T."Conds",COUNT(*) FROM "JIVO_OIL_HANADB"."OWTM" T JOIN "JIVO_OIL_HANADB"."WTM3" D ON D."WtmCode"=T."WtmCode" WHERE D."TransType"=20 GROUP BY 1,2;  -- Y/Y 20, N/N 2, N/Y 16 : zero Active+Always.  And: SELECT H."DocType",H."WddStatus",COUNT(DISTINCT H."DocEntry"),COUNT(W."WddCode") FROM "JIVO_OIL_HANADB"."OPDN" H LEFT JOIN "JIVO_OIL_HANADB"."OWDD" W ON W."ObjType"=20 AND W."DocEntry"=H."DocEntry" WHERE H."CANCELED"='N' GROUP BY 1,2;  -- I/P 4048 docs/4815 requests; S/'-' 3923 docs/0 requests

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
sapb1 add-draft on a GRPO POSTS IT LIVE, it does not submit — no active Always-terms template covers ObjType 20 and query-conditioned ones are skipped for API docs. C-0034 is A/P-only.
