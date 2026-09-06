# Phase 4 — `live/freeze_live.py`: the engine on live state

**Decision (Fable, 2026-09-03):** the calibrated simulator (`engine/august_sim.py`,
0.27% on August — the figure is pinned in `reference/august-calibration.json`, see
`../CLAUDE.md`) is **not modified**. It reads one inputs JSON. Phase 4 writes
that JSON from `live/state/state.json` every cycle — `sim/live-inputs.json` —
and the engine runs on it unchanged (`SIM_INPUTS=sim/live-inputs.json
SIM_TAG=-live`). "Live" = a fresh opening position every 3 minutes, a horizon
of *now → month-end*, and demand/arrivals that come from the live systems
instead of a 31-August photo.

RULE 0 in `../CLAUDE.md` applies: nothing in this file is sourced from SAP —
with the one named exception below, which is a FILE a daily cron wrote, never a
call made from here.

---

## MARK 4 — what the freeze now writes on top of all of this (2026-09-06)

**The switch is the inputs, not the checkout.** `freeze_live.py` embeds
`reference/mark4-rulebook.json` whole as `rulebook`, and
`engine/august_sim.py` runs rulebook mode **iff `S["rulebook"]` is present**.
The August calibration and the `-sep` path carry no rulebook, so every line of
the legacy engine executes exactly as before. **A missing or unreadable
rulebook stops the freeze (rc=2)** — a Mark 3 plan wearing a Mark 4 date puts
15-litre tins back on Clear Pack and nothing in the output would say so.

| new key | what it is |
|---|---|
| `rulebook` | the whole rulebook, `sku_pack` merged with anything this file had to class itself |
| `rulebook_applied` | `{A01, A09, A10, A17, A18, R16, R21} -> {in_effect, note}` — which rulings this run actually put into effect, and what fell back. The engine adds its own flags in `sim/summary-live.json`; gen merges the two |
| `lines` | keyed by the **rulebook's** slots: Tin Head carries `15L`/`3L`/`5L`, and no line carries a `15L` key it was not given (AC02). A slot with no planning speed is SKIPPED, not guessed |
| `lines_basis` / `lines_basis_kind` | `"planning"` for every slot, plus the rulebook's own word for how it was arrived at (`capped`/`rated`/`typical`/`carried`/`derived`) |
| `lines_speeds` | everything behind each speed: rating, August median/best/runs, the planning figure, the prose basis, the structured `planning_rule`, and the slot → bottle-family → preference map |
| `lines_multi` | containers/hour for a combo-set SKU, on the lines with a record of filling one (B19). The engine reads this instead of `lines` when `fills_per_piece > 1` |
| `lines_carried_mark3` / `lines_app_rated_now` | what Mark 3 fed in, and what ji.jivo.in lists today. Published, compared, **never fed in** |
| `demand_baseline` | the whole provenance of the expected stream (below) |
| `lag` | median / p90 / max / mean days, rows, window, `static` |
| `dispatch_book` | the open book, the Oil pile, and days of pendency at the recent gate pace |
| `money` | target and floor from the rulebook, month-to-date and today's rupees, split by which rate priced them |
| `plan_code_aliases` / `opening.fg_alias_applied` | A10, the 16 → 20 piece carton change |

**`rules` changes, and they matter:**

- `shift_hours` **10** and `sundays_off` from the rulebook (R02/R04), plus
  `sessions_per_day_max`, `night_lines_max`.
- `efficiency` **1.0**, with `efficiency_basis` saying why. The speeds in
  `lines` are PLANNING speeds — 80% of the rating, capped at the best sustained
  August hour — so the 0.5 is already inside them. **The engine refuses a
  rulebook run at any other efficiency**: derating twice plans the plant at half
  (2.01 M L instead of 3.19 M) and every check still passes.
- `line_clearance_min` and `flush_litres` from `rulebook.changeover`.
- `invoice_truck_lag_days` + `invoice_truck_lag_p90_days` + a basis string.

**`live/loop.sh` no longer forces 12 h.** `SIM_HOURS` / `SIM_SUNDAYS_OFF` are
passed through only when somebody sets them. The engine takes its hours from
`rules.shift_hours`, and it REFUSES an override longer than the rulebook's
session — so the old `SIM_HOURS` default would not merely inflate the published
plan by 11%, it would stop the chain dead every cycle.

