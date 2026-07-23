---
title: "EXIM endpoint — GET /sap-sync/customer-aging-balance/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/customer-aging-balance/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/customer-aging-balance/`

> Customer aging balances (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/customer-aging-balance/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "data": [
    {
      "DocNum": 626078203,
      "DocDate": "2026-07-18T00:00:00",
      "Days_Difference": 0,
      "Aging": "0-30 Days",
      "CardCode": "ORGC000001",
      "CardName": "GAGANDEEP SINGH",
      "SlpName": "GAGANDEEP SINGH FACTORY",
      "ShipToCode": "GAGANDEEP SINGH NEW DELHI",
      "DocTotal": 25000.0,
      "PaidToDate": 0.0,
      "Balance": 25000.0,
      "Outstanding Amount": 1256921.9999
    },
    {
      "DocNum": 626078196,
      "DocDate": "2026-07-18T00:00:00",
      "Days_Difference": 0,
      "Aging": "0-30 Days",
      "CardCode": "CUSTA001205",
      "CardName": "SHIVAYE BEVERAGES",
      "SlpName": "SHARANJEET KAUR",
      "ShipToCode": "SHIVAYE BEVERAGES DELHI",
      "DocTotal": 28750.0,
      "PaidToDate": 0.0,
      "Balance": 28750.0,
      "Outstanding Amount": 28750.0
    },
    "...(+4845 more of 4847)"
  ]
}
```

## Field reference

- `data[]` — one row per open customer invoice (4,847 in the sample), used to build the aging buckets.
- `DocNum` — SAP invoice document number.
- `DocDate` — invoice date (ISO datetime).
- `Days_Difference` — days the invoice has been open (today minus `DocDate`).
- `Aging` — aging bucket label derived from `Days_Difference` (e.g. `0-30 Days`).
- `CardCode` / `CardName` — customer SAP code and name.
- `SlpName` — salesperson on the account.
- `ShipToCode` — ship-to address code on the invoice.
- `DocTotal` — invoice total (₹).
- `PaidToDate` — amount already paid against this invoice (₹).
- `Balance` — unpaid remainder on this invoice (₹) = `DocTotal` − `PaidToDate`.
- `Outstanding Amount` — total outstanding across all invoices of this customer (₹), repeated on each of its rows.

## Used by pages

- [[pages/customer-aging|Customer Aging]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
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
