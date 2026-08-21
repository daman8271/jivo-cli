---
id: C-0020
date: 2026-08-21
author: Daman (accounts-dashboard build)
area: accounts
severity: high
status: active
supersedes: 
tags: [intercompany]
---

# Intercompany vendors hide outside the BRANCH groups — match on name too

## Wrong
Identified JIVO's own intercompany and branch accounts by joining OCRD to OCRG and testing GroupName LIKE '%BRANCH%', assuming that catches every group entity.

## Right
On the vendor side several intercompany accounts sit in ordinary trading groups, so a group-only test silently counts JIVO's own money as external trade payable. Measured live 2026-08-21: Mart VENDA000001 'JIVO WELLNESS PVT LTD' is in group PURCHASE at -20.93 Cr and is Mart's single largest payable; Mart VENDA000004 'JIVO WELLNESS PVT LTD - DL' also in PURCHASE; Oil VENDA000483 'JIVO MART PVT LTD' is in group E-COMMERCE at -2.25 Cr. Together 23.19 Cr is missed. The remaining group entities do sit in BRANCH VENDOR, so the group test is necessary but not sufficient. Correction C-0005 lists 23 intercompany CardCodes but they are all CUSTA* — it covers no vendor codes at all. Test the group AND the CardName (JIVO / AKAL), and flag the rows rather than dropping them.

## Evidence
SELECT c."CardCode", c."CardName", g."GroupName", CAST(c."Balance" AS DOUBLE) FROM <SCHEMA>.OCRD c LEFT JOIN <SCHEMA>.OCRG g ON g."GroupCode"=c."GroupCode" AND g."GroupType"=c."CardType" WHERE c."CardType"='S' AND (UPPER(c."CardName") LIKE '%JIVO%' OR UPPER(c."CardName") LIKE '%AKAL%') AND CAST(c."Balance" AS DOUBLE) <> 0 -- run per company, 2026-08-21: 3 of 13 group vendors sit outside BRANCH VENDOR, worth 23.19 Cr.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Intercompany vendors hide outside BRANCH groups: Mart VENDA000001 'JIVO WELLNESS' is in group PURCHASE (-20.93 Cr), Oil VENDA000483 in E-COMMERCE. Match OCRD.CardName too, never group alone.
