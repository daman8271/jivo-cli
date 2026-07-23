---
title: "EXIM endpoint — GET /daily-price/highest-lowest/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /daily-price/highest-lowest/
category: daily-price
kind: read
resource: dailyprice/daily_price
auth: bearer
---

# `GET /daily-price/highest-lowest/`

> Highest & lowest commodity prices over a date range.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/daily-price/highest-lowest/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `end_date`, `start_date` |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "highest": {
    "id": 2603,
    "commodity_name": "Sunflower",
    "factory_price": "171.50",
    "packing_cost_kg": "185.50",
    "with_gst_kg": "194.78",
    "with_gst_ltr": "177.25",
    "date": "2026-07-14",
    "created_by": "System"
  },
  "lowest": {
    "id": 2382,
    "commodity_name": "Ricebran DO",
    "factory_price": "137.28",
    "packing_cost_kg": "151.28",
    "with_gst_kg": "158.84",
    "with_gst_ltr": "144.54",
    "date": "2026-06-25",
    "created_by": "System"
  }
}
```

## Field reference

- `highest` / `lowest` — the single price record with the highest and lowest factory price inside `start_date`..`end_date`. Each record:
  - `id` — daily-price record id.
  - `commodity_name` — oil/commodity name, e.g. "Sunflower", "Ricebran DO".
  - `factory_price` — ex-factory price, ₹ per kg (string decimal).
  - `packing_cost_kg` — price including packing cost, ₹ per kg.
  - `with_gst_kg` — price with GST, ₹ per kg.
  - `with_gst_ltr` — price with GST, ₹ per litre.
  - `date` — ISO date (YYYY-MM-DD) the price was recorded.
  - `created_by` — who created the row; "System" for auto-fetched prices.

## Used by pages

- [[pages/daily-price|Daily Price]]

## Related endpoints

- [[endpoints/daily-price_db-list|`GET /daily-price/db-list/`]]
- [[endpoints/daily-price_fetch|`GET /daily-price/fetch/`]]
- [[endpoints/daily-price_trends|`GET /daily-price/trends/`]]
- [[endpoints/daily-price_range|`GET /daily-price/range/`]]

## Notes

- Kind: **read**. Resource permission group: `dailyprice/daily_price`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
