---
title: "EXIM endpoint — PATCH /tank/{tank_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: PATCH
path: /tank/{tank_code}/
category: tank
kind: write
resource: tankdata/tankitem/tanklog
auth: bearer
---

# `PATCH /tank/{tank_code}/`

> Update a tank.

## Request

| | |
|---|---|
| Method | `PATCH` |
| URL | `https://eximbe.jivo.in/tank/{tank_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `tank_code` |
| Request body | `{fields}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/tank|`GET /tank/`]]
- [[endpoints/tank_capacity-insights|`GET /tank/capacity-insights/`]]
- [[endpoints/tank_in-tank-items|`GET /tank/in-tank-items/`]]
- [[endpoints/tank_item-wise-average|`GET /tank/item-wise-average/`]]
- [[endpoints/tank_item-wise-summary|`GET /tank/item-wise-summary/`]]
- [[endpoints/tank_items|`GET /tank/items/`]]
- [[endpoints/tank_log|`GET /tank/log/`]]
- [[endpoints/tank_tank-summary|`GET /tank/tank-summary/`]]

## Notes

- Kind: **write**. Resource permission group: `tankdata/tankitem/tanklog`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
