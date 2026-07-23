---
title: "EXIM endpoint — GET /stock-status/stock-dashboard/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /stock-status/stock-dashboard/
category: stock-status
kind: read
resource: stockstatus/debitentry/vehicle_report
auth: bearer
---

# `GET /stock-status/stock-dashboard/`

> Multi-dimensional stock dashboard (in/outside factory, by status/vendor).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/stock-status/stock-dashboard/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `rounding` |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "summary": {
    "outside_factory_total": 104275.0,
    "active_items": 12
  },
  "status_vendors": {
    "ON_THE_WAY": [
      "AWL AGRI BUSINESS LIMITED",
      "DHANLAXMI EDIBLES PRIVATE LIMITED",
      "...(+2 more of 4)"
    ],
    "UNDER_LOADING": [
      "DHANLAXMI EDIBLES PRIVATE LIMITED"
    ],
    "AT_REFINERY": [
      "EDIBLE OIL CO D LLC",
      "GRAINCORP OILSEEDS PTY LTD"
    ],
    "ON_THE_SEA": [
      "MIGASA ACEITES S L U"
    ],
    "IN_CONTRACT": [
      "AWL AGRI BUSINESS LIMITED",
      "M/S ARORA AGRI BUSINESS VENTURES",
      "...(+1 more of 3)"
    ],
    "COMPLETED": [
      "ALBA EDIBLE OILS PTY LTD",
      "AWL AGRI BUSINESS LIMITED",
      "...(+9 more of 11)"
    ]
  },
  "items": [
    {
      "item_code": "RMMKG02",
      "item_name": "MUSTARD KACHI GHANI 2B",
      "dashboard_id": 14,
      "outside_factory": 0,
      "status_data": {
        "ON_THE_WAY__AWL AGRI BUSINESS LIMITED": 0,
        "ON_THE_WAY__DHANLAXMI EDIBLES PRIVATE LIMITED": 0,
        "ON_THE_WAY__M/S ARORA AGRI BUSINESS VENTURES": 0,
        "ON_THE_WAY__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 0,
        "UNDER_LOADING__DHANLAXMI EDIBLES PRIVATE LIMITED": 0,
        "AT_REFINERY__EDIBLE OIL CO D LLC": 0,
        "AT_REFINERY__GRAINCORP OILSEEDS PTY LTD": 0,
        "ON_THE_SEA__MIGASA ACEITES S L U": 0,
        "IN_CONTRACT__AWL AGRI BUSINESS LIMITED": 0,
        "IN_CONTRACT__M/S ARORA AGRI BUSINESS VENTURES": 0,
        "IN_CONTRACT__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 0,
        "COMPLETED__ALBA EDIBLE OILS PTY LTD": 0,
        "COMPLETED__AWL AGRI BUSINESS LIMITED": 0,
        "COMPLETED__DHANLAXMI EDIBLES PRIVATE LIMITED": 0,
        "COMPLETED__DIL EXIM COMMODITIES PRIVATE LIMITED": 0,
        "COMPLETED__EDIBLE OIL CO D LLC": 0,
        "COMPLETED__GRAINCORP OILSEEDS PTY LTD": 0,
        "COMPLETED__JIVO WELLNESS PVT LTD - DL": 87815.09,
        "COMPLETED__M/S ARORA AGRI BUSINESS VENTURES": 0,
        "COMPLETED__MIGASA ACEITES S L U": 0,
        "COMPLETED__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 0,
        "COMPLETED__VAISHNODEVI REFOILS AND SOLEX": 0
      },
      "total": 87815.09
    },
    {
      "item_code": "RM00GNR",
      "item_name": "GROUNDNUT REFINED",
      "dashboard_id": 15,
      "outside_factory": 0,
      "status_data": {
        "ON_THE_WAY__AWL AGRI BUSINESS LIMITED": 0,
        "ON_THE_WAY__DHANLAXMI EDIBLES PRIVATE LIMITED": 41575.0,
        "ON_THE_WAY__M/S ARORA AGRI BUSINESS VENTURES": 0,
        "ON_THE_WAY__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 0,
        "UNDER_LOADING__DHANLAXMI EDIBLES PRIVATE LIMITED": 42000.0,
        "AT_REFINERY__EDIBLE OIL CO D LLC": 0,
        "AT_REFINERY__GRAINCORP OILSEEDS PTY LTD": 0,
        "ON_THE_SEA__MIGASA ACEITES S L U": 0,
        "IN_CONTRACT__AWL AGRI BUSINESS LIMITED": 0,
        "IN_CONTRACT__M/S ARORA AGRI BUSINESS VENTURES": 0,
        "IN_CONTRACT__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 0,
        "COMPLETED__ALBA EDIBLE OILS PTY LTD": 0,
        "COMPLETED__AWL AGRI BUSINESS LIMITED": 0,
        "COMPLETED__DHANLAXMI EDIBLES PRIVATE LIMITED": 165249.97,
        "COMPLETED__DIL EXIM COMMODITIES PRIVATE LIMITED": 0,
        "COMPLETED__EDIBLE OIL CO D LLC": 0,
        "COMPLETED__GRAINCORP OILSEEDS PTY LTD": 0,
        "COMPLETED__JIVO WELLNESS PVT LTD - DL": 0,
        "COMPLETED__M/S ARORA AGRI BUSINESS VENTURES": 0,
        "COMPLETED__MIGASA ACEITES S L U": 0,
        "COMPLETED__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 0,
        "COMPLETED__VAISHNODEVI REFOILS AND SOLEX": 0
      },
      "total": 248824.97
    },
    "...(+10 more of 12)"
  ],
  "totals": {
    "outside_factory": 104275.0,
    "status_vendor_totals": {
      "ON_THE_WAY__AWL AGRI BUSINESS LIMITED": 39880.0,
      "ON_THE_WAY__DHANLAXMI EDIBLES PRIVATE LIMITED": 82555.0,
      "ON_THE_WAY__M/S ARORA AGRI BUSINESS VENTURES": 40060.0,
      "ON_THE_WAY__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 80100.0,
      "UNDER_LOADING__DHANLAXMI EDIBLES PRIVATE LIMITED": 42000.0,
      "AT_REFINERY__EDIBLE OIL CO D LLC": 433.0,
      "AT_REFINERY__GRAINCORP OILSEEDS PTY LTD": 156026.2,
      "ON_THE_SEA__MIGASA ACEITES S L U": 44000.0,
      "IN_CONTRACT__AWL AGRI BUSINESS LIMITED": 653360.0,
      "IN_CONTRACT__M/S ARORA AGRI BUSINESS VENTURES": 32760.0,
      "IN_CONTRACT__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 39660.0,
      "COMPLETED__ALBA EDIBLE OILS PTY LTD": 248618.0,
      "COMPLETED__AWL AGRI BUSINESS LIMITED": 1537990.0,
      "COMPLETED__DHANLAXMI EDIBLES PRIVATE LIMITED": 369149.97,
      "COMPLETED__DIL EXIM COMMODITIES PRIVATE LIMITED": 480089.97,
      "COMPLETED__EDIBLE OIL CO D LLC": 76814.0,
      "COMPLETED__GRAINCORP OILSEEDS PTY LTD": 696698.0,
      "COMPLETED__JIVO WELLNESS PVT LTD - DL": 87815.09,
      "COMPLETED__M/S ARORA AGRI BUSINESS VENTURES": 608180.0,
      "COMPLETED__MIGASA ACEITES S L U": 21850.0,
      "COMPLETED__VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED": 605010.0,
      "COMPLETED__VAISHNODEVI REFOILS AND SOLEX": 82880.0
    },
    "status_totals": {
      "ON_THE_WAY": 242595.0,
      "UNDER_LOADING": 42000.0,
      "AT_REFINERY": 156459.2,
      "ON_THE_SEA": 44000.0,
      "IN_CONTRACT": 725780.0,
      "COMPLETED": 4815095.03
    },
    "grand_total": 6130204.2299999995
  }
}
```

## Field reference

- `summary.outside_factory_total` — total quantity currently outside the factory across all items (kg).
- `summary.active_items` — number of items on the dashboard (12).
- `status_vendors` — map of lifecycle status → list of vendor names that currently have stock in that status; defines the dashboard's column set.
- `items[]` — one row per item:
  - `item_code` / `item_name` — SAP item code and oil name.
  - `dashboard_id` — row's position/id on the dashboard grid.
  - `outside_factory` — this item's quantity outside the factory (kg).
  - `status_data` — quantity (kg) per `STATUS__VENDOR` cell (e.g. `"ON_THE_WAY__DHANLAXMI EDIBLES PRIVATE LIMITED": 41575.0`); 0 where that vendor holds none of this item.
  - `total` — row total across all cells (kg).
- `totals` — column footer:
  - `outside_factory` — grand outside-factory quantity (kg), matches `summary.outside_factory_total`.
  - `status_vendor_totals` — per `STATUS__VENDOR` column totals (kg).
  - `status_totals` — quantity per lifecycle status summed over vendors (kg).
  - `grand_total` — all stock across every status and vendor (kg; ~6,130 MTS here).
- `rounding` query param controls decimal rounding of the quantities.

## Used by pages

- [[pages/stock-dashboard|Stock Dashboard]]

## Related endpoints

- [[endpoints/stock-status|`GET /stock-status/`]]
- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]]
- [[endpoints/stock-status_debit-entries|`GET /stock-status/debit-entries/`]]
- [[endpoints/stock-status_debit-insights|`GET /stock-status/debit-insights/`]]
- [[endpoints/stock-status_stock-insights|`GET /stock-status/stock-insights/`]]
- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]]
- [[endpoints/stock-status_vehicle-report|`GET /stock-status/vehicle-report/`]]
- [[endpoints/stock-status_id|`GET /stock-status/{id}/`]]

## Notes

- Kind: **read**. Resource permission group: `stockstatus/debitentry/vehicle_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
