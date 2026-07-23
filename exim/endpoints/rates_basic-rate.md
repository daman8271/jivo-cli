---
title: "EXIM endpoint — GET /rates/basic-rate/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /rates/basic-rate/
category: rates
kind: read
resource: exim_rates
auth: bearer
---

# `GET /rates/basic-rate/`

> Basic (our) rate rows over a date range.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/rates/basic-rate/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `end_date`, `start_date` |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "basic_rates": [
    {
      "id": 1,
      "basic_price_ltr": 145.8731458731459,
      "basic_price_kg": "160.300",
      "date": "2026-07-18",
      "packing_type": 1,
      "market_rate": 1
    },
    {
      "id": 2,
      "basic_price_ltr": 149.5131495131495,
      "basic_price_kg": "164.300",
      "date": "2026-07-18",
      "packing_type": 2,
      "market_rate": 1
    },
    "...(+10 more of 12)"
  ]
}
```

## Field reference

- `basic_rates` — array of computed "our rate" rows:
  - `id` — basic rate row id.
  - `basic_price_ltr` — our basic selling price, ₹ per litre (e.g. 145.87).
  - `basic_price_kg` — our basic selling price, ₹ per kg (string, e.g. "160.300").
  - `date` — rate date, ISO `YYYY-MM-DD`; rows are filtered by the `start_date`/`end_date` query params.
  - `packing_type` — id of the packing type priced (FK to `GET /rates/packing/`, e.g. 1 = Pouch).
  - `market_rate` — id of the underlying market rate row (FK to `GET /rates/market-rate/get/`) this basic price is derived from.

## Used by pages

- [[pages/our-rates|Our Rates]]

## Related endpoints

- [[endpoints/rates_commodity|`GET /rates/commodity/`]]
- [[endpoints/rates_market-rate_get|`GET /rates/market-rate/get/`]]
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]]
- [[endpoints/rates_packing|`GET /rates/packing/`]]
- [[endpoints/rates_rate-table_latest|`GET /rates/rate-table/latest/`]]

## Notes

- Kind: **read**. Resource permission group: `exim_rates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
