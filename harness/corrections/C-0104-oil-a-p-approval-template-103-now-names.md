---
id: C-0104
date: 2026-09-19
author: Daman
area: accounts
severity: high
status: active
supersedes: C-0078, C-0088
tags: [approval]
---

# Oil A/P approval template 103 now names USER07 too

## Wrong
Carried C-0078/C-0088 as saying the Oil A/P Always-terms template names only USER39 and USER08, so add-draft from USER07 would post live.

## Right
Template 103 (Oil A/P invoice) now lists USER08 DIVJOT, USER39 MUQEEM and USER07 HARSH. add-draft from USER07 on an Oil A/P submits for approval - it does not post live. Read WTM1 for the template before deciding, rather than trusting the older correction.

## Evidence
SELECT w.WtmCode,u.USER_CODE,u.U_NAME FROM JIVO_OIL_HANADB.WTM1 w JOIN OUSR u ON u.USERID=w.UserID WHERE w.WtmCode=103 -> USER08, USER39, USER07 (2026-09-19). Confirmed live: drafts 57454-57462 and 57468 from USER07 all read back WddStatus='W', AuthorizationStatus dasPending, nothing posted.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Oil A/P Always-terms template 103 now names USER07 (HARSH) as well as USER08 and USER39 - add-draft from USER07 on an Oil A/P SUBMITS, it does not post live. Verify via WTM1 before any add-draft; the list changes.
