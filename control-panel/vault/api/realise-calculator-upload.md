---
endpoint: /realise/api/realise-calculator/upload/
method: POST
auth: session + X-CSRFToken (multipart form-data)
readonly: false
used_by: [realise-calculator]
tags: [jivo, api, calculator-ratelist]
---

# `POST /realise/api/realise-calculator/upload/`

# Purpose
Parses an uploaded `.xlsx` and returns calculator rows so the [[realise-calculator]] Planning Grid (or a Compare A/B grid) can be pre-filled. Rows are matched against the SAP item master ([[realise-calculator-items]]) by **Item Code** to hydrate name / pcs-per-box / box-litres. **WRITE/upload — not executed during recon; signature captured from page JS only.**

## Request
`multipart/form-data`, `X-CSRFToken: <csrftoken>` (no `Content-Type: application/json`; the browser sets the multipart boundary). Form fields:

| Field | Type | Meaning |
|---|---|---|
| `file` | file (`.xlsx`) | Spreadsheet with an **Item Code** column; other trade-term columns fill the grid inputs |

Sent via `FormData` with a single `file` part.

## Response
Not probed. Page JS expects JSON:

| Key | Type | Meaning |
|---|---|---|
| `status` | str | `"ok"` on success |
| `rows` | array | Parsed rows, each shaped like a grid row: `item, code, retailer, ss, dm, gst, pcsbox, disc, boxltr, scheme, sell` |
| `count` | int | Total rows parsed |
| `matched` | int | How many `code`s matched the SAP master (unmatched → blank name/box, and a warning is shown) |

On `status!=='ok'` or empty `rows`, an `error` string is shown to the user.

## Used by
[[realise-calculator]] — "Upload Excel" on the Planning Grid and on Compare Plan A / Plan B grids.

## Notes
- **WRITE/upload endpoint — mutating (accepts a file).** In the recipe's skip list; documented from `realise__realise-calculator.html` only, never called.
- Order-tab counterpart (fills both Old + New grids): [[realise-calculator-order-upload]].
- Export counterpart: [[realise-calculator-export]].
