---
endpoint: /realise/api/sales-data/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: true
used_by: [sales-dashboard, home]
tags: [jivo, api, sales-dashboard]
---
# `POST /realise/api/sales-data/`

## Purpose
Core feed for the OILS [[sales-dashboard|Realise Dashboard]]. Returns per-product realise rows (litres, ₹, realise, target) plus flattened channel/line-item rows used to build Slide-1 grid and Slide-2 channel cards. Aggregated over the requested date range for the [[OILS]] segment.

## Request
JSON body:
- `start_date` (str, `YYYY-MM-DD`) — range start.
- `end_date` (str, `YYYY-MM-DD`) — range end.
- `refresh` (bool, optional) — force server recompute/cache-bust (Slide-1 sends `refresh:!!opts.force`; other callers omit it).

## Response
HTTP 200. Top-level keys:
- `status` — "ok".
- `data` — array of product rows: `{u_type, u_sub_group, month, year, litres, linetotal, realise, target_sale, target_realise}`.
- `count` — number of product rows.
- `channel_rows` — array of line-item rows (used range): `{u_type, u_sub_group, u_main_group, state, sales_person, card_name, item_name, sku, liter, line_total}`.
- `channel_month_rows` — same lines rolled to month buckets: adds `ym`, `mlabel`; `main_group` instead of `u_main_group`.

Trimmed sample:
```json
{"status":"ok","count":14,
 "data":[{"u_type":"PREMIUM","u_sub_group":"OLIVE","month":"JUL","year":"2026","litres":171420.0,"linetotal":47469034.04,"realise":276.92,"target_sale":310000,"target_realise":253}],
 "channel_rows":[{"u_type":"COMMODITY","u_sub_group":"MUSTARD","u_main_group":"GT","state":"DELHI","sales_person":"DELHI GT","card_name":"RAJESHWAR KISHORE MAHENDERPAL","item_name":"FG0000030 — MUSTARD KACHI GHANI 1 LTR 20 PCS","sku":"1 LTR","liter":4000.0,"line_total":620920.0}],
 "channel_month_rows":[{"u_type":"COMMODITY","main_group":"GT","state":"DELHI","sales_person":"DELHI GT","u_sub_group":"MUSTARD","ym":"2026-07","mlabel":"JUL 2026","liter":4000.0,"line_total":620920.0}]}
```

## Used by
[[sales-dashboard]] (Slide 1 grid, Slide 2 channel cards), [[control-panel]] (Control Panel KPIs — shared API).

## Notes
POST **read**. `realise` = `linetotal/litres` (₹/L, see [[REALISE]]). `target_sale`/`target_realise` merge in the month's [[targets]]. Probe with a single-day range only — do not pull months.
