---
title: "JIVO EXIM — Knowledge Base (Map of Content)"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: map
tags: [jivogpt, exim, map-of-content]
---

# JIVO EXIM — Knowledge Base (Map of Content)

> Reverse-engineered documentation of the JIVO EXIM platform (`https://exim.jivo.in`, API `https://eximbe.jivo.in`).
> Every **page** and every **API endpoint** is documented as an identical-format note. Links are Obsidian wikilinks.

## Start here

- [[CLI/exim/README|README]] — what this vault is & how to use the `exim` CLI
- [[CLI/exim/ARCHITECTURE|ARCHITECTURE]] — how the app is built (SPA + REST + SAP sync)
- [[AUTH]] — login / JWT / refresh flow
- [[DOMAIN-MODEL]] — entities & permission resources
- [[API-INVENTORY]] — table of all endpoints

**Scale:** 38 pages · 66 safe read/detail catalogue entries (65 unique GET routes) · 34 write/sync entries.

## Pages by section

### Reports
- [[pages/contracts|Contracts]] — `/reports/contracts`
- [[pages/dashboard|Dashboard]] — `/dashboard`
- [[pages/director-dashboard|Director Dashboard]] — `/reports/director-dashboard`
- [[pages/planning|Planning]] — `/reports/planning`
- [[pages/stock-dashboard|Stock Dashboard]] — `/stock-dashboard`
- [[pages/vehicle-report|Vehicle Report]] — `/reports/vehicle-report`
- [[pages/warehouse-inventory|Warehouse Inventory]] — `/stock/warehouse-inventory`

### Stock
- [[pages/contractual-history|Contractual History]] — `/stock/contractual-history`
- [[pages/in-tank-breakdown|In Tank Breakdown]] — `/stock/in-tank-breakdown`
- [[pages/shortage-report|Shortage Report]] — `/stock/variance`
- [[pages/stock-status|Stock Status]] — `/stock/stock-status`
- [[pages/tank-data|Tank Data]] — `/stock/tank-data`
- [[pages/tank-items|Tank Items]] — `/stock/tank-items`
- [[pages/tank-logs|Tank Logs]] — `/stock/tank-logs`
- [[pages/tank-monitoring|Tank Monitoring]] — `/stock/tank-monitoring`

### Domestic Contracts
- [[pages/domestic-contracts|Domestic Contracts (FY 2025-26)]] — `/domestic-contracts`
- [[pages/domestic-2627|Domestic Contracts (FY 2026-27)]] — `/contracts/domestic-2627`
- [[pages/open-grpos|Open GRPOs]] — `/contracts/open-grpos`

### Accounts
- [[pages/customer-aging|Customer Aging]] — `/accounts/customer-aging`
- [[pages/customer-outstanding|Customer Outstanding]] — `/accounts/customer-outstanding`
- [[pages/exim-account|Oil Dr/Cr Outstanding]] — `/exim-account`
- [[pages/open-aps|Open APs]] — `/accounts/open-aps`
- [[pages/open-ars|Open ARs]] — `/accounts/open-ars`
- [[pages/open-pos|Open POs]] — `/accounts/open-pos`
- [[pages/vendor-outstanding|Vendor Outstanding]] — `/accounts/vendor-outstanding`

### Commodity Price
- [[pages/daily-price|Daily Price]] — `/commodity/daily-price`
- [[pages/jivo-rates|Jivo Rates]] — `/commodity/jivo-rates`
- [[pages/market-rates|Market Rates]] — `/commodity/market-rates`
- [[pages/our-rates|Our Rates]] — `/commodity/our-rates`

### Exchange Rates
- [[pages/exim-rates|Exchange Rates]] — `/exim-rates`

### License
- [[pages/advance-license|Advance License]] — `/license/advance-license`
- [[pages/dfia-license|DFIA License]] — `/license/dfia-license`

### Administration
- [[pages/stock-updation-logs|Stock Updation Logs]] — `/admin/stock-updation-logs`
- [[pages/sync-finished-goods|Sync Finished Goods]] — `/admin/sync-finished-goods-data`
- [[pages/sync-logs|Sync Logs]] — `/admin/sync-logs`
- [[pages/sync-raw-material|Sync Raw Material]] — `/admin/sync-raw-material-data`
- [[pages/sync-vendor-data|Sync Vendor Data]] — `/admin/sync-vendor-data`
- [[pages/users|Users]] — `/admin/users`

Linked: [[docs/EXIM_MAP|EXIM_MAP]] · [[CLI/exim/README|EXIM README]] · [[CLI/exim/API-INVENTORY|API-INVENTORY]]
