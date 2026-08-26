---
id: C-0035
date: 2026-08-26
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [ap-draft, dimensions]
---

# A/P draft lines do NOT inherit Effective Month from the GRPO — set CostingCode2 explicitly

## Wrong
Built 20 A/P invoice drafts with lines drawn from the GRPO (BaseType 20/BaseEntry/BaseLine) and assumed SAP would copy the whole dimension block down from the base document. Verified totals, quantities, tax, branch, series, location and attachments — never checked the dimensions — and reported the batch as complete. All 20 drafts (37 lines) came out with Effective Month null.

## Right
A line drawn from a GRPO inherits Dimension 1 (Variety: CANOLA/OLIVE/MUSTARD/GROUNDNT came through correctly) but NOT Dimensions 2, 3 or 5 — those arrive null and must be set by the payload. Effective Month is Dimension 2 = DocumentLines.CostingCode2, an OOCR DimCode=2 code in MM-YYYY form (e.g. '08-2026'), and for an A/P invoice it is the month of the DOCUMENT date (DocDate = the gate-in date per C-0017), not the vendor's invoice date and not today. It can be set after the fact with PATCH Drafts(<DocEntry>) {"DocumentLines":[{"LineNum":n,"CostingCode2":"MM-YYYY"}]} — that leaves DocTotal, the GRPO base links, LocationCode and AttachmentEntry untouched.

## Evidence
sapb1 query Drafts --filter "DocEntry eq 55311" --json -> every line CostingCode='CANOLA' but CostingCode2=None, CostingCode3=None, CostingCode5=None (same on all 20 of drafts 55302,55311-55329, 37 lines). Valid codes: SELECT OcrCode,OcrName,Active FROM JIVO_OIL_HANADB.OOCR WHERE DimCode=2 -> '08-2026' Active=Y (MM-YYYY series). Posted Aug-26 A/P lines do carry it: SELECT OcrCode2,COUNT(*) FROM JIVO_OIL_HANADB.PCH1 WHERE DocEntry IN (SELECT DocEntry FROM JIVO_OIL_HANADB.OPCH WHERE DocDate>='2026-08-01' AND CANCELED='N') GROUP BY OcrCode2 -> 07-2026:124, NULL:112, 08-2026:51. Fixed live 2026-08-26 by PATCH on all 20; read-back confirms Dim2='08-2026' on all 37 lines with DocTotal, base GRPO links, LocationCode and AttachmentEntry unchanged.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P draft lines inherit only Dim1 from the GRPO: always set CostingCode2 (Effective Month) = the DocDate month as MM-YYYY, e.g. 08-2026, on EVERY line, and check Dim3/Dim5 too.
