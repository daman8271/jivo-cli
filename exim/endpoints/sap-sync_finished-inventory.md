---
title: "EXIM endpoint — GET /sap-sync/finished-inventory/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/finished-inventory/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/finished-inventory/`

> Finished-goods inventory (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/finished-inventory/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "finished_inventory": [
    {
      "Warehouse": "BH-EC",
      "Category": "BLENDED",
      "Total": 5125.0
    },
    {
      "Warehouse": "BH-EC",
      "Category": "CANOLA",
      "Total": 2058.0
    },
    "...(+20 more of 22)"
  ]
}
```

## Field reference

- `finished_inventory[]` — one row per warehouse × category of finished (packed) goods.
- `Warehouse` — SAP finished-goods warehouse code (e.g. `BH-EC`).
- `Category` — oil category of the finished stock (BLENDED, CANOLA, OLIVE, etc.).
- `Total` — finished-goods quantity on hand for that pair, in KG.

## Used by pages

- [[pages/warehouse-inventory|Warehouse Inventory]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]
- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
