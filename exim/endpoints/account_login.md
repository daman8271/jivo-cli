---
title: "EXIM endpoint — POST /account/login/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /account/login/
category: auth
kind: write
resource: 
auth: bearer
---

# `POST /account/login/`

> Authenticate; returns access+refresh+permissions.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/account/login/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |
| Request body | `{email,password}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/account_login_refresh|`POST /account/login/refresh/`]]
- [[endpoints/account_logout|`POST /account/logout/`]]

## Notes

- Kind: **write**. Resource permission group: `n/a`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
