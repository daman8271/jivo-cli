---
id: C-0019
date: 2026-08-21
author: Daman (accounts-dashboard build)
area: accounts
severity: high
status: active
supersedes: 
tags: [ageing]
---

# DocStatus='O' is unreliable — age from OCRD.Balance, not open documents

## Wrong
Built an ageing by summing open documents (OINV/OPCH DocStatus='O', DocTotal-PaidToDate) and bucketing on DocDueDate, treating 'open' as 'unpaid'.

## Right
At JIVO a document stays DocStatus='O' long after the money moved, because settlements are posted as manual journal entries (JDT1.TransType=30) and as on-account ORCT/OVPM receipts and payments that are never internally reconciled to the document. OCRD.Balance is the only ground truth for what a party owes or is owed. Measured live 2026-08-21, open documents vs OCRD balances: Oil A/R 180.69 vs 109.51 Cr and A/P 309.20 vs 102.63 Cr; Mart A/R 128.12 vs 23.35 Cr and A/P 219.60 vs 29.22 Cr; Bev A/R 6.34 vs 4.83 Cr and A/P 3.56 vs 2.24 Cr. Overstatement 1.3x to 7.5x, worst on Mart payables. Correct method: take the party balance as the real exposure, derive unapplied credit as sum(open docs) - balance, consume it oldest-due-first, then bucket the remainder.

## Evidence
SELECT (SELECT SUM(CAST("DocTotal"-"PaidToDate" AS DOUBLE)) FROM <SCHEMA>.OINV WHERE "DocStatus"='O' AND "CANCELED"='N') AS AR_OPEN_DOCS, (SELECT SUM(GREATEST(0,CAST("Balance" AS DOUBLE))) FROM <SCHEMA>.OCRD WHERE "CardType"='C') AS AR_OCRD, (SELECT SUM(CAST("DocTotal"-"PaidToDate" AS DOUBLE)) FROM <SCHEMA>.OPCH WHERE "DocStatus"='O' AND "CANCELED"='N') AS AP_OPEN_DOCS, (SELECT SUM(GREATEST(0,-CAST("Balance" AS DOUBLE))) FROM <SCHEMA>.OCRD WHERE "CardType"='S') AS AP_OCRD FROM DUMMY -- run per company schema, 2026-08-21. Cross-check: OCRD customers 106.07 Cr - vendors 93.65 Cr = 12.42 Cr, ties exactly to the GL BP control lines in JDT1.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
SAP DocStatus='O' is unreliable at JIVO: documents settled by manual JE or unapplied on-account payment stay open. Age from OCRD.Balance, not open documents - naive ageing overstates 1.3-7.5x.
