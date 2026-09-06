#!/usr/bin/env python3
"""freeze_live.py — the LIVE opening position, written in the shape the engine reads.

    python3 live/freeze_live.py            # from jolly/
    python3 -m live.freeze_live            # same thing
    live/loop.sh                           # what cron runs, right after collect.py

WHAT IT IS
==========
`engine/august_sim.py` is CALIBRATED (against the plant's real August; the measured
figure and the hashes it was measured against are pinned in
`reference/august-calibration.json`, rebuilt by `engine/calibrate_august.py`) and is
NEVER modified. It reads exactly one JSON. This script writes that JSON —
`sim/live-inputs.json` — from `live/state/state.json` every cycle, so the same
untouched engine runs on a plant position that is minutes old instead of a
31-August photograph.

"Live" means three things and only these three:
  * a fresh OPENING (stock, finished goods, the invoiced-not-trucked pile) each cycle
  * a HORIZON of today -> month-end, not 1 Sept -> 30 Sept
  * DEMAND and ARRIVALS out of OMS / ecom / EXIM / the factory app, not a freeze

Everything the month cannot change — `plan`, `bom`, `blends`, `items`, `realise`,
and the base `rules` — is CARRIED verbatim from `sim/sep-inputs.json`. Those are
BOM and master-data facts, not a live position, and re-deriving them every three
minutes would put the whole calibration at the mercy of one bad API page.

RULE 0 (../CLAUDE.md): NOTHING here touches SAP. No sapb1, no hana-sql, no
sap-b1/, no saphist. Every number below comes from `live/state/`, which comes from
the factory / OMS / ecom / EXIM CLIs. `live/state/demand_baseline.json` is a FILE a
daily cron wrote (live/demand_baseline_sap.py, the one allowed SAP read); this script
reads the file and never makes the call.

MARK 4 — THE RULEBOOK (2026-09-06)
==================================
This file embeds `reference/mark4-rulebook.json` whole as `rulebook`, and its PRESENCE
in the inputs is what switches engine/august_sim.py into rulebook mode. Without it the
engine is Mark 3 in every line, which is why a missing or unreadable rulebook REFUSES
here (rc=2) instead of quietly producing the old plan with today's date on it.

What that changes in this file, all of it detailed in PHASE4-FREEZE-LIVE.md:
  * `lines` is keyed by the RULEBOOK's slots and holds its PLANNING speeds. The Tin Head
    carries 15L/3L/5L and no other line carries a 15 L key at all (AC02) — Mark 3 keyed
    it "TIN" and let the engine derive a 15 L rate as the 5 L head / 3, which is how a
    15-litre tin came to be planned on Clear Pack.
  * `rules.efficiency` is 1.0 (A01). A planning speed is ALREADY 80% of the rating and
    capped at the best sustained August hour; the old 0.5 on top of it plans the plant
    at half. The engine refuses a rulebook run at any other efficiency.
  * `rules.shift_hours` is the rulebook's 10, not the loop's 12 (R02).
  * expected orders come from three months of outside billing, week-of-month shaped
    (R17/R18) — see THE DAILY FILES below — and every plan row the baseline knows
    carries `trailing_l_per_month`, which is how R19 ranks the expected-only tier.
  * `rulebook_applied` records, per ruling, whether this run put it into effect.

THE DAILY FILES — read here, written by cron, never called from here
====================================================================
  live/state/demand_baseline.json   live/demand_baseline_sap.py   (SAP billing, R17)
  live/state/dispatch_lag.json      live/dispatch_lag.py          (ji.jivo.in gate, R21)
Both are adapter-shaped and both go through one helper, `daily_file()`, with one rule:
ok, and no more than 8 days old, and (for the baseline) a window ending on the last day
of last month. Anything else is a declared fallback that is named in honesty.assumed —
the plan sheet's weekly buckets, and the static 3 Sep lag note. Never a refusal.

WHAT IT REFUSES TO DO
=====================
It exits NON-ZERO and writes nothing when any of these is neither live nor carried from
a last-good file. A silent zero in any of them is not a degraded answer, it is a WRONG
answer that looks fine:
  * fg = 0     -> the godown reads empty, the plan re-makes a month of stock
  * standing=0 -> the storage ceiling reads free when it is not
  * orders = 0 -> the engine's own assert fires anyway, but later and less clearly
  * PM = 0     -> every SKU blocks on packaging; refused unless AT LEAST ONE packaging
                  room answered (one room is a floor, no room is a fiction)
  * tanks = 0  -> every blend blocks and the plan re-orders oil the plant is standing
                  on; a total EXIM outage is refused for the same reason as PM
Every other field degrades to a declared fallback and says so in `honesty.assumed`.

THE STANDING PILE — WHY THE ENGINE IS FED THE SMALLER NUMBER
============================================================
factory_dispatch publishes two undispatched figures that do NOT reconcile (5.8x apart
on 2026-09-03) and the adapter says so itself:
  WIDE  invoiced_not_dispatched.by_company[JIVO_OIL] = every Oil BILL invoiced in the
        last 14 days whose dispatch plan never reached DISPATCHED. 1,260,504 L — 152%
        of the whole declared godown, so the engine opened with negative space and made
        ZERO on days 1 and 2.
  CHEAP invoiced_not_dispatched.litres = open dispatch plans, PENDING + BOOKED, no date
        bound, all three books. 284,549 L.
Daman proved on 2026-09-03 that the dock module records only about 45% of dispatches,
so "the plan never reached DISPATCHED" sweeps in bills that physically left the gate.
The wide figure is an upper bound on PAPERWORK, not a measurement of stock in the way.
The engine is therefore fed the cheap pile, apportioned to Oil by the share of the last
heavy company split (a ratio ages far better than a litre count). The wide figure is
published beside it as `standing_l_wide_14d` with its own provenance, never fed in, and
never added to the other.

WHERE EACH FIELD COMES FROM  (unit -> engine key)
=================================================
meta.horizon            [today, last day of the month]          <- state.collected_at
meta.rolling            true — this is a re-plan, not a freeze
meta.pieces_made_mtd    NOT AVAILABLE from state.json (see PIECES_MADE_MTD below)

opening.fg              PIECES per FG code
                        factory_production.fg_stock BH-PF + BH-BT, FG codes only.
                        Both rooms or neither: a half-read godown is not published.
opening.fg_other_l      LITRES of FG in those rooms that is NOT a plan code —
                        never made, never shipped, always in the way. pack_litres().
opening.stock[PM…]      PIECES per PM code
                        factory_production.pm_stock summed over EVERY packaging room on
                        GODOWNS.md's allow-list (PM_ROOMS: BH-BS, BH-PM, BH-NM, BH-SDL,
                        GP-NM, GP-PM, GP-FG), room by room. NOT in the FG ceiling.
                        BH-NM and GP-NM are NON-MOVING and are COUNTED — see
                        opening.packaging_in_non_moving_rooms_pcs and NON_MOVING_ROOMS.
opening.stock[RM…]      LITRES per RM code. THE RULING (2026-09-03): the EXIM TANK dip
                        if EXIM has a tank for that code (mapped NAME -> RM code by
                        OIL_NAME_TO_RM below; EXIM and SAP share NO item code), ELSE the
                        drummed litres out of the raw-material rooms (RM_ROOMS: BH-LO,
                        BH-CRUDE, BH-EX, BH-GJ), converted by the unit each ROW carries.
                        NEVER BOTH — EXIM is the bulk-oil truth.
opening.oil_l           LITRES, every tank — a DIFFERENT series from a day file's
                        `oil_on_hand_l` (which is BOM-relevant only). Never one line.
opening.oil_tank_l      LITRES from the tanks alone.
opening.oil_drum_l      LITRES from the raw-material store, for the TANK-LESS oils only.
opening.oil_book_l      {code: LITRES} — what SAP's own warehouses say the raw-material
                        rooms hold, for EVERY oil. INFORMATION ONLY where a tank exists:
                        it is the LAGGING BOOK VIEW of the same oil, not a second stock.
opening.oil_unmapped_l  LITRES in tanks whose name this file cannot map. Reported,
                        never guessed into a code, never silently dropped.
opening.rm_drums_unconverted  plan-oil rows held in PCS/NOS with no litre figure.
                        Reported and LEFT OUT of oil on hand — a drum count is not
                        litres and this file will not invent a drum size.
opening.rm_store_other  {code: {qty, uom, name, rooms}} — everything in those rooms that
                        is NOT an oil in this month's recipes: rosemary leaf, walnut,
                        ghee, a vitamin premix, 3,249 finished 15 kg canola tins.
                        Counted NOWHERE and invented nowhere. Nothing in a raw-material
                        room is allowed to disappear without a name.
opening.standing_l      LITRES invoiced and not yet physically gone (JIVO_OIL) — the
                        CHEAP dispatch-fulfilment backlog (PENDING+BOOKED, all three
                        books) x the Oil share of the last heavy company split.
opening.standing_l_wide_14d  LITRES, the 14-day bills window's Oil figure. INFORMATION
                        ONLY, never fed to the engine — see THE STANDING PILE below.

orders                  rows {docnum,date,due,customer,code,pieces,value,channel,_src}
  _src="OMS"            oms.orders_recent, one row per LINE, qty is PIECES (C-0001),
                        statuses Completed / Rejected / Billing Rejected excluded.
  _src="ECOM-PO"        ecom.dated_demand (litres x required-by date) split over FG
                        codes by the open-PO mix, litres -> pieces via the plan.
  _src="FORECAST"       the monthly plan, NET of the two real streams per code,
                        in EXIM's weekly buckets. Triple-tagged: channel=FORECAST,
                        docnum FCST-*, customer "(forecast — not yet ordered)".
backlog                 the OMS docs dated before today, at their ORIGINAL date.
inbound_prebooked       {date: {code: qty}} — qty is PIECES for PM, LITRES for RM.
inbound_provenance      {date: {code: "src"}} — parallel, same keys.
lines                   {line: {pack: PIECES/HOUR}} — see LINE RATES below.
rules                   carried, with invoice_truck_lag_days set from the MEASURED
                        median in factory_dispatch.lag_note.

LINE RATES — THE DOUBLE-DERATE TRAP, AND HOW MARK 4 CLOSES IT
=============================================================
The engine multiplies whatever is in `lines` by `rules.efficiency` at run time
(`rate = sp[slot] * EFF`), so a rate that has already been derated gets derated TWICE —
the trap named in ../CLAUDE.md.

MARK 4 closes it by making the multiplication a no-op: `lines` holds the rulebook's
PLANNING speeds — min(80% x the app's rating, the best sustained August hour over at
least three runs) — and `rules.efficiency` is 1.0. The cut happens once, in the
rulebook, and never again here. `lines_basis` says "planning" and `lines_basis_kind`
carries the rulebook's own word for how each one was arrived at (capped / rated /
typical / carried / derived). `build_lines_mark4()` does this.

MARK 3's rule is GONE from this file: it stored a PRE-efficiency rate (an August
observation, else the app's rating verbatim, else the carried table) for the engine to
halve. It could not run any more — the rulebook is mandatory here — and the only thing
it still did was write two honesty sentences about a derate this plan does not do. See
the tombstone above build_lines_mark4() and, for the -sep freeze, engine/freeze_sep.py.

PIECES_MADE_MTD — A DECLARED GAP, NOT A ZERO
============================================
`meta.pieces_made_mtd` is meant to net what the plant has already built off the
plan. `factory_production` fetches TODAY and YESTERDAY only — there is no month
window in `state.json` — so it cannot be computed here without adding a live call,
and inventing one from two days would be a made-up number wearing a real label. It
is published as null with `pieces_made_mtd_basis` saying why, and today's booked
pieces are published beside it under their own honest name. The engine does not
read the field (Mark 2 shipped `SIM_ASOF` and never switched it on), so null costs
nothing today; filling it needs a month-window call added to the adapter.

DEGRADATION
===========
Per SOURCE: live -> `live/state/<src>.last-good.json` -> missing.
Per BLOCK (fg_stock / pm_stock / line_configs are HOURLY, so they are absent from
most envelopes by design): live -> last-good -> `sim/live-carry.json`, this
script's own carry of the last hourly block it actually saw. Nothing is ever
written into `live/state/` from here — that directory belongs to collect.py.
"""

from __future__ import annotations

import calendar
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), "IST")

_HERE = os.path.dirname(os.path.abspath(__file__))          # …/jolly/live
JOLLY = os.path.dirname(_HERE)                              # …/jolly
STATE_DIR = os.environ.get("MARK3_STATE_DIR") or os.path.join(_HERE, "state")
BASE_INPUTS = os.environ.get("FREEZE_BASE_INPUTS") or os.path.join(JOLLY, "sim", "sep-inputs.json")
OUT_PATH = os.environ.get("FREEZE_OUT") or os.path.join(JOLLY, "sim", "live-inputs.json")
CARRY_PATH = os.environ.get("FREEZE_CARRY") or os.path.join(JOLLY, "sim", "live-carry.json")
SYNONYMS_CSV = os.path.join(JOLLY, "reference", "oil-synonyms.csv")

sys.path.insert(0, os.path.join(JOLLY, "engine"))
try:
    from plan_units import pack_litres                      # type: ignore
except Exception:                                           # pragma: no cover
    def pack_litres(sku):                                   # type: ignore
        return None, "plan_units unavailable"
# R15 — the pack and the bottle come from the RECIPE, and there is ONE implementation of
# that rule (engine/pack_class.py). The rulebook pre-computes it for the plan sheet's 84
# rows; this file calls the same function for anything the sheet does not carry (A18).
from pack_class import pack_class                            # type: ignore  # noqa: E402

# ---------------------------------------------------------------------------
# MARK 4 — THE RULEBOOK, and the two DAILY files that feed it
#
# reference/mark4-rulebook.json is the plant's machine rulebook: which line may fill
# which pack in which bottle, at what planning speed, for how many hours, with which
# demand. The freeze EMBEDS it whole, and its presence in sim/live-inputs.json is what
# switches engine/august_sim.py into rulebook mode. There is no other switch — a repo
# path would couple the engine to the checkout and make the August calibration and the
# -sep run ambiguous.
#
# It is generated: edit reference/build_mark4_rulebook.py, never the JSON.
# ---------------------------------------------------------------------------
RULEBOOK_PATH = os.environ.get("MARK4_RULEBOOK") or os.path.join(
    JOLLY, "reference", "mark4-rulebook.json")

# The two files a DAILY cron writes and this file only ever READS. Both are
# adapter-shaped (live/README.md) and both live in live/state/, which is gitignored —
# a fresh clone copies live/fixtures/demand_baseline.json in before running the chain.
#   live/demand_baseline_sap.py -> demand_baseline.json   (the one allowed SAP read)
#   live/dispatch_lag.py        -> dispatch_lag.json      (ji.jivo.in gate log, R21)
# NEITHER is ever called from here: R21 says the lag is daily and RULE 0 keeps SAP out
# of the loop. A missing or stale file is a declared fallback, never a refusal.
DAILY_FILE_ENV = {
    "demand_baseline": "MARK4_DEMAND_BASELINE",
    "dispatch_lag": "MARK4_DISPATCH_LAG",
}
DAILY_MAX_AGE_DAYS = 8          # a weekly cron that missed one run is still usable

# ---------------------------------------------------------------------------
# THE OIL NAME MAP — every entry is a DECLARED ASSUMPTION, written down here.
#
# EXIM names its tanks in plant language ("MUSTARD KACHI GHANI 2B") and SAP names
# the same oil in item-master language ("MUSTARD LOOSE OIL", RM0000003). The two
# systems share NO item code — EXIM's own `code` column (RM00CN, RM0MKG) is a
# different vocabulary from SAP's RM0000002 / RM0000003. So the join is by NAME,
# by hand, once, in the open.
#
#   * "2B" is a SECOND TANK of the same oil, not a second grade — it merges.
#   * RM0000013 POMACE OLIVE is NOT RM0000012 EXTRA LIGHT OLIVE. Ruled by Daman
#     2026-08-29 (reference/oil-synonyms.csv). They are separate lines below and
#     must never be collapsed, however similar the two names look.
#   * A tank whose name is not in this table is NOT guessed. Its litres go to
#     opening.oil_unmapped_l with the tank named, and a warning is raised.
# ---------------------------------------------------------------------------
OIL_NAME_TO_RM = {
    "CANOLA":               "RM0000002",   # CANOLA COLD PRESS LOOSE OIL OLD
    "CANOLA 2B":            "RM0000002",   # second canola tank
    "CRUDE CANOLA":         "RM0000016",   # CRUDE DEGUMMED RAPESEED OIL NEW
    "MUSTARD KACHI GHANI":  "RM0000003",   # MUSTARD LOOSE OIL (kachi ghani = cold pressed)
    "MUSTARD KACHI GHANI 2B": "RM0000003",
    "MUSTARD DEO":          "RM0000017",   # MUSTARD REFINED LOOSE OIL (deodorised = refined)
    "MUSTARD PAKKI GHANI":  "RM0000017",   # pakki ghani = refined
    "MUSTARD REFINED LIGHT": "RM0000017",
    "SOYABEAN":             "RM0000025",   # SOYABEAN REFINED LOOSE OIL
    "POMACE":               "RM0000013",   # POMACE OLIVE LOOSE OIL IMPORTED  <-- NOT RM0000012
    "POMACE 2B":            "RM0000013",
    "EXTRA LIGHT":          "RM0000012",   # EXTRA LIGHT OLIVE LOOSE IMPORTED <-- NOT RM0000013
    "EXTRA LIGHT 2B":       "RM0000012",
    "GROUNDNUT":            "RM0000011",   # GROUNDNUT LOOSE OIL (= PEANUT, C-synonym)
    "GROUNDNUT 2B":         "RM0000011",
    "GROUNDNUT FILTER":     "RM0000011",
    "GROUNDNUT REFINED":    "RM0000011",
    "PEANUT":               "RM0000011",   # synonyms.csv: RM0000066 PEANUT -> RM0000011
    "RICE BRAN REFINED":    "RM0000007",   # RICE BRAN REFINED OIL
    "SESAME":               "RM0000054",   # SEASAME OIL (the plain one; TOASTED is RM0000053)
    "SESAME 2":             "RM0000054",
    "VIRGIN COCONUT OIL":   "RM0000037",   # COCONUT EXTRA VIRGIN OIL
    "COCONUT OIL":          "RM0000043",   # COCONUT OIL (plain)
    "COCONUT OIL 2B":       "RM0000043",
    "VIRGIN OLIVE OIL":     "RM0000014",   # EXTRA VIRGIN OLIVE OIL IMPORTED
    "SUNFLOWER":            "RM0000009",   # REFINED SUNFLOWER OIL
    "OLIVE":                "RM0000001",   # LOOSE REFINED OLIVE OIL
}

# reference/oil-synonyms.csv, applied AFTER the name map: an alias code collapses
# into its canonical. Loaded from the file so a new ruling reaches this script
# through main, not through an edit here.
def load_synonyms(path=SYNONYMS_CSV):
    """alias RM code -> canonical RM code. Comment lines (the never-merge pair) skipped."""
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith("#") or i == 0:
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2 and parts[0].startswith("RM") and parts[1].startswith("RM"):
                    out[parts[1]] = parts[0]
    except OSError:
        pass
    return out

def load_rulebook(path=None):
    """The Mark 4 rulebook, or a refusal. There is no third outcome.

    A plan built without it is Mark 3: it puts 15 L tins on Clear Pack, derives a 15 L
    rate from the 5 L head, runs 12-hour sessions nobody works and derates the planning
    speeds a second time. Every one of those looks fine in the output. So a missing or
    unreadable rulebook stops the freeze rather than silently producing the old plan
    wearing a Mark 4 date.
    """
    p = path or RULEBOOK_PATH
    try:
        rb = load(p)
    except OSError as exc:
        die(f"the Mark 4 rulebook is not readable at {p} ({exc.strerror}). Without it "
            "this freeze would write a Mark 3 plan — 15 L on Clear Pack again, a derived "
            "15 L rate and a 12-hour shift. Rebuild it: python3 reference/build_mark4_rulebook.py")
    except ValueError as exc:
        die(f"the Mark 4 rulebook at {p} is not valid JSON ({exc}). It is GENERATED — "
            "rebuild it with python3 reference/build_mark4_rulebook.py, never hand-edit it.")
    if not isinstance(rb, dict) or not rb.get("version") or not rb.get("lines"):
        die(f"the Mark 4 rulebook at {p} has no version or no lines block — it is not a "
            "rulebook. Rebuild it: python3 reference/build_mark4_rulebook.py")
    return rb


def daily_file(name, today, max_age_days=DAILY_MAX_AGE_DAYS, month_ok=None):
    """One of the DAILY inputs, with its freshness stated. Never raises, never dies.

    Returns (data, mode, age_days, fetched_at) where mode is one of:
        "fresh"        — the file is there, ok, and no older than `max_age_days`
        "stale <n>d"   — it is there and readable, and too old to plan on
        "wrong-month"  — it is fresh but describes a window this month cannot use
        "missing"      — no file, unreadable file, or an envelope with ok:false

    Every consumer of this helper has a declared fallback and says so in honesty, so a
    missing daily file degrades the plan by one named sentence and never refuses it.
    `age_days` is floored at 0: the loop reads a state.json that can be a few minutes
    older than a file written this morning, and "-1 days old" is not a freshness.
    """
    path = os.environ.get(DAILY_FILE_ENV.get(name, "")) or os.path.join(STATE_DIR, f"{name}.json")
    try:
        env = load(path)
    except (OSError, ValueError):
        return None, "missing", None, path
    if not isinstance(env, dict) or not env.get("ok") or not isinstance(env.get("data"), dict):
        return None, "missing", None, path
    at = parse_dt(env.get("fetched_at"))
    age = max(0, (today - at.date()).days) if at else None
    fetched_at = env.get("fetched_at")
    if age is None or age > max_age_days:
        return env["data"], (f"stale {age}d" if age is not None else "missing"), age, fetched_at
    if month_ok is not None and not month_ok(env["data"]):
        return env["data"], "wrong-month", age, fetched_at
    return env["data"], "fresh", age, fetched_at


