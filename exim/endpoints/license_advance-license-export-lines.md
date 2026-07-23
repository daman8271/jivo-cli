---
title: "EXIM endpoint — GET /license/advance-license-export-lines/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /license/advance-license-export-lines/
category: license
kind: read
resource: advancelicense*/dfialicense*
auth: bearer
---

# `GET /license/advance-license-export-lines/`

> Advance-license export (shipping bill) lines.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/license/advance-license-export-lines/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
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
  "...(+7 more of 9)"
]
```

## Field reference

- `id` — internal row id of the export line.
- `linked_import_line` / `linked_import_line_id` — optional link to the import (BOE) line this export fulfils; `null` when the export is not tied to a specific import line.
- `shipping_bill_no` — Shipping Bill number for the export (customs document).
- `sb_value_usd` — FOB value on the Shipping Bill, in USD.
- `sb_date` — Shipping Bill date (ISO date).
- `export_in_mts` — quantity exported under this Shipping Bill, in MTS (metric tonnes); counts toward the license export obligation.
- `license_no` — Advance Authorisation license number this export line discharges; joins to `GET /license/advance-license-headers/`.

## Used by pages

- [[pages/advance-license|Advance License]]

## Related endpoints

- [[endpoints/license_advance-license-headers|`GET /license/advance-license-headers/`]]
- [[endpoints/license_dfia-license-header_list|`GET /license/dfia-license-header/list/`]]
- [[endpoints/license_advance-license-import-lines|`GET /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-import-lines_dropdown|`GET /license/advance-license-import-lines/dropdown/`]]
- [[endpoints/post_license_advance-license-headers|`POST /license/advance-license-headers/`]]
- [[endpoints/post_license_advance-license-import-lines|`POST /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines_create|`POST /license/advance-license-export-lines/create/`]]
- [[endpoints/license_dfia-license-header_create|`POST /license/dfia-license-header/create/`]]

## Notes

- Kind: **read**. Resource permission group: `advancelicense*/dfialicense*`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
