---
id: C-0033
date: 2026-08-25
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [dimensions]
---

# Effective Month is SAP Dimension 2, not TaxDate

## Wrong
Asked for expenses by 'effective month', assumed it meant the vendor's invoice date and built the analysis on JDT1.TaxDate, then reported a posting-date vs effective-date comparison on that basis.

## Right
JIVO names all five SAP dimensions in ODIM: 1 = Variety, 2 = Effective Month, 3 = Budget, 4 = Sub Budget, 5 = State. Effective Month is a real dimension held in JDT1.OcrCode2 as MM-YYYY codes (e.g. 04-2026) - the month the cost BELONGS to, which is what Accounts means by the phrase. It is already in use on 53% of Oil expense lines, 40% Beverages, 20% Mart, and it genuinely differs from the posting month: Apr-2026 postings carry effective months of Jan, Feb and Mar 2026 and even Jun 2024. TaxDate is the vendor's invoice date (see C-0017) and is NOT the effective month.

## Evidence
SELECT "DimCode","DimName","DimDesc" FROM JIVO_OIL_HANADB.ODIM -- DimDesc gives Variety / Effective Month / Budget / Sub Budget / State. Coverage + drift: SELECT LEFT(j."RefDate",7) POSTED, j."OcrCode2" EFF_MTH, COUNT(*), SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) FROM JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account" WHERE SUBSTRING(a."AcctCode",1,2)='56' AND a."GroupMask"=5 AND IFNULL(j."OcrCode2",'')<>'' AND j."RefDate">='2026-04-01' AND j."RefDate"<'2026-08-01' GROUP BY 1,2

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Effective Month = SAP Dimension 2, JDT1.OcrCode2, MM-YYYY codes. It is the month a cost belongs to. Never substitute TaxDate or RefDate. Dim1=Variety Dim2=EffMonth Dim3=Budget Dim4=SubBudget Dim5=State.
