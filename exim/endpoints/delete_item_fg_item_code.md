---
title: "EXIM endpoint — DELETE /item/fg/{item_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: DELETE
path: /item/fg/{item_code}/
category: item
kind: write
resource: rmproducts/fgproducts
auth: bearer
---

# `DELETE /item/fg/{item_code}/`

> Delete an FG item.

## Request

| | |
|---|---|
| Method | `DELETE` |
| URL | `https://eximbe.jivo.in/item/fg/{item_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `item_code` |
| Request body | `-` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/item_rm_item_code|`GET /item/rm/{item_code}/`]]
- [[endpoints/item_fg_item_code|`GET /item/fg/{item_code}/`]]
- [[endpoints/delete_item_rm_item_code|`DELETE /item/rm/{item_code}/`]]

## Notes

- Kind: **write**. Resource permission group: `rmproducts/fgproducts`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
