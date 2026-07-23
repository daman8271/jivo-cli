---
title: "EXIM endpoint — GET /daily-price/range/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /daily-price/range/
category: daily-price
kind: read
resource: dailyprice/daily_price
auth: bearer
---

# `GET /daily-price/range/`

> Daily prices over a from/to range.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/daily-price/range/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `from_date`, `to_date` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 2307,
    "commodity_name": "Soya DO",
    "factory_price": "145.10",
    "packing_cost_kg": "159.10",
    "with_gst_kg": "167.06",
    "with_gst_ltr": "152.02",
    "date": "2026-06-18",
    "created_by": "System"
  },
  {
    "id": 2308,
    "commodity_name": "Soya Refined",
    "factory_price": "146.00",
    "packing_cost_kg": "160.00",
    "with_gst_kg": "168.00",
    "with_gst_ltr": "152.88",
    "date": "2026-06-18",
    "created_by": "System"
  },
  "...(+334 more of 336)"
]
```

## Field reference

- Response is an array of daily-price rows for every commodity on every day between `from_date` and `to_date` (12 commodities x days, e.g. 336 rows in the sample):
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

- [[endpoints/daily-price_db-list|`GET /daily-price/db-list/`]]
- [[endpoints/daily-price_fetch|`GET /daily-price/fetch/`]]
- [[endpoints/daily-price_highest-lowest|`GET /daily-price/highest-lowest/`]]
- [[endpoints/daily-price_trends|`GET /daily-price/trends/`]]

## Notes

- Kind: **read**. Resource permission group: `dailyprice/daily_price`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
