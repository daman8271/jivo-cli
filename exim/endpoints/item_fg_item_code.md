---
title: "EXIM endpoint — GET /item/fg/{item_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /item/fg/{item_code}/
category: item
kind: detail
resource: rmproducts/fgproducts
auth: bearer
---

# `GET /item/fg/{item_code}/`

> Single finished-good item detail.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/item/fg/{item_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `item_code` |

## Response — real sample (trimmed)

```json
{
  "id": 48655,
  "item_code": "FG0000412",
  "item_name": "JIVO PREMIUM OLIVE OIL 1 LTR 16 PCS",
  "category": "OIL",
  "sal_factor2": "16.000000",
  "u_tax_rate": 5,
  "deleted": "N",
  "u_variety": "EXTRA VIRGIN",
  "sal_pack_un": "1.000000",
  "u_brand": "JIVO",
  "u_unit": "OIL",
  "u_sub_group": "OLIVE"
}
```

## Field reference

- `id` — internal EXIM database id.
- `item_code` — SAP item code, `FG…` prefix for finished goods (path parameter echoed back).
- `item_name` — SAP item description including pack (e.g. `JIVO PREMIUM OLIVE OIL 1 LTR 16 PCS`).
- `category` — item category from SAP (`OIL`).
- `u_variety` — oil variety user-field (`EXTRA VIRGIN`).
- `u_brand` — brand user-field (`JIVO`).
- `u_unit` — unit group user-field (`OIL`).
- `u_sub_group` — sub-group user-field, the oil family (`OLIVE`).
- `u_tax_rate` — GST rate in % (5).
- `sal_factor2` — pieces per case/pack (`16.000000` = 16 pcs).
- `sal_pack_un` — pack size per piece in litres (`1.000000` = 1 L).
- `deleted` — SAP soft-delete flag, `"N"` = active.

## Used by pages

- [[pages/sync-finished-goods|Sync Finished Goods]]

## Related endpoints

- [[endpoints/item_rm_item_code|`GET /item/rm/{item_code}/`]]
- [[endpoints/delete_item_rm_item_code|`DELETE /item/rm/{item_code}/`]]
- [[endpoints/delete_item_fg_item_code|`DELETE /item/fg/{item_code}/`]]

## Notes

- Kind: **detail**. Resource permission group: `rmproducts/fgproducts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
