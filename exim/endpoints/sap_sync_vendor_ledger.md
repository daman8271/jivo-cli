---
title: "EXIM endpoint — GET /sap-sync/vendor/ledger/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/vendor/ledger/
category: sap-sync
kind: read
resource: customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/vendor/ledger/`

> Vendor ledger entries for one party (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/vendor/ledger/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `cardCode` |

## Response — real sample (trimmed)

```json
{
  "vendor_ledger": [
    {
      "PostingDate": "2025-07-22T00:00:00",
      "DocumentDate": "2025-07-22T00:00:00",
      "VoucherNo": 725303228,
      "DocType": "46",
      "SourceDocNo": "725466951",
      "Narration": "Outgoing Payments - VENDA000102",
      "Debit": 2360.0,
      "Credit": 0.0,
      "NetAmount": 2360.0,
      "FCDebit": 0.0,
      "FCCredit": 0.0,
      "DaysSinceLastTrans": 362
    },
    {
      "PostingDate": "2025-07-17T00:00:00",
      "DocumentDate": "2025-07-17T00:00:00",
      "VoucherNo": 725301897,
      "DocType": "46",
      "SourceDocNo": "725466770",
      "Narration": "Outgoing Payments - VENDA000102",
      "Debit": 2360.0,
      "Credit": 0.0,
      "NetAmount": 2360.0,
      "FCDebit": 0.0,
      "FCCredit": 0.0,
      "DaysSinceLastTrans": 367
    },
    "...(+8)"
  ]
}
```

## Field reference

- `vendor_ledger[]` — array of ledger line entries for the vendor identified by `cardCode`.
- `vendor_ledger[].PostingDate` — date the entry was posted to the ledger (ISO date).
- `vendor_ledger[].DocumentDate` — date on the source document (ISO date).
- `vendor_ledger[].VoucherNo` — SAP voucher/journal-entry number.
- `vendor_ledger[].DocType` — SAP document-type code (e.g. `46` = outgoing payment).
- `vendor_ledger[].SourceDocNo` — reference number of the originating document.
- `vendor_ledger[].Narration` — free-text description of the transaction (e.g. `Outgoing Payments - VENDA000102`).
- `vendor_ledger[].Debit` — debit amount (₹).
- `vendor_ledger[].Credit` — credit amount (₹).
- `vendor_ledger[].NetAmount` — net of debit minus credit for the line (₹).
- `vendor_ledger[].FCDebit` — debit amount in foreign currency (0 when the entry is INR-only).
- `vendor_ledger[].FCCredit` — credit amount in foreign currency (0 when the entry is INR-only).
- `vendor_ledger[].DaysSinceLastTrans` — age of the entry in days since the last transaction with the party.

## Notes

- Read-only GET. Ported from the sibling build (`daman8271/exim`) to close a coverage gap.
- CLI: `exim <group> get-...`. Part of [[API-INVENTORY]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
