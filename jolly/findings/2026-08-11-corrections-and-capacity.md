# Finding 04 — corrections, and what capacity actually says

**Date:** 2026-08-11 · Jivo Oil
**Supersedes Finding 03 §4 (SAP posting) and §2 (capacity).**

---

## 1. Correction: SAP *does* have production. I was wrong.

`OWOR` (production orders), Jivo Oil: **8,092 orders**, running 2024-10-01 to
today. Operator's framing was right — SAP knows the **final output**; it does not
know **which machine** made it.

Cross-check, Aug 10, factory app runs vs SAP production orders:

| Factory run (line) | Cases | × pack | = bottles | SAP order | SAP qty | |
|---|---|---|---|---|---|---|
| RICE BRAN 5 LTR 4 PCS (6 Head) | 287 | ×4 | 1,148 | FG0000226 | 1,148 | ✅ exact |
| GROUNDNUT 1 LTR 16 PCS (10 Head) | 1,153 | ×16 | 18,448 | FG0000142 | 18,448 | ✅ exact |
| MUSTARD KG 1 LTR ROUND (JP) | 689 | ×20 | 13,780 | FG0000379 | 13,780 | ✅ exact |
| SANO MUSTARD 1 LTR (JP) | 442 | ×20 | 8,840 | FG0000136 | **9,840** | ❌ off by 1,000 |
| SUNFLOWER 1 LTR (Clear Pack) | 390 | ×20 | 7,800 | *none* | — | ❌ absent |

And SAP carries four Aug-10 orders with **no matching factory run**: sesame 1 LTR
(1,148), soyabean 1 LTR pouch (4,728), soyabean 750 gms pouch (1,092), extra light
olive CSD (12).

**The honest read:** three of five reconcile to the bottle, which proves the two
systems are describing the same reality. They just don't close. Neither system is
complete on its own, and nothing today notices the difference.

The `SAP Entry = -` column in the factory app means the **run** isn't linked to a
production order — not that production is unposted. Different problem, much
smaller: it costs you machine-level traceability, not stock accuracy.

## 2. Correction: the performance drop is material starvation, not slow machines

Operator's diagnosis: lines are not running slowly, they are **waiting for raw
material**. That fits the data better than my reading did — availability sits at
93–100% (the machine is *powered and assigned*), while performance collapses
(it isn't *making anything*). A line that is up but starved looks exactly like this.

**This is testable, and testing it is the highest-value thing on the list.** See §5.

## 3. Line settings, settled

| | |
|---|---|
| Default | **1 shift/day** |
| Shift length | 12 hours |
| Two shifts | possible, up to **22 h/day** — the machine takes 2 h rest |
| So `22 h/day` in the app | the **maximum**, not the default. Capacity math must use **12**. |

**Tin Head: 480 tins/day, 15 L each = 7,200 L/day.** (Quoted per day, not per hour —
so it goes in as a daily rate, not a bottles/hr standard like the others.)

**Manual: excluded.** Hand filling, not a planned line.

## 4. Capacity at 1 shift — there is no machine problem

1 LTR capable: JP 5,400 + Clear Pack 4,800 + 10 Head 2,100 + 6 Head 1,080 =
**13,380 bottles/hr**.

At 12 h × 26 days = **312 h/month**:

| Pack | Aug plan | Capacity available | Verdict |
|---|---|---|---|
| 1 LTR | 2,189,500 bottles | 4,174,560 | **1.9× headroom** |
| 5 LTR | 215,400 bottles | Clear Pack alone: 936,000 | comfortable |
| 2 LTR | 88,500 bottles | 10 Head + 6 Head: 618,000 | comfortable |
| Pouch | ~130,400 | Pouch Machine: 561,600–748,800 | comfortable |
| 3 LTR | ~10,667 | 6 Head has run it, **no standard entered** | gap |
| 200 ML | ~160,000 | **no line** | ❌ "Machine Pending" |
| 500 ML | ~47,000 | **no line** | ❌ "Machine Pending" |

**Conclusion: JIVO does not have a filling-capacity problem for its main packs.**
Roughly double the machine time it needs, at one shift, before touching the second
shift. My Finding 03 shortfall was an artefact of multiplying plan against a
performance number whose cause I had misread.

Real gaps: **200 ML and 500 ML have no line at all**, and **3 LTR has no standard**.

## 5. The test that proves the whole project

If lines starve for material, then on the worst-performing days the material
should have been at or near zero. That is checkable, entirely from data already in
hand:

```
for each production run with performance < 40%
  → its FG item → BOM → components
  → each component's stock on that date
  → was any component at/near zero, or did a GRPO land that same day?
```

Two outcomes, both useful:

- **It correlates** → the premise is proved with JIVO's own numbers, and every
  starved hour has a rupee value. That is the business case, and it is not an
  opinion.
- **It doesn't** → the standards are wrong, and OEE is measuring nothing. Worth
  knowing before anyone is asked to act on a 28% number.

This is the next thing to run.

## 6. `/production/planning` is not live

Tried as **Manager** (gurwinder@jivo.in) — still `Unauthorized`. There is no
Planning link anywhere in the navigation for that role either. The route exists in
the front-end route map but the module is not exposed.

**So the monthly plan lives in Gurvinder's Excel, not in the app.** For now the
pilot reads the spreadsheet. Worth confirming with whoever is building the app
whether planning is coming — if it is, the pilot should read the app instead.

---

## Scorecard

| Input | Status |
|---|---|
| BOM, item master, stock, sales | ✅ SAP |
| Production output | ✅ SAP (`OWOR`) — final output only, no machine |
| Machine-level production, OEE, breakdowns | ✅ ji.jivo.in |
| Line speeds | ✅ 5 lines + Tin Head daily rate; 3 LTR / 200 ML / 500 ML missing |
| Material-to-machine map | ✅ derivable from run history |
| Lead times | ✅ derivable from PO→GRPO, per vendor |
| Shift basis | ✅ 1 shift, 12 h; 22 h = 2-shift max |
| Monthly plan | ✅ Excel (app module not live) |
| Labour per line | ❌ zero everywhere |
| Committed/orders | → from OMS, not SAP |
| **The actual constraint** | ⚠️ **material availability — to be proved by §5** |
