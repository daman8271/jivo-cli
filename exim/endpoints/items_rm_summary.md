---
title: "EXIM endpoint — GET /items/rm/summary/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /items/rm/summary/
category: items
kind: read
resource: rmproducts/fgproducts
auth: bearer
---

# `GET /items/rm/summary/`

> Aggregate summary of raw-material items (counts, qty, value).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/items/rm/summary/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "summary": {
    "total_count": 23,
    "total_qty": 610957.2899,
    "avg_rate": 350.74,
    "total_trans_value": 93912353.0541
  }
}
```

## Field reference

- `summary` — single aggregate object over all raw-material items:
  - `total_count` — number of RM items in the master (23).
  - `total_qty` — combined on-hand quantity across all RM items, in kg (610,957.29 ≈ 611 MTS).
  - `avg_rate` — average per-kg rate in ₹ (350.74).
  - `total_trans_value` — combined net transaction value in ₹ (93,912,353 ≈ ₹9.39 Cr).

## Used by pages

- [[pages/sync-raw-material|Sync Raw Material]]

## Related endpoints

- [[endpoints/items_fg|`GET /items/fg/`]]
- [[endpoints/items_rm|`GET /items/rm/`]]
- [[endpoints/items_rm_varieties|`GET /items/rm/varieties/`]]

## Notes

- Kind: **read**. Resource permission group: `rmproducts/fgproducts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
