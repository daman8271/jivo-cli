---
title: Contractual History
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: page
tags: [jivogpt, exim, page]
route: /stock/contractual-history
section: Stock
---

# Contractual History

[[INDEX|JIVO EXIM]] › **Stock** › Contractual History

**Route:** `/stock/contractual-history`  ·  **Web:** `https://exim.jivo.in/stock/contractual-history`

## What this page does

A read-only list of past purchase contracts from `GET /stock-status/contractual-history/`: each row shows item_code/item_name (e.g. RM000MR MUSTARD REFINED), vendor_code/vendor_name, the contracted rate, contract_start and contract_end dates, plus who created the record and when. The sample holds 20 historical contracts across vendors like AWL AGRI BUSINESS LIMITED and M/S ARORA AGRI BUSINESS VENTURES.

## How it helps

Rate benchmarking for new deals: before signing a fresh domestic contract, procurement checks what rate the same item fetched from each vendor in earlier contract windows (e.g. MUSTARD REFINED at ₹145 vs ₹147/unit two days apart from different vendors). It also documents the contract trail for finance and audit.

## Backend endpoints

- [[endpoints/stock-status_contractual-history|`GET /stock-status/contractual-history/`]] — Contractual history of stock items (rates, contract dates).

## Key data & interactions

- Table columns: item_code, item_name, vendor_code, vendor_name, rate, contract_start, contract_end, created_at, created_by
- Filter/search by item code and vendor name to compare rates across contracts
- Sorted newest contract first (by created_at)

## Related pages (same section)

- [[pages/stock-status|Stock Status]]
- [[pages/shortage-report|Shortage Report]]
- [[pages/tank-items|Tank Items]]
- [[pages/tank-monitoring|Tank Monitoring]]
- [[pages/tank-data|Tank Data]]
- [[pages/in-tank-breakdown|In Tank Breakdown]]
- [[pages/tank-logs|Tank Logs]]


Linked: [[INDEX]] · [[API-INVENTORY]]
