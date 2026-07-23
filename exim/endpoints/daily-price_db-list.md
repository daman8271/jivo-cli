---
title: "EXIM endpoint — GET /daily-price/db-list/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /daily-price/db-list/
category: daily-price
kind: read
resource: dailyprice/daily_price
auth: bearer
---

# `GET /daily-price/db-list/`

> Historical daily commodity factory-price records (optionally for a date).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/daily-price/db-list/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `date` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 2631,
    "commodity_name": "Soya DO",
    "factory_price": "147.40",
    "packing_cost_kg": "161.40",
    "with_gst_kg": "169.47",
    "with_gst_ltr": "154.22",
    "date": "2026-07-17",
    "created_by": "System"
  },
  {
    "id": 2632,
    "commodity_name": "Soya Refined",
    "factory_price": "147.30",
    "packing_cost_kg": "161.30",
    "with_gst_kg": "169.37",
    "with_gst_ltr": "154.12",
    "date": "2026-07-17",
    "created_by": "System"
  },
  "...(+10 more of 12)"
]
```

## Field reference

- Response is an array of stored daily-price rows (one per commodity per day; pass `date` to get a single day's set of 12):
  - `id` — daily-price record id.
  - `commodity_name` — oil/commodity name, e.g. "Soya DO", "Soya Refined".
  - `factory_price` — ex-factory price, ₹ per kg (string decimal).
  - `packing_cost_kg` — price including packing cost, ₹ per kg.
  - `with_gst_kg` — price with GST, ₹ per kg.
  - `with_gst_ltr` — price with GST, ₹ per litre.
  - `date` — ISO date (YYYY-MM-DD) the price applies to.
  - `created_by` — who created the row; "System" for auto-fetched prices.

## Used by pages

- [[pages/daily-price|Daily Price]]

## Related endpoints

- [[endpoints/daily-price_fetch|`GET /daily-price/fetch/`]]
- [[endpoints/daily-price_highest-lowest|`GET /daily-price/highest-lowest/`]]
- [[endpoints/daily-price_trends|`GET /daily-price/trends/`]]
- [[endpoints/daily-price_range|`GET /daily-price/range/`]]

## Notes

- Kind: **read**. Resource permission group: `dailyprice/daily_price`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
