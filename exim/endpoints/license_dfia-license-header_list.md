---
title: "EXIM endpoint — GET /license/dfia-license-header/list/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /license/dfia-license-header/list/
category: license
kind: read
resource: advancelicense*/dfialicense*
auth: bearer
---

# `GET /license/dfia-license-header/list/`

> DFIA license headers list.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/license/dfia-license-header/list/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[]
```

## Field reference

- Sample is an empty array — no DFIA (Duty Free Import Authorisation) licenses recorded yet, so no per-record fields to document from live data.
- Each element, when present, is a DFIA license header; expect the shape defined by `POST /license/dfia-license-header/create/`, analogous to the Advance Authorisation headers in `GET /license/advance-license-headers/` (license number, dates, values, quantities in MTS).

## Used by pages

- [[pages/dfia-license|DFIA License]]

## Related endpoints

- [[endpoints/license_advance-license-headers|`GET /license/advance-license-headers/`]]
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
