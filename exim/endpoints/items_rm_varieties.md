---
title: "EXIM endpoint — GET /items/rm/varieties/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /items/rm/varieties/
category: items
kind: read
resource: rmproducts/fgproducts
auth: bearer
---

# `GET /items/rm/varieties/`

> Distinct raw-material varieties.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/items/rm/varieties/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "varieties": [
    "COLD PRESS",
    "CRUDE",
    "...(+11 more of 13)"
  ]
}
```

## Field reference

- `varieties[]` — distinct `u_variety` values across the RM item master (13 total: `COLD PRESS`, `CRUDE`, …). Plain string list, used to populate variety filter dropdowns.

## Used by pages

- [[pages/sync-raw-material|Sync Raw Material]]

## Related endpoints

- [[endpoints/items_fg|`GET /items/fg/`]]
- [[endpoints/items_rm|`GET /items/rm/`]]
- [[endpoints/items_rm_summary|`GET /items/rm/summary/`]]

## Notes

- Kind: **read**. Resource permission group: `rmproducts/fgproducts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
