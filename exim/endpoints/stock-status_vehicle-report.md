---
title: "EXIM endpoint — GET /stock-status/vehicle-report/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/vehicle-report/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/vehicle-report/`

> Vehicle-wise stock grouped by a status.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/vehicle-report/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `status` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "vehicle_number": null,
    "transporter": null,
    "items": [
      {
        "item_code": "RM00MDEO",
        "item_name": "MUSTARD DEO",
        "vendor_code": "VENDA000930",
        "vendor_name": "VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED",
        "total_quantity_in_litre": 43582.37,
        "total_quantity_in_mts": 39.66,
        "eta": null,
        "arrival_date": null,
        "status": "IN_CONTRACT",
        "job_work": null,
        "rate": 154.8
      },
      {
        "item_code": "RM00MRD",
        "item_name": "MUSTARD REFINED DARK",
        "vendor_code": "VENDA000224",
        "vendor_name": "AWL AGRI BUSINESS LIMITED",
        "total_quantity_in_litre": 18527.45,
        "total_quantity_in_mts": 16.86,
        "eta": null,
        "arrival_date": null,
        "status": "IN_CONTRACT",
        "job_work": null,
        "rate": 149.5
      },
      "...(+5 more of 7)"
    ]
  }
]
```

## Field reference

- Top level: array of vehicle groups — stock rows grouped by vehicle for the requested `status`.
- `vehicle_number` — truck registration number; `null` for stock not yet assigned to a vehicle (e.g. IN_CONTRACT).
- `transporter` — transport company hauling the vehicle; `null` when no vehicle is assigned.
- `items[]` — stock lines on that vehicle:
  - `item_code` / `item_name` — SAP item code and oil name (e.g. `RM00MDEO`, MUSTARD DEO).
  - `vendor_code` / `vendor_name` — SAP supplier code and name.
  - `total_quantity_in_litre` — quantity in litres.
  - `total_quantity_in_mts` — same quantity in metric tonnes.
  - `eta` — expected arrival date (ISO date, nullable).
  - `arrival_date` — actual arrival date (ISO date, nullable).
  - `status` — stock lifecycle status (the `status` query filter value, e.g. `IN_CONTRACT`).
  - `job_work` — job-work reference if the stock is out for third-party processing, else `null`.
  - `rate` — contracted rate (₹ per kg, e.g. 154.8).

## Used by pages

- [[pages/director-dashboard|Director Dashboard]]
- [[pages/vehicle-report|Vehicle Report]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-dashboard|`GET /stock-status/stock-dashboard/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_id|`GET /stock-status/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
