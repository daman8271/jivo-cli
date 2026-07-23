---
title: "EXIM endpoint — GET /stock-status/debit-insights/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/debit-insights/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/debit-insights/`

> Aggregate shortage/debit totals.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/debit-insights/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "total_deduction_shortager": 4.574,
  "total_records": 130,
  "total_deduction_amount": 711668.539
}
```

## Field reference

- `total_deduction_shortager` — total shortage quantity actually deducted across all debit entries (MTS; 4.574 MTS here).
- `total_records` — count of debit/shortage entries aggregated (130), matching the row count of `GET /stock-status/debit-entries/`.
- `total_deduction_amount` — total money deducted from suppliers for shortages (₹; ~₹7.12 Lakh here).

## Used by pages

- [[pages/shortage-report|Shortage Report]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]
- [[endpoints/stock-status_id|`GET /stock-status/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
