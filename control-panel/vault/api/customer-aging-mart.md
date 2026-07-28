---
endpoint: /realise/api/customer-aging-mart/
method: GET
auth: session + XHR header (X-Requested-With / X-CSRFToken)
readonly: true
used_by: [customer-aging]
tags: [jivo, api, accounts]
---
# `GET /realise/api/customer-aging-mart/`

## Purpose
Returns the **Mart** entity's A/R aging as a **pre-bucketed pivot** — customers grouped by **Format** (channel), each with balances split across the standard aging buckets, plus book-level KPIs and totals. Powers the Mart view of the [[customer-aging]] page directly (no client bucketing needed).

## Request
Query params:
- `as_of` — `YYYY-MM-DD` (optional; default today). Ages balances to this date.

Headers: `X-Requested-With: XMLHttpRequest` required. Session cookie required.

## Response
HTTP `200`, `application/json` (~16 KB sample). Top-level keys:
- `status` — `"ok"`.
- `company` — `"mart"`.
- `aging_date` — effective date.
- `buckets` — `[{key,label,color}]` bucket definitions: `b0_30` "0 - 30", `b31_60` "31 - 60", `b61_90` "61 - 90", `b91_120` "91 - 120", `b121` "121+".
- `groups` — list of format groups; each `{format, customers[], original, balance_due, b0_30, b31_60, b61_90, b91_120, b121, count}`.
- `total` — book totals `{original, balance_due, b0_30, b31_60, b61_90, b91_120, b121}`.
- `kpis` — `{total_outstanding, current, current_pct, overdue_90, overdue_90_pct, customer_count, format_count, top_customer_name, top_customer_value, top_customer_pct}`.

Customer object (inside `groups[].customers`): `{code, name, format, original, balance_due, b0_30, b31_60, b61_90, b91_120, b121, gstin, segment}` — `segment` is `B2B` (has `gstin`) or `B2C`.

Trimmed sample:
```json
{"status":"ok","company":"mart","aging_date":"2026-07-23",
 "total":{"original":313188550.54,"balance_due":168983857.74,"b0_30":41542122.54,"b121":183608931.56},
 "kpis":{"total_outstanding":168983857.74,"current_pct":24.6,"overdue_90_pct":81.3,"customer_count":53,
         "top_customer_name":"JIVO MART PVT LTD - DL","top_customer_pct":60.5},
 "groups":[{"format":"E-COMMERCE","count":...,"customers":[
   {"code":"CUSTA000048","name":"R K WORLDINFOCOM PVT LTD","balance_due":74955734.34,
    "b0_30":13875346.09,"b121":71652588.1,"gstin":"36AAECR0564M3Z2","segment":"B2B"}]}]}
```

## Used by
[[customer-aging]] (Mart company toggle).

## Notes
- Read-only. Probed live (today) → HTTP 200, 10 groups, 53 customers.
- Sum of the five bucket columns = `balance_due` (negatives = advances/credit notes).
- Mart is the only company exposing the `segment` (B2B/B2C) split, which drives that page's B2B/B2C filter.
- Twin endpoints: [[customer-aging-beverages]] (same shape), [[customer-aging-oil-ar]] (flat, different shape).
