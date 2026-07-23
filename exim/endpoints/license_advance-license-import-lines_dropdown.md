---
title: "EXIM endpoint — GET /license/advance-license-import-lines/dropdown/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /license/advance-license-import-lines/dropdown/
category: license
kind: read
resource: advancelicense*/dfialicense*
auth: bearer
---

# `GET /license/advance-license-import-lines/dropdown/`

> Import-line dropdown for a license.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/license/advance-license-import-lines/dropdown/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `license_no` |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 2,
    "boe_No": "3131526",
    "boe_value_usd": "418666.250",
    "boe_date": "2022-11-02",
    "import_in_mts": "241.952",
    "license_no": "511015224"
  }
]
```

## Field reference

- `id` — internal row id of the import line; used as the value when linking an export line to this import (`linked_import_line_id`).
- `boe_No` — Bill of Entry number shown as the dropdown label.
- `boe_value_usd` — CIF value on the Bill of Entry, in USD.
- `boe_date` — Bill of Entry date (ISO date).
- `import_in_mts` — imported quantity under this BOE, in MTS (metric tonnes).
- `license_no` — license number matching the `license_no` query param; only lines of that license are returned.

## Used by pages

- [[pages/advance-license|Advance License]]

## Related endpoints

- [[endpoints/license_advance-license-headers|`GET /license/advance-license-headers/`]]
- [[endpoints/license_dfia-license-header_list|`GET /license/dfia-license-header/list/`]]
- [[endpoints/license_advance-license-import-lines|`GET /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines|`GET /license/advance-license-export-lines/`]]
- [[endpoints/post_license_advance-license-headers|`POST /license/advance-license-headers/`]]
- [[endpoints/post_license_advance-license-import-lines|`POST /license/advance-license-import-lines/`]]
- [[endpoints/license_advance-license-export-lines_create|`POST /license/advance-license-export-lines/create/`]]
- [[endpoints/license_dfia-license-header_create|`POST /license/dfia-license-header/create/`]]

## Notes

- Kind: **read**. Resource permission group: `advancelicense*/dfialicense*`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
