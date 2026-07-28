---
endpoint: /realise/api/customer-aging-beverages/
method: GET
auth: session + XHR header (X-Requested-With / X-CSRFToken)
readonly: true
used_by: [customer-aging]
tags: [jivo, api, accounts]
---
# `GET /realise/api/customer-aging-beverages/`

## Purpose
Returns the **Beverages** entity's A/R aging as a **pre-bucketed pivot** — customers grouped by **Format** (here the salesperson/ASM name is used as the grouping band), split across the standard aging buckets, with book KPIs and totals. Powers the Beverages view (and RAW DATA workspace) of the [[customer-aging]] page.

## Request
Query params:
- `as_of` — `YYYY-MM-DD` (optional; default today). Ages balances to this date.

Headers: `X-Requested-With: XMLHttpRequest` required. Session cookie required.

## Response
HTTP `200`, `application/json` (~82 KB sample). Same shape as [[customer-aging-mart]]:
- `status` `"ok"`, `company` `"bev"`, `aging_date`.
- `buckets` — `b0_30 / b31_60 / b61_90 / b91_120 / b121` definitions.
- `groups` — `[{format, customers[], original, balance_due, b0_30…b121, count}]`.
- `total` — `{original, balance_due, b0_30…b121}`.
- `kpis` — `{total_outstanding, current, current_pct, overdue_90, overdue_90_pct, customer_count, format_count, top_customer_name, top_customer_value, top_customer_pct}`.

Customer object here is leaner than Mart (no `gstin`/`segment`): `{code, name, format, original, balance_due, b0_30, b31_60, b61_90, b91_120, b121}`.

Trimmed sample:
```json
{"status":"ok","company":"bev","aging_date":"2026-07-23",
 "kpis":{"total_outstanding":6337904.51,"current_pct":60.7,"overdue_90_pct":16.9,"customer_count":350,
         "format_count":46,"top_customer_name":"GAGANDEEP SINGH","top_customer_pct":21.0},
 "groups":[{"format":"NAVNEET SINGH","customers":[
   {"code":"CUSTA000986","name":"TAVISH INDUSTRIES","original":200002.0,"balance_due":154413.0,
    "b0_30":154413.0,"b31_60":0.0,"b61_90":0.0,"b91_120":0.0,"b121":0.0}]}]}
```

## Used by
[[customer-aging]] (Beverages company toggle + Beverages RAW DATA workspace).

## Notes
- Read-only. Probed live (today) → HTTP 200, 46 groups, 350 customers.
- Groups are keyed by salesperson name (e.g. `"NAVNEET SINGH"`) rather than channel format.
- Companion write/upload endpoints: `aging-remark-upload-beverages/`, `aging-remark-clear-beverages/` — see [[aging-remark]].
