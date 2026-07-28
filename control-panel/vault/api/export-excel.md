---
endpoint: /realise/api/export-excel/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: false
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard, export]
---
# `POST /realise/api/export-excel/` — EXPORT (file download, NOT PROBED)

## Purpose
Exports the main **Realise Dashboard** grid to Excel. The client builds a layout-row representation of the on-screen table and this endpoint returns the `.xlsx` file.

## Request
Signature read from page JS (never executed):
```json
{"layout_rows": buildExcelLayoutRows("Realise Dashboard") }
```
- `layout_rows` — array describing the rendered grid (headers, product rows, drills, totals) produced by the client `buildExcelLayoutRows(...)` helper.

POST with `Content-Type: application/json` + `X-CSRFToken`; response read as `blob()`, filename derived as `Realise_Export_<dFrom>_<dTo>.xlsx` (server may also set `Content-Disposition`).

## Response
Not probed. Binary XLSX stream. No JSON.

## Used by
[[sales-dashboard]] (main-grid Excel export).

## Notes
**EXPORT — file-generating write path; do not call on the live system.** Method is **POST** (despite the "export-excel" name that reads GET-like); a separate CSV path (`exportCSV`) builds a client-side CSV blob. Sibling xlsx builder for sub-tables is [[export-xlsx]]. Documented from page HTML only.
