---
endpoint: /realise/api/flex-targets/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/flex-targets/`

## Purpose
Returns "flex" (flat, dimension-scoped) litre targets — currently keyed per **salesperson** — for the current target month. Used by the [[sales-dashboard]] to attribute a monthly litre goal to each sales owner alongside the product-level [[targets]].

## Request
Query params (all optional; defaults to current month/year):
- `seg` (str, optional) — segment scope (e.g. `OILS`, `BEVERAGES`).
- `month`, `year` (int, optional) — target period.

## Response
HTTP 200. Keys: `status`, `month`, `year`, `data`. `data` is an object mapping a **flex key** → target litres (float). Keys use the internal `¦<dim>=<value>` encoding, here `¦person=<NAME>`.

Trimmed sample:
```json
{"status":"ok","month":7,"year":2026,
 "data":{"¦person=PRABHU SIR":650000.0,"¦person=SUNNY JI":115000.0,"¦person=—":65000.0}}
```

## Used by
[[sales-dashboard]] (per-salesperson target attribution).

## Notes
GET read. The `¦person=` prefix is the app's generic flex-dimension key format (other dims may appear if configured). `—` (em dash) is the unassigned/blank salesperson bucket. Related: [[targets]], [[segment-targets]], [[target-nodes]], concept [[TGT]].
