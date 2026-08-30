# RESUMPTION — the ARY expansion task, paused

> **Claude: if the user says "resumption", "resume the ARY task", "continue ARY", or
> "start the resumption" — this file is the entry point. Read it, then
> `assort/vault/00-ARY-Atlas.md`, then pick up at "What to run first" below.**

**Paused:** 2026-08-29, 00:20 IST · **Reason:** Anthropic session quota exhausted
**RESUMED:** 2026-08-30 · **Owner:** Daman

## ⚡ What changed on resumption (2026-08-30) — read this before anything else

1. **THE DATA IS LIVE AGAIN.** The internal physical stock audit that froze the feed at
   2026-08-21 is over. Sales, purchases and accounting now run to **2026-08-30**
   (1,099,364 bills; ~1,100-1,200 bills/day since 08-22, normal). **Every figure in the
   vault and in VERIFIED-FACTS.md is windowed to 2026-08-21 and is now slightly stale.**
   Catalogue is 21,472 SKUs / 19,487 active (was 21,466 / 19,481).
2. **10 "missing" demand lanes were never missing — they were unharvested.**
   `harvest.py` pulled them straight out of the workflow journals: demand **36 → 46
   (COMPLETE)**, sweep **10 → 15**. Zero agent cost. Gap #3 below is CLOSED.
3. **Two dated, legal findings were buried by the quota wall** — see "Live exposures" below.
   Neither is in the published brief.
4. **✅ The `verify` + `priority` stages are DONE** — workflow `wf_b45e4f60-a14`,
   38/38 agents. **293 claims tested, 106 REFUTED, 91 load-bearing. 7 of 15 lanes now
   rate LOW.** Full record: **`assort/vault/05-corrections/Verify-Pass-2026-08-30.md`
   — READ THAT BEFORE QUOTING ANY FIGURE FROM THIS VAULT OR THE PUBLISHED BRIEF.**
5. **Coverage diff COMPLETE — 46/46.** (A `timeout 900 ... | tail` pipeline had masked
   a kill at 24/46: a pipeline returns `tail`'s exit code, not `timeout`'s. Re-run
   unbuffered.) Across the 22 new categories: **1,280 SKU lines checked, 8 missing.**
6. **The finding: 3,049 of 5,953 retail SKUs that sold this year are OUT OF STOCK today
   (51.2%), with Rs 1.51 Cr of trailing sales behind them — 27 of the top 100 sellers
   among them.** Sizing verdict across 21 categories: **18 AVAILABILITY_NOT_ASSORTMENT,
   2 REAL_GAP, 1 FALSE_GAP.** The fleet's Rs 13.3 Cr of recommendations grounded to
   **Rs 53 L revenue / Rs 9.8 L GM — a 96% cut.**
7. **🔴 The biggest customer sells at cost.** Hunger Heroes (Delhi NGO, 9.2% of turnover):
   **1.04% GM on Rs 69.81 L** vs retail's 24.42%. Loose milk to them is **-10.49%**, and
   **100% of the -Rs 67,094 loose-milk loss goes to that NGO — zero litres to campus
   residents.** Any framing of it as a subsidy for boarding children is wrong.
8. **🔴 REVERSED: FusionERP8 CANNOT hold batch/expiry.** An earlier correction saying it
   could was wrong. `ProductChildMaster` = 111,253 rows, **0 real expiry dates**; only
   MatrixID 3 covers 49 SKUs (0.25%) while MatrixID 4 covers 19,054 and defines no such
   fields; Benadryl's "22 batches" are nine years of price revisions. **The pharmacy
   blocker is REAL — restore the vendor question.**
9. **🔧 `ary assort probe` is NON-DETERMINISTIC and silently zeroes on hyphens.** It is
   the mandated anti-false-gap guard, so **every "probe returned zero" verdict is unsafe.**
   Fix before trusting further output.

### 🔴 Live exposures found in the newly harvested lanes (hand-verified against live DB)

| | Lane finding | My live re-check | Status |
|---|---|---|---|
| **Allopathic drugs, no Form 20 licence** | Rs 8,849/yr, 183 lines | **Rs 29,668/yr, 598 bill lines, 14 active SKUs** (Volini gel/spray, Disprin, Crocin) | ⚠️ **3.4x worse than the lane said**. NOTE: Schedule K of the D&C Rules exempts certain household remedies in rural areas — a lawyer or the drug inspector must settle whether it applies before either de-listing or filing Form 19. I did NOT confirm this either way. |
| **IMS Act 1992 — infant formula/food/bottles** | 59 active SKUs | **59 exactly** — 9 formula + 34 infant food + 16 bottles/nipples | ✅ confirmed. Mandatory-minimum 6 months' imprisonment under s.20(2) for a category doing ~Rs 535/month. |
| **BIS QCO 2026 appliance cliff, 1-Oct-2026** | 34 SKUs, Rs 2.08 L | 59 SKUs / Rs 3.07 L on a loose name-match — **the lane's group-scoped 34 is the better cut** | ⚠️ needs a clean re-cut. The escape hatch is FREE: a six-month sell-down declaration to BIS, filed before the deadline. |

---

## What this task is

ARY (Akal Rozgar Yojana, a unit of Jivo Wellness Pvt Ltd) is the **only shop for ~5,000
people** living on the closed 450-acre Baru Sahib campus in Rajgarh, Himachal Pradesh.
The brief: **find every product those 5,000 people need that ARY does not sell, and
maximise ARY.**

