---
title: Customer Aging
route: /realise/customer-aging/
type: page
endpoints: [customer-aging-oil-ar, customer-aging-mart, customer-aging-beverages, aging-remark, export-aging-detail, export-xlsx]
tags: [jivo, control-panel, accounts]
---
# Customer Aging

## Purpose
Accounts-receivable (A/R) aging report for the JIVO ops / collections team. Shows how much each customer owes, split into **aging buckets** (0-30, 31-60, 61-90, 91-120, 121+ days overdue), so the team can chase the oldest / largest outstanding balances. Balances are computed live from **SAP Business One** reconciliation aging and tie to customer ledger balances. A single **As of** date re-ages the whole book to any point in time.

## What it shows
- **Company toggle** (top-left segmented control, `#agCo`): **Oil** · **Beverages** · **Mart** — each is a separate legal entity / A/R book with its own data source.
- **KPI cards** (`#agKpis`): Total Outstanding, Current (0-30 & its %), Overdue >90 days (& %), Top customer (name / value / %). Sourced from each dataset's `kpis` block (Mart/Bev) or computed client-side (Oil).
- **As of** date picker (`#agAsOf`, default today, max = today) → sent as `?as_of=YYYY-MM-DD` to the aging APIs.
- **Aging table** grouped by **Format** (channel/segment grouping) → expandable to individual customers, with bucket columns tinted green→red by age. A sticky grand-total row.
- **Filters**: search (customer/format), **Format** multi-select, **Remarks** multi-select, **Days** multi-select (invoice age; Oil RAW view only), **Balance-Due sign** segmented (Both/Positive/Negative — negatives are advances/credits), **B2B/B2C** segmented (Mart only; B2B = has GSTIN, B2C = none), and a **Conditions** popup (Balance Due ≥ / ≤ / between).
- **RAW DATA workspace** (Oil & Beverages): an Excel-like per-open-invoice table + custom **Pivot** builder + inline **remark** editing and Excel **upload** of remarks/special-prices. Fed by [[customer-aging-oil-ar]] / [[customer-aging-beverages]].
- **Exports**: **Export Excel** (current pivot → [[export-xlsx]]), **Export Detail** (every open document + remarks for filtered parties → [[export-aging-detail]]).
- Inline **remark** editing per open invoice (autosaves via [[aging-remark]]).

## Data sources
- [[customer-aging-oil-ar]] — GET; flat per-open-invoice A/R list for the **Oil** company (feeds the Oil RAW DATA workspace; each row carries `days` / `tdd` the client buckets).
- [[customer-aging-mart]] — GET; pre-bucketed pivot (groups→customers with `b0_30…b121`) for the **Mart** entity, incl. `kpis`, `total`, `buckets`.
- [[customer-aging-beverages]] — GET; pre-bucketed pivot for the **Beverages** entity (feeds both main view and Beverages RAW DATA workspace).
- Oil's default bucketed pivot is server-embedded in a `<script id="aging-data">` block on page load; the API above supplies the raw invoice detail.
- [[aging-remark]] — POST family (WRITE): save per-invoice remark; bulk upload / clear remarks per company.
- [[export-aging-detail]] — POST (EXPORT): full open-document + remark workbook for the filtered parties.
- [[export-xlsx]] — POST (EXPORT): generic client-built-rows → .xlsx (shared helper).

## Key fields & columns
- **Format** — the grouping band (e.g. `E-COMMERCE`, `MODERN TRADE`, ASM/salesperson name for Beverages). One "format" row aggregates its customers.
- **Original** (`original`) — original document / invoice value before payments.
- **Balance Due** (`balance_due`) — net open balance still owed as of the aging date (negative = customer is in credit / has an advance).
- **Aging buckets** `b0_30 / b31_60 / b61_90 / b91_120 / b121` — the balance split by how overdue it is in days. See [[AR-aging]] buckets: 0-30 = current, 121+ = seriously overdue. Sum of buckets = Balance Due.
- **Oil A/R invoice fields** (`customer-aging-oil-ar` rows): `doc` (SAP doc no), `date` (invoice date), `days` (age in days), `ltd` (last transaction/due date), `tdd` (days to/from due), `status` `O` = Open, `total` / `bal` (invoice & balance), `outstanding`, `sp` / `actual_sp` (sales person / buyer), plus dispatch fields (`bilty`, `transporter`, `vehicle`, `driver`, `mobile`) and `remark`.
- **B2B / B2C** (Mart) — `segment`; B2B = customer has a `gstin` on file, B2C = none.
- **KPIs**: `current_pct` = share of book in 0-30; `overdue_90` / `overdue_90_pct` = balance aged >90 days; `top_customer_*` = single largest exposure.

## Notes / gotchas
- Three separate companies (Oil / Beverages / Mart) — never mix their totals; each has its own endpoint and its own book.
- Oil returns **flat invoices** (client buckets them by `days`); Mart & Beverages return **pre-bucketed** groups from the server.
- Negative bucket / balance values are legitimate (customer advances, credit notes) — the Balance-Due sign filter exists to isolate them.
- Remarks/special-prices are a **local overlay** stored by the Control Panel (via [[aging-remark]]); "Clear" wipes them for the whole company book but never touches SAP.
- `export-aging-detail/`, the `aging-remark*` writes/uploads, and `export-xlsx/` are WRITE/EXPORT — documented from page JS only, never executed.

## Related
[[required-credit-limit]], [[open-payments]], [[claims]], [[customer-master]], [[REALISE]], [[AR-aging]], [[GT]], [[MT]], [[ECOM]]
