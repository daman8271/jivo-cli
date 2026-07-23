---
title: Tank Logs
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/tank-logs
section: Stock
---

# Tank Logs

[[INDEX|JIVO EXIM]] › **Stock** › Tank Logs

**Route:** `/stock/tank-logs`  ·  **Web:** `https://exim.jivo.in/stock/tank-logs`

## What this page does

A chronological register of every tank movement from `GET /tank/log/`: each entry has a log_type (INWARD or outward), quantity, vehicle_number, rate, party, timestamp, created_by, and the linked stock_status row id. New inflow/outflow entries are recorded via `POST /tank/log/`. The sample data holds ~140 log entries tied back to specific stock rows.

## How it helps

The audit trail for physical tank stock: when a tank balance looks wrong, ops traces which vehicle delivered or drew how many litres, at what rate, from which party, and who logged it. It reconciles tank fill levels against the stock-status ledger via the stock_status link on each entry.

## Backend endpoints

- [[endpoints/tank_log|`GET /tank/log/`]] — Create a tank inflow/outflow log.

## Key data & interactions

- Log table columns: log_type (INWARD/outward), quantity (litres), vehicle_number, rate, party, item_code/name, arrival, created_at, created_by, linked stock_status id
- Filter by log_type and by party/vehicle; date ordering newest first
- Add-log form posting to `/tank/log/` for manual inflow/outflow entries

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/shortage-report|Shortage Report]]
- [[pages/contractual-history|Contractual History]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/tank-data|Tank Data]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]


Linked: [[INDEX]] · [[API-INVENTORY]]
