---
endpoint: /realise/api/customer-master/
method: GET
auth: session + XHR header
readonly: true
used_by: [customer-master]
tags: [jivo, api, masterdata]
---
# `GET /realise/api/customer-master/`

## Purpose
Returns the **entire customer master** — every customer with contact, tax, address, salesperson, terms, credit limit, balance and status — in a single JSON payload. Backs the [[customer-master]] page, which does all filtering, sorting and KPI computation client-side. Read-only reference data; the `code` field is the join key used by the transactional Realise / Accounts reports.

## Request
- **Method:** GET
- **Headers:** `X-Requested-With: XMLHttpRequest` (required; without it the app returns 403/404). Session cookie required — an unauthenticated call returns `HTTP 401 {"error":"Authentication required"}`.
- **Query params:** none. No pagination, no server-side filter — the full master is always returned.
- **Access:** `customer_master_viewer` group / `can_customer_master` permission.

## Response
- **Observed:** `HTTP 200`, `application/json`, ~448 KB (1,167 rows in sample).
- **Top-level keys:**
  - `status` — string, `"ok"` on success; `"error"` with an `error` message on failure (the page then shows "Could not load").
  - `count` — integer, number of rows (1167).
  - `rows` — array of customer objects.
- **Each `rows[]` object (17 keys, all present per row; many values may be empty strings):**
  - `code` — string, customer master code (e.g. `"CUSTA000936"`). Join key.
  - `name` — string, customer name.
  - `main_group` — string, business-group/channel bucket (24 distinct: `GT`, `MT`, `ROI`, `E-COMMERCE`, `HORECA`, `CSD`, `CORPORATE`, `EXPORT`, `BRANCH`, `BULK OIL`, `PURCHASE OIL`, `COMPANY UNIT`, `CASH SALE`, `CALL CENTER`, `WEBSITE`, `CONSUMABLES`, `EVENTS & EXHIBITIONS`, `FIXED ASSETS`, `JOB WORK`, `REFERENCE`, `SANGAT`, `STAFF`, `STAFF CUSTOMER`, `TRANSPORT`).
  - `contact_person` — string.
  - `mobile` — string (often empty).
  - `email` — string (usually empty).
  - `gstin` — string, 15-char GSTIN (present ~75%).
  - `pan` — string (usually empty; PAN is embedded in GSTIN).
  - `address` — string (present ~44%).
  - `city` — string.
  - `state` — string (28 distinct incl. foreign like `ABU DHABI` for exports).
  - `pincode` — string.
  - `sales_person` — string, mapped salesperson (68 distinct; present ~26%).
  - `payment_terms` — string (14 distinct: `ADVANCE/CASH/0 DAYS`, `COD`, `CAD`, `20% ADVANCE`, `45 % ADV`, `LC 60`, `NET-01`…`NET-30`).
  - `credit_limit` — number, ₹ sanctioned credit limit.
  - `balance` — number, ₹ current outstanding ledger balance (can be **negative** = customer in advance/credit).
  - `status` — string, `"Active"` | `"Frozen"` (page also supports `"Inactive"` as a filter, not seen in feed).

### Trimmed sample (1 row)
```json
{
  "status": "ok",
  "count": 1167,
  "rows": [
    {
      "code": "CUSTA000936",
      "name": "AMAN TRADING COMPANY",
      "main_group": "GT",
      "contact_person": "RESHAM SINGH",
      "mobile": "9815904600",
      "email": "",
      "gstin": "03ACHPS3233Q1ZA",
      "pan": "",
      "address": "SHOP NO.89",
      "city": "MOGA",
      "state": "PUNJAB",
      "pincode": "142001",
      "sales_person": "G PURE",
      "payment_terms": "ADVANCE/CASH/0 DAYS",
      "credit_limit": 1334000.0,
      "balance": -938.0,
      "status": "Active"
    }
  ]
}
```

## Used by
- [[customer-master]] — the sole consumer; fetched once on page load.

## Notes
- **Read-only, safe** — probed live with the smallest possible call (no params; the endpoint has no filtering so the full ~448 KB is unavoidable, sampled once for schema).
- Companion **export** at `/realise/customer-master/export/` streams the same data as XLSX (EXPORT — not probed; documented via the page's `<a href>`).
- Large single payload; all slicing happens in the browser.
