---
endpoint: /inventory/reconciliation/api/ledgers/
method: GET
auth: session + XHR header (X-Requested-With) + X-CSRFToken
readonly: true
used_by: [reconciliation]
tags: [jivo, api, inventory, reconciliation, accounts]
---
# `GET /inventory/reconciliation/api/ledgers/`

## Purpose
Returns the **business-partner ledgers behind the Wellness–Mart reconciliation**, pivoted by **ORIGIN (document type)** for each side — the **JIVO Mart** BP ledger and the **JIVO Wellness** BP ledger — with debit/credit/balance totals per origin. Powers the "Ledgers" tab of the [[reconciliation]] page (the cash-side view of the same [[wellness-mart-reconciliation]] chains). Cancellation entries are excluded; Balance = Debit − Credit (LC = local currency).

## Request
| Param | Type | Meaning |
|---|---|---|
| `schema` | `oil` \| `beverages` | Seller company. |
| `date_from` | `YYYY-MM-DD` *optional* | Window start (page's From). |
| `date_to` | `YYYY-MM-DD` *optional* | Window end (page's To). |

Same `qs()` builder as [[inventory-reconciliation-data]] (`schema` + optional dates).

## Response
HTTP 200 · `application/json`. Top key `data`:

| Key | Shape | Meaning |
|---|---|---|
| `date_from` / `date_to` / `company` | — | Echo of the window + seller company. |
| `mart` | object | JIVO Mart BP ledger — `{rows[], total}`. |
| `wellness` | object | JIVO Wellness BP ledger — `{rows[], total}`. |

Each `rows[]` entry:

| Field | Type | Meaning |
|---|---|---|
| `origin` | string | SAP document-type origin code — e.g. `PC` (A/P invoice), `PS` (goods receipt PO), `IN` (A/R invoice). Determines which SAP object posted the ledger line. |
| `debit` | number | Sum of debit (LC). |
| `credit` | number | Sum of credit (LC). |
| `count` | int | Number of documents of that origin. |
| `balance` | number | `debit − credit` (LC). |

`total` = `{debit, credit, balance}` for that side.

Trimmed sample (`schema=oil&date_from=2026-07-22&date_to=2026-07-22`):
```json
{"data":{"date_from":"2026-07-22","date_to":"2026-07-22","company":"oil",
 "mart":{"rows":[{"origin":"PC","debit":34952967.0,"credit":0.0,"count":4,"balance":34952967.0},
                 {"origin":"PS","debit":6400000.0,"credit":0.0,"count":2,"balance":6400000.0}],
         "total":{"debit":41352967.0,"credit":0.0,"balance":41352967.0}},
 "wellness":{"rows":[{"origin":"IN","debit":100043555.0,"credit":0.0,"count":11,"balance":100043555.0}],
             "total":{"debit":100043555.0,"credit":0.0,"balance":100043555.0}}}}
```

## Used by
- [[reconciliation]] — "Ledgers" tab (Mart vs Wellness BP ledger pivot).

## Notes
- Read-only. `origin` is the SAP OBTF/transaction origin code (PC/PS/IN/…), i.e. which document type generated each ledger posting. Cancellation entries are filtered out server-side.
