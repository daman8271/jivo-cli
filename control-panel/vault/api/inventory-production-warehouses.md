---
endpoint: /inventory/production/api/warehouses/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [production-plan]
tags: [jivo, api, inventory, production]
---
# `GET /inventory/production/api/warehouses/`

## Purpose
Returns the **full warehouse master** (code + name) so the [[production-plan]] page can build its **"Stock from"** warehouse multi-select. The user's chosen set (or `ALL`) is passed as the `warehouses` param to [[inventory-production-feasibility]] and [[inventory-production-plan]], defining which godowns' stock counts as "available" when checking component sufficiency.

## Request
No params. GET with XHR header. Fetched lazily the first time the "Stock from" picker is opened.

## Response
HTTP 200 · `application/json`:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"`. |
| `data` | object[] | Warehouse master (35 rows at probe). |

`data[]` row: `{ "code": "BH-EC", "name": "BHAKHARPUR FINISHED E-COMMERCE" }`.

Trimmed sample:
```json
{"status":"ok","data":[
  {"code":"BH-BS","name":"Bhakharpur Basement"},
  {"code":"BH-EC","name":"BHAKHARPUR FINISHED E-COMMERCE"},
  {"code":"BH-FG","name":"Bhakharpur Finished Basement"},
  {"code":"BH-PF","name":"Bhakharpur Production Finished 1st Floor"},
  {"code":"GP-FG","name":"GUPTA GODOWN BASEMENT FINISHED GODOWN"}
]}
```

## Used by
- [[production-plan]] — "Stock from" warehouse selector.

## Notes
- Read-only. Covers all godown types — finished (FG/PF/EC), raw/packing (PC/PP/PM/LO), transit (INT), non-moving (NM), job-work (JW/GJ), Gujarat crude, fixed assets, etc. See [[warehouses]] for the code scheme. Note the finished-stock warehouse `BH-FU` used on [[stock-available]] is **not** in this production master.
