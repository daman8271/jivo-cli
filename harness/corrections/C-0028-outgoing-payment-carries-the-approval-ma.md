---
id: C-0028
date: 2026-08-25
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [payments]
---

# Outgoing payment carries the approval MAIL, not the vendor's bill

## Wrong
Attached the vendor's tax invoice (pulled off the A/P invoice's attachment row) to an outgoing payment draft, treating the bill as the supporting paper.

## Right
The paper that belongs on an outgoing payment is the COMPLETE approval email thread printed to PDF. The mail is the authorisation - it carries the request, the figures, the approver's name and the timestamp. The bill proves what was bought; the mail proves the payment was allowed. A contract advance carries the PO as a SECOND line, never instead of the mail. A screenshot cropped out of the mail is not the mail.

## Evidence
Oil OVPM x ATC1, 2026 YTD, uncancelled: 2840 of 4037 attachment files are 'Jivo Wellness Mail - ...' prints vs 169 purchase orders. VENDA001090 ASHOK KITAB GHAR: all 15 payments since Mar-2025 carry a mail print, ZERO carry the vendor's bill. Query: SELECT ... FROM OVPM O INNER JOIN ATC1 A ON A.AbsEntry=O.AtcEntry WHERE O.CardCode='VENDA001090'

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Outgoing payment attachment = the FULL approval mail thread as PDF (a PO may ride as a second line). Never the vendor's bill, never a cropped screenshot.
