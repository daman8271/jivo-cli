---
endpoint: /realise/api/export-xlsx/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: false
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard, export]
---
# `POST /realise/api/export-xlsx/` — EXPORT (file download, NOT PROBED)

## Purpose
Generic client-driven **XLSX builder**: the browser assembles the sheet rows and this endpoint streams back an `.xlsx` file. On the [[sales-dashboard]] it exports the Beverages **Customer Grading** table; other Realise screens reuse it for their own grids.

## Request
Signature read from page JS (never executed):
```json
{"filename": "<str, no extension>",
 "sheets": [ {"name": "<sheet name>", "rows": [ [<cell>, ...], ... ]} ]}
```
- `rows` cells are plain values or `{value, bold}` objects for styled/total cells.
- Example filename built as `Beverages_Customer_Grading[_<Brand>]`.

POSTed with `Content-Type: application/json` + `X-CSRFToken`; response consumed as a `blob()`.

## Response
Not probed. Binary XLSX stream (with a `Content-Disposition` attachment). No JSON.

## Used by
[[sales-dashboard]] (Beverages customer-grading export; shared by other Realise grids).

## Notes
**EXPORT — file-generating write path; do not call on the live system.** Distinct from [[export-excel]] which exports the main Realise grid. Documented from page HTML only.
