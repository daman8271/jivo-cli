---
endpoint: /realise/api/save-targets/
method: POST
auth: session + X-CSRFToken + XHR header + admin re-auth
readonly: false
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard, write]
---
# `POST /realise/api/save-targets/` — ⚠️ WRITE (NOT PROBED)

## Purpose
Persists edited product-level monthly targets (litres + ₹/L rate) for a month/year, overriding the defaults returned by [[targets]]. Invoked by the **Update Targets** flow on the [[sales-dashboard]].

## Request
Signature read from page JS (never executed):
```json
{"month": <int>, "year": <int>,
 "targets": [ {"key": "<U_TYPE>|<SUB_GROUP>", "tgt_ltrs": <float>, "tgt_rate": <float>}, ... ]}
```
- `key` — `pr.u_type + '|' + pr.u_sub_group` per edited row.
- `tgt_ltrs` — parsed from the `data-field="ltrs"` input.
- `tgt_rate` — parsed from the `data-field="rate"` input.

Gated: the "Update Targets" button first opens an admin re-auth modal that POSTs `/realise/api/verify-pin/` `{"pin":"<password>"}`; only on `{status:"ok",verified:true}` does the editable target table open.

## Response
Not probed. On success the UI toasts "All targets saved for <MONTH> <YEAR>"; error path reads `err.detail || err.error`.

## Used by
[[sales-dashboard]] (Update Targets).

## Notes
**WRITE — mutating, on a LIVE PRODUCTION system. Never call.** Documented from page HTML only. Read counterpart: [[targets]]. Concept: [[TGT]].
