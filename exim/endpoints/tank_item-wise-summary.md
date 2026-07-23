---
title: "EXIM endpoint — GET /tank/item-wise-summary/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/item-wise-summary/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/item-wise-summary/`

> Per-item tank summary (qty, capacity, tank list).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/item-wise-summary/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "total_quantity": 892500.0,
  "items": [
    {
      "color": "#10e0c8",
      "tank_item_code": "RM0EL",
      "tank_item_name": "EXTRA LIGHT",
      "quantity_in_liters": 14800.0,
      "total_capacity": 20000.0,
      "tank_count": 1,
      "tank_numbers": [
        "TNK019"
      ]
    },
    {
      "color": "#59f37f",
      "tank_item_code": "RM00POM",
      "tank_item_name": "POMACE",
      "quantity_in_liters": 63000.0,
      "total_capacity": 87000.0,
      "tank_count": 2,
      "tank_numbers": [
        "TNK015",
        "TNK006"
      ]
    },
    "...(+14 more of 16)"
  ]
}
```

## Field reference

- `total_quantity` — total litres in all tanks across every item (892,500 L in the sample).
- `items[]` — one row per tank item currently held:
  - `color` — hex colour for this item in charts (matches `color` on `GET /tank/items/`).
  - `tank_item_code` / `tank_item_name` — item code and display name (e.g. `RM0EL` / EXTRA LIGHT).
  - `quantity_in_liters` — litres of this item currently in tanks.
  - `total_capacity` — combined capacity in litres of the tanks assigned to this item.
  - `tank_count` — number of tanks holding this item.
  - `tank_numbers[]` — the tank codes involved (e.g. `TNK015`, `TNK006`).

## Used by pages

- [[pages/stock-dashboard|Stock Dashboard]]
- [[pages/tank-monitoring|Tank Monitoring]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]
- [[endpoints/tank_tank_code|`GET /tank/{tank_code}/`]]

## Notes

- Kind: **read**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
