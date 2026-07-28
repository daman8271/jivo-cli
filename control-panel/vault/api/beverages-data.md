---
endpoint: /realise/api/beverages-data/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard, beverages]
---
# `POST /realise/api/beverages-data/`

## Purpose
Core feed for the **[[BEVERAGES]]** dataset of the [[sales-dashboard]] (activated by the OILS⇄BEVERAGES toggle). Returns beverage sales lines plus today/yesterday box comparison, customer grading, month rollup and beverage [[OIH]] — all in litres/boxes rather than ₹/L.

## Request
JSON body:
- `start_date`, `end_date` (str, `YYYY-MM-DD`) — range.

## Response
HTTP 200. Top-level keys:
- `status`, `count` — status and line count.
- `data` — line rows: `{variety, sub_group, sku, item, main_group, state, brand, chain, sales_person, customer, ym, quantity, boxes, oih}`.
- `today_boxes` / `yesterday_boxes`, `today_items` / `yesterday_items` (arrays), `today_date` / `yesterday_date` — day-over-day comparison.
- `customer_rows` — `{customer, brand, ym, quantity, boxes}` for customer grading.
- `month_rows` — `{ym, brand, label, quantity, boxes}` monthly totals.
- `oih_rows` — open beverage orders `{variety, sub_group, item, customer, brand, ym, quantity, boxes}`.

Trimmed sample:
```json
{"status":"ok","count":..,"today_boxes":0.0,"yesterday_boxes":7481.0,"today_date":"2026-07-23","yesterday_date":"2026-07-22",
 "data":[{"variety":"WATER","sub_group":"MINERAL WATER","sku":"250 MLS","item":"PET BOTTLE 250 ML JIVO ...","main_group":"GT","state":"DELHI","brand":"JIVO","chain":"DISTRIBUTOR","sales_person":"SHUNTY ACC","customer":"VARDHMAN TRADERS","ym":"2026-07","quantity":16800.0,"boxes":700.0,"oih":0.0}],
 "customer_rows":[{"customer":"GURU RAMDAS DISTRIBUTORS","brand":"JIVO","ym":"2026-07","quantity":12000.0,"boxes":500.0}],
 "month_rows":[{"ym":"2026-07","brand":"JIVO","label":"Jul 2026","quantity":170778.0,"boxes":7481.0}],
 "oih_rows":[{"variety":"WATER","sub_group":"MINERAL WATER","item":"PET BOTTLE 500 ML ...","customer":"GAGANDEEP SINGH","brand":"JIVO","ym":"2026-07","quantity":48000.0,"boxes":2000.0}]}
```

## Used by
[[sales-dashboard]] (BEVERAGES dataset).

## Notes
POST **read** — sample a single day. `quantity` is units, `boxes` is cartons; beverages are tracked in boxes/units, not ₹/L realise. Invoice/SO drill behind a node = [[beverages-docs]]. Concepts: [[BEVERAGES]], [[OIH]].
