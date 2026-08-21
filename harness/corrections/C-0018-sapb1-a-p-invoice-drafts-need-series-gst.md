---
id: C-0018
date: 2026-08-21
author: Claude (verified live), session with Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [sapb1-write]
---

# sapb1 A/P invoice drafts: need Series+GST subtype, and come out with TDS = 0

## Wrong
Assumed POST /Drafts for an A/P invoice needs only CardCode, dates, branch and base-GRPO lines, and that SAP would apply the vendor's 0.1% TDS automatically like the client does.

## Right
Oil numbers A/P invoices per branch x month x sub-type (NNM1: HR_B0826=3324 plain, HR_G0826=3684 GST tax invoice, HR_D0826=3857 for FACTORY Aug-26). Without Series SAP answers -10 'define the numbering series'; with Series 3684 but no DocumentSubType it answers -4002 the same. Series 3684 + DocumentSubType bod_GSTTaxInvoice succeeds. The created draft had WTLiable tNO on every line and WTAmount 0 although the BP is SubjectToWithholdingTax with WTCode 1031, whereas every client-made SSY/Frystal invoice carries 0.1% TDS (WTAmount 187/292/177/73).

## Evidence
2026-08-21 Oil: two rejected attempts (-10, -4002) then success creating Drafts 54937 for VENDA000936 26-27/1450; read-back WTAmount 0, lines WTLiable tNO; BusinessPartners VENDA000936 SubjectToWithholdingTax boYES WTCode 1031; hana-sql: SELECT Series,SeriesName,DocSubType,BPLId,Indicator FROM JIVO_OIL_HANADB.NNM1 WHERE ObjectCode='18' AND Indicator='AUG-26-27'; posted invoices 49158/49117/49116 WTAmount 187/292/177. Fix for TDS (WTLiable tYES per line via SL) NOT yet verified.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
sapb1 draft purchase-invoice needs Series (branch+month+GA subtype, FACTORY Aug-26 = 3684) + DocumentSubType bod_GSTTaxInvoice, and comes out with TDS 0 (WTLiable tNO) — check WTAmount before Add.
