---
title: "EXIM endpoint — GET /sap-sync/monthly-planning/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/monthly-planning/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/monthly-planning/`

> Monthly SAP planning rows for a given month id.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/monthly-planning/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `monthId` |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "monthly_planning": [
    {
      "U_Sub_Group": "MUSTARD",
      "Quantity": 940174.0
    },
    {
      "U_Sub_Group": "OLIVE",
      "Quantity": 394734.0
    },
    "...(+11 more of 13)"
  ]
}
```

## Field reference

- `monthly_planning[]` — one row per oil sub-group in the selected planning month (13 in the sample).
- `U_Sub_Group` — SAP user-defined sub-group, i.e. the oil category being planned (MUSTARD, OLIVE, etc.).
- `Quantity` — planned quantity for that sub-group in the month, in KG.

## Used by pages

- [[pages/planning|Planning]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]
- [[endpoints/sap-sync_open-pos|`GET /sap-sync/open-pos/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
