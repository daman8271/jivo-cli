---
id: C-0034
date: 2026-08-26
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [approval]
---

# Only add-draft submits for approval; post goes live unapproved

## Wrong
Treated 'create the document in SAP' as one step — used 'sapb1 post PurchaseInvoices' to enter an A/P invoice, and assumed a 'sapb1 draft' would show up in the approver's queue. Also assumed the DI API on a Windows box would fix it.

## Right
Three different doors. 'sapb1 draft' creates a draft the approver NEVER sees (ODRF.WddStatus='-'; 14,341 such drafts sit in Oil). 'sapb1 post' creates the document LIVE with AuthorizationStatus='dasWithout' — it bypasses the approval procedure entirely and hits the ledger (this is how Oil invoice 49987, Rs 5,664, was posted unapproved on 2026-08-26). Only 'sapb1 add-draft <DocEntry>' (DraftsService_SaveDraftToDocument) is the client's Add button. But Add only SUBMITS if an approval template matches — and SAP deliberately SKIPS templates whose terms are user queries for BOTH the Service Layer and the DI API (SAP Support: 'it is not possible to get the correct value of ApprovalTemplatesID... when the Approval Procedures is based on User Queries'). All 8 of JIVO's active A/P templates were query-only, so nothing matched and Add would have posted live. The fix is an approval template with UseTerms='tNO' (Terms = Always, no query), which the Service Layer DOES honour. Rewriting query conditions to $[TABLE.FIELD] does NOT help — that is also a form reference. Approval does not post the document either: a human presses Add a second time (78 Oil drafts sat at dasApproved worth Rs 87.55 lakh, dasGenerated zero).

## Evidence
Proven live 2026-08-26 Oil. FAIL: POST /PurchaseInvoices -> DocEntry 49987, AuthorizationStatus dasWithout, OJDT TransId 229289 (in the ledger, unapproved). FAIL: POST /Drafts -> 55297, WddStatus '-', zero OWDD rows. PASS: created template 103 (UseTerms tNO, 0 queries, originator USER39, atdtApInvoice, stage 13) then 'sapb1 add-draft 55331' -> SELECT d.WddStatus, w.WddCode, w.WtmCode, u.USER_CODE FROM ODRF d JOIN OWDD w ON w.DraftEntry=d.DocEntry JOIN WDD1 s ON s.WddCode=w.WddCode JOIN OUSR u ON u.USERID=s.UserID WHERE d.DocEntry=55331 -> W | 73093 | 103 | USER03 (BHAWANI); OJDT count 0, OPCH count 0. Corroborated by template 67 (UseTerms tNO) catching 29 API-created (DataSource='S') deliveries at add time, vs 0 of 28 A/R invoices caught by 21 query-conditioned templates in the same period.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P: 'draft' never reaches the approver, 'post' goes live unapproved. Only 'sapb1 add-draft' submits, and only if an Always-terms template matches. Verify ODRF.WddStatus='W'.
