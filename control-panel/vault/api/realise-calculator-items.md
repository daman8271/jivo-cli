---
endpoint: /realise/api/realise-calculator/items/
method: GET
auth: session + XHR header (X-Requested-With / X-CSRFToken)
readonly: true
used_by: [realise-calculator]
tags: [jivo, api, calculator-ratelist]
---

# `GET /realise/api/realise-calculator/items/`

## Purpose
Serves the **SAP finished-goods item master** that powers the [[realise-calculator]] item picker (SKU / Size → Variety → Item cascade) and auto-fills Pcs/Box and Box Litres when an item is chosen. One flat list of all sellable FG items.

## Request
No query params. Requires the XHR header set (`X-Requested-With: XMLHttpRequest`); without it Django returns 401/403. Session cookie required.

## Response
HTTP **200**, `application/json` (~68 KB). Top-level keys:

- `status` — string, `"ok"`.
- `items` — array (**374** rows observed). Each item:

| Field | Type | Meaning |
|---|---|---|
| `code` | str | SAP item code, e.g. `FG0000185` |
| `name` | str | Full item description |
| `variety` | str | Oil variety group, e.g. `BLENDED` |
| `sku` | str | Pack size, e.g. `1 LTR` |
| `type` | str | SAP item classification flag — `P` or `C` |
| `litres_per_pack` | float | Litres per single piece |
| `pcs_per_box` | float | Pieces per box (SAP `SalFactor2`) → auto-fills Pcs/Box |
| `box_litres` | float | Total saleable litres per box → auto-fills Box Ltrs |

Trimmed 1-row sample:
```json
{"code":"FG0000185","name":"BB ROYAL BLENDED OIL OLIVE + RICE BRAN 1 LTR 20 PCS",
 "variety":"BLENDED","sku":"1 LTR","type":"P",
 "litres_per_pack":1.0,"pcs_per_box":20.0,"box_litres":20.0}
```

## Used by
[[realise-calculator]] (item picker + auto-fill of pcs/box & box litres)

## Notes
- Read-only GET; probed live (200, 374 items).
- `box_litres` = `litres_per_pack × pcs_per_box` in the samples seen.
- `type` (P/C) is shown as a coloured chip in the picker but does not affect the realise maths.
