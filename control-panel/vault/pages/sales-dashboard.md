---
title: Sales Channel Dashboard (Realise)
aliases: [sales]
route: /realise/
type: page
endpoints: [sales-data, targets, flex-targets, segment-targets, target-nodes, channel-targets, oih-breakdown, order-in-hand, order-in-hand-rows, commodity-oih-rows, drill-down, historical-realise, beverages-data, beverages-docs, channel-detail-docs, save-targets, save-closing-remark, export-xlsx, export-excel]
tags: [jivo, control-panel, sales-dashboard]
---
# Sales Channel Dashboard (Realise)

The biggest screen in the Control Panel (internal proc name `REPORT_SALES_ANALYSIS`, "v11"). Server-rendered Django shell at `/realise/` that loads ~25 AJAX fetches against the shared [[sales-data|/realise/api/…]] JSON API. The client sets `API = '/realise'` and every call is `${API}/api/<endpoint>/`.

## Purpose
Single cockpit for JIVO sales leadership to track **realisation** (₹ earned per litre sold) against **targets**, by product, by sales channel, and by salesperson — for both the [[OILS]] and [[BEVERAGES]] segments. Answers: are we hitting target litres and target ₹/L this month? How much is still sitting as [[OIH]] (open sales orders not yet invoiced)? Which channel / person / customer is lagging?

## What it shows
The page is a **two-slide deck** (arrow nav, `slideOne` / `slideTwo`) with a global **OILS ⇄ BEVERAGES** dataset toggle (`switchDataset()`) in the header and a `LIVE` pill.

**Slide 1 — Realise Dashboard (product grid):**
- Summary cards: Target Wtd Realise, Net Realise, Target Litres, Actual Litres, Target vs Actual, Line Total ₹, Products.
- Main table by product (`u_type` × `u_sub_group`): Tgt Ltrs, Tgt Rate, Avg Realise, Act Ltrs, Act Realise, Variance, Recovery, Rate Impact — each product row drills down (▸) by a chosen dimension.
- Filters: **Month / Year** (`fMonth`,`fYear`), **date range** From/To (`dFrom`,`dTo`), **Drill By** (`fDrill` → `State` / `U_Main_Group` (Main Group) / `U_Chain` (Chain) / `ItemName` (Item Name) / `CardName` (Customer)).
- **Historical avg realise** overlay (`fAvgPeriod`: 12 Months / 6 Months / Quarterly / Last Month) via [[historical-realise]].
- **Update Targets** button → admin re-auth ([[save-targets|verify-pin]]) → editable target table saved by [[save-targets]] (WRITE).

**Slide 2 — Sales Channel view (`sc2-*`):** channel cards for **[[GT]] / [[MT]] / [[ROI]] / [[ECOM]] / HORECA / CSD / REST**, each showing Target Ltr, Done Ltr, OIH Ltr, Bal Ltr, Bal Rlz, Realise. A faint Wellness/Mart map backdrop. Its own date range (`sc2From`,`sc2To`). Clicking a card/cell opens a doc-detail modal ([[channel-detail-docs]]) listing the underlying invoices ("Done") or open sales orders ("OIH") with per-warehouse stock `[GP-FG, BH-EC, BH-PF]`.

**Beverages mode** swaps the grid for a beverages view: today-vs-yesterday boxes, customer grading, month totals, OIH — from [[beverages-data]], with an invoice/SO drill via [[beverages-docs]].

