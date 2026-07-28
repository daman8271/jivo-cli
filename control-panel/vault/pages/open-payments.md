---
title: Open Payments
route: /realise/open-payments/
type: page
endpoints: [open-payments, export-xlsx]
tags: [jivo, control-panel, accounts]
---
# Open Payments

## Purpose
Lists customer **payments on account** — receipts received but **not yet applied** to specific invoices (unallocated / "on-account" money) — within a chosen date range. Lets the accounts team see how much unapplied cash is sitting against each customer / channel / territory so it can be reconciled against open invoices.

## What it shows
- **Date range** pickers (`#opStart` / `#opEnd`) + **Fetch** button → POST to [[open-payments]] with `{start_date, end_date}`.
- **KPI cards**: **Open Balance** (Σ unapplied on-account ₹) and **Payment on Account** (Σ receipt amount ₹).
- **Table** — per-payment (flat) by default, or **grouped/pivoted** by any combination of dimensions chosen in the **Drill** picker.
- **Drill dimensions** (`DIMS`): Customer, Contact Person (assigned territory owner), State, Main Group (channel), Date.
- **Filters**: search (customer / code / doc), **State** dropdown, **Main Group** dropdown, **Contact Person** dropdown, and a flat/grouped **mode** toggle.
- Sortable columns; **Export Excel** of the current view (flat or pivot) via [[export-xlsx]].

## Data sources
- [[open-payments]] — POST(JSON) `{start_date, end_date}`; returns `rows[]` of unapplied receipts + `count`, `start`, `end`.
- [[export-xlsx]] — POST (EXPORT): client-built rows → .xlsx download.

## Key fields & columns
- **Date** (`date`) — payment / receipt date.
- **Doc No** (`doc_no`) — SAP receipt document number.
- **Customer** (`code` / `name`) — SAP CardCode + CardName.
- **Main Group** (`main_group`) — sales channel (e.g. `GT`, `MT`, `ROI`, `ECOM`).
- **State** (`state`) — party state.
- **Contact Person** — derived client-side (`personOf`) from Main Group + State (assigned territory owner), not a raw field.
- **Payment on Account** (`amount`) — the receipt amount.
- **Open Balance** (`open_bal`) — the still-unapplied portion of that receipt.

## Notes / gotchas
- Body is `{start_date, end_date}` (both required — page won't fetch without both); sampled with a single day to capture schema.
- "Contact Person" is computed in the browser from a Main-Group × State → owner map, so it exists as a filter/drill dimension but not in the API payload.
- `export-xlsx/` is EXPORT — documented from JS only, not executed.

## Related
[[customer-aging]], [[required-credit-limit]], [[claims]], [[REALISE]], [[GT]], [[MT]], [[ROI]], [[ECOM]]
