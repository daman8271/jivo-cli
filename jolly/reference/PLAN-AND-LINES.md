---
title: The plan sheet and the filling lines
type: reference
company: JIVO_OIL_HANADB
last_verified: 2026-08-29
tags: [jivo/reference, jivo/plan, jivo/lines]
---

# The plan sheet — settled

**`FINAL (2)` is the plan. Daman, 2026-08-29.** Verified live against the workbook:

| | Tonnes |
|---|---:|
| GT/MT/ROI (trade) | 1,998.40 |
| Ecom | 2,083.00 |
| **TOTAL PLANNING** | **4,156.40** ✅ |
| — of which first week | 1,135.12 |

99 SKU rows · 2,809,166 total pieces · file kept locally at
`jolly/briefs/AUG-PLAN-2026.xlsx`

**The other two sheets are dead to us.** `FINAL` (186 rows, 4,390 T) and `Sheet2`
(3,661 T) are earlier or partial cuts. Any engine reading the plan reads
`FINAL (2)`, column **`TOTAL PLANNING (IN TONS)`** (index 15).

Ecom is **50.1%** of the plan. It reaches Oil as transfers to JIVO Mart, which Oil
cannot see until Mart raises the order.

---

# The filling lines — settled

| Line | Speed | Source |
|---|---|---|
| JP Machine | 5,400 btl/hr (1 LTR) | ji.jivo.in |
| Clear Pack | 4,800 (1 LTR) · 3,000 (5 LTR) — **size-changeable: 1 L / 4 L / 5 L** (Daman 2026-08-29) | ji.jivo.in |
| 10 Head | 2,100 (1 LTR) · 1,260 (2 LTR) · 900 (5 LTR) | ji.jivo.in |
| 6 Head | 1,080 (1 LTR) · 720 (2 LTR) · 600 (5 LTR) | ji.jivo.in |
| Pouch Machine | Hitech 1,800 · Samarpan 2,400 | ji.jivo.in |
| **Tin Head** | **4 tins/min = 240/hr** | **Daman, 2026-08-29** |
| ~~Manual~~ | **NOT CONSIDERED** — hand filling, out of scope | Daman |

## Shift length is a DECISION, not a constant — Daman, 2026-08-29

> *"We can run this at minimum 12 hours a day for 26 days a month, but it is your
> choice. If we need to fulfil everything and earn more money we can run this all
> month plus 24 hours. But you will also have to consider the inefficiency of machines
> since the electricity bill goes up."*

| | Hours/line/month |
|---|---:|
| **Floor** (current default) | 12 h x 26 d = **312 h** |
| Extended days | 12 h x 31 d = 372 h |
| Two shifts | 22 h x 26 d = 572 h (24 h minus 2 h machine rest) |
| **Ceiling** | 24 h x 31 d = **744 h** |

**The engine must CHOOSE the shift pattern**, per line and per period, trading extra
contribution against extra electricity and the efficiency loss on long runs. 12 h is
the minimum, not the answer. Alternating patterns are allowed.

## ANY OIL RUNS ON ANY LINE — ruled by Daman, 2026-08-29

There is **no oil-to-line restriction**. Every line can fill every oil. A line is
constrained only by the CONTAINER SIZE it is set up for, never by what is in the tank.
This kills the whole "which oil belongs on which machine" question — it does not exist.

## FLUSHING — the hard constant

> **Every oil change costs 400 L of the NEXT oil.** — Daman, 2026-08-29

That is the entire cost of a changeover, and it is a MATERIAL cost first:

    flush oil   = 400 L of the incoming oil, per changeover, per line
    flush time  = 400 L / that line's throughput in L/hr
                = 400 / (pieces_per_hour x litres_per_piece)

Time cost per flush, computed from the rated speeds above:

| Line | Pack | L/hr | Flush time |
|---|---|---:|---:|
| JP Machine | 1 L | 5,400 | **4.4 min** |
| Clear Pack | 1 L | 4,800 | 5.0 min |
| Clear Pack | 5 L | 15,000 | 1.6 min |
| Pouch Machine | 1 L | 4,200 | 5.7 min |
| Tin Head | 15 L | 3,600 | 6.7 min |
| 10 Head | 1 L | 2,100 | 11.4 min |
| 6 Head | 1 L | 1,080 | **22.2 min** |

### The flush oil is REUSED — and it lasts about a MONTH — Daman, 2026-08-29

> *"That is why we use the oil of flushing multiple times."*
> *"The oil which is used in flushing lasts for like one month."*

**So flush oil is a monthly working stock, not a per-changeover consumable.** The
correct cost model:

    MATERIAL : ~400 L per oil, ONCE PER MONTH   (not 400 L per changeover)
    TIME     : 400 L / line litres-per-hour     (per changeover, every time)

Charging 400 L on every change overstated the material cost by roughly the number of
changeovers in the month. Time is the only cost that scales with how often you switch.

**So the 400 L is not scrapped.** It is put back and used again, which means a
changeover's real cost is the TIME on the line, not the oil. Correcting an earlier
reading in this file that called flushing "expensive in oil" — it is not.

**What this actually means for scheduling:** a changeover costs 4-22 minutes and
almost nothing in material. Seventeen changeovers across six lines in a shift is
roughly 14 minutes per line — affordable. So the scheduler should NOT contort itself
to group oils; it should chase value and accept the flushes. The one line where
flushing genuinely hurts is **6 Head at 22 min a change**, because it is the slowest.

> [!success] Tin Head — SETTLED: **240 per hour**
> **4 tins/min = 240/hr = 2,880 per 12-hour shift = 74,880 per 26-day month.**
> Daman confirmed 2026-08-29. The old "480/day" figure from 2026-08-11 is DEAD —
> do not quote it, do not average the two.
> Tins are 15 L, so 240/hr = 3,600 L/hr.
>
> **This makes Tin Head the ONLY binding constraint in August.** The plan needs
> 88,333 tins against 74,880 of capacity — 118%, short 13,453 tins (56 hours).
> Every other line has slack; 6 Head is completely idle.