### Expected orders — the demand baseline (R17/R18/A09/A17/A18)

`live/state/demand_baseline.json`, written **daily** by
`live/demand_baseline_sap.py` (the one allowed SAP read;
`../reference/DEMAND-BASELINE-SOURCE.md`). The freeze **only reads the file** —
it never makes the call, and nothing in the 3-minute loop touches SAP.

Per SKU: monthly litres × its week-of-month share ÷ that bucket's calendar days
this month, summed over the days still to come, **netted by the real OMS book**
(floored at zero) and spread back proportionally. **e-com is never netted** —
its POs are their own stream and the baseline excluded e-commerce billing to
begin with. A SKU that sold in every month of the window uses its **own** week
shape; anything else takes the **pooled** one. Rows are triple-tagged exactly as
before and carry `basis: "gt-mt-3m-billing"`.

Two more things come out of the same file:

- **R19** — `plan[code].trailing_l_per_month` on every row the baseline knows.
  Without it the engine ranks the expected-only tier by the order the rows
  happen to sit in; `summary-live.json`'s `rulebook.trailing_source` says which
  it used.
- **A18** — SKUs the plant sells that the plan sheet never had are appended as
  `pieces: 0, expected_only: true` rows, but **only** when SAP's BOM names them,
  that BOM names an oil, and `engine/pack_class.py` can class the pack (drums
  are out, R14). Everything else is published by name with its reason in
  `demand_baseline.nonplan.skipped` — demand the plan cannot place is still
  demand. *Today all 61 land in `skipped` with "no BOM": `sim/sep-inputs.json`
  carries recipes for the 84 plan codes only.*

Missing / stale / wrong-month → the plan sheet's weekly buckets, said in
`honesty.assumed` and on the assumptions page, with `used_for_forecast: false`.

### The invoice-to-gate lag (R21)

`live/state/dispatch_lag.json`, written **daily** by `live/dispatch_lag.py` off
`gate-core sales-dispatch` — `gate_out_date − sap_doc_date` per DISPATCHED row
over the last 30 days. Fresh → `rules.invoice_truck_lag_days` is that median and
`lag.static` is `false`. Missing or stale → `factory_dispatch.LAG_NOTE`, the
single by-hand measurement of 2026-09-03, `lag.static: true`, and a sentence
naming the file. Both files' freshness rule is the same helper (`daily_file()`,
8 days); see `README.md`.

### honesty in rulebook mode — the sentence carries its own mode

The Mark 3 block said "the engine then derates everything by 50% again" and "the
engine applies `rules.efficiency` (0.5) on top of it". Both are **false** here,
and both are gone from this file.

How the engine drops what does not belong to its mode is a **positive contract,
not a keyword blocklist** (fixed 2026-09-06). `F.assume(text, mode=...)` records
`"legacy" | "rulebook" | "both"` — **`"both"` is the default**, so a sentence has
to be deliberately tagged before anything can delete it — and the freeze publishes
the map as `honesty.assumed_modes`. `engine/august_sim.py` drops only what is
tagged for the mode it is NOT running, names it in `rulebook.honesty_dropped`, and
never republishes the map itself.

What it replaced: the engine matched each sentence against `("derate",
"rules.efficiency", "of rated", "50% again")`. Those are words a TRUE sentence
about planning speeds cannot avoid, so "every line is planned at 80% **of rated**
capacity, capped by its best August hour (R05/A01)" and "the plan never
**derates** a planning speed a second time (A01)" were silently deleted when this
file wrote them, and the engine then printed a warning blaming this file for the
text it had just eaten.

This freeze only ever writes rulebook inputs (a missing rulebook is a refusal, not
a fallback), so **nothing it writes may be tagged `legacy`** —
`live/_freeze_mark4_test.py` asserts that, that every sentence carries a mode, and
separately that no sentence claims the 50% derate, which is the thing the old
filter was really there to catch.

---

## What the engine reads (from `engine/august_sim.py`, verified)

