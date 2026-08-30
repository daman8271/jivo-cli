---
title: How JIVO plans the month — projection, PO, and the three allocation factors
type: reference
company: JIVO_OIL_HANADB
told_by: Daman (after a conversation with Gurvinderjeet Singh)
last_verified: 2026-08-29
status: owner-stated, not yet reproduced from data
tags: [jivo/reference, jivo/planning, jivo/allocation]
---

# How JIVO plans the month

**Told by Daman, 2026-08-29.** This is the model the whole scheduler must implement.
It is the owner's description of how the business actually works, and it supersedes any
reading of the plan as a fixed monthly list.

---

## 1. The month opens with a PROJECTION, not an order book

At the start of the month there is a **projection** — currently made by people, and
intended to be computed here in future. It is built from:

- last month's **demand**
- last month's **data** (the history in SAP)
- **market demand** — and this is explicit: *"let's say there is Diwali in September or
  October, so we'll automatically add some amount of purchases."*

**How the seasonal uplift must actually be computed** (Daman, 2026-08-29 — "this should
be properly calculated"): go to the SAME PERIOD LAST YEAR, measure what was selling
normally before it, and measure how much it ACTUALLY rose. The uplift is a measured
multiplier from history, never a guess.

**And it is not only festivals.** Platform events count the same way — a Flipkart or
Amazon sale event drives the same kind of spike and must be in the same calendar.
Source: ecom.jivo.in (platform PO feed).

The August workbook (`FINAL (2)`, 4,156.4 sale-tonnes) IS that projection. It is a
**forecast, not a commitment** — which is why it does not have to fit the factory.

## 2. Then the POs arrive, and the plan bends to them

From the 1st of the month, real purchase orders start landing. **Work is prioritised
against the PO, not against the projection.** As Daman put it: *"assuming POs start
coming from the first of that month, then things get prioritised according to that PO.
The planning shifts regarding which line to run and which things to do."*

A PO for 30 T of mustard reshuffles the schedule the moment it lands. The projection is
the backdrop; the PO is the instruction.

As POs accumulate through the month the two converge — the business "reaches its
planning and reaches its projection."

## 3. THE THREE FACTORS that alter the plan

> **1. PO**  ·  **2. realisation**  ·  **3. premium over commodity**

1. **PO** — an actual order outranks a projected one. Always.
2. **Realisation** — ₹ per litre. NOT turnover, NOT volume. See
   [[../../control-panel/vault/SALES-LENS-DECODER]]: JIVO's sales lens measures
   `realise` in ₹/L. A litre that realises more wins the line-hour.
3. **Premium beats commodity** — *"we give more and more preference to the premium
   section than commodity."* The plan already carries this split: `HEAD` =
   `COMMODITY` (2,282.0 T) or `PREMIUM` (1,874.4 T). Premium is the tiebreak, and
   it is a standing preference, not a per-decision judgement call.

## 4. The bottleneck is the whole point

> *"There might be a full stop since we have a bottleneck in production and our demand
> is kind of more. Our planning is doubled than our actual production, so we will
> allocate properly to proper SKUs accordingly."*

**The owner already knows the plan is ~2x what the factory can make.** This is not a
finding to report to him — it is the premise of the job. Measured independently:

| | |
|---|---:|
| Plan needs | 159,862 L/day |
| Factory's observed median day | 75,404 L/day |
| Ratio | **47%** |
| JIVO's own OEE screen (05 Aug) | median **46.2%** |

Two independent routes to the same number. The plan is written at 100% line efficiency;
the floor runs at ~47%.

## 5. Therefore the job is NOT scheduling. It is ALLOCATION FOR PROFIT.

> *"That is why we are making you to properly optimise this for profit and the factors
> as I told you."*

Capacity is scarce and demand is roughly double it, so **every line-hour given to one
SKU is taken from another.** The engine's job is to decide which SKUs win, maximising
profit, subject to:

```
maximise    sum over SKUs of ( litres_scheduled x realisation_per_litre )
subject to  line-hours available      (6 lines x 12 h x working days)
            material on hand + inbound (oil, bottles, caps, labels, cartons)
            flush cost                 (400 L of the next oil per oil change)
            PO commitments first       (a real order outranks a projection)
            premium preferred          (tiebreak toward the premium head)
```

**What this means for every engine in `jolly/engine/`:** the current chain answers
*"can we make the plan?"* — the answer is no, and that was never the question. The
question is *"of the plan we cannot fully make, which part do we make?"*

## 5a. Expiry is a constraint on shuffling

When POs reshuffle the plan, **expiry has to stay in view** (Daman, 2026-08-29). Stock
made early and displaced by a reshuffle can age out. ecom.jivo.in already tracks this:
`dashboard expiry-alerts-pos` — "purchase orders behind a platform expiry alert".

## 5b. The engine must decide what to DROP

> *"You should know what to ignore for other PO to get going first, on the factors I
> told you."*

Because demand is ~2x capacity, allocation is as much about what is REFUSED as what is
run. Every shift, the engine must name what it dropped and why — silently omitting a
SKU is the failure mode.

## 5c. Premium earns; commodity is for volume

> *"Premium oil is what earns us money, commodity is only for sale and all."*

Measured live from the Control Panel, Aug 2026:

| | Litres | Realise |
|---|---:|---:|
| PREMIUM | 785,436 | **Rs 195.72/L** |
| COMMODITY | 1,030,591 | Rs 155.98/L |

Premium earns **Rs 39.74 more per litre**. The owner's rule is confirmed by the data.

> **CAUTION: realise is REVENUE per litre, not MARGIN.** COGS is permission-blocked
> (HTTP 403 under the `preshit` login), so true profit per litre cannot be computed
> yet. Optimising on realise alone maximises REVENUE, and that is not the same
> instruction as "optimise for profit". See the open item below.

## 6. What is still needed to run this

| Input | Status |
|---|---|
| Realisation (₹/L) per SKU | ✅ **LIVE** — Control Panel `jivo sales data`, no auth needed. `out/realise-by-item.csv`, 81 items |
| **COGS / margin per SKU** | ❌ **HTTP 403 for `preshit`** — without it we optimise REVENUE, not PROFIT |
| Live PO feed, dated | ⚠️ ecom.jivo.in `platform pos` exists; the stored access token has EXPIRED |
| Premium/commodity flag | ✅ in the plan sheet, column `HEAD` |
| Line capacity | ✅ [[PLAN-AND-LINES]] — any oil, any line, 400 L flush |
| Material position | ✅ SAP + EXIM inbound |
| Projection method | **NOT BUILT** — to be computed here from history + season |

## Links

[[PLAN-AND-LINES]] · [[GODOWNS]] · [[OIL-PROCESSING]] · [[../people/SCOPE]]
