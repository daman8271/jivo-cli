---
title: "EXIM endpoint — GET /item/rm/{item_code}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /item/rm/{item_code}/
category: item
kind: detail
resource: rmproducts/fgproducts
auth: bearer
---

# `GET /item/rm/{item_code}/`

> Single raw-material item detail incl movement totals.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/item/rm/{item_code}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `item_code` |

## Response — real sample (trimmed)

```json
{
  "id": 689,
  "item_code": "RM0000001",
  "item_name": "LOOSE REFINED OLIVE OIL",
  "category": "OIL",
  "sal_factor2": "1.000000",
  "u_tax_rate": 5,
  "deleted": "N",
  "u_variety": "POMACE",
  "sal_pack_un": "1.000000",
  "u_brand": "JIVO",
  "u_unit": "OIL",
  "u_sub_group": "OLIVE",
  "total_trans_value": "4808.215100",
  "total_in_qty": "7894035.196000",
  "total_out_qty": "7894001.173300",
  "total_qty": "34.022700",
  "rate": "141.000000"
}
```

## Field reference

- `id` — internal EXIM database id.
- `item_code` — SAP item code, `RM…` prefix for raw materials (path parameter echoed back).
- `item_name` — SAP item description (e.g. `LOOSE REFINED OLIVE OIL`).
- `category` — item category from SAP (`OIL`).
- `u_variety` — oil variety user-field (`POMACE`).
- `u_brand` — brand user-field (`JIVO`).
- `u_unit` — unit group user-field (`OIL`).
- `u_sub_group` — sub-group user-field, the oil family (`OLIVE`).
- `u_tax_rate` — GST rate in % (5).
- `sal_factor2` — sales conversion factor (`1.000000` for loose oil).
- `sal_pack_un` — pack size per unit (`1.000000`).
- `deleted` — SAP soft-delete flag, `"N"` = active.
- `total_in_qty` / `total_out_qty` — cumulative inward / outward transaction quantity in kg.
- `total_qty` — current on-hand quantity in kg (`in − out`, here 34.02 kg).
- `total_trans_value` — net transaction value in ₹.
- `rate` — current per-kg rate in ₹ (141.00).

## Used by pages

- [[pages/sync-raw-material|Sync Raw Material]]

## Related endpoints

- [[endpoints/item_fg_item_code|`GET /item/fg/{item_code}/`]]
- [[endpoints/delete_item_rm_item_code|`DELETE /item/rm/{item_code}/`]]
- [[endpoints/delete_item_fg_item_code|`DELETE /item/fg/{item_code}/`]]

## Notes

- Kind: **detail**. Resource permission group: `rmproducts/fgproducts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
