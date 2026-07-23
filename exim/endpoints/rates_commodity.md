---
title: "EXIM endpoint — GET /rates/commodity/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /rates/commodity/
category: rates
kind: read
resource: exim_rates
auth: bearer
---

# `GET /rates/commodity/`

> Commodity master with margin rates.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/rates/commodity/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 1,
    "commodity": "Soya DO",
    "margin_rate": null,
    "created_by": "super@exim.com"
  },
  {
    "id": 2,
    "commodity": "Soya Refined",
    "margin_rate": "3.00",
    "created_by": "super@exim.com"
  },
  "...(+10 more of 12)"
]
```

## Field reference

- `id` — commodity id; referenced as `commodity` in market-rate rows.
- `commodity` — commodity name (e.g. "Soya DO", "Soya Refined").
- `margin_rate` — margin added on top of the market rate for this commodity, ₹ per kg (string, e.g. "3.00"); `null` when no margin applies.
- `created_by` — email of the user who created the commodity entry.

## Used by pages

- [[pages/market-rates|Market Rates]]
- [[pages/our-rates|Our Rates]]

## Related endpoints

- [[endpoints/rates_basic-rate|`GET /rates/basic-rate/`]]
- [[endpoints/rates_market-rate_get|`GET /rates/market-rate/get/`]]
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]]
- [[endpoints/rates_packing|`GET /rates/packing/`]]
- [[endpoints/rates_rate-table_latest|`GET /rates/rate-table/latest/`]]

## Notes

- Kind: **read**. Resource permission group: `exim_rates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
