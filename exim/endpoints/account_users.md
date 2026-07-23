---
title: "EXIM endpoint — GET /account/users/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /account/users/
category: account
kind: read
resource: user
auth: bearer
---

# `GET /account/users/`

> List of application user accounts (id, name, email).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/account/users/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 23,
    "name": "Karishma Soni",
    "email": "karishma@exim.com"
  },
  {
    "id": 26,
    "name": "Factory User",
    "email": "factory@exim.com"
  },
  "...(+10 more of 12)"
]
```

## Field reference

- `id` — user account ID; use with `GET /account/user/{id}/` for detail.
- `name` — display name of the user (person or role account, e.g. "Factory User").
- `email` — login email address for the account.

## Used by pages

- [[pages/users|Users]]

## Related endpoints

- [[endpoints/account_user_id|`GET /account/user/{id}/`]]
- [[endpoints/account_register|`POST /account/register/`]]

## Notes

- Kind: **read**. Resource permission group: `user`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
