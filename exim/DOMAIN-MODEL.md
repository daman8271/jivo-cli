---
title: "Domain Model & Permissions"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, exim, domain-model]
---

# Domain Model & Permissions

> Resources and allowed operations, taken from the live login permission map (user id 34).

## Entities (high level)

- **Stock Status** — imported raw-material stock lots moving through statuses (IN_CONTRACT → ON_THE_SEA → MUNDRA_PORT → ON_THE_WAY → AT_REFINERY → UNDER_LOADING → COMPLETED). See [[pages/stock-status|Stock Status]].
- **Tanks** — physical storage tanks + tank items (oils), fill levels, logs. See [[pages/tank-monitoring|Tank Monitoring]].
- **Domestic Contracts (DC)** — POs / delivery challans by financial year. See [[pages/domestic-contracts|Domestic Contracts]].
- **Licenses** — Advance Authorisation & DFIA import/export licenses. See [[pages/advance-license|Advance License]].
- **Items / Parties** — SAP-synced RM/FG item masters & business partners.
- **Rates / Prices** — daily commodity prices, JIVO rates, market rates, exchange rates.
- **Accounts** — SAP-synced open AR/AP/PO/GRPO, balance sheets, aging.

## Permission resources (from token)

| Resource | Ops |
|---|---|
| `advancelicenseexportlines` | change, add, view, delete |
| `advancelicenseheaders` | change, view, add, delete |
| `advancelicenseimportlines` | add, delete, change, view |
| `advancelicenselines` | add, view, delete, change |
| `balance_sheet` | sync |
| `contractualhistory` | add, change, view, delete |
| `customer_balance_sheet` | view |
| `daily_price` | fetch |
| `daily_price_graph` | view |
| `dailyprice` | delete, view, change, add |
| `dashboardorder` | change, view, delete, add |
| `dashboardsnapshot` | change, add, delete, view |
| `debitentry` | add, delete, change, view |
| `dfia_line_insights` | view |
| `dfialicenseexportlines` | add, change, delete, view |
| `dfialicenseheader` | delete, add, change, view |
| `dfialicenseimportlines` | change, add, delete, view |
| `dfialicenselines` | view, delete, add, change |
| `director_report` | view |
| `domesticcontract` | change, delete, view, add |
| `domesticcontracts` | add, view, change, delete |
| `domesticreports` | delete, add, change, view |
| `exim_rates` | view |
| `fg` | sync |
| `fgproducts` | view, change, add, delete |
| `inventory` | sync |
| `itemwise_average` | view |
| `jivo_rate` | fetch |
| `jivo_rates` | fetch |
| `jivorates` | add, change, view, delete |
| `line_insights` | view |
| `open_grpos` | sync |
| `opening_rate` | add |
| `party` | add, view, sync, change, delete |
| `po` | sync |
| `products` | view, change, add, delete |
| `rm` | sync |
| `rmproducts` | delete, change, add, view |
| `stockstatus` | change, view, delete, add |
| `stockstatuschangesession` | view, delete, add, change |
| `stockstatusfieldlog` | delete, view, change, add |
| `stockstatusupdatelog` | add, view, change, delete |
| `synclogs` | change, add, delete, view |
| `tankdata` | delete, change, view, add |
| `tankitem` | change, view, add, delete |
| `tanklayer` | change, delete, add, view |
| `tanklog` | delete, change, view, add |
| `tanklogconsumption` | view, delete, change, add |
| `user` | delete, change, add, view |
| `vehicle_report` | view |

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
