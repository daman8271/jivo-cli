---
title: Users
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /admin/users
section: Administration
---

# Users

[[INDEX|JIVO EXIM]] › **Administration** › Users

**Route:** `/admin/users`  ·  **Web:** `https://exim.jivo.in/admin/users`

## What this page does

Lists the application's user accounts from `GET /account/users/`: 12 users, each with `id`, `name`, and `email` (e.g. Karishma Soni / karishma@exim.com, Factory User / factory@exim.com). It is the admin roster of who can log in to EXIM.

## How it helps

An admin opens this page to see who has access to the platform and to match audit-log emails (as shown in Stock Updation Logs' `changed_by_label`) to real people. Useful when onboarding/offboarding staff or investigating who made a change.

## Backend endpoints

- [[endpoints/account_users|`GET /account/users/`]] — List of application user accounts (id, name, email).

## Key data & interactions

- User table: ID, Name, Email (12 accounts)
- Search/filter by name or email
- Refresh action to reload the account list

## Related pages (same section)

- [[pages/sync-raw-material|Sync Raw Material]]
- [[pages/sync-finished-goods|Sync Finished Goods]]
- [[pages/sync-vendor-data|Sync Vendor Data]]
- [[pages/sync-logs|Sync Logs]]
- [[pages/stock-updation-logs|Stock Updation Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
