---
title: "EXIM endpoint — GET /license/advance-license-import-lines/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /license/advance-license-import-lines/
category: license
kind: read
resource: advancelicense*/dfialicense*
auth: bearer
---

# `GET /license/advance-license-import-lines/`

> Advance-license import (BOE) lines.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/license/advance-license-import-lines/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
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
  },
  {
    "id": 3,
    "boe_No": "3831237",
    "boe_value_usd": "474373.000",
    "boe_date": "2024-05-16",
    "import_in_mts": "499.340",
    "license_no": "511023873"
  },
  "...(+2 more of 4)"
]
```

## Field reference

- `id` — internal row id of the import line.
- `boe_No` — Bill of Entry number for the import clearance (customs document).
- `boe_value_usd` — CIF value declared on the Bill of Entry, in USD.
- `boe_date` — Bill of Entry date (ISO date).
- `import_in_mts` — quantity imported under this BOE, in MTS (metric tonnes).
- `license_no` — Advance Authorisation license number this import line is booked against; joins to the header in `GET /license/advance-license-headers/`.

## Used by pages

- [[pages/advance-license|Advance License]]

## Related endpoints

- [[endpoints/license_advance-license-headers|`GET /license/advance-license-headers/`]]
- [[endpoints/license_dfia-license-header_list|`GET /license/dfia-license-header/list/`]]
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
