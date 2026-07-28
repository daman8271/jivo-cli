---
endpoint: /realise/api/customer-aging-oil-ar/
method: GET
auth: session + XHR header (X-Requested-With / X-CSRFToken)
readonly: true
used_by: [customer-aging]
tags: [jivo, api, accounts]
---
# `GET /realise/api/customer-aging-oil-ar/`

## Purpose
Returns the **Oil** company's full **open accounts-receivable ledger as a flat, per-open-invoice list** — one row per open SAP document. Feeds the [[customer-aging]] page's Oil **RAW DATA** workspace (Excel-like table + pivot); the client buckets rows by `days` for aging views.

## Request
Query params:
- `as_of` — `YYYY-MM-DD` (optional; default = today). Ages all balances to this date. Sent by the page as `?as_of=…`.

Headers: `X-Requested-With: XMLHttpRequest` required (else 401/403). Session cookie required.

## Response
HTTP `200`, `application/json` (large — ~2 MB, ~5,400 rows on sample). Top-level keys:
- `status` — `"ok"`.
- `company` — `"oil"`.
- `aging_date` — the effective as-of date, e.g. `"2026-07-23"`.
- `error` — null on success.
- `rows` — list of open-invoice objects.

Row shape (all keys): `sp` (sales employee/buyer), `code` (CardCode), `name` (customer), `doc` (SAP doc no), `date` (invoice date), `days` (age in days), `ltd` (last txn / due date), `tdd` (days to due), `dispatch`, `bilty`, `biltydate`, `transporter`, `vehicle`, `driver`, `mobile`, `status` (`"O"` = Open), `total` (invoice value), `bal` (open balance), `outstanding`, `remark`, `actual_sp`.

Trimmed 1-row sample:
```json
{"sp":"-No Sales Employee / Buyer-","code":"CUSTA000851","name":"MAHAVIR TRADING CO. (ADIPJ9162D)",
 "doc":"324101016","date":"2024-10-05","days":656,"ltd":"2025-12-11","tdd":224,
 "status":"O","total":375500.0,"bal":375500.0,"outstanding":2.0,"remark":"","actual_sp":""}
```

## Used by
[[customer-aging]] (Oil company → RAW DATA workspace; also the raw feed the Oil aging buckets derive from).

## Notes
- Read-only. Probed live with no `as_of` (today) → HTTP 200, 5,405 rows, all `status:"O"`.
- Mart/Beverages use pre-bucketed endpoints ([[customer-aging-mart]], [[customer-aging-beverages]]); Oil is the only one returned as flat invoices.
- The dispatch fields (`bilty`, `transporter`, `vehicle`, …) are often empty; they support the dispatch-tracking columns in the RAW view.
- Companion write/upload endpoints for this company: `aging-remark-upload-oil/`, `aging-remark-clear-oil/` — see [[aging-remark]].
