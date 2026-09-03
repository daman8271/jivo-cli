# jolly/ — JIVO Mark 2, the September 2026 production plan

You are in the **production planner**. Live at **https://jivo-mark2.vercel.app**
(Vercel project `jivo-mark2`, built from `site-sep/`).

**Owner: Gurvinderjeet Singh** — he owns JIVO's monthly planning. He has no SAP
login of his own (checked: not among the 55 SAP users) and does not need one.
He works from an **iPad** through a cloud Claude Code session, so he cannot run
anything locally, cannot open a terminal, and cannot see files you don't show him.
Answer in plain language. Give the number first, then one line on where it came from.

---

## 🔴 RULE 0 — FACTORY TRUTH IS `ji.jivo.in`. NEVER SAP. (Daman, 2026-09-03)

> *"ji.jivo.in has the ultimate data about the factory, no one dares come near.
> You should always listen to ji.jivo.in whatever the case. All the factory
> monitoring is there and there only. This is the reason your results are so
> different."*

**Do not answer a factory question from SAP.** Not production, not stock, not
dispatch, not receiving, not lines. Every one of them has a live owner:

| Question | Ask | Never ask |
|---|---|---|
| what was made, on which line, stock on hand | **ji.jivo.in** (`factory-cli`) | SAP |
| what left the gate / is still in the warehouse | **ji.jivo.in `/dispatch`** | SAP invoices |
| what material arrived, what is in QC | **ji.jivo.in** GRPO / gate board | SAP GRPO |
| bulk oil, tanks, the monthly plan | **EXIM** | SAP |
| sales + purchase orders, GT/MT | **OMS** (`oms.jivo.in`) | SAP `Orders` |
| ecom purchase orders | **ecom.jivo.in** | SAP |

**Why this is not a preference.** Backtested 2026-09-03 against the first two days
of September, a SAP-sourced answer said the plant would make 269,740 L and run
COLD PRESS GROUNDNUT 5 LTR. The factory made 85,488 L of **1-litre** olive,
mustard and sunflower — **0 of 15 SKUs matched**. Meanwhile ji.jivo.in's gate
board showed 156,000 one-litre caps and 37,000 one-litre bottles arriving. The
factory systems were coherent with each other and SAP was the outlier.

**If a live source lacks something Mark 3 needs, BUILD the CLI for it.** Daman:
*"if you find something which is not part of the CLI just make one of it, simple
as that."* Do not fall back to SAP because it is easier.

**A business truth that changes the storage maths:** goods stay in the warehouse
and count as storage pressure **until they are physically DISPATCHED**. Booked,
invoiced and billed are not dispatched. `ji.jivo.in/dispatch` holds that truth —
Mark 2's flat "2-day invoice→truck lag" is a guess that this source replaces.

---

## MARK 3 — the live system (LIVE since 2026-09-03 14:59 IST)

Mark 3 replaces the 31-August photo with the plant's position **every 3 minutes**,
read from the live systems above — never SAP — by the VPS:

```
live/                      the ingest loop. README.md is the adapter contract.
live/adapters/<source>.py  factory_dispatch · factory_production · factory_inbound · exim · oms · ecom
live/collect.py            runs them, writes live/state/state.json   (cron */3 on the VPS)
live/keepalive.sh          daily re-logins (factory, OMS, ecom)       (cron 04:17)
live/publish/              the HTTPS publisher (Traefik route + read-only JSON server)
live/PHASE4-FREEZE-LIVE.md the engine on live state  — freeze_live.py rebuilds sim/live-inputs.json
live/PHASE5-SITE.md        the Mark 3 site — a static shell that fetches the publisher every 180 s
reference/MARK3-LIVE-SOURCES.md   every live command, verified, with its traps (102 KB — read it)
```

