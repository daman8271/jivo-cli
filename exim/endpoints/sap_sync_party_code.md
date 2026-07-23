---
title: "EXIM endpoint — POST /sap_sync/party/{code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /sap_sync/party/{code}/
category: sap_sync
kind: sync
resource: open_grpos
auth: bearer
---

# `POST /sap_sync/party/{code}/`

> Trigger SAP vendor/party sync.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/sap_sync/party/{code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `code` |
| Request body | `-` |

## ⚠️ SYNC TRIGGER — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/sap_sync_open-grpos|`GET /sap_sync/open-grpos/`]]
- [[endpoints/sap_sync_rm_items|`POST /sap_sync/rm/items/`]]
- [[endpoints/sap_sync_fg_items|`POST /sap_sync/fg/items/`]]

## Notes

- Kind: **sync**. Resource permission group: `open_grpos`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