The answer so far inverted the premise — **ARY has an availability problem, not an
assortment problem.** It lists 1.79× the benchmark range and sells 0.59× of it. Full
argument: `assort/vault/00-ARY-Atlas.md`.

---

## What is DONE (do not redo)

| | |
|---|---|
| **`ary assort` CLI module** | 13 commands, ~1,400 lines Go, `go vet` clean, all live-tested |
| **`assort/vault/`** | 27 linked notes, 124 wikilinks, 0 broken — the readable findings |
| **`assort/data/VERIFIED-FACTS.md`** | 46 sections, the audit trail, every number carries its query |
| **Published brief** | <https://jivo-ary.vercel.app> (public, no SSO — verified 200 logged out) |
| **`assort/bin/harvest.py`** | pulls agent results out of workflow journals into the corpus |
| **`assort/bin/diff.py`** | matches researched SKU lines against the live catalogue |
| **Research corpus** | 36 demand categories / 1,984 SKU lines · 21 coverage · 10 sweep lanes |

**79 of ~145 research agents completed** across three workflows.

---

## What is LEFT

### 1. The workflows — resume, do not restart

Three runs, all resumable from cache (completed agents replay free):

```
wf_96b430ed-466   ary-assortment-expansion   demand → coverage → priority
wf_ed9e002f-cae   ary-intelligence-sweep     population, wallet, leakage, diagnostics
wf_e4a35fe9-196   ary-execution-reality      pricing, licensing, suppliers, risk
```

Scripts live under
`~/.claude/projects/-Users-damanpreetsingh-jivo-cli/<session>/workflows/scripts/`.
Resume with `Workflow({scriptPath: …, resumeFromRunId: …})`. **Stop a run first with
TaskStop if it reports "still running".**

### 2. Stages that have NEVER run

- **`verify` — all ~40 lanes. This is the real gap.** Nothing in the research corpus has
  been adversarially challenged; every verifier died at a quota wall. Findings marked
  VERIFIED in the vault were checked by hand against the live DB and do not depend on it,
  but every research-derived figure has exactly one pair of eyes.
- **`priority` — all 46 lanes.** Rupee-sizing each gap with a stated penetration assumption.

### 3. ~~Demand research missing — 10 of 46 categories~~ ✅ CLOSED 2026-08-30

All 46 lanes were already in the workflow journals; `python3 assort/bin/harvest.py`
folded them into the corpus. **Lesson: check `harvest.py --list` against
`ary assort research` before commissioning any agent — the journals routinely hold
finished work the corpus has not absorbed.**

**Note:** `gurmat` matters more than its position suggests — dastar/patka is already
ARY's fourth-largest per-resident category at ₹198.70/resident/yr
(`assort/vault/02-categories/Institution-Range.md`) and no external benchmark contains it.

### 4. Coverage diff — in progress 2026-08-30

Now 46 demand lanes to diff, not 36. `diff.py` re-running in background (23/46 at last
check; it is slow, ~1 category/min). Safe to re-run; it overwrites.

### 5. Six questions that need a HUMAN, not an agent

Full detail: `assort/vault/06-playbooks/Open-Questions.md`

1. **What do Akal Dairy, Akal Bakery and Akal Modi Khana actually supply?** ← highest value.
   Decides whether the ₹2.51 Cr institutional headline is an opportunity or a mirage.
2. Is the ₹47/L milk price deliberate subsidy or neglect? (₹66,951/yr)
3. Does Akal Charitable Hospital hold a drug licence?
4. Can FusionERP8 store a batch/expiry date? (0 of 111,021 rows do — the real pharmacy gate)
5. Does stitching labour sit inside the unstitched-suit margin? (₹11 L rides on it)
6. What is Akal Academy's actual enrolment? (±350, moves every per-resident figure)

---

## What to run first on resumption

```bash
cd ~/jivo-cli/ary-cli
set -a; . ../connections/ary.env; set +a
./ary doctor                    # is ARY reachable, and how fresh is the data?
./ary assort research           # what the corpus holds now
python3 assort/bin/harvest.py --list    # what the workflow journals hold
```

Then, in priority order:

1. **Resume the three workflows** — `verify` and `priority` first; they are the honest gap.
2. **Re-run `diff.py`** for the 15 missing coverage categories.
3. **Harvest and fold new findings into the vault**, not into a new file.
4. **Re-publish** — edit `assort/out/ary-expansion-brief.html`, then
   `cd assort/site && vercel deploy --prod --yes` (site is a copy; rebuild it from the
   brief the same way it was built first time).

---

## Rules that apply to this task

- **Read-only, always.** Zero `sapb1` calls across ~280 agents so far; keep it that way.
  The `ary` CLI cannot write (SELECT-only guard + always-rolled-back transaction).
- **The burden of proof sits on "missing", never on "covered."** Four times a confident
  finding turned out to be a broken field. Read
  `assort/vault/01-foundations/Data-Quality-Traps.md` before quoting any number.
- **Never total the research lanes' recommendations.** They sum to ₹13.3 Cr against a
  ₹7.55 Cr business — see `assort/vault/05-corrections/Fleet-Method.md`.
- **This repo is PUBLIC.** `connections/ary.env` is gitignored and must stay that way.
- Commit by pathspec. The index in this repo is usually not ours.
