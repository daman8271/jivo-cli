---
title: "EXIM endpoint — GET /tank/tank-summary/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/tank-summary/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/tank-summary/`

> Tank totals (capacity, current stock, utilisation).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/tank-summary/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "summary": {
    "total_tank_capacity": 1351500.0,
    "current_stock": 892500.0,
    "utilisation_rate": 66.04,
    "tank_count": 32,
    "item_count": 16
  }
}
```

## Field reference

- `summary` — single aggregate object:
  - `total_tank_capacity` — combined capacity of all tanks, litres (1,351,500 L).
  - `current_stock` — litres currently held across all tanks.
  - `utilisation_rate` — current fill as % of total capacity (66.04).
  - `tank_count` — number of tanks (32).
  - `item_count` — number of distinct items currently in tanks (16).

## Used by pages

- [[pages/tank-data|Tank Data]]
- [[pages/tank-monitoring|Tank Monitoring]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank_code|`GET /tank/{tank_code}/`]]

## Notes

- Kind: **read**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
