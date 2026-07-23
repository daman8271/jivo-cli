---
title: "EXIM endpoint — GET /sap-sync/balance-sheet/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/balance-sheet/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/balance-sheet/`

> Oil Dr/Cr outstanding balance sheet (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/balance-sheet/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "balance_sheet": [
    {
      "CardCode": "VENDA001347",
      "CardName": "INDRANI FOODS",
      "Balance": -50604960.0,
      "Last Transaction Date": "2025-12-17T00:00:00",
      "Last Transanction Amount": 1000000.0
    },
    {
      "CardCode": "VENDA001490",
      "CardName": "MAHA MAYA FOOD PRODUCTS PRIVATE LIMITED",
      "Balance": -45000004.0,
      "Last Transaction Date": "2026-01-23T00:00:00",
      "Last Transanction Amount": 4975700.0
    },
    "...(+21 more of 23)"
  ]
}
```

## Field reference

- `balance_sheet[]` — one row per business partner in the oil Dr/Cr ledger.
- `CardCode` — SAP business-partner code (VENDA-prefixed vendors here).
- `CardName` — partner legal name.
- `Balance` — net Dr/Cr outstanding (₹); negative = amount payable by JIVO (credit balance), positive = receivable.
- `Last Transaction Date` — date of the most recent ledger transaction with this partner (ISO datetime).
- `Last Transanction Amount` — value of that last transaction (₹); note the SAP-side typo in the key name.

## Used by pages

- [[pages/dashboard|Dashboard]]
- [[pages/exim-account|Oil Dr/Cr Outstanding]]

## Related endpoints

- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
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
