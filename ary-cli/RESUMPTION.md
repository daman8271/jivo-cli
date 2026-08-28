# RESUMPTION — the ARY expansion task, paused

> **Claude: if the user says "resumption", "resume the ARY task", "continue ARY", or
> "start the resumption" — this file is the entry point. Read it, then
> `assort/vault/00-ARY-Atlas.md`, then pick up at "What to run first" below.**

**Paused:** 2026-08-29, 00:20 IST · **Reason:** Anthropic session quota exhausted
**Owner:** Daman · **Resumes:** when the user says so, in this chat or any other

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

### 3. Demand research missing — 10 of 46 categories

`kidswear · winterwear · stationery · books · sports · toys · mobile-tech · appliances ·
gurmat · festival-gift`

**Note:** `gurmat` matters more than its position suggests — dastar/patka is already
ARY's fourth-largest per-resident category at ₹198.70/resident/yr
(`assort/vault/02-categories/Institution-Range.md`) and no external benchmark contains it.

### 4. Coverage diff — 15 of 36 categories

`diff.py` stalled. Re-run: `python3 assort/bin/diff.py` (safe to re-run; it overwrites).

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
