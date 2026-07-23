---
title: "EXIM endpoint — GET /tank/in-tank-items/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /tank/in-tank-items/
category: tank
kind: read
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `GET /tank/in-tank-items/`

> Distinct item codes currently in tanks.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/tank/in-tank-items/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "item_code": "RM00CN"
  },
  {
    "item_code": "RM00MDEO"
  },
  "...(+26 more of 28)"
]
```

## Field reference

- `item_code` — distinct tank-item code with stock currently in a tank (e.g. `RM00CN`); feeds the item picker on In Tank Breakdown, and is the `item_code` param accepted by `GET /tank/item-wise-average/`.

## Used by pages

- [[pages/in-tank-breakdown|In Tank Breakdown]]

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
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
