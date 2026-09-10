---
id: C-0074
date: 2026-09-02
author: Daman's session 2026-09-02 (incident: Mart A/P 12210 posted live from draft 40128)
area: accounts
severity: high
status: superseded
supersedes: 
tags: [sap-approval, add-draft, mart, beverages]
---

# Mart and Beverages: approval procedures are OFF for the DI/Service Layer — add-draft posts LIVE there

## Wrong
Template 48 'API AP AUTO (USER39)' exists in JIVO_MART_HANADB (Always terms, originator USER39, approver USER03), so sapb1 add-draft on a Mart A/P draft will be submitted for approval, exactly as in Oil.

## Right
SAP only evaluates approval templates for DI-API/Service Layer documents when the company flag EnableApprovalProcedureInDI (General Settings → BP → 'Enable Approval Procedures in DI') is on. It is tYES in JIVO_OIL_HANADB and tNO in JIVO_MART_HANADB and JIVO_BEVERAGES_HANADB (checked 2026-09-02). In Mart and Bev no template can ever fire for an API Add, so add-draft posts the document LIVE with no approver. Draft 40128 (DPTC bill 122, Rs 88,951) became live A/P invoice 12210 / JE 85639 this way.

## Evidence
POST /b1s/v1/CompanyService_GetAdminInfo per company 2026-09-02: Oil EnableApprovalProcedureInDI=tYES, Mart=tNO, Bev=tNO. Mart OWTM 48 Conds=N Active=Y WTM3 TransType 18 WTM1 USER39 WST 4 USER03 — present, ignored. Drafts(40128) add-draft → PurchaseInvoices 12210 DocNum 608264293, OPCH.WddStatus '-', OWDD rows for DraftEntry 40128 = 0, OJDT 85639 posted. Oil proof of the opposite: draft 55331 → request 73093 (2026-08-26).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
sapb1 add-draft in JIVO_MART_HANADB or JIVO_BEVERAGES_HANADB posts LIVE — EnableApprovalProcedureInDI is tNO there, templates never fire for API Adds. Only Oil (tYES) routes to approval. In Mart/Bev stop at the draft; a person presses Add.
