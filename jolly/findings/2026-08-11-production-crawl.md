# Finding 03 — production, crawled properly

**Date:** 2026-08-11 · **Company:** Jivo Oil · read-only browse, logged in
**Supersedes section C of Finding 02, which was wrong.**

---

## 0. Correction

Finding 02 reported 6 Head, Clear Pack and JP Machine as having **zero**
configurations. That was my error — the dropdown selection wasn't registering, so
the page kept showing the previous line's empty state and I read it as data.
Re-verified with a fresh page load per line. The speeds are there.

**Lesson for the pilot itself:** a UI that renders an empty state on a failed
selection is indistinguishable from real emptiness. Any agent scraping a screen
must confirm the selection took effect before trusting what the screen says. This
is exactly the class of error that would make a pilot message the wrong person.

---

## 1. The lines — real numbers

| Line | Configs | Speeds (bottles/hr) | Runs (17 d) | Avg OEE |
|---|---|---|---|---|
| **JP Machine** | 1 | 1 LTR **5,400** | 15 | 56.8% |
| **Clear Pack** | 2 | 1 LTR **4,800** · 5 LTR **3,000** | 22 | 43.5% |
| **10 Head** | 3 | 1 LTR **2,100** · 2 LTR **1,260** · 5 LTR **900** | 20 | 47.6% |
| **6 Head** | 3 | 1 LTR **1,080** · 2 LTR **720** · 5 LTR **600** | 22 | 40.1% |
| **Pouch Machine** | 2 | Hitech **1,800** · Samarpan **2,400** | 5 | 56.9% |
| **Tin Head** | 0 | — | 1 | 70.3% |
| **Manual** | 0 | — | 0 | — |

Only **Tin Head** and **Manual** lack configured speeds. Tin Head has run (once,
70.3% OEE), so it is a real line with a missing standard. Manual may not need one.

Line settings, identical on all seven: **std 572 h/month · 22 h/day**.
Operator says the default is a **12-hour shift** — 22 h/day is consistent with
*two* shifts minus changeover, not one. **Unresolved, and it is a 2× swing on every
capacity number.** Must be settled.

## 2. Nameplate capacity is sufficient. Measured performance is not.

Lines that can run 1 LTR: JP 5,400 + Clear Pack 4,800 + 10 Head 2,100 + 6 Head
1,080 = **13,380 bottles/hr**.

| Basis | Hours/month | 1 LTR bottles/month | vs Aug plan (2,189,500) |
|---|---|---|---|
| Nameplate, 12 h × 26 d | 312 | 4,174,560 | **1.9× — comfortable** |
| At measured Aug performance (~32%) | 312 | **1,335,859** | **short by ~854,000** |

**So the shortfall I claimed in Finding 02 is real, but my reason was wrong.**
It is not too few machines. It is machines running at roughly a third of the speed
they are configured for.

Confidence: medium. Performance % is computed against the configured standard
speed. Those standards were only recently entered and the SKU column is blank, so
some may simply be wrong (a standard set too high manufactures a bad OEE). Worth
settling before anyone acts on it.

## 3. OEE — availability is fine, performance is collapsing

85 runs over 17 days. **Overall average OEE 47%.**

| Date | Runs | Availability | Performance | Quality | OEE |
|---|---|---|---|---|---|
| 2026-07-31 | 4 | 92.1% | 92.8% | 100% | **84.9%** |
| 2026-08-01 | 7 | 98.8% | 30.5% | 100% | 29.3% |
| 2026-08-03 | 10 | 99.5% | 32.0% | 100% | 31.9% |
| 2026-08-04 | 7 | 97.1% | 41.2% | 100% | 40.0% |
| 2026-08-05 | 7 | 98.4% | 68.3% | 100% | 67.0% |
| 2026-08-06 | 7 | 93.6% | 31.1% | 100% | 26.9% |
| 2026-08-07 | 6 | 97.6% | 37.8% | 100% | 37.2% |
| 2026-08-08 | 3 | 100% | 32.2% | 100% | 32.2% |
| 2026-08-10 | 5 | 97.4% | 28.1% | 100% | **27.5%** |

Three things read off this:

