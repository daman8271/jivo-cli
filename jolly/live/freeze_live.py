#!/usr/bin/env python3
"""freeze_live.py — the LIVE opening position, written in the shape the engine reads.

    python3 live/freeze_live.py            # from jolly/
    python3 -m live.freeze_live            # same thing
    live/loop.sh                           # what cron runs, right after collect.py

WHAT IT IS
==========
`engine/august_sim.py` is CALIBRATED (2,122,639 L simulated against 2,119,237 L
actual on August — 0.16%) and is NEVER modified. It reads exactly one JSON. This
script writes that JSON — `sim/live-inputs.json` — from `live/state/state.json`
every cycle, so the same untouched engine runs on a plant position that is minutes
old instead of a 31-August photograph.

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
the factory / OMS / ecom / EXIM CLIs.

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

LINE RATES — THE DOUBLE-DERATE TRAP
===================================
The engine multiplies whatever is in `lines` by `rules.efficiency` (0.50) at run
time (`rate = sp[slot] * EFF`). So `lines` holds the PRE-efficiency number, and
storing a rate that has already been derated would derate it TWICE — the trap
named in ../CLAUDE.md. Order of preference per (line, pack):
  1. MEASURED_RATES below — the August observations that REFUTED the app's rating
     (Clear Pack 5 L rated 3,000, observed 1,000; Tin Head has no config row at all)
  2. the live ji.jivo.in line-config rated speed, VERBATIM, not multiplied
  3. the carried sep-inputs value
`lines_basis` says which of the three every slot got.

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

# EXIM sells and stores oil by WEIGHT; the engine counts LITRES. 0.91 kg/L is the
# adapter's own declared constant (exim.inbound.kg_per_litre) and is re-read from
# state at run time; this is only the fallback if that key is absent.
KG_PER_LITRE_DEFAULT = 0.91

# reference/PLAN-AND-LINES.md + the August observations that refuted the app's
# ratings. PRE-efficiency: the engine multiplies these by rules.efficiency itself.
MEASURED_RATES = {
    ("Clear Pack", "5L"): 1000.0,   # rated 3,000 REFUTED; observed median 831/hr
    ("Clear Pack", "4L"): 1000.0,   # same head, size-changeable 1 L / 4 L / 5 L
    ("Tin Head",   "TIN"): 215.0,   # August peak. Tin Head has NO line-config row.
}

OMS_DEAD_STATUSES = {"COMPLETED", "REJECTED", "BILLING_REJECTED", "BILLING REJECTED"}
FORECAST_CUSTOMER = "(forecast — not yet ordered)"
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
        self.provenance = {}
        self.carry = {}
        self.carry_used = []
        self.carry_new = {}
        self.carry_drop = set()

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def assume(self, msg):
        if msg not in self.assumed:
            self.assumed.append(msg)

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
            self.warn(f"{key} reported ok:false ({err}); its partial live data is used and "
                      "each block is checked on its own")
            self.assume(f"{key} half-failed this cycle and its partial live payload was used — "
                        f"{err}")
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
    items = base["items"]
    bom, blends = base["bom"], base["blends"]
    DEF_R = 148.33                                    # the engine's own default ₹/L

    oils = {c for kids in bom.values() for c, _ in kids if c.startswith("RM")}
    for b, kids in blends.items():
        oils.add(b)
        oils.update(c for c, _ in kids)

    prod, prod_mode, prod_env = F.source("factory_production")
    disp, disp_mode, disp_env = F.source("factory_dispatch")
    inb, inb_mode, inb_env = F.source("factory_inbound")
    exim, exim_mode, exim_env = F.source("exim")
    oms, oms_mode, oms_env = F.source("oms")
    ecom, ecom_mode, ecom_env = F.source("ecom")

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
    # packaging today, and Mark 2's August run — the one calibrated to 0.16% — counted
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

    lag_note = (disp or {}).get("lag_note") or {}
    lag_days = lag_note.get("median_days")
    if lag_days is None:
        lag_days = base["rules"]["invoice_truck_lag_days"]
        F.assume(f"invoice-to-truck lag kept at the carried {lag_days} days — "
                 "factory_dispatch.lag_note carried no measured median this cycle")
    else:
        lag_days = int(lag_days)

    # --------------------------------------------------------- orders -------
    orders, backlog = [], []
    real_pieces = {}
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
    amz_mix = {k: f(v) for k, v in ((ecom or {}).get("open_po_litres_by_fg_amazon_sep") or {}).items()}
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
            ec_excluded_l += lit                       # August backlog and October POs alike
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
        F.warn(f"{ec_excluded_l:,.0f} L of ecom demand is dated outside {today.strftime('%B %Y')} "
               "(Amazon's open book is mostly stale August backlog plus one October PO) and is "
               "NOT in the demand stream")
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

    # -- 3. FORECAST — the plan, net of the two real streams ------------------
    weekly = load_weekly_buckets(F)
    fc_rows = 0
    fc_pieces = 0.0
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
                       "channel": "FORECAST", "_src": "FORECAST"})
            fc_rows += 1
            fc_pieces += pieces
    F.assume("the remainder of the monthly plan, net of every real order this run can see, is "
             "carried as FORECAST rows — they are NOT orders and are tagged three ways "
             "(channel=FORECAST, docnum FCST-*, customer '(forecast — not yet ordered)')")
    if not orders:
        die("orders — no OMS line, no ecom row and no forecast bucket survived. The engine "
            "asserts on an empty demand stream; writing this file would only move the failure.")

    recon["orders"] = {"rows": len(orders), "by_channel": order_rows_by_channel,
                       "oms_lines": oms_kept, "ecom_rows": ec_rows, "forecast_rows": fc_rows,
                       "backlog_rows": len(backlog),
                       "real_pieces": sum(real_pieces.values()), "forecast_pieces": fc_pieces}

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
    lines, lines_basis, lines_unslotted = build_lines(F, prod, prod_mode, prod_env, base, plan)
    prov("lines", "factory_production", prod_mode, prod_env,
         "measured August rates where they exist, else the ji.jivo.in rated speed VERBATIM "
         "(the engine applies rules.efficiency itself — storing rated x efficiency here would "
         "derate twice), else the carried table")
    recon["lines"] = {ln: {p: lines_basis[ln][p] for p in sorted(lines_basis[ln])}
                      for ln in sorted(lines_basis)}

    # ---------------------------------------------------------- rules -------
    rules = dict(base["rules"])
    rules["invoice_truck_lag_days"] = lag_days
    app_lines = ((prod or {}).get("lines") or [])
    app_hours = sorted({f(l.get("standard_hours_per_day")) for l in app_lines
                        if l.get("is_active") and f(l.get("standard_hours_per_day")) > 0})
    if app_hours:
        rules["standard_hours_per_day_app"] = app_hours if len(app_hours) > 1 else app_hours[0]
        rules["standard_hours_per_day_app_basis"] = (
            "ji.jivo.in's own standard hours per line. rules.shift_hours is a DECISION "
            "(PLAN-AND-LINES.md: 12 h is the floor, not the answer) and overrides this — "
            "the field is published so the two are not confused.")
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
    if lag_note.get("median_days") is not None:
        F.assume(f"the {lag_days}-day invoice-to-truck lag is the MEASURED median off the gate "
                 f"log ({lag_note.get('rows')} rows, {lag_note.get('measured_window')}); the "
                 f"tail runs to {lag_note.get('max_days')} days and the plan ignores it")

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
            "NOT AVAILABLE. factory_production reads today and yesterday only; state.json "
            "carries no month window, so month-to-date pieces cannot be computed here without "
            "a new live call. Published as null rather than as two days wearing a month's "
            "label. The engine does not read this field."),
        "pieces_booked_today": booked.get("pcs"),
        "pieces_booked_today_basis": booked.get("note"),
        "rule": ("A ROLLING RE-PLAN from a LIVE opening. Only the opening is observed; every "
                 "day after today is computed. Nothing past today has happened."),
        "generated_by": "live/freeze_live.py",
        "state_collected_at": F.state.get("collected_at"),
        "state_completed_at": F.state.get("completed_at"),
    }
    F.assume("month-to-date production is not netted off the plan — the factory adapter carries "
             "no month window, so pieces_made_mtd is null this run")

    # --------------------------------------------------------- assemble -----
    opening = {
        "stock": stock,
        "fg": fg,
        "fg_litres": round(fg_plan_l + fg_other_l),
        "fg_plan_l": round(fg_plan_l),
        "fg_other_l": round(fg_other_l),
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
        "opening": opening,
        "orders": orders,
        "backlog": backlog,
        "inbound_prebooked": inbound,
        "inbound_provenance": inb_prov,
        "lines": lines,
        "lines_basis": lines_basis,
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
                "the invoice-to-truck lag, measured off the gate log",
                "BOMs, blends, realise May-Jul, and the monthly plan (carried)",
            ],
            "assumed": F.assumed,
        },
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


def slot_of(p):
    """The engine's own slot(), reproduced so `lines` is keyed the way it reads them."""
    pt = str(p.get("pack_type", "")).upper()
    sku = str(p.get("sku", "")).upper()
    l = f(p.get("litres_per_piece"))
    if "DRUM" in pt:
        return "DRUM"
    if "TIN" in pt or "KGS" in sku:
        return "TIN"
    if "POUCH" in pt or "POUCH" in sku:
        return "POUCH"
    for cap, name in ((1.05, "1L"), (2.05, "2L"), (3.05, "3L"), (4.05, "4L"), (5.05, "5L")):
        if l <= cap:
            return name
    return "15L"


