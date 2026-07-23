---
title: "Authentication"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, exim, auth]
---

# Authentication

JWT (access + refresh) stored in the SPA's `localStorage`.

## Login
```http
POST https://eximbe.jivo.in/account/login/
Content-Type: application/json

{"email":"...","password":"..."}
```
Returns: `{ access, refresh, name, email, id, permissions }`.

## Authenticated requests
```
Authorization: Bearer <access_token>
```

## Refresh (on 401)
```http
POST https://eximbe.jivo.in/account/login/refresh/

{"refresh":"<refresh_token>"}
```
Returns `{ access }`.

## Logout
`POST /account/logout/` with `{refresh_token}` — invalidates the refresh token. **Do not call from tooling** (kills the session).

## Notes
- Local helper: `scripts/eximapi.py` (`login()`, `get(path, params)` with auto-refresh).
- Credentials (`EXIM_*`) live in the jivogpt root `.env` (gitignored; consolidated from `.secrets/creds.env` on 2026-07-19). Token cache stays in `.secrets/token.json`.

_Part of [[INDEX]]_

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
