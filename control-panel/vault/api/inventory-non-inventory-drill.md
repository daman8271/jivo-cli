---
endpoint: /inventory/non-inventory/api/drill/
method: GET
auth: session + XHR header (X-Requested-With) + X-CSRFToken
readonly: true
used_by: [non-moving-stock]
tags: [jivo, api, inventory, ageing]
---
# `GET /inventory/non-inventory/api/drill/`

## Purpose
Drill-down for a **single finished good** on the [[non-moving-stock]] page: breaks that item's on-hand stock out **by warehouse** (code, name, qty, and the lot production date). Fired when a user expands/clicks an item row.

## Request
| Param | Type | Meaning |
|---|---|---|
| `schema` | `jivo_oil` \| `jivo_mart` \| `jivo_beverages` | Company DB. Same schema as the parent page. |
| `item` | string (ItemCode) | SAP FG code to drill (e.g. `FG0000441`). |
| `whs` | string (CSV) *optional* | Comma-separated warehouse codes to restrict to — only appended when a warehouse filter is active on the page. |

Built in page JS as `?schema=<s>&item=<code>[&whs=<a,b>]`.

## Response
HTTP 200 · `application/json`. Top key `data` — an array of per-warehouse rows:

| Field | Type | Meaning |
|---|---|---|
| `WhsCode` | string | Warehouse code (see [[warehouses]]). |
| `WhsName` | string | Warehouse full name. |
| `Qty` | number | On-hand physical units in that warehouse. |
| `ProdDate` | date | Production date of the lot held there. |

Sample (`schema=jivo_oil&item=FG0000441`):
```json
{"data":[{"WhsCode":"BH-PF","WhsName":"Bhakharpur Production Finished 1st Floor",
  "Qty":23170.0,"ProdDate":"2026-06-01"}]}
```

## Used by
- [[non-moving-stock]] — per-item warehouse breakdown expander.

## Notes
- Read-only. Returns only warehouses where the item currently has stock.
