---
title: "EXIM endpoint — GET /daily-price/trends/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /daily-price/trends/
category: daily-price
kind: read
resource: dailyprice/daily_price
auth: bearer
---

# `GET /daily-price/trends/`

> Daily-price trend series (labels + datasets) for charting over a range.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/daily-price/trends/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `end_date`, `start_date` |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "labels": [
    "Jun 18",
    "Jun 20",
    "...(+26 more of 28)"
  ],
  "datasets": [
    {
      "label": "Soya DO",
      "data": [
        145.1,
        145.1,
        "...(+26 more of 28)"
      ]
    },
    {
      "label": "Soya Refined",
      "data": [
        146.0,
        146.0,
        "...(+26 more of 28)"
      ]
    },
    "...(+10 more of 12)"
  ]
}
```

## Field reference

- `labels[]` — x-axis date labels ("Jun 18" style, one per day with data) between `start_date` and `end_date`.
- `datasets[]` — one chart series per commodity (12 in the sample):
  - `label` — commodity name, e.g. "Soya DO", "Soya Refined".
  - `data[]` — factory price in ₹ per kg for each label date, aligned index-for-index with `labels`.

## Used by pages

- [[pages/daily-price|Daily Price]]
- [[pages/dashboard|Dashboard]]

## Related endpoints

- [[endpoints/daily-price_db-list|`GET /daily-price/db-list/`]]
- [[endpoints/daily-price_fetch|`GET /daily-price/fetch/`]]
- [[endpoints/daily-price_highest-lowest|`GET /daily-price/highest-lowest/`]]
- [[endpoints/daily-price_range|`GET /daily-price/range/`]]

## Notes

- Kind: **read**. Resource permission group: `dailyprice/daily_price`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