| Key | Engine use | Shape |
|---|---|---|
| `meta.horizon` | `[first_day, last_day]` of the run | `["YYYY-MM-DD","YYYY-MM-DD"]` |
| `opening.stock` | packaging + raw-material on hand at open | `{code: qty}` — PM pieces, RM **litres** |
| `opening.fg` | finished goods on hand | `{FG code: pieces}` |
| `opening.standing_l` | invoiced-but-not-gone pile occupying the godown at open | litres |
| `orders` | the dated demand stream (`orders_by_day`), filtered to plan codes | rows `{docnum,date,due,customer,code,pieces,value,channel,_src}` |
| `backlog` | seeds `po_left` for docs NOT in `orders` | same row shape |
| `inbound_prebooked` | material landing on a date | `{date: {code: qty}}` |
| `lines` | rate per line per pack | `{line: {pack: pieces_per_hour}}` |
| `rules` | shift, efficiency, ceiling, lead days, lag | as in `sim/sep-inputs.json` |
| `plan`, `bom`, `blends`, `items`, `realise` | static for the month | carry from `sim/sep-inputs.json` |

## The mapping — every field, its live source, its unit, its fallback

### meta
- `as_of` = `state.collected_at`; `frozen` = same; `horizon` = `[today, last day of month]`;
  `rolling: true`; `replanned_days` = days left incl. today; `month` unchanged.
