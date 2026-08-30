---
title: The September projection — computed, not hand-made
date: 2026-08-29
company: JIVO_OIL_HANADB
engine: engine/forecast.py
output: out/forecast-sep.csv
tags: [jivo/planning, jivo/forecast]
---

# Finding 12 — computing the projection for September 2026

Built to Daman's spec in [PLANNING-MODEL.md](../reference/PLANNING-MODEL.md) §1:
the month should open with a projection computed **here**, from last month's
demand, SAP history, and a seasonal uplift *measured* from the same period last
year — "never a guess".

`engine/forecast.py`. Read-only, one command:

```bash
python3 engine/forecast.py --target 2026-09
```

## The answer

| | Litres | Sale-T |
|---|---:|---:|
| Method A — momentum | 2,276,784 | 2,276.8 |
| Method B — level | 1,990,320 | 1,990.3 |
| **Projection (midpoint)** | **2,133,552** | **2,133.6** |
| Human plan (EXIM, uploaded 27 Aug) | 4,323,300 | 4,323.3 |

**September 2026 will be about 2.1 million litres. The plan asks for 4.3 million —
2.03x more.**

## Why two methods, and why a range

There is **one September in SAP** (Oil's history starts 2024-10), so the seasonal
multiplier rests on a single observation. The method chosen moves the answer by
13%, and quoting either number alone would be false precision.

- **A · momentum** — base = trailing 3 months; season = Sep-2025 ÷ its own
  trailing-3. Follows where the business is actually heading. Vulnerable to a
  spiky window: July 2025 ran at 1.44x, which inflates Sep-2025's baseline and
  makes September look weaker than it is (0.886).
- **B · level** — base = 2026's own monthly mean so far; season = Sep-2025 ÷ the
  whole 2025 mean. Immune to a spiky window, blind to momentum. Gives 0.966.

The truth sits between. The spread narrows with every month that passes.

## September is not an up month

This is the finding that matters, because it is the opposite of the assumption:

| | Sep index |
|---|---:|
| vs its own trailing 3 months | **0.886** |
| vs the full 2025 mean | **0.966** |

**September carries no festival uplift.** The calendar-month shape from 20 measured
multipliers puts the year's peaks in **July (1.354)**, **May (1.200)** and
**August (1.147)**, with the trough in **November (0.652)**. Diwali-season buying
lands in the month or two before the festival, and in 2026 that is October and
November — not September. Planning September as a festival month over-builds it.

> [!note] One September, stated plainly
> Sep, Oct, Nov and Dec each have **n=1**. Jan-Aug have n=2. Every conclusion above
> about autumn is a single observation and should be re-checked once
> September 2026 closes.

## Per-group seasonality (credibility-weighted)

A group's raw multiplier is shrunk toward the all-item multiplier by
`w = V/(V+50,000 L)` on its baseline volume — one September must not let a
2,000-litre category claim a 4.5x swing.

| Group | Base L/mth | Raw | Used | Credibility |
|---|---:|---:|---:|---:|
| MUSTARD | 577,609 | 0.723 | **0.734** | 0.94 |
| OLIVE | 437,880 | 1.154 | **1.112** | 0.84 |
| CANOLA | 323,359 | 1.033 | **1.016** | 0.88 |
| GROUNDNUT | 313,143 | 1.955 | **1.338** | 0.42 |
| SOYABEAN | 282,156 | 0.689 | **0.705** | 0.92 |
| SUNFLOWER | 276,281 | 1.335 | **1.199** | 0.70 |
| COCONUT | 63 | 4.505 | **0.961** | 0.02 |

Coconut is the guard working: a 4.5x raw swing on 63 litres is noise, and
credibility shrinks it to the market's own shape.

## The projection independently confirms the 2x problem

Finding 05 measured the factory at a median **75,404 L/day** against a plan needing
159,862 L/day — **47%**. This projection, built from a completely different route
(sales history, not production history), lands at **49% of the plan**. Two
independent methods, the same answer: **the plan is twice the business.**

And 2.13 M L/month is ~71,000 L/day — almost exactly the factory's observed median.
**The projection is achievable. The plan is not.**

## Where the plan and history disagree

### Over-planned (top 6 by litres)

| Code | SKU | Plan L | Forecast L | Over |
|---|---|---:|---:|---:|
| FG0000030 | MUSTARD KACHI GHANI 1 LTR 20 PCS | 690,000 | 138,983 | **551,017** |
| FG0000081 | COLD PRESS SUNFLOWER 1 LTR 20 PCS | 310,000 | 121,639 | 188,361 |
| FG0000250 | SOYABEAN OIL 15 KGS | 200,000 | 18,518 | 181,482 |
| FG0000011 | MUSTARD KACCHI GHANI 5 LTR 4 PCS | 230,000 | 77,216 | 152,784 |
| FG0000142 | COLD PRESS GROUNDNUT OIL 1 LTR 16 PCS | 385,000 | 234,327 | 150,673 |
| FG0000194 | SOYABEAN OIL 1 LTR POUCH 12 PCS | 150,000 | 17,794 | 132,206 |

One SKU — Mustard Kachi Ghani 1 L — carries **551,017 L** of the 2.19 M L gap, a
quarter of it. It is planned at 5x its own selling rate.

### In the plan, never sold

**12 SKUs, 52,000 L.** No invoice line in 23 months. Small, but they consume
packaging and line time that the binding SKUs need.

### Selling, but missing from the plan

**61 SKUs, 316,626 L of forecast demand with no plan row.** Dominated by soyabean
pouches and tins (`FG0000359` 50,861 L, `FG0000316` 40,160 L, `FG0000299`
37,138 L). Worth checking before treating as an omission — these may be job-worked
or planned under another code — but if they are real, the plan is short on them
while being long by 2.19 M L elsewhere.

## CORRECTION 2026-08-30 — "September is not an up month" was only half true

Daman pushed back on the claim that there is nothing happening on the platforms in
September. He was right to. Two separate errors:

**1. I conflated "no event data" with "no events."** What I actually established is
that no event/promotion/calendar endpoint exists in ecom — that says nothing about
whether events occur. Retracted as written.

**2. The Oil-only lens hid a channel split.** Running the same engine both ways:

| | Sep-2026 projection | Sep index (2025) |
|---|---:|---:|
| Direct trade (Oil external) | 767,408 L | **0.841** — down |
| E-com channel (Oil→Mart) | ~1,366,000 L | — |
| **Mart's own outward sales** | — | **1.222** — up, its best month of 2025 |
| Factory total | 2,133,552 L | 0.886 / 0.966 |

**September is an UP month for e-com and a DOWN month for direct trade.** They
roughly cancel, which is why the factory total looks flat and why the Oil-only
headline read as "no uplift". The MIX shifts even when the total does not — and the
September plan is 56% ecom (2,433,000 of 4,323,300 L), which is directionally right.

**What I could NOT confirm: an actual platform sale event.** Mart's invoice count on
2025-09-30 hit 585 against 6-34 on a normal early-September day, which looks like a
Big Billion Days / Great Indian Festival signature. It is not. Month-end
concentration is normal for Mart — the last 3 days carry 60% of September's lines,
but 73% of Feb-2025's and 81% of Feb-2026's. The spike is the billing cycle, not an
event. **No claim about platform events is supported by this data either way.**

## CORRECTION 2 — 2026-08-30 — the festival MOVED, and the forecast had imported it

Daman told me to stop saying the data does not know and go look it up. Correct call;
the dates are public. Written up in [EVENT-CALENDAR.md](../reference/EVENT-CALENDAR.md).

**September 2025 contained Navratri (22 Sep - 1 Oct), Flipkart Big Billion Days
(23 Sep - 2 Oct) and Amazon Great Indian Festival (23 Sep).** Measured in SAP: those
nine days ran at **2.06x** the rest of the month and carried **485,343 L, 24% of the
entire month**.

**September 2026 contains none of it.** Navratri is 11-19 Oct, Dussehra 20 Oct,
Diwali 8 Nov — everything has shifted ~19 days later. A multiplier measured from
Sept-2025 imports a festival that will not happen.

`engine/forecast.py` now takes `--event-days` and measures the season on event-free
days only:

| | Sep-2026 projection | Midpoint |
|---|---:|---:|
| Event included (original, wrong for 2026) | 1,990,320 - 2,276,784 L | 2,133,552 |
| **Event stripped** | **1,682,117 - 1,892,024 L** | **1,787,070** |

**-346,482 L, about 16%.** This supersedes the headline figure above.

The open variable is where BBD/GIF 2026 lands — not yet announced. Late September
keeps the event in the month; early-mid October (the better prior, since both sales
have opened ~4 weeks before Diwali for three years) takes it out. **The two
scenarios are 346,000 L apart, about 4.5 days of factory output.**

## What is still missing from the spec

**No JIVO system holds event dates** — not SAP, not ecom's 31 dashboards, not EXIM.
That gap is now filled by hand in [EVENT-CALENDAR.md](../reference/EVENT-CALENDAR.md),
which the forecast reads via `--event-days`. It must be maintained: add each date as
it is announced, and re-measure each event's impact as it closes.

**Still outstanding: the 2026 BBD / Great Indian Festival dates.** Both platforms
confirm 2-3 weeks ahead. Getting them is worth 346,000 L of September accuracy.

## Method notes

- Litres throughout ([C-0050](../../harness/corrections/C-0050-a-tonne-means-litres-on-the-sale-side-ki.md)); `INV1`/`RIN1` quantities are PIECES ([C-0001](../../harness/corrections/)) converted by the settled name parser in `plan_units.py`.
- Grouped on SAP's `U_Sub_Group` ([C-0003](../../harness/corrections/)), never the item name.
- Credit notes subtracted; `CANCELED='N'` only.
- **Intercompany INCLUDED** ([C-0005](../../harness/corrections/)) and reported separately — Oil→Mart is oil the factory still has to make. `--external-only` flips it.
- The current month is scaled `days_in_month / days_elapsed` before use as base. August ran 30 of 31 days, scaled x1.033. Without this the model would forecast a 6% collapse that is purely a calendar artefact.
