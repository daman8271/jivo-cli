---
title: "EXIM endpoint — POST /account/logout/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /account/logout/
category: auth
kind: write
resource: 
auth: bearer
---

# `POST /account/logout/`

> Invalidate the refresh token.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/account/logout/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |
| Request body | `{refresh_token}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/account_login|`POST /account/login/`]]
- [[endpoints/account_login_refresh|`POST /account/login/refresh/`]]

## Notes

- Kind: **write**. Resource permission group: `n/a`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
