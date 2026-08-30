# Finding 06 — the production-requirement formula, tested on live data

**Date:** 2026-08-11 · Jivo Oil · read-only
**Source:** operator's handwritten note

---

## The formula

```
OIH  = Order In Hand, from OMS
MSL  = 35% of finished goods sold last month

Production Requirement = OIH + MSL − FG in BH-BS (godown)
```

Operator's example:

```
FG0000023   OIH 7,300 · FG 1,200 · last-month sale 10,000
            MSL = 10,000 × 35% = 3,500
            Required = 7,300 + 3,500 − 1,200 = 9,600
```

The logic is sound: cover what's ordered, hold a buffer proportional to how fast
the SKU moves, credit what's already sitting in the godown. Nothing to argue with
in the shape of it. Everything below is about the terms.

---

## Run live on a real SKU

`FG0000030 — MUSTARD KACHI GHANI 1 LTR 20 PCS`, as of 2026-08-11:

| Term | Value | Source |
|---|---|---|
| Open sales orders (`OpenQty`) | **69,339 PCS** | SAP `RDR1`/`ORDR`, 20 open orders |
| July 2026 sold, gross | 158,085 PCS | SAP `INV1`, 37 invoices |
| July returns | 2,965 PCS | SAP `RIN1` |
| July net | 155,120 PCS | |
| **MSL** = 35% × net | **54,292 PCS** | |
| **FG in BH-BS** | **0** | ← see below |
| FG in the actual finished godowns | 10,232 PCS | BH-BT 6,852 + BH-FG 3,380 |

```
As written (BH-BS)      : 69,339 + 54,292 −      0 = 123,631 PCS  (6,182 cartons)
With real FG stock      : 69,339 + 54,292 − 10,232 = 113,399 PCS  (5,670 cartons)
                                                     ─────────────
                          over-production from one wrong warehouse: 512 cartons
```

For comparison, the **August plan for this SKU is 220,000 PCS** — roughly 1.9× what
the formula returns.

---

## ⚠️ Q1. BH-BS is the packaging warehouse. It holds no finished goods.

Not an inference — the whole contents:

```
BH-BS "Bhakharpur Basement" — 127 items, 2,649,984 units, EVERY ONE prefix PM
  PM0000235  CAPS 1 LTR WHITE AND YELLOW      480,000
  PM0000594  PREFORM 40 GMS 36 MM             304,000
  PM0000852  PREFORM 49.5 GMS 36 MM           288,253
  PM0000817  PREFORM 21/23 GMS                223,488
  ...
```

Zero `FG` items. Finished goods actually live here:

| Warehouse | Name | SKUs | Qty |
|---|---|---|---|
| **BH-BT** | Bhakharpur **New** Basement | 102 | **202,753** |
| **BH-PF** | Bhakharpur Production Finished 1st Floor | 59 | **183,411** |
| BH-SC | Bhakharpur Schemes | 18 | 70,296 |
| GP-FG | Gupta Godown Basement Finished | 55 | 19,741 |
| BH-FG | Bhakharpur Finished Basement | 18 | 13,432 |
| BH-GR | Bhakharpur GR | 48 | 9,633 |
| PB-JP | Punjab Grover Agency C&F | 9 | 3,105 |
| BH-WST | Wastage | 59 | 3,365 |

**Best guess:** "Bhakharpur Basement" was written from memory and the real
finished-goods basement in SAP is **BH-BT, "Bhakharpur New Basement"**. But that is
a guess and it must not be one — reading the wrong godown silently inflates every
production number by whatever sits in the godowns you left out.

Three sub-questions inside this one:

- **BH-PF** holds 183,411 units of finished goods on the production floor. Produced
  but not yet moved down. Does it count as stock in hand?
- **GP-FG (Gupta Godown)** and **PB-JP (Punjab Grover C&F)** hold finished goods at
  agents. We own them. Do they count, or is anything outside Bhakharpur invisible?
- **BH-SC (Schemes)**, 70,296 units — reserved for promotions, or available?

## Q2. Units — OMS counts boxes, SAP counts bottles

OMS order lines carry `boxes`, `qty`, `pcs` **and** `ltrs`:

```
order 2653 → FG0000015 REFINED OIL 15 LTR : boxes 6 · pcs 1 · ltrs 90 · qty 6
```

SAP holds finished-goods stock in **PCS** (`InvntryUom = PCS`, and per correction
C-0001 that means single bottles, never cartons).

