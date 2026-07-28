---
endpoint: /inventory/production/api/plan/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [production-plan]
tags: [jivo, api, inventory, production]
---
# `GET /inventory/production/api/plan/`

## Purpose
Multi-item version of [[inventory-production-feasibility]]: takes a **basket of finished goods with quantities**, explodes and **aggregates all their BOM components** (a shared RM/PM is summed across the FGs that use it), and returns net material sufficiency for the whole production plan. Powers the "Production plan (multiple)" mode of [[production-plan]].

## Request
Query params (GET, XHR header):

| Param | Type | Meaning |
|---|---|---|
| `items` | string (URL-encoded JSON) | Array of `{"fg_code":"<code>","qty":<n>}` — the FGs + quantities to plan. Built in page JS as `encodeURIComponent(JSON.stringify(items))`. |
| `warehouses` | string | `ALL` or comma-separated warehouse codes ("Stock from"). |

Example (decoded `items`): `[{"fg_code":"FG0000149","qty":1}]`.

## Response
HTTP 200 · `application/json`. `status:"ok"` + `data`:

| Key | Shape | Meaning |
|---|---|---|
| `items` | object[] | Echo of each planned FG: `{fg_code, fg_name, qty, found}`. |
| `materials` | object[] | Aggregated component requirement across the whole basket. |
| (also carries plan-level `feasible` / `short_count` consumed by the page KPIs) | | |

`materials[]` row:

| Field | Type | Meaning |
|---|---|---|
| `code` / `name` / `kind` / `uom` | — | Component identity (RM/PM). |
| `warehouse` | string | Primary BOM warehouse. |
| `onhand` | number | Stock in primary warehouse. |
| `available` | number | Stock across selected warehouses. |
| `all_wh` | number | Stock across all warehouses. |
| `warehouses` | object[] | `{wh, qty}` physical locations. |
| `required` | number | **Total** required across all FGs in the basket. |
| `used_in` | string[] | Which planned FG codes consume this component. |
| `balance` | number | `available − required` (negative = short). |
| `short` | bool | Short in the selection. |
| `elsewhere` | bool | Short here but available in other warehouses. |

Trimmed sample (`items=[{"fg_code":"FG0000149","qty":1}]`):
```json
{"status":"ok","data":{
 "items":[{"fg_code":"FG0000149","fg_name":"JIVO GOLD 1 LTR 20 PCS","qty":1.0,"found":true}],
 "materials":[{"code":"RM0000021","name":"LOOSE OIL GOLD","kind":"RM","uom":"LTR","warehouse":"BH-PC",
   "onhand":0.0,"available":-981.0,"all_wh":227.0,
   "warehouses":[{"wh":"BH-LO","qty":176.0},{"wh":"BH-WST","qty":45.0},{"wh":"BH-GR","qty":6.0}],
   "required":1.0,"used_in":["FG0000149"],"balance":-982.0,"short":true,"elsewhere":true}]}}
```

## Used by
- [[production-plan]] — multi-item plan KPIs + aggregated materials table.

## Notes
- Read-only. `items` is passed as a **query param** (URL-encoded JSON), not a POST body. The value of `used_in` is what distinguishes this from single-item feasibility — it shows shared-component pooling.
