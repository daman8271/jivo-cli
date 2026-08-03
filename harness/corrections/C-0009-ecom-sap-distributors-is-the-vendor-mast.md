---
id: C-0009
date: 2026-08-03
author: damanpreetsingh (ecom rescrape 2026-08-03)
area: all
severity: high
status: active
supersedes: 
tags: [ecom, sap]
---

# ecom 'sap distributors' is the vendor master, not distributors

## Wrong
Answered 'which distributors do we have' from ecom's 'sap distributors' command, and read an empty 'sap distributor-invoices <code>' result as 'this distributor has no business'.

## Right
ecom's /api/sap/distributors returns OCRD rows with CardType='S' - the VENDOR master (ad agencies, suppliers). 1,247 rows, exactly the Mart vendor count. The actual sales distributors are on the customer side, via 'sap platform-distributors'. Querying distributor-invoices with a VENDA... code is a category error: it asks the customer-side ledger about a vendor, so an empty result means wrong side of the ledger, not no business.

## Evidence
Live GET /api/sap/distributors 2026-08-03 returns 1,247 rows whose CardCodes are all VENDA*; matches SELECT COUNT(*) FROM JIVO_MART_HANADB.OCRD WHERE CardType='S' = 1247. Sample rows are advertising agencies. Reproduced by an adversarial verifier. Record: ecom-cli/research/studies/study-sap.md.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
ecom 'sap distributors' = VENDOR master (OCRD CardType='S', ad agencies/suppliers). For real distributors use 'sap platform-distributors'. An empty distributor-invoices result on a VENDA code means wrong ledger side, not no business.
