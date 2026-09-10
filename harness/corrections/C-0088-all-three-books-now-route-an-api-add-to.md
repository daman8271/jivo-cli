---
id: C-0088
date: 2026-09-10
author: Daman 2026-09-10 (asked for Add & New on Muqeem and Divjot desks)
area: accounts
severity: high
status: active
supersedes: C-0074
tags: [sap-approval, add-draft, mart, beverages]
---

# All three books now route an API Add to approval, and Divjot is an originator too

## Wrong
C-0074: EnableApprovalProcedureInDI is tNO in Mart and Beverages, so sapb1 add-draft posts LIVE there and must stop at the draft. And the Always-terms A/P templates (Oil 103, Mart 48, Bev 68) each name USER39 alone, so any other login posts live.

## Right
Both halves have changed. (1) The DI flag is now on in ALL THREE companies: OADM.EnbApprDI = Y in JIVO_OIL_HANADB, JIVO_MART_HANADB and JIVO_BEVERAGES_HANADB, read 2026-09-10. An admin turned it on in Mart and Bev some time after 2026-09-02 - this repo does not know when or by whom. Guard 5b reads the flag live on every run, so it opened by itself and no binary change was needed. Verified end to end, not just from the flag: add-draft --dry-run as USER39 on Mart draft 39829 and Bev draft 16056 raised ZERO di-approval problems and both printed 'would be submitted for approval'. (2) USER08 (DIVJOT, USERID 17 in all three books) was PATCHed onto all three Always-terms A/P templates on 2026-09-10 on Damans instruction, beside USER39 (MUQEEM). Approver is still USER03 (BHAWANI), terms still Always, document type still A/P invoice only. So Muqeem AND Divjot both reach Bhawani from their own login, in any of the three books. Everyone else is unchanged and still posts LIVE - USER07 and USER19 are on no Always-terms template at all, which is why the Shahrukh, Vishal, Priya and Mahak desks stay drafts-only.

## Evidence
OADM read 2026-09-10 via hana-sql: EnbApprDI = Y in all three company DBs (was Oil Y, Mart N, Bev N on 2026-09-02). Live add-draft --dry-run from Muqeems box, new binary 670c3569: Mart 39829 as USER39 and Bev 16056 as USER39 both zero di-approval hits and zero originator hits, verdict 'would be submitted for approval'; Divjot 51326 as USER08 in Oil the same. Templates read back after PATCH via OWTM/WTM3/WTM1 join on WTM1/OUSR: Oil 103 USER39,USER08; Mart 48 USER39,USER08; Bev 68 USER39,USER08; two originators each, no duplicates, approver USER03 via WTM2/WST1 in every book. Divjot before the change: same command, same draft, refused with 'USER08 is not an originator'.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
add-draft routes to BHAWANI in ALL THREE books now (OADM.EnbApprDI=Y, 2026-09-10) and Oil 103 / Mart 48 / Bev 68 each name USER39 + USER08. Every other login still posts LIVE - never submit from one.
