---
id: C-0085
date: 2026-09-08
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [tds, 194q, ap-draft]
---

# 194Q TDS is not a judgement call — check the Rs 50 lakh threshold on EVERY A/P entry and apply TDS automatically when the seller is over

## Wrong
Decided TDS per bill from the vendor master flag and how that vendor's last posted invoices were booked, and ran the Rs 50 lakh threshold check only when an operator asked for it. On 2026-09-08 three A/P drafts (56484/56485/56486) were built with WTLiable tNO on precedent alone; the threshold was measured afterwards, on request, and only then confirmed nil.

## Right
The Rs 50 lakh 194Q test is MANDATORY and AUTOMATIC on every A/P entry, before the draft is built. Compute the seller's financial-year purchases -- SUM(OPCH.DocTotal - VatSum) from 01-Apr, aggregated across every CardCode sharing that seller's PAN (C-0037) -- and if the total is over Rs 50,00,000, SET 194Q TDS 0.1% (WTCode 1031) on the bill without being asked. Under Rs 50 lakh, no TDS. Precedent is not evidence: a vendor that carried no TDS on its last three bills may have crossed the threshold since, and SAP will never say so (C-0036). When the PAN is missing from CRD7.TaxId0 -- true for 155 of the 408 vendors with Oil purchases in FY26-27 -- fall back to the CardCode total and SAY that the PAN aggregation could not run.

## Evidence
Measured live 2026-09-08, JIVO_OIL_HANADB, FY26-27 (DocDate >= 2026-04-01, CANCELED='N'), OPCH net of ORPC: AG POLY PACKS VENDA000031 Rs 11,96,190 taxable and THE TIN FACTORY VENDA000365 Rs 0 -- both far under, so drafts 56484/56485/56486 are correctly nil. The same sweep grouped by COALESCE(CRD7.TaxId0, CardCode) shows the cost of NOT checking: ANJU MANGLA (PAN ACGPG8020Q, resident, INR) Rs 21.06 Cr FYTD with TDS Rs 0 (~Rs 2.06 L at 0.1% of the excess), RAHUL MANGLA Rs 1.85 Cr with Rs 0, and TPAC (2 cards on AAGCT4816J) Rs 82.7 L with Rs 1,141 taken against ~Rs 3,272 due. GRAINCORP (AU) and MIGASA (ES) also show nil and are CORRECT -- non-resident sellers are outside 194Q. KUBER PAPER sits at Rs 47.03 L, Rs 2.97 L from crossing with no PAN in SAP to aggregate on.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Every A/P entry: SUM(OPCH.DocTotal-VatSum) FYTD across all cards on the seller's PAN, and SET 194Q TDS 0.1% (WTCode 1031) if over Rs 50 lakh. Never decide TDS from the vendor's precedent.
