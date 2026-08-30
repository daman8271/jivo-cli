---
title: Conversion cost — built from SAP, and it changes the ranking
date: 2026-08-30
company: JIVO_OIL_HANADB
engine: engine/conversion_cost.py
output: out/conversion-cost.csv
tags: [jivo/cost, jivo/allocation]
---

# Finding 13 — what it costs to fill a bottle, and why it matters

> [!warning] REWRITTEN 2026-08-30 after Daman's tip. The first version had three errors.
> 1. **Electricity.** It loaded the whole Rs 26.04 L plant bill into Oil. That bill is
>    shared with Beverages, and **water is the heavy user** — Beverages books
>    Rs 15,76,107/month of it in its own company, Oil Rs 11,74,510. Oil now takes only
>    its own. *(-Rs 14.3 L/month)*
> 2. **500 ml was Rs 123/litre. It is Rs 2.91.** Daman doubted it and was right — 42x
>    too high. The cause is below.
> 3. **Permanent salary is out.** Daman: *"For actual people, employees, we are not
>    considering that."* Factory labour is CASUAL labour (5100008), not the Rs 1.17 Cr
>    salary line. *(-Rs 58.6 L/month at the old 50% share)*
>
> The corrected engine: `engine/conversion_cost.py --salary-share 0 --prod <csv>`.

## The 500 ml error — why "active days" was the wrong denominator

The first version divided cost by **median litres on an active day**. For 500 ml that
read 549 L/day. But 549 litres is 1,098 bottles, and a filler does ~3,345 bottles an
hour — so that "day" was **twenty minutes of running**, not a line-day. Charging a
full day of factory cost to twenty minutes of output inflated the number 42x, and did
it worst on exactly the packs that run least.

**The fix: buy line-time in BOTTLES, not litres.** A 500 ml bottle occupies the filler
for the same tick as a 1 L bottle, so cost per bottle is flat within a line and cost
per litre simply scales with pack size:

| Pack | Btl/hr | Rs/bottle | Rs/litre |
|---|---:|---:|---:|
| 500 ml | 3,345 | 0.52 | **1.04** |
| 1 L | 3,345 | 0.52 | 0.52 |
| 2 L | 990 | 1.76 | 0.88 |
| 5 L | 1,500 | 1.16 | 0.23 |

Two checks the old version failed and this one passes: implied line-hours put the
fillers at **41% of the 12-hour pattern** (JIVO's own OEE screen says 46%), and
**1,911,201 L/month** filled, which matches actual sales.



Daman, 2026-08-30: *"yes do it, build your own then."* The Control Panel refuses
COGS (HTTP 403), so cost is built from SAP's ledger instead of waiting on a
permission.

```bash
python3 engine/conversion_cost.py
```

## The cost

| | ₹/month |
|---|---:|
| Casual labour | 1,040,783 |
| **Electricity (actual bill)** | **2,604,139** |
| Salary — 50% factory share *(assumption)* | 5,862,257 |
| Rent — 50% factory share *(assumption)* | 446,492 |
| Plant & machinery R&M | 365,230 |
| Consumables, job work, loading, inward freight | 228,369 |
| **Total conversion cost** | **10,547,270** |

At 6 lines × 26 days × 12 h: **₹67,611 per line-day, ₹5,634 per line-hour.**

> [!warning] The books understate factory power by ₹14.3 lakh a month
> The P&L carries ₹11.75 L across `5680011` + `5100020`. The real bill is
> ₹26,04,139 (Daman, confirmed). Per [ELECTRICITY.md](../reference/ELECTRICITY.md)
> it posts to `2110004 SUNDRY CREDITOR SERVICE` — a balance-sheet account that never
> touches an expense line. **Any cost model that trusts the P&L for electricity is
> wrong by more than half.**

## Allocate by LINE-TIME, not by litre

```
conversion ₹/litre = ₹ per line-day ÷ litres that pack yields in a line-day
```

Allocating per litre would assume a 200 ml bottle costs the same per litre as a 5 L
tin. It does not — and that difference is the entire point when line-hours are the
scarce thing.

| Pack | ₹/litre | ₹/bottle |
|---|---:|---:|
| 1 L | **2.36** | 2.36 |
| 5 L | 3.59 | 17.96 |
| 2 L | 10.03 | 20.06 |
| 15 L | 10.41 | 156.14 |
| 500 ml | **123.15** | 61.58 |
| 250 ml | 202.43 | 50.61 |

**A litre in 500 ml bottles costs 52x more to fill than a litre in 1 L bottles.**

## What it does to the ranking

Applied to `out/allocation-ALL-2026-08-29.csv` (99 SKUs):

**The top is unchanged.** Extra Virgin Olive 10 ml, 500 ml and 1 L hold ranks 1-3;
nothing in the top 12 moves more than one place. The premium olive range earns its
place on profit, not just revenue — that is worth knowing.

**The bottom collapses. 36 of 99 SKUs lose money once line-time is charged.**

| SKU | Old ₹/L | Conv ₹/btl | New ₹/L | Rank |
|---|---:|---:|---:|---|
| JIVO RICE 1 KGS 4 PCS | 95.10 | 464.36 | **-369.26** | #31 → #99 |
| SOYABEAN OIL 15 KGS TIN IMP | -51.12 | 149.60 | -200.72 | — |
| COLD PRESS GROUNDNUT 500 MLS | 19.78 | 61.58 | -107.19 | #56 → #96 |
| COLD PRESS 500 MLS 24 PCS | 28.16 | 61.58 | -100.14 | #50 → #95 |
| MUSTARD KACHI GHANI 200 ML | -9.72 | 13.51 | -77.24 | — |

Small packs are the destroyers. On revenue-minus-material they looked mid-table; on
profit they are burning line-hours that the olive range needs.

> [!important] Two things here are NOT solid — read before acting
> **1. The 50% factory shares on salary and rent are my assumption, not a ruling.**
> Salary alone is ₹5.86 L/month of the basket. A 30% or 70% share moves every number
> on this page. Somebody has to rule the real split.
>
> **2. Rare packs are overstated.** The allocation divides by *median litres per
> active day*, and a "day" on which only 160 L of a pack ran was a short changeover,
> not a full line-day. So ₹464/bottle on rice, and every figure for a pack with few
> active days, is too high. The DIRECTION (small and rare packs are expensive) is
> right; the MAGNITUDE for rare packs is not. **Fix: read actual line-hours per
> production order from `OWOR`/`WOR1` instead of counting active days.** That is the
> next job on this engine.

## What is now unblocked

`allocate.py` can rank on `(price − material − conversion) ÷ oil litres` — profit,
not contribution. That was Daman's instruction from the start: *"properly optimise
this for profit."* It is now computable without the Control Panel permission.
