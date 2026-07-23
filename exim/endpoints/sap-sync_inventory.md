---
title: "EXIM endpoint — GET /sap-sync/inventory/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/inventory/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/inventory/`

> Raw/factory inventory (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/inventory/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "inventory": [
    {
      "Warehouse": "BH-CRUDE",
      "Category": "CANOLA",
      "Total": 177261.0
    },
    {
      "Warehouse": "BH-EX",
      "Category": "CANOLA",
      "Total": 0.0
    },
    "...(+48 more of 50)"
  ]
}
```

## Field reference

- `inventory[]` — one row per warehouse × oil-category combination.
- `Warehouse` — SAP warehouse code (e.g. `BH-CRUDE` crude stock, `BH-EX` export, at the Baddi/factory site).
- `Category` — oil category the stock rolls up to (CANOLA, OLIVE, MUSTARD, etc.).
- `Total` — quantity on hand in that warehouse for that category, in KG (0.0 rows are kept so every warehouse × category pair appears).

## Used by pages

- [[pages/warehouse-inventory|Warehouse Inventory]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]
- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
