---
endpoint: /realise/api/segment-targets/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/segment-targets/`

## Purpose
Returns saved target overrides scoped to a single **segment** (e.g. [[OILS]], [[BEVERAGES]], PREMIUM, COMMODITY). Feeds the [[sales-dashboard]] target layer when the segment view is active.

## Request
Query params:
- `segment` (str, required) — segment name; server lower-cases it (`OILS`→`oils`).
- `month`, `year` (int, optional) — target period.
- `seg` (str, optional) — secondary segment scope passed by Slide-1 (`&seg=`).

The page builds it as `?segment=<seg>&month=<m>&year=<y>&seg=<seg>`.

## Response
HTTP 200. Keys: `status`, `segment` (echoed, lower-cased), `month`, `year`, `data`. `data` is an object of saved targets (same `key → {tgt_ltrs,tgt_rate}` shape as [[targets]]); **empty `{}` when no segment-specific overrides are saved**.

Trimmed sample (observed — no OILS overrides for Jul 2026):
```json
{"status":"ok","segment":"oils","month":7,"year":2026,"data":{}}
```

## Used by
[[sales-dashboard]].

## Notes
GET read. Empty object is normal — it only holds *explicitly saved* segment overrides (via [[save-targets]]), not the base defaults which live in [[targets]]. Related: [[flex-targets]], [[target-nodes]], concept [[TGT]].