- `pieces_made_mtd` = **factory_production** month-to-date pieces (sum of
  `reports-daily-production` per day, or the movement report's month window).
  This is what makes "plan left to make" net off what the plant has actually done.
  Mark 2 had this feature (`SIM_ASOF`) and never switched it on.

### opening.fg — live ✅ (already in state)
`factory_production.fg_stock["BH-PF"]` + `["BH-BT"]`, summed per FG code, pieces.
Both rooms are the FG godown (GODOWNS.md). If either warehouse is in
`unavailable`, **do not emit a partial total** — carry the last-good file and set
`provenance.opening_fg = "last-good <ts>"`.

### opening.stock — packaging: NEEDS ONE ADAPTER EXTENSION
The engine wants PM pieces per code. `factory_production` hourly currently pulls
only BH-PF/BH-BT. Extend its hourly set with `dashboards stock --warehouse BH-BS`
and `--warehouse BH-PM` (**one warehouse per call** — a CSV silently sums), emit
`pm_stock {BH-BS:{code:pcs}, BH-PM:{code:pcs}}`. `opening.stock[PM…]` = the sum.
`on_hand` is trustworthy; `stock_status`/`min_stock` are not — never read them.

### opening.stock — raw oil: EXIM tanks, litres, mapped by NAME
`exim.tanks.by_oil[].litres` is the physical bulk-oil position (manual daily dip
reading — label it). EXIM and the factory share **no item code**, so map each
EXIM oil name → RM code with `reference/oil-synonyms.csv` + a small explicit
table in `freeze_live.py` (write it down; every mapping is a declared
assumption). **`RM0000013` pomace is NOT `RM0000012` extra light — never
merge.** Unmapped EXIM litres go to `opening.oil_unmapped_l` and a warning,
never silently dropped and never guessed into a code.
Also carry `opening.oil_l` (all tank litres) — it is a DIFFERENT series from the
day files' BOM-relevant `oil_on_hand_l`; never chart them together.

### opening.standing_l — THE BIG CORRECTION, live ✅
= `factory_dispatch.invoiced_not_dispatched.by_company["JIVO_OIL"].litres`
(fall back to the Oil share of the headline if the split is empty on a cheap
cycle — and say so). Mark 2 set this to **0** and called it optimistic; the
real Oil pile today is in the tens of thousands of litres. Goods count as
storage pressure **until physically dispatched** (Daman's rule) — this is that.
Keep `rules.invoice_truck_lag_days` for the drain, but set it from
`factory_dispatch.lag_note.median_days` (measured 2 d) not the old guess.

### orders — real, dated demand
Three streams, each row tagged in `channel` and `_src`, kept **visually
distinct downstream**:
1. **OMS** (`oms.orders_recent`): Oil orders with status not in
   {Completed, Rejected, Billing Rejected}; one row per line;
   `date` = order created date, `due` = `delivery_date`, `pieces` = `qty`
   (**pieces, C-0001**), `value` = line value, `channel` = main group (GT/MT/…),
   `_src = "OMS"`. Exclude `price_outliers` lines from `value` (keep pieces).
2. **ecom** (`ecom.dated_demand` by FG × required-by date): `channel = "ECOM"`,
   `_src = "ECOM-PO"`, `pieces` from litres ÷ `litres_per_piece` (from `plan`
   rows), `docnum = "EC-<platform>-<date>"`. **This replaces Mark 2's even
   ecom spread.** Amazon August-dated PENDING is stale backlog: include only
   rows with `po_month` = current month, and note the excluded litres.
3. **FORECAST** — **SUPERSEDED IN MARK 4** by the demand baseline above; what follows is
   the fallback the freeze still uses when that file is missing, stale or from the wrong
   month. The monthly plan, net of 1+2 by FG code for the rest of the
   month: weekly buckets where the plan has them, else spread evenly across
   the remaining working days. Triple-tag exactly as Mark 2 did
   (`channel=FORECAST`, `docnum FCST-*`, customer `(forecast — not yet ordered)`).
   Never let forecast exceed plan-minus-real per code (floor at 0).

### backlog
OMS Oil orders **already older than today** and not completed — the overdue
pile the day-1 chart showed. Same row shape; docs already present in `orders`
are skipped by the engine, so include them in `orders` with their original
date and leave `backlog` for docs the cursor never saw (rare).

### inbound_prebooked — arrivals that are real, not lead-time maths
- `factory_inbound.in_qc` lines: land on `today+1` (packaging clears QC in ~1 h)
  or `today+2` for bulk oil (tankers sit in QC for days — measured). Use
  `received_qty` gated on `qc_status == ACCEPTED`; **never `accepted_qty`**.
- `exim.inbound.on_the_way` rows: land on their `eta`, litres → RM code via the
  same name map.
- `exim.open_bulk_pos` (status not COMPLETED): `contract_qty − load_qty` remaining,
  landing at `po_date + rules.lead_days.oil` if no ETA — labelled `_src="PO-LEAD"`.
- Packaging on order: the one confirmed gap. Use `factory_inbound.month_pending`
  PO lines (ordered − received) at `po_date + rules.lead_days.packaging`, then
  **the day-1 rule Mark 2 used**: lines already overdue are spread over the
  next 5 working days, not dumped on today.
Every entry carries provenance in a parallel `inbound_provenance {date:{code:src}}`.

### lines
**SUPERSEDED IN MARK 4** — see the rulebook table above; `lines` now comes from
`rulebook.lines[..].speeds[..].planning` and the live configs are a WATCH only. What
follows is the Mark 3 rule, still what the `-sep` path uses.

From `factory_production.line_configs` → `{line: {pack: pieces_per_hour}}`, but
**rated speed is wrong in both directions** (Tin Head 15 L measured 3.3× its
rating; Clear Pack 5 L at 17%). Use the measured August pieces/hr table in
`findings/` / `reference/PLAN-AND-LINES.md` where it exists; fall back to rated
× `rules.efficiency`. Tin Head and Manual have **no config rows** — keep Mark
2's `Tin Head: {TIN: 215}` (observed) rather than concluding they fill nothing.
Emit `lines_basis {line: {pack: "measured|rated×eff|carried"}}`.

### rules
**SUPERSEDED IN MARK 4** for `shift_hours`, `efficiency`, `line_clearance_min`,
`flush_litres` and the lag — all of those now come from the rulebook and the daily lag
file. The ceiling paragraph below is unchanged and still correct.

Carry Mark 2's; override `invoice_truck_lag_days` from the measured median;
`storage_ceiling_l` = 827,000 — **Daman's declared limit** (STORAGE-CAPACITY.md,
reaffirmed 2026-09-04: "no guess now"; Q2 closed). Never badge it as assumed.

### provenance + honesty (write them, the site renders them)
`provenance.{opening_fg, opening_pm, opening_oil, standing, orders, inbound,
lines}` = source + `fetched_at` + `server_at` + `"live" | "last-good <ts>" |
"carried"`. `honesty.assumed[]` lists every mapping/fallback used **this cycle**
(oil-name map entries actually exercised, lead-day fallbacks actually applied), and
`honesty.assumed_modes` says which plan mode each of those sentences is true in — see
"honesty in rulebook mode" above.

## Rulings applied on top of this design (2026-09-03, after the first live cycles)

**1. EXIM is the bulk-oil truth. `opening.stock[RM]` is the TANK dip when EXIM has a
tank for that code, ELSE the drummed litres from the raw-material rooms. NEVER both.**
The freeze briefly counted the tank AND the raw-material store as two physical stocks.
It is one stock counted twice: `reference/GODOWNS.md` says bulk oil is not in SAP's
godowns at all, EXIM's own sap-sync inventory shows BH-LO groundnut at exactly the
store's figure for the same oil (275,110 L), and the two added together came to 1.55 M L
against a measured tank capacity of 1,351,500 L. The store's figure is still published,
per code, as `opening.oil_book_l` with `oil_book_l_note` — the LAGGING BOOK VIEW, for
information. `opening.oil_tank_l` and `opening.oil_drum_l` stay; drum now means the
tank-less oils only.

**2. Only the plan's own oils are converted out of the raw-material rooms.** The KG
branch used to divide rosemary leaf (26.65 KG) and walnut (11.5 KG) by 0.91 kg/L and
count them as bulk oil. Anything whose canonical code is not in the BOM oil set now goes
to `opening.rm_store_other` with its own qty and unit — counted nowhere, invented
nowhere — and that is also where the two rows that used to be dropped in silence land:
SF0000009 (3,249 finished 15 kg canola tins, ~48.7 t, published as tins and NEVER as
litres) and SC0000051 (vitamin AD2 premix). **Nothing in those rooms may vanish without
a name.**

**3. Room membership.** `GP-FG` is a PACKAGING room (GODOWNS.md allow-lists it for
oil+packaging as well as finished goods, and it holds 64,680 PM). `BH-GJ` is a
RAW-MATERIAL room (allow-listed by the same 2026-08-29 ruling, but what it holds is oil —
read as packaging, every litre was thrown away by the PM-code test). A room that has just
moved is **NOT YET READ** until the next hourly cycle: a warning and a declared floor,
never a refusal.

**4. The NON-MOVING rooms are COUNTED and BADGED — and it is an open question.**
GODOWNS.md allow-lists `BH-NM` and `GP-NM` in its table and calls them "not available" in
its Traps section, both Daman's, same page. They are counted (the plant is running on that
packaging, and Mark 2's calibrated August counted them) and the exposure is published:
`opening.packaging_in_non_moving_rooms_pcs` / `packaging_only_in_non_moving_codes`, plus a
`honesty.assumed` line naming the codes that would vanish if "non-moving" means unusable.
**Ask Daman.**

**5. Publish hygiene.** `gen_live.py` writes `live/state/plan/manifest.json` — the exact
list of files this cycle produced — and `loop.sh`'s publish step deletes any other
`*.json` in `plan/` and `plan/days/`, logging each one. No manifest, no sweep. A refused
`gen_live.py` run now exits through its own "N CHECK(S) FAILED — NOT WRITING" line
instead of a traceback, and leaves no `out/order-by-live.{json,csv}` behind: the gap list
is built to a temp name and moved into place only after every check has passed.

## Runtime
`live/loop.sh` step order per cycle: `collect.py` → `freeze_live.py` (writes
`sim/live-inputs.json`, refuses to write if any of opening.fg / standing / orders
is neither live nor last-good, or if the rulebook is unreadable) →
`engine/august_sim.py` with `SIM_INPUTS=sim/live-inputs.json SIM_TAG=-live`
(**no `SIM_HOURS`, no `SIM_SUNDAYS_OFF`** — the rulebook decides; set either one
and it is a scenario the gen gate refuses to publish)
→ `site-sep/scripts/gen-data.py` (its 55 cross-checks stay the gate) → copy
`site-sep/data/*.json` into `live/state/plan/` so the publisher serves them.
Budget: sim ≈ seconds, gen ≈ seconds; the whole chain must stay under the
175 s loop timeout — measure and log each step.

## Acceptance (the verifier's checklist)
1. `sim/live-inputs.json` validates against every key/shape in the table above.
2. Engine runs to completion on it; day-1 opening equals today's live numbers
   to the piece/litre (fg, standing, tanks) — print the reconciliation.
3. `orders` splits cleanly by `channel`; FORECAST never exceeds plan−real per code.
4. No SAP anywhere (`grep -rn sapb1|hana|sap-b1 live/freeze_live.py` = 0 hits).
5. Every assumption exercised this cycle appears in `honesty.assumed`.
6. A missing/failed adapter degrades to last-good with provenance saying so —
   never a silent zero opening.
