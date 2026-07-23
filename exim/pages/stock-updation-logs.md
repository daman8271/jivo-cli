---
title: Stock Updation Logs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /admin/stock-updation-logs
section: Administration
---

# Stock Updation Logs

[[INDEX|JIVO EXIM]] › **Administration** › Stock Updation Logs

**Route:** `/admin/stock-updation-logs`  ·  **Web:** `https://exim.jivo.in/admin/stock-updation-logs`

## What this page does

Displays the field-level audit trail of every stock-status edit: `GET /stock-status/stock-logs/` returns ~1,480 log entries, each with the stock record id, `action` (e.g. UPDATE), `changed_by_label` (user email such as raspreet@exim.com), timestamp, an optional note, and nested `field_logs` showing each changed field with `old_value` → `new_value` (e.g. status OUT_SIDE_FACTORY → IN_TANK, quantity 38880.00 → 38820.00). It answers who changed which stock, when, and exactly what changed.

## How it helps

When a stock quantity or lifecycle status looks wrong, this page lets an admin or director trace the exact edit and the user behind it instead of guessing. It also serves as the accountability record for manual moves through the stock lifecycle (IN_CONTRACT → ... → COMPLETED).

## Backend endpoints

- [[endpoints/stock-status_stock-logs|`GET /stock-status/stock-logs/`]] — Field-level audit log of stock-status changes.

## Key data & interactions

- Log table: Timestamp, Stock ID, Action (UPDATE), Changed By (user email), Note
- Expandable field-change detail per row: Field Name, Old Value, New Value (status transitions, quantity edits)
- Filter/search by stock id or user; newest entries first
- Refresh action; ~1,480 entries in the current log

## Related pages (same section)

- [[pages/users|Users]]
- [[pages/sync-raw-material|Sync Raw Material]]
- [[pages/sync-finished-goods|Sync Finished Goods]]
- [[pages/sync-vendor-data|Sync Vendor Data]]
- [[pages/sync-logs|Sync Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