## Data sources
- [[sales-data]] — POST core: product realise rows + `channel_rows` / `channel_month_rows` for the OILS grid and channel cards.
- [[beverages-data]] — POST core for the BEVERAGES dataset (variety/box/OIH rollups + today/yesterday).
- [[targets]] — GET default+saved product targets (tgt_ltrs / tgt_rate) for a month.
- [[flex-targets]] — GET per-salesperson flat litre targets (keyed `¦person=NAME`).
- [[segment-targets]] — GET saved targets scoped to a segment (OILS/BEVERAGES/PREMIUM…).
- [[channel-targets]] — GET target litres per channel (GT/MT/ROI/ECOM/HORECA/CSD/REST).
- [[target-nodes]] — GET granular target rows (main_group × state × person × segment).
- [[order-in-hand]] — GET OIH ₹ totals per salesperson.
- [[oih-breakdown]] — GET line-level OIH: item × customer × SO, premium/commodity split.
- [[order-in-hand-rows]] — GET OIH open-qty rows (channel view, date-scoped).
- [[commodity-oih-rows]] — GET OIH open-qty rows for commodity oils.
- [[channel-detail-docs]] — GET invoices ("done") or open SOs ("oih") behind a channel card.
- [[beverages-docs]] — GET invoice/SO list behind a beverages node.
- [[drill-down]] — POST expand one product row by a dimension.
- [[historical-realise]] — POST trailing-period average realise overlay.
- [[save-targets]] — POST **WRITE** (edit targets; admin re-auth via verify-pin).
- [[save-closing-remark]] — POST **WRITE** (period closing note).
- [[export-xlsx]] / [[export-excel]] — POST **EXPORT** (xlsx/csv downloads).

## Key fields & columns
- **REALISE / Realise / Avg Realise** — ₹ per litre = linetotal ÷ litres. See [[REALISE]].
- **Tgt Ltrs / Tgt Rate** — target litres and target ₹/L for the month (from [[targets]]).
- **Act Ltrs / Act Realise** — actual litres sold and actual ₹/L for the range.
- **[[TGT]] / [[DONE]] / DONE L** — target vs invoiced-done litres on the channel cards.
- **[[OIH]] / OIH Ltr / OIH RLZ** — Order In Hand: open sales orders not yet invoiced (litres and its realise).
- **[[BAL]] / Bal Ltr / Bal Rlz / BAL W/O OIH** — balance to target; realise on that balance; balance excluding OIH.
- **Variance / Recovery / Rate Impact** — target-vs-actual gap analytics on Slide 1.
- **u_type** — segment/tier: `COMMODITY` vs `PREMIUM` (within oils). **u_sub_group** — oil variety (MUSTARD, OLIVE, CANOLA, SOYABEAN…). **u_main_group / main_group** — channel (GT/MT/ECOM/E-COMMERCE…). **u_chain** — DISTRIBUTOR / chain type. See [[Main Group]] drill.
- **linetotal / line_total** — ₹ net line value. **litres / liter** — quantity in litres. **open_qty** — open (uninvoiced) litres on an SO.
- Warehouse stock triple `[GP-FG, BH-EC, BH-PF]` on doc rows = per-plant available stock for the item.

## Notes / gotchas
- GET reads require header `X-Requested-With: XMLHttpRequest`; POST reads require JSON body + `X-CSRFToken`.
- `sales-data`/`beverages-data`/`drill-down`/`historical-realise` are POST *reads* — sample the smallest date range.
- **`segment-targets/?segment=OILS`** returned `{}` (no OILS overrides saved for Jul 2026) — it holds only explicitly-saved segment targets, empty is normal.
- **`drill_by` values are case-sensitive** and Pascal/Title-cased: `State`, `U_Main_Group`, `U_Chain`, `ItemName`, `CardName`. Sending `state` yields `dimension:"UNKNOWN"`.
- `channel-detail-docs` needs a channel/metric that actually has rows — GT/OILS on a single day was empty; `metric=oih` (open orders, not date-bound) returns rows readily.
- **Update Targets** is gated by an admin re-auth modal hitting [[save-targets|/api/verify-pin/]] before opening the editable table — never call save-targets.

## Related
[[control-panel]] (Control Panel — same shared API), [[REALISE]], [[OIH]], [[BAL]], [[TGT]], [[DONE]], [[GT]], [[MT]], [[ROI]], [[ECOM]], [[OILS]], [[BEVERAGES]], [[Main Group]], [[COGS]], [[DRR]]
