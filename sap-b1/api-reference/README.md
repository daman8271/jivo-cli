# SAP Business One — Service Layer API Reference

A complete, offline-first reference to the **SAP Business One (HANA) Service
Layer** — every service, every operation, organized by business domain — paired
with a copy-paste playbook for actually pulling data through the companion
[`sapb1`](#companion-tool--sapb1-cli) CLI.

## What the Service Layer is

The Service Layer is SAP Business One's **OData REST API**, served over HTTPS at:

```
https://<host>:50000/b1s/v1/
```

Every business object is an OData **entity set** you read with a plain HTTP
`GET` and shape with the standard query options — `$select`, `$filter`,
`$orderby`, `$top`, `$skip`, `$inlinecount`. A session starts with
`POST /b1s/v1/Login` (CompanyDB + user + password), which returns a
`B1SESSION`/`ROUTEID` cookie carried on every later request; `POST /b1s/v1/Logout`
tears it down. Function-style `...Service` endpoints expose RPC-like actions on
top of the plain entity sets.

## The catalog at a glance

The full schema is captured in [`catalog/`](catalog/) and embedded in the CLI:

| Metric         | Count    |
|----------------|---------:|
| **Services**   | **498**  |
| **Operations** | **1950** |
| `GET`          | 600      |
| `POST`         | 840      |
| `PATCH`        | 279      |
| `DELETE`       | 230      |
| `PUT`          | 1        |

The **600 `GET` operations** are what this reference is built around — everything
you can **read**.

## Read-only focus

This reference and the `sapb1` CLI are deliberately **read-only**. Write
operations (`POST` / `PATCH` / `PUT` / `DELETE` against business data) are
catalogued **for reference only** and are **never executed**. The only writes the
tooling ever issues are `POST /Login` and `POST /Logout` to open and close a
session — every business-data command is a plain OData `GET`. The goal is safe,
auditable data extraction for analysis and AI pipelines, not data entry.

---

## ▶ START HERE — fetch data

**[`docs/00-READ-PLAYBOOK.md`](docs/00-READ-PLAYBOOK.md)** is the cheat-sheet you
open the moment you connect. It covers the **17 highest-value read (GET) entities**,
their **real** field names to `--select`, the common OData `$filter` patterns,
and copy-paste `sapb1 query` commands for the business questions people actually
ask ("which invoices are open?", "which items are low on stock?", "what do
customers owe us?"). **If you only read one file, read that one.**

---

## Domain reference

The 498 services are grouped into 19 business domains. Each doc lists the
services/entities in that domain, which are readable, and how to `GET` them.

| # | Doc | Domain — what's in it | Services |
|---|-----|-----------------------|---------:|
| 01 | [`docs/01-fixed-assets.md`](docs/01-fixed-assets.md) | **Fixed Assets** — asset master, capitalization, depreciation, retirement & transfers | 23 |
| 02 | [`docs/02-banking-payments.md`](docs/02-banking-payments.md) | **Banking & Payments** — incoming/outgoing payments, deposits, checks, bills of exchange, bank statements & house-bank accounts | 38 |
| 03 | [`docs/03-purchasing.md`](docs/03-purchasing.md) | **Purchasing (A/P)** — purchase orders, goods-receipt POs, A/P invoices, credit notes, returns & landed costs | 24 |
| 04 | [`docs/04-production-mrp.md`](docs/04-production-mrp.md) | **Production & MRP** — production orders plus manufacturing resources, capacities & groups | 9 |
| 05 | [`docs/05-inventory-warehouse-1.md`](docs/05-inventory-warehouse-1.md) | **Inventory & Warehouse (1)** — item master, item groups, bin locations, batches, inventory counts & goods entry/exit | 40 |
| 06 | [`docs/06-inventory-warehouse-2.md`](docs/06-inventory-warehouse-2.md) | **Inventory & Warehouse (2)** — stock transfers, price lists, special prices, serial numbers, units of measure & warehouses | 11 |
| 07 | [`docs/07-service-contracts.md`](docs/07-service-contracts.md) | **Service & Contracts** — service calls, service contracts, contract templates & service-call setup tables | 16 |
| 08 | [`docs/08-sales-ar.md`](docs/08-sales-ar.md) | **Sales (A/R)** — quotations, sales orders, deliveries, A/R invoices, credit notes, returns, drafts, opportunities & tax codes | 44 |
| 09 | [`docs/09-business-partners-crm.md`](docs/09-business-partners-crm.md) | **Business Partners & CRM** — customer/supplier master, contacts, activities, campaigns, territories & BP groups | 28 |
| 10 | [`docs/10-financials-accounting-1.md`](docs/10-financials-accounting-1.md) | **Financials & Accounting (1)** — chart of accounts, cost centers, dimensions, budgets, currencies & tax setup | 40 |
| 11 | [`docs/11-financials-accounting-2.md`](docs/11-financials-accounting-2.md) | **Financials & Accounting (2)** — journal entries, distribution rules, profit centers, financial years, withholding tax & VAT groups | 21 |
| 12 | [`docs/12-hr-resources.md`](docs/12-hr-resources.md) | **HR & Employees** — employee master info, positions, statuses, transfers & role setup | 11 |
| 13 | [`docs/13-projects.md`](docs/13-projects.md) | **Projects** — project master, project-management records & timesheets | 6 |
| 14 | [`docs/14-administration-setup-1.md`](docs/14-administration-setup-1.md) | **Administration & Setup (1)** — approvals, branches, departments, credit lines, discounts & core setup services | 40 |
| 15 | [`docs/15-administration-setup-2.md`](docs/15-administration-setup-2.md) | **Administration & Setup (2)** — reports, queries, series, users & Web Client configuration services | 40 |
| 16 | [`docs/16-administration-setup-3.md`](docs/16-administration-setup-3.md) | **Administration & Setup (3)** — approval templates, attachments, user-defined fields/tables/objects & user queries | 40 |
| 17 | [`docs/17-administration-setup-4.md`](docs/17-administration-setup-4.md) | **Administration & Setup (4)** — users, user tables & Web Client form/list-view/variant settings | 5 |
| 18 | [`docs/18-system-other-1.md`](docs/18-system-other-1.md) | **System & Other (1)** — Login/Logout, sessions, countries/states, holidays, KPIs, messages & localization indexers | 40 |
| 19 | [`docs/19-system-other-2.md`](docs/19-system-other-2.md) | **System & Other (2)** — product trees, relationships, teams, tracking notes, value mappings & Web Client dashboards | 22 |

The canonical domain → services map lives in
[`catalog/domains.json`](catalog/domains.json); the flat service list is in
[`catalog/services.txt`](catalog/services.txt) and the full operation index in
[`catalog/services.json`](catalog/services.json).

---

## Companion tool — `sapb1` CLI

This reference pairs with the read-only **`sapb1`** command-line client at
**`~/sapb1-cli`**. It ships the **entire Service Layer schema embedded offline**
(the same 498 services / 1950 operations), so you can explore what's available
with **zero network access** — before you're even on the VPN — and then read
live data once you connect.

**The power tool — read any entity set:**

```bash
sapb1 query <Entity> --select "<fields>" --filter "<odata>" --top <N>

# examples
sapb1 query Orders --select "DocNum,CardName,DocTotal" --filter "DocStatus eq 'O'" --top 50
sapb1 query Invoices --filter "DocTotal gt 10000" --all --json | jq '[.[].DocTotal] | add'
sapb1 query BusinessPartners --select "CardCode,CardName,CurrentAccountBalance" --json
```

`--json` / `--csv` make every result pipeable into `jq`, a spreadsheet, or an AI
agent. There are also typed shortcuts for the busiest entities —
`sapb1 orders list --open`, `sapb1 invoices list`, `sapb1 items list --low-stock 10`,
`sapb1 partners list --customers`.

**Offline discovery (no network, no VPN, no login):**

```bash
sapb1 entities                    # list all 498 services: ops count, methods, is-readable
sapb1 entities --search invoice   # find the entity-set name you want
sapb1 ops Orders                  # every operation catalogued for one service/entity
sapb1 catalog stats               # totals: 498 services / 1950 ops + per-method breakdown
```

`sapb1 entities`, `sapb1 ops`, and `sapb1 catalog stats` read the embedded
catalog and always work offline — use them to figure out *what* to query before
you connect. Run `sapb1 doctor` for an end-to-end ✓/✗ connection check
(config → reachable → login).

---

## Blockers — what still stands between you and live data

Everything above is built and works offline today. **Two things** must be
supplied before any live `GET` succeeds (see
[`ready/CONNECT-CHECKLIST.md`](ready/CONNECT-CHECKLIST.md) and
[`ready/admin-request.txt`](ready/admin-request.txt)):

1. **Network access — company VPN or IP whitelist.** The Service Layer host is
   firewalled to the corporate network (ports 50000/50001). You must be on the
   company **VPN**, or have your **public IP whitelisted** on the firewall,
   before any network command will connect. Off-network, every command fails
   fast with `cannot reach … are you on the VPN?` rather than hanging.

2. **The CompanyDB name.** Service Layer `Login` requires the exact **company
   database** name (e.g. `SBO_XXXX`) — ask your SAP admin. Set it as
   `SAPB1_COMPANYDB` in `~/sapb1-cli/.env` (or pass `--company`). Until it's set,
   any command that needs it fails with a clear "Company database not set"
   message.

Once both are in place: `cd ~/sapb1-cli && ./sapb1 doctor` → all ✓ → start with
the [READ Playbook](docs/00-READ-PLAYBOOK.md).
