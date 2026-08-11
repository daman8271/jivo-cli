---
id: C-0015
date: 2026-08-12
author: Karanpreet Singh (GST manager), via Daman
area: all
severity: high
status: active
supersedes: 
tags: [segmentation]
---

# U_Main_Group segment tags disagree between company books

## Wrong
Answered a HoReCa Delhi-NCR sales question by filtering OCRD.U_Main_Group = 'HORECA' in one book plus a hardcoded city list, and reported the total as complete. It silently omitted Rs 1.20 Cr because the same customer (Star Sales) was tagged CORPORATE on its Oil card and HORECA on its Mart card. The arithmetic was verified every turn; the filter never was. The user caught it by asking 'is the data from Jivo Wellness or Jivo Mart?'

## Right
U_Main_Group is maintained per company and does NOT agree across the three books. Verified live: 129 customers matched by name carry a different U_Main_Group in Oil vs Mart. The largest split is a spelling difference - Oil spells it 'CALL CENTER' and Mart spells it 'CALL CENTRE' (111 customers), so an equality filter on either spelling silently drops the other company entirely. Four more involve HORECA: Oil CORPORATE / Mart HORECA, Oil HORECA / Mart E-COMMERCE, Oil HORECA / Mart GT, Oil HORECA / Mart ROI. Also seen: ROI vs GT (4), WEBSITE vs E-COMMERCE (3). Any segment total built on this tag in one book is incomplete for the group.

## Evidence
SELECT o."U_Main_Group", m."U_Main_Group", COUNT(*) FROM "JIVO_OIL_HANADB"."OCRD" o JOIN "JIVO_MART_HANADB"."OCRD" m ON UPPER(TRIM(m."CardName"))=UPPER(TRIM(o."CardName")) WHERE o."CardType"='C' AND m."CardType"='C' AND IFNULL(TRIM(o."U_Main_Group"),'')<>'' AND IFNULL(TRIM(m."U_Main_Group"),'')<>'' AND UPPER(TRIM(o."U_Main_Group"))<>UPPER(TRIM(m."U_Main_Group")) GROUP BY 1,2 ORDER BY 3 DESC -- 15 distinct mismatch pairs, 129 customers, top pair CALL CENTER/CALL CENTRE = 111

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
U_Main_Group differs across company books for 129 customers - Oil 'CALL CENTER' vs Mart 'CALL CENTRE' (111), plus 4 HORECA mismatches. Never segment across companies on this tag alone.
