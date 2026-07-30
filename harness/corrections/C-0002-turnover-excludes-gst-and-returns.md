---
id: C-0002
date: 2026-07-30
author: daman
area: accounts
severity: high
status: superseded
supersedes: 
tags: []
---

# Turnover excludes GST and returns

## Wrong
Quoted DocTotal as turnover.

## Right
Turnover is DocTotal minus VatSum, then minus CreditNotes, excluding cancelled.

## Evidence
_not recorded — add the query or source that proves this_

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Turnover = Invoices(DocTotal - VatSum) - CreditNotes, by DocDate, Cancelled eq 'tNO'. DocTotal alone is GST-inclusive, not turnover.
