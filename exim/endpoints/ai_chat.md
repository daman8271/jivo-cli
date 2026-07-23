---
title: "EXIM endpoint — POST /ai/chat/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /ai/chat/
category: ai
kind: write
resource: 
auth: bearer
---

# `POST /ai/chat/`

> AI assistant chat over EXIM data.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/ai/chat/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |
| Request body | `{message}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- _(none)_

## Notes

- Kind: **write**. Resource permission group: `n/a`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
