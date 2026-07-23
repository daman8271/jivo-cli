---
title: "EXIM endpoint — GET /license/advance-license-headers/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /license/advance-license-headers/
category: license
kind: read
resource: advancelicense*/dfialicense*
auth: bearer
---

# `GET /license/advance-license-headers/`

> Advance Authorisation licenses with nested import/export lines.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/license/advance-license-headers/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "license_no": "511015224",
    "import_lines": [
      {
        "id": 2,
        "boe_No": "3131526",
        "boe_value_usd": "418666.250",
        "boe_date": "2022-11-02",
        "import_in_mts": "241.952",
        "license_no": "511015224"
      }
    ],
    "export_lines": [
      {
        "id": 5,
        "linked_import_line": null,
        "linked_import_line_id": null,
        "shipping_bill_no": "6611229",
        "sb_value_usd": "111365.650",
        "sb_date": "2024-01-08",
        "export_in_mts": "106.570",
        "license_no": "511015224"
      },
      {
        "id": 6,
        "linked_import_line": null,
        "linked_import_line_id": null,
        "shipping_bill_no": "8361972",
        "sb_value_usd": "293108.200",
        "sb_date": "2024-03-15",
        "export_in_mts": "135.950",
        "license_no": "511015224"
      }
    ],
    "issue_date": "2022-10-11",
    "import_validity": "2023-10-11",
    "export_validity": "2024-04-11",
    "cif_value_inr": "37500000.000",
    "cif_value_usd": "466417.910",
    "cif_exchange_rate": "80.400",
    "fob_value_inr": "45000000.000",
    "fob_value_usd": "575447.570",
    "fob_exhange_rate": "78.200",
    "status": "CLOSE",
    "total_import_quantity": "258.000",
    "total_import": "241.952",
    "total_export": "242.520",
    "to_be_exported": "250.002",
    "balance": "7.482"
  },
  {
    "license_no": "511007116",
    "import_lines": [
      {
        "id": 1,
        "boe_No": "6907664",
        "boe_value_usd": "1392500.000",
        "boe_date": "2021-12-31",
        "import_in_mts": "500.000",
        "license_no": "511007116"
      }
    ],
    "export_lines": [
      {
        "id": 4,
        "linked_import_line": null,
        "linked_import_line_id": null,
        "shipping_bill_no": "6829939",
        "sb_value_usd": "187093.400",
        "sb_date": "2023-01-09",
        "export_in_mts": "121.695",
        "license_no": "511007116"
      },
      {
        "id": 3,
        "linked_import_line": null,
        "linked_import_line_id": null,
        "shipping_bill_no": "8500238",
        "sb_value_usd": "142538.000",
        "sb_date": "2023-03-15",
        "export_in_mts": "66.860",
        "license_no": "511007116"
      },
      "...(+2 more of 4)"
    ],
    "issue_date": "2021-12-22",
    "import_validity": "2022-12-22",
    "export_validity": "2023-06-22",
    "cif_value_inr": "54500000.000",
    "cif_value_usd": "718050.066",
    "cif_exchange_rate": "75.900",
    "fob_value_inr": "65500000.000",
    "fob_value_usd": "882749.326",
    "fob_exhange_rate": "74.200",
    "status": "CLOSE",
    "total_import_quantity": "516.000",
    "total_import": "500.000",
    "total_export": "400.174",
    "to_be_exported": "500.004",
    "balance": "99.830"
  },
  "...(+2 more of 4)"
]
```

## Field reference

- `license_no` — Advance Authorisation license number; the record key.
- `import_lines[]` — nested Bill of Entry lines booked against this license: `id`, `boe_No` (BOE number), `boe_value_usd` (CIF value in USD), `boe_date` (ISO date), `import_in_mts` (imported quantity, MTS).
- `export_lines[]` — nested Shipping Bill lines discharging the license: `id`, `linked_import_line`/`linked_import_line_id` (optional tie to a specific import line, often `null`), `shipping_bill_no`, `sb_value_usd` (FOB value in USD), `sb_date` (ISO date), `export_in_mts` (exported quantity, MTS).
- `issue_date` — license issue date (ISO date).
- `import_validity` — last date imports are allowed under the license (ISO date).
- `export_validity` — deadline for completing the export obligation (ISO date).
- `cif_value_inr` / `cif_value_usd` / `cif_exchange_rate` — sanctioned CIF import value in ₹ and USD, plus the ₹/USD rate used (e.g. 80.400).
- `fob_value_inr` / `fob_value_usd` / `fob_exhange_rate` — export obligation FOB value in ₹ and USD, plus the ₹/USD rate (field name misspelt in the API).
- `status` — license state, e.g. `CLOSE` (redeemed/closed) vs open.
- `total_import_quantity` — sanctioned import quantity on the license, MTS.
- `total_import` — quantity actually imported so far (sum of `import_in_mts`), MTS.
- `total_export` — quantity actually exported so far (sum of `export_in_mts`), MTS.
- `to_be_exported` — export obligation quantity derived from actual imports, MTS.
- `balance` — remaining export obligation (`to_be_exported` minus `total_export`), MTS.

## Used by pages

- [[pages/advance-license|Advance License]]

## Related endpoints

- [[endpoints/license_dfia-license-header_list|`GET /license/dfia-license-header/list/`]]
- [[endpoints/license_advance-license-import-lines|`GET /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines|`GET /license/advance-license-export-lines/`]]
- [[endpoints/license_advance-license-import-lines_dropdown|`GET /license/advance-license-import-lines/dropdown/`]]
- [[endpoints/post_license_advance-license-headers|`POST /license/advance-license-headers/`]]
- [[endpoints/post_license_advance-license-import-lines|`POST /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines_create|`POST /license/advance-license-export-lines/create/`]]
- [[endpoints/license_dfia-license-header_create|`POST /license/dfia-license-header/create/`]]

## Notes

- Kind: **read**. Resource permission group: `advancelicense*/dfialicense*`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
