---
endpoint: /inventory/production/api/fg-list/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [production-plan]
tags: [jivo, api, inventory, production]
---
# `GET /inventory/production/api/fg-list/`

## Purpose
Returns the **catalogue of manufacturable finished goods (FGs)** — every product that has a Bill of Materials and can be production-planned. Populates the searchable FG picker on the [[production-plan]] page (both "Single item" and multi-item "Production plan" modes). The chosen `code` is then passed to [[inventory-production-feasibility]] / [[inventory-production-plan]].

## Request
No params. GET with XHR header.

## Response
HTTP 200 · `application/json`:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"`. |
| `data` | object[] | FG catalogue rows. |

`data[]` row:

| Field | Type | Meaning |
|---|---|---|
| `code` | string | SAP FG item code (`FG…`/`FB…`) — the `fg_code` used downstream. |
| `name` | string | Full FG description. |
| `type` | string | `PREMIUM` / `COMMODITY`. |
| `sub_group` | string | Product sub-group (BLENDED, COTTON SEED…). |
| `variety` | string | Variety/brand (GOLD, REFINED…). |
| `sku` | string | Pack size (`1 LTR`, `5 LTR`, `13 KGS`…). |

Trimmed sample:
```json
{"status":"ok","data":[
  {"code":"FG0000149","name":"JIVO GOLD 1 LTR 20 PCS","type":"COMMODITY","sub_group":"BLENDED","variety":"GOLD","sku":"1 LTR"},
  {"code":"FG0000169","name":"REFINED COTTON SEED OIL 13 KGS","type":"COMMODITY","sub_group":"COTTON SEED","variety":"REFINED","sku":"13 KGS"}
]}
```

## Used by
- [[production-plan]] — FG search/select dropdown.

## Notes
- Read-only. Only FGs with a BOM appear (they can be exploded into RM/PM components).
