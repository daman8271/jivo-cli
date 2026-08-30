# ji.jivo.in — the factory app already answers feasibility

> [!info] This is the **factory app**, not a new system
> `ji.jivo.in` is the web UI of the system this repo already covers as
> `factory-cli` / the `fct_*` MCP tools. Reach it through those, not the browser.

**Read-only recon, 11 Aug 2026.** Pointed here by Daman: *"there is one separate
engine turning — just read it, do not interfere."* Nothing was clicked that
writes; navigation and reads only.

---

## The correction this makes

I reported machine capacity as a **hard blocker — "exists in no system."** Wrong.

**And it is not even a system we didn't have.** `ji.jivo.in` is the **factory
app** — the one this repo already has a CLI and MCP surface for (`factory-cli`,
`fct_*`). Not a fourth system. A system we had, whose capacity data we failed to
read.

Three separate reasons it came back empty, none of them "the data isn't there":

1. The `raw/` captures my search read were scraped **3 Aug**. Line Management was
   added **5 Aug**. The captures are older than the feature.
2. The factory CLI's stored token **expired 2 Aug**, so nothing could be checked live.
3. The factory MCP surface **never substituted `{id}`** — 108 of 110 detail
   endpoints returned an HTML 404 to agents until it was patched **today**.

Three independent failures pointing the same way, and the conclusion I drew from
them was about JIVO's data rather than about my own coverage.

## What it holds

**Modules:** Admin · Daily Tasks · Dashboards · Dispatch · Gate · Goods Return ·
Labour · Vehicle Management · Quality Control · **Production** · Maintenance ·
Fire · Warehouse · Warehouse Ops · Barcode · Marketplace · **Supply Chain** ·
Order Processing · Notifications

**Production sub-modules:**

| Page | What it is |
|---|---|
| `/production/execution` | **Live production runs** — per line, per day, cases produced |
| `/production/execution/line-management` | Configuration presets per line, chosen when a run starts |
| `/production/execution/line-clearance` | Pre-production checklists & QA approval |
| `/production/execution/waste` | Waste logs, multi-level approval |
| `/production/execution/reports` | **OEE, efficiency, yield, downtime** |
| `/production/execution/cost-master` | Cost master |
| `/production/blowing` + `/make-vs-buy` + `/cost-master` | **PET bottle blowing** — in-house vs buy, with costing |
| `/dashboards/production-movement` | Production movement |

## Capacity — the answer, from actual output

Runs carry **line + product + cases produced + status**. That is *observed*
throughput, which is better than a rated capacity because it already includes
changeover, downtime and the real product mix.

Six named lines, plus Manual: **10 Head · 6 Head · Clear Pack · JP Machine ·
Pouch Machine · Tin Head**. These match the six line accounts found in the
factory app exactly.

Observed best-day output per line (cases), Jul–Aug 2026:

| Line | Peak run | Typical range | Products it runs |
|---|---|---|---|
| **Clear Pack** | **1,617** | 100–1,600 | cold press 1L/5L, sunflower, combos |
| **JP Machine** | **1,453** | 300–1,450 | mustard kachi ghani, sano mustard, groundnut |
| **Pouch Machine** | **1,550** | 790–1,550 | soyabean 700/750 gms pouch |
| **10 Head** | **1,800** | 10–1,800 | olive, groundnut, rice bran, pomace |
| **6 Head** | **1,600** | 8–1,600 | 5L packs, 2L handle, 3L, yellow mustard |
| **Tin Head** | **1,265** | (rare) | soyabean 12 kg tins |

Roughly **4–7 runs a day across the plant**, one line per run. **This is the
capacity model the pilot needs** — and it is per line per product, which is
exactly the "material-to-machine map" the brief asks Production to hand over on
a template. It already exists here.

## Rated speed — this is the actual capacity number

**Line Management holds rated speeds in bottles/hour**, created 5 Aug 2026 — 11
configurations across five Oil lines. *This is the machine capacity the brief
asks Production to supply on a template.* It already exists:

| Line | Rated speed (bottles/hour) |
|---|---|
| **JP Machine** | 5,400 |
| **Clear Pack** | 4,800 (1 L) · 3,000 |
| **Pouch Machine** | 2,400 · 1,800 |
| **10 Head** | 2,100 (1 L) · 1,260 (2 L) · 900 (5 L) |
| **6 Head** | 1,080 (1 L) · 720 (2 L) · 600 (5 L) |

Configs are **named presets, SKU optional** — Oil's are pack sizes (`1 LTR`,
`2 LTR`, `5 LTR`), and the operator picks one **by name** when starting a run.

## OEE — and my first reading of it was wrong

I initially read the five per-run figures on the reports screen (73.2% / 21.3% /
15.9% / 13.6% / 13.5%) as "the plant is at 13–21%." **That is a single day's
spread, not the plant's OEE.**

Measured properly across all 90 Oil runs, earlier today:

| | |
|---|---|
| **Median OEE** | **46.2%** |
| Median performance | 48.8% |
| Runs above 50% | 43 |
| Runs returning non-zero | 88 of 90 |
| **Availability, plant-wide** | **95.7%** |

Before 5 Aug, Oil had **zero** line-configs, so rated speed was missing and OEE
computed to 0.4–2.2% — the factory guide had written it off as "not usable as a
KPI." Adding the eleven rated speeds is what fixed it.

