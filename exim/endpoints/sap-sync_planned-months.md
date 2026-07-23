---
title: "EXIM endpoint — GET /sap-sync/planned-months/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap-sync/planned-months/
category: sap-sync
kind: read
resource: balance_sheet/inventory/customer_balance_sheet
auth: bearer
---

# `GET /sap-sync/planned-months/`

> Available planning months (SAP).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap-sync/planned-months/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "Planned_months": [
    {
      "AbsID": 2,
      "Code": "Nov-2024",
      "Name": "Planning Month Of November 2024",
      "UserSign": 22,
      "StartDate": "2024-11-01T00:00:00",
      "EndDate": "2024-11-30T00:00:00",
      "FormView": "M"
    },
    {
      "AbsID": 3,
      "Code": "DEC-2024",
      "Name": "Planning Month Of DEC 2024",
      "UserSign": 22,
      "StartDate": "2024-12-01T00:00:00",
      "EndDate": "2024-12-31T00:00:00",
      "FormView": "M"
    },
    "...(+21 more of 23)"
  ]
}
```

## Field reference

- `Planned_months[]` — one row per SAP planning period the Planning page can select.
- `AbsID` — SAP internal absolute ID of the period; used as the month selector value.
- `Code` — short month code (e.g. `Nov-2024`, `DEC-2024`; casing varies as entered in SAP).
- `Name` — display label (e.g. "Planning Month Of November 2024").
- `UserSign` — SAP user ID that created the period.
- `StartDate` / `EndDate` — first and last day of the planning month (ISO datetime).
- `FormView` — SAP period view flag; `M` = monthly.

## Used by pages

- [[pages/planning|Planning]]

## Related endpoints

- [[endpoints/sap-sync_balance-sheet|`GET /sap-sync/balance-sheet/`]]
- [[endpoints/sap-sync_custa_balance-sheet|`GET /sap-sync/custa/balance-sheet/`]]
- [[endpoints/sap-sync_customer-aging-balance|`GET /sap-sync/customer-aging-balance/`]]
- [[endpoints/sap-sync_finished-inventory|`GET /sap-sync/finished-inventory/`]]
- [[endpoints/sap-sync_inventory|`GET /sap-sync/inventory/`]]
- [[endpoints/sap-sync_monthly-planning|`GET /sap-sync/monthly-planning/`]]
- [[endpoints/sap-sync_open-ap|`GET /sap-sync/open-ap/`]]
- [[endpoints/sap-sync_open-ar|`GET /sap-sync/open-ar/`]]

## Notes

- Kind: **read**. Resource permission group: `balance_sheet/inventory/customer_balance_sheet`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
