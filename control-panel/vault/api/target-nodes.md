---
endpoint: /realise/api/target-nodes/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/target-nodes/`

## Purpose
Returns the granular target "nodes" — target litres broken down by **main group × state × salesperson × segment** — for a month. Used by the [[sales-dashboard]] detail/target-node views (cached per key `month|year|seg`) to attribute channel/geo/person-level goals.

## Request
Query params:
- `month` (int 1–12), `year` (int) — target period.
- `seg` (str) — segment scope (e.g. `OILS`, `BEVERAGES`).

## Response
HTTP 200. Keys: `status`, `month`, `year`, `data`. `data` is an array of rows: `{main_group, state, sales_person, segment, target_ltrs, target_realise}` (blank string = "all/unscoped" for that dimension).

Trimmed sample:
```json
{"status":"ok","month":7,"year":2026,
 "data":[{"main_group":"ECOM","state":"","sales_person":"","segment":"COMMODITY","target_ltrs":650000.0,"target_realise":0.0},
         {"main_group":"GT","state":"DELHI","sales_person":"SUNNY JI","segment":"COMMODITY","target_ltrs":85000.0,"target_realise":0.0}]}
```

## Used by
[[sales-dashboard]] (channel/geo/person target detail).

## Notes
GET read. `segment` here is the finer PREMIUM/COMMODITY tier (see [[Main Group]] drill), distinct from the OILS/BEVERAGES `seg` query param. `target_realise` often 0 (litre-only targets). Related: [[channel-targets]], [[segment-targets]], [[flex-targets]], concept [[TGT]].
