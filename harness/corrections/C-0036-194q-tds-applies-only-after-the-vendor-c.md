---
id: C-0036
date: 2026-08-26
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [tds, 194q, ap-draft]
---

# 194Q TDS applies only after the vendor crosses Rs 50 lakh of purchases in the financial year — SAP does not enforce it

## Wrong
Decided TDS per bill by looking at whether the vendor's recent posted invoices happened to carry WTSum, treating 'this vendor usually has TDS' as the rule. That is a symptom, not the rule — it gets the right answer only by accident, and it gives no way to tell when a vendor is about to become liable or when an existing deduction was a mistake.

## Right
Section 194Q is a THRESHOLD rule: TDS at 0.1% is deducted only on purchases from a vendor once aggregate purchases from that vendor in the financial year exceed Rs 50,00,000, and it applies to the amount above that threshold. Below Rs 50 lakh FYTD, no TDS. This is why some vendors show TDS on every invoice and others on none — it is not a per-vendor setting, it is where that vendor sits against the threshold this year. CRITICAL: SAP does NOT enforce the threshold. If WTCode 1031 is set on a line SAP computes 0.1% regardless, so the threshold decision is a human one, made before the code goes on. Measured Oil FY26-27 as at 2026-08-26: Raj Technopack Rs 1,41,16,772 / SSY Containers Rs 92,27,837 / Echo Plast Rs 74,48,210 are over and carry TDS on every invoice; Babaji Rs 46,83,067, Pioneer Pet Rs 41,36,754, Royal Prime Rs 41,04,807, Kuber Rs 37,27,315, TPAC Rs 37,26,273, BR Agrotech Rs 26,44,198, Multilayer Rs 3,93,696 are under and should carry none.

## Evidence
Threshold vs behaviour, Oil FY26-27: SELECT CardCode, SUM(DocTotal-VatSum) AS TAXABLE_FYTD, SUM(WTSum) FROM JIVO_OIL_HANADB.OPCH WHERE DocDate>='2026-04-01' AND CANCELED='N' GROUP BY CardCode -> the only three vendors above Rs 50L (Raj Technopack 1.41 Cr, SSY 92.3 L, Echo Plast 74.5 L) are exactly the three with TDS (Rs 9,131 / 4,502 / 3,061); the seven below Rs 50L carry Rs 0 apart from four stray rows. Withholding shape on all 18 recent posted invoices of those three: WTCode 1031, Rate 0.1, Category I, WithholdingType V, TaxableAmount = SUM(LineTotal) net of GST, WTAmount rounded to the rupee. PROOF SAP DOES NOT ENFORCE THE THRESHOLD: OPCH rows 43996/46047/48780 (TPAC, Rs 37.3 L FYTD) and 48981 (Royal Prime, Rs 41.0 L FYTD) carry WTSum 156/125/138/67 while both vendors are under Rs 50 lakh — keyed by UserSign 16 and 17, i.e. SAP accepted a deduction that the threshold did not permit.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
194Q TDS 0.1% (WTCode 1031) only once that vendor's FY purchases pass Rs 50 lakh — check SUM(DocTotal-VatSum) FYTD before setting it. SAP does NOT enforce the threshold; it deducts whenever the code is set.
