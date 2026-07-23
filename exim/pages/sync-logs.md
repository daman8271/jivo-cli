---
title: Sync Logs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /admin/sync-logs
section: Administration
---

# Sync Logs

[[INDEX|JIVO EXIM]] › **Administration** › Sync Logs

**Route:** `/admin/sync-logs`  ·  **Web:** `https://exim.jivo.in/admin/sync-logs`

## What this page does

Shows the run history of SAP sync jobs: `GET /sync_logs/` returns ~340 entries with `sync_type` (e.g. PRT for parties), `status` (SCS success / FLD failed), `triggered_by` (Manual), `started_at`/`completed_at` timestamps, record counts (`records_procesed`, `records_created`, `records_updated`), and the full `error_message` on failure (e.g. a SQL relation error). It tells an admin whether the last item/party/inventory pull from SAP actually worked and how many records it touched.

## How it helps

When items, parties, or inventory look stale in EXIM, this page is the first stop: it shows whether the sync ran, failed, or processed zero records, with the exact error message for debugging. It keeps SAP-to-EXIM data trust auditable without SAP access.

## Backend endpoints

- [[endpoints/sync_logs|`GET /sync_logs/`]] — History of SAP sync jobs (type, status, counts).

## Key data & interactions

- Log table: Sync Type (e.g. PRT), Status (SCS/FLD), Triggered By (Manual), Started At, Completed At, Records Processed / Created / Updated, Error Message
- Status badges distinguishing success from failed runs; failed rows expose the full error text
- Filter by sync type or status; newest runs first
- Refresh action; ~340 runs in the current history

## Related pages (same section)

- [[pages/users|Users]]
- [[pages/sync-raw-material|Sync Raw Material]]
- [[pages/sync-finished-goods|Sync Finished Goods]]
- [[pages/sync-vendor-data|Sync Vendor Data]]
- [[pages/stock-updation-logs|Stock Updation Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
