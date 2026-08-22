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

---
## 2026-08-22 — the rule above was measured, not inferred. Here is the proof.

A rescrape run probed the `/sap_sync/` namespace before reading this file, and
`/sync_logs/` recorded every call. That makes this the strongest evidence we have
that a GET here writes:

| sync_logs id | started (UTC) | type | processed | created | updated |
|---|---|---|---|---|---|
| 343–350 | 09:06–09:08 | PRD | 333 / 45 / 0 | 0 | 0 |
| **351** | **09:09:26** | **PRT** | **1** | 0 | **1** |
| 352–357, 359–361 | 09:28–09:35 | PRD | 333 / 45 / 0 | 0 | 0 |
| **358** | **09:29:04** | **PRT** | **1** | 0 | **1** |

Nineteen rows in one morning, all `triggered_by: Manual`, one per GET, and **two
production rows updated** — both re-pulls of business partner `VENDA000224` by
`GET /sap_sync/party/VENDA000224/`. `records_created` was 0 throughout and the
partner's business fields are unchanged, so the damage is two spurious sync-log
entries and two no-op row rewrites. It is still a write.

**What should have caught it, and did not:** every criterion on the list above
fired. The path was in the underscore namespace (2). The responses came back as
`{"success": true, "Items_processed": …}` and `{status, count, preview_data}` (4).
And the app reaches them from its own `/admin/sync-finished-goods-data`,
`/admin/sync-raw-material-data` and `/admin/sync-vendor-data` screens — an admin
*sync* route, visible in the harvest, sitting one hop above every one of them.
The evidence was all present and this file already named the endpoints. Read this
file before probing EXIM, not after.

**`/sap_sync/open-grpos/` is excluded too**, and stays excluded even though an
isolated call left `/sync_logs/` unchanged at 361 rows. It is in the namespace and
this file names it. One clean observation does not outrank the rule.

**`/daily-price/fetch/` and `/jivo-rate/fetch/` also stay excluded**, and here the
evidence genuinely points the other way, so the conflict is recorded rather than
resolved: repeated GETs returned byte-identical bodies 20–25 s apart,
`/daily-price/db-list/` stayed at 2,781 rows / max id 3038, `/jivo-rate/range/`
stayed at 3,475 rows / max id 3475, and no `sync_logs` row appeared. The app's own
source has GET as the preview and POST as "save prices". That is a good case for
reclassifying them as reads — but it is Daman's call, not a run's, and until he
makes it the rule as written wins.

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