So `OIH` arrives in boxes and `FG` is in bottles. For FG0000030 that is a **20×
error** if they are added directly. Which unit should the formula run in? My
recommendation is **PCS everywhere**, converting OMS boxes × case-pack on the way
in, because BOM explosion and stock are both already in PCS.

Your example numbers (7,300 / 1,200 / 10,000) — bottles or boxes?

## Q3. Which OMS statuses count as "in hand"?

OMS has eleven:

```
1 Order Created · 2 Rate Approval · 3 Billing · 4 Need Approval ·
5 Billing Pending · 6 Approved · 7 Rejected · 8 Billing Rejected ·
9 Completed · 10 Auditor Approval · 11 Draft
```

`Rejected`, `Billing Rejected` and `Draft` are clearly out. `Completed` is out —
already billed. **The other seven are a judgement call**, and it is a large one:
counting orders still sitting in Rate/Need/Auditor Approval means producing for
demand that may never be confirmed.

Live example: order **2653** was raised today by *sumit* for ILAHI CO, delivery
13 Aug, and its `approved_at` is **null** — it is sitting in approval right now.
In hand, or not?

## Q4. E-commerce is more than half the plan and OMS cannot see it

Your own August plan:

| | Litres | Share |
|---|---|---|
| Commodity (GT/MT/ROI) | 1,232,500 | 28% |
| Premium | 799,400 | 18% |
| **Ecom** | **2,358,000** | **54%** |

OMS raises orders into Oil and Beverages only, and e-commerce demand does not flow
through it. SAP even has a dedicated warehouse — `BH-EC "BHAKHARPUR FINISHED
E-COMMERCE"`.

**If OIH comes only from OMS, the formula is blind to 54% of the demand it is
meant to plan for.** Where does e-com order-in-hand come from, and is it in scope?

## Q5. Scheme and free-of-charge goods

OMS lines carry `qty_scheme`, `scheme_item_code`, `scheme_name`; orders carry
`is_foc`. Free goods are real bottles off a real line. Are scheme quantities inside
OIH, or added separately? (`BH-SC` holding 70,296 units suggests scheme stock is
managed apart.)

## Q6. "Sold last month" — three sub-decisions

- **Gross or net of returns?** FG0000030 July: 158,085 gross vs 155,120 net —
  2,965 bottles, ~1% here, much more on high-return SKUs. JIVO's settled definition
  of sales is net of credit notes, so net is the consistent choice.
- **Does intercompany count?** Oil sells to Mart across 23 group card codes
  (correction C-0005). Those are internal transfers, not market demand. Counting
  them buffers against your own group movement.
- **Calendar month or rolling 30 days?** On 1 August, "last month" is fresh. On
  31 August it is 60 days stale, in a business whose whole problem is moving fast.
  Rolling 30 days keeps MSL current and costs nothing.

## Q7. Production already scheduled is not subtracted

The formula counts orders and stock but not work already in flight. If 20,000 are
already released to a line, requirement should fall by 20,000 or you make them
twice.

**But this needs care** — SAP's open production orders are not clean:

```
FG0000030, status P (planned), never completed:
  626818   10,000 PCS   posted 2025-06-28
  1124026615 8,400 PCS  posted 2024-11-20
```

Two stale orders, one nearly two years old, still open. Subtracting open production
orders naively would wipe out 18,400 bottles of genuine requirement. If we subtract
them, it must be with an age cut-off.

## Q8. Floor at zero

When `FG > OIH + MSL` the formula returns a negative. Assume that means "produce
nothing" rather than a negative requirement flowing downstream into BOM explosion.
Confirm.

## Q9. The formula and the monthly plan disagree

FG0000030: formula ≈ **113,000**, August plan **220,000**. Nearly 2×.

They may simply answer different questions — the formula is a snapshot of what to
make now, the plan is a month's intent including stock-build and e-com. But if both
exist, one of them has to govern what actually runs. Which?

---

## What I need to build this

Answer Q1 (which godown), Q2 (which unit) and Q3 (which statuses) and I can compute
the production requirement for every Oil SKU tonight, live, and show it against the
August plan line by line. The rest can be decided as we look at the output.

Then the same machine runs downward into raw materials: requirement → BOM →
packaging and oil needed → minus stock → minus what's on order → against real
per-vendor lead times → what must be bought today.
