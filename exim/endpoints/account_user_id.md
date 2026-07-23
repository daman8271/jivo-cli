---
title: "EXIM endpoint — GET /account/user/{id}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /account/user/{id}/
category: account
kind: detail
resource: user
auth: bearer
---

# `GET /account/user/{id}/`

> Single user detail.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/account/user/{id}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `id` |

## Response — real sample (trimmed)

```json
{
  "id": 34,
  "name": "Daman",
  "email": "daman@exim.in"
}
```

## Field reference

- `id` — user account ID (matches the `{id}` path param).
- `name` — display name of the user.
- `email` — login email address for the account.

## Used by pages

- [[pages/users|Users]]

## Related endpoints

- [[endpoints/account_users|`GET /account/users/`]]
- [[endpoints/account_register|`POST /account/register/`]]

## Notes

- Kind: **detail**. Resource permission group: `user`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
