---
title: "EXIM endpoint — GET /tank/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/`

> Storage tanks (code, item, capacity, current fill).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "tank_code": "TNK005",
    "item_code": "RM00CN",
    "tank_capacity": "50000.00",
    "current_capacity": "49000.00",
    "tank_type": "TANK",
    "is_active": true,
    "created_at": "2026-03-24T12:32:55.859877Z",
    "updated_at": "2026-07-03T05:16:14.141859Z"
  },
  {
    "tank_code": "TNK0024",
    "item_code": "RM00MDEO",
    "tank_capacity": "50000.00",
    "current_capacity": "44500.00",
    "tank_type": "TANK",
    "is_active": true,
    "created_at": "2026-06-26T05:47:37.668063Z",
    "updated_at": "2026-07-16T05:47:23.162083Z"
  },
  "...(+30 more of 32)"
]
```

## Field reference

- `tank_code` — unique tank identifier (e.g. `TNK005`); used as the path param in `GET /tank/{tank_code}/`.
- `item_code` — tank-item code of the oil currently stored (e.g. `RM00CN`); joins to `tank_item_code` in `GET /tank/items/`.
- `tank_capacity` — total tank capacity in litres, as a decimal string (`"50000.00"`).
- `current_capacity` — current fill level in litres, decimal string; `current_capacity / tank_capacity` gives utilisation.
- `tank_type` — tank classification; `"TANK"` in the sample.
- `is_active` — whether the tank is in use (boolean).
- `created_at` / `updated_at` — record creation and last-update timestamps (ISO 8601 UTC); `updated_at` moves on every fill-level change.

## Used by pages

- [[pages/tank-data|Tank Data]]
- [[pages/tank-monitoring|Tank Monitoring]]

## Related endpoints

- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]
- [[endpoints/tank_tank_code|`GET /tank/{tank_code}/`]]

## Notes

- Kind: **read**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
