---
id: C-0023
date: 2026-08-22
author: Avtar
area: accounts
severity: high
status: active
supersedes: 
tags: [ledger]
---

# A party ledger comes from JDT1, not from document extracts

## Wrong
Built the vendor/customer Ledger from the ageing extract (Invoices + CreditNotes + Payments) and treated it as a statement of account.

## Right
The business-partner sub-ledger is JDT1 (JOIN OCRD ON CardCode = ShortName). A document-based extract silently omits every journal entry posted against a party, plus pre-cutover postings, cancelled documents with their reversals, and payments booked under the other side's DocType. Re-verified live 2026-08-22 in JIVO_OIL_HANADB since the migration: A/R invoice 30,956 / A/P invoice 16,330 / incoming payment 13,021 / outgoing payment 10,640 / JOURNAL ENTRY 7,478 (Rs 3,043.6 cr) / A/R credit note 6,431 / A/P credit note 1,587 / manual reconciliation 48. On CUSTA000578 RELIANCE RETAIL the document-based ledger showed 324 of the 620 postings SAP holds. It still footed to the correct closing balance only because the builder plugged the difference into a fabricated opening-balance row - so the omission was invisible from the total. Treat any figure that ties only because of a plug as unverified.

## Evidence
SELECT T0."TransType", COUNT(*) N, ROUND(TO_DOUBLE(SUM(ABS(T0."Debit"-T0."Credit"))),0) VAL FROM "JIVO_OIL_HANADB"."JDT1" T0 JOIN "JIVO_OIL_HANADB"."OCRD" T1 ON T1."CardCode" = T0."ShortName" WHERE T0."RefDate" >= '2024-09-30' GROUP BY T0."TransType" ORDER BY N DESC  -- first run by Avtar 2026-08-20 (JDT1 rebuild tied all 3,585 parties to CurrentAccountBalance with no plug, worst deviation 1 paisa); re-run live 2026-08-22 from JIVO201, every count reproduced with two days' growth

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Build a party ledger from JDT1 (OCRD.CardCode = JDT1.ShortName), never from document extracts - they miss every journal entry (7,478 in Oil, Rs 3,043 cr), cancellations and pre-cutover postings.
