---
title: "EXIM endpoint — GET /tank/{tank_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/{tank_code}/
category: tank
kind: detail
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/{tank_code}/`

> Single tank detail.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/{tank_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `tank_code` |

## Response — real sample (trimmed)

```json
{
  "tank_code": "TNK005",
  "item_code": "RM00CN",
  "tank_capacity": "50000.00",
  "current_capacity": "49000.00",
  "tank_type": "TANK",
  "is_active": true,
  "created_at": "2026-03-24T12:32:55.859877Z",
  "updated_at": "2026-07-03T05:16:14.141859Z"
}
```

## Field reference

- `tank_code` — the tank identifier requested in the path (e.g. `TNK005`).
- `item_code` — tank-item code of the oil currently stored (joins to `tank_item_code` in `GET /tank/items/`).
- `tank_capacity` — total capacity in litres, decimal string (`"50000.00"`).
- `current_capacity` — current fill level in litres, decimal string.
- `tank_type` — tank classification; `"TANK"` in the sample.
- `is_active` — whether the tank is in use (boolean).
- `created_at` / `updated_at` — creation and last-update timestamps (ISO 8601 UTC).

## Used by pages

- [[pages/tank-data|Tank Data]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]

## Notes

- Kind: **detail**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
