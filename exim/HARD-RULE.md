---
title: "HARD RULE — JIVO EXIM is Read-Only"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, exim, read-only]
---

⛔ HARD RULE — JIVO EXIM IS READ-ONLY.
Only ever READ / FETCH from exim.jivo.in (API eximbe.jivo.in).
NEVER write, create, update, delete, PATCH/POST/PUT/DELETE, or trigger a sync.
This is production JIVO + SAP data. No writes, ever, without explicit per-request approval from Daman.


---
## How to tell a WRITE from a READ in EXIM (GET is NOT a safety guarantee)
An endpoint MUTATES data (exclude from read tooling) if ANY of these hold:
1. Method is POST / PUT / PATCH / DELETE.
2. It is in the underscore `/sap_sync/` namespace (the hyphen `/sap-sync/` family are reads of already-synced data).
3. Its token permission for that resource is ONLY `fetch` or `sync` (no `view`) — e.g. rm, fg, po, inventory, open_grpos, balance_sheet, daily_price, jivo_rate.
4. Its response is an import-result shape: `{status, count, preview_data}` or `{success, Items_processed}`.
5. Path contains create / dispatch / move / register / update / delete, or ends in `/fetch/` with a fetch permission.

Several EXIM endpoints are GETs that WRITE (the app fires them on page load to refresh). Excluded from the CLI: `/sap_sync/rm/items/`, `/sap_sync/fg/items/`, `/sap_sync/party/*`, `/sap_sync/open-grpos/`, `/daily-price/fetch/`, `/jivo-rate/fetch/`, plus all POST/PATCH/DELETE. Kept as reads: `/exim-rates/fetch/` (permission=view, plain data).

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
