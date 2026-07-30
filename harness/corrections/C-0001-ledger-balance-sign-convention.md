---
id: C-0001
date: 2026-07-30
author: daman
area: accounts
severity: high
status: active
supersedes: 
tags: [ledger, sign-convention]
---

# Ledger balance sign convention

## Wrong
Reported a negative CurrentAccountBalance as 'the customer owes JIVO'.

## Right
Negative CurrentAccountBalance is a CREDIT — JIVO owes them. Positive is a DEBIT — they owe JIVO.

## Evidence
sapb1 query BusinessPartners --filter "CardCode eq 'V0001'" --select "CardName,CurrentAccountBalance" --json

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
BusinessPartners.CurrentAccountBalance: positive = DEBIT (party owes JIVO), negative = CREDIT (JIVO owes party). Never state the direction without checking the sign.
