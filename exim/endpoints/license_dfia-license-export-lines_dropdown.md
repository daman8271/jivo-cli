---
title: "EXIM endpoint — GET /license/dfia-license-export-lines/dropdown/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /license/dfia-license-export-lines/dropdown/
category: license
kind: read
resource: dfialicenseexportlines
auth: bearer
---

# `GET /license/dfia-license-export-lines/dropdown/`

> DFIA export-line dropdown for a license file.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/license/dfia-license-export-lines/dropdown/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | `file_no` |

## Response — real sample (trimmed)

```json
// (empty)
```

## Field reference

- Sample captured empty, so no field shapes are confirmed. Per the endpoint description it returns DFIA export-line dropdown options (id plus display label) for the license identified by `file_no`, for use in select controls.

## Notes

- Read-only GET. Ported from the sibling build (`daman8271/exim`) to close a coverage gap.
- CLI: `exim <group> get-...`. Part of [[API-INVENTORY]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
