---
title: "EXIM endpoint — POST /stock-status/dashboard-order/{id}/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: POST
path: /stock-status/dashboard-order/{id}/
category: stock-status
kind: write
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `POST /stock-status/dashboard-order/{id}/`

> Reorder dashboard items.

## Request

| | |
|---|---|
| Method | `POST` |
| URL | `https://eximbe.jivo.in/stock-status/dashboard-order/{id}/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | `id` |
| Request body | `{order}` |

## ⚠️ WRITE — not wired into the CLI (v1 is read-only)

This endpoint **mutates data** on the production JIVO/SAP system. It is documented for completeness but intentionally excluded from runnable CLI commands.

## Used by pages

- _(not directly bound to a listed page)_

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]

## Notes

- Kind: **write**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Mutating; requires explicit confirmation before use.


Linked: [[API-INVENTORY]] · [[INDEX]]
