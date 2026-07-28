---
endpoint: /realise/api/sales-flow/open-items/
method: POST
auth: session + X-CSRFToken
readonly: true
used_by: [sales-flow]
tags: [jivo, api, sales, flow-dispatch]
---
# `POST /realise/api/sales-flow/open-items/`

## Purpose
Drill-down for a **single open** Sales Quotation or Sales Order: returns its still-open line items (the quantities not yet delivered/invoiced). Powers the "open items" modal on [[sales-flow]] when a green **Open** document number is clicked.

## Request
JSON body (`Content-Type: application/json` + `X-CSRFToken`):

| Field | Type | Meaning |
|---|---|---|
| `doc_type` | string | `"order"` or `"quotation"` — which document kind to open. |
| `doc_no` | string | The SAP document number (from the row's `order_no`/`quotation_no`). |
| `company` | string | `"oil"` or `"beverages"` — the SAP company DB (must match the row). |

Example: `{"doc_type":"order","doc_no":"1726076736","company":"oil"}`

## Response
HTTP 200. Top-level keys:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` (or `"error"` + `error`). |
| `doc_type` / `doc_no` / `company` | string | Echo of the request. |
| `measure` | string | `"Litres"` (oil) / `"Boxes"` (beverages). |
| `party` | string | Customer name on the document. |
| `items` | array | Open line items (see below). |
| `total_open` | number | Sum of open quantity across items (in `measure` units). |
| `total_pcs` | number | Sum of open pieces across items. |

Each `items[]` object:
- `code` (string) — FG item code (e.g. `FG0000009`).
- `name` (string) — item description · `label` (string) — `"code — name"` convenience string.
- `open_qty` (number) — open quantity in `measure` units (Litres/Boxes).
- `open_pcs` (number) — open pieces (units/cases).

TRIMMED sample (order 1726076736, oil):
```json
{
  "status": "ok", "doc_type": "order", "doc_no": "1726076736",
  "company": "oil", "measure": "Litres", "party": "JIVO MART PVT LTD",
  "items": [{
    "code": "FG0000009", "name": "EXTRA LIGHT OLIVE 5 LTR TIN 4 PCS",
    "label": "FG0000009 — EXTRA LIGHT OLIVE 5 LTR TIN 4 PCS",
    "open_qty": 5000.0, "open_pcs": 1000.0
  }],
  "total_open": 5000.0, "total_pcs": 1000.0
}
```

## Used by
[[sales-flow]]

## Notes
- READ endpoint — safe. Probed live with a real open order from the sales-flow result.
- Only meaningful for documents whose `*_open` flag is true; a fully-processed (closed) document returns no open items.
- `open_qty` is the [[order-in-hand]] (OIH) residual for that line — demand still to be fulfilled.
