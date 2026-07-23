---
title: "EXIM endpoint — DELETE /party/{card_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: DELETE
path: /party/{card_code}/
category: party
kind: write
resource: party
auth: bearer
---

# `DELETE /party/{card_code}/`

> Delete a party.

## Request

| | |
|---|---|
| Method | `DELETE` |
| URL | `https://eximbe.jivo.in/party/{card_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `card_code` |
| Request body | `-` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/party_card_code|`GET /party/{card_code}/`]]

## Notes

- Kind: **write**. Resource permission group: `party`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