1. **Availability is 93–100%.** The machines are not breaking down. Whatever is
   wrong is not downtime.
2. **Performance has fallen from ~93% to ~28% inside eleven days.** That is the
   entire story of August so far, and nothing in the current process surfaces it.
3. **Quality is 100% on every single day, on every line.** That is not a quality
   record, that is a field nobody fills. Treat it as absent, not perfect.

## 4. ⚠️ Production never reaches SAP

Every run in the execution list shows **SAP Entry = `-`**.

`Reports → Plan vs Production` — *"Compare SAP planned quantities against actual
production output"* — returns:

```
Total Orders 0 · Avg Achievement 0% · Total Planned 0 · Total Actual 0
"No production orders with SAP links found for the selected period."
```

`Reports → Procurement vs Planned` cannot run at all: it requires a SAP Production
Order to compare against, and there are none.

**Consequence, and it is the largest structural finding so far:** the factory app
knows what was produced; SAP does not. Every finished-goods stock figure in SAP is
missing actual output, and every raw-material figure is missing actual consumption.

The management brief's *"Live stock on hand — ERP — automatic"* is therefore true
about the field and false about the meaning. Any requirement the pilot computes
from SAP stock alone is computed from a book that stopped being posted to.

*(Consistent with the previously-noted broken factory→SAP GRPO feed. This is now
confirmed live and confirmed to affect production posting, not just receipts.)*

## 5. The material-to-machine map is derivable — same trick as lead times

The SKU column on line configs is blank, but **85 runs of history say what
actually ran where**:

| Line | Observed products |
|---|---|
| **JP Machine** | Mustard 1 LTR — Kachi Ghani, Sano, Round Bottle. Mustard's home line. |
| **10 Head** | Groundnut 1 LTR · Extra Light Olive 1 LTR · Sunflower 1 LTR |
| **6 Head** | Rice Bran 5 LTR · Groundnut 1/5 LTR · Yellow Mustard 1 LTR · Cold Press 2/3 LTR · Mustard 5 LTR |
| **Clear Pack** | Sunflower 1/5 LTR · Groundnut 5 LTR · Cold Press 5 LTR · combo packs |
| **Pouch Machine** | Soyabean 700/750 GMS pouches |
| **Tin Head** | 1 run |

So the third "reference template" ask is also derivable from history, at least as a
first draft that Production then corrects. **All three template asks now have a
data-driven starting point.**

## 6. Today is a bad day and nothing has raised a hand

**Aug 11: 6 runs started, 0 cases produced, 2 in Breakdown.** Aug 10 produced 2,961
cases across 5 runs.

Also, the execution list and the daily report disagreed on run status at the same
moment (Running vs Stopped). Low confidence — may be a refresh artefact — but two
screens disagreeing about the same run is exactly the ambiguity a pilot must
resolve before it messages anyone.

## 7. Access gap

`/production/planning` → **Unauthorized** on this account. The planning module —
where the monthly plan presumably lives inside the app — is not readable with the
credentials in use. Needed.

---

## What changed in the scorecard

| Input | Before | Now |
|---|---|---|
| Machine capacity | "mostly empty" | ✅ **11 configs on 5 of 7 lines** — only Tin Head and Manual missing |
| Material-to-machine map | ❌ missing | ✅ **derivable from 85 runs of history** |
| Labour per line | ❌ | ❌ still zero on every config |
| Hours/day basis | unknown | ⚠️ **app says 22, operator says 12-hour shift — unresolved, 2× impact** |
| SAP ← production posting | assumed working | ❌ **broken — zero runs linked to SAP** |
| Real constraint | assumed materials | ⚠️ **performance at ~30% of rated speed** |

## Open questions, ranked by what they cost

1. **Is the 22 h/day real, or is it one 12-hour shift?** Every capacity number
   doubles or halves on this.
2. **Why has performance fallen from 93% to 28% since 1 August?** Either the
   factory has a real problem nobody has escalated, or the newly-entered standard
   speeds are wrong. Both matter; they need different people.
3. **Is anything meant to post production to SAP, and did it ever work?**
4. **Who can grant read access to `/production/planning`?**
5. **Is Quality genuinely 100%, or is nobody entering rejects?**
