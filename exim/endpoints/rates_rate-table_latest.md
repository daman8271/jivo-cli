---
title: "EXIM endpoint — GET /rates/rate-table/latest/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /rates/rate-table/latest/
category: rates
kind: read
resource: exim_rates
auth: bearer
---

# `GET /rates/rate-table/latest/`

> Composite latest rate table (commodities + rows).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/rates/rate-table/latest/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "commodities": [
    "Soya Refined",
    "Cottonseed Refined",
    "...(+2 more of 4)"
  ],
  "rows": [
    {
      "pack_size": "Pouch 1 Ltr",
      "rates": {
        "Soya Refined": 145.87,
        "Ricebran Refined": 149.49,
        "Mustard Refined": 166.08
      }
    },
    {
      "pack_size": "Pouch 750 Gm",
      "rates": {
        "Soya Refined": 120.23
      }
    },
    "...(+5 more of 7)"
  ]
}
```

## Field reference

- `commodities` — column headers: list of commodity names covered by the latest rate table (e.g. "Soya Refined", "Cottonseed Refined").
- `rows` — one row per pack size:
  - `pack_size` — packing type plus size label (e.g. "Pouch 1 Ltr", "Pouch 750 Gm").
  - `rates` — map of commodity name to latest basic price for that pack, ₹ per litre (e.g. "Soya Refined": 145.87); a commodity missing from the map has no rate for that pack size.

## Used by pages

- [[pages/our-rates|Our Rates]]

## Related endpoints

- [[endpoints/rates_basic-rate|`GET /rates/basic-rate/`]]
- [[endpoints/rates_commodity|`GET /rates/commodity/`]]
- [[endpoints/rates_market-rate_get|`GET /rates/market-rate/get/`]]
- [[endpoints/rates_market-rate_latest|`GET /rates/market-rate/latest/`]]
- [[endpoints/rates_packing|`GET /rates/packing/`]]

## Notes

- Kind: **read**. Resource permission group: `exim_rates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
