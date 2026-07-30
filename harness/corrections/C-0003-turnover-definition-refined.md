---
id: C-0003
date: 2026-07-30
author: daman
area: accounts
severity: high
status: active
supersedes: C-0002
tags: []
---

# Turnover definition refined

## Wrong
Earlier rule omitted the cancelled-document filter.

## Right
Turnover must also exclude cancelled documents.

## Evidence
_not recorded — add the query or source that proves this_

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Turnover = Invoices(DocTotal - VatSum) - CreditNotes by DocDate, excluding Cancelled eq 'tYES'. DocTotal alone is GST-inclusive.
