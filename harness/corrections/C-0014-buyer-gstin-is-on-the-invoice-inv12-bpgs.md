---
id: C-0014
date: 2026-08-12
author: Karanpreet Singh (GST manager), via Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [gst]
---

# Buyer GSTIN is on the invoice (INV12.BpGSTN), not the customer master

## Wrong
Stated 'OCRD.LicTradNum is empty for all active customers and CRD7.TaxId0 holds the 10-character PAN, not the GSTIN' as a master-data defect, implying JIVO has no GSTIN on file. Testing B2B vs B2C against the customer master would classify every customer as B2C and make every e-invoicing, GSTR-1 and IRN-exemption number wrong.

## Right
The buyer GSTIN is captured per invoice in INV12.BpGSTN (NVARCHAR 15), alongside INV12.BpGSTType and INV12.LocGSTN for JIVO's own registration. It is populated and reliable. Verified live on Oil from 1 Nov 2025: 5,127 invoices (Rs 368.76 Cr) carry a 15-char BpGSTN = B2B and require an IRN; 1,357 invoices (Rs 1.23 Cr) have none = B2C and are exempt. By contrast OCRD.LicTradNum is empty on all 1,163 active customers and CRD7.TaxId0 is 10 characters (PAN) on all 4,035 populated rows. The master is not the source.

## Evidence
SELECT CASE WHEN LENGTH(TRIM(IFNULL(T."BpGSTN",'')))=15 THEN 'B2B' ELSE 'B2C' END, COUNT(*), ROUND(SUM(H."DocTotal")/10000000,2) FROM "JIVO_OIL_HANADB"."OINV" H JOIN "JIVO_OIL_HANADB"."INV12" T ON T."DocEntry"=H."DocEntry" WHERE H."CANCELED"='N' AND H."DocDate">='2025-11-01' GROUP BY 1 -- B2B 5127/368.76Cr, B2C 1357/1.23Cr. Master check: OCRD.LicTradNum non-empty=0 of 1163 active customers; CRD7.TaxId0 all length 10 (PAN), TaxId1 all empty.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Buyer GSTIN is INV12.BpGSTN (invoice level, 15 chars). OCRD.LicTradNum is EMPTY for all customers and CRD7.TaxId0 is the 10-char PAN - never use either to decide B2B vs B2C.