def build_lines(F, prod, prod_mode, prod_env, base, plan):
    """{line: {pack: pieces/hour}} + a parallel basis map.

    PRE-EFFICIENCY, always: the engine multiplies by rules.efficiency at run time.
    """
    carried = base["lines"]
    cfgs, cfg_mode = F.block("factory_production", prod, prod_mode, prod_env,
                             "line_configs", lambda v: isinstance(v, list) and bool(v))
    rated, unslotted = {}, {}
    if cfgs:
        for c in cfgs:
            if not c.get("is_active"):
                continue
            ln = c.get("line_name")
            speed = f(c.get("rated_speed"))
            if not ln or speed <= 0:
                continue
            slot = config_slot(c.get("config_name"))
            if slot is None and c.get("sku_code") in plan:
                slot = slot_of(plan[c["sku_code"]])       # the per-SKU path, for when it returns
            if slot:
                rated.setdefault(ln, {}).setdefault(slot, []).append(speed)
            else:
                unslotted.setdefault(ln, []).append((c.get("config_name"), speed))
        for ln, slot in PARALLEL_MACHINE_LINES.items():
            rows = unslotted.get(ln)
            if rows and slot not in rated.get(ln, {}):
                total = sum(sp for _n, sp in rows)
                rated.setdefault(ln, {})[slot] = [total]
                unslotted.pop(ln, None)
                F.assume(f"{ln} runs {len(rows)} machines side by side "
                         f"({', '.join(str(n) for n, _sp in rows)}); their rated speeds are "
                         f"SUMMED into one {slot} rate ({total:g}/hr), never averaged")
        if unslotted:
            F.warn("line configs whose name is neither a pack size nor a known machine, so "
                   "they set no rate: " + "; ".join(
                       f"{ln} {[n for n, _s in rows]}" for ln, rows in unslotted.items()))
    else:
        F.assume("ji.jivo.in line configs were not available this run, so every line rate is "
                 "the carried August-calibrated table")

    lines, basis = {}, {}
    for ln, packs in carried.items():                  # keep the carried shape as the spine
        lines[ln], basis[ln] = {}, {}
        for pack, val in packs.items():
            m = MEASURED_RATES.get((ln, pack))
            if m is not None:
                lines[ln][pack], basis[ln][pack] = m, "measured"
            elif rated.get(ln, {}).get(pack):
                vals = sorted(rated[ln][pack])
                lines[ln][pack] = vals[len(vals) // 2]  # median of that slot's configs
                basis[ln][pack] = "rated"
            else:
                lines[ln][pack], basis[ln][pack] = f(val), "carried"
    for ln, packs in rated.items():                    # a slot the app knows and we did not
        for pack, vals in packs.items():
            if ln in lines and pack not in lines[ln]:
                vals = sorted(vals)
                lines[ln][pack] = vals[len(vals) // 2]
                basis[ln][pack] = "rated"
    if any(b == "measured" for p in basis.values() for b in p.values()):
        F.assume("Clear Pack 5 L and Tin Head run at OBSERVED August rates, not their app "
                 "rating (Clear Pack 5 L was rated 3,000/hr and measured 1,000; Tin Head has "
                 "no config row at all) — and the engine then derates everything by "
                 f"{base['rules']['efficiency'] * 100:.0f}% again")
    if any(b == "rated" for p in basis.values() for b in p.values()):
        F.assume("line rates marked `rated` are ji.jivo.in's own rating carried VERBATIM; the "
                 "rating has measured 17%-327% of reality, and the engine applies "
                 f"rules.efficiency ({base['rules']['efficiency']}) on top of it")
    if any(b == "carried" for p in basis.values() for b in p.values()):
        F.assume("line rates marked `carried` are the August-calibrated table — the live "
                 "configs had no row for that line and pack size")
    return lines, basis, {ln: [n for n, _s in rows] for ln, rows in unslotted.items()}


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
    a("  LINE RATES (pieces/hour BEFORE the engine's "
      f"{out['rules']['efficiency'] * 100:.0f}% derate)")
    for ln in sorted(out["lines"]):
        bits = ", ".join(f"{p} {out['lines'][ln][p]:g} [{out['lines_basis'][ln][p]}]"
                         for p in sorted(out["lines"][ln]))
        a(f"     {ln:<14} {bits}")
    a(f"  invoice->truck lag {out['rules']['invoice_truck_lag_days']} d (measured median)   "
      f"assumptions this run: {len(out['honesty']['assumed'])}   warnings: {len(out['warnings'])}")
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
