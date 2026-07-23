---
title: "EXIM endpoint — GET /rates/market-rate/get/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /rates/market-rate/get/
category: rates
kind: read
resource: exim_rates
auth: bearer
---

# `GET /rates/market-rate/get/`

> Market rate rows over a date range.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/rates/market-rate/get/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `end_date`, `start_date` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 1,
    "commodity": 2,
    "factory_kg": "147.30",
    "with_packing": 161.3,
    "with_gst_kg": 169.365,
    "with_gst_ltr": 154.12230412230412,
    "date": "2026-07-18"
  },
  {
    "id": 2,
    "commodity": 1,
    "factory_kg": "147.40",
    "with_packing": 161.4,
    "with_gst_kg": 169.47,
    "with_gst_ltr": 154.2178542178542,
    "date": "2026-07-18"
  },
  "...(+10 more of 12)"
]
```

## Field reference

- `id` — market rate row id.
- `commodity` — id of the commodity this rate belongs to (FK to `GET /rates/commodity/`, e.g. 1 = Soya DO, 2 = Soya Refined).
- `factory_kg` — base factory-gate market rate, ₹ per kg (string, e.g. "147.30").
- `with_packing` — rate after adding the packing margin, ₹ per kg (e.g. 161.3).
- `with_gst_kg` — rate with packing plus GST, ₹ per kg (e.g. 169.365).
- `with_gst_ltr` — the same GST-inclusive rate converted to ₹ per litre using oil density (e.g. 154.12).
- `date` — rate date, ISO `YYYY-MM-DD`; rows are filtered by the `start_date`/`end_date` query params.

## Used by pages

- [[pages/market-rates|Market Rates]]
- [[pages/our-rates|Our Rates]]

## Related endpoints

- [[endpoints/rates_basic-rate|`GET /rates/basic-rate/`]]
- [[endpoints/rates_commodity|`GET /rates/commodity/`]]
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]]
- [[endpoints/rates_packing|`GET /rates/packing/`]]
- [[endpoints/rates_rate-table_latest|`GET /rates/rate-table/latest/`]]

## Notes

- Kind: **read**. Resource permission group: `exim_rates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
