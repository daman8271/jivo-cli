---
endpoint: /realise/api/targets/
method: GET
auth: session + XHR header
readonly: true
used_by: [sales-dashboard, home]
tags: [jivo, api, sales-dashboard]
---
# `GET /realise/api/targets/`

## Purpose
Returns the product-level monthly targets — target litres and target ₹/L per `u_type|u_sub_group` key — used to fill the Tgt Ltrs / Tgt Rate columns and target KPIs on the [[sales-dashboard]]. Falls back to hard-coded defaults when no saved override exists.

## Request
Query params:
- `month` (int 1–12) — target month.
- `year` (int) — target year.

## Response
HTTP 200. Keys: `status`, `month`, `year`, `data`. `data` is an object keyed `"<U_TYPE>|<SUB_GROUP>"` → `{tgt_ltrs, tgt_rate, source}` where `source` is `"default"` or `"saved"`.

Trimmed sample:
```json
{"status":"ok","month":7,"year":2026,
 "data":{"COMMODITY|MUSTARD":{"tgt_ltrs":625000,"tgt_rate":145,"source":"default"},
         "PREMIUM|BLENDED":{"tgt_ltrs":10000,"tgt_rate":190,"source":"default"}}}
```

## Used by
[[sales-dashboard]] (target columns / KPIs), [[control-panel]].

## Notes
GET read. The editable counterpart is [[save-targets]] (WRITE — never call). `source:"saved"` means a value persisted via save-targets overrides the default. Concept: [[TGT]].
