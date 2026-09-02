# TASK — Build the JIVO Oil SEPTEMBER 2026 production plan, and a new site for it

You are working in `/Users/damanpreetsingh/jivo-cli/jolly`. Read `CLAUDE.md` at the repo
root first. Everything below was paid for in mistakes — treat it as fact, not suggestion.

## What you are building

A **forward production plan for September 2026** — what to make, on which line, in what
order, every day — plus **a NEW site** (do not modify `jolly/site`, that is August's).
September has not happened, so this is a real plan, not a backtest.

August was the proving run. Standing on 1 August with no later data, the planner produced
**2,122,639 L against the plant's actual 2,119,237 L — within 0.2%.** The model is
calibrated. Now use it forward.

---

## THE RULE (Daman, and he has repeated it)

> **Only day 1 is observed. Every later day is COMPUTED from the day before plus what the
> algorithm decided.** You do not look up what happened on 2 September. The one thing that
> legitimately arrives each day is that day's purchase orders — news landing, not hindsight.

Opening stock = **SAP as at 31 August** (the eve of the month). That is already frozen in
`sim/sep-inputs.json` — verify it, do not re-derive from scratch.

---

## THE LOOP HE WANTS TO SEE

> *"We need to make sunflower oil but we do not have the cap, so we order the cap. That
> takes days, so we do something else for 7 days. Then the cap comes and we run it."*

Block → order → run something else → it lands → unblock → run it. Make that **visible**,
not implied. The August engine already emits `ORDERED_BLOCKER` / `UNBLOCKED` events.

## AND GAUTAM GETS A DAILY BUILD LIST

> *"Gautam is responsible for what to run on what machine. Teach him: 'Gautam, run this on
> this machine.' Every day, and it changes as POs land."*

Per machine, per day, in sequence, with the oil and the changeover called out. Real number
**+91 86073 32900**. Everyone else is exception-driven — routine ordering is NOT a message.

---

## WHAT IS ALREADY BUILT (reuse it, do not rewrite)

```
engine/freeze_sep.py    the September opening — RUN THIS FIRST, writes sim/sep-inputs.json
engine/august_sim.py    the simulator. Parameterised:
                          SIM_INPUTS=sim/sep-inputs.json SIM_TAG=-sep \
                          SIM_HOURS=12 SIM_SUNDAYS_OFF=1 python3 engine/august_sim.py
engine/messages.py      events -> WhatsApp threads (point it at the -sep files)
engine/plan_units.py    pack-size parsing. pack_litres() is the ONLY way to get litres
engine/plan_explode.py  BOM explosion with the yield guard
engine/sep_gap.py       the zero-cover gap list with order-by dates
reference/*.md          EVERY ruling Daman has given. Read all of them before coding.
out/plan-sep-*.csv      the September plan, already resolved and exploded
```

**Status when handed over:** `sim/sep-inputs.json` is built and sane (84 SKUs, 4,323,300 L,
FG 638,321 L, oil 690,768 L, packaging 11,210,240 pcs, backlog 1,403,999 pcs = ₹46.85 Cr,
**8 components at ZERO**). The simulator had just been pointed at it and **had not yet been
validated for September** — the first run produced nonsense (nothing shipped, godown pinned
at 100%, production died on day 2) because demand was undated. A dated demand stream was
then built. **Your first job is to run it and check it is sane before trusting anything.**

---

## THE TRAPS — every one of these has already burned this project

**Item codes**
- `reference/oil-synonyms.csv` — **MERGE SYNONYMS BEFORE COMPUTING ANY SHORTAGE.**
  groundnut=peanut, canola=cold-press-rapeseed, crude-rapeseed-new=domestic,
  olive=olive-dark-colour. Unmerged they invented a **522,373 L phantom groundnut shortage
  AND 357,635 L of phantom stranded peanut** — the same oil counted as both, and it survived
  three adversarial verifiers because both numbers looked credible.
  **`RM0000013` pomace is NOT `RM0000012` extra light. Do not merge those.**

**Units — correction C-0050**
- Oil is 910 g/L. Sale-tonne = 1,000 L. Purchase-tonne = 1,000 kg = 1,098.9 L.
- Godown capacity quoted in "tonnes" means **LITRES**.
- `POR1."OpenQty"` is in the PURCHASE unit. Use **`OpenInvQty`**. Summing OpenQty once hid
  **1,107,113 L** of inbound oil.
- Never add litres to kilograms. Never add PCS to MTR.

**Godowns**
- COUNT: `BH-GJ` (imports land there, crude goes to job work, cold press comes back).
- EXCLUDE: `BH-OT` (Param's, not ours), `BH-PP` (SAP-inactive), `BH-PC` (issued to floor),
  `BH-WST` (wastage).
- **Apply the allow-list to BOTH stock and inbound.** Applying it to one side cut a headline
  from 17.7% to 7.7% and refuted a whole workflow.

**Storage — correction C-0054**
- SAP removes stock at the **invoice**; the truck leaves later. Physical occupancy =
  book on hand + **invoiced-but-not-yet-gated-out**.
- Space is released by `dispatched_at`, and there are **TWO exit doors**:
  `/gate-core/sales-dispatch/` (customers) and `/warehouse/bst/` (Mart transfers, needs a
  `Company-Code: JIVO_OIL` header). Miss the second and Mart's pallets look like they never left.
- FG for SKUs **outside** the plan still occupies the godown (~57,000 L in September).
- The ceiling (827,000 L working / 923,000 peak) is **Daman's spreadsheet, not a measured
  capacity.** It is the least-verified number in the model. See open question Q2.

**Purchase orders**
- Only **LIVE** POs count. A naive query returns **141,034,848 L** of phantom oil from three
  POs keyed ×1000, plus 22.4M units on paper older than 90 days that delivered **0.0%**.
- Where a PO has no ship date, land it at order-date + measured lead (oil 11 d, packaging 6 d).
  Overdue lines do not all arrive on the 1st — spread them across week one and **declare it**.

**Demand — pick the right system**
- Use **SAP `ORDR`/`RDR1`**. The factory app has no Oil order book of its own (its Order
  Processing is a dead OMS mirror, unjoinable, last sync 17 Aug). OMS's own book is 99.9%
  junk by value — two ₹464 Cr orders with **zero line items**.
- **A FORECAST IS NOT AN ORDER.** The demand file once mixed three sources and the plant's
  own forecast (3,126,479 pcs, all dated 1 Aug) got loaded as real orders. Tag forecast
  demand `channel=FORECAST` and keep it separable.

**Lines** (`reference/PLAN-AND-LINES.md`)
- Any oil runs on any line. Only container size binds.
- **Clear Pack 5 L is 1,000/hr, not the rated 3,000** (observed median 831, best 1,068).
- **Tin Head 215/hr** — August's peak. There is no config for it in the app at all.
- **Flush = 400 L of the next oil per changeover.** The oil is REUSED and lasts a month, so
  it costs TIME, not material. Time = 400 L ÷ that line's litres-per-hour.
- **Line clearance = 51.3 min median**, on top of the flush.
- Lines run at **~50% of rated** when running. Plan at 50%, not at rated.
- 12 h × 26 days is the FLOOR, 24 h × 31 d the ceiling, and the choice is ours. **For August,
  22 h × 31 d bought +₹6.96 Cr but used only 9% of the extra hours** — the lines were idle
  for want of material, not time. Check whether September is the same before recommending it.

**Electricity** — ₹26,04,139 last month. Booked to `2110004 SUNDRY CREDITOR SERVICE`, a
balance-sheet account, so it is invisible to any account-name search. Search the VENDOR side.
Its per-litre cost is set by utilisation, which makes it an argument FOR longer shifts.

**Wellness is the parent; Mart buys from it.** Oil→Mart is a real sale but internal to the
group, and it is ~79% of the order book. Realise from the Control Panel INCLUDES it at
transfer price — so ranking by realise partly ranks an internal accounting choice.

---

## DATA SOURCES — which system for what

| Need | Source | How |
|---|---|---|
| Stock, BOMs, orders, invoices | **SAP HANA** | `./hana-sql/hana-sql -env connections/hana-office-bridge.env "<SQL>"` |
| The monthly plan | **EXIM** `GET /planning/latest/` | per-SKU, FG codes, **weekly buckets**. No Excel. |
| Realise ₹/L (the objective) | **Control Panel** | `control-panel/cli/jivo/jivo sales data --start-date … --end-date …` — **no auth needed** |
| Lines, gate, dispatch, production, storage | **factory app** | `factory-cli/jivo-factory-pp-cli` — ji.jivo.in = factory.jivo.in, one system |
| Bulk oil in tanks | **EXIM** | route via `ssh vps` — the Mac's TLS to eximbe is flaky |

**If HANA refuses:** the tunnel is probably down. `nohup ssh -N -L 13015:127.0.0.1:43015 -L 15000:127.0.0.1:45000 vps &`
The VPS-side port 43015 is parked by the SAP box itself and is usually alive.

**The factory app is NOT independent of SAP** — its own metadata says on-hand is
*"reconstructed from SAP OINM"*. Agreement between them is an implementation check, not two
measurements. Also: its `stock-as-of` returns **end-of-day**; a SAP rewind returns
**start-of-day**. Mixing them double-counts a day.

**Never call these GETs — they have side effects:** `/marketplace/settings/`,
`/marketplace/orders/resolve`, `/gate-core/sales-dispatch/lock`, `/blowing/runs/{id}/cost`,
`/barcode/dispatch/sessions/from-bill`.

---

## BUILD A NEW SITE

**Do not touch `jolly/site`** — that is the August replay and it is deployed. Make
`jolly/site-sep` (Next.js app router, TypeScript, Tailwind). You may copy August's shape:
`lib/types.ts`, `lib/data.ts`, `components/Card.tsx` are worth reusing.

Pages: **Overview · Day 1–30 (the spine) · Lines · Storage · Materials · WhatsApp · Floor 3D**
Plus, for a forward month, two that August did not need:
- **Order by** — every component, its cover, its lead time, and **the last day it can be
  ordered**. This is the page that earns money. August's equivalent found **₹8.48 Cr** blocked
  by 38 items at zero, and September already has **8 at zero on day one**.
- **Build list** — Gautam's daily plan, per machine, printable.

Deploy: `npx -y vercel deploy --prod --yes`, then
`python3 ~/.claude/scripts/vercel-public.py <project>` — **new Vercel projects are SSO-gated
by default and that step is mandatory.** Verify logged-out `curl -sI` returns 200, and give
the SHORT `https://<project>.vercel.app` URL, never the long hashed one.

⚠️ **The site renders real employees' personal WhatsApp numbers.** August's is public with
Daman's explicit approval. **Ask him before publishing September's.**

---

## HOW TO NOT BE WRONG

**Six adversarial verification passes ran on this project. Every computed figure they
re-derived matched. Every single refutation landed on PROSE** — a hardcoded "90%" in a
heading when the data said 95%, a mechanism over-claimed as explaining a whole gap it
explained 70% of, a forecast narrated as a commitment. **Verify the sentences, not just the
numbers.** Never type a number into a page; compute it.

**Assert a conservation law on every run.** Oil consumed must reconcile to litres produced
within a stated tolerance. That check is the only reason a 2.29× double-count was caught —
the output looked perfect: right names, sorted, plausible.

**Sanity-check every rate against a physical bound.** A previous session shipped ₹123/L for a
500 ml fill — 42× too high and physically impossible — behind a footnote.

**Separate measured from assumed on the page itself**, and mark simulated content at the DATA
layer (a field like `assumed: true`), never only in view copy. A previous build showed 20
invented replies as real messages from real people with their real numbers.

**Say "I did not check" when you did not.** Daman will catch a confident wrong number, and he
would rather have a gap than a guess.

---

## OPEN QUESTIONS

`out/QUESTIONS-FOR-DAMAN.csv` — 22, with a best guess on each. Live on August's site at
`/questions`. **The three that change the model: Q2** (is the basement 628 or 739 pallet
positions — decides the ceiling), **Q4** (do lines stop at 16:20 or run to ~19:00 — decides
what the 50% efficiency means), **Q13** (should the planner refuse or only warn when a run's
BOM exceeds packaging on hand — the engine currently refuses).

**Do not re-ask anything you can answer from data.** Twelve questions were dropped that way.

---

## FIRST FIVE MOVES

1. Read `reference/*.md` — all of it. Then `CLAUDE.md`.
2. Verify HANA, EXIM, factory-cli and the Control Panel all answer.
3. Re-run `engine/freeze_sep.py`, then the simulator, and **check the output is sane**
   (does anything ship? does the godown drain? is utilisation plausible?). It was not
   validated at handover.
4. Run the conservation check and the gap list before building any UI.
5. Then build the site.

**Report what you find, including where the handover was wrong. It will be wrong somewhere.**
