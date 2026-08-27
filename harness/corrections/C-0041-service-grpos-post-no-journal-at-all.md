---
id: C-0041
date: 2026-08-27
author: measured 2026-08-27 (Daman GRPO session)
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# Service GRPOs post no journal at all

## Wrong
Said a service GRPO debits the freight expense and credits 2140001 Goods Received But Not Invoiced, i.e. that it accrues the cost — repeating the journal section of the entry-vault note sap-b1/entry-vault/02-documents/GRPO.md.

## Right
That is the ITEM receipt only. A service GRPO (DocType 'S') posts no journal entry whatsoever: TransId is NULL on all 3,923 non-cancelled Oil service GRPOs, against 4,762 of 6,858 item GRPOs that do carry one. No expense, no GRNI, no accrual, no vendor liability, at any point in its life — nothing reaches the ledger until the A/P invoice. So the 'open GRPOs waiting for a bill' figure is a commitment, not a ledger balance, and the credits to 2140001 under TransType 20 are item receipts.

## Evidence
SELECT "DocType", CASE WHEN "TransId" IS NULL OR "TransId"=0 THEN 'NO journal' ELSE 'has journal' END K, COUNT(*) FROM "JIVO_OIL_HANADB"."OPDN" WHERE "CANCELED"='N' GROUP BY 1,2;  -- S/NO journal 3923 (no 'has journal' row for S); I/has journal 4762, I/NO journal 2096

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Service GRPOs (DocType S) post NO journal: TransId NULL on all 3,923 Oil docs — no expense, no GRNI, no accrual. Only item GRPOs credit 2140001. Open service GRPOs are a commitment, not a balance.
