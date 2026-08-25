---
id: C-0029
date: 2026-08-25
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [payments]
---

# Settling bills: pull the BP's open transactions and select all

## Wrong
Hand-picked the single open invoice that matched the amount quoted in the mail, and applied the payment only to that one.

## Right
On an outgoing payment that settles bills, go to the Contents page, set Display to 'Transactions for Business Partner', and select all - so nothing open is silently left behind. Via the API: fetch EVERY open item for the CardCode and put each one in PaymentInvoices, rather than only the row whose figure matches the request. Cross-check the total against OCRD.Balance, because DocStatus='O' is unreliable (C-0019) and open documents can disagree with the balance.

## Evidence
Asserted by Daman 2026-08-25 as the office procedure. Partly verified: PDF2 on draft 2159 carried the applied row correctly (invoice 49114, 6868, InstId 1), and VENDA001090 had exactly ONE open item so the outcome matched - the procedure gap is that the open-item list was never pulled, so a second open bill would have been missed. Not yet verified against a multi-open-item vendor.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Outgoing payment that settles bills: Contents page -> Display = 'Transactions for Business Partner' -> select all. Never apply to one hand-picked invoice; reconcile the total to OCRD.Balance.
