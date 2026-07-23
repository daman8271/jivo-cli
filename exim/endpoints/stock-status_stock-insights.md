---
title: "EXIM endpoint — GET /stock-status/stock-insights/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/stock-insights/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/stock-insights/`

> Aggregate stock KPIs (value, qty, avg price).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/stock-insights/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "summary": {
    "total_value": 1227724680.22636,
    "total_qty": 7905497.56,
    "total_qty_kg": 7905497.56,
    "total_qty_litre": 8687351.27,
    "total_count": 222,
    "weighted_sum_kg": 1227724680.22636,
    "weighted_sum_liter": 1227723555.01978,
    "avg_price_per_kg": 155.3,
    "avg_price_per_ltr": 141.32
  }
}
```

## Field reference

- `summary.total_value` — total value of all stock (₹; ~₹122.77 Cr here).
- `summary.total_qty` — total stock quantity (kg; same number as `total_qty_kg`).
- `summary.total_qty_kg` — total quantity in kg (~7,905 MTS).
- `summary.total_qty_litre` — total quantity converted to litres.
- `summary.total_count` — number of stock-status records aggregated (222).
- `summary.weighted_sum_kg` — sum of rate × quantity over kg-based rates (₹); numerator for `avg_price_per_kg`.
- `summary.weighted_sum_liter` — sum of litre-rate × litre-quantity (₹); numerator for `avg_price_per_ltr`.
- `summary.avg_price_per_kg` — quantity-weighted average price (₹ per kg, 155.3).
- `summary.avg_price_per_ltr` — quantity-weighted average price (₹ per litre, 141.32).

## Used by pages

- [[pages/stock-status|Stock Status]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]
- [[endpoints/stock-status_id|`GET /stock-status/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
