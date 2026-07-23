---
title: "EXIM endpoint — POST /license/advance-license-headers/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /license/advance-license-headers/
category: license
kind: write
resource: advancelicense*/dfialicense*
auth: bearer
---

# `POST /license/advance-license-headers/`

> Create advance-license header.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/license/advance-license-headers/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |
| Request body | `{header}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/license_advance-license-headers|`GET /license/advance-license-headers/`]]
- [[endpoints/license_dfia-license-header_list|`GET /license/dfia-license-header/list/`]]
- [[endpoints/license_advance-license-import-lines|`GET /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines|`GET /license/advance-license-export-lines/`]]
- [[endpoints/license_advance-license-import-lines_dropdown|`GET /license/advance-license-import-lines/dropdown/`]]
- [[endpoints/post_license_advance-license-import-lines|`POST /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines_create|`POST /license/advance-license-export-lines/create/`]]
- [[endpoints/license_dfia-license-header_create|`POST /license/dfia-license-header/create/`]]

## Notes

- Kind: **write**. Resource permission group: `advancelicense*/dfialicense*`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
