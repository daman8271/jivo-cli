---
endpoint: /realise/api/open-payments/
method: POST
auth: session + X-CSRFToken (JSON)
readonly: true
used_by: [open-payments]
tags: [jivo, api, accounts]
---
# `POST /realise/api/open-payments/`

## Purpose
Returns customer **payments on account** — receipts received but not yet applied to specific invoices — for a given date range. Backs the [[open-payments]] page.

## Request
Headers: `Content-Type: application/json`, `X-CSRFToken: <csrftoken>`, `X-Requested-With: XMLHttpRequest`. Session cookie required.

JSON body:
- `start_date` — `YYYY-MM-DD` (required). Start of the receipt-date range.
- `end_date` — `YYYY-MM-DD` (required). End of the range (inclusive).

Page won't fire the request unless both dates are set. Built in JS as `body: JSON.stringify({start_date:sd, end_date:ed})`.

## Response
HTTP `200`, `application/json`. Top-level keys:
- `status` — `"ok"`.
- `rows` — list of on-account receipts.
- `count` — number of rows.
- `start` / `end` — echoed range.

Row shape: `{date, doc_no, code, name, main_group, state, amount, open_bal}`
- `date` receipt date · `doc_no` SAP receipt no · `code`/`name` CardCode/CardName · `main_group` channel · `state` party state · `amount` payment on account (₹) · `open_bal` still-unapplied balance (₹).

Trimmed sample (probed with a single day `2026-07-22`, 14 rows):
```json
{"status":"ok","count":14,"start":"2026-07-22","end":"2026-07-22",
 "rows":[{"date":"2026-07-22","doc_no":"726246746","code":"CUSTA000365",
   "name":"RAJESHWAR KISHORE MAHENDERPAL","main_group":"GT","state":"HARYANA",
   "amount":1132770.0,"open_bal":1132770.0}]}
```

An empty body returns HTTP `400` (dates are mandatory).

## Used by
[[open-payments]].

## Notes
- Read-only, but a POST — sampled with a **single day** per read-only discipline; do not pull wide ranges.
- "Contact Person" shown on the page is derived client-side from `main_group` + `state`, not returned here.
