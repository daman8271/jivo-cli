---
title: "EXIM endpoint — POST /account/register/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /account/register/
category: account
kind: write
resource: user
auth: bearer
---

# `POST /account/register/`

> Create a new user.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/account/register/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |
| Request body | `{name,email,password,...}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/account_users|`GET /account/users/`]]
- [[endpoints/account_user_id|`GET /account/user/{id}/`]]

## Notes

- Kind: **write**. Resource permission group: `user`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
