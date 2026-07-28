---
endpoint: /realise/api/aging-remark/ (+ upload/clear variants)
method: POST
auth: session + X-CSRFToken (JSON or multipart)
readonly: false
used_by: [customer-aging]
tags: [jivo, api, accounts]
---
# `POST /realise/api/aging-remark/` (remark family — WRITE)

## Purpose
The write-side of the [[customer-aging]] RAW DATA workspace: attach / edit **per-open-invoice remarks** (and special-price overlays) on the Oil and Beverages A/R books, and bulk-upload or clear them. These are a **Control-Panel-local overlay** — SAP data is never modified.

## Endpoints in this family (all POST, all WRITE — documented only, never called)
| Path | Body | Role |
|---|---|---|
| `/realise/api/aging-remark/` | `{code, row_key, remark}` | Save/update one invoice's remark. `row_key` is `<prefix><doc>` (Oil `OILDOC:` / `OILSP:`, Bev `BEVDOC:` / `BEVSP:`). |
| `/realise/api/aging-remark-upload-oil/` | multipart: `file` (.xlsx/.csv) + `as_of` | Bulk import Oil remarks/special-prices from a spreadsheet. |
| `/realise/api/aging-remark-upload-beverages/` | multipart: `file` + `as_of` | Bulk import Beverages remarks/special-prices. |
| `/realise/api/aging-remark-clear-oil/` | `{what}` | Erase all saved Oil remarks/special-prices for the whole book. |
| `/realise/api/aging-remark-clear-beverages/` | `{what}` | Erase all saved Beverages remarks/special-prices. |

## Request (details from page JS)
- Single save (`aging-remark/`): `Content-Type: application/json`, `X-CSRFToken`; body `{code:<CardCode>, row_key:<prefix+doc>, remark:<text>}`. Autosaves (debounced) on cell blur.
- Uploads: `FormData` with `file` and `as_of`; `X-CSRFToken` header, no JSON content-type. Response reports `{status, unmatched:[docNos…]}` for doc numbers with no matching open invoice.
- Clears: JSON `{what}` selecting which overlay (remark vs special-price) to wipe; guarded by a confirm dialog ("cannot be undone. SAP data is untouched").

## Response
Not probed. On success returns `{status:"ok"}` (single save adds a green "saved" flash; upload returns match/unmatched counts; clear resets the book).

## Used by
[[customer-aging]] (RAW DATA workspace, Oil & Beverages).

## Notes
- **WRITE — never executed.** All fields above are reverse-engineered from the page JavaScript (`CO_CFG`, `arCfg()`, `saveRawRemark`, upload/clear handlers).
- Overlay only: affects the Control-Panel store, not SAP. "Clear" is book-wide and irreversible.
- Mart has no remark overlay (only Oil & Beverages expose the RAW DATA workspace).
