# jolly/ — JIVO Mark 2, the September 2026 production plan

You are in the **production planner**. Live at **https://jivo-mark2.vercel.app**
(Vercel project `jivo-mark2`, built from `site-sep/`).

**Owner: Gurvinderjeet Singh** — he owns JIVO's monthly planning. He has no SAP
login of his own (checked: not among the 55 SAP users) and does not need one.
He works from an **iPad** through a cloud Claude Code session, so he cannot run
anything locally, cannot open a terminal, and cannot see files you don't show him.
Answer in plain language. Give the number first, then one line on where it came from.

---

## THE ONE RULE THAT DEFINES THIS PROJECT

> **Only day 1 is observed. Every later day is COMPUTED from the day before plus
> what the algorithm decided.**

Opening stock is SAP as at **31 August 2026**, frozen in `sim/sep-inputs.json`.
Days 2–30 are the simulator's own output stacked on that. **Nothing after 1 Sept
has happened.** Never present a simulated day as a record, and never "look up"
what actually happened on a later date to improve it — that breaks the whole
premise.

Why it is worth trusting: the same engine, standing on 1 August knowing nothing
later, predicted **2,122,639 L** against the plant's actual **2,119,237 L**.
**0.16% off.** That calibration is the only reason these numbers get to have an
opinion.

---

## THE SECOND RULE — never type a business number

**Every figure on the site is computed by `site-sep/scripts/gen-data.py` from
`sim/` and `out/`, and imported from `site-sep/data/*.json`.** Never write a
business number into JSX, copy or markdown. UI constants (padding, widths,
Tailwind tokens) are fine.

`npm run gen` rebuilds `data/`. It runs **55 cross-checks and a phone-mask scan**
and **writes nothing if any fail**. If it refuses, the data is wrong — fix the
input, never the check.

---

## What is where

```
engine/freeze_sep.py    the opening position — reads SAP, writes sim/sep-inputs.json
engine/august_sim.py    the simulator. SIM_INPUTS=… SIM_TAG=-sep SIM_HOURS=12
                        SIM_SUNDAYS_OFF=1 python3 engine/august_sim.py
engine/plan_units.py    pack-size parsing. pack_litres() is the ONLY way to get litres
engine/plan_explode.py  BOM explosion with the yield guard
engine/sep_gap.py       zero-cover gap list with order-by dates
engine/refresh.sh       the 8-stage rolling refresh (freeze → sim → gen → deploy)
reference/*.md          EVERY ruling Daman has given. Read before coding.
sim/sep-inputs.json     the frozen 31-Aug opening — verify, don't re-derive
out/plan-sep-*.csv      the resolved, exploded September plan
site-sep/               the Next.js site (10 routes) behind jivo-mark2.vercel.app
```

---

## Traps that have already burned this project

**Merge oil synonyms before computing ANY shortage.** `reference/oil-synonyms.csv`
— groundnut=peanut, canola=cold-press-rapeseed, crude-rapeseed-new=domestic,
olive=olive-dark-colour. Unmerged they invented a **522,373 L phantom groundnut
shortage AND 357,635 L of phantom stranded peanut** — the same oil counted twice —
and it survived three adversarial verifiers because both numbers looked credible.
**`RM0000013` pomace is NOT `RM0000012` extra light. Never merge those two.**

**Two different oil series.** `opening.oil_l` (all RM oils) and the day files'
`oil_on_hand_l` (BOM-relevant only) are different definitions. Never chart them
as one line.

**Orders are 64% forecast.** The demand stream mixes real SAP orders with the
monthly plan dated into forecast buckets. Forecast rows are triple-tagged
(`channel=FORECAST`, docnum `FCST-*`, customer `(forecast — not yet ordered)`).
**Always split them, always keep them visually distinct.** On a quiet day the
"new orders" figure is 100% forecast.

**The day-1 order pile is real, not a bug.** 40 of 47 open plan-SKU orders were
already overdue on 31 Aug. That is the state of the book.

**The storage ceiling is ASSUMED.** 827,000 L working / 923,000 L peak, from
Daman's spreadsheet — **never measured** (open question Q2). Badge it wherever it
appears. The godown is FG only: two rooms, `BH-BT` + `BH-PF`. Bulk oil is in EXIM
tanks, packaging in `BH-BS`/`BH-PM` — neither is in this ceiling.

**Storage pressure is mostly already-sold stock.** On a bad day two-thirds of the
godown is invoiced-but-not-trucked, sitting on a declared **2-day invoice→truck
lag**. Measured against the factory app's real gate log, that 2 days is the right
median — but the tail runs to 14 days, and the plan ignores the tail.

**`standing_l = 0` at open is a declared OPTIMISTIC assumption** (C-0054).
Stock invoiced on or before 31 Aug but not gated out is uncounted, so day 1 is
really tighter than shown.

**Lines are derated twice where noted.** Clear Pack 5L and Tin Head are stored at
*observed* rates and the sim derates 50% again — say **"observed rate, then 50%
efficiency"**, never "50% of rated". 15 L PET has no measured rate anywhere; it is
DERIVED as the 5 L slot ÷ 3.

**Four plan SKUs are UNPRODUCIBLE** (no 3 L PET or DRUM line): FG0000034,
FG0000043, FG0000328, FG0000006. Show them, don't hide them.

**FG0000155 realise is an inherited outlier** (₹1,162/L vs ₹350/L in its own order
book). Never headline it unqualified.

**WhatsApp is simulated drafts.** Nothing was sent, nobody replied, every number
is masked. Never render it as real traffic. **No real phone number, ever.**

---

## Changing the plan

Scenarios are cheap and are the point of this thing:

```bash
SIM_INPUTS=sim/sep-inputs.json SIM_TAG=-sep SIM_HOURS=22 SIM_SUNDAYS_OFF=0 \
  python3 engine/august_sim.py          # re-run
cd site-sep && npm run gen && npm run build
```

Known result: **Sundays on** only reaches ~84% marginal usage; **flat 22 h** is the
best lever found (+₹18.5 Cr). Baseline is 2.67M L.

**Deploying:** the Vercel project is `jivo-mark2` and it is **not** linked to
GitHub — a push does not redeploy. Deploy with `engine/refresh.sh`, or
`npx -y vercel deploy --prod --yes` inside `site-sep/`, then make it public with
`python3 ~/.claude/scripts/vercel-public.py jivo-mark2`. **A cloud session cannot
do this — Vercel is blocked by the sandbox network policy.** Push the change and
say it needs deploying from a machine that can reach Vercel.

---

## What a cloud/iPad session cannot do

Say this plainly rather than failing quietly:

- **Reach SAP, factory, EXIM, Postgres** — they answer only from inside the office
  network loop. The credentials being in this repo does not change that.
- **Reach Vercel**, or view `jivo-mark2.vercel.app`. Verify against the local
  build and page source instead.
- **Re-freeze from live SAP** (`engine/freeze_sep.py`). The frozen inputs in
  `sim/` are what you have; everything else can still be re-run on top of them.

Everything else — re-running the simulator, regenerating the site data, editing
pages, fixing bugs — works completely.
