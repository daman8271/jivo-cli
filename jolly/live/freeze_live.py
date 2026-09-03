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
It exits NON-ZERO and writes nothing when `opening.fg`, `opening.standing_l` or
`orders` is neither live nor carried from a last-good file. A silent zero in any
of those three is not a degraded answer, it is a WRONG answer that looks fine:
  * fg = 0     -> the godown reads empty, the plan re-makes a month of stock
  * standing=0 -> the storage ceiling reads free when it is not
  * orders = 0 -> the engine's own assert fires anyway, but later and less clearly
Every other field degrades to a declared fallback and says so in `honesty.assumed`.

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
                        factory_production.pm_stock BH-BS + BH-PM (the two packaging
                        rooms), summed. NOT in the FG ceiling.
opening.stock[RM…]      LITRES per RM code
                        exim.tanks.by_oil[].litres, mapped NAME -> RM code by
                        OIL_NAME_TO_RM below. EXIM and SAP share NO item code.
opening.oil_l           LITRES, every tank — a DIFFERENT series from a day file's
                        `oil_on_hand_l` (which is BOM-relevant only). Never one line.
opening.oil_unmapped_l  LITRES in tanks whose name this file cannot map. Reported,
                        never guessed into a code, never silently dropped.
opening.standing_l      LITRES invoiced and not yet physically gone (JIVO_OIL).
                        factory_dispatch.invoiced_not_dispatched.by_company.

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
    def both_pm(v):
        return isinstance(v, dict) and all(w in v for w in ("BH-BS", "BH-PM"))

    pm_stock, pm_mode = F.block("factory_production", prod, prod_mode, prod_env,
                                "pm_stock", both_pm)
    stock = {}
    pm_nonpm = 0
    if pm_stock is None:
        # NOT one of the three refusals PHASE4-FREEZE-LIVE.md lists, and refused anyway,
        # for the reason acceptance criterion 6 gives: "never a silent zero opening".
        # The engine reads an absent PM code as zero on hand, and a zero packaging
        # position blocks nearly every SKU — so the plan would say "the plant can build
        # nothing" and an operator would act on it. An unread room and an empty room are
        # the same number here and this run cannot tell them apart. That is precisely
        # the failure that once reported Rs 8.48 Cr blocked by 38 "zero" packaging items.
        die("opening.stock[PM…] — factory_production.pm_stock (BH-BS + BH-PM) is not "
            "available live, in last-good, or carried. The engine reads an absent PM code "
            "as zero, so writing this file would publish a plan that says the plant can "
            "build nothing. Wait for an hourly cycle (MARK3_FORCE_HOURLY=1 forces one).")
    else:
        for wh in ("BH-BS", "BH-PM"):
            for code, qty in (pm_stock.get(wh) or {}).items():
                q = f(qty)
                if q <= 0:
                    continue
                if str(code).upper().startswith("PM"):
                    stock[code] = stock.get(code, 0.0) + q
                else:
                    pm_nonpm += 1
        pm_meta, _ = F.block("factory_production", prod, prod_mode, prod_env,
                             "pm_stock_meta", lambda v: isinstance(v, dict) and bool(v))
        for wh in ("BH-BS", "BH-PM"):
            if ((pm_meta or {}).get(wh) or {}).get("truncated"):
                F.warn(f"pm_stock[{wh}] page filled up — packaging on hand is a FLOOR for "
                       "that room, and the rows lost are the SMALLEST (sorted desc), which "
                       "is the direction that invents a stock-out")
                F.assume(f"pm_stock[{wh}] did not fit one page; the smallest stocks are missing")
    prov("opening_pm", "factory_production", pm_mode, prod_env,
         "dashboards stock BH-BS + BH-PM (the packaging rooms), one warehouse per call")
    recon["pm"] = dict(codes=sum(1 for k in stock if k.startswith("PM")),
                       pieces=sum(v for k, v in stock.items() if k.startswith("PM")),
                       nonpm_rows=pm_nonpm, mode=pm_mode)

    # ------------------------------------------- opening.stock (RM, litres) -
    syn = load_synonyms()
    tanks = ((exim or {}).get("tanks") or {})
    by_oil = tanks.get("by_oil") or []
    oil_l_total = f(tanks.get("total_l"))
    mapped_l, unmapped_l, unmapped = 0.0, 0.0, []
    map_used = {}
    if not by_oil:
        F.warn("exim.tanks.by_oil is empty — no bulk oil position this run; every RM code "
               "reads zero and the plan will order oil it may already have")
        F.assume("bulk oil on hand is UNKNOWN this run (EXIM tanks did not answer)")
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
    absent = sorted(c for c in oils if c not in blends and stock.get(c, 0.0) <= 0)
    if absent:
        F.warn("BOM oils with NO tank in EXIM, so they read zero: "
               + ", ".join(f"{c} {items.get(c, {}).get('name', '')}" for c in absent))
        F.assume("EXIM tanks are the ONLY bulk-oil source in this freeze; an oil with no tank "
                 "reads zero even if drums of it sit in the raw-material store — "
                 + ", ".join(absent))
    prov("opening_oil", "exim", exim_mode, exim_env,
         "tanks by_oil litres — a MANUAL DAILY DIP READING, not a sensor; "
         "mapped to RM codes by name (OIL_NAME_TO_RM), synonyms applied")
    recon["oil"] = dict(tanks=len(by_oil), total_l=oil_l_total, mapped_l=mapped_l,
                        unmapped_l=unmapped_l, codes=len(map_used), mode=exim_mode)

    # ------------------------------------------------- opening.standing_l ---
    # The Oil split of this pile only exists on a HEAVY cycle: on a cheap one
    # by_company is {} and oil.undispatched_litres is null, leaving only the
    # all-company headline — a DIFFERENT population, not a subset, and measured
    # 2026-09-03 at 284,549 L against the heavy read's 1,260,504 L for Oil alone.
    # Letting standing_l flip 4x every thirty minutes would make day-1 godown space
    # a function of the cadence clock, so the last Oil figure is CARRIED instead.
    ind = ((disp or {}).get("invoiced_not_dispatched") or {})
    oil_row = (ind.get("by_company") or {}).get("JIVO_OIL") or {}
    standing_basis = None
    standing = None
    disp_at = (disp_env or {}).get("fetched_at") or F.collected_at.isoformat()
    if oil_row.get("litres") is not None:
        standing = f(oil_row["litres"])
        standing_basis = ("invoiced_not_dispatched.by_company[JIVO_OIL].litres — "
                          + str(ind.get("by_company_basis") or "")[:200])
        F.carry_put("standing_l", standing, disp_at)
    elif ((disp or {}).get("oil") or {}).get("undispatched_litres") is not None:
        standing = f(disp["oil"]["undispatched_litres"])
        standing_basis = "factory_dispatch.oil.undispatched_litres (the by_company split was empty)"
        F.carry_put("standing_l", standing, disp_at)
        F.assume("the invoiced-not-dispatched split by company was empty this cycle, so the "
                 "Oil pile came from factory_dispatch.oil.undispatched_litres instead")
    else:
        carried, at = F.carry_get("standing_l")
        if carried is not None:
            standing = f(carried)
            standing_basis = (f"CARRIED from the last heavy cycle ({at}) — the Oil split of the "
                              "invoiced-not-dispatched pile is only read every 30 minutes")
            disp_mode = f"carried {at}"
            F.assume(f"the invoiced-but-not-trucked Oil pile is carried from {at}: the split by "
                     "company is only fetched on a heavy cycle, and the all-company headline "
                     "available every cycle is a different population, not an Oil subset")
        elif ind.get("litres") is not None:
            head = f(ind["litres"])
            standing = head
            standing_basis = ("the ALL-COMPANY headline invoiced_not_dispatched.litres — no Oil "
                              "split has been read yet, and this is a DIFFERENT population, "
                              "not an Oil subset")
            F.assume(f"no Oil split of the invoiced-not-dispatched pile has been read yet; the "
                     f"all-company headline ({head:,.0f} L) stands in. It counts open dispatch "
                     "PLANS with no date bound across all three books, where the Oil figure "
                     "counts BILLS in a 14-day window — the two do not reconcile and the "
                     "headline has measured about a fifth of the Oil-only number")
    if standing is None:
        die("opening.standing_l — factory_dispatch gave neither an Oil split nor a headline, "
            "live or last-good. Zero here reads the godown as free when it is not (C-0054).")
    prov("standing", "factory_dispatch", disp_mode, disp_env, standing_basis)
    ceil_l = f(base["rules"]["storage_ceiling_l"])
    if standing >= ceil_l:
        F.warn(f"the invoiced-not-dispatched Oil pile ({standing:,.0f} L) is at or above the "
               f"whole ASSUMED godown ceiling ({ceil_l:,.0f} L) — day 1 opens with no space "
               "and the engine will throttle production until the pile drains. That figure "
               "counts bills over a 14-day invoice window whose dispatch plan never reached "
               "DISPATCHED, which the adapter warns includes bills that physically left.")
    # The two dispatch endpoints do not reconcile and are not meant to be added or
    # differenced (the adapter says so). The one this freeze uses is named in
    # provenance.standing; the others are published beside it so the choice is visible
    # rather than buried — this single number decides day-1 godown space.
    standing_alts = {
        "used": round(standing),
        "by_company_JIVO_OIL_l": oil_row.get("litres"),
        "headline_all_company_l": ind.get("litres"),
        "headline_source": ind.get("source"),
        "godown_rooms_only_all_company_l": (ind.get("godown_rooms_only") or {}).get("litres"),
        "note": (ind.get("reconciliation") or {}).get("note"),
    }
    recon["standing"] = dict(litres=standing, mode=disp_mode,
                             ceiling_l=ceil_l, pct=100.0 * standing / ceil_l if ceil_l else 0)

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
    kg_per_l = f(((exim or {}).get("inbound") or {}).get("kg_per_litre"), KG_PER_LITRE_DEFAULT) \
        or KG_PER_LITRE_DEFAULT
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
    rules["storage_ceiling_l_basis"] = ("ASSUMED — Daman's spreadsheet, never measured "
                                        "(open question Q2). BH-BT + BH-PF only.")
    rules["storage_peak_l_basis"] = rules["storage_ceiling_l_basis"]
    F.assume(f"the godown ceiling {rules['storage_ceiling_l']:,} L working / "
             f"{rules['storage_peak_l']:,} L peak is ASSUMED, never measured (Q2 still open)")
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
        "standing_l": round(standing),
        "standing_l_alternatives": standing_alts,
        "oil_l": round(oil_l_total),
        "oil_mapped_l": round(mapped_l),
        "oil_unmapped_l": round(unmapped_l),
        "oil_unmapped": unmapped,
        "oil_absent_codes": absent,
        "packaging_pieces": round(sum(v for k, v in stock.items() if k.startswith("PM"))),
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
                "packaging in BH-BS and BH-PM (ji.jivo.in, live)",
                "bulk oil in the EXIM tanks (manual daily dip reading)",
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
    r = recon["oil"]
    a(f"  BULK OIL (tanks)  {r['total_l']:>14,.0f} L in {r['tanks']} tanks          [{r['mode']}]")
    a(f"     mapped         {r['mapped_l']:>14,.0f} L -> {r['codes']} RM codes")
    a(f"     UNMAPPED       {r['unmapped_l']:>14,.0f} L" +
      ("   <- named in opening.oil_unmapped" if r["unmapped_l"] else ""))
    if op["oil_absent_codes"]:
        a(f"     no tank at all  {', '.join(op['oil_absent_codes'])}")
    r = recon["standing"]
    a(f"  INVOICED, NOT GONE{r['litres']:>14,.0f} L  = {r['pct']:.0f}% of the "
      f"{r['ceiling_l']:,.0f} L ASSUMED ceiling   [{r['mode']}]")
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
