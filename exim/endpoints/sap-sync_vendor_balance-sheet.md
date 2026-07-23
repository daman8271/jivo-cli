---
title: "EXIM endpoint — GET /sap-sync/vendor/balance-sheet/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/vendor/balance-sheet/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/vendor/balance-sheet/`

> Vendor outstanding balance sheet (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/vendor/balance-sheet/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "data": [
    {
      "CardCode": "VENDA000003",
      "CardName": "JIVO WELLNESS PVT LTD - HR",
      "Balance": -689617985.65,
      "Last Transaction Date": "2026-04-30T00:00:00",
      "Last Transanction Amount": 751.0
    },
    {
      "CardCode": "VENDA000004",
      "CardName": "JIVO WELLNESS PVT LTD - DL",
      "Balance": -54018504.0,
      "Last Transaction Date": "2024-12-10T00:00:00",
      "Last Transanction Amount": 700319.0
    },
    "...(+385 more of 387)"
  ]
}
```

## Field reference

- `data[]` — one row per vendor account (387 in the sample).
- `CardCode` — SAP vendor code (VENDA-prefixed; includes inter-company entities like JIVO WELLNESS HR/DL).
- `CardName` — vendor legal name.
- `Balance` — net outstanding with the vendor (₹); negative = payable by JIVO (credit balance in SAP sign convention).
- `Last Transaction Date` — date of the most recent ledger entry with this vendor (ISO datetime).
- `Last Transanction Amount` — value of that last transaction (₹); key name carries the SAP-side typo.

## Used by pages

- [[pages/vendor-outstanding|Vendor Outstanding]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
