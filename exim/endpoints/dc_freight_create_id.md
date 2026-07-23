---
title: "EXIM endpoint — POST /dc/freight/create/{id}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /dc/freight/create/{id}/
category: dc
kind: write
resource: domesticcontracts
auth: bearer
---

# `POST /dc/freight/create/{id}/`

> Add freight to a contract.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/dc/freight/create/{id}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `id` |
| Request body | `{freight}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/dc|`GET /dc/`]]
- [[endpoints/get_dc|`GET /dc/`]]
- [[endpoints/dc_dropdown|`GET /dc/dropdown/`]]
- [[endpoints/dc_contract_create|`POST /dc/contract/create/`]]
- [[endpoints/dc_loading_create_id|`POST /dc/loading/create/{id}/`]]

## Notes

- Kind: **write**. Resource permission group: `domesticcontracts`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