**The Mark 3 site — public, no login: https://jivo-mark3.vercel.app**
(Vercel project `jivo-mark3`; `site-live/`; a static shell that fetches the
publisher every 180 s — a deploy is a UI change only, never a data change.
`vercel.json` pins `framework: nextjs`; without it Vercel served `public/` and
every route 404'd.) Mark 2 stays frozen at jivo-mark2.vercel.app as the baseline.

**The forward plan, over HTTPS:** `…/plan/overview.json`, `…/plan/manifest.json`,
`…/plan/days/day-NN.json` (+ spine, storage, materials, loops, honesty, lines) —
the calibrated engine re-run on live state every cycle by `live/freeze_live.py`
→ `engine/august_sim.py` → `live/gen_live.py`. **Only day 1 is observed** is
still the rule — day 1 is now re-observed every 3 minutes.

**Rulings that shape the live plan (2026-09-03), all carried in honesty.assumed:**
- storage pile = the live PENDING+BOOKED backlog × Oil share, never the 14-day
  bills window (C-0076: "not DISPATCHED" ≠ "still in godown").
- bulk oil = EXIM tank if one exists, else drums in BH-LO/BH-CRUDE/BH-EX/BH-GJ —
  never both (BH-LO is SAP's lagging book of the same oil).
- packaging from all allow-listed rooms incl. **BH-NM / GP-NM — OPEN QUESTION
  for Daman**: GODOWNS.md both allows them and calls them "non-moving, not
  available"; 41 BOM codes / 655,666 pcs (PM0000075 tape) have their only stock
  there. If "non-moving" means unusable, the plan changes materially.
- open bulk POs are blanket contracts: the undrawn balance is booked as arriving
  at lead time and is the loosest number in the freeze.
- a fresh clone's freeze REFUSES (rc=2) until the hourly stock set has run once —
  `rm live/state/.cadence.json`, then one `loop.sh`. Correct, not a bug.
- phone numbers are masked at the publisher door (`live/adapters/_mask.py`);
  the site never renders driver fields at all.

**The live state, over HTTPS, no login:**
`https://mark3-2ff07f84.srv1685505.hstgr.cloud/state.json` (and `/healthz`).
`collected_at` is when the loop ran; each source carries its own `fetched_at`,
`server_at`, `ok`, `error`. A source with `ok:false` keeps its last-good file
beside it — read `last_good_at`, never treat a failed source as zero.

**What is live and what is not, inside state.json** — say it on any page:
tank levels are a **manual daily dip reading**; ecom targets are **carried from
July**; the invoice→gate lag note is **static** (measured once, 2026-09-03);
GRPO posting counts and the QC scoreboard are **all-time**; the 827,000 L
ceiling is still **ASSUMED**. The MES sees ~⅔ of the plant; goods receipts see
the rest. Dispatch litres are **three companies** — Oil is the split, never the
merged headline (3 Sep: 47,182 L "dispatched" was 89% Beverages).

**A cloud/iPad session can read all of this** — the publisher is plain HTTPS.
It still cannot run the loop, reach the source systems, or deploy Vercel.

---

## THE ONE RULE THAT DEFINED MARK 2 (superseded in Mark 3)

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

## What a cloud/iPad session can and cannot do

**SAP is reachable from the cloud since 2026-09-03 — if the environment allows
it.** The sandbox cannot SSH (no client, port 22 refused) and speaks HTTPS only
to hostnames on its environment's allowlist. So the Service Layer is published
on the VPS as `https://sl-14fce609.srv1685505.hstgr.cloud`, and the claude.ai
environment must (a) allow `*.srv1685505.hstgr.cloud` under **Network access →
Custom** and (b) set `SAPB1_HOST=sl-14fce609.srv1685505.hstgr.cloud` and
`SAPB1_PORT=443` as environment variables. Then `sap-b1/cli/sapb1.linux` works
exactly as in the office. Full runbook, the setting steps and a paste-in
verification prompt: `connections/CLOUD-SESSION-ACCESS.md`.

If `curl https://sl-14fce609.srv1685505.hstgr.cloud/b1s/v1/` answers
`CONNECT tunnel failed, response 403`, the setting is missing — say exactly that
and point at the runbook. **No prompt inside the session can change it.**

Say these plainly rather than failing quietly:

- **HANA raw SQL and Postgres** are not HTTP, so they never pass the proxy. That
  is why **re-freezing from live SAP** (`engine/freeze_sep.py`, HANA CLI) stays a
  laptop/VPS job — the frozen inputs in `sim/` are what you have. Reads of ecom,
  OMS, factory, EXIM and Postgres go through the MCP gateway on the same host
  (see the runbook).
- **Reach Vercel**, or view `jivo-mark2.vercel.app` — not on the allowlist
  (untested even with it). Verify against the local build and page source.

Everything else — re-running the simulator, regenerating the site data, editing
pages, fixing bugs — works completely.
