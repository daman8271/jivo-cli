---
id: C-0032
date: 2026-08-25
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [reconciliation]
---

# Establish a figures file's company scope before calling any variance unexplained

## Wrong
Reconciled Accounts' budget-3-month.xlsx against JIVO_OIL_HANADB alone, reported a Rs 1.95 Cr (22%) unexplained gap, named Factory (Rs 1.39 Cr) and Delivery Bhakharpur (Rs 45.07 L) as irreproducible, and explicitly listed 'Oil and Beverages added together' as a hypothesis already ruled out. The file was in fact Oil + Beverages combined; on the correct scope the gap is Rs 11.96 L, i.e. 1.11%.

## Right
The file covered TWO company DBs. Master data proves it: OOCR Dimension-4 codes DIG MKT and PPR MED exist ONLY in JIVO_BEVERAGES_HANADB (Oil and Mart carry DIGTAL M and POP instead), and both tie to the rupee against Beverages - PPR MED Jun-2026 file Rs 600 = Bev Rs 600; DIG MKT Jul-2026 file Rs 20,512 = Bev Rs 20,512. On Oil+Bev: 18 of 46 Dim3xDim4 cells tie exactly, 33 within Rs 50,000, Delivery Bhakharpur falls from Rs 45.07 L out to Rs 5.07 L and Factory from Rs 1.39 Cr out to Rs 31.80 L. Also: a Dim3xDim4 comparison must normalise blanks first - Beverages stores '' where Oil stores a value, which splits one cell into two and hides the match.

## Evidence
SELECT "OcrCode" FROM <DB>.OOCR WHERE "DimCode"=4 AND "OcrCode" IN ('DIG MKT','PPR MED','DIGTAL M','POP') -- returns DIG MKT+PPR MED for JIVO_BEVERAGES_HANADB only, DIGTAL M+POP for Oil and Mart. Tie-out: SELECT j."OcrCode4", LEFT(j."RefDate",7), SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) FROM JIVO_BEVERAGES_HANADB.JDT1 j JOIN OACT a ON a."AcctCode"=j."Account" WHERE SUBSTRING(a."AcctCode",1,2)='56' AND a."GroupMask"=5 AND j."OcrCode4" IN ('DIG MKT','PPR MED') AND j."RefDate">='2026-05-01' AND j."RefDate"<'2026-08-01' GROUP BY 1,2

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Before calling any variance unexplained, prove which company DBs the file covers: OOCR Dim4 DIG MKT/PPR MED exist ONLY in Beverages, DIGTAL M/POP only in Oil+Mart. Normalise blank dims before diffing.
