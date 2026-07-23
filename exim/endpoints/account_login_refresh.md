---
title: "EXIM endpoint — POST /account/login/refresh/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /account/login/refresh/
category: auth
kind: write
resource: 
auth: bearer
---

# `POST /account/login/refresh/`

> Exchange refresh token for a new access token.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/account/login/refresh/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |
| Request body | `{refresh}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/account_login|`POST /account/login/`]]
- [[endpoints/account_logout|`POST /account/logout/`]]

## Notes

- Kind: **write**. Resource permission group: `n/a`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
