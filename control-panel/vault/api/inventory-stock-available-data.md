---
endpoint: /inventory/stock-available/api/data/
method: GET
auth: session + XHR header (X-Requested-With) + X-CSRFToken
readonly: true
used_by: [stock-available]
tags: [jivo, api, inventory, stock]
---
# `GET /inventory/stock-available/api/data/`

## Purpose
Returns **live finished-goods on-hand stock** for one company, grouped both as product-type summaries (for the [[stock-available]] cards/KPIs) and as per-SKU × per-warehouse rows (for the drill-down table). Stock is computed as **In − Out** across the five finished-goods warehouses **GP-FG / BH-FG / BH-PF / BH-EC / BH-FU** — see [[warehouses]]. One call fully powers the page; all filtering (Premium/Commodity type, SKU multi-select) is done client-side.

## Request
Query params (GET, XHR header required):

| Param | Type | Meaning |
|---|---|---|
| `schema` | `jivo_oil` \| `jivo_mart` \| `jivo_beverages` | Which company DB to read. **Default `jivo_oil`** (page loads with the Jivo Oil segment active). Toggled by the company segment buttons. |

No date param — stock is a live snapshot ("as of now").

## Response
HTTP 200 · `application/json`. Single top-level key `data`, an object with:

| Key | Shape | Meaning |
|---|---|---|
| `warehouses` | string[] | The finished-goods warehouse codes columned in the table, in order: `["GP-FG","BH-FG","BH-PF","BH-EC","BH-FU"]`. See [[warehouses]]. |
| `products` | object[] | Type × sub-group **summary** rows (drive the cards + KPIs). |
| `items` | object[] | Per-SKU × per-warehouse **detail** rows (drive the drill table). |

`products[]` row:

| Field | Type | Meaning |
|---|---|---|
| `type` | string | `PREMIUM` / `COMMODITY` (oils); `DRINKS` / `WATER` / … (beverages). |
| `sub_group` | string | Product sub-group (OLIVE, CANOLA, MUSTARD, SOYABEAN…). |
| `qty` | number | On-hand physical units (bottles/jars/boxes as stocked). |
| `litres` | number | On-hand converted to litres (pack size × qty). Headline metric for oils. |
| `sku_count` | number | Distinct SKUs in this sub-group with stock. |

`items[]` row (per finished good):

| Field | Type | Meaning |
|---|---|---|
| `type`, `sub_group`, `variety` | string | Classification (e.g. PREMIUM / BLENDED / BB ROYAL). |
| `item_code` | string | SAP FG item code (e.g. `FG0000185`). |
| `item_name` | string | Full SAP item description. |
| `sku` | string | Pack size label (`1 LTR`, `5 LTR`…). |
| `wh` | object | `{warehouse_code: qty}` on-hand physical units per warehouse. |
| `wh_litres` | object | `{warehouse_code: litres}` on-hand litres per warehouse. |
| `grand_total` | number | Total on-hand units across the 5 warehouses. |
| `litres` | number | Total on-hand litres across the 5 warehouses. |

Trimmed sample (`schema=jivo_oil`):
```json
{"data":{
  "warehouses":["GP-FG","BH-FG","BH-PF","BH-EC","BH-FU"],
  "products":[{"type":"PREMIUM","sub_group":"CANOLA","qty":48008.55,"litres":173659.71,"sku_count":26}],
  "items":[{"type":"PREMIUM","sub_group":"BLENDED","variety":"BB ROYAL","item_code":"FG0000185",
    "item_name":"BB ROYAL BLENDED OIL OLIVE + RICE BRAN 1 LTR 20 PCS","sku":"1 LTR",
    "wh":{"GP-FG":60.0,"BH-FG":0.0,"BH-PF":0.0,"BH-EC":0.0,"BH-FU":0.0},
    "wh_litres":{"GP-FG":60.0,"BH-FG":0.0,"BH-PF":0.0,"BH-EC":0.0,"BH-FU":0.0},
    "grand_total":60.0,"litres":60.0}]
}}
```

## Used by
- [[stock-available]] — cards, Total/Premium/Commodity litre KPIs, and the per-SKU drill table.

## Notes
- Live snapshot; no history. Beverages payload flags its unit as **boxes** (oils use **litres**).
- Excel export lives at a **separate** route `GET /inventory/stock-available/export/?schema=` (server-side "Inventory Audit Report" pivot download — file response, **not probed**).
