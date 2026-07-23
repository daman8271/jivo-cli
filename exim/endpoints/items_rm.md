---
title: "EXIM endpoint — GET /items/rm/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /items/rm/
category: items
kind: read
resource: rmproducts/fgproducts
auth: bearer
---

# `GET /items/rm/`

> Raw-material item master (SAP-synced).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/items/rm/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "count": 23,
  "items": [
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
    },
    {
      "id": 43,
      "item_code": "RM0000002",
      "item_name": "CANOLA COLD PRESS LOOSE OIL OLD",
      "category": "OIL",
      "sal_factor2": "1.000000",
      "u_tax_rate": 0,
      "deleted": "N",
      "u_variety": "COLD PRESS",
      "sal_pack_un": "1.000000",
      "u_brand": "JIVO",
      "u_unit": "OIL",
      "u_sub_group": "CANOLA",
      "total_trans_value": "2279043.754900",
      "total_in_qty": "12222299.642900",
      "total_out_qty": "12206016.667300",
      "total_qty": "16282.975600",
      "rate": "139.000000"
    },
    "...(+21 more of 23)"
  ]
}
```

## Field reference

- `count` — number of raw-material items in the master (23 in sample).
- `items[]` — one entry per SAP-synced RM item:
  - `id` — internal EXIM database id.
  - `item_code` — SAP item code, `RM…` prefix for raw materials (e.g. `RM0000001`).
  - `item_name` — SAP item description (e.g. `LOOSE REFINED OLIVE OIL`).
  - `category` — item category from SAP (`OIL`).
  - `u_variety` — oil variety user-field (`POMACE`, `COLD PRESS`, …); feeds `/items/rm/varieties/`.
  - `u_brand` — brand user-field (`JIVO`).
  - `u_unit` — unit group user-field (`OIL`).
  - `u_sub_group` — sub-group user-field, the oil family (`OLIVE`, `CANOLA`).
  - `u_tax_rate` — GST rate in % (5 or 0).
  - `sal_factor2` — sales conversion factor (pieces per pack; `1.000000` for loose oil).
  - `sal_pack_un` — pack size per unit (`1.000000`).
  - `deleted` — SAP soft-delete flag, `"N"` = active.
  - `total_in_qty` / `total_out_qty` — cumulative inward / outward transaction quantity in kg.
  - `total_qty` — current on-hand quantity in kg (`in − out`).
  - `total_trans_value` — net transaction value in ₹.
  - `rate` — current per-kg rate in ₹ (e.g. `141.000000`).

## Used by pages

- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]]
- [[pages/sync-raw-material|Sync Raw Material]]

## Related endpoints

- [[endpoints/items_fg|`GET /items/fg/`]]
- [[endpoints/items_rm_summary|`GET /items/rm/summary/`]]
- [[endpoints/items_rm_varieties|`GET /items/rm/varieties/`]]

## Notes

- Kind: **read**. Resource permission group: `rmproducts/fgproducts`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
