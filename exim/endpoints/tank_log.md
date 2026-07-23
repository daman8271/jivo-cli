---
title: "EXIM endpoint — GET /tank/log/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/log/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/log/`

> Tank inflow/outflow log entries.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/log/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 150,
    "log_type": "INWARD",
    "quantity": "29820.00",
    "vehicle_number": "GJ39TA8718",
    "rate": "147.00",
    "party": "AWL AGRI BUSINESS LIMITED",
    "item_code": null,
    "item_name": null,
    "arrival": null,
    "created_at": "2026-04-21T06:03:21.062998Z",
    "created_by": "raspreet@exim.com",
    "stock_status": 306
  },
  {
    "id": 151,
    "log_type": "INWARD",
    "quantity": "41730.00",
    "vehicle_number": "RJ14GQ1756",
    "rate": "154.30",
    "party": "BD EDIBLE OILS PVT LTD",
    "item_code": null,
    "item_name": null,
    "arrival": null,
    "created_at": "2026-04-21T06:49:33.760132Z",
    "created_by": "raspreet@exim.com",
    "stock_status": 305
  },
  "...(+138 more of 140)"
]
```

## Field reference

- `id` — log entry id (integer).
- `log_type` — flow direction: `INWARD` (into a tank) vs outward movements.
- `quantity` — quantity moved, litres, as a decimal string (`"29820.00"`).
- `vehicle_number` — tanker registration that carried the load (e.g. `GJ39TA8718`).
- `rate` — per-litre rate in ₹, decimal string (`"147.00"`).
- `party` — counterparty/supplier name (e.g. AWL AGRI BUSINESS LIMITED).
- `item_code` / `item_name` — tank item on the entry; null in the sample when the entry is tied to a stock record instead.
- `arrival` — linked arrival reference; null for these entries.
- `created_at` — when the log was recorded (ISO 8601 UTC).
- `created_by` — user email that recorded the entry.
- `stock_status` — id of the linked stock-status record the movement belongs to.

## Used by pages

- [[pages/tank-logs|Tank Logs]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]
- [[endpoints/tank_tank_code|`GET /tank/{tank_code}/`]]

## Notes

- Kind: **read**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
