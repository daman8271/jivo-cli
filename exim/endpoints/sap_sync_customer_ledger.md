---
title: "EXIM endpoint — GET /sap-sync/customer/ledger/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/customer/ledger/
category: sap-sync
kind: read
resource: customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/customer/ledger/`

> Customer ledger entries for one party (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/customer/ledger/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `cardCode` |

## Response — real sample (trimmed)

```json
{
  "customer_ledger": []
}
```

## Field reference

- `customer_ledger[]` — array of ledger line entries for the customer identified by `cardCode`. Empty in this sample (no transactions for the party). Each entry mirrors the vendor-ledger shape: `PostingDate`/`DocumentDate` (ISO date), `VoucherNo`, `DocType`, `SourceDocNo`, `Narration`, `Debit` (₹), `Credit` (₹), `NetAmount` (₹), `FCDebit`/`FCCredit` (foreign-currency amounts), `DaysSinceLastTrans` (days).

## Notes

- Read-only GET. Ported from the sibling build (`daman8271/exim`) to close a coverage gap.
- CLI: `exim <group> get-...`. Part of [[API-INVENTORY]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
