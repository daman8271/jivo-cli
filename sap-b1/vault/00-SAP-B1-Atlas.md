# SAP B1 Atlas — Master Map of Content

> [!danger] READ-ONLY STANDING RULE
> **We NEVER write to SAP.** This is a live production ERP. The only sanctioned access path is the read-only `sapb1` CLI (`cd ~/sap-b1/cli && ./sapb1 ...`), which issues GET requests exclusively — the sole exceptions are [[Login]]/[[Logout]], which touch nothing but a session cookie. No curl against the server, no POST/PATCH/PUT/DELETE, ever. The write-side RPC services documented in this vault exist for completeness only; they are never called.

## Connection

- **Server**: SAP Business One Service Layer (`b1s/v1`) on SAP HANA, port 50000 (HTTPS). Reachable only from the company VPN or a whitelisted IP.
- **Client**: `cd /Users/damanpreetsingh/sap-b1/cli && ./sapb1 ...` — the CLI reads credentials from `.env` in the **current directory** (gitignored), so always `cd` there first. `./sapb1 doctor` runs an end-to-end config/network/login diagnostic.
- **Three branch company databases**, switched per-call with `--company`:

| CompanyDB | Business | Role |
|---|---|---|
| `JIVO_OIL_HANADB` | Edible oils | **Default** (set in `.env`) — all `rows_oil` counts in this vault come from here |
| `JIVO_MART_HANADB` | Mart / distribution | `--company JIVO_MART_HANADB` |
| `JIVO_BEVERAGES_HANADB` | Beverages | `--company JIVO_BEVERAGES_HANADB` |

```bash
cd /Users/damanpreetsingh/sap-b1/cli
./sapb1 doctor                                        # connectivity check
./sapb1 query Orders --count                          # oil DB (default)
./sapb1 query Orders --count --company JIVO_MART_HANADB
```

## Stats

- **498** catalogued services — every one has a note in `services/` and appears in exactly one domain hub below.
- **307** readable (entity sets answering GET); the other 191 are write/RPC-side, documented but never called.
- **140** entities hold live data in `JIVO_OIL_HANADB` (`rows_oil > 0`) — see [[03-Live-Data-Census]] for the full table and a three-DB comparison.

## Start here

- [[01-Data-Model]] — how SAP B1's tables fit together: master data, document flows, join keys.
- [[02-Query-Cookbook]] — real business questions mapped to exact `sapb1` commands.
- [[03-Live-Data-Census]] — which entities actually contain data at JIVO, with live cross-DB counts.

## Domain hubs

| Domain | Services | Readable | Covers |
|---|---:|---:|---|
| [[sales-ar]] | 44 | 27 | Quotations → orders → deliveries → invoices; returns, credit notes, dunning, opportunities |
| [[banking-payments]] | 38 | 24 | Incoming/vendor payments, deposits, checks, BoE, house banks, payment terms |
| [[purchasing]] | 24 | 13 | Purchase requests → orders → GRPO → A/P invoices; landed costs, returns |
| [[inventory-warehouse-1]] | 40 | 21 | Item master, bins, batches, goods entry/exit, counting, pick lists |
| [[inventory-warehouse-2]] | 11 | 11 | Warehouses, price lists, stock takings/transfers, serials, UoM |
| [[business-partners-crm]] | 28 | 20 | BP master, contacts, activities, campaigns, territories |
| [[financials-accounting-1]] | 40 | 19 | Chart of accounts, cost accounting, budgets, currencies, TDS masters |
| [[financials-accounting-2]] | 21 | 21 | Journal entries, VAT/tax determination, withholding, account rules |
| [[production-mrp]] | 9 | 5 | Production orders, resources and capacities |
| [[fixed-assets]] | 23 | 20 | Asset master, depreciation setup, capitalization/transfer/retirement |
| [[service-contracts]] | 16 | 10 | Service calls, contracts, knowledge base (unused at JIVO) |
| [[hr-resources]] | 11 | 6 | Employee master and HR setup tables |
| [[projects]] | 6 | 3 | Financial project codes + project-management module |
| [[administration-setup-1]] | 40 | 3 | RPC config services: company, approvals, branches, reconciliation |
| [[administration-setup-2]] | 40 | 0 | RPC config services: users, series, layouts, Web Client personalization |
| [[administration-setup-3]] | 40 | 40 | Readable setup: approvals, UDFs, attachments, form preferences, queries |
| [[administration-setup-4]] | 5 | 5 | Users, user tables, Web Client settings tail |
| [[system-other-1]] | 40 | 37 | Login/session, messages, HSN codes, departments, localization tables |
| [[system-other-2]] | 22 | 22 | Product trees (BOMs), relationships, states, Web Client runtime |
| **Total** | **498** | **307** | |
