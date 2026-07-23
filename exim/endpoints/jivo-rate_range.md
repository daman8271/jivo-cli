---
title: "EXIM endpoint — GET /jivo-rate/range/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /jivo-rate/range/
category: jivo-rate
kind: read
resource: jivo_rate/jivorates
auth: bearer
---

# `GET /jivo-rate/range/`

> JIVO pack rates over a range.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/jivo-rate/range/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `from_date`, `to_date` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 1951,
    "pack_type": "Pouch 1 Ltr",
    "commodity": "SOYA",
    "rate": "153.000",
    "date": "2026-06-18",
    "created_by": "System"
  },
  {
    "id": 1952,
    "pack_type": "Pouch 1 Ltr",
    "commodity": "Mustard",
    "rate": "168.000",
    "date": "2026-06-18",
    "created_by": "System"
  },
  "...(+698 more of 700)"
]
```

## Field reference

- Response is an array of stored JIVO pack-rate rows for every pack/commodity combination on every day between `from_date` and `to_date` (25 combinations x days, e.g. 700 rows in the sample):
  - `id` — rate record id.
  - `pack_type` — retail pack format, e.g. "Pouch 1 Ltr".
  - `commodity` — oil type the rate applies to, e.g. "SOYA", "Mustard".
  - `rate` — JIVO selling rate for that pack, ₹ (string decimal, per pack unit).
  - `date` — ISO date (YYYY-MM-DD) the rate applies to.
  - `created_by` — who created the row; "System" for auto-fetched rates.

## Used by pages

- [[pages/jivo-rates|Jivo Rates]]

## Related endpoints

- [[endpoints/jivo-rate_fetch|`GET /jivo-rate/fetch/`]]

## Notes

- Kind: **read**. Resource permission group: `jivo_rate/jivorates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
