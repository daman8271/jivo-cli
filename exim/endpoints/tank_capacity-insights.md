---
title: "EXIM endpoint — GET /tank/capacity-insights/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/capacity-insights/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/capacity-insights/`

> Overall tank capacity fill/empty percentages.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/capacity-insights/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "total_capacity": 1351500.0,
  "filled_capacity": 892500.0,
  "filled_percentage": 66.04,
  "empty_capacity": 459000.0,
  "empty_percentage": 33.96
}
```

## Field reference

- `total_capacity` — combined capacity of all tanks, in litres (1,351,500 L in the sample).
- `filled_capacity` — litres currently held across all tanks.
- `filled_percentage` — filled share of total capacity, % (66.04).
- `empty_capacity` — free headroom across all tanks, litres (`total_capacity - filled_capacity`).
- `empty_percentage` — empty share of total capacity, % (33.96); sums with `filled_percentage` to 100.

## Used by pages

- [[pages/dashboard|Dashboard]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
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
