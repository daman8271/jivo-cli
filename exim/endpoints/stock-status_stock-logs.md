---
title: "EXIM endpoint — GET /stock-status/stock-logs/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/stock-logs/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/stock-logs/`

> Field-level audit log of stock-status changes.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/stock-logs/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": "00644799-678b-4002-a14d-bbceb7424664",
    "stock": 648,
    "action": "UPDATE",
    "changed_by_label": "raspreet@exim.com",
    "note": "",
    "timestamp": "2026-07-18T13:42:03.644166Z",
    "field_logs": [
      {
        "field_name": "status",
        "old_value": "OUT_SIDE_FACTORY",
        "new_value": "IN_TANK"
      },
      {
        "field_name": "quantity",
        "old_value": "38880.00",
        "new_value": "38820.00"
      }
    ]
  },
  {
    "id": "c9e4723c-f0a8-4c9f-ba18-75e63e934a71",
    "stock": 656,
    "action": "UPDATE",
    "changed_by_label": "raspreet@exim.com",
    "note": "move \u2192 ON_THE_WAY",
    "timestamp": "2026-07-18T10:11:01.961826Z",
    "field_logs": [
      {
        "field_name": "status",
        "old_value": "UNDER_LOADING",
        "new_value": "ON_THE_WAY"
      },
      {
        "field_name": "quantity",
        "old_value": "40060.00",
        "new_value": "40060"
      }
    ]
  },
  "...(+1478 more of 1480)"
]
```

## Field reference

- `id` — log entry UUID.
- `stock` — id of the stock-status row that was changed (`GET /stock-status/{id}/`).
- `action` — change type (e.g. `UPDATE`).
- `changed_by_label` — email of the user who made the change.
- `note` — optional free-text note attached to the change (e.g. "move → ON_THE_WAY"); often empty.
- `timestamp` — when the change happened (ISO datetime, UTC).
- `field_logs[]` — one entry per changed field:
  - `field_name` — which field changed (e.g. `status`, `quantity`).
  - `old_value` / `new_value` — before/after values as strings (status codes, kg quantities, etc.).

## Used by pages

- [[pages/stock-updation-logs|Stock Updation Logs]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]
- [[endpoints/stock-status_id|`GET /stock-status/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
