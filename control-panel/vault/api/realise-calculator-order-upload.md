---
endpoint: /realise/api/realise-calculator/order-upload/
method: POST
auth: session + X-CSRFToken (multipart form-data)
readonly: false
used_by: [realise-calculator]
tags: [jivo, api, calculator-ratelist]
---

# `POST /realise/api/realise-calculator/order-upload/`

## Purpose
Order-tab variant of [[realise-calculator-upload]]: parses an uploaded order `.xlsx` and returns rows used to fill **both** the Old Order and New Order grids in the [[realise-calculator]] "New vs Old Order" tab (the same parsed rows seed both grids so the user can then edit the New side). **WRITE/upload — not executed during recon; signature captured from page JS only.**

## Request
`multipart/form-data`, `X-CSRFToken: <csrftoken>`. Form fields:

| Field | Type | Meaning |
|---|---|---|
| `file` | file (`.xlsx`) | Order spreadsheet with an **Item Code** column |

Sent via `FormData` with a single `file` part. Routed here (instead of `upload/`) when the upload target is `order` / `ordOld` / `ordNew`.

## Response
Not probed. Same shape as [[realise-calculator-upload]]: `{status, rows[], count, matched}`, where `rows[]` are grid-row objects (`item, code, retailer, ss, dm, gst, pcsbox, disc, boxltr, scheme, sell`) matched to the SAP master by code.

## Used by
[[realise-calculator]] — "Upload Excel" in the New vs Old Order tab (fills Old + New grids).

## Notes
- **WRITE/upload endpoint — mutating (accepts a file).** In the recipe's skip list; documented from `realise__realise-calculator.html` only, never called.
- Planning-grid / Compare counterpart: [[realise-calculator-upload]].
