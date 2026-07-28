---
endpoint: /realise/api/drill-down/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `POST /realise/api/drill-down/`

## Purpose
Expands one product row of the [[sales-dashboard]] Slide-1 grid into a chosen dimension — returns litres + linetotal for each value of that dimension (state / channel / chain / item / customer). Powers the ▸ drill (and recursive sub-drill) on the realise table.

## Request
JSON body:
- `start_date`, `end_date` (str, `YYYY-MM-DD`) — range.
- `u_type` (str) — product tier, e.g. `PREMIUM` / `COMMODITY`.
- `u_sub_group` (str) — product variety, e.g. `OLIVE`, `MUSTARD`.
- `drill_by` (str) — **case-sensitive** dimension: `State` | `U_Main_Group` | `U_Chain` | `ItemName` | `CardName`.
- `filters` (object) — path filters accumulated from parent drills, e.g. `{"State":"HARYANA"}` for sub-drills; `{}` at top level.
- `month`, `year` (str, optional) — added when the Month/Year filters are set.

## Response
HTTP 200. Key: `data` — array of `{dimension, litres, linetotal}`, one per value of the drill dimension.

Trimmed sample (`u_type=PREMIUM, u_sub_group=OLIVE, drill_by=State`):
```json
{"data":[{"dimension":"HARYANA","litres":169684.0,"linetotal":47105000.0},
         {"dimension":"DELHI","litres":1761.0,"linetotal":370828.9272}]}
```

## Used by
[[sales-dashboard]] (row drill / sub-drill).

## Notes
POST **read** — sample a single day. **Gotcha:** `drill_by` must be Pascal/Title case; passing `state` (lowercase) returns a single `dimension:"UNKNOWN"` bucket. `realise` per node = `linetotal/litres` ([[REALISE]]). Related: [[historical-realise]] (trailing-avg overlay), [[Main Group]] drill.
