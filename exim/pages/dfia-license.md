---
title: DFIA License
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /license/dfia-license
section: License
---

# DFIA License

[[INDEX|JIVO EXIM]] › **License** › DFIA License

**Route:** `/license/dfia-license`  ·  **Web:** `https://exim.jivo.in/license/dfia-license`

## What this page does

Lists JIVO's DFIA (Duty Free Import Authorisation) license headers via `GET /license/dfia-license-header/list/`, the DFIA counterpart of the Advance License register. New DFIA headers are entered with `POST /license/dfia-license-header/create/`. The register is currently empty in the sample data, so the page shows the header list plus the create form.

## How it helps

DFIA licenses let JIVO import edible-oil inputs duty free against completed exports; keeping them registered here gives ops and finance one place to record each authorisation instead of tracking DGFT paperwork offline, alongside the Advance License register.

## Backend endpoints

- [[endpoints/license_dfia-license-header_list|`GET /license/dfia-license-header/list/`]] — DFIA license headers list.
- [[endpoints/license_dfia-license-export-lines_dropdown|`GET /license/dfia-license-export-lines/dropdown/`]] — DFIA export-line dropdown for a license file.

## Key data & interactions

- DFIA header list table fed by `GET /license/dfia-license-header/list/` (empty state when no licenses are recorded)
- Add-DFIA form posting a header object to `POST /license/dfia-license-header/create/`
- No query filters on the list endpoint; the table loads the full register on open/refresh

## Related pages (same section)

- [[pages/advance-license|Advance License]]


Linked: [[INDEX]] · [[API-INVENTORY]]