def week_of_month5(d: date) -> int:
    """The demand baseline's FIVE buckets: 1 = days 1-7 … 5 = days 29-31.

    NOT the same as week_of_month() below, which caps at four because EXIM's plan sheet
    has four columns. Bucket 5 is the whole point of R17 — 134,695 L a day against
    20,317 in bucket 1 — so it cannot be folded into bucket 4.
    """
    return min(5, (d.day - 1) // 7 + 1)


# EXIM sells and stores oil by WEIGHT; the engine counts LITRES. 0.91 kg/L is the
# adapter's own declared constant (exim.inbound.kg_per_litre) and is re-read from
# state at run time; this is only the fallback if that key is absent.
KG_PER_LITRE_DEFAULT = 0.91

# The book this plan makes for. ji.jivo.in's gate is ONE gate carrying three companies, and
# dispatch_lag.py splits every measurement by company for exactly this reason. This engine
# plans JIVO Oil and nothing else, so it takes JIVO Oil's own lag — never the merged
# headline (CLAUDE.md: "Dispatch litres are three companies — Oil is the split").
PLAN_BOOK = "JIVO_OIL"

OMS_DEAD_STATUSES = {"COMPLETED", "REJECTED", "BILLING_REJECTED", "BILLING REJECTED"}
FORECAST_CUSTOMER = "(forecast — not yet ordered)"
# What a FORECAST row was shaped from. The plan sheet's weekly buckets are the Mark 3
# fallback; three months of outside billing is the Mark 4 baseline (R17/R18/A09).
FORECAST_BASIS_SHEET = "plan-sheet-weekly"
FORECAST_BASIS_BILLING = "gt-mt-3m-billing"
OVERDUE_SPREAD_DAYS = 5          # Mark 2's day-1 rule for arrivals already late

# ---------------------------------------------------------------------------
# THE GODOWN ALLOW-LIST — reference/GODOWNS.md, settled by Daman 2026-08-29 and
# mirrored in live/adapters/factory_production.py (PM_WAREHOUSES / RM_WAREHOUSES).
# It is repeated here on purpose: this file has to know what it EXPECTED in order
# to say which room is missing. A room the adapter did not read is UNKNOWN, and an
# unknown packaging room understates packaging and invents stock-outs.
#
# BH-BS and BH-PM are ~98% of the pieces; the other rooms hold the tail, and the
# tail is what BLOCKS — 49 BOM packaging codes carrying 691,184 pieces at the
# 31-Aug freeze read ZERO while only those two rooms were being read.
#
# 2026-09-03: GP-FG IN (allow-listed for oil+packaging as well as finished goods, and it
# holds 64,680 PM), BH-GJ OUT to RM_ROOMS (allow-listed, but what it holds is oil).
# ---------------------------------------------------------------------------
PM_ROOMS = ("BH-BS", "BH-PM", "BH-NM", "BH-SDL", "GP-NM", "GP-PM", "GP-FG")
# The raw-material store. Five BOM oils have no EXIM tank at all and sit here in
# drums: RM0000001 refined olive, RM0000009 sunflower, RM0000015 (a child of both
# blends), RM0000030 cotton, RM0000053 toasted sesame.
# BH-GJ joined this list 2026-09-03. It is allow-listed by Daman's 2026-08-29 ruling (the
# front door for imported oil) and was being read as a PACKAGING room, where every litre
# it holds was thrown away by the PM-code test — 226.8 L of loose oil on 2026-09-03, and
# 42,853 RM in GODOWNS.md's own table. A room that has only just moved here is NOT YET
# READ until the next hourly cycle; that is a warning, never a refusal.
RM_ROOMS = ("BH-LO", "BH-CRUDE", "BH-EX", "BH-GJ")
# The two NON-MOVING rooms, a SUBSET of PM_ROOMS. GODOWNS.md allow-lists them in its table
# and calls them "not available" in its Traps section — both Daman's, same page, same day.
# Ruled 2026-09-03: they are COUNTED (the plant is running on that packaging, and Mark 2's
# calibrated August counted them) and BADGED, with the exposure published so the open
# question can be settled on a number instead of an argument.
NON_MOVING_ROOMS = ("BH-NM", "GP-NM")

# THE GODOWN CEILING IS A DECLARED FACT, NOT AN ASSUMPTION.
# Daman, 2026-09-04: "827,000 L godown = this is correct, no guess now." The figure is
# his own capacity sheet of 2026-08-29 (reference/STORAGE-CAPACITY.md), given with the
# ruling that a tonne means litres on the sale side (C-0050). Mark 2 carried it as
# "assumed, never measured (open question Q2)"; that flag is withdrawn and Q2 is closed.
# The litres themselves are UNCHANGED — 827,000 working / 923,000 peak, out of
# base["rules"]. Only the label changes: this is the owner's declared limit, so it never
# goes into honesty.assumed and the site badges it YOUR LIMIT, not OUR GUESS.
STORAGE_CEILING_BASIS = (
    "DECLARED LIMIT — Daman's capacity sheet, 2026-08-29 "
    "(reference/STORAGE-CAPACITY.md): BH-BT 502 T + BH-PF 421 T = 923 T peak, "
    "450 T + 377 T = 827 T working; tonne = litre (C-0050); reaffirmed as fact "
    "2026-09-04. BH-BT + BH-PF only. The owner's own limit, not an estimate."
)
STORAGE_CEILING_DECLARED_BY = "Daman, 2026-09-04 (capacity sheet 2026-08-29)"

# The UNIT RULE for a raw-material row, declared per code in honesty.assumed for every
# code actually converted. The store mixes units in one list, so the unit is read off
# the row and never assumed. Anything not below is NOT guessed: its pieces go to
# opening.rm_drums_unconverted and are warned about, because a drum count is not litres
# and inventing a drum size is exactly the class of error this project keeps catching.
LITRE_UOMS = {"L", "LT", "LTR", "LTRS", "LIT", "LITRE", "LITRES"}
KG_UOMS = {"KG", "KGS", "KGM", "KILO", "KILOS", "KILOGRAM", "KILOGRAMS"}
TONNE_UOMS = {"MT", "MTS", "TON", "TONS", "TONNE", "TONNES"}


# --------------------------------------------------------------------- utils
def f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_dt(ts):
    if not isinstance(ts, str) or not ts.strip():
        return None
    try:
        dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def parse_date(v):
    """'2026-09-04', an ISO datetime, or None -> date | None. Parsed, never sliced."""
    if isinstance(v, str) and v.strip():
        dt = parse_dt(v)
        if dt:
            return dt.date()
        try:
            return date.fromisoformat(v.strip()[:10])
        except ValueError:
            return None
    return None


def month_end(d: date) -> date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


_KG_IN_NAME = re.compile(r"(\d+(?:\.\d+)?)\s*(?:KG|KGS|KILO|KILOS)\b")


def _kg_in_name(name):
    """'REFINED CANOLA OIL 15 KG TIN' -> 15.0. None when the name does not say.

    Read off the ITEM NAME, so it is only ever good enough to SIZE a warning ("about
    48.7 tonnes of canola is sitting there as tins"), never good enough to turn into
    litres and add to oil on hand. A pack size in a name is a label, not a measurement.
    """
    m = _KG_IN_NAME.search(str(name or "").upper())
    try:
        return float(m.group(1)) if m else None
    except (TypeError, ValueError):
        return None


def kg_per_l_default(exim):
    """EXIM's OWN declared kg/L, re-read from state each run; 0.91 only as the fallback.

    Used in two places that must agree — the drummed-oil conversion in the opening and
    the tonne-to-litre conversion on arrivals — so it lives in one function rather than
    being computed twice from the same key.
    """
    return f(((exim or {}).get("inbound") or {}).get("kg_per_litre"),
             KG_PER_LITRE_DEFAULT) or KG_PER_LITRE_DEFAULT


class Freeze:
    """One freeze. Collects warnings/assumptions as it goes so honesty is a record
    of what THIS run actually did, not a list of what could happen."""

    def __init__(self):
        self.warnings = []
        self.assumed = []
        # sentence -> the plan mode it is true in: "legacy" | "rulebook" | "both".
        # THE POSITIVE CONTRACT the engine drops by (engine/august_sim.py, honesty block).
        # It replaced a keyword blocklist there that struck any sentence containing
        # "derate" / "of rated" / "rules.efficiency" / "50% again" — words a TRUE sentence
        # about planning speeds cannot avoid. What is true in both modes is the default,
        # so a sentence has to be deliberately tagged before anything can delete it.
        self.assumed_modes = {}
        self.provenance = {}
        self.carry = {}
        self.carry_used = []
        self.carry_new = {}
        self.carry_drop = set()

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def assume(self, msg, mode="both"):
        """Record an assumption THIS run made, and the plan mode it is true in.

        mode="both" (the default) is a sentence that holds however the engine is run.
        "rulebook" or "legacy" is a sentence the other mode must not publish — the engine
        drops it by this tag and names it in summary.rulebook.honesty_dropped."""
        if mode not in ("legacy", "rulebook", "both"):
            die(f"honesty mode {mode!r} — it is legacy, rulebook or both")
        if msg not in self.assumed:
            self.assumed.append(msg)
        self.assumed_modes[msg] = mode

    # ---------------------------------------------------------------- sources
    def load_state(self):
        path = os.path.join(STATE_DIR, "state.json")
        if not os.path.exists(path):
            die(f"no {path} — run live/collect.py first")
        self.state = load(path)
        self.sources = self.state.get("sources") or {}
        self.collected_at = parse_dt(self.state.get("collected_at")) or datetime.now(IST)
        try:
            self.carry = load(CARRY_PATH)
        except (OSError, ValueError):
            self.carry = {}

    def source(self, key):
        """(data, mode, env) — live envelope, else the last-good file, else (None,'missing',None).

        A source with ok:false is NOT discarded. collect.py's contract is that partial
        data from a half-failed adapter is published as-is beside ok:false, and the
        adapter itself names the blocks that failed in `data.unavailable`. One dead call
        out of ten sets ok:false for the whole source — throwing away the nine good
        blocks over it would turn a small outage into a refusal. So partial live data is
        used, tagged `live-partial`, and each BLOCK is then validated on its own by
        block() below; only a source with no live data at all falls back to last-good.
        """
        row = self.sources.get(key) or {}
        live = self.state.get(key)
        if isinstance(live, dict) and live:
            if row.get("ok"):
                return live, "live", row
            err = str(row.get("error") or "")[:160]
            # The reason is often EMPTY (an adapter can report ok:false with no
            # error string). Both sentences are rendered on the site, so neither
            # may trail off into nothing: "…was used — " with a blank after the
            # dash is a sentence that says less than saying nothing.
            self.warn(f"{key} reported ok:false ({err or 'it gave no reason'}); its partial "
                      "live data is used and each block is checked on its own")
            self.assume(f"{key} half-failed this cycle and its partial live payload was used"
                        + (f" — {err}" if err else "; it gave no reason why"))
            return live, "live-partial", row
        lg_path = os.path.join(STATE_DIR, f"{key}.last-good.json")
        try:
            env = load(lg_path)
        except (OSError, ValueError):
            env = None
        if isinstance(env, dict) and env.get("ok") and isinstance(env.get("data"), dict):
            at = env.get("fetched_at") or "?"
            self.warn(f"{key} is not ok this cycle ({row.get('error') or 'no data'}); "
                      f"using last-good from {at}")
            # A last-good fallback IS a fallback exercised this cycle, so it belongs in
            # honesty.assumed and not only in warnings/provenance — the site renders
            # honesty.assumed, and a stale source that says nothing there reads as fresh.
            self.assume(f"{key} did not answer this cycle; every number from it is the "
                        f"LAST-GOOD read at {at}, not the plant's position now")
            return env["data"], f"last-good {at}", {"fetched_at": at,
                                                    "server_at": env.get("server_at")}
        self.warn(f"{key} unavailable: no live data and no last-good file")
        return None, "missing", None

    def block(self, key, data, mode, env, field, need):
        """One HOURLY block out of a source, with this script's own carry behind it.

        `need(value) -> bool` decides whether what came back is complete enough to
        publish. fg_stock / pm_stock / line_configs are fetched once an hour, so
        they are absent from ~19 of every 20 envelopes BY DESIGN — that is not an
        outage and must not read as one.
        Returns (value, mode_string).
        """
        unavail = set((data or {}).get("unavailable") or [])
        val = (data or {}).get(field)
        if field in unavail:
            val = None                      # the adapter itself says this block did not answer
        if val is not None and need(val):
            self.carry_new[field] = {
                "at": (env or {}).get("fetched_at") or self.collected_at.isoformat(),
                "source": key, "data": val,
            }
            return val, mode
        # not in this envelope — try the source's own last-good file directly
        try:
            env2 = load(os.path.join(STATE_DIR, f"{key}.last-good.json"))
        except (OSError, ValueError):
            env2 = None
        if isinstance(env2, dict) and isinstance(env2.get("data"), dict):
            v2 = env2["data"].get(field)
            if v2 is not None and need(v2):
                at = env2.get("fetched_at") or "?"
                self.carry_new[field] = {"at": at, "source": key, "data": v2}
                self.assume(f"{field} is not in this cycle's envelope; it is the LAST-GOOD "
                            f"{key} read at {at}")
                return v2, f"last-good {at}"
        c = self.carry.get(field)
        if isinstance(c, dict) and c.get("data") is not None and need(c["data"]):
            self.carry_used.append(field)
            self.carry_new[field] = c
            self.assume(f"{field} carried from the last hourly read at {c.get('at')} "
                        f"— it is fetched once an hour, not every cycle")
            return c["data"], f"carried {c.get('at')}"
        return None, "missing"

    def rooms(self, key, data, mode, env, field, expected):
        """One WAREHOUSE-keyed hourly block, taken ROOM BY ROOM.

        `block()` carries a whole field as a unit, which is right for fg_stock and wrong
        here. factory_production reads ten warehouses inside ONE wall-clock budget and
        names the ones it could not reach in `unavailable`, so a perfectly healthy cycle
        can answer with six rooms out of seven. Carrying the block as a unit would then
        either throw six FRESH rooms away to keep one stale set, or keep the six and let
        the seventh read as zero — and a packaging room that reads zero blocks a whole SKU
        (that is exactly how 49 BOM codes holding 691,184 pieces read empty).

        So every room is taken from the freshest place that has it — this cycle, the
        source's last-good file, then this script's own per-room carry — and the mode is
        recorded PER ROOM. A room nobody has ever seen is returned in `missing`; the
        caller decides whether that is a warning or a refusal.

        Returns (rooms {wh: value}, modes {wh: mode}, missing [wh]).
        """
        unavail = set((data or {}).get("unavailable") or [])
        live_block = (data or {}).get(field) or {}
        try:
            env2 = load(os.path.join(STATE_DIR, f"{key}.last-good.json"))
        except (OSError, ValueError):
            env2 = None
        lg_block = ((env2 or {}).get("data") or {}).get(field) or {}
        lg_at = (env2 or {}).get("fetched_at") or "?"
        carried = self.carry.get(field + "_rooms") or {}
        # A room that has been MOVED OFF this list — BH-GJ went from pm_stock to rm_stock
        # on 2026-09-03 — must not keep a reading in this carry. Its old entry is in the
        # wrong SHAPE for wherever it went (pm_stock carries {code: pieces}, rm_stock
        # carries {code: {qty, uom, name}}), so a stale one would come back as a wrong
        # number the day somebody moved the room again.
        keep = {wh: v for wh, v in carried.items() if wh in expected}
        at_live = (env or {}).get("fetched_at") or self.collected_at.isoformat()

        # An EMPTY room is an answer, not a failure. BH-CRUDE and BH-EX are legitimately
        # empty most days, and the adapter already draws the line for us: a room whose
        # call died is named in `unavailable` and is ABSENT from the block, while a room
        # that answered with nothing in it is PRESENT as {}. Requiring a non-empty dict
        # would turn every empty room into a phantom outage and then reach back for a
        # stale reading of a room that is genuinely bare.
        rooms, modes, missing = {}, {}, []
        for wh in expected:
            v = None if f"{field}[{wh}]" in unavail else live_block.get(wh)
            if isinstance(v, dict) and wh in live_block:
                rooms[wh], modes[wh] = v, mode
                keep[wh] = {"at": at_live, "data": v}
                continue
            v2 = lg_block.get(wh)
            if isinstance(v2, dict) and wh in lg_block:
                rooms[wh], modes[wh] = v2, f"last-good {lg_at}"
                keep[wh] = {"at": lg_at, "data": v2}
                continue
            c = carried.get(wh)
            if isinstance(c, dict) and isinstance(c.get("data"), dict):
                rooms[wh], modes[wh] = c["data"], f"carried {c.get('at')}"
                self.carry_used.append(f"{field}[{wh}]")
                continue
            missing.append(wh)
        self.carry_new[field + "_rooms"] = keep
        self.carry_drop.add(field)          # superseded by the per-room carry above
        return rooms, modes, missing

    def carry_put(self, field, value, at):
        self.carry_new[field] = {"at": at, "data": value}

    def carry_get(self, field):
        c = self.carry.get(field)
        if isinstance(c, dict) and c.get("data") is not None:
            self.carry_used.append(field)
            self.carry_new[field] = c
            return c["data"], c.get("at")
        return None, None

    def save_carry(self):
        keep = dict(self.carry)
        keep.update(self.carry_new)
        for k in self.carry_drop:
            keep.pop(k, None)
        keep["_written_at"] = self.collected_at.isoformat()
        tmp = CARRY_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(keep, fh, indent=1)
        os.replace(tmp, CARRY_PATH)


def die(msg):
    print(f"freeze_live: REFUSING TO WRITE — {msg}", file=sys.stderr)
    sys.exit(2)


# =============================================================== the freeze ==
def build():
    F = Freeze()
    F.load_state()
    base = load(BASE_INPUTS)

    today = F.collected_at.date()
    d1 = month_end(today)
    if today > d1:                                    # cannot happen, but say so if it does
        die(f"collected_at {today} is past its own month end {d1}")
    horizon_days = [today + timedelta(days=i) for i in range((d1 - today).days + 1)]
    working_days = [d for d in horizon_days if d.weekday() != 6]

    plan_rows = base["plan"]
    plan = {p["code"]: p for p in plan_rows}
    realise = base["realise"]
    # Which codes had a MAY-JUL realise rate of their own before this run started. A18
    # rows get a rate out of the billing baseline further down and `realise` is the same
    # object, so the money block has to remember the difference or every rupee would
    # claim to come from the plan sheet (R16/A12 publishes the split).
    sheet_realise_codes = set(realise)
    items = base["items"]
    bom, blends = base["bom"], base["blends"]
    DEF_R = 148.33                                    # the engine's own default ₹/L

    oils = {c for kids in bom.values() for c, _ in kids if c.startswith("RM")}
    for b, kids in blends.items():
        oils.add(b)
        oils.update(c for c, _ in kids)

    # ======================================================= THE RULEBOOK ====
    # Embedded whole, and its presence in the inputs is what makes this a Mark 4 plan.
    rb = load_rulebook()
    sku_pack = dict(rb.get("sku_pack") or {})

    # A10/R20 — the 1-litre carton went from 16 pieces to 20 and SAP opened a NEW item
    # code for the same oil in the bigger box. FG0000461 IS FG0000142's product: the
    # godown holds it, the plant books it today, and the plan sheet has never heard of
    # it, so without this every piece of it reads as finished goods the plan does not
    # recognise and every litre of it is made twice. The alias moves stock and production
    # onto the planned code and is published so the site can say "running now: FG0000461,
    # which is FG0000142's product". The BOM is NOT touched — the 20-piece carton item is
    # not in this month's frozen recipe, so the plan still buys the 16-piece carton.
    ALIAS = dict(((rb.get("carton_change") or {}).get("known_new_code") or {}))

    def alias(code):
        return ALIAS.get(code, code)

    # ------------------------------------------- the demand baseline (R17) ---
    # Usable only when it describes the month BEFORE this one: the shape is "what the
    # last three completed months did", and a window that has not rolled over is last
    # month's answer to this month's question. Wrong month -> the plan sheet, said out
    # loud. The freshness rule protects October from a September file.
    want_to = (today.replace(day=1) - timedelta(days=1)).isoformat()
    want_months = int(f((rb.get("demand") or {}).get("months"), 3)) or 3

    def baseline_month_ok(d):
        w = d.get("window") or {}
        return str(w.get("to")) == want_to and int(f(w.get("months"))) == want_months

    baseline, bl_mode, bl_age, bl_at = daily_file("demand_baseline", today,
                                                  month_ok=baseline_month_ok)
    bl_usable = bl_mode == "fresh" and bool((baseline or {}).get("skus"))
    # FRESH IS NOT USABLE. The daily SAP read can answer ok:true with no SKU rows — a
    # right-month file written this morning that nothing can be planned from — and both
    # the fallback reason and the honesty sentence then said "demand_baseline.json is
    # fresh" while telling the operator to go and run the job that had just run. The
    # state the plan reports has to be the state that made it fall back.
    bl_state = ("fresh but carries no SKU rows" if bl_mode == "fresh" and not bl_usable
                else bl_mode)

    # ------------------------------------ A18 — the SKUs the sheet never had ---
    # Appended BEFORE anything else reads `plan`, so one definition of "a code this plan
    # can build" runs through the whole freeze: the OMS filter, the ecom split, the
    # expected stream, the FG split and the engine all see the same set.
    nonplan = {"candidates": 0, "appended": 0, "appended_l_per_month": 0,
               "skipped": [], "skipped_l_per_month": 0}
    a18_rows = []
    if bl_usable:
        a18_rows, a18_packs, nonplan = expected_only_rows(baseline, plan, bom, items,
                                                          oils, realise)
        for row in a18_rows:
            plan_rows.append(row)
            plan[row["code"]] = row
        sku_pack.update(a18_packs)
        if a18_rows:
            F.assume(f"{len(a18_rows)} SKU(s) the plant SELLS are not on the plan sheet and "
                     f"are carried as expected-only rows worth "
                     f"{nonplan['appended_l_per_month']:,} L a month — their pack comes from "
                     "SAP's own recipe and their rate from what they billed for (A18)")
        if nonplan["skipped"]:
            F.assume(f"{len(nonplan['skipped'])} SKU(s) worth "
                     f"{nonplan['skipped_l_per_month']:,} L a month sold in the last three "
                     "months and are in NO day of this plan: this month's frozen master data "
                     "has no recipe for them, so nothing here knows what they are made of. "
                     "They are named in demand_baseline.nonplan.skipped (A18)")

    # R19/B08 — a SKU nobody has ordered yet is ranked by its TRAILING monthly litres.
    # The engine reads it off the plan row; nothing wrote that field until now, so the
    # whole expected tier ranked by the order the rows happened to sit in.
    trailing_set = 0
    if bl_usable:
        for code, sku in (baseline.get("skus") or {}).items():
            if code in plan:
                plan[code]["trailing_l_per_month"] = round(f(sku.get("litres_per_month")))
                trailing_set += 1

    # ------------------------------------------ AC06 — a class for every row ---
    # The rulebook pre-computes the sheet's rows; anything it did not see is classed here
    # by the SAME function (engine/pack_class.py), never by a second copy of the rule.
    derived_packs = []
    for code, p in plan.items():
        if code in sku_pack:
            continue
        pc = pack_class(code, bom, items, p.get("litres_per_piece"), p.get("pack_type", ""))
        sku_pack[code] = dict(sku=p.get("sku"), litres_per_piece=p.get("litres_per_piece"),
                              sheet_pack_type=p.get("pack_type"), derived_by="freeze", **pc)
        derived_packs.append(code)
    unclassed = sorted(c for c, v in sku_pack.items()
                       if c in plan and (v.get("slot") is None or v.get("family") == "UNKNOWN"))
    if unclassed:
        die("pack class (R15/AC06) — no machine slot can be worked out for "
            f"{', '.join(unclassed)}. The engine would carry them as UNKNOWN, which makes "
            "them eligible on no line at all and drops them out of the plan with no error "
            "anywhere. Their BOM names no container this file recognises: fix the recipe "
            "or rule on the pack, then rebuild reference/mark4-rulebook.json.")
    if derived_packs:
        F.assume(f"{len(derived_packs)} plan row(s) are not in the rulebook's own pack table "
                 "and were classed here by the same rule (the BOM's container child, R15): "
                 + ", ".join(derived_packs[:8]) + ("…" if len(derived_packs) > 8 else ""))

    prod, prod_mode, prod_env = F.source("factory_production")
    disp, disp_mode, disp_env = F.source("factory_dispatch")
    inb, inb_mode, inb_env = F.source("factory_inbound")
    exim, exim_mode, exim_env = F.source("exim")
    oms, oms_mode, oms_env = F.source("oms")
    ecom, ecom_mode, ecom_env = F.source("ecom")
    # The days already gone this month. Read for the site, NOT fed to the engine
    # on this run — the plan still starts from today's live position and nothing
    # about these records changes it. It comes through F.source() rather than
    # being opened out of state.json directly so it inherits the same
    # live / live-partial / last-good / missing handling as every other source,
    # and so it can never be a different vintage from the plan beside it.
    hist, hist_mode, hist_env = F.source("factory_history")

    def prov(name, key, mode, env, note):
        F.provenance[name] = {
            "source": key,
            "fetched_at": (env or {}).get("fetched_at"),
            "server_at": (env or {}).get("server_at"),
            "mode": mode,
            "note": note,
        }

    recon = {}

    # ------------------------------------------------------- opening.fg -----
    def both_fg(v):
        return isinstance(v, dict) and all(w in v for w in ("BH-PF", "BH-BT"))

    fg_stock, fg_mode = F.block("factory_production", prod, prod_mode, prod_env,
                                "fg_stock", both_fg)
    if fg_stock is None:
        die("opening.fg — factory_production.fg_stock has neither BH-PF nor BH-BT "
            "live, in last-good, or carried. A zero godown is not a degraded answer, "
            "it is a wrong one: the plan would re-make a month of stock that exists.")
    fg = {}
    fg_nonfg = {}
    for wh in ("BH-PF", "BH-BT"):
        for code, qty in (fg_stock.get(wh) or {}).items():
            q = f(qty)
            if q <= 0:
                continue
            tgt = fg if str(code).upper().startswith("FG") else fg_nonfg
            tgt[code] = tgt.get(code, 0.0) + q

    detail, _ = F.block("factory_production", prod, prod_mode, prod_env,
                        "fg_stock_detail", lambda v: isinstance(v, dict) and bool(v))
    names = {}
    for wh in ("BH-PF", "BH-BT"):
        for row in ((detail or {}).get(wh) or []):
            names.setdefault(row.get("item_code"), row.get("item_name"))
    # ---- A10: the carton change, applied to the godown ---------------------------
    # Done BEFORE fg_other_l is worked out, so the aliased pieces are counted as the
    # planned product they are and not as "other FG in the way".
    fg_alias_applied = {}
    for new_code, planned in sorted(ALIAS.items()):
        pieces = f(fg.pop(new_code, 0.0))
        if pieces <= 0:
            continue
        fg[planned] = fg.get(planned, 0.0) + pieces
        fg_alias_applied[new_code] = {"to": planned, "pieces": round(pieces),
                                      "name": names.get(new_code) or plan.get(planned, {}).get("sku")}
        names.pop(new_code, None)
    if fg_alias_applied:
        F.assume("the 1-litre carton changed from 16 pieces to 20 and SAP opened a new code "
                 "for the same oil, so " + ", ".join(
                     f"{n} ({v['pieces']:,} pieces) is counted as {v['to']}"
                     for n, v in sorted(fg_alias_applied.items()))
                 + ". The recipe is NOT changed — this month's frozen BOM has no 20-piece "
                   "carton item, so the plan still buys the 16-piece one (A10/R20)")

    fg_other_l, fg_other_unparsed = 0.0, 0
    for code, qty in fg.items():
        if code in plan:
            continue
        lit, _basis = pack_litres(names.get(code) or "")
        if lit:
            fg_other_l += qty * lit
        else:
            fg_other_unparsed += 1
    if fg_other_unparsed:
        F.assume(f"{fg_other_unparsed} non-plan finished-goods code(s) in the godown have a "
                 "pack size this file cannot read from the name, so opening.fg_other_l is a floor")
    fg_meta, _ = F.block("factory_production", prod, prod_mode, prod_env,
                         "fg_stock_meta", lambda v: isinstance(v, dict) and bool(v))
    for wh in ("BH-PF", "BH-BT"):
        if ((fg_meta or {}).get(wh) or {}).get("truncated"):
            F.warn(f"fg_stock[{wh}] page filled up — opening.fg is a FLOOR for that room")
    prov("opening_fg", "factory_production", fg_mode, prod_env,
         "dashboards stock BH-PF + BH-BT, one warehouse per call, FG codes only")

    fg_plan_l = sum(q * plan[c]["litres_per_piece"] for c, q in fg.items() if c in plan)
    recon["fg"] = dict(codes=len(fg), pieces=sum(fg.values()), plan_l=fg_plan_l,
                       other_l=fg_other_l, nonfg_codes=len(fg_nonfg), mode=fg_mode)

    # ------------------------------------------------- opening.stock (PM) ---
    # EVERY packaging room on GODOWNS.md's allow-list, not just the two big ones, and
    # room by room so one unread room cannot take the other six down with it.
    pm_rooms, pm_modes, pm_missing = F.rooms("factory_production", prod, prod_mode,
                                             prod_env, "pm_stock", PM_ROOMS)
    stock = {}
    pm_nonpm = 0
    pm_by_room = {}
    if not pm_rooms:
        # NOT one of the three refusals PHASE4-FREEZE-LIVE.md lists, and refused anyway,
        # for the reason acceptance criterion 6 gives: "never a silent zero opening".
        # The engine reads an absent PM code as zero on hand, and a zero packaging
        # position blocks nearly every SKU — so the plan would say "the plant can build
        # nothing" and an operator would act on it. An unread room and an empty room are
        # the same number here and this run cannot tell them apart. That is precisely
        # the failure that once reported Rs 8.48 Cr blocked by 38 "zero" packaging items.
        # ONE room is enough to publish; ZERO rooms is the refusal.
        die("opening.stock[PM…] — not one of the packaging rooms "
            f"({', '.join(PM_ROOMS)}) is available live, in last-good, or carried. The "
            "engine reads an absent PM code as zero, so writing this file would publish a "
            "plan that says the plant can build nothing. Wait for an hourly cycle "
            "(MARK3_FORCE_HOURLY=1 forces one).")
    pm_meta, _ = F.block("factory_production", prod, prod_mode, prod_env,
                         "pm_stock_meta", lambda v: isinstance(v, dict) and bool(v))
    for wh in PM_ROOMS:
        if wh not in pm_rooms:
            continue
        room_codes = room_pieces = 0
        for code, qty in (pm_rooms[wh] or {}).items():
            q = f(qty)
            if q <= 0:
                continue
            if str(code).upper().startswith("PM"):
                stock[code] = stock.get(code, 0.0) + q
                room_codes += 1
                room_pieces += q
            else:
                pm_nonpm += 1
        pm_by_room[wh] = {"codes": room_codes, "pieces": round(room_pieces),
                          "mode": pm_modes.get(wh)}
        if ((pm_meta or {}).get(wh) or {}).get("truncated"):
            F.warn(f"pm_stock[{wh}] page filled up — packaging on hand is a FLOOR for "
                   "that room, and the rows lost are the SMALLEST (sorted desc), which "
                   "is the direction that invents a stock-out")
            F.assume(f"pm_stock[{wh}] did not fit one page; the smallest stocks are missing")
    # ---- THE NON-MOVING ROOMS: counted, and BADGED ---------------------------------
    # GODOWNS.md contradicts itself about BH-NM and GP-NM. Its allow-list table has both
    # on the oil+packaging list; its Traps section says "BH-NM / GP-NM are non-moving —
    # 2.65 M PM parked between them. Not available." Both statements are Daman's, on the
    # same page, from the same day.
    #
    # RULED (2026-09-03): INCLUDE them, and say so loudly. The plant is running on that
    # packaging today, and Mark 2's August run — the calibrated one — counted
    # them. Dropping them now would move the calibration out from under the engine.
    # But "non-moving" may well mean unusable, and if it does the codes below are the
    # ones that disappear, so the size of the exposure is published rather than argued
    # about: it is an OPEN QUESTION for Daman, not a settled reading.
    nm_read = [wh for wh in NON_MOVING_ROOMS if wh in pm_rooms]
    pm_bom_codes = {c for kids in bom.values() for c, _ in kids
                    if str(c).upper().startswith("PM")}
    nm_only, nm_only_pcs = [], 0.0
    for code in sorted(pm_bom_codes):
        in_nm = sum(f((pm_rooms.get(wh) or {}).get(code)) for wh in nm_read)
        in_rest = sum(f((pm_rooms.get(wh) or {}).get(code))
                      for wh in pm_rooms if wh not in NON_MOVING_ROOMS)
        if in_nm > 0 and in_rest <= 0:
            nm_only.append({"code": code, "pieces": round(in_nm),
                            "name": items.get(code, {}).get("name", "")})
            nm_only_pcs += in_nm
    nm_only.sort(key=lambda r: -r["pieces"])
    nm_total_pcs = sum(f(q) for wh in nm_read
                       for c, q in (pm_rooms.get(wh) or {}).items()
                       if str(c).upper().startswith("PM") and f(q) > 0)
    if not nm_read:
        F.assume("the non-moving rooms (" + ", ".join(NON_MOVING_ROOMS) + ") were not read "
                 "this cycle, so how much of the plan leans on them is UNKNOWN this run — "
                 "not zero")
    else:
        F.assume(
            "NM rooms counted as available — open question for Daman; if 'non-moving' means "
            f"unusable, {len(nm_only)} BOM codes / {round(nm_only_pcs):,} pcs "
            + ("(" + ", ".join(r["code"] for r in nm_only[:3]) + " among them) "
               if nm_only else "")
            + "vanish and the plan changes materially. "
            + ", ".join(nm_read) + f" hold {round(nm_total_pcs):,} pcs of packaging in all; "
            "GODOWNS.md lists them as allowed AND calls them 'not available' in the same "
            "document, and Mark 2's calibrated August run counted them")
        if nm_only:
            F.warn(
                f"{len(nm_only)} packaging codes this month's recipes need have stock ONLY in "
                "the NON-MOVING rooms " + ", ".join(nm_read) + f" — {round(nm_only_pcs):,} "
                "pieces, biggest first: "
                + ", ".join(f"{r['code']} {r['name']} {r['pieces']:,}" for r in nm_only[:6])
                + ". They are COUNTED as available here. If Daman rules that non-moving means "
                  "unusable, every one of those codes goes to zero and blocks its whole "
                  "product.")
    prov("packaging_non_moving", "factory_production",
         "+".join(sorted({pm_modes[wh] for wh in nm_read})) or "not read this cycle", prod_env,
         "BH-NM and GP-NM are COUNTED as available packaging (ruled 2026-09-03). "
         "reference/GODOWNS.md allow-lists them and, in its Traps section, calls them "
         "'not available' — an unresolved contradiction, open question for Daman. Mark 2's "
         "calibrated August run counted them, so this run does too.")

    stale_pm = sorted(wh for wh, m in pm_modes.items() if not str(m).startswith("live"))
    if stale_pm:
        F.assume("packaging rooms read from an older cycle rather than this one: "
                 + ", ".join(f"{wh} ({pm_modes[wh]})" for wh in stale_pm))
    if pm_missing:
        F.warn("packaging room(s) not read this cycle — no live answer, no last-good, no "
               "carry: " + ", ".join(pm_missing) + ". A room only just added to the list is "
               "NOT YET READ, not unavailable — it fills in on the next hourly cycle, and it "
               "is never a reason to refuse the whole plan. Until then packaging on hand is a "
               "FLOOR by whatever they hold, and a missing room understates stock, which is "
               "the direction that invents a stock-out.")
        F.assume("packaging on hand EXCLUDES " + ", ".join(pm_missing) +
                 " — those rooms have not answered yet, so their codes read zero here even "
                 "if the room is full")
    prov("opening_pm", "factory_production",
         "+".join(sorted(set(pm_modes.values()))) or "missing", prod_env,
         "dashboards stock, ONE WAREHOUSE PER CALL, over GODOWNS.md's packaging "
         "allow-list: " + ", ".join(wh for wh in PM_ROOMS if wh in pm_rooms) +
         (" (missing: " + ", ".join(pm_missing) + ")" if pm_missing else ""))
    recon["pm"] = dict(codes=sum(1 for k in stock if k.startswith("PM")),
                       pieces=sum(v for k, v in stock.items() if k.startswith("PM")),
                       nonpm_rows=pm_nonpm, rooms=pm_by_room, missing=pm_missing,
                       mode="+".join(sorted(set(pm_modes.values()))) or "missing")

    # ------------------------------------------- opening.stock (RM, litres) -
    syn = load_synonyms()
    tanks = ((exim or {}).get("tanks") or {})
    by_oil = tanks.get("by_oil") or []
    oil_l_total = f(tanks.get("total_l"))
    mapped_l, unmapped_l, unmapped = 0.0, 0.0, []
    map_used = {}
    if not by_oil:
        # A total EXIM outage behaves EXACTLY like a missing packaging room, and for the
        # same reason: with no tank reading every RM code is zero, the plan orders oil the
        # plant is standing on, and every blend reads blocked. F.source() has already tried
        # exim.last-good.json at the SOURCE level; this reaches into the file one more time
        # in case exim answered but the tanks block itself was the half that failed.
        try:
            env_x = load(os.path.join(STATE_DIR, "exim.last-good.json"))
        except (OSError, ValueError):
            env_x = None
        lg_tanks = (((env_x or {}).get("data") or {}).get("tanks") or {})
        if lg_tanks.get("by_oil"):
            tanks = lg_tanks
            by_oil = tanks.get("by_oil") or []
            oil_l_total = f(tanks.get("total_l"))
            at = (env_x or {}).get("fetched_at") or "?"
            exim_mode = f"last-good {at}"
            F.warn(f"exim.tanks.by_oil was empty this cycle; the tank position is the "
                   f"LAST-GOOD dip reading from {at}")
            F.assume(f"bulk oil in tanks is the LAST-GOOD read at {at}, not the position now")
    if not by_oil:
        die("opening.stock[RM…] — EXIM gave no tank position, live or last-good. Every "
            "bulk oil would read zero, so the plan would block every blend and re-order "
            "oil the plant is standing on. That is a wrong answer wearing a plausible "
            "face, not a degraded one — the same refusal the packaging rooms get.")
    for row in by_oil:
        name = str(row.get("oil") or "").strip().upper()
        lit = f(row.get("litres"))
        rm = OIL_NAME_TO_RM.get(name)
        if rm:
            rm = syn.get(rm, rm)                       # collapse a ruled alias
            stock[rm] = stock.get(rm, 0.0) + lit
            mapped_l += lit
            map_used.setdefault(rm, []).append(name)
        else:
            unmapped_l += lit
            unmapped.append({"oil": row.get("oil"), "exim_code": row.get("code"), "litres": lit})
    if unmapped:
        F.warn("EXIM tanks this file cannot map to an RM code: "
               + ", ".join(f"{u['oil']} ({u['litres']:,.0f} L)" for u in unmapped)
               + " — counted in opening.oil_unmapped_l, never guessed into a code")
        F.assume(f"{unmapped_l:,.0f} L of bulk oil sits in tanks whose name has no RM mapping "
                 "and is therefore invisible to the plan")
    for rm, srcs in sorted(map_used.items()):
        F.assume("oil name map used: " + " + ".join(sorted(set(srcs))) + f" -> {rm} "
                 f"({items.get(rm, {}).get('name', rm)})")
    prov("opening_oil", "exim", exim_mode, exim_env,
         "tanks by_oil litres — a MANUAL DAILY DIP READING, not a sensor; "
         "mapped to RM codes by name (OIL_NAME_TO_RM), synonyms applied")
    tank_l_by_code = {c: v for c, v in stock.items() if str(c).startswith("RM")}

    # ------------------------------------- opening.stock (RM, the DRUM store) -
    # THE RULING — EXIM IS THE BULK-OIL TRUTH (Daman, through Fable, 2026-09-03).
    #
    # opening.stock for an oil is the EXIM TANK dip if EXIM has a tank for that code, and
    # the DRUMMED litres out of the raw-material rooms ONLY if it does not. NEVER BOTH.
    # This REPLACES the "two separate physical stocks" reading this file carried earlier
    # the same day. The three things that settled it:
    #   * reference/GODOWNS.md: "Bulk oil is not in SAP's godowns at all — it is in EXIM
    #     ... BH-LO and the tanks cannot be reconciled."
    #   * EXIM's own sap-sync inventory shows BH-LO GROUNDNUT at 275,110 L — EXACTLY the
    #     figure the raw-material store reports for the same oil. BH-LO is SAP's BOOK view
    #     of the loose oil in the tanks, not a second stock standing beside it.
    #   * Added together they gave 754,900 L of tanks + 792,221 L of "drums" = 1.55 M L
    #     against a MEASURED tank capacity of 1,351,500 L. The plant cannot hold it.
    #
    # The book figure is not thrown away. Every oil's raw-material-store litres are
    # published as opening.oil_book_l, for information, marked as the LAGGING view: it is
    # what SAP thinks, and SAP moves after the tank does.
    #
    # ONLY THE PLAN'S OWN OILS ARE CONVERTED. These rooms are a general store — they hold
    # rosemary leaf (26.65 KGS) and walnut (11.5 KGS) alongside the oil, and the KG branch
    # used to divide those by 0.91 kg/L and count them as 29 L and 13 L of bulk oil.
    # Anything whose canonical code is not in the plan's oil set now goes to
    # opening.rm_store_other with its own qty and unit: named, counted nowhere, invented
    # nowhere. Nothing in these rooms is allowed to vanish without a name.
    rm_rooms, rm_modes, rm_missing = F.rooms("factory_production", prod, prod_mode,
                                             prod_env, "rm_stock", RM_ROOMS)
    kgl = kg_per_l_default(exim)
    drum_l_by_code, drum_by_room, drums_unconverted = {}, {}, {}
    book_l_by_code, book_rows, rm_store_other = {}, {}, {}
    superseded, weight_conv = {}, []
    drum_l = 0.0
    for wh in RM_ROOMS:
        if wh not in rm_rooms:
            continue
        room_l, room_codes = 0.0, 0
        for code, row in (rm_rooms[wh] or {}).items():
            if isinstance(row, dict):
                qty, uom, nm = f(row.get("qty")), str(row.get("uom") or "").upper(), row.get("name")
            else:                                   # a bare number: no unit came with it
                qty, uom, nm = f(row), "", None
            if qty <= 0:
                continue
            canon = syn.get(code, code)             # a ruled alias is the same oil
            if canon not in oils:
                # Not an oil this month's recipes ask for — a tin, a premix, a leaf, a
                # nut, a ghee. FIX: it used to be either silently dropped (anything not
                # starting with RM, which lost SF0000009's 3,249 tins and the vitamin
                # premix) or converted as if it were oil (the KG rows). Named here.
                slot = rm_store_other.setdefault(
                    code, {"qty": 0.0, "uom": uom or "(none)", "name": nm, "rooms": []})
                if slot["uom"] not in (uom or "(none)", "MIXED"):
                    slot["uom"] = "MIXED"
                slot["qty"] = round(slot["qty"] + qty, 3)
                if wh not in slot["rooms"]:
                    slot["rooms"].append(wh)
                continue
            if uom in LITRE_UOMS:
                lit = qty
            elif uom in KG_UOMS:
                lit = qty / kgl
                weight_conv.append((canon, code, wh, qty, uom, lit, f"{uom} / {kgl} kg per L"))
            elif uom in TONNE_UOMS:
                lit = qty * 1000.0 / kgl
                weight_conv.append((canon, code, wh, qty, uom, lit,
                                    f"{uom} x 1000 / {kgl} kg per L"))
            else:
                slot = drums_unconverted.setdefault(
                    code, {"qty": 0.0, "uom": uom or "(none)", "name": nm, "rooms": []})
                slot["qty"] = round(slot["qty"] + qty, 3)
                if wh not in slot["rooms"]:
                    slot["rooms"].append(wh)
                continue
            # THE BOOK FIGURE — recorded for every plan oil, whether or not it is fed in.
            book_l_by_code[canon] = book_l_by_code.get(canon, 0.0) + lit
            book_rows.setdefault(canon, []).append(
                {"code": code, "wh": wh, "qty": qty, "uom": uom, "l": lit, "name": nm})
            if tank_l_by_code.get(canon, 0.0) > 0:
                # THE RULING: EXIM has a tank for this oil, so the tank IS the position
                # and the store's figure is the same oil counted a second time on paper.
                superseded[canon] = superseded.get(canon, 0.0) + lit
                continue
            stock[canon] = stock.get(canon, 0.0) + lit
            drum_l_by_code[canon] = drum_l_by_code.get(canon, 0.0) + lit
            drum_l += lit
            room_l += lit
            room_codes += 1
        drum_by_room[wh] = {"codes": room_codes, "litres": round(room_l),
                            "mode": rm_modes.get(wh)}
    stale_rm = sorted(wh for wh, m in rm_modes.items() if not str(m).startswith("live"))
    if stale_rm:
        F.assume("raw-material rooms read from an older cycle rather than this one: "
                 + ", ".join(f"{wh} ({rm_modes[wh]})" for wh in stale_rm))
    if rm_missing:
        F.warn("raw-material room(s) not read this cycle — no live answer, no last-good, no "
               "carry: " + ", ".join(rm_missing) + ". A room that has only just been added to "
               "the list is NOT YET READ, not unavailable: it fills in on the next hourly "
               "cycle. Until then, drummed oil in it is invisible to this plan.")
        F.assume("drummed oil EXCLUDES " + ", ".join(rm_missing) +
                 " — those rooms have not answered yet, so bulk oil is a FLOOR")

    # --- the synonym merges, named so the merge is auditable (oil-synonyms.csv) -------
    merge_note = {}
    for canon, rows in sorted(book_rows.items()):
        aliases = sorted({r["code"] for r in rows if r["code"] != canon})
        if not aliases:
            continue
        parts = []
        for a in aliases:
            nm = next((r["name"] for r in rows if r["code"] == a and r["name"]), "")
            parts.append(f"{a} {nm}".strip() +
                         f" {sum(r['l'] for r in rows if r['code'] == a):,.0f} L")
        merge_note[canon] = " + ".join(parts) + f" merged into {canon} per "\
                            "reference/oil-synonyms.csv (Daman, 2026-08-29)"
        F.assume(
            "synonym merge in the raw-material store: " + " + ".join(parts)
            + f" is counted as {canon} {items.get(canon, {}).get('name', '')}".rstrip()
            + f", so {canon}'s book figure is {book_l_by_code[canon]:,.0f} L over "
            + ", ".join(sorted({r["wh"] for r in rows}))
            + " — ruled in reference/oil-synonyms.csv by Daman, 2026-08-29")

    # --- the ruling, said out loud per oil, with the merge named where there was one --
    for canon in sorted(superseded):
        F.assume(
            f"{canon} {items.get(canon, {}).get('name', '')}".rstrip()
            + f": opening stock is the EXIM TANK dip of {tank_l_by_code[canon]:,.0f} L. The "
              f"raw-material store's {book_l_by_code[canon]:,.0f} L for the same oil"
            + (f" (which includes {merge_note[canon]})" if canon in merge_note else "")
            + " is SAP's BOOK view of that same tank oil and is NOT added — EXIM is the "
              "bulk-oil truth (ruled 2026-09-03). It is published for information in "
              "opening.oil_book_l")
    if drum_l_by_code:
        F.assume(
            "no EXIM tank exists for " + ", ".join(
                f"{c} {items.get(c, {}).get('name', '')}".rstrip() + f" {v:,.0f} L"
                for c, v in sorted(drum_l_by_code.items(), key=lambda kv: -kv[1]))
            + " — for these, and only these, opening stock is the raw-material store's own "
              "figure. It is a BOOK figure and lags the floor")

    # --- FIX: the self-report must name every weight->litre conversion actually made ---
    if weight_conv:
        for canon, code, wh, qty, uom, lit, how in weight_conv:
            F.assume(f"weight -> litres conversion made on drummed oil {canon} "
                     + (f"(from {code}) " if code != canon else "")
                     + f"{items.get(canon, {}).get('name', '')}".rstrip()
                     + f" in {wh}: {qty:,.2f} {uom} -> {lit:,.0f} L ({how})")
    else:
        kg_other = sorted(c for c, v in rm_store_other.items()
                          if v["uom"] in (KG_UOMS | TONNE_UOMS))
        F.assume(
            "NO weight->litre conversion was made this run: every raw-material row that "
            "counted was already in litres"
            + ((". The rooms' weighed rows — "
                + ", ".join(f"{c} {rm_store_other[c]['name'] or ''} "
                            f"{rm_store_other[c]['qty']:,.2f} {rm_store_other[c]['uom']}".strip()
                            for c in kg_other)
                + " — are NOT oils in this month's recipes, so they are reported in "
                  "opening.rm_store_other instead of being divided by "
                  f"{kgl} kg/L and counted as bulk oil") if kg_other else ""))

    # --- nothing in these rooms vanishes without a name -------------------------------
    if drums_unconverted:
        F.warn("plan oils held in a unit that is neither a volume nor a weight, so they are "
               "NOT converted and NOT counted as oil on hand: "
               + ", ".join(f"{c} {v['qty']:,.0f} {v['uom']}"
                           for c, v in sorted(drums_unconverted.items()))
               + " — published in opening.rm_drums_unconverted. A drum count is not litres "
                 "and this file will not invent a drum size.")
        F.assume("some plan oil is held in PCS/NOS with no litre figure; it is reported in "
                 "opening.rm_drums_unconverted and left OUT of oil on hand, so bulk oil is "
                 "understated by whatever those drums hold")
    if rm_store_other:
        F.warn("raw-material rooms hold stock that is NOT an oil in this month's recipes. It "
               "is named in opening.rm_store_other and counted nowhere — never converted, "
               "never invented: "
               + ", ".join(f"{c} {v['qty']:,.2f} {v['uom']} {v['name'] or ''}".strip()
                           for c, v in sorted(rm_store_other.items(),
                                              key=lambda kv: -kv[1]["qty"]))
               + ".")
        F.assume(f"{len(rm_store_other)} raw-material row(s) are not plan oils and are "
                 "counted nowhere — they are listed with their own qty and unit in "
                 "opening.rm_store_other so nothing in those rooms disappears silently")
    tins = rm_store_other.get("SF0000009")
    if tins:
        per_tin_kg = _kg_in_name(tins.get("name"))
        F.warn(
            f"SF0000009 {tins['name'] or 'REFINED CANOLA OIL 15 KG TIN'}: {tins['qty']:,.0f} "
            f"{tins['uom']} in {', '.join(tins['rooms'])}"
            + (f" — the item name says {per_tin_kg:g} kg a tin, so that is roughly "
               f"{tins['qty'] * per_tin_kg / 1000:,.1f} TONNES of canola"
               if per_tin_kg else " — a tin count with no weight in its name")
            + " sitting in the raw-material store as FINISHED TINS. It is NOT converted to "
              "litres and NOT counted anywhere in this plan: a pack size read off an item "
              "name is not a measurement, and this file does not invent litres. It is oil "
              "the plan cannot see until somebody rules on it.")
        F.assume(
            f"SF0000009 REFINED CANOLA OIL 15 KG TIN — {tins['qty']:,.0f} {tins['uom']} in "
            + ", ".join(tins["rooms"])
            + (f" (~{tins['qty'] * per_tin_kg / 1000:,.1f} t by the name's own pack size)"
               if per_tin_kg else "")
            + " — is left out of oil on hand entirely. Unconverted tins, not litres")
    prov("opening_oil_drums", "factory_production",
         "+".join(sorted(set(rm_modes.values()))) or "missing", prod_env,
         "dashboards stock, one warehouse per call, over the raw-material rooms "
         + ", ".join(wh for wh in RM_ROOMS if wh in rm_rooms) +
         "; each row converted by ITS OWN uom (L as-is, KG/MT via EXIM's "
         f"{kgl} kg/L) and ONLY for oils this month's recipes use. An oil that EXIM has a "
         "tank for takes the TANK figure, never both (ruled 2026-09-03); the store's own "
         "figure for it is published as opening.oil_book_l. Everything else in those rooms "
         "is named in opening.rm_store_other and counted nowhere")
    # The oils that are in BOTH places. Under the 2026-09-03 ruling this is no longer
    # "two physical stocks" — it is the list of oils where the tank WON and the book
    # figure was set aside, which is exactly what has to stay visible for the call to be
    # reversible without re-deriving anything.
    both = sorted(superseded)
    absent = sorted(c for c in oils if c not in blends and stock.get(c, 0.0) <= 0)
    if absent:
        F.warn("BOM oils with NO tank in EXIM and no drums in the raw-material store, so "
               "they read zero: "
               + ", ".join(f"{c} {items.get(c, {}).get('name', '')}" for c in absent))
        F.assume("an oil with neither a tank nor a raw-material row reads zero on hand — "
                 + ", ".join(absent))
    recon["oil"] = dict(tanks=len(by_oil), total_l=oil_l_total, mapped_l=mapped_l,
                        unmapped_l=unmapped_l, codes=len(map_used), mode=exim_mode,
                        drum_l=drum_l, drum_codes=len(drum_l_by_code), drum_rooms=drum_by_room,
                        drum_missing=rm_missing, unconverted=len(drums_unconverted),
                        both_codes=both, book_l=sum(book_l_by_code.values()),
                        book_codes=len(book_l_by_code),
                        superseded_l=sum(superseded.values()),
                        store_other=len(rm_store_other))

    # ------------------------------------------------- opening.standing_l ---
    # THE PILE FED TO THE ENGINE IS THE CHEAP PATH, NOT THE 14-DAY WINDOW.
    #
    # factory_dispatch publishes two figures and they do not reconcile (ratio 5.8x on
    # 2026-09-03). The WIDE one — invoiced_not_dispatched.by_company[JIVO_OIL] — counts
    # every Oil BILL invoiced in the last 14 days whose dispatch plan never reached
    # DISPATCHED: 1,260,504 L, which is 152% of the whole declared godown, so the engine
    # opened with negative space and made ZERO on days 1 and 2. Daman proved on
    # 2026-09-03 that the dock module records only ~45% of dispatches, so "the plan never
    # reached DISPATCHED" includes a great many bills that physically left the gate. The
    # wide figure is therefore an upper bound on paperwork, not a measurement of stock in
    # the way.
    #
    # The CHEAP one — the dispatch-fulfilment-summary backlog, PENDING + BOOKED only — is
    # open dispatch plans across all three books: 284,549 L. It is all-company, so the
    # Oil share is taken from the last heavy read's company split and applied to it.
    # Both figures are published: standing_l is what the engine eats, standing_l_wide_14d
    # is the wide one kept beside it so the choice is visible rather than buried.
    ind = ((disp or {}).get("invoiced_not_dispatched") or {})
    by_co = ind.get("by_company") or {}
    oil_row = by_co.get("JIVO_OIL") or {}
    cheap_l = ind.get("litres")
    wide_oil_l = oil_row.get("litres")
    all_co_l = ind.get("by_company_total_litres")
    if all_co_l is None and by_co:
        all_co_l = sum(f((v or {}).get("litres")) for v in by_co.values())
    disp_at = (disp_env or {}).get("fetched_at") or F.collected_at.isoformat()

    # The Oil share of the cheap pile, carried between heavy cycles the way the wide
    # figure used to be. A ratio ages far better than a litre count: the book's company
    # mix moves slowly, the pile itself moves hourly.
    share = share_at = None
    if wide_oil_l is not None and f(all_co_l) > 0:
        share = f(wide_oil_l) / f(all_co_l)
        share_at = disp_at
        F.carry_put("standing_oil_share",
                    {"share": share, "oil_l": f(wide_oil_l), "all_l": f(all_co_l)}, disp_at)
        F.carry_put("standing_l_wide_14d", f(wide_oil_l), disp_at)
    else:
        c, at = F.carry_get("standing_oil_share")
        if isinstance(c, dict) and f(c.get("share")) > 0:
            share, share_at = f(c["share"]), at

    standing = standing_basis = None
    if cheap_l is not None:
        cheap = f(cheap_l)
        # If the cheap endpoint ever grows its own company split, use it directly: a
        # split whose parts add back to the headline is the same population, not the
        # 14-day one. Two per cent of slack for rounding, nothing more.
        cheap_has_split = (f(all_co_l) > 0 and cheap > 0
                           and abs(f(all_co_l) - cheap) / cheap <= 0.02)
        if cheap_has_split and wide_oil_l is not None:
            standing = f(wide_oil_l)
            standing_basis = ("invoiced_not_dispatched.by_company[JIVO_OIL].litres, whose "
                              "company split adds back to the same headline this cycle — "
                              "one population, no ratio needed")
        elif share is not None:
            standing = cheap * share
            standing_basis = (
                f"the CHEAP pile {cheap:,.0f} L (dispatch-fulfilment-summary backlog, "
                f"PENDING+BOOKED, all three books) x the Oil share {share:.4f} of the last "
                f"heavy bills read ({share_at})")
            F.assume(
                f"the invoiced-but-not-trucked Oil pile is the ALL-COMPANY cheap backlog "
                f"({cheap:,.0f} L) apportioned by the Oil share of the last heavy company "
                f"split ({share * 100:.1f}%, read {share_at}) = {standing:,.0f} L. The two "
                f"endpoints count different populations, so the share is a proportion "
                f"carried across, NOT a subset of either figure")
            F.assume(
                "the WIDE 14-day figure "
                + (f"({f(wide_oil_l):,.0f} L) " if wide_oil_l is not None else "")
                + "is NOT fed to the engine: it counts every Oil bill in a 14-day invoice "
                  "window whose dispatch plan never reached DISPATCHED, and the dock module "
                  "records only about 45% of dispatches (Daman, 2026-09-03), so it includes "
                  "bills that physically left. It is published as opening.standing_l_wide_14d")
        else:
            standing = cheap
            standing_basis = ("the ALL-COMPANY cheap backlog with NO Oil share available — "
                              "no heavy company split has ever been read on this box")
            F.assume(f"no Oil share of the dispatch backlog has ever been read, so the whole "
                     f"all-company cheap pile ({cheap:,.0f} L) stands in for Oil's. That "
                     f"OVERSTATES Oil's pile — it includes Mart and Beverages — which "
                     f"understates free godown space and therefore production")
        F.carry_put("standing_l", standing, disp_at)
    else:
        carried, at = F.carry_get("standing_l")
        if carried is not None:
            standing = f(carried)
            standing_basis = (f"CARRIED from {at} — factory_dispatch published no backlog "
                              "headline this cycle")
            disp_mode = f"carried {at}"
            F.assume(f"the invoiced-but-not-trucked Oil pile is carried from {at}: "
                     "factory_dispatch gave no backlog figure this cycle")
    if standing is None:
        die("opening.standing_l — factory_dispatch gave neither a backlog headline nor a "
            "carried figure, live or last-good. Zero here reads the godown as free when it "
            "is not (C-0054).")
    prov("standing", "factory_dispatch", disp_mode, disp_env, standing_basis)

    # The wide figure, published for information only. Carried when the heavy split is
    # not in this cycle's envelope so the site never shows it as blank on a cheap cycle.
    wide_mode = disp_mode
    if wide_oil_l is None:
        w, at = F.carry_get("standing_l_wide_14d")
        if w is not None:
            wide_oil_l, wide_mode = f(w), f"carried {at}"
    if wide_oil_l is not None:
        F.provenance["standing_wide_14d"] = {
            "source": "factory_dispatch",
            "fetched_at": (disp_env or {}).get("fetched_at"),
            "server_at": (disp_env or {}).get("server_at"),
            "mode": wide_mode,
            "note": ("invoiced_not_dispatched.by_company[JIVO_OIL].litres — "
                     + str(ind.get("by_company_basis") or "")[:200]
                     + " INFORMATION ONLY: not fed to the engine, because the dock module "
                       "records only ~45% of dispatches so this window includes bills that "
                       "physically left."),
        }

    # The two companion figures the alternatives block quotes BESIDE the wide one — the
    # all-company 14-day total and the godown-rooms-only slice — come out of the SAME
    # heavy read as the company split, so on a cheap cycle they go missing at exactly
    # the moment the Oil share does. The wide figure itself is already carried a few
    # lines up; these were not, so every cheap cycle published two bare nulls under
    # keys whose names say "litres", gen_live.py's null scan refused the whole run, and
    # the chain stopped at gen 19 cycles out of 20 (seen live, 2026-09-03T16:30).
    # Carried with the share and stamped, for the same reason: a null there does not
    # mean "unknown", it means "this cycle was cheap".
    alt_all_l = f(all_co_l) if all_co_l is not None else None
    alt_rooms_l = (ind.get("godown_rooms_only") or {}).get("litres")
    alt_note = (ind.get("reconciliation") or {}).get("note")
    alt_at = disp_at if alt_all_l is not None else None      # never stamp an absent figure
    if alt_all_l is not None:
        F.carry_put("standing_alt_companions",
                    {"all_l": alt_all_l, "rooms_l": alt_rooms_l, "note": alt_note}, disp_at)
    else:
        c, at = F.carry_get("standing_alt_companions")
        if isinstance(c, dict):
            alt_all_l = c.get("all_l")
            alt_rooms_l = c.get("rooms_l") if alt_rooms_l is None else alt_rooms_l
            alt_note = c.get("note") if not alt_note else alt_note
            alt_at = at

    ceil_l = f(base["rules"]["storage_ceiling_l"])
    # Warned, NEVER capped: the ceiling is Daman's DECLARED limit (his capacity sheet,
    # 2026-08-29, reaffirmed as fact 2026-09-04) and silently trimming a measured pile to
    # fit the declared room would hide the very collision the planner exists to show.
    if standing >= ceil_l:
        F.warn(f"the invoiced-not-dispatched Oil pile ({standing:,.0f} L) is at or above the "
               f"whole DECLARED godown ceiling ({ceil_l:,.0f} L) — day 1 opens with no space "
               "and the engine will throttle production until the pile drains.")
    elif standing + fg_plan_l + fg_other_l > ceil_l:
        F.warn(f"the opening godown is already OVER the DECLARED ceiling: "
               f"{standing:,.0f} L invoiced-not-gone + {fg_plan_l + fg_other_l:,.0f} L of "
               f"finished goods = {standing + fg_plan_l + fg_other_l:,.0f} L against "
               f"{ceil_l:,.0f} L "
               f"({100 * (standing + fg_plan_l + fg_other_l) / ceil_l:.0f}%). Nothing is "
               "capped — the ceiling is Daman's declared limit and the collision is the "
               "finding, not an error to smooth away.")
    if wide_oil_l is not None and f(wide_oil_l) >= ceil_l:
        F.warn(f"for scale: the WIDE 14-day figure ({f(wide_oil_l):,.0f} L) is "
               f"{100 * f(wide_oil_l) / ceil_l:.0f}% of the whole declared godown on its own. "
               "It is published for information and is NOT what the engine was given.")
    # The two dispatch endpoints do not reconcile and are not meant to be added or
    # differenced (the adapter says so). The one this freeze uses is named in
    # provenance.standing; the others are published beside it so the choice is visible
    # rather than buried — this single number decides day-1 godown space.
    standing_alts = {
        "used": round(standing),
        "used_basis": standing_basis,
        "cheap_backlog_all_company_l": ind.get("litres"),
        "cheap_backlog_source": ind.get("source"),
        "oil_share_of_heavy_split": round(share, 4) if share is not None else None,
        "oil_share_read_at": share_at,
        "wide_14d_by_company_JIVO_OIL_l": round(f(wide_oil_l)) if wide_oil_l is not None else None,
        "wide_14d_all_company_l": alt_all_l,
        "godown_rooms_only_all_company_l": alt_rooms_l,
        "companions_read_at": alt_at,
        "note": alt_note,
    }
    recon["standing"] = dict(litres=standing, mode=disp_mode,
                             ceiling_l=ceil_l, pct=100.0 * standing / ceil_l if ceil_l else 0,
                             wide_l=f(wide_oil_l) if wide_oil_l is not None else None,
                             wide_mode=wide_mode, share=share,
                             cheap_l=f(cheap_l) if cheap_l is not None else None,
                             fg_l=fg_plan_l + fg_other_l)

    # ------------------------------------------- the invoice-to-gate lag (R21) --
    # MEASURED DAILY off ji.jivo.in's gate log by live/dispatch_lag.py, which is a cron
    # script and not an adapter — R21 says daily in as many words, and a 30-day gate read
    # does not fit inside a 3-minute loop. When that file is missing or stale the plan
    # falls back to factory_dispatch.LAG_NOTE: ONE measurement, taken by hand on
    # 2026-09-03 off page 1 of 4. It is a real number and it is three days older every
    # three days, so the fallback is always named.
    lag_file, lag_mode, lag_age, lag_at = daily_file("dispatch_lag", today)
    lag_note = (disp or {}).get("lag_note") or {}
    lag_days, out_lag, lag_live, lag_say = select_lag(
        lag_file, lag_mode, lag_age, lag_at, lag_note, base["rules"]["invoice_truck_lag_days"])
    F.assume(lag_say)
    F.provenance["dispatch_lag"] = {
        "source": "live/state/dispatch_lag.json" if lag_live else "factory_dispatch.LAG_NOTE",
        "fetched_at": lag_at if lag_live else out_lag["measured_on"],
        "server_at": None, "mode": lag_mode, "age_days": lag_age,
        "note": out_lag["source"],
    }

    # --------------------------------------------------------- orders -------
    orders, backlog = [], []
    real_pieces = {}
    # R18 — the expected stream is netted by the REAL TRADE book only. ecom is on its own
    # POs and the billing baseline excluded e-commerce in the first place, so netting it
    # too would take the same litres out twice. Kept apart from real_pieces for that one
    # reason, and dated inside the horizon because demand due in October is not this
    # month's cover.
    oms_pieces = {}
    order_rows_by_channel = {}

    def add_order(row):
        orders.append(row)
        order_rows_by_channel[row["channel"]] = order_rows_by_channel.get(row["channel"], 0) + 1

    # -- 1. OMS ---------------------------------------------------------------
    oms_rows = ((oms or {}).get("orders_recent") or [])
    outliers = {(o.get("order_id"), o.get("code")) for o in ((oms or {}).get("price_outliers") or [])}
    oms_kept = oms_dropped_nonplan = 0
    oms_nonplan_pieces = 0.0
    oms_value_suppressed = 0.0
    for o in oms_rows:
        st = str(o.get("status_code") or "").upper()
        if st in OMS_DEAD_STATUSES or str(o.get("status_name") or "").upper() in OMS_DEAD_STATUSES:
            continue
        created = parse_date(o.get("created"))
        if created is None:
            continue
        due = parse_date(o.get("delivery_date")) or created
        docnum = str(o.get("order_number") or o.get("id"))
        for ln in (o.get("lines") or []):
            code = ln.get("code")
            pieces = f(ln.get("qty"))                  # PIECES, not cartons (C-0001)
            if pieces < 1:
                continue
            if code not in plan:
                oms_dropped_nonplan += 1
                oms_nonplan_pieces += pieces
                continue
            value = f(ln.get("total"))
            if (o.get("id"), code) in outliers:        # keep the pieces, drop the money
                oms_value_suppressed += value
                value = 0.0
            # date is CLAMPED to today for an order created before the horizon, and the
            # original date is kept on the backlog row beside it. Not cosmetic: the engine
            # walks `orders_by_day` day by day from D0, so a row dated before D0 is never
            # read into po_left — it would be dispatchable but invisible as demand, which
            # is silently losing the overdue pile. (The engine then skips the backlog row,
            # because its docnum is already in `orders` — no double count.)
            row = {"docnum": docnum, "date": max(created, today).isoformat(),
                   "due": due.isoformat(), "customer": str(o.get("customer") or "")[:60],
                   "code": code, "pieces": pieces, "value": value,
                   "channel": str(ln.get("category") or "TRADE").upper(), "_src": "OMS"}
            add_order(row)
            real_pieces[code] = real_pieces.get(code, 0.0) + pieces
            if today <= date.fromisoformat(row["date"]) <= d1:
                oms_pieces[code] = oms_pieces.get(code, 0.0) + pieces
            oms_kept += 1
            if created < today:
                backlog.append(dict(row, date=created.isoformat()))
    if oms_dropped_nonplan:
        F.warn(f"{oms_dropped_nonplan} live OMS order line(s) ({oms_nonplan_pieces:,.0f} pieces) "
               "are on codes the September plan does not carry — the engine cannot build them, "
               "so they are not in the demand stream")
    if oms_value_suppressed:
        F.assume(f"₹{oms_value_suppressed:,.0f} of OMS line value was zeroed on price-outlier "
                 "lines (kept as pieces) — the rate is outside the 3-1,000 ₹/L band")
    if oms_mode == "missing":
        F.warn("OMS did not answer and has no last-good file — the real trade order book is "
               "MISSING from this run and forecast will stand in for all of it")
    prov("orders", "oms", oms_mode, oms_env,
         "orders_recent, one row per LINE, qty is PIECES (C-0001); statuses "
         "Completed/Rejected/Billing Rejected excluded; price-outlier lines keep pieces, lose value")

    # -- 2. ecom --------------------------------------------------------------
    dated = ((ecom or {}).get("dated_demand") or [])
    # every UNEXPIRED Amazon litre (the adapter's new key), falling back to the
    # old plan-month-only key if this run is reading an older state file.
    amz_mix = {k: f(v) for k, v in (
        (ecom or {}).get("open_po_litres_by_fg_amazon")
        or (ecom or {}).get("open_po_litres_by_fg_amazon_sep") or {}).items()}
    qc_mix = {k: f(v) for k, v in ((ecom or {}).get("open_po_litres_by_fg_qcomm") or {}).items()}

    def mix_for(platform):
        m = amz_mix if str(platform).upper() == "AMAZON" else qc_mix
        m = {c: v for c, v in m.items() if c in plan and v > 0}
        tot = sum(m.values())
        return ({c: v / tot for c, v in m.items()}, tot) if tot > 0 else ({}, 0.0)

    ec_kept_l = ec_excluded_l = ec_unallocated_l = ec_subpiece_l = 0.0
    ec_rows = 0
    for row in dated:
        d = parse_date(row.get("date"))
        lit = f(row.get("litres"))
        if d is None or lit <= 0:
            continue
        if not (today.year == d.year and today.month == d.month):
            ec_excluded_l += lit         # unexpired, but due in a later month
            continue
        share, _tot = mix_for(row.get("platform"))
        if not share:
            ec_unallocated_l += lit
            continue
        land = max(d, today)
        docnum = f"EC-{str(row.get('platform') or 'ECOM').replace(' ', '')}-{d.isoformat()}"
        for code, w in share.items():
            lpp = f(plan[code]["litres_per_piece"], 1.0) or 1.0
            pieces = lit * w / lpp
            if pieces < 1:
                ec_subpiece_l += pieces * lpp    # a slice too small to be one bottle
                continue
            add_order({"docnum": docnum, "date": land.isoformat(), "due": d.isoformat(),
                       "customer": str(row.get("platform") or "ECOM"), "code": code,
                       "pieces": pieces, "value": pieces * lpp * f(realise.get(code), DEF_R),
                       "channel": "ECOM", "_src": "ECOM-PO"})
            real_pieces[code] = real_pieces.get(code, 0.0) + pieces
            ec_rows += 1
        ec_kept_l += lit
    if dated:
        F.assume("ecom gives litres by DATE and litres by FG code but never the two together, "
                 "so each dated row is split across FG codes in the proportion of that "
                 "platform group's OPEN-PO mix (Amazon separately from q-commerce)")
        F.assume("ecom order value is DERIVED as litres x the May-Jul realise rate — ecom's "
                 "dated demand carries no money")
    if ec_excluded_l:
        F.warn(f"{ec_excluded_l:,.0f} L of ecom demand is required AFTER "
               f"{today.strftime('%B %Y')} — every litre of it is an unexpired open PO, it is "
               "simply not due this month, so it is not in this month's demand stream")
    if ec_subpiece_l >= 1:
        F.assume(f"{ec_subpiece_l:,.0f} L of ecom demand fell out as sub-one-bottle slices when "
                 "each dated row was split across that platform's FG mix — the ecom stream is a "
                 f"FLOOR by that much ({100 * ec_subpiece_l / max(ec_kept_l, 1):.2f}% of it)")
    if ec_unallocated_l:
        F.warn(f"{ec_unallocated_l:,.0f} L of dated ecom demand could not be split onto any plan "
               "code — that platform group's open-PO mix is empty")
    if ecom_mode == "missing":
        F.warn("ecom did not answer and has no last-good file — no ecom demand in this run")
    F.provenance["orders_ecom"] = {
        "source": "ecom", "fetched_at": (ecom_env or {}).get("fetched_at"),
        "server_at": (ecom_env or {}).get("server_at"), "mode": ecom_mode,
        "note": "dated_demand (" + str((ecom or {}).get("dated_demand_date_basis") or "") +
                ") split onto FG codes by the open-PO mix",
    }

    # -- 3. EXPECTED ORDERS — three months of outside billing, week-shaped ----
    # R17/R18: the month's GT/MT orders are PREDICTED from what those customers actually
    # bought, not waited for. The plan sheet's weekly buckets stay as the fallback and
    # every fallback says so on the assumptions page.
    fc_rows = 0
    fc_pieces = 0.0
    fc_basis = FORECAST_BASIS_SHEET
    exp_stats = {}
    if bl_usable:
        rows, exp_stats = expected_stream(baseline, plan, today, d1, oms_pieces,
                                          want_months, realise, DEF_R)
        for row in rows:
            add_order(row)
            fc_rows += 1
            fc_pieces += row["pieces"]
        fc_basis = FORECAST_BASIS_BILLING
        F.assume("expected orders are three months of OUTSIDE billing per SKU "
                 f"({', '.join(baseline.get('channels_included') or [])}; e-commerce, "
                 "branches, staff, cash sales and the inter-company cards left out), shaped "
                 "by which week of the month those customers actually buy in and netted by "
                 "the real trade order book. They are NOT orders and are tagged three ways "
                 "(channel=FORECAST, docnum FCST-*, customer "
                 f"'{FORECAST_CUSTOMER}')")
        if exp_stats.get("sku_shape_pooled"):
            F.assume(f"{exp_stats['sku_shape_pooled']} SKU(s) did not sell in all "
                     f"{want_months} months of the window, so their month is shaped by the "
                     "WHOLE book's week-of-month pattern rather than their own (A09)")
        if exp_stats.get("dropped_subpiece_l", 0) >= 1:
            F.assume(f"{exp_stats['dropped_subpiece_l']:,.0f} L of expected demand fell out "
                     "as sub-one-bottle daily slices — the expected stream is a FLOOR by "
                     "that much")
        if exp_stats.get("negative_slice_l", 0) <= -1:
            F.assume(f"{abs(exp_stats['negative_slice_l']):,.0f} L of NEGATIVE expected demand "
                     "was dropped — week buckets where the three months of billing are net "
                     "returns. A return is not an order to make something, so it neither "
                     "creates a row nor reduces one")
    else:
        weekly = load_weekly_buckets(F)
        for code, p in plan.items():
            net = f(p.get("pieces")) - real_pieces.get(code, 0.0)
            if net < 1:
                continue
            profile = forecast_profile(code, weekly, working_days, today, F)
            if not profile:
                continue
            lpp = f(p["litres_per_piece"], 1.0) or 1.0
            rate = f(realise.get(code), DEF_R)
            for d, w in profile.items():
                pieces = net * w
                if pieces < 1:
                    continue
                add_order({"docnum": f"FCST-W{week_of_month(d)}-{code}", "date": d.isoformat(),
                           "due": d.isoformat(), "customer": FORECAST_CUSTOMER, "code": code,
                           "pieces": pieces, "value": pieces * lpp * rate,
                           "channel": "FORECAST", "_src": "FORECAST",
                           "basis": FORECAST_BASIS_SHEET})
                fc_rows += 1
                fc_pieces += pieces
        F.assume("the remainder of the monthly plan, net of every real order this run can see, "
                 "is carried as FORECAST rows — they are NOT orders and are tagged three ways "
                 "(channel=FORECAST, docnum FCST-*, customer '(forecast — not yet ordered)')")
        F.assume("expected orders are the plan sheet's weekly buckets — "
                 f"live/state/demand_baseline.json is {bl_state}; run "
                 "live/demand_baseline_sap.py (a DAILY job on the VPS, never in the loop) "
                 "to plan from what the trade actually bought (R17)")
    if not orders:
        die("orders — no OMS line, no ecom row and no forecast bucket survived. The engine "
            "asserts on an empty demand stream; writing this file would only move the failure.")

    recon["orders"] = {"rows": len(orders), "by_channel": order_rows_by_channel,
                       "oms_lines": oms_kept, "ecom_rows": ec_rows, "forecast_rows": fc_rows,
                       "backlog_rows": len(backlog), "forecast_basis": fc_basis,
                       "real_pieces": sum(real_pieces.values()), "forecast_pieces": fc_pieces}

    # ------------------------------------------ demand_baseline, published ---
    # Everything about where the expected stream came from, including the three internal
    # reconciliations — the SKU rows, the channel split and the week buckets each have to
    # add back up to the window total, and a baseline that does not is a baseline nobody
    # should plan on (AC08).
    def _pct_of_total(part, whole):
        return round(100.0 * part / whole, 2) if whole else None

    bl_tot = f(((baseline or {}).get("totals") or {}).get("litres"))
    bl_skus = (baseline or {}).get("skus") or {}
    bl_months = int(f(((baseline or {}).get("window") or {}).get("months"), want_months)) or want_months
    out_baseline = {
        "present": baseline is not None,
        "mode": bl_mode,
        "usable": bl_usable,
        "fetched_at": bl_at if baseline is not None else None,
        "age_days": bl_age,
        "path": os.environ.get(DAILY_FILE_ENV["demand_baseline"])
                or os.path.join(STATE_DIR, "demand_baseline.json"),
        "window": (baseline or {}).get("window"),
        "months": bl_months,
        "months_expected": want_months,
        "source": (baseline or {}).get("basis"),
        "channel_field": (baseline or {}).get("channel_field"),
        "channels_included": (baseline or {}).get("channels_included"),
        "channels_excluded": (baseline or {}).get("channels_excluded"),
        "intercompany_excluded": (baseline or {}).get("intercompany_excluded"),
        "totals": (baseline or {}).get("totals"),
        "by_channel": (baseline or {}).get("by_channel"),
        "week_of_month": (baseline or {}).get("week_of_month"),
        "reconciliation": {
            "skus_vs_totals_pct": _pct_of_total(
                sum(f(s.get("litres_per_month")) * bl_months for s in bl_skus.values()), bl_tot),
            "channels_vs_totals_pct": _pct_of_total(
                sum(f(v.get("litres")) for v in ((baseline or {}).get("by_channel") or {}).values()),
                bl_tot),
            "weeks_vs_totals_pct": _pct_of_total(
                sum(f(v.get("litres")) for v in ((baseline or {}).get("week_of_month") or {}).values()),
                bl_tot),
            "note": ("each is that block's litres as a % of the window total — 100% means the "
                     "SKU rows, the channel split and the week buckets all add back up"),
        },
        "used_for_forecast": bool(bl_usable and fc_basis == FORECAST_BASIS_BILLING),
        "fallback_reason": (None if bl_usable else
                            f"demand_baseline.json is {bl_state}" +
                            (f" (window {(baseline or {}).get('window')}, wanted a window "
                             f"ending {want_to} over {want_months} months)"
                             if bl_mode == "wrong-month" else "")),
        "expected_rows": fc_rows,
        "expected_litres": round(exp_stats.get("litres", 0.0)),
        "expected_skus": exp_stats.get("skus", 0),
        "netted_oms_pieces": round(exp_stats.get("netted_oms_pieces", 0.0)),
        # Sub-one-bottle slices only, so it can never publish a negative "dropped litres".
        "dropped_subpiece_l": round(exp_stats.get("dropped_subpiece_l", 0.0)),
        # Negative day slices out of week buckets that are net returns — dropped for the
        # same reason and counted apart, signed, so the sign says what it is.
        "negative_slice_l": round(exp_stats.get("negative_slice_l", 0.0)),
        "sku_shape_own": exp_stats.get("sku_shape_own", 0),
        "sku_shape_pooled": exp_stats.get("sku_shape_pooled", 0),
        "trailing_rows_set": trailing_set,
        "nonplan": nonplan,
    }
    if baseline is not None and not bl_usable:
        F.warn(f"the demand baseline is {bl_state} — expected orders fall back to the plan "
               "sheet's weekly buckets, which have no month-end bunching in them at all")

    # ------------------------------------------------- inbound_prebooked ----
    inbound, inb_prov, qty_by_src = {}, {}, {}
    kg_per_l = kg_per_l_default(exim)
    lead = base["rules"]["lead_days"]
    counts = {}                       # bookings placed, per source

    def land(d: date, code, qty, src, _spread=False):
        """Put qty on a date, never before today. Anything already overdue is SPREAD over
        the next few working days rather than dumped on day 1 — Mark 2's rule, kept.

        `_spread` marks the recursive calls a spread makes, so ONE overdue booking counts
        as one booking and not as five (the spread once reported 7 open bulk POs as
        "35 bookings"). The litres are unaffected either way — the five shares sum back
        to the original quantity.
        """
        if qty <= 0:
            return
        if d < today:
            spread = [x for x in working_days[:OVERDUE_SPREAD_DAYS]] or [today]
            share = qty / len(spread)
            base_src = src.replace("-OVERDUE", "")
            if not _spread:
                counts[base_src] = counts.get(base_src, 0) + 1
            for dd in spread:
                land(dd, code, share, src + "-OVERDUE", _spread=True)
            return
        if d > d1 + timedelta(days=7):
            return                                     # lands past the engine's own window
        k = d.isoformat()
        inbound.setdefault(k, {})[code] = inbound.setdefault(k, {}).get(code, 0.0) + qty
        # Two different sources CAN land the same code on the same date — a truck with an
        # ETA of the 4th and the spread balance of the blanket PO it was drawn against.
        # The quantities add; the label must add too. Overwriting it once relabelled
        # 130,363 L of real EXIM trucks as an undrawn contract balance, which is the
        # provenance reading BACKWARDS: firm arrival dressed up as the loosest number here.
        prior = inb_prov.setdefault(k, {}).get(code)
        parts = prior.split("+") if prior else []
        if src not in parts:
            parts.append(src)
        inb_prov[k][code] = "+".join(parts)
        base_src = src.replace("-OVERDUE", "")
        if not _spread:
            counts[base_src] = counts.get(base_src, 0) + 1
        qty_by_src[base_src] = qty_by_src.get(base_src, 0.0) + qty

    # (a) material sitting in QC at the factory — packaging clears in ~1 h, oil in days
    qc_accepted = qc_pending = 0
    for entry in ((inb or {}).get("in_qc") or []):
        for it in (entry.get("items") or []):
            if str(it.get("qc_status") or "").upper() != "ACCEPTED":
                qc_pending += 1
                continue                               # never accepted_qty; never a pending line
            code = it.get("code")
            qty = f(it.get("received_qty"))
            uom = str(it.get("uom") or "").upper()
            if not code or qty <= 0:
                continue
            if uom in ("MTS", "MT", "TON", "TONS"):
                qty = qty * 1000.0 / kg_per_l          # tonnes -> kg -> litres
                land(today + timedelta(days=2), code, qty, "QC-OIL")
            else:
                land(today + timedelta(days=1), code, qty, "QC-PM")
            qc_accepted += 1
    if qc_pending:
        F.assume(f"{qc_pending} line(s) sitting in the factory's QC queue are still "
                 "INSPECTION_PENDING / NO_ARRIVAL_SLIP, not ACCEPTED, so none of that material "
                 "is booked as arriving — a pending line is not a delivery")
    if qc_accepted:
        F.assume("QC-cleared packaging is booked to land tomorrow and QC-cleared bulk oil the "
                 "day after — measured behaviour (packaging clears in about an hour, tankers "
                 "sit in QC for days)")
    if inb_mode == "missing":
        F.warn("factory_inbound did not answer and has no last-good file — nothing in QC is "
               "counted as arriving this run")

    # (b) EXIM tankers actually rolling, with an ETA
    otw_l = otw_unmapped_l = 0.0
    otw_by_rm = {}                    # litres per RM already booked as a truck on the road
    for r in (((exim or {}).get("inbound") or {}).get("on_the_way") or []):
        eta = parse_date(r.get("eta"))
        lit = f(r.get("litres"))
        name = str(r.get("oil") or "").strip().upper()
        rm = OIL_NAME_TO_RM.get(name)
        if not rm or lit <= 0:
            otw_unmapped_l += lit
            continue
        rm = syn.get(rm, rm)
        if eta is None:
            eta = today + timedelta(days=int(f(lead.get("oil"), 11)))
            F.assume("an EXIM tanker on the way carries no ETA; it is booked at the measured "
                     f"oil lead time ({lead.get('oil')} days)")
        land(eta, rm, lit, "EXIM-OTW")
        otw_l += lit
        otw_by_rm[rm] = otw_by_rm.get(rm, 0.0) + lit
    if otw_unmapped_l:
        F.warn(f"{otw_unmapped_l:,.0f} L on the way from EXIM has an oil name with no RM "
               "mapping and is not booked as arriving")
    other_exim_l = sum(
        f(r.get("litres"))
        for k in ("under_loading", "in_contract")
        for r in ((((exim or {}).get("inbound") or {}).get(k)) or [])
    )
    if other_exim_l:
        F.warn(f"{other_exim_l:,.0f} L of EXIM oil is under loading or still in contract and is "
               "NOT booked as arriving — only trucks already on the way are")

    # (c) open bulk POs — the remaining contract, landing at the measured lead time
    po_l = 0.0
    po_rows = ((exim or {}).get("open_bulk_pos") or [])
    heads, loaded = {}, {}
    for r in po_rows:
        if str(r.get("status") or "").upper().startswith("COMPLET"):
            continue
        rm = syn.get(r.get("rm_code"), r.get("rm_code"))   # a ruled alias is the same oil
        if rm not in oils:                             # /pos/ is EVERY raw material, not oils
            continue
        pon = str(r.get("po_number"))
        heads.setdefault(pon, {"qty": f(r.get("contract_qty")), "rm": rm,
                               "date": parse_date(r.get("po_date"))})
        loaded[pon] = loaded.get(pon, 0.0) + f(r.get("load_qty"))
    # A truck already booked in (b) is STILL inside the undrawn balance here: every
    # open_bulk_pos row carries a grpo_no, so load_qty counts only what has been RECEIVED,
    # while an on_the_way row carries grpo_number null. Booking both counts the rolling
    # tankers twice and makes oil look more available than it is — the one direction a
    # production plan must not err in. So the on-the-way litres are netted out of the
    # remaining contract for the same oil first, floored at zero.
    otw_credit = dict(otw_by_rm)
    po_netted_l = 0.0
    for pon, h in heads.items():
        remain_mt = h["qty"] - loaded.get(pon, 0.0)    # contract_qty repeats per TRUCK
        if remain_mt <= 0:
            continue
        lit = remain_mt * 1000.0 / kg_per_l
        take = min(lit, otw_credit.get(h["rm"], 0.0))
        if take > 0:
            lit -= take
            otw_credit[h["rm"]] -= take
            po_netted_l += take
        if lit <= 0:
            continue
        d = (h["date"] or today) + timedelta(days=int(f(lead.get("oil"), 11)))
        land(d, h["rm"], lit, "PO-LEAD")
        po_l += lit
    if po_l:
        F.warn(f"{po_l:,.0f} L is booked to arrive from OPEN BULK POs (contract quantity minus "
               "what has been drawn down). JIVO's oil POs are BLANKET orders drawn down over "
               "many part-loads — the adapter says so itself — so this is the undrawn balance "
               "of a contract, NOT a shipment on its way. It is the loosest number in this "
               "freeze and it makes oil look more available than it is.")
        F.assume("open bulk POs are booked as arriving at order date + the oil lead time. They "
                 "are BLANKET contracts drawn down in part-loads, so the remaining balance is "
                 "not a scheduled delivery — treat it as an upper bound on oil arriving")
        F.assume("EXIM bulk-PO quantities are undeclared units and are read as METRIC TONNES "
                 f"(the rates are ~₹150,000 per unit), converted at {kg_per_l} kg/L; the "
                 "remaining contract lands at order date + the measured oil lead time")
        F.assume("open bulk POs are de-duplicated on po_number before differencing — "
                 "contract_qty is the PO header repeated on every truck line")
    if po_netted_l:
        F.assume(f"{po_netted_l:,.0f} L of open-contract balance was NOT booked a second time: "
                 "every open_bulk_pos line carries a GRPO number, so load_qty counts only "
                 "RECEIVED trucks, and the tankers already on the way (grpo_number null) are "
                 "still inside the undrawn balance. They are booked once, at their own ETA")

    # (d) packaging on order — the confirmed gap
    mp = ((inb or {}).get("month_pending") or [])
    if mp:
        F.warn(f"{len(mp)} gate entr(ies) have pending packaging POs, but "
               "factory_inbound.month_pending carries no item lines and no ordered/received "
               "quantity — packaging ON ORDER cannot be booked as arriving from state.json. "
               "The engine will re-order it from zero pipeline, so it lands later than reality.")
        F.assume("packaging already on order is MISSING from arrivals — month_pending has no "
                 "quantities to read; the plan re-orders it and books it at the packaging lead "
                 f"time ({lead.get('packaging')} days), which is pessimistic, not optimistic")
    prov("inbound", "factory_inbound + exim", f"{inb_mode} / {exim_mode}", inb_env,
         "QC-accepted lines + EXIM trucks on the way + the remaining open bulk contracts; "
         "anything already overdue is spread over the next 5 working days")
    recon["inbound"] = {"dates": len(inbound),
                        "cells": sum(len(v) for v in inbound.values()),
                        "by_src": counts, "qty_by_src": qty_by_src,
                        "exim_otw_l": otw_l, "po_lead_l": po_l, "qc_lines": qc_accepted}

    # ---------------------------------------------------------- lines -------
    # THE RULEBOOK'S table, keyed by the slots the rulebook names each line for. The live
    # ji.jivo.in configs are still read — but as a WATCH, published as lines_app_rated_now
    # and compared, never fed in (A01: the planning speed already carries the 80% and the
    # August cap, and the cap did not move when somebody retyped a rating).
    cfgs, cfg_mode = F.block("factory_production", prod, prod_mode, prod_env,
                             "line_configs", lambda v: isinstance(v, list) and bool(v))
    lines, lines_basis, lines_basis_kind, lines_speeds, lines_multi = build_lines_mark4(
        F, rb, cfgs, base)
    lines_app_now, lines_unslotted = app_rated_now(cfgs, F)
    if not cfgs:
        F.assume("ji.jivo.in's line configs were not readable this run, so the plan cannot "
                 "check the rulebook's ratings against what the app lists today — the "
                 "planning speeds are used unchanged either way")
    rating_moved = []
    for ln, slots in sorted(lines_app_now.items()):
        for slot, now in sorted(slots.items()):
            was = ((lines_speeds.get(ln) or {}).get("speeds") or {}).get(slot, {}).get("rated")
            if was is not None and abs(f(now) - f(was)) > 0.5:
                rating_moved.append(f"{ln} {slot} {f(was):g} -> {f(now):g}")
    if rating_moved:
        F.assume("the app's listed speed has changed since the rulebook was built ("
                 + "; ".join(rating_moved) + "); the plan keeps the rulebook's speed until "
                 "it is rebuilt (python3 reference/build_mark4_rulebook.py)")
    if lines_unslotted:
        F.warn("line configs whose name is neither a pack size nor a known machine, so they "
               "set no rating to compare: " + "; ".join(
                   f"{ln} {rows}" for ln, rows in lines_unslotted.items()))
    prov("lines", "reference/mark4-rulebook.json", "rulebook " + str(rb.get("version")), None,
         "PLANNING speeds (A01): min(80% x the app's rating, the best sustained August hour "
         "over at least 3 runs). Already post-efficiency — rules.efficiency is 1.0 and the "
         "engine refuses a rulebook run at anything else. The live ji.jivo.in ratings are "
         f"read for comparison only and published as lines_app_rated_now [{cfg_mode}]")
    recon["lines"] = {ln: {p: lines_basis[ln][p] for p in sorted(lines_basis[ln])}
                      for ln in sorted(lines_basis)}

    # ---------------------------------------------------------- rules -------
    rules = dict(base["rules"])
    rules["invoice_truck_lag_days"] = lag_days
    # R02/R03/R04 — the shift is the RULEBOOK's, not the loop's and not the plan sheet's.
    # 10 working hours a session, one line gets a second session, Sunday makes nothing.
    # Mark 3 ran 12 h because live/loop.sh exported it, which put 24 h on the line that
    # also took the night. No litre figure for that is quoted here: it moves with the
    # inputs (measured at +11% once and at a LOSS on 2026-09-06, because a storage-bound
    # month gives the hours back). The ruling is the reason, not the arithmetic.
    shift = rb.get("shift") or {}
    rules["shift_hours"] = shift.get("hours_per_session")
    rules["shift_hours_basis"] = shift.get("source")
    rules["sessions_per_day_max"] = shift.get("sessions_per_day_max")
    rules["night_lines_max"] = shift.get("night_lines_max")
    rules["sundays_off"] = shift.get("sundays_off")
    rules["working_days_basis"] = shift.get("working_days_basis")
    # A01 — THE DOUBLE-DERATE, closed. `lines` now holds PLANNING speeds, which are the
    # 80% and the August cap already applied; multiplying by 0.5 again ran the plant at
    # half and every check still passed.
    # The rate the engine falls back to for a plan row with no price of its own. It is
    # engine/august_sim.py's own DEF_R and it is worth about a crore and a half on the
    # month's sheet, so it is PUBLISHED rather than retyped a third time downstream.
    rules["default_realise_rs_per_l"] = DEF_R
    rules["efficiency"] = 1.0
    rules["efficiency_basis"] = (
        "planning speeds carry the 80% and the August cap (A01); the engine multiplies "
        "by 1.0. rules.efficiency 0.5 is a Mark 3 number and the engine refuses a "
        "rulebook run that carries it.")
    changeover = rb.get("changeover") or {}
    rules["line_clearance_min"] = f(changeover.get("clearance_min"),
                                    base["rules"]["line_clearance_min"])
    rules["flush_litres"] = f(changeover.get("flush_l_per_oil_change"),
                              base["rules"]["flush_litres"])
    rules["one_product_per_line_per_session"] = changeover.get("one_product_per_line_per_session")
    rules["changeover_rule"] = changeover.get("rule")
    # The engine takes ONE lag number and it must be the book it plans for. `lag_book` and
    # `lag_all_books_*` ride beside it so the site can show the merged gate without the
    # engine ever being fed it.
    rules["invoice_truck_lag_p90_days"] = out_lag["p90_days"]
    rules["invoice_truck_lag_book"] = out_lag["book"]
    rules["invoice_truck_lag_book_say"] = out_lag["book_say"]
    rules["invoice_truck_lag_all_books_days"] = out_lag["all_books"]["median_days"]
    rules["invoice_truck_lag_all_books_p90_days"] = out_lag["all_books"]["p90_days"]
    if lag_live:
        rules["invoice_truck_lag_basis"] = (
            f"measured daily off the gate log, {out_lag['rows']} dispatched "
            f"{'JIVO Oil ' if out_lag['book'] == PLAN_BOOK else ''}rows, {out_lag['window']}")
    else:
        rules["invoice_truck_lag_basis"] = (
            f"measured once by hand on {out_lag['measured_on']} "
            f"({out_lag['rows']} rows, {out_lag['window']}, all books merged) — "
            f"live/state/dispatch_lag.json is {lag_mode}")
    app_lines = ((prod or {}).get("lines") or [])
    app_hours = sorted({f(l.get("standard_hours_per_day")) for l in app_lines
                        if l.get("is_active") and f(l.get("standard_hours_per_day")) > 0})
    if app_hours:
        rules["standard_hours_per_day_app"] = app_hours if len(app_hours) > 1 else app_hours[0]
        rules["standard_hours_per_day_app_basis"] = (
            "ji.jivo.in's own standard hours per line. rules.shift_hours is the RULEBOOK's "
            "(R02: 10 hours a session, 20 for a day plus a night) and overrides this — the "
            "field is published so the two are not confused.")
    # THE CEILING IS A DECLARED FACT, NOT AN ASSUMPTION (Daman, 2026-09-04).
    # Mark 2 carried Daman's own capacity sheet as "assumed, never measured (Q2)" and
    # Mark 3 inherited the flag, so every "% of the godown" on the site was badged OUR
    # GUESS. Daman: "827,000 L godown = this is correct, no guess now." Q2 is closed.
    # It stays OUT of honesty.assumed — an owner's declared limit is not a guess the
    # engine made — and it is published as provenance instead, so the site can name
    # where the number came from without calling it an estimate.
    rules["storage_ceiling_l_basis"] = STORAGE_CEILING_BASIS
    rules["storage_peak_l_basis"] = STORAGE_CEILING_BASIS
    rules["storage_ceiling_declared"] = True
    rules["storage_ceiling_declared_by"] = STORAGE_CEILING_DECLARED_BY
    prov("storage_ceiling", "reference/STORAGE-CAPACITY.md", "declared", None,
         STORAGE_CEILING_BASIS)

    # --------------------------------------- the open dispatch book (R21/B09) --
    # Gurvinder's question, in his words: "for the open dispatch book, how many days of
    # pendency are there?" Days of work at the pace the gate has actually kept — the open
    # book divided by the mean of the last recorded days. Entirely ji.jivo.in (R01).
    # The two populations are NOT one: `open_l_all_books` is all three companies' open
    # dispatch plans, `oil_pile_l` is the Oil share the engine is actually given.
    hist_days = ((hist or {}).get("days") or [])
    dispatch_book = dispatch_pendency((disp or {}).get("invoiced_not_dispatched"),
                                      hist_days, standing)
    prov("dispatch_book", "factory_dispatch + factory_history", disp_mode, disp_env,
         dispatch_book["basis"])
    if dispatch_book["pendency_days_all"] is None:
        F.warn("days of pendency on the open dispatch book cannot be worked out this run — "
               + (dispatch_book["basis_missing"] or "the open book did not answer"))

    # ------------------------------------------------- money (R16/A12/B10) ---
    # R16: the plant is asked for a rupee figure a day against a floor and a target, and
    # A12 fixes the rate as `realise`. The COUNT is goods receipts, not the MES: the MES
    # sees about two-thirds of the plant and the receipts see the rest. Every rupee says
    # which rate priced it, so a default-rate share is visible instead of hidden in a total.
    money_rb = rb.get("money") or {}
    bl_rate = {}
    for code, sku in ((baseline or {}).get("skus") or {}).items():
        litres_m = f(sku.get("litres_per_month"))
        if litres_m > 0:
            bl_rate[code] = f(sku.get("inr_per_month")) / litres_m
    money_split = {"realise_rs": 0.0, "baseline_rs": 0.0, "default_rs": 0.0}
    money_unvalued = 0.0
    alias_booked_pcs = {}          # A10: production booked on the NEW carton code

    def value_of(code, pieces):
        """Pieces of one item code -> rupees, accumulating the rate split and A10 hits."""
        nonlocal money_unvalued
        rs, key, unvalued, c = price_pieces(code, pieces, plan, items, realise,
                                            sheet_realise_codes, bl_rate, ALIAS, DEF_R)
        if c != code and pieces:
            alias_booked_pcs[code] = alias_booked_pcs.get(code, 0.0) + pieces
        money_unvalued += unvalued
        if key:
            money_split[key] += rs
        return rs

    mtd_rs, mtd_days = 0.0, 0
    for d in hist_days:
        by_item = d.get("booked_by_item")
        if not isinstance(by_item, dict) or not by_item:
            continue
        mtd_days += 1
        for code, pcs in by_item.items():
            mtd_rs += value_of(code, f(pcs))
    # Snapshot BEFORE today is priced: mtd_by_basis has to split the month-to-date figure
    # beside it and nothing else, or the shares add up to more than the total they explain.
    mtd_split = dict(money_split)
    mtd_unvalued = money_unvalued
    booked_today = ((prod or {}).get("booked_today") or {})
    today_rs = 0.0
    for code, row in (booked_today.get("by_item") or {}).items():
        today_rs += value_of(code, f((row or {}).get("pcs")))
    today_split = {k: money_split[k] - mtd_split[k] for k in money_split}
    money = {
        "target_rs_per_day": money_rb.get("target_inr_per_day"),
        "floor_rs_per_day": money_rb.get("floor_inr_per_day"),
        "target_basis": money_rb.get("basis"),
        "mtd_made_rs": round(mtd_rs),
        "mtd_days": mtd_days,
        "mtd_basis": ("goods receipts per item for every day already gone this month "
                      "(ji.jivo.in, factory_history.booked_by_item), pieces x litres per "
                      "piece x realise. The MES sees about two-thirds of the plant; the "
                      "receipts see the rest, so this is the fuller count."),
        "mtd_by_basis": {k: round(v) for k, v in mtd_split.items()},
        "mtd_unvalued_pcs": round(mtd_unvalued),
        "today_booked_rs": round(today_rs),
        "today_booked_by_basis": {k: round(v) for k, v in today_split.items()},
        "today_booked_basis": booked_today.get("note"),
        "today_booked_pcs": booked_today.get("pcs"),
        "unvalued_pcs_total": round(money_unvalued),
    }
    if alias_booked_pcs:
        F.assume("the plant is booking production on the new 20-piece carton code — "
                 + ", ".join(f"{n} {p:,.0f} pieces this month" for n, p in sorted(alias_booked_pcs.items()))
                 + f" — and it is counted and valued as {', '.join(sorted(set(alias(n) for n in alias_booked_pcs)))}, "
                   "the product the plan sheet carries. The recipe is NOT changed: this "
                   "month's frozen BOM has no 20-piece carton item, so the plan still buys "
                   "the 16-piece one (A10/R20)")
    if money_unvalued:
        F.assume(f"{money_unvalued:,.0f} booked piece(s) this month are on codes with no pack "
                 "size this file can read, so the rupees made month-to-date are a FLOOR")
    if money_split["default_rs"] > 0:
        F.assume(f"₹{money_split['default_rs']:,.0f} of the month's production is priced at the "
                 f"engine's default ₹{DEF_R}/L — those codes have neither a May-Jul realise "
                 "rate nor three months of billing behind them (A12)")
    prov("money", "factory_history + factory_production", hist_mode, hist_env, money["mtd_basis"])

    # ------------------------------------------------------------ meta ------
    booked = ((prod or {}).get("booked_today") or {})
    meta = {
        "frozen": F.collected_at.isoformat(),
        "as_of": F.collected_at.isoformat(),
        "horizon": [today.isoformat(), d1.isoformat()],
        "month": today.strftime("%B %Y"),
        "rolling": True,
        "replanned_days": len(horizon_days),
        "working_days_left": len(working_days),
        "pieces_made_mtd": None,
        "pieces_made_mtd_basis": (
            "NOT NETTED OFF THE PLAN on this run. The pieces per item code for every day "
            "already gone this month now arrive with factory_history (out[\"history\"]) and "
            "are published as records; reducing the plan by them changes what the engine is "
            "asked to make, so it is a deliberate next step, not a side effect of reading "
            "them. Published as null rather than as a figure the plan beside it does not "
            "use. The engine does not read this field."),
        "pieces_booked_today": booked.get("pcs"),
        "pieces_booked_today_basis": booked.get("note"),
        "rule": ("A ROLLING RE-PLAN from a LIVE opening. Only the opening is observed; every "
                 "day after today is computed. Nothing past today has happened."),
        "generated_by": "live/freeze_live.py",
        "state_collected_at": F.state.get("collected_at"),
        "state_completed_at": F.state.get("completed_at"),
        # WS3 step 1 asks for it here by name. It is also at provenance.rulebook.version
        # and rulebook.version, so nothing was lost — but a consumer following the spec
        # read None, and this file refuses to run without a rulebook, so it is never null.
        "rulebook_version": rb.get("version"),
    }
    # Says the same thing as pieces_made_mtd_basis three lines above, because the
    # SITE renders this one and the two must not contradict each other. The month
    # window EXISTS now (factory_history publishes booked_by_item for every day
    # already gone); what has not happened is netting the plan by it, which is a
    # decision about what the engine is asked to make, not a missing read.
    F.assume("month-to-date production is not netted off the plan — what has already been made "
             "this month is read and shown as records, but the plan is not reduced by it on "
             "this run, so pieces_made_mtd is null")

    # ------------------------------------------------------- history --------
    # Never a die(): a month's records failing to read is a gap on one panel,
    # not a reason to refuse the whole plan.
    prov("history", "factory_history", hist_mode, hist_env,
         "the days already gone this month, read off ji.jivo.in — records, not the plan. "
         "Not used by the engine on this run.")
    if hist is None:
        F.warn("factory_history has no data this cycle — the days already gone cannot be shown")
    elif hist_mode != "live":
        F.assume("the days already gone are from a %s read, not this cycle's" % hist_mode)

    # ------------------------------------------------- rulebook_applied -----
    # Which rulings this run actually put into effect, and which fell back. The engine
    # adds its own flags to sim/summary-live.json and gen merges the two, so the
    # assumptions page ("Taken as fact", R26) can say per ruling whether the plan in front
    # of the reader was built with it — never "we intend to".
    rb["sku_pack"] = sku_pack                 # the sheet's rows plus anything derived here
    F.provenance["rulebook"] = {
        "source": os.path.relpath(RULEBOOK_PATH, JOLLY),
        "version": rb.get("version"), "written": rb.get("written"),
        "fetched_at": None, "server_at": None, "mode": "embedded",
        "note": ("generated by reference/build_mark4_rulebook.py — never hand-edited. Its "
                 "presence in these inputs is what makes the engine run rulebook mode."),
    }
    F.provenance["demand_baseline"] = {
        "source": out_baseline["path"], "fetched_at": out_baseline["fetched_at"],
        "server_at": None, "mode": bl_mode, "age_days": bl_age,
        "note": ("written daily by live/demand_baseline_sap.py — the ONE allowed SAP read "
                 "(reference/DEMAND-BASELINE-SOURCE.md). This file only reads it; a missing "
                 "or stale file falls back to the plan sheet's weekly buckets."),
    }
    channels = ", ".join((baseline or {}).get("channels_included") or [])
    rulebook_applied = {
        "A01": {"in_effect": True, "note": (
            "the machine speeds are the rulebook's PLANNING speeds and rules.efficiency is "
            "1.0, so nothing is derated twice")},
        "A09": {"in_effect": out_baseline["used_for_forecast"], "note": (
            f"expected orders are {want_months} months of outside billing, week-of-month "
            f"shaped, netted by the real trade book — {fc_rows:,} rows, "
            f"{out_baseline['expected_litres']:,} L" if out_baseline["used_for_forecast"]
            else f"expected orders fell back to the plan sheet's weekly buckets: "
                 f"{out_baseline['fallback_reason']}")},
        "A17": {"in_effect": out_baseline["used_for_forecast"], "note": (
            f"the outside channels counted are {channels}; e-commerce, branches, staff, cash "
            "sales and the inter-company cards are left out"
            if out_baseline["used_for_forecast"] else
            "no baseline this run, so no channel filter was applied")},
        "A18": {"in_effect": bool(nonplan["appended"]), "note": (
            f"{nonplan['appended']} sold-but-unplanned SKU(s) appended as expected-only plan "
            f"rows ({nonplan['appended_l_per_month']:,} L a month); "
            f"{len(nonplan['skipped'])} more ({nonplan['skipped_l_per_month']:,} L a month) "
            "could not be: they are named with their reason in demand_baseline.nonplan.skipped")},
        "A10": {"in_effect": bool(fg_alias_applied or alias_booked_pcs), "note": "; ".join(
            ([", ".join(f"{n} counted as {v['to']} ({v['pieces']:,} pieces of finished goods)"
                        for n, v in sorted(fg_alias_applied.items()))]
             if fg_alias_applied else
             ["no stock of the new carton code in the godown this cycle"])
            + ([", ".join(f"{n} booked {p:,.0f} pieces this month, valued as {alias(n)}"
                          for n, p in sorted(alias_booked_pcs.items()))]
               if alias_booked_pcs else []))},
        "R16": {"in_effect": True, "note": (
            f"target ₹{f(money['target_rs_per_day']):,.0f} a day, floor "
            f"₹{f(money['floor_rs_per_day']):,.0f}, both read from the rulebook; "
            f"₹{money['mtd_made_rs']:,} booked over {money['mtd_days']} day(s) so far")},
        "R21": {"in_effect": lag_live, "note": (
            f"the lag is measured daily off the gate log and the plan runs on JIVO OIL's own "
            f"— median {out_lag['median_days']} d, p90 {out_lag['p90_days']} d over "
            f"{out_lag['rows']} Oil rows ({out_lag['window']}); the merged all-books gate is "
            f"{out_lag['all_books']['median_days']} d / p90 "
            f"{out_lag['all_books']['p90_days']} d and is published beside it, not used"
            if lag_live and out_lag["book"] == PLAN_BOOK else
            f"the lag is measured daily off the gate log — median {out_lag['median_days']} d, "
            f"p90 {out_lag['p90_days']} d over {out_lag['rows']} rows ({out_lag['window']}); "
            f"this cycle's file carries no JIVO Oil row, so it is the merged gate"
            if lag_live else
            f"the lag is the one-off {out_lag['measured_on']} measurement, all books merged "
            f"— live/state/dispatch_lag.json is {lag_mode}")},
    }

    # --------------------------------------------------------- assemble -----
    opening = {
        "stock": stock,
        "fg": fg,
        "fg_litres": round(fg_plan_l + fg_other_l),
        "fg_plan_l": round(fg_plan_l),
        "fg_other_l": round(fg_other_l),
        # A10 — the new 20-piece carton code, counted as the planned product it is.
        "fg_alias_applied": fg_alias_applied,
        # What the engine eats.
        "standing_l": round(standing),
        # The 14-day bills window, INFORMATION ONLY — see provenance.standing_wide_14d.
        "standing_l_wide_14d": round(f(wide_oil_l)) if wide_oil_l is not None else None,
        "standing_l_alternatives": standing_alts,
        "oil_l": round(oil_l_total),
        "oil_mapped_l": round(mapped_l),
        "oil_unmapped_l": round(unmapped_l),
        "oil_unmapped": unmapped,
        "oil_absent_codes": absent,
        # The bulk position in two halves that are ADDED but published apart, and that
        # never overlap: oil_tank_l is EXIM's dip reading, oil_drum_l is the raw-material
        # store's figure for the oils EXIM has NO tank for. An oil is in exactly one of
        # them (ruled 2026-09-03: EXIM is the bulk-oil truth).
        "oil_tank_l": round(mapped_l),
        "oil_drum_l": round(drum_l),
        "oil_drum_by_code": {c: round(v) for c, v in sorted(drum_l_by_code.items())},
        "oil_drum_by_room": drum_by_room,
        # The SAP BOOK view of the same oil, for every code the raw-material rooms hold —
        # published for information, fed to the engine only where there is no tank.
        "oil_book_l": {c: round(v) for c, v in sorted(book_l_by_code.items())},
        "oil_book_total_l": round(sum(book_l_by_code.values())),
        "oil_book_superseded_l": round(sum(superseded.values())),
        "oil_book_l_note": (
            "What SAP's own warehouses say is in the raw-material rooms "
            + ", ".join(wh for wh in RM_ROOMS if wh in rm_rooms)
            + ", for the oils this month's recipes actually use. Everything else those "
              "rooms hold is in opening.rm_store_other in its own unit, so this is NOT the "
              "rooms' whole contents and must not be totalled as if it were. "
              "It is the LAGGING BOOK VIEW, not a second physical stock: for every oil "
              "EXIM has a tank for, this is the SAME oil written down a second time, and "
              "the book moves only after the tank does. GODOWNS.md says it plainly — 'bulk "
              "oil is not in SAP's godowns at all, it is in EXIM ... BH-LO and the tanks "
              "cannot be reconciled' — and EXIM's own sap-sync inventory shows BH-LO "
              "groundnut at exactly this file's book figure for that oil. Where EXIM has "
              "NO tank, this book figure IS what opening.stock uses, because it is the "
              "only figure there is. Added to the tanks it would have given 1.55 M L "
              "against a measured tank capacity of 1,351,500 L."),
        # Oils where EXIM has a tank AND the book has a figure: the tank won.
        "oil_in_tank_and_drum_codes": both,
        "rm_drums_unconverted": drums_unconverted,
        # Everything those rooms hold that is NOT an oil in this month's recipes —
        # rosemary leaf, walnut, ghee, a vitamin premix, 3,249 finished canola tins.
        # Counted nowhere, converted nowhere, and named here so nothing vanishes.
        "rm_store_other": rm_store_other,
        "rm_rooms_missing": rm_missing,
        "packaging_pieces": round(sum(v for k, v in stock.items() if k.startswith("PM"))),
        "packaging_by_room": pm_by_room,
        "packaging_rooms_missing": pm_missing,
        # The NON-MOVING exposure, badged. See honesty.assumed and provenance
        # .packaging_non_moving: BH-NM and GP-NM are COUNTED here, and GODOWNS.md calls
        # them "not available" one section below the table that allows them.
        "packaging_non_moving_rooms": list(nm_read),
        "packaging_non_moving_pcs": round(nm_total_pcs),
        "packaging_in_non_moving_rooms_pcs": round(nm_only_pcs),
        "packaging_only_in_non_moving_codes": len(nm_only),
        "packaging_only_in_non_moving": nm_only,
        "fg_nonplan_codes": len(fg_nonfg),
        # PM and RM rows DO turn up in the finished-goods rooms. They are reported, not
        # added to opening.stock: that comes from the packaging rooms, and adding a
        # second source of the same code would double-count it.
        "pm_in_fg_rooms_pieces": round(sum(q for c, q in fg_nonfg.items()
                                           if str(c).upper().startswith("PM"))),
        "pm_in_fg_rooms_codes": sorted(c for c in fg_nonfg if str(c).upper().startswith("PM")),
        "orders_nonplan_lines": oms_dropped_nonplan,
    }

    out = {
        "meta": meta,
        # Passed through untouched. The engine reads its inputs by name and never
        # sees this key; gen_live.py builds plan/history.json out of it.
        "history": {"data": hist, "mode": hist_mode, "env": hist_env},
        "opening": opening,
        "orders": orders,
        "backlog": backlog,
        "inbound_prebooked": inbound,
        "inbound_provenance": inb_prov,
        "lines": lines,
        "lines_basis": lines_basis,
        # The rulebook's own word for HOW each planning speed was arrived at — capped /
        # rated / typical / carried / derived. Published beside lines_basis so a consumer
        # can say "80% of its rating, capped at its best August hour" without re-deriving it.
        "lines_basis_kind": lines_basis_kind,
        # Everything behind each speed: the app rating, the August median / best / run
        # count, the planning figure, the prose basis and the structured planning_rule the
        # site's AC05 check recomputes — plus the slot -> bottle-family -> preference map.
        "lines_speeds": lines_speeds,
        # B19 — containers an hour for a SKU whose recipe holds more than one container,
        # on the lines that have a RECORD of filling one. The engine reads this instead of
        # `lines` for those SKUs and schedules them nowhere else.
        "lines_multi": lines_multi,
        # What Mark 3 fed the engine, kept for comparison. NOT used.
        "lines_carried_mark3": base["lines"],
        # What ji.jivo.in lists TODAY. Read, compared, published — never fed in (A01).
        "lines_app_rated_now": lines_app_now,
        "lines_unmapped_configs": lines_unslotted,
        "rules": rules,
        "actuals_for_scoring": {
            "made_l": 0, "made_pieces": 0, "skus": 0, "plan_pct": 0.0,
            "line_utilisation_pct": 0.0, "production_days": 0,
            "note": ("A rolling re-plan of the rest of the month. Nothing after today has "
                     "happened, so there is nothing to score it against."),
        },
        "honesty": {
            "measured": [
                "finished goods in BH-PF and BH-BT (ji.jivo.in, live, this cycle)",
                "packaging in " + ", ".join(wh for wh in PM_ROOMS if wh in pm_rooms)
                + " (ji.jivo.in, live)",
                "bulk oil in the EXIM tanks (manual daily dip reading)",
                "drummed oil in " + (", ".join(wh for wh in RM_ROOMS if wh in rm_rooms)
                                     or "no raw-material room this run")
                + " — counted only for the oils EXIM has no tank for",
                "the invoiced-but-not-trucked Oil pile (factory dispatch plans)",
                "the live OMS order book and the ecom open-PO book",
            ] + ([
                "three months of outside billing (SAP, read once a day into a file)"
            ] if out_baseline["used_for_forecast"] else []) + [
                ("the invoice-to-gate lag, measured daily off the gate log" if lag_live else
                 "the invoice-to-gate lag, measured once off the gate log"),
                "what the plant has already booked this month (ji.jivo.in goods receipts)",
                "BOMs, blends, realise May-Jul, and the monthly plan (carried)",
            ],
            "assumed": F.assumed,
            # Which mode each sentence above is true in. engine/august_sim.py reads this
            # and drops only what is tagged for the mode it is NOT running; a sentence
            # with no tag is "both" and survives. The engine does not republish the map.
            "assumed_modes": dict(F.assumed_modes),
        },
        # ------------------------------------------------- MARK 4 ------------
        # The rulebook, embedded WHOLE. Its presence is the switch: engine/august_sim.py
        # runs rulebook mode iff S["rulebook"] is there, and every legacy path (August,
        # -sep) is untouched because neither carries it.
        "rulebook": rb,
        "rulebook_applied": rulebook_applied,
        # A10 — {new code: the planned code it is}. The site says "running now: FG0000461,
        # which is FG0000142's product" instead of a code nobody's plan has heard of.
        "plan_code_aliases": ALIAS,
        "demand_baseline": out_baseline,
        "lag": out_lag,
        "dispatch_book": dispatch_book,
        "money": money,
        "provenance": F.provenance,
        "warnings": F.warnings,
        # carried verbatim — BOM and master data, not a live position
        "plan": plan_rows,
        "bom": bom,
        "blends": blends,
        "items": items,
        "realise": realise,
        "people": base.get("people", []),
    }
    return F, out, recon


# ------------------------------------------------------------- forecast -----
def load_weekly_buckets(F):
    """{code: {"w1..w4": litres, "ecom": litres}} from EXIM's uploaded plan sheet."""
    path = os.path.join(STATE_DIR, "exim.plan.json")
    try:
        rows = (load(path).get("plan") or {}).get("rows") or []
    except (OSError, ValueError):
        F.assume("EXIM's weekly plan buckets were not readable, so the forecast is spread "
                 "evenly across the working days left instead of by week")
        return {}
    out = {}
    for r in rows:
        code = r.get("code")
        if not code:
            continue
        rec = out.setdefault(code, {"w1": 0.0, "w2": 0.0, "w3": 0.0, "w4": 0.0, "ecom": 0.0})
        for w in ("w1", "w2", "w3", "w4"):
            rec[w] += f(r.get(f"commodity_{w}")) + f(r.get(f"premium_{w}"))
        rec["ecom"] += f(r.get("ecom_planning"))
    return out


def week_of_month(d: date) -> int:
    return min(4, (d.day - 1) // 7 + 1)


def forecast_profile(code, weekly, working_days, today, F):
    """{date: share} summing to 1 — how this code's remaining plan lands over the month.

    EXIM buckets the TRADE half of the plan into four weeks and leaves the ecom half
    un-bucketed. A week whose days are all behind us has not been cancelled — the
    month's target did not shrink — so its share moves onto the days that are left.
    """
    if not working_days:
        return {}
    rec = weekly.get(code)
    if not rec or (rec["w1"] + rec["w2"] + rec["w3"] + rec["w4"] + rec["ecom"]) <= 0:
        share = 1.0 / len(working_days)
        F.assume("the forecast for codes with no weekly split in EXIM's sheet is spread evenly "
                 "across the working days left")
        return {d: share for d in working_days}
    weights = {d: 0.0 for d in working_days}
    spare = 0.0
    for w in (1, 2, 3, 4):
        lit = rec[f"w{w}"]
        if lit <= 0:
            continue
        days = [d for d in working_days if week_of_month(d) == w]
        if not days:
            spare += lit                               # that week is behind us — carry it on
            continue
        for d in days:
            weights[d] += lit / len(days)
    for d in working_days:                             # ecom half + any week already gone
        weights[d] += (rec["ecom"] + spare) / len(working_days)
    if rec["ecom"] > 0:
        F.assume("EXIM gives the ecom half of the plan no weekly split, so it is spread evenly "
                 "across the working days left (Mark 2's rule, kept)")
    if spare > 0:
        F.assume("plan weeks that are already behind us are not cancelled — their volume moves "
                 "onto the working days that are left, so the month's target does not shrink")
    tot = sum(weights.values())
    return {d: w / tot for d, w in weights.items() if w > 0} if tot > 0 else {}


# ------------------------------------------------- the demand baseline (R17) -
# THE RULING (R17/R18, meeting 10:19-11:02, Daman 2026-09-06): never plan from POs
# alone. GT/MT bunches its orders into the last days of the month — the baseline
# measures 134,695 L a day in days 29-31 against 20,317 in days 1-7 — so a PO-only
# plan is empty at month end and the buffer runs dry. Expected orders come from three
# months of OUTSIDE billing per SKU, week-of-month shaped, netted by the real OMS book.
#
# The numbers come out of live/state/demand_baseline.json, which a DAILY cron writes
# (live/demand_baseline_sap.py, the one allowed SAP read). This file only reads it.
def baseline_shape(sku, pooled, months):
    """({1..5: share}, "own" | "pooled") — how this SKU's month is distributed.

    A SKU's OWN week shape is only usable when it sold in EVERY month of the window: one
    month of history through five buckets is a shape of one sale, and it would put the
    whole year on whichever week that sale happened to fall in. Everything else takes the
    pooled shape — the same bunching, measured across the whole book (A09).
    """
    own = sku.get("by_week") or {}
    tot = sum(f(v) for v in own.values())
    if int(f(sku.get("months_seen"))) >= months and tot > 0:
        return {w: f(own.get(str(w))) / tot for w in range(1, 6)}, "own"
    return {w: f((pooled.get(str(w)) or {}).get("share")) for w in range(1, 6)}, "pooled"


def expected_stream(baseline, plan, today, last_day, oms_pieces, months, realise, def_r):
    """The FORECAST rows the billing baseline implies for the rest of the month.

    Returns (rows, stats). PURE: no state, no clock, no I/O — the shaping is the part
    that has to be testable, and the netting rule is the part that gets argued about.

    Per SKU: monthly litres x its week-of-month share, divided by the CALENDAR days that
    bucket has in THIS month, summed over the days still to come. Then netted by the real
    OMS pieces already on the book for the same SKU (floored at zero — an over-ordered SKU
    does not create negative demand), and the remainder spread back over the same days in
    the same proportion. **e-com is never netted** (R18): its POs are its own stream and
    the baseline excluded e-commerce billing in the first place, so subtracting one from
    the other would take the same litres out twice.
    """
    days = [today + timedelta(days=i) for i in range((last_day - today).days + 1)]
    first = today.replace(day=1)
    # The bucket's CALENDAR days in this month, not the days still left in it: the share
    # is a share of the whole bucket, so dividing it by a shrinking denominator would
    # inflate the daily rate every time the month got shorter.
    bucket_days = {}
    for i in range((month_end(first) - first).days + 1):
        w = week_of_month5(first + timedelta(days=i))
        bucket_days[w] = bucket_days.get(w, 0) + 1
    pooled = baseline.get("week_of_month") or {}
    rows = []
    stats = {"rows": 0, "litres": 0.0, "skus": 0, "netted_oms_pieces": 0.0,
             "dropped_subpiece_l": 0.0, "negative_slice_l": 0.0,
             "sku_shape_own": 0, "sku_shape_pooled": 0,
             "skus_known_not_planned": 0}
    for code, sku in sorted((baseline.get("skus") or {}).items()):
        if code not in plan:
            stats["skus_known_not_planned"] += 1
            continue
        monthly = f(sku.get("litres_per_month"))
        if monthly <= 0:
            continue
        share, kind = baseline_shape(sku, pooled, months)
        stats["sku_shape_own" if kind == "own" else "sku_shape_pooled"] += 1
        per_day = {}
        for d in days:
            n = bucket_days.get(week_of_month5(d), 0)
            if n:
                per_day[d] = monthly * share.get(week_of_month5(d), 0.0) / n
        total = sum(per_day.values())
        if total <= 0:
            continue
        lpp = f(plan[code]["litres_per_piece"], 1.0) or 1.0
        booked_l = f(oms_pieces.get(code)) * lpp
        net = max(0.0, total - booked_l)
        stats["netted_oms_pieces"] += min(booked_l, total) / lpp
        if net <= 0:
            continue
        stats["skus"] += 1
        rate = f(realise.get(code), def_r)
        for d, weight in per_day.items():
            litres = net * weight / total
            pieces = litres / lpp
            if litres < 0:
                # A week bucket whose three months carry net RETURNS gives a NEGATIVE day
                # slice. It is dropped like a sub-bottle slice — a negative order is not an
                # order — but it is not one, and putting it in that counter published
                # `dropped_subpiece_l: -2,734`, a negative count of dropped litres that
                # reads as a bug on the site. Two different facts, two counters.
                stats["negative_slice_l"] += litres
                continue
            if pieces < 1:
                stats["dropped_subpiece_l"] += litres    # too small to be one bottle
                continue
            rows.append({"docnum": f"FCST-W{week_of_month5(d)}-{code}", "date": d.isoformat(),
                         "due": d.isoformat(), "customer": FORECAST_CUSTOMER, "code": code,
                         "pieces": pieces, "value": pieces * lpp * rate,
                         "channel": "FORECAST", "_src": "FORECAST",
                         "basis": FORECAST_BASIS_BILLING})
            stats["rows"] += 1
            stats["litres"] += litres
    return rows, stats


def select_lag(lag_file, lag_mode, lag_age, lag_at, lag_note, carried_days):
    """The invoice-to-gate lag and where it came from. Returns (days, block, live, say).

    R21 wants it measured daily. live/dispatch_lag.py does that off the gate log; when its
    file is fresh this uses it, and when it is not, the plan falls back to
    factory_dispatch.LAG_NOTE — ONE measurement, taken by hand on 2026-09-03 off page 1 of
    4. The fallback is a real number that gets a day older every day, so `static` and the
    sentence are not decoration: they are how anybody reading the plan knows which it is.

    THE BOOK THE PLAN RUNS ON IS OIL, not the merged gate (fixed 2026-09-06). This engine
    plans one company: JIVO Oil. It reads the Oil pile, it bills Oil litres, and the lag it
    is given decides how long each of those litres sits in the godown before a truck takes
    it away. Up to now it was handed `all` — the merged three-book gate — and dispatch_lag.py
    says in its own docstring that the three books are NOT one population:
    `by_company.JIVO_OIL` is the plan's lag, `all` is published beside it because the gate is
    one gate. CLAUDE.md says the same in the other direction: "Dispatch litres are three
    companies — Oil is the split, never the merged headline."

    The merged figure is 2 days / p90 9; Oil's is 3 days / p90 11. The plan opens at 100% of
    the declared godown ceiling, so a day of lag is a day of headroom, and the merged number
    was buying the plan a day of storage that JIVO Oil's own gate log does not give it.
    Beverages is 313 of the 551 rows and turns its trucks fastest, so the merged median was
    mostly a Beverages measurement being spent on Oil stock.

    `all` is not dropped. It is published beside the plan's lag as `all_books`, and `book`
    names which one the plan ran on, so the page can show both and say which is which.
    """
    stats_of = lambda s: {"median_days": (s or {}).get("median_days"),
                          "p90_days": (s or {}).get("p90_days"),
                          "max_days": (s or {}).get("max_days"),
                          "mean_days": (s or {}).get("mean_days"),
                          "rows": (s or {}).get("n")}
    fresh = (lag_file or {}) if lag_mode == "fresh" else {}
    by_company = fresh.get("by_company") or {}
    all_stats = fresh.get("all") or {}
    oil_stats = by_company.get(PLAN_BOOK) or {}
    # Oil first; the merged gate only if this cycle's file carries no Oil rows at all.
    plan_stats = oil_stats if oil_stats.get("median_days") is not None else all_stats
    plan_book = PLAN_BOOK if plan_stats is oil_stats else "ALL_BOOKS"
    if plan_stats.get("median_days") is not None:
        window = (fresh.get("window") or {})
        block = dict(stats_of(plan_stats))
        block.update({
            "book": plan_book,
            "book_say": ("JIVO Oil's own gate rows — the book this plan makes for"
                         if plan_book == PLAN_BOOK else
                         "all three books merged, because this cycle's gate log carries no "
                         "JIVO Oil row to measure"),
            "all_books": dict(stats_of(all_stats)),
            "window": f"{window.get('from')}..{window.get('to')}",
            "measured_on": fresh.get("measured_on") or lag_at,
            "by_company": by_company,
            "source": "live/state/dispatch_lag.json (ji.jivo.in gate log, measured daily)",
            "static": False, "age_days": lag_age,
            "method": fresh.get("method"), "caveat": fresh.get("caveat"),
        })
        days = int(round(f(block["median_days"])))
        merged = block["all_books"]
        beside = ""
        if merged.get("median_days") is not None and plan_book == PLAN_BOOK:
            beside = (f". The merged all-books gate is {merged['median_days']} d median / "
                      f"p90 {merged['p90_days']} d over {merged['rows']} rows — published "
                      "beside it, NOT what the plan runs on: the three books are not one "
                      "queue and this plan makes Oil")
        return days, block, True, (
            f"the {days}-day invoice-to-gate lag is measured DAILY off the gate log and is "
            f"JIVO OIL's own ({block['rows']} dispatched Oil rows, {block['window']}); the "
            f"p90 is {block['p90_days']} days and the tail runs to {block['max_days']} — the "
            f"plan uses the median and ignores the tail{beside}"
            if plan_book == PLAN_BOOK else
            f"the {days}-day invoice-to-gate lag is measured DAILY off the gate log, but this "
            f"cycle's file carries NO JIVO Oil row, so it is the merged all-books gate "
            f"({block['rows']} rows, {block['window']}) standing in for Oil's own")
    note = lag_note or {}
    days = note.get("median_days")
    days = carried_days if days is None else int(days)
    block = {
        "median_days": note.get("median_days"), "p90_days": note.get("p90_days"),
        "max_days": note.get("max_days"), "mean_days": note.get("mean_days"),
        "rows": note.get("rows"), "window": note.get("measured_window"),
        "measured_on": note.get("measured_on"), "by_company": {},
        "book": "ALL_BOOKS", "all_books": stats_of(None),
        "book_say": ("the one-off hand measurement was never split by book, so it is all "
                     "three merged standing in for Oil's own"),
        "source": "factory_dispatch.LAG_NOTE (measured once, by hand)",
        "static": True, "age_days": lag_age,
        "method": note.get("method"), "caveat": note.get("caveat"),
    }
    return days, block, False, (
        f"the invoice-to-gate lag is the one-off {note.get('measured_on') or '3 Sep'} "
        f"measurement, all three books merged and never split — "
        f"live/state/dispatch_lag.json is {lag_mode}; run live/dispatch_lag.py "
        "(a DAILY job, never in the 3-minute loop) to measure it off the last 30 days of the "
        "gate log and get JIVO Oil's own (R21)")


def dispatch_pendency(ind, hist_days, standing_l):
    """How many days of work the open dispatch book is (R21/B09).

    Gurvinder's question in his own words. The open book divided by the pace the gate has
    actually kept over the last recorded days — every figure from ji.jivo.in (R01). NULL
    with a reason when no day has a gate figure yet: a plant that has dispatched nothing on
    record has an INFINITE pendency, not a zero one, and publishing 0 would read as "clear".
    The three books are NOT one queue, so the Oil line uses the Oil pile and the Oil pace.
    """
    ind = ind or {}
    rec_all = [f(d["dispatched_all_l"]) for d in (hist_days or [])
               if d.get("dispatched_all_l") is not None][-7:]
    rec_oil = [f(d["dispatched_oil_l"]) for d in (hist_days or [])
               if d.get("dispatched_oil_l") is not None][-7:]
    daily_all = (sum(rec_all) / len(rec_all)) if rec_all else None
    daily_oil = (sum(rec_oil) / len(rec_oil)) if rec_oil else None
    open_all = f(ind.get("litres")) if ind.get("litres") is not None else None
    return {
        "open_l_all_books": round(open_all) if open_all is not None else None,
        "open_bills": ind.get("bills"),
        "oil_pile_l": round(f(standing_l)),
        "trailing_days": len(rec_all),
        "trailing_daily_all_l": round(daily_all) if daily_all else None,
        "trailing_daily_oil_l": round(daily_oil) if daily_oil else None,
        "pendency_days_all": (round(open_all / daily_all, 1)
                              if (open_all is not None and daily_all) else None),
        "pendency_days_oil": (round(f(standing_l) / daily_oil, 1) if daily_oil else None),
        "basis": (
            "open dispatch plans from ji.jivo.in (dispatch-plans dispatch-fulfilment-summary, "
            "PENDING + BOOKED, all three books) divided by the mean litres the gate actually "
            f"passed over the last {len(rec_all)} recorded day(s) (factory_history). The Oil "
            "line uses the Oil pile the engine is given and the Oil gate figure — the three "
            "books are not one queue."),
        "basis_missing": (None if rec_all else
                          "no day already gone this month carries a gate figure yet, so days "
                          "of pendency cannot be worked out — factory_history is HOURLY and a "
                          "cold box fills it in over the first hours"),
    }


def price_pieces(code, pieces, plan, items, realise, sheet_codes, bl_rate, aliases, def_r):
    """(rupees, which_rate, unvalued_pieces, planned_code) for one item code's pieces.

    A12 fixes the rate as `realise`. Three rates in order, and WHICH one is published
    rather than folded into a total: the plan sheet's own May-Jul realise, then the SKU's
    ₹/L out of three months of billing, then the engine's default. A10 is applied first —
    the new 20-piece carton code is the planned product, priced as the planned product.
    """
    c = aliases.get(code, code)
    if c in plan:
        lpp = f(plan[c].get("litres_per_piece"))
    else:
        lpp = f(pack_litres(((items.get(c) or {}).get("name")) or "")[0])
    if lpp <= 0:
        return 0.0, None, pieces, c
    if c in sheet_codes:
        rate, key = f(realise.get(c), def_r), "realise_rs"
    elif c in bl_rate:
        rate, key = f(bl_rate[c]), "baseline_rs"
    else:
        rate, key = def_r, "default_rs"
    return pieces * lpp * rate, key, 0.0, c


def expected_only_rows(baseline, plan, bom, items, oils, realise):
    """A18 — SKUs the plant SELLS that the plan sheet never mentions, as pieces-0 rows.

    27% of the outside litres in the baseline (844,054 L over three months) are on codes
    the September sheet does not carry. Ignoring them plans a month that cannot serve a
    quarter of its own demand. Inventing them is worse, so a row is appended ONLY when
    the engine could actually build it: SAP's own BOM names it, that BOM names an oil, and
    engine/pack_class.py can say which pack and which bottle it is. A drum is out by R14 —
    it is filled by hand, not scheduled. Everything else is published, by name and with
    the reason, in `nonplan.skipped`: demand the plan cannot place is still demand.

    Returns (rows, packs, nonplan). `rows` are plan rows, `packs` their sku_pack entries.
    """
    def oil_of(code):
        o = [(c, per) for c, per in bom.get(code, []) if c in oils]
        return max(o, key=lambda x: x[1])[0] if o else None

    rows, packs, skipped = [], {}, []
    for code, sku in sorted((baseline.get("skus") or {}).items()):
        if code in plan:
            continue
        name = str(sku.get("name") or code)
        if code not in bom:
            skipped.append({"code": code, "name": name, "reason": "no BOM",
                            "litres_per_month": round(f(sku.get("litres_per_month")))})
            continue
        if oil_of(code) is None:
            skipped.append({"code": code, "name": name, "reason": "no oil in BOM",
                            "litres_per_month": round(f(sku.get("litres_per_month")))})
            continue
        pc = pack_class(code, bom, items, f(sku.get("litres_per_piece")) or None, "")
        if pc["slot"] is None or pc["family"] == "UNKNOWN":
            skipped.append({"code": code, "name": name, "reason": "pack not classed",
                            "litres_per_month": round(f(sku.get("litres_per_month")))})
            continue
        if pc["slot"] == "DRUM":
            skipped.append({"code": code, "name": name, "reason": "drum — filled by hand (R14)",
                            "litres_per_month": round(f(sku.get("litres_per_month")))})
            continue
        head = str(sku.get("type") or "").upper()
        rows.append({
            "code": code, "sku": name,
            "head": head if head in ("PREMIUM", "COMMODITY") else "OTHER",
            "category": sku.get("sub_group") or "",
            "pack_type": ("TIN" if pc["family"] == "TIN" else
                          "POUCH" if pc["slot"] == "POUCH" else "PET"),
            "litres_per_piece": f(sku.get("litres_per_piece"), 1.0) or 1.0,
            "pieces": 0, "litres": 0.0,
            "expected_only": True, "source": "demand_baseline A18",
            "trailing_l_per_month": round(f(sku.get("litres_per_month"))),
        })
        packs[code] = dict(sku=name, litres_per_piece=f(sku.get("litres_per_piece")),
                           sheet_pack_type=None, derived_by="freeze", **pc)
        if code not in realise:
            monthly_l = f(sku.get("litres_per_month"))
            if monthly_l > 0:
                realise[code] = round(f(sku.get("inr_per_month")) / monthly_l, 2)
    nonplan = {"candidates": len(skipped) + len(rows), "appended": len(rows),
               "appended_l_per_month": round(sum(r["trailing_l_per_month"] for r in rows)),
               "skipped": skipped,
               "skipped_l_per_month": round(sum(s["litres_per_month"] for s in skipped))}
    return rows, packs, nonplan


# ---------------------------------------------------------------- lines -----
# ji.jivo.in's line configs are keyed by PACK SIZE, not by SKU: every row measured
# 2026-09-03 carries sku_code "" and a config_name of "1 LTR" / "5 LTR" / "Hitech".
# So the join to the engine's pack slots is on config_name, with the per-SKU path
# kept for the day sku_code starts being filled in.
PARALLEL_MACHINE_LINES = {
    # reference/PLAN-AND-LINES.md: "Pouch Machine — Hitech 1,800 · Samarpan 2,400".
    # Two machines side by side under one line name, so their configs are named after
    # the MACHINE and not a pack size, and the line's throughput is their SUM (4,200),
    # never the median of the two.
    "Pouch Machine": "POUCH",
}


def config_slot(name):
    """'5 LTR' -> '5L', 'POUCH ...' -> 'POUCH', 'Hitech' -> None (a machine, not a size)."""
    n = str(name or "").upper()
    for kw in ("POUCH", "TIN", "DRUM"):
        if kw in n:
            return kw if kw != "POUCH" else "POUCH"
    lit, _basis = pack_litres(n)
    if not lit:
        return None
    for cap, slot in ((1.05, "1L"), (2.05, "2L"), (3.05, "3L"), (4.05, "4L"), (5.05, "5L")):
        if lit <= cap:
            return slot
    return "15L"


# slot_of() and build_lines() USED TO LIVE HERE — the Mark 3 line table: the engine's
# legacy slot vocabulary reproduced by hand, and a rate chosen per (line, pack) from
# MEASURED_RATES / the app's rating / the carried August table, all PRE-efficiency for
# the engine to derate by 0.5.
#
# Both are gone (Mark 4, 2026-09-06). The rulebook is not optional in this file — a
# missing one REFUSES — so neither could ever run again, and the only thing they still
# did that nothing else does was write the two honesty sentences the engine now has to
# strip ("the engine then derates everything by 50% again", "the engine applies
# rules.efficiency (0.5) on top of it"). A dead path whose distinctive behaviour is
# publishing a false sentence about the plan beside it is not a fallback worth keeping.
# The R15 replacement for slot_of() is engine/pack_class.py, which is the ONE
# implementation of "which pack is this"; build_lines_mark4() is the line table.
# git log this file for the code.


def app_rated_now(cfgs, F):
    """{line: {slot: rated}} — what ji.jivo.in lists TODAY, in the rulebook's vocabulary.

    Published, never fed in. The rulebook's planning speeds were built against the config
    dump of 2026-09-06 (reference/app-line-configs-2026-09-06.json); if somebody retypes a
    rating tomorrow the plan must not silently move with it, because the August cap that
    sits on top of the rating did not move. So the live rating is carried beside the
    planning speed and any disagreement is said out loud — the fix is to rebuild the
    rulebook, not to let the freeze drift.
    """
    rated, unslotted = {}, {}
    for c in (cfgs or []):
        if not c.get("is_active"):
            continue
        ln, speed = c.get("line_name"), f(c.get("rated_speed"))
        if not ln or speed <= 0:
            continue
        slot = config_slot(c.get("config_name"))
        if slot:
            rated.setdefault(ln, {}).setdefault(slot, []).append(speed)
        else:
            unslotted.setdefault(ln, []).append((c.get("config_name"), speed))
    for ln, slot in PARALLEL_MACHINE_LINES.items():           # Pouch = two machines, SUMMED
        rows = unslotted.get(ln)
        if rows and slot not in rated.get(ln, {}):
            rated.setdefault(ln, {})[slot] = [sum(sp for _n, sp in rows)]
            unslotted.pop(ln, None)
    out = {}
    for ln, slots in rated.items():
        out[ln] = {}
        for slot, vals in slots.items():
            vals = sorted(vals)
            out[ln][slot] = vals[len(vals) // 2]              # median of that slot's configs
    return out, {ln: [n for n, _s in rows] for ln, rows in unslotted.items()}


def build_lines_mark4(F, rb, cfgs, base):
    """`lines` from the RULEBOOK's planning speeds (A01) — the Mark 4 line table.

    Two things change and both are traps Mark 3 walked into:

    1. THE KEYS. `lines[line][slot]` now holds exactly the slots the rulebook names that
       line for — Tin Head carries 15L / 3L / 5L and NOTHING carries a 15 L key it was not
       given (AC02). Mark 3 keyed the Tin Head "TIN", one bucket for every tin from 3 L to
       15 kg, and then let engine/august_sim.py DERIVE a 15 L rate as the 5 L slot / 3 on
       every line that had a 5 L head — which is how a 15-litre tin came to be planned on
       Clear Pack.
    2. THE NUMBER. A planning speed is POST-efficiency: min(80% x the app's rating, the
       best sustained August hour over at least three runs). `rules.efficiency` is
       therefore 1.0 and the engine refuses to run a rulebook at anything else — storing
       these speeds under the old 0.5 would derate them a second time and plan the plant
       at half (2.01 M L instead of 3.19 M).

    A slot with no planning speed is SKIPPED, not guessed: Clear Pack 2 L and 6 Head 3 L
    have no rating and no August run, and the rulebook says so in as many words
    ("NO RATE — needs a ruling"). The engine reads a missing rate as "this machine cannot
    fill this pack", which is the truthful reading until somebody rules on it.
    """
    lines, basis, kinds, speeds, multi = {}, {}, {}, {}, {}
    no_rate = []
    for ln, spec in (rb.get("lines") or {}).items():
        blocks = spec.get("speeds") or {}
        speeds[ln] = {"app_line_id": spec.get("app_line_id"), "slots": spec.get("slots") or {},
                      "notes": spec.get("notes") or [], "speeds": blocks,
                      "speeds_multi": spec.get("speeds_multi") or {},
                      "aug_litres_by_slot": spec.get("aug_litres_by_slot") or {}}
        for slot, sp in blocks.items():
            planning = sp.get("planning")
            if planning is None:
                no_rate.append(f"{ln} {slot}")
                continue
            lines.setdefault(ln, {})[slot] = f(planning)
            basis.setdefault(ln, {})[slot] = "planning"
            kinds.setdefault(ln, {})[slot] = (sp.get("planning_rule") or {}).get("kind")
        # B19 — a SKU whose recipe holds more than one container fills at the COMBO rate,
        # on the lines that have a record of running one. The engine reads this table
        # instead of `lines` for those SKUs and will not schedule them anywhere else.
        for slot, sp in (spec.get("speeds_multi") or {}).items():
            if sp.get("planning") is not None:
                multi.setdefault(ln, {})[slot] = f(sp["planning"])
    if no_rate:
        F.assume("these machine-and-pack pairs have no planning speed in the rulebook — no "
                 "app rating and no August run — so the plan treats them as pairs the plant "
                 "cannot run, rather than inventing a rate: " + ", ".join(sorted(no_rate)))
    F.assume("each machine is planned at the rulebook's PLANNING speed, which is already "
             f"{f((rb.get('efficiency') or {}).get('planning_factor'), 0.8) * 100:.0f}% of "
             "its listed rating and never faster than the best hour it held in August — so "
             "the plan multiplies it by 1.0 and cuts it no further (A01)")
    return lines, basis, kinds, speeds, multi


# ------------------------------------------------------------ reconcile -----
def reconcile(F, out, recon, path):
    L = []
    a = L.append
    m = out["meta"]
    op = out["opening"]
    a("=" * 78)
    a(f"  FREEZE LIVE — {m['month']}   horizon {m['horizon'][0]} -> {m['horizon'][1]}"
      f"   ({m['replanned_days']} days, {m['working_days_left']} working)")
    a(f"  state collected {m['state_collected_at']}   ->  {path}")
    a("=" * 78)
    r = recon["fg"]
    a(f"  OPENING FG        {r['pieces']:>14,.0f} pieces over {r['codes']} codes   [{r['mode']}]")
    a(f"     plan codes     {r['plan_l']:>14,.0f} L        other FG {r['other_l']:>12,.0f} L")
    r = recon["pm"]
    a(f"  PACKAGING         {r['pieces']:>14,.0f} pieces over {r['codes']} codes   [{r['mode']}]")
    for wh, rm_ in r["rooms"].items():
        a(f"     {wh:<14}{rm_['pieces']:>14,.0f} pieces over {rm_['codes']} codes  "
          f"[{rm_['mode']}]")
    if r["missing"]:
        a(f"     NOT READ       {', '.join(r['missing'])}  <- not yet read, NOT empty; "
          "packaging is a FLOOR by whatever they hold")
    if op["packaging_non_moving_rooms"]:
        a(f"     NON-MOVING     {op['packaging_non_moving_pcs']:>14,.0f} pieces in "
          f"{', '.join(op['packaging_non_moving_rooms'])} — COUNTED as available (badged)")
        a(f"       only there   {op['packaging_only_in_non_moving_codes']:>12} recipe codes"
          f" / {op['packaging_in_non_moving_rooms_pcs']:,.0f} pcs would vanish if "
          "'non-moving' means unusable")
        if op["packaging_only_in_non_moving"]:
            a("       biggest      " + ", ".join(
                f"{x['code']} {x['pieces']:,}" for x in op["packaging_only_in_non_moving"][:4]))
    r = recon["oil"]
    a(f"  BULK OIL (tanks)  {r['total_l']:>14,.0f} L in {r['tanks']} tanks          [{r['mode']}]")
    a(f"     mapped         {r['mapped_l']:>14,.0f} L -> {r['codes']} RM codes")
    a(f"     UNMAPPED       {r['unmapped_l']:>14,.0f} L" +
      ("   <- named in opening.oil_unmapped" if r["unmapped_l"] else ""))
    # codes vs rows: a synonym ruling collapses two room rows into one canonical code
    # (RM0000066 peanut -> RM0000011 groundnut), so the room rows can outnumber the codes.
    a(f"  DRUMMED OIL (RM store){r['drum_l']:>10,.0f} L over {r['drum_codes']} tank-less "
      "codes  <- COUNTED")
    for wh, rm_ in r["drum_rooms"].items():
        a(f"     {wh:<14}{rm_['litres']:>14,.0f} L over {rm_['codes']} rows  [{rm_['mode']}]")
    if r["drum_missing"]:
        a(f"     NOT READ       {', '.join(r['drum_missing'])}  <- not yet read, NOT empty")
    if r["unconverted"]:
        a(f"     NOT CONVERTED  {r['unconverted']} plan-oil code(s) held in pieces with no "
          "litres <- opening.rm_drums_unconverted")
    if r["store_other"]:
        a(f"     NOT AN OIL     {r['store_other']} code(s) in those rooms are not in this "
          "month's recipes <- opening.rm_store_other, counted nowhere")
    a(f"  SAP BOOK (RM store) {r['book_l']:>12,.0f} L over {r['book_codes']} codes   "
      "<- INFORMATION ONLY, the lagging book view")
    if r["both_codes"]:
        a(f"     tank WINS      {r['superseded_l']:>14,.0f} L of book set aside for "
          f"{', '.join(r['both_codes'])}")
        a("                    EXIM is the bulk-oil truth (ruled 2026-09-03) — the tank "
          "and the book are the SAME oil, never added")
    if op["oil_absent_codes"]:
        a(f"     no tank, no book {', '.join(op['oil_absent_codes'])}")
    a(f"  BULK OIL FED IN   {(r['mapped_l'] + r['drum_l']):>14,.0f} L  = tanks "
      f"{r['mapped_l']:,.0f} + tank-less store {r['drum_l']:,.0f}")
    r = recon["standing"]
    a(f"  INVOICED, NOT GONE{r['litres']:>14,.0f} L  = {r['pct']:.0f}% of the "
      f"{r['ceiling_l']:,.0f} L DECLARED ceiling  [{r['mode']}]  <- FED TO THE ENGINE")
    if r["cheap_l"] is not None:
        a(f"     cheap backlog  {r['cheap_l']:>14,.0f} L all three books"
          + (f"  x Oil share {r['share'] * 100:.1f}%" if r["share"] is not None else
             "  (no Oil share available)"))
    if r["wide_l"] is not None:
        a(f"     wide 14d Oil   {r['wide_l']:>14,.0f} L = "
          f"{100 * r['wide_l'] / r['ceiling_l']:.0f}% of the ceiling   [{r['wide_mode']}]"
          "  <- INFORMATION ONLY")
    a(f"     + finished gds {r['fg_l']:>14,.0f} L  = opening godown "
      f"{100 * (r['litres'] + r['fg_l']) / r['ceiling_l']:.0f}% of the DECLARED ceiling")
    r = recon["orders"]
    a(f"  ORDERS            {r['rows']:>14,} rows   real {r['real_pieces']:>12,.0f} pcs   "
      f"forecast {r['forecast_pieces']:>12,.0f} pcs")
    for ch, n in sorted(r["by_channel"].items(), key=lambda kv: -kv[1]):
        a(f"     {ch:<14}{n:>14,} rows")
    a(f"     backlog        {r['backlog_rows']:>14,} rows (OMS docs dated before today)")
    r = recon["inbound"]
    a(f"  ARRIVALS          {r['cells']:>14,} date x code cells over {r['dates']} dates "
      f"({sum(r['by_src'].values())} bookings)")
    for src, n in sorted(r["by_src"].items(), key=lambda kv: -r["qty_by_src"].get(kv[0], 0)):
        a(f"     {src:<14}{n:>7,} bookings {r['qty_by_src'].get(src, 0):>16,.0f}  (L for RM, pieces for PM)")
    a(f"     EXIM on the way{r['exim_otw_l']:>14,.0f} L    open contracts {r['po_lead_l']:>12,.0f} L")
    b = out["demand_baseline"]
    a(f"  DEMAND BASELINE   [{b['mode']}] {b['window'] and b['window'].get('from')}.."
      f"{b['window'] and b['window'].get('to')}   used for expected orders: "
      f"{'YES' if b['used_for_forecast'] else 'NO — ' + str(b['fallback_reason'])}")
    if b["used_for_forecast"]:
        a(f"     expected       {b['expected_litres']:>14,} L over {b['expected_rows']:,} rows"
          f" / {b['expected_skus']} SKU(s)   shape own {b['sku_shape_own']} · pooled "
          f"{b['sku_shape_pooled']}")
        a(f"     netted OMS     {b['netted_oms_pieces']:>14,} pieces   (ecom is NEVER netted "
          "— R18)   trailing set on {} plan row(s)".format(b["trailing_rows_set"]))
        r = b["reconciliation"]
        a(f"     reconciles     skus {r['skus_vs_totals_pct']}% · channels "
          f"{r['channels_vs_totals_pct']}% · weeks {r['weeks_vs_totals_pct']}% of the "
          "window total")
        n = b["nonplan"]
        a(f"     A18            {n['appended']} appended ({n['appended_l_per_month']:,} L/mo)"
          f" · {len(n['skipped'])} skipped ({n['skipped_l_per_month']:,} L/mo)")
    a(f"  LINE RATES — the rulebook's PLANNING speeds, pieces/hour, already post-efficiency "
      f"(rules.efficiency {out['rules']['efficiency']:g})")
    for ln in sorted(out["lines"]):
        bits = ", ".join(f"{p} {out['lines'][ln][p]:g} [{out['lines_basis_kind'][ln][p]}]"
                         for p in sorted(out["lines"][ln]))
        a(f"     {ln:<14} {bits}")
    for ln in sorted(out["lines_multi"]):
        bits = ", ".join(f"{p} {out['lines_multi'][ln][p]:g}"
                         for p in sorted(out["lines_multi"][ln]))
        a(f"     {ln:<14} COMBO SETS {bits}")
    a(f"  SHIFT             {out['rules']['shift_hours']} h a session, "
      f"{out['rules']['sessions_per_day_max']} session(s) a day max, "
      f"{out['rules']['night_lines_max']} line at night, Sundays off: "
      f"{out['rules']['sundays_off']}")
    lg = out["lag"]
    a(f"  INVOICE->GATE LAG median {lg['median_days']} d · p90 {lg['p90_days']} d · max "
      f"{lg['max_days']} d over {lg['rows']} rows ({lg['window']})   "
      f"[{lg['book']} — THE PLAN'S BOOK] "
      f"[{'MEASURED DAILY' if not lg['static'] else 'MEASURED ONCE — static'}]")
    if lg["all_books"]["median_days"] is not None:
        a(f"     beside it     all three books merged: median "
          f"{lg['all_books']['median_days']} d · p90 {lg['all_books']['p90_days']} d over "
          f"{lg['all_books']['rows']} rows — published, NOT what the engine was given")
    db = out["dispatch_book"]
    _open_l = "{:,}".format(db["open_l_all_books"]) if db["open_l_all_books"] is not None else "?"
    a(f"  OPEN DISPATCH BOOK {_open_l} L all "
      f"books / Oil pile {db['oil_pile_l']:,} L   pendency all "
      f"{db['pendency_days_all']} d · Oil {db['pendency_days_oil']} d "
      f"(last {db['trailing_days']} recorded day(s))")
    m = out["money"]
    a(f"  MONEY             ₹{m['mtd_made_rs']:,} booked over {m['mtd_days']} day(s); today "
      f"₹{m['today_booked_rs']:,}   target ₹{f(m['target_rs_per_day']):,.0f}/day, floor "
      f"₹{f(m['floor_rs_per_day']):,.0f}")
    a(f"     by rate        realise ₹{m['mtd_by_basis']['realise_rs']:,} · billing "
      f"₹{m['mtd_by_basis']['baseline_rs']:,} · default ₹{m['mtd_by_basis']['default_rs']:,}"
      f"   unvalued {m['mtd_unvalued_pcs']:,} pcs")
    a("  RULEBOOK " + str(out["rulebook"]["version"]) + "   in effect: " + ", ".join(
        f"{k}{'' if v['in_effect'] else ' (fallback)'}"
        for k, v in sorted(out["rulebook_applied"].items())))
    a(f"  assumptions this run: {len(out['honesty']['assumed'])}   "
      f"warnings: {len(out['warnings'])}")
    for w in out["warnings"]:
        a(f"     ! {w}")
    a("=" * 78)
    return "\n".join(L)


def main():
    F, out, recon = build()
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    os.replace(tmp, OUT_PATH)
    F.save_carry()
    print(reconcile(F, out, recon, OUT_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
