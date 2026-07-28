---
endpoint: /realise/api/historical-realise/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `POST /realise/api/historical-realise/`

## Purpose
Returns the **trailing-period average realise** (₹/L) per product and per drilled dimension, as an overlay column on the [[sales-dashboard]] Slide-1 grid. Selected via the `fAvgPeriod` dropdown.

## Request
JSON body:
- `start_date`, `end_date` (str, `YYYY-MM-DD`) — anchor range (period is measured relative to it).
- `period` (str) — trailing window: `12m` (12 Months) | `6m` (6 Months) | `3m` (Quarterly) | `last_month` (Last Month). Empty = overlay off.

## Response
HTTP 200. Keys: `status`, `data`, `drill_data`, `period`.
- `data` — object `"<U_TYPE>|<SUB_GROUP>"` → avg realise (float ₹/L) over the window.
- `drill_data` — object `"<U_TYPE>|<SUB_GROUP>|<Dim>|<Value>"` → avg realise, precomputed per drill dimension so expanded rows also show the historical avg.
- `period` — echoed window.

Trimmed sample:
```json
{"status":"ok","period":"month",
 "data":{"PREMIUM|OLIVE":276.92,"COMMODITY|MUSTARD":150.2,"PREMIUM|GHEE":0},
 "drill_data":{"COMMODITY|MUSTARD|State|DELHI":155.27,"COMMODITY|MUSTARD|U_Main_Group|GT":156.2}}
```

## Used by
[[sales-dashboard]] (historical avg-realise overlay).

## Notes
POST **read** — sample a single day. `drill_data` keys use the same Pascal-case dimensions as [[drill-down]] (`State`, `U_Main_Group`, `U_Chain`, `ItemName`, `CardName`). `0` = no sales in that product for the window. Concept: [[REALISE]].