> [!warning] Do not quote OEE as an audited number
> The per-run spread is genuinely wide (13.5%–73.2% on 10 Aug alone). That is
> either real product/line variation **or operators picking the wrong named
> config for the run** — and the two are **not distinguishable from the data**.
> The figure is only ever as good as the rated speed somebody typed in.

## Downtime — 2,243 minutes, 49 incidents, one month

| Cause | Minutes | Incidents |
|---|---|---|
| **machine** | **937** | 6 |
| oil issue | 324 | 1 |
| **sticker issue** | 217 | **8** |
| SHRINK | 114 | 3 |
| bottle issue | 112 | 3 |

**37 hours lost in a month.** And read the tail: *sticker issue* (8×), *SHRINK*
(3×), *bottle issue* (3×) — **14 of 21 recorded stoppages are packaging-material
problems**, not machine problems. That is [[Ravinder Jivo]]'s and Kulbir's
territory, and it is the strongest argument yet that packaging deserves the
attention the brief gives to oil.

## Waste — all packaging

| Item | Wasted |
|---|---|
| PET BOTTLE 1 LTR 40 GMS | 3,651 pcs |
| PET BOTTLE 1 LTR 26 GM | 2,811 pcs |
| PET BOTTLE 1 LTR 52 GMS POMACE | 2,250 pcs |
| LABEL 1 LTR GROUNDNUT BACK | 1,697 pcs |
| LABEL 1 LTR GROUNDNUT FRONT | 1,672 pcs |

264 waste logs. **Every top-5 item is packaging.** Any 35% safety-stock
calculation that ignores this will under-order.

## Reports already built

`Daily Report` · `Resource Consumption` · `Monthly Summary` · **`Plan vs
Production`** · **`Procurement vs Planned`** · `OEE Trend` · `Downtime Pareto` ·
`Cost Analysis` · `Waste Trend`

> [!important] Two of these are the pilot
> **"Plan vs Production"** and **"Procurement vs Planned"** are, by name, the
> comparisons the whole coordination system is meant to produce. Before building
> them again, open them and see what they already do.

## Two live problems visible today

**1. Today's production has not started.** All six runs opened on 11 Aug read
**"No production yet"** — three *Stopped*, two *Breakdown*, one more *Stopped*:

| Run | Product | Line | Status |
|---|---|---|---|
| #6 | Mustard Kachi Ghani 1L 20pc | JP Machine | Stopped |
| #5 | Cold Press Groundnut 5L 4pc | 6 Head | **Breakdown** |
| #4 | Cold Press Sunflower 1L 20pc | Clear Pack | Stopped |
| #3 | Sano Mustard 1L 20pc | JP Machine | **Breakdown** |
| #2 | Rice Bran 5L 4pc | 6 Head | Stopped |
| #1 | Cold Press Groundnut 1L 16pc | 10 Head | Stopped |

By contrast 10 Aug completed all five runs (287–1,153 cases). **This is exactly
the event the pilot should be raising an alarm on** — and it is visible, today,
in a system nobody has connected to anything.

**2. Production is not reaching SAP.** The runs table has a **"SAP Entry"**
column and it is **`-` on nearly every row**. Only a handful carry a number
(2650, 3651, 6189, 6175, 2945), and those are older. This is the same shape as
the **factory GRPO feed found dead for 15 days** in earlier work: the floor
records production here, and SAP never hears about it.

## What this changes for the pilot

| Chain step | Was | Now |
|---|---|---|
| **7. Feasibility — machine capacity** | 🔴 blocker, "in no system" | ✅ **available** — per line, per product, observed |
| Material-to-machine map | asked for on a template | ✅ **already implied** by run history |
| Downtime / OEE | unknown | ✅ measured, and it says packaging is the problem |
| Waste | unknown | ✅ logged, all packaging |
| Plan vs actual | to be built | ⚠️ **a report already exists — go look** |

## Next, before building anything

1. **Open `Plan vs Production` and `Procurement vs Planned`.** By name, those are
   most of what this pilot is meant to produce. Check what they already do.
2. **Pull rated speeds + run history through `factory-cli`,** not the browser.
   The API is already generated and the `{id}` bug was fixed today, so the
   feasibility layer is a query, not a project.
3. **Ask who owns this system.** It is more advanced than anything in
   [[Kamalpreet Kaur]]'s brief, and the brief does not mention it. Somebody built it.
4. **Raise the SAP-entry gap** — production recorded here is not reaching the books.
5. **Don't average `per_unit_cost`** — it is 0.00 on 48% of Oil cost records
   (₹1.5 Cr of costed value), and those rows carry no run/date/line reference.
   Use `reports-analytics-cost-analysis` (`per_run`) instead.

## Two method notes worth keeping

**1. "Not in the systems I searched" is not "does not exist."** I checked SAP,
JSAP and the factory app's local captures, found nothing, and reported machine
capacity as missing from JIVO. The data was in the factory app the whole time;
my captures predated the feature, the token was expired, and the MCP path-param
bug 404'd the detail endpoints. **Three signals all saying "empty" for three
different reasons that were all mine.** Repeated empties from one toolchain are
evidence about the toolchain.

**2. A five-row screen is not a population.** I read five per-run OEE figures off
a dashboard and reported "the plant runs at 13–21%." The real median across 90
runs is **46.2%**. The five rows were a day's spread, and the framing turned a
normal distribution into a crisis.

## Links

[[people/SCOPE|SCOPE]] · [[people/Gautam|Gautam]] · [[people/Ravinder Jivo|Ravinder Jivo]] · [[people/ROSTER|ROSTER]]
