# Phase 4 — `live/freeze_live.py`: the engine on live state

**Decision (Fable, 2026-09-03):** the calibrated simulator (`engine/august_sim.py`,
0.16% on August) is **not modified**. It reads one inputs JSON. Phase 4 writes
that JSON from `live/state/state.json` every cycle — `sim/live-inputs.json` —
and the engine runs on it unchanged (`SIM_INPUTS=sim/live-inputs.json
SIM_TAG=-live`). "Live" = a fresh opening position every 3 minutes, a horizon
of *now → month-end*, and demand/arrivals that come from the live systems
instead of a 31-August photo.

RULE 0 in `../CLAUDE.md` applies: nothing in this file is sourced from SAP.

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
3. **FORECAST** (the monthly plan, net of 1+2 by FG code for the rest of the
   month): weekly buckets where the plan has them, else spread evenly across
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
From `factory_production.line_configs` → `{line: {pack: pieces_per_hour}}`, but
**rated speed is wrong in both directions** (Tin Head 15 L measured 3.3× its
rating; Clear Pack 5 L at 17%). Use the measured August pieces/hr table in
`findings/` / `reference/PLAN-AND-LINES.md` where it exists; fall back to rated
× `rules.efficiency`. Tin Head and Manual have **no config rows** — keep Mark
2's `Tin Head: {TIN: 215}` (observed) rather than concluding they fill nothing.
Emit `lines_basis {line: {pack: "measured|rated×eff|carried"}}`.

### rules
Carry Mark 2's; override `invoice_truck_lag_days` from the measured median;
`storage_ceiling_l` = 827,000 — **Daman's declared limit** (STORAGE-CAPACITY.md,
reaffirmed 2026-09-04: "no guess now"; Q2 closed). Never badge it as assumed.

### provenance + honesty (write them, the site renders them)
`provenance.{opening_fg, opening_pm, opening_oil, standing, orders, inbound,
lines}` = source + `fetched_at` + `server_at` + `"live" | "last-good <ts>" |
"carried"`. `honesty.assumed[]` lists every mapping/fallback used **this cycle**
(oil-name map entries actually exercised, lead-day fallbacks actually applied).

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
is neither live nor last-good) → `engine/august_sim.py` with
`SIM_INPUTS=sim/live-inputs.json SIM_TAG=-live SIM_HOURS=12 SIM_SUNDAYS_OFF=1`
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
