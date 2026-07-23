---
title: "EXIM endpoint — GET /sap-sync/custa/balance-sheet/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/custa/balance-sheet/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/custa/balance-sheet/`

> Customer (custa) outstanding balance sheet (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/custa/balance-sheet/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "data": [
    {
      "CardCode": "CUSTA001101",
      "CardName": "VARNAY CO GOODS WHOLESALERS CO. L.L.C",
      "SlpName": "GURPREET SINGH",
      "Outstanding Amount": -1350280.75,
      "Outstanding After 1-Apr-26": 0.0,
      "DocNum": 626027401,
      "InvoiceDate": "2026-02-28T00:00:00",
      "Since_Last_Invoice": 140,
      "InvoiceAmount": 4270133.0,
      "Transaction_Date": "2026-02-03T00:00:00",
      "Transaction_Amount": 1350280.75,
      "Since_Last_Transaction": 165
    },
    {
      "CardCode": "CUSTA001124",
      "CardName": "DELHI SIKH GURDWARA MANAGEMENT COMMITTEE",
      "SlpName": "GAGANDEEP SINGH FACTORY",
      "Outstanding Amount": -240000.0,
      "Outstanding After 1-Apr-26": 0.0,
      "DocNum": 626038207,
      "InvoiceDate": "2026-03-30T00:00:00",
      "Since_Last_Invoice": 110,
      "InvoiceAmount": 48000.0,
      "Transaction_Date": null,
      "Transaction_Amount": null,
      "Since_Last_Transaction": null
    },
    "...(+350 more of 352)"
  ]
}
```

## Field reference

- `CardCode` — SAP business-partner code of the customer (CUSTA-prefixed).
- `CardName` — customer legal name.
- `SlpName` — salesperson assigned to the account.
- `Outstanding Amount` — net outstanding balance (₹); negative = customer owes JIVO (debit balance in SAP sign convention).
- `Outstanding After 1-Apr-26` — portion of the outstanding accrued after 1 Apr 2026, i.e. current financial year (₹).
- `DocNum` — SAP document number of the latest invoice for this customer.
- `InvoiceDate` — date of that latest invoice (ISO datetime, time always 00:00).
- `Since_Last_Invoice` — days elapsed since the latest invoice.
- `InvoiceAmount` — value of that latest invoice (₹).
- `Transaction_Date` — date of the last incoming payment/receipt (ISO datetime); null if none recorded.
- `Transaction_Amount` — amount of that last payment (₹); null if none.
- `Since_Last_Transaction` — days since the last payment; null if no payment recorded.

## Used by pages

- [[pages/customer-outstanding|Customer Outstanding]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]
- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
