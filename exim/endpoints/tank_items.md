---
title: "EXIM endpoint — GET /tank/items/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/items/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/items/`

> Tank item master (code, name, category, colour).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/items/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": "6bdeafc4-be36-490a-bf9e-c063ae8eb8c6",
    "tank_item_code": "RMSESMT",
    "tank_item_name": "SESAME TOASTED",
    "category": "SESAME",
    "is_active": true,
    "created_at": "2026-03-16T09:48:47.923091Z",
    "created_by": "admin@exim.com",
    "color": "#3498db"
  },
  {
    "id": "c6420d4c-c736-4f5e-990b-7771b059f1ac",
    "tank_item_code": "RM0SESM",
    "tank_item_name": "SESAME",
    "category": "SESAME",
    "is_active": true,
    "created_at": "2026-03-16T09:47:40.007407Z",
    "created_by": "admin@exim.com",
    "color": "#3498db"
  },
  "...(+49 more of 51)"
]
```

## Field reference

- `id` — tank item UUID.
- `tank_item_code` — item code (e.g. `RMSESMT`); referenced as `item_code` on tanks, logs, and averages.
- `tank_item_name` — display name (e.g. SESAME TOASTED).
- `category` — oil category grouping (e.g. `SESAME`).
- `is_active` — whether the item is available for use (boolean).
- `created_at` — record creation timestamp (ISO 8601 UTC).
- `created_by` — email of the user who created the item.
- `color` — hex colour used for this item in tank-monitoring charts (shared per category in the sample).

## Used by pages

- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/stock-status|Stock Status]]
- [[pages/tank-data|Tank Data]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]
- [[endpoints/tank_tank_code|`GET /tank/{tank_code}/`]]

## Notes

- Kind: **read**. Resource permission group: `tankdata/tankitem/tanklog`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
