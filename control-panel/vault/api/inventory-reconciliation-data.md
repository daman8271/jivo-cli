---
endpoint: /inventory/reconciliation/api/data/
method: GET
auth: session + XHR header (X-Requested-With) + X-CSRFToken
readonly: true
used_by: [reconciliation]
tags: [jivo, api, inventory, reconciliation, accounts]
---
# `GET /inventory/reconciliation/api/data/`

## Purpose
Returns the **inter-company billing chains between JIVO Mart (buyer) and JIVO Wellness (seller/manufacturer)** and flags where the paperwork doesn't line up. Each chain follows **Mart PO → Wellness SO → GRPO → A/P → A/R** and is classified MATCHED / MISMATCH / INCOMPLETE by comparing tax-inclusive totals (partials summed; differences ≤ tolerance ignored). Powers the [[reconciliation]] page table + summary. See [[wellness-mart-reconciliation]].

## Request
| Param | Type | Meaning |
|---|---|---|
| `schema` | `oil` \| `beverages` | Seller company — `oil` = JIVO Wellness (oils), `beverages` = Wellness Beverages. **Default `oil`**. |
| `date_from` | `YYYY-MM-DD` *optional* | Window start. Omitted → server default (~last 3 months). |
| `date_to` | `YYYY-MM-DD` *optional* | Window end. Omitted → server default (today). |

Built as `?schema=<s>[&date_from=…][&date_to=…]`.

## Response
HTTP 200 · `application/json`. Top key `data`:

| Key | Shape | Meaning |
|---|---|---|
| `date_from` / `date_to` | date | Effective window (echoes defaults when unspecified). |
| `tolerance` | number | ₹ tolerance below which a total difference is treated as matched (default 1.0). |
| `summary` | object | `{total, matched, mismatch, incomplete, mismatch_value}` counts + total ₹ value of mismatched chains. |
| `chains` | object[] | One entry per Mart PO chain. |

`chains[]` entry:

| Field | Type | Meaning |
|---|---|---|
| `po` / `po_date` / `vendor` | — | Mart purchase order number, date, and vendor (the Wellness seller). |
| `po_total` | number | PO tax-inclusive total. |
| `po_docs` / `so_docs` / `grpo_docs` / `ap_docs` / `ar_docs` / `delivery_docs` | object[] | The linked documents at each node: `{num, date, amt}`. |
| `so` / `grpo` / `ap` / `ar` / `delivery` | number\|null | Summed amount at each node (null = missing). |
| `so_cnt` / `grpo_cnt` / … | int | Document count at each node. |
| `status` | string | `MATCHED` / `MISMATCH` / `INCOMPLETE`. |
| `detail` | string | Human note, e.g. `"Missing GRPO, A/P, A/R"`. |

Node meaning: **PO** = Mart's purchase order → **SO** = Wellness sales order → **GRPO** = Mart's goods receipt → **A/P** = Mart's A/P invoice → **A/R** = Wellness's A/R invoice (mirror). A chain is INCOMPLETE if any node is missing, MISMATCH if all present but totals differ > tolerance, else MATCHED.

Trimmed sample (`schema=oil`, default window):
```json
{"data":{"date_from":"2026-04-21","date_to":"2026-07-23","tolerance":1.0,
 "summary":{"total":214,"matched":91,"mismatch":68,"incomplete":55,"mismatch_value":124924207.84},
 "chains":[{"po":726224560,"po_date":"2026-07-22","vendor":"JIVO WELLNESS PVT LTD","po_total":1668408.0,
   "po_docs":[{"num":"726224560","date":"2026-07-22","amt":1668408.0}],
   "so":1668408.0,"so_cnt":1,"so_docs":[{"num":"1726076733","date":"2026-07-22","amt":1668408.0}],
   "grpo":null,"grpo_cnt":0,"ap":null,"ar":null,
   "status":"INCOMPLETE","detail":"Missing GRPO, A/P, A/R"}]}}
```

## Used by
- [[reconciliation]] — summary KPIs, status-filtered chain table, per-chain document drill.

## Notes
- Read-only. The page's **CSV export** is a separate route `GET /inventory/reconciliation/export/?schema=both&only=<broken|all>&date_from=&date_to=` — it **always** uses `schema=both` so a PO split across Oil+Beverages reconciles in one sheet (file download, **not probed**).
