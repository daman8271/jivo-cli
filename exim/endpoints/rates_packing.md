---
title: "EXIM endpoint — GET /rates/packing/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /rates/packing/
category: rates
kind: read
resource: exim_rates
auth: bearer
---

# `GET /rates/packing/`

> Packing types with packing margins.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/rates/packing/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 1,
    "packing_name": "Pouch",
    "packing_margin": "10.00000",
    "created_by": "super@exim"
  },
  {
    "id": 2,
    "packing_name": "Tin",
    "packing_margin": "14.00000",
    "created_by": "super@exim"
  },
  "...(+1 more of 3)"
]
```

## Field reference

- `id` — packing type id; referenced as `packing_type` in basic-rate rows.
- `packing_name` — packing format name (e.g. "Pouch", "Tin").
- `packing_margin` — margin added to the factory rate for this packing, ₹ per kg (string, e.g. "10.00000" for Pouch, "14.00000" for Tin).
- `created_by` — user who created the packing entry.

## Used by pages

- [[pages/our-rates|Our Rates]]

## Related endpoints

- [[endpoints/rates_basic-rate|`GET /rates/basic-rate/`]]
- [[endpoints/rates_commodity|`GET /rates/commodity/`]]
- [[endpoints/rates_market-rate_get|`GET /rates/market-rate/get/`]]
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]]
- [[endpoints/rates_rate-table_latest|`GET /rates/rate-table/latest/`]]

## Notes

- Kind: **read**. Resource permission group: `exim_rates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
