---
endpoint: /inventory/production/api/feasibility/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [production-plan]
tags: [jivo, api, inventory, production]
---
# `GET /inventory/production/api/feasibility/`

## Purpose
Checks whether a **single finished good** can be produced at a requested quantity, given current component (raw-material + packing-material) stock in the selected warehouses. Explodes the FG's Bill of Materials, compares required vs available for each component, and returns the **maximum producible FG count** (`max_fg`) plus a per-component sufficiency table. Powers the "Single item" mode of [[production-plan]].

## Request
Query params (GET, XHR header):

| Param | Type | Meaning |
|---|---|---|
| `fg_code` | string | FG code to check (from [[inventory-production-fg-list]], e.g. `FG0000149`). |
| `qty` | number | Planned FG quantity to test. |
| `warehouses` | string | `ALL` **or** comma-separated warehouse codes ("Stock from" selection) — defines which godowns' stock counts as *available*. |

## Response
HTTP 200 · `application/json`. `status:"ok"` + `data`:

| Field | Type | Meaning |
|---|---|---|
| `fg_code` / `fg_name` | string | The FG being planned. |
| `planned_qty` | number | Echo of requested qty. |
| `fg_onhand` | number | FG units already in stock. |
| `fg_uom` | string | FG unit of measure (`PCS`…). |
| `found` | bool | Whether a BOM was located. |
| `feasible` | bool | Can the full `planned_qty` be made from selected-warehouse stock? |
| `max_fg` | number | Max FGs producible now (limited by the scarcest component; can be negative when a component is already oversold). |
| `short_count` | int | Number of components that fall short. |
| `components` | object[] | Per-component sufficiency (below). |

`components[]` row:

| Field | Type | Meaning |
|---|---|---|
| `code` / `name` | string | Component item code + name. |
| `kind` | string | `RM` (raw material) or `PM` (packing material). |
| `uom` | string | Component unit. |
| `warehouse` | string | Primary/BOM warehouse for this component. |
| `per_fg` | number | Component qty consumed per 1 FG. |
| `required` | number | `per_fg × planned_qty`. |
| `onhand` | number | Stock in the primary warehouse. |
| `available` | number | Stock across the **selected** warehouses (drives balance/max). |
| `all_wh` | number | Stock across **all** warehouses. |
| `balance` | number | `available − required` (negative = short). |
| `max_fg` | number | Max FGs this component alone allows. |
| `short` | bool | Component is short in the selection. |
| `elsewhere` | bool | Short here, but enough exists in other warehouses ("↪ transferable"). |
| `warehouses` | object[] | `{wh, qty}` — where this component physically sits. |

Trimmed sample (`fg_code=FG0000149&qty=1`, `warehouses` default):
```json
{"status":"ok","data":{"fg_code":"FG0000149","fg_name":"JIVO GOLD 1 LTR 20 PCS",
 "planned_qty":1.0,"fg_onhand":457.0,"fg_uom":"PCS","found":true,"feasible":false,
 "max_fg":-981,"short_count":1,
 "components":[{"code":"RM0000021","name":"LOOSE OIL GOLD","kind":"RM","uom":"LTR","warehouse":"BH-PC",
   "per_fg":1.0,"required":1.0,"onhand":0.0,"available":-981.0,"all_wh":227.0,"balance":-982.0,
   "max_fg":-981,"short":true,"elsewhere":true,
   "warehouses":[{"wh":"BH-LO","qty":176.0},{"wh":"BH-WST","qty":45.0},{"wh":"BH-GR","qty":6.0}]}]}}
```

## Used by
- [[production-plan]] — Single-item feasibility KPIs (Feasible?, Max FG, Short components) + component table.

## Notes
- Read-only computation; nothing is produced/consumed. Resources & labour are excluded — material sufficiency only.
- `available`/`max_fg` can be negative when SAP shows a component oversold in the selected warehouse.
