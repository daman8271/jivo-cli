---
title: "EXIM endpoint — GET /items/fg/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /items/fg/
category: items
kind: read
resource: rmproducts/fgproducts
auth: bearer
---

# `GET /items/fg/`

> Finished-goods item master (SAP-synced).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/items/fg/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "count": 331,
  "items": [
    {
      "id": 48746,
      "item_code": "FG0000424",
      "item_name": "COLD PRESS SUNFLOWER 1 LTR 24 PCS",
      "category": "OIL",
      "sal_factor2": "24.000000",
      "u_tax_rate": 5,
      "deleted": "N",
      "u_variety": "SUNFLOWER",
      "sal_pack_un": "1.000000",
      "u_brand": "JIVO",
      "u_unit": "OIL",
      "u_sub_group": "1203007- DOCK TIN SHED (GUPTA GODOWN)"
    },
    {
      "id": 44271,
      "item_code": "FG0000375",
      "item_name": "SO OLIVE OIL 5LTR TIN 4 PCS",
      "category": "OIL",
      "sal_factor2": "4.000000",
      "u_tax_rate": 5,
      "deleted": "N",
      "u_variety": "OLIVE",
      "sal_pack_un": "5.000000",
      "u_brand": "JIVO",
      "u_unit": "OIL",
      "u_sub_group": "BLENDED"
    },
    "...(+329 more of 331)"
  ]
}
```

## Field reference

- `count` — number of finished-goods items in the master (331 in sample).
- `items[]` — one entry per SAP-synced FG item:
  - `id` — internal EXIM database id.
  - `item_code` — SAP item code, `FG…` prefix for finished goods (e.g. `FG0000424`).
  - `item_name` — SAP item description including pack (e.g. `COLD PRESS SUNFLOWER 1 LTR 24 PCS`).
  - `category` — item category from SAP (`OIL`).
  - `u_variety` — oil variety user-field (`SUNFLOWER`, `OLIVE`, …).
  - `u_brand` — brand user-field (`JIVO`).
  - `u_unit` — unit group user-field (`OIL`).
  - `u_sub_group` — sub-group user-field; usually oil family (`OLIVE`, `BLENDED`) but can hold a warehouse label from SAP (e.g. `1203007- DOCK TIN SHED (GUPTA GODOWN)`).
  - `u_tax_rate` — GST rate in % (5).
  - `sal_factor2` — pieces per case/pack (`24.000000` = 24 pcs, `4.000000` = 4 pcs).
  - `sal_pack_un` — pack size per piece in litres (`1.000000` = 1 L, `5.000000` = 5 L tin).
  - `deleted` — SAP soft-delete flag, `"N"` = active.

## Used by pages

- [[pages/sync-finished-goods|Sync Finished Goods]]

## Related endpoints

- [[endpoints/items_rm|`GET /items/rm/`]]
- [[endpoints/items_rm_summary|`GET /items/rm/summary/`]]
- [[endpoints/items_rm_varieties|`GET /items/rm/varieties/`]]

## Notes

- Kind: **read**. Resource permission group: `rmproducts/fgproducts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
