---
title: Required Credit Limit
route: /realise/required-credit-limit/
type: page
endpoints: [save-closing-remark, credit-lock-unlock]
tags: [jivo, control-panel, accounts]
---
# Required Credit Limit

## Purpose
Tells the credit-control / sales team **how much credit limit each customer needs** to cover both their current ledger dues **and** their open orders (Order-in-Hand), so a customer's limit in SAP can be set high enough to let pending sales orders release without a credit block. Combines live A/R exposure with OIH to produce a **Required Limit** per party. Managers can **freeze (lock)** the headline numbers for a set number of days.

## What it shows
- **KPI cards** (`#rcKpis`) — book-level roll-up from the embedded `total` block (total OIH litres/revenue, ledger, total outstanding, required limit).
- **Table** grouped by **ASM** (Area Sales Manager) → party rows. Columns:
  - **ASM / Party**, **Type** (P / C / P+C), **Main Group** (channel), **State**, **Delivery Remark**.
  - **OIH Litres** — open-order volume, split premium/commodity/canola/olive.
  - **SO No** — open sales-order numbers (click → modal listing each SO + value).
  - **OIH Revenue ₹** — open-order value.
  - **Ledger Amt ₹** — customer balance just before the selected As-of date.
  - **Total Outstanding ₹** = Ledger Amt + OIH Revenue.
  - **Required Limit ₹** = Total Outstanding × 1.02 (a ~2% buffer).
  - **Payment Done ₹** — bank-transfer receipts (SAP `ORCT`) dated on the As-of date.
  - **Outstanding ₹** = Total Outstanding − Payment Done.
- **Filters**: **Type** segmented (All / P / C / P+C, multi-select), **ASM** multi-select, search (party/ASM/state), **As of** date.
- **Lock control** (`#rcLock`) — freeze *Total Outstanding* & *Required Limit* at current values for N days (default 30); shown as a status pill with "days left" + **Unlock** when active. Ledger Amt, Payment Done & Outstanding always follow the live As-of date even while locked.
- Per-row inline **remark** (Delivery Remark) autosaves via `save-closing-remark/`.

## Data sources
- **Server-embedded JSON** — the entire table is rendered from a `<script id="credit-data">` block (keys: `asms[]`, `total`, `lock`, `as_of`); this page does **not** call a READ API for its rows.
- [[credit-lock-unlock]] — POST (WRITE): freeze / unfreeze the headline columns.
- `save-closing-remark/` — POST (WRITE): persist the per-party Delivery Remark. (Documented only; shared with other Realise pages.)

## Key fields & columns
- **Type** — `P` = Premium, `C` = Commodity, `P+C` = both (derived from the OIH litres mix: `litres.premium` vs `litres.commodity`).
- **litres** `{premium, commodity, canola, olive, total}` — open-order volume by product family.
- **value** block per row: `total` (OIH revenue), `pi_total` (proforma-invoice value), `ledger`, `outstanding` (= ledger + OIH revenue), `required_limit` (= outstanding × 1.02), `payment_done`, `remaining` (= Outstanding column).
- **no_open_order** — true when the party has only ledger dues and no pending SOs (OIH = 0).
- **so_list** `[{no, value}]` — each open sales order and its value (surfaced in the SO modal).
- **lock** — null when free; when active carries `active`, `days_left`, `lock_until`.

## Notes / gotchas
- Required Limit is a **management target** (Total Outstanding + 2%), not a value read back from SAP.
- Locking freezes only two columns (Total Outstanding, Required Limit); everything else stays live to the As-of date — by design, so a frozen limit doesn't hide fresh receipts.
- All mutating actions here — `credit-lock/`, `credit-unlock/`, `save-closing-remark/` — are WRITE, documented from page JS only, never called. See [[credit-lock-unlock]].
- OIH litres/revenue tie back to the [[OIH]] concept used across the [[REALISE]] pages.

## Related
[[customer-aging]], [[open-payments]], [[claims]], [[REALISE]], [[OIH]], [[credit-lock-unlock]]
