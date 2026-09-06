#!/usr/bin/env python3
"""
THE AUGUST SIMULATION v2 — a strict forward run from a MEASURED 1 August.

Reads ONLY sim/sim-inputs.json. Writes sim/days/day-NN.json, sim/events.json,
sim/summary.json.

THE RULE (Daman, 2026-08-31): only 1 August is observed. Every later day is computed
from the day before plus what the algorithm decided. The one thing that legitimately
arrives each day is that day's purchase orders — news landing, not hindsight.

WHAT v1 GOT WRONG (all corrected here):
  opening FG      664,341 L measured on 30 AUG   ->   461,225 L measured on 1 Aug
  standing pile   84,465 L (a Jul-Aug average)   ->   467,089 L, per document, and it
                                                      DRAINS over the first days
  inbound         naive open-PO query            ->   LIVE POs only (1,693 dead/phantom
                                                      rows dropped: 141M L of x1000
                                                      keying errors, 22.4M units of
                                                      >90-day paper that delivered 0.0%)
  Clear Pack 5 L  3,000/hr rated                 ->   1,000/hr (observed median 831)
  Tin Head        240/hr (owner's word)          ->   215/hr (August peak; no app config)
  line clearance  not modelled at all            ->   51.3 min per changeover
  line speed      rated                          ->   x0.50, the observed rate when running

THE LOOP THE OWNER ASKED FOR, made explicit and logged as events:
  need a SKU -> a component is at zero -> ORDER it -> it takes N days ->
  RUN SOMETHING ELSE meanwhile -> the component lands -> the SKU UNBLOCKS and runs.

MARK 4 — RULEBOOK MODE (2026-09-06). If the inputs carry a `rulebook` block (the freeze
embeds reference/mark4-rulebook.json), this same script schedules to the plant's machine
rulebook instead of "any slot on any line":
  * the pack and the bottle come from the RECIPE (R15), so a '15 LTR PET' row that is
    really a tin goes to the Tin Head and nowhere else, and no 15 L slot is derived (AC02);
  * a run is only possible where the line names that pack AND that bottle family, at
    preference 1/2/3 — a SKU reaches a lesser machine only once every better one is full;
  * one product change a line a session, continuation first, and the cap lifts only rather
    than leave a line idle — every lift is printed in that day's decisions, and the day
    file carries the TRUE number of changes a line made so nothing understates R06 (B02);
  * 10 working hours a session and ONE line gets a second session, named with its reason
    each day (R02/R03/A07); Sunday makes nothing and still dispatches (R04/A11);
  * the three 200 L drums are filled by hand: never scheduled, never "stuck" (R14);
  * the speeds in `lines` are PLANNING speeds — rules.efficiency must be 1.0 or the run
    stops, because derating them twice runs the plant at half (A01).
Without that block every line below behaves exactly as it did for the August calibration,
which is checked to the litre by engine/_rulebook_sim_test.py.
"""
import json, collections, os
from datetime import date, timedelta

import os as _os
S = json.load(open(_os.environ.get("SIM_INPUTS", "sim/sim-inputs.json")))
L, R, OP = S["lines"], S["rules"], S["opening"]
# MARK 4 — THE SWITCH. The freeze embeds reference/mark4-rulebook.json in the inputs and
# its PRESENCE turns on rulebook mode: bottle families, line preferences, one product per
# line per session, a named night line, Sunday dispatch, hand-filled drums. Absent — the
# August calibration and the -sep path — every line below runs exactly as it always did.
RB = S.get("rulebook")
# combo sets: containers/hour on the lines that have a RECORD of filling one (B19). A SKU
# whose recipe holds more than one container is not schedulable on a line missing from here.
LM = S.get("lines_multi") or {}
import os as _os
FLUSH = R["flush_litres"]; EFF = R["efficiency"]
# A01: a rulebook input carries PLANNING speeds — the 80% and the August cap are already
# inside them. Derating them a second time runs the plant at half and every check still
# passes. Raised, not asserted: `python3 -O` strips an assert, and the loop takes its
# interpreter from the environment (MARK3_PYTHON), so an assert here is a guard that any
# env var can switch off — measured: the same inputs then plan 2.01M L instead of 3.19M.
if RB is not None and abs(EFF - 1.0) > 1e-9:
    raise SystemExit("rulebook inputs must carry rules.efficiency 1.0 — planning speeds "
                     "already include the 80% and the August cap (A01)")
# R02: the shift is the rulebook's, not the loop's. SIM_HOURS stays a scenario override and
# says so in the summary, so a longer run can never be mistaken for the plan — and it may
# only make the shift SHORTER. R02 is explicit that day + night is 20 hours, not 22, not 24;
# live/loop.sh exported SIM_HOURS=12 by default, so every 3-minute cycle planned a day the
# plant had not ruled and put 24.0 h on the line that also took the night. No litre figure is
# quoted for that here on purpose: it was measured at +11% on the inputs of the day it was
# found and at 1,202,011 L against 10 h's 1,284,706 L on 2026-09-06 — a storage-bound month
# gives the extra hours back. (That second figure needs _cap_hours below lifted to reproduce;
# the engine refuses SIM_HOURS=12 on rulebook inputs now.) The number rots, the argument does
# not, so the argument is what is written down. A knob that
# silently replaces the plant's own ruling is not a scenario knob whichever way it moves.
HOURS = float(_os.environ.get("SIM_HOURS") or (RB["shift"]["hours_per_session"] if RB else R["shift_hours"]))
HOURS_OVERRIDE = _os.environ.get("SIM_HOURS") or None
def _cap_hours(h, what):
    if RB is not None and h > float(RB["shift"]["hours_per_session"]) + 1e-9:
        raise SystemExit(
            f"{what} is {h:g} h — longer than the rulebook's "
            f"{float(RB['shift']['hours_per_session']):g} h session (R02: day + night = 20 hours, "
            f"not 22, not 24). A scenario may shorten the shift, never lengthen it — if the "
            f"plant really works longer, that is a ruling in reference/mark4-rulebook.json.")
    return h
_cap_hours(HOURS, "SIM_HOURS" if HOURS_OVERRIDE else "the shift")
# SIM_HOURS_SCHEDULE="1-13:22,14-30:12" overrides HOURS by day-of-month (taper
# scenarios). Unset = empty dict = every day falls back to HOURS, output unchanged.
def _sched(s):
    out = {}
    for part in s.split(","):
        rng, h = part.split(":"); a, _, b = rng.partition("-")
        for dd in range(int(a), int(b or a) + 1): out[dd] = float(h)
    return out
SCHED = _sched(_os.environ["SIM_HOURS_SCHEDULE"]) if _os.environ.get("SIM_HOURS_SCHEDULE") else {}
for _d, _h in SCHED.items(): _cap_hours(_h, f"SIM_HOURS_SCHEDULE day {_d}")
# PRESENT, not truthy. HEAD read `.get("SIM_SUNDAYS_OFF", "1") == "1"`, so an exported-but-
# empty value meant Sundays were WORKED; a truthiness test sends "" to the default instead and
# turns them off — 2,340,592 L against August's 2,124,866 L, Rs 3.64 Cr, on a file whose own
# contract is that the legacy path behaves exactly as it always did. No caller in the tree
# exports it empty, so this was latent; `in os.environ` keeps it that way.
SUNDAYS_OFF = (_os.environ["SIM_SUNDAYS_OFF"] == "1") if "SIM_SUNDAYS_OFF" in _os.environ \
    else (RB["shift"]["sundays_off"] if RB else True)
TAG = _os.environ.get("SIM_TAG", "")
CLEAR_H = R["line_clearance_min"] / 60.0
CEIL = R["storage_ceiling_l"]; PEAK = R["storage_peak_l"]
LEAD = R["lead_days"]; LAG = R["invoice_truck_lag_days"]
_h = S["meta"]["horizon"]
D0, D1 = date.fromisoformat(_h[0]), date.fromisoformat(_h[1])

# 15 L PET jars fill through the same head as the 5 L jars: the nozzle gives
# litres/hour, so pieces/hour scales by 1/3. DERIVED, not measured — no 15 L fill
# rate exists in reference/PLAN-AND-LINES.md or the app. Before this, slot() dropped
# 15 L PET into the 5 L bucket and it ran at 5-litre PIECE rates — 6,700-7,500 L/hr
# sustained, above 10 Head's full RATED litre throughput (252,786 L of September was
# booked in 39.5 line-hours). August is untouched: its only 15 L items are TINs.
# Mark 4 switches this off (AC02): with a rulebook a line fills exactly the slots the
# rulebook names it for — 15 L belongs to the Tin Head and no 5 L head inherits it.
if RB is None:
    for _sp in L.values():
        if "5L" in _sp and "15L" not in _sp: _sp["15L"] = _sp["5L"] / 3.0

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def slot(p):
    pt = str(p["pack_type"]).upper(); sku = str(p["sku"]).upper(); l = p["litres_per_piece"]
    if "DRUM" in pt: return "DRUM"
    if "TIN" in pt or "KGS" in sku: return "TIN"
    if "POUCH" in pt or "POUCH" in sku: return "POUCH"
    if l <= 1.05: return "1L"
    if l <= 2.05: return "2L"
    if l <= 3.05: return "3L"
    if l <= 4.05: return "4L"
    if l <= 5.05: return "5L"
    return "15L"

plan = {p["code"]: dict(p, slot=slot(p)) for p in S["plan"]}
# R15/B13/R14 — with a rulebook the pack, the bottle family and how many containers one
# saleable piece holds come from the RECIPE (rulebook.sku_pack), never the plan sheet's
# pack-type column; the 200 L drums are filled by hand and leave the schedule entirely.
unmapped_codes = []
if RB is not None:
    _pack = RB.get("sku_pack") or {}
    _drums = set((RB.get("drums") or {}).get("skus") or [])
    for _c, _p in plan.items():
        _e = _pack.get(_c)
        if _e:
            _p["slot"], _p["family"] = _e["slot"], _e["family"]
            _p["fills_per_piece"] = int(_e.get("fills_per_piece") or 1)
        else:
            _p["family"] = "UNKNOWN"; _p["fills_per_piece"] = 1
            unmapped_codes.append(_c)
        _p["manual"] = _p["slot"] == "DRUM" or _c in _drums
MANUAL = sorted(c for c, p in plan.items() if p.get("manual"))
bom, blends, items, realise = S["bom"], S["blends"], S["items"], S["realise"]
DEF_R = 148.33
oils = {c for kids in bom.values() for c, _ in kids if c.startswith("RM")}
for b, kids in blends.items():
    oils.add(b); oils.update(c for c, _ in kids)

def oil_of(code):
    o = [(c, p) for c, p in bom.get(code, []) if c in oils]
    return max(o, key=lambda x: x[1])[0] if o else None
def lpc(c): return plan[c]["litres_per_piece"]
def fills(c): return plan[c].get("fills_per_piece", 1)      # containers per saleable piece (B13)
def rs_hour(c, rate, n=1): return rate * EFF * lpc(c) / n * realise.get(c, DEF_R)

# --- rulebook mode: which machine may fill what, and in what order (R07-R15, A03, B01) ---
def rb_rate(c, ln):
    """Containers an hour for this SKU on this line — None when the line has no planning
    speed for that pack (B16) or no record of filling it as a combo set (B19). A line that
    cannot run something is not a line that can hold it back from another machine."""
    tbl = LM.get(ln) if fills(c) > 1 else L.get(ln)
    return (tbl or {}).get(plan[c]["slot"])

def rb_pref(c, ln):
    """1 first choice, 2 when the better lines are full, 3 last resort. None = this machine
    never fills this pack in this bottle — or has no speed for it."""
    p = plan[c]
    if p.get("manual"): return None
    fams = ((RB["lines"].get(ln) or {}).get("slots") or {}).get(p["slot"])
    if not fams or rb_rate(c, ln) is None: return None
    return fams.get(p["family"], fams.get("ANY"))

def rb_tier(c):
    """0 a real order behind it, 1 only an expected one, 2 the plan sheet's remainder."""
    b = book[c]
    return 0 if b["po_left"] > 0 else (1 if b["fc_left"] > 0 else 2)

def rb_full(ln):
    """A line that cannot start another run: under one clearance of free hours left (B01)."""
    return free[ln] <= CLEAR_H

def rb_admissible(c, ln, p, active):
    """A SKU may open on a preference-p line only once every better line for it is full.

    `active` is the set of lines RUNNING this session. A machine that is not in it is not
    merely busy, it is dark — nobody is standing at it and its leftover day hours cannot be
    spent — so it counts as full. Read against the day session's free hours instead, the
    JP night session was refused FG0000142, FG0000028, FG0000005 and five more on 9 and 10
    September because Clear Pack, closed for the night, still showed unused day hours (B01).
    """
    return all(rb_full(m) or m not in active
               for m in L if m != ln and (rb_pref(c, m) or 9) < p)

def rb_lph(c, ln):
    """Planning LITRES an hour for this SKU on this line — the rate the plant would quote.
    rb_rate is containers an hour and a combo set fills more than one per saleable piece."""
    rate = rb_rate(c, ln)
    return 0.0 if rate is None else rate * lpc(c) / fills(c)

def rb_home_rank(c):
    """Every machine that may fill this SKU, best first: preference, then planning litres
    an hour, then the name. The third key only ever settles a genuine dead heat."""
    return sorted((rb_pref(c, ln), -rb_lph(c, ln), ln)
                  for ln in L if rb_pref(c, ln) is not None)

def rb_home(c):
    """The best machine that may fill this SKU — where its litres belong when the night
    line is chosen. A SKU that three lines can run is ONE SKU, not three.

    Preference FIRST, then the planning speed on that slot. Until 2026-09-06 this was
    `sorted((rb_pref(c, ln), ln) …)`, so a preference tie was broken on the LINE NAME: all
    nine 5 L HDPE SKUs are preference 1 on both Clear Pack (1,068 containers/h) and 6 Head
    (480/h), and "6 Head" < "Clear Pack" — so the whole flagship 5 L class was attributed to
    the machine 2.2x slower, every day, and the night line was decided by the alphabet while
    the day file published "the most ordered litres still unmade" over the margin sorted()
    had invented. Litres an hour is the plant's own reason for preferring a machine."""
    r = rb_home_rank(c)
    return r[0][2] if r else None

def rb_home_tie(c):
    """The machines that are a REAL dead heat for this SKU — same preference AND the same
    planning litres an hour as the winner. More than one and the name decided it, which is
    a fact the night line's reason has to own rather than hide."""
    r = rb_home_rank(c)
    tied = [ln for p, lph, ln in r if r and (p, lph) == (r[0][0], r[0][1])]
    return tied if len(tied) > 1 else []

def rb_can_make(c):
    """Material on the floor right now for at least one piece — the same test the run loop
    applies through its binder, asked before a line is given a night for this SKU."""
    for ch, per in bom.get(c, []):
        if per <= 0: continue
        av = stock.get(ch, 0.0)
        if ch in blends:
            av = min((stock.get(k, 0.0) / kp) for k, kp in blends[ch] if kp > 0)
        if av < per: return False
    return True

def rb_prio(c, ln, rate):
    """Preference first, then what the line is already running (R06), then the demand tier
    (R19/B08), then value an hour — or trailing sales for a SKU nobody has ordered yet."""
    t = rb_tier(c)
    return (rb_pref(c, ln), 0 if c == on_code[ln] else 1, t,
            -(TRAIL.get(c, 0.0) if t == 1 else rs_hour(c, rate, fills(c))),
            0 if plan[c]["head"] == "PREMIUM" else 1)

# demand: the plan is the projection; POs are commitments layered on as they land.
# po_left / po_value hold REAL orders only (backlog + dated SAP orders); fc_left holds
# the FORECAST stream — the plan standing in for orders that do not exist yet. Mixing
# them put Rs 92 Cr of mostly-forecast money under a "po_open_value" label.
book = {c: dict(plan_left=max(0.0, p["pieces"] - f(OP["fg"].get(c, 0))), po_left=0.0, po_value=0.0, fc_left=0.0)
        for c, p in plan.items()}
# A backlog doc the freeze ALSO emits as a dated order row must not be seeded here too —
# it would count twice in want() and the sim would overproduce demand that cannot ship
# (August: 0 of 75 backlog docs overlap orders, so this changes nothing there;
#  September: all backlog docs re-enter as day-dated orders, so seeding is skipped).
_order_docs = {o["docnum"] for o in S["orders"]}
for b in S["backlog"]:
    if b["docnum"] in _order_docs: continue
    if b["code"] in book: book[b["code"]]["po_left"] += b["pieces"]; book[b["code"]]["po_value"] += b["value"]
orders_by_day = collections.defaultdict(list)
for o in S["orders"]:
    if o["code"] in plan: orders_by_day[o["date"]].append(dict(o))
# Raised, not asserted, for the reason written at :65-67: `python3 -O` strips an assert and
# the loop takes its interpreter from the environment, so this gate would be one env var
# away from off — measured, rc=0 and a full plan written on an empty demand stream.
if not S["orders"]:
    raise SystemExit("S['orders'] is empty — the freeze emitted no dated demand stream; "
                     "re-run the freeze, then the sim")

# R19/B08 — a product nobody has ordered yet is ranked by its TRAILING monthly litres,
# below everything with a real order and above the rest of the plan sheet. The freeze puts
# that figure on the plan row from live/state/demand_baseline.json (skus[code].
# litres_per_month, the 3-month GT/MT billing average). Until 2026-09-06 this line read a
# field NOTHING wrote: every expected-only SKU scored 0, so the tier ranked by plan-sheet
# insertion order — 123 of 249 placements and 54% of September's litres, decided by the
# order the rows happened to sit in (worth Rs 2.30 Cr against a real ranking). No trailing
# figure at all for a SKU = last inside its tier, which is R19 itself.
TRAIL = {}
TRAIL_SOURCE = None
if RB is not None:
    _rows = {c: f(p.get("trailing_l_per_month")) for c, p in plan.items()}
    if any(v > 0 for v in _rows.values()):
        TRAIL = {c: v for c, v in _rows.items() if v > 0}
        TRAIL_SOURCE = "trailing_l_per_month on the plan rows (the 3-month billing average)"
    else:
        # No baseline on the rows: this run's own expected stream measures the same thing —
        # every FORECAST row in it is demand this SKU is expected to carry — so the tier is
        # still ranked biggest expected seller first, never by insertion order.
        _fc = collections.Counter()
        for _o in S["orders"]:
            if _o["channel"] == "FORECAST" and _o["code"] in plan:
                _fc[_o["code"]] += _o["pieces"] * lpc(_o["code"])
        TRAIL = {c: v for c, v in _fc.items() if v > 0}
        TRAIL_SOURCE = ("this run's own expected-order stream — the plan rows carry no "
                        "trailing_l_per_month")
# A SKU carrying expected demand with NO trailing sales behind it is R19 itself — "no
# order behind it and last in sales goes last" — so it ranks last inside its tier and is
# NAMED, for the site to say so. The gate is `trailing_source`, not this list: on the real
# September plan 22 plan-sheet codes have sold nothing in three months, which is business
# truth, while a null source is the bug that made the whole tier rank by insertion order.
NO_TRAILING = sorted({o["code"] for o in S["orders"] if o["channel"] == "FORECAST"
                      and o["code"] in plan and TRAIL.get(o["code"], 0) <= 0}) if RB else []

stock = collections.defaultdict(float, {k: f(v) for k, v in OP["stock"].items()})
fg = collections.defaultdict(float, {k: f(v) for k, v in OP["fg"].items()})
inbound = collections.defaultdict(lambda: collections.defaultdict(float))
for d, m in S["inbound_prebooked"].items():
    for c, q in m.items(): inbound[d][c] += f(q)

# the 1-Aug standing pile: 467,089 L already billed, trucks going over the first days.
# 84 of 84 customer docs docked on 1 Aug or later, so it drains — it does not sit.
standing = collections.deque()
open_pile = f(OP["standing_l"])
# It leaves 45/35/20 over days 2, 3 and 4 (D0 + 1/2/3). Day 1's pile IS the live count
# — gen_live reconciles the end of day 1 to it — so nothing of it goes on day 1; the
# trucks start tomorrow. Seed only a real pile — a zero entry is noise in the queue.
if open_pile > 0:
    for i, share in enumerate([0.45, 0.35, 0.20]):
        standing.append([D0 + timedelta(days=i + 1), open_pile * share])

placed, events, days = [], [], []
on_oil = {ln: None for ln in L}
on_slot = {ln: None for ln in L}
on_family = {ln: None for ln in L}  # the BOTTLE on the line: a family change is a changeover too
on_fills = {ln: None for ln in L}   # containers per saleable piece — a combo set is a change
on_code = {ln: None for ln in L}    # what the line is running — continuation ranks first (R06)
blocked_since = {}          # code -> first day it was blocked (for the unblock story)
ordered_for = {}            # component -> day we ordered it because it blocked something

# B20 — what a held-up row says when the GODOWN is the binder, not a bottle. It is not a
# PM/RM code on purpose: the buy list, the PACKAGING_ZERO / OIL_SHORT events and the
# stuck-item chains all key off those prefixes, and there is no supplier to order storage
# from and no arrival that will unblock it.
STORAGE_BINDER = "STORAGE"
STORAGE_BINDER_NAME = "the godown is full — no room for another bottle today"

FG_OTHER = f(OP.get("fg_other_l", 0))   # FG outside the plan: never made, never shipped, always in the way
def fg_litres(): return FG_OTHER + sum(q * lpc(c) for c, q in fg.items() if c in plan and q > 0)
def standing_l(): return sum(v for _, v in standing)
def physical(): return fg_litres() + standing_l()
def ev(day, kind, **kw): events.append(dict(day=day, kind=kind, **kw))

# honesty is stamped on every day file and the site prints it — it must describe THIS
# month's inputs. The freeze writes a month-true block into the inputs (September:
# ~60% of the demand stream is FORECAST buckets, 31-Aug stock, the derived 15 L rate);
# August's inputs carry none, so its original text stands. Never narrate a forecast
# as the measured order book.
HON = S.get("honesty") or dict(
    measured=["1-Aug stock, FG and standing pile (per document)", "the order book (SAP, dated)",
              "BOMs", "line speeds and clearance (ji.jivo.in)", "realise May-Jul", "lead times (12m pre-Aug)"],
    assumed=["supply arrives exactly on its lead time", f"{LAG}-day invoice-to-truck lag",
             f"lines run at {EFF*100:.0f}% of rated, the observed rate"])
# A carried sentence belongs to a MODE, and the freeze says which. `honesty.assumed_modes`
# maps each sentence to "legacy" | "rulebook" | "both" (missing = "both", so an older input
# keeps every line it has), and this run drops only what is tagged for the OTHER mode.
#
# It replaces a keyword blocklist — ("derate", "rules.efficiency", "of rated", "50% again")
# matched against the sentence — that could not tell a false claim from a true one. Two
# sentences that are TRUE under the rulebook, "every line is planned at 80% OF RATED
# capacity, capped by its best August hour (R05/A01)" and "the plan never DERATES a planning
# speed a second time (A01)", were silently deleted when the freeze wrote them, and the
# engine then printed a warning blaming the freeze for text it should have kept. The words
# this plan needs in order to explain itself were exactly the words the filter banned.
# What the blocklist was really guarding — a Mark 3 sentence about a 50% derate reaching a
# plan that does not derate — is now the freeze's job to tag and live/_freeze_mark4_test.py's
# job to check, which is where the sentence is actually written.
_MODE = "rulebook" if RB is not None else "legacy"
_modes = HON.get("assumed_modes") or {}
honesty_dropped = [a for a in HON.get("assumed", [])
                   if _modes.get(a, "both") not in ("both", _MODE)]
_keep = [a for a in HON.get("assumed", []) if _modes.get(a, "both") in ("both", _MODE)]
if honesty_dropped or "assumed_modes" in HON:
    HON = dict(HON, assumed=_keep)
    HON.pop("assumed_modes", None)      # the tag map is an input, never a published line
if RB is not None:
    _eff = RB.get("efficiency") or {}
    # the run's own rules go FIRST — they are how every number below was arrived at.
    HON = dict(HON, assumed=[
        f"each machine is planned at the rulebook's PLANNING speed — "
        f"{float(_eff.get('planning_factor') or 0.8) * 100:.0f}% of its listed rating, and never faster than "
        f"the best hour it held in August over at least {_eff.get('min_runs_for_cap', 3)} runs. It is cut "
        f"once, in the rulebook, and not again here (A01)",
        f"{HOURS:.0f} working hours a session; ONE line gets a second session and the plan names "
        f"it and says why, every day (R02/R03)",
        ("Sunday makes nothing and still dispatches (R04)" if SUNDAYS_OFF else
         "Sundays are WORKED in this scenario — the rulebook says the plant does not (R04)"),
        f"the {len(MANUAL)} drum SKU(s) are filled by hand: never scheduled here, and never "
        f"holding a line up (R14)"] + _keep)

today = D0
while today <= D1:
    key = today.isoformat(); working = (today.weekday() != 6) or not SUNDAYS_OFF
    day = dict(date=key, weekday=today.strftime("%A"), working=working, received=[], new_orders=[],
               runs=[], blocked=[], dispatched=[], bought=[], decisions=[], unblocked=[], flushes=0)

    # trucks leave -> space released — by DATE, wherever the entry sits. Until
    # 2026-09-05 this popped the head only, so a day-1 bill (due day 3) waited behind
    # the pile's day-4 tranche and left on day 4, a day past the lag the plant shows.
    # gen_live's "trucks never fall behind the billing queue" caught it the moment the
    # live pile fell below day-1 billing (4 Sep 21:39) and refused to publish for 14 h.
    standing = collections.deque(e for e in standing if e[0] > today)

    # 1 RECEIVE — and note anything that unblocks a SKU we were waiting on
    for c, q in inbound.pop(key, {}).items():
        stock[c] += q
        day["received"].append(dict(code=c, name=items.get(c, {}).get("name", c), qty=round(q)))
        if c in ordered_for:
            waited = (today - date.fromisoformat(ordered_for[c])).days
            day["unblocked"].append(dict(code=c, name=items.get(c, {}).get("name", c),
                                         qty=round(q), ordered_on=ordered_for[c], waited_days=waited))
            ev(key, "UNBLOCKED", code=c, name=items.get(c, {}).get("name", c), waited_days=waited)
            del ordered_for[c]

    # 2 DEMAND — today's POs land and outrank the projection. A FORECAST row is not
    # an order: it drives want(), never the committed-PO ledger.
    for o in orders_by_day.get(key, []):
        b = book[o["code"]]
        if o["channel"] == "FORECAST": b["fc_left"] += o["pieces"]
        else: b["po_left"] += o["pieces"]; b["po_value"] += o["value"]
        day["new_orders"].append(dict(docnum=o["docnum"], customer=o["customer"][:40], channel=o["channel"],
                                      code=o["code"], sku=plan[o["code"]]["sku"],
                                      pieces=round(o["pieces"]), value=round(o["value"])))

    hrs = SCHED.get(today.day, HOURS)
    shipped = 0.0
    if working:
        free = {ln: hrs for ln in L}
        # R02/R03: every line gets one session and ONE line gets a second, so the hours a
        # line HAD today is a per-line number, never hrs x lines.
        hmax = {ln: hrs for ln in L}
        changes = {ln: 0 for ln in L}       # product changes on this line this session (B02)
        # the TRUE count, both sessions, for the day file: every time a line's product
        # changes, including the first placement of a session when the line was running
        # something else before (it pays a clearance the same way). B02 gives every line
        # one free change a session and logs only the lifts on top, so the lift count alone
        # understates how far the plan is from R06 ("one product on a line all day") —
        # measured on the real September rulebook run, 117 changes behind 51 logged lifts.
        pchanges = {ln: 0 for ln in L}
        night = None; night_picked = None; night_note = ""; night_cands = []; night_l = 0
        # B20 — THE STORAGE CEILING IS A HARD CAP ON EVERY RUN, and it is the single
        # biggest hand on this month's sheet. Worked out fresh each morning off what is
        # PHYSICALLY in the godown (finished goods + billed-not-yet-trucked), and
        # decremented litre for litre as the day is filled: when it reaches zero the
        # plant stops for the day however many hours, bottles and orders are left.
        # Everything below `storage_*` measures what that cap actually did on this run,
        # because until 2026-09-06 it did all of it silently — no rule, no assumption,
        # no build choice, and the word "headroom" nowhere on the site.
        headroom = max(0.0, CEIL - physical())
        headroom_open = headroom
        storage_capped_l = 0.0        # litres the ceiling took off runs it still allowed
        storage_capped_runs = 0       # runs the ceiling cut short
        storage_stopped = set()       # products the ceiling stopped outright today
        throttle = headroom < 100000
        if throttle:
            day["decisions"].append(dict(kind="STORAGE_THROTTLE", headroom_l=round(headroom),
                text=f"Godown at {physical()/CEIL*100:.0f}% at start of day — capped to what can ship"))
            ev(key, "STORAGE_THROTTLE", pct_start_of_day=round(physical() / CEIL * 100), headroom_l=round(headroom))

        # want/prio see COMBINED demand (real + forecast) — identical scheduling to the
        # calibrated behaviour; only the LABELS (po_backed, book.po_open_*) are real-only.
        def want(c): return max(book[c]["plan_left"], book[c]["po_left"] + book[c]["fc_left"])
        def prio(c, rate):
            return (0 if book[c]["po_left"] + book[c]["fc_left"] > 0 else 1, -rs_hour(c, rate),
                    0 if plan[c]["head"] == "PREMIUM" else 1)
        made_l = 0.0; oil_day = 0.0
        for _sess in ("day", "night"):
            if _sess == "night":
                if RB is None: break
                # R03/A07/B03 — labour allows ONE line a second session. It goes where the
                # most ORDERED litres are still unmade after the day session; ties go to JP.
                # Nothing ordered left: the most expected and plan litres. Nothing at all:
                # no night session, and the reason is published either way.
                # Each SKU counts ONCE, on the best machine that may fill it, and only while
                # there is material for it and something still wanted. Counting a 1 L mustard
                # in full against JP *and* 10 Head *and* 6 Head made two lines tie to the
                # litre on 9 nights of 22 and let sorted() hand the night to whichever name
                # came first; ignoring material gave the Tin Head 15 Sep on 21,100 ordered
                # litres whose every component was empty — 10 line-hours, 0 L, and a day file
                # that said "the most ordered litres still unmade".
                # MATERIAL-blocked only. A row whose binder is the GODOWN (B20) is not
                # evidence that a line has no work — it is evidence that the warehouse is
                # full, which the guard below answers on its own and for every line at
                # once. Folding storage rows in here emptied the measure entirely on a
                # full godown and published "nothing left to make" over a book full of
                # orders, which is a different lie from the one this filter was built for.
                _blk = {b["code"] for b in day["blocked"] if b.get("reason") != "storage"}
                _home = {}; _dead_heat = collections.Counter()
                for c in plan:
                    if c in _blk or plan[c].get("manual") or want(c) < 1 or not rb_can_make(c): continue
                    h = rb_home(c)
                    if not h: continue
                    _home[c] = h
                    # a SKU two machines fill at the SAME planning speed was placed by the
                    # line name — count those litres so the reason can own it (item 2)
                    if rb_home_tie(c): _dead_heat[h] += want(c) * lpc(c)
                _po = collections.Counter(); _oth = collections.Counter()
                for c, ln in _home.items():
                    _po[ln] += book[c]["po_left"] * lpc(c); _oth[ln] += want(c) * lpc(c)
                _po = {ln: round(_po[ln]) for ln in L}; _oth = {ln: round(_oth[ln]) for ln in L}
                # the tie-break in the open: JP first (A07/B03), then the line with the most
                # expected and plan litres behind it, then the name — and the reason says
                # which of them actually decided it, so no day file claims a margin it had not.
                def _why_tied(rank, measure, second):
                    tied = [ln for ln in rank if measure[ln] == measure[rank[0]]]
                    if len(tied) < 2: return ""
                    if rank[0] == "JP Machine": why = "the rulebook sends a tie to the JP Machine (A07)"
                    # against the BEST loser, not the worst: min() over the whole tied set
                    # includes lines that had already lost on the JP key, so a pick with no
                    # margin at all over its nearest rival still claimed one.
                    elif second is not None and second[rank[0]] > max(second[ln] for ln in tied
                                                                     if ln != rank[0]):
                        why = "more expected and plan litres behind it"
                    else: why = "nothing else separated them, so the line name did"
                    return (f"; tied at {measure[rank[0]]:,} L with "
                            f"{', '.join(ln for ln in tied if ln != rank[0])} — {why}")
                _rank = sorted(L, key=lambda ln: (-_po[ln], 0 if ln == "JP Machine" else 1, -_oth[ln], ln))
                night_cands = [dict(line=ln, po_backed_l=_po[ln], other_l=_oth[ln]) for ln in _rank]
                if _po[_rank[0]] > 0:
                    night = _rank[0]; night_l = _po[night]
                    night_note = ("the most ordered litres still unmade after the day session"
                                  + _why_tied(_rank, _po, _oth))
                else:
                    _rank = sorted(L, key=lambda ln: (-_oth[ln], 0 if ln == "JP Machine" else 1, ln))
                    night_cands = [dict(line=ln, po_backed_l=_po[ln], other_l=_oth[ln]) for ln in _rank]
                    if _oth[_rank[0]] > 0:
                        night = _rank[0]
                        night_note = ("nothing order-backed left; picked by expected and plan litres"
                                      + _why_tied(_rank, _oth, None))
                    else:
                        night_note = "nothing left to make"
                # a SKU that two machines fill at the same preference AND the same planning
                # speed is placed on one of them by its name. That is a real dead heat, so
                # the night's own reason says how many of its litres rest on it (item 2).
                if night is not None and _dead_heat[night] >= 1:
                    night_note += (f"; {round(_dead_heat[night]):,} L of that is SKU(s) another "
                                   f"machine fills at the same planning speed — a dead heat the "
                                   f"line name broke")
                # B20 OVERRIDES A07 — A NIGHT SESSION IS A CREW, DON'T ROSTER ONE FOR
                # NOTHING. The measure above picks the line with the most ordered litres
                # still unmade, and on a full godown that sentence is true and useless:
                # there is nowhere to put a single bottle, so the session opens, works
                # nought hours and prints against nothing. Measured 2026-09-06 — 22
                # sessions opened, 10.5 hours worked in the whole month, 10.0 of it on one
                # day, and eleven nights named a line under "the most ordered litres still
                # unmade". The measure's answer is kept as `picked` (it is still the right
                # machine, and the tie-break reason is still worth reading); what changes
                # is that no crew is rostered and the reason says why.
                night_picked = night
                if night is not None:
                    _smallest = min((lpc(c) for c in plan
                                     if want(c) >= 1 and rb_can_make(c)
                                     and not plan[c].get("manual")), default=None)
                    if _smallest is not None and headroom < _smallest:
                        night_note += ("; but NO second session tonight — the godown has no "
                                       "room for another bottle, so a night shift could not "
                                       "put anything anywhere (B20)")
                        night = None; night_l = 0
                if night is None: break
                free[night] += hrs; hmax[night] += hrs
                changes = {ln: 0 for ln in L}
            active = set(L) if _sess == "day" else {night}
            for _ in range(400):
                placed_any = False
                for ln, sp in sorted(L.items(), key=lambda kv: -max(kv[1].values())):
                    if ln not in active or free[ln] <= 0.05: continue
                    if RB is None:
                        order = [(0, c) for c in sorted([c for c in plan if plan[c]["slot"] in sp and want(c) >= 1],
                                                        key=lambda c: prio(c, sp[plan[c]["slot"]]))]
                    else:
                        cands = sorted([c for c in plan if want(c) >= 1 and rb_pref(c, ln) is not None
                                        and rb_admissible(c, ln, rb_pref(c, ln), active)],
                                       key=lambda c: rb_prio(c, ln, rb_rate(c, ln)))
                        # B02 — one product change per line per session. The cap lifts only
                        # when the line would otherwise stand idle with hours to spare, and
                        # every lift is printed in the day's decisions. A code carried on the
                        # SECOND list is a lift; the first list is the cap being obeyed.
                        if changes[ln] < 1: order = [(0, c) for c in cands]
                        else:
                            # changes[ln] only reaches 1 through the counter below, which
                            # needs on_code[ln], so here it is never None. And the line's
                            # own product has just been tried at _li=0: re-queueing it on
                            # the lift list buys a second identical failure and a duplicate
                            # row in day['blocked'].
                            order = [(0, c) for c in cands if c == on_code[ln]]
                            if free[ln] > CLEAR_H:
                                order += [(1, c) for c in cands if c != on_code[ln]]
                    for _li, c in order:
                        n = fills(c)      # containers per saleable piece: a combo set fills two
                        rate = (rb_rate(c, ln) if RB is not None else sp[plan[c]["slot"]]) * EFF
                        o = oil_of(c)
                        change = on_oil[ln] is not None and o and o != on_oil[ln]
                        # The 51.3-min clearance is per CHANGEOVER — an oil change, a cold
                        # start, or a same-oil PACK-SIZE change (change parts still go on).
                        # Only the 400 L flush is oil-specific. Before this, 14 same-oil
                        # size changes in September booked zero minutes (~12 uncharged hours).
                        # The BOTTLE is a changeover too, and it was the same bug one
                        # dimension over: Mark 4 made `family` and `fills_per_piece` real
                        # scheduling dimensions and this line still only knew the slot, so
                        # 5 L HDPE -> 5 L TIN on the 6 Head and 1 L 26G -> 1 L 23.8G round on
                        # JP booked fh = 0.0 — about 2.6 uncharged line-hours a month, and it
                        # quietly made the cheapest schedule the one that alternates bottles.
                        # Legacy inputs carry no family and every piece is one container, so
                        # both extra tests are constant there and August does not move.
                        sizechg = on_slot[ln] is not None and (
                            plan[c]["slot"] != on_slot[ln]
                            or plan[c].get("family") != on_family[ln]
                            or fills(c) != on_fills[ln])
                        if change: fh = FLUSH / (rate * lpc(c) / n) + CLEAR_H
                        elif on_oil[ln] is None or sizechg: fh = CLEAR_H
                        else: fh = 0.0
                        if fh >= free[ln]: continue
                        cap = (free[ln] - fh) * rate / n
                        binder = None
                        for ch, per in bom.get(c, []):
                            if per <= 0: continue
                            av = stock.get(ch, 0.0)
                            if ch in blends:
                                av = min((stock.get(k, 0.0) / kp) for k, kp in blends[ch] if kp > 0)
                            if av / per < cap: cap, binder = av / per, ch
                        # B20 — the godown is the LAST cap and it beats the other two. It is
                        # applied here rather than up with the hours so that it can be NAMED:
                        # while it was folded into `cap` before the material loop, a product
                        # the ceiling stopped had binder=None and fell out of the `did < 1`
                        # branch below without a row — 11 of this run's 18 throttled days
                        # published "nothing is stuck" with five machines standing idle.
                        # `cap` itself is unchanged either way: min(hours, material, godown).
                        cap_room = max(0.0, headroom) / lpc(c)
                        storage_bound = cap_room < cap
                        if storage_bound:
                            capped_off = cap - cap_room
                            cap, binder = cap_room, None
                        did = min(want(c), cap)
                        if did < 1:
                            if binder:
                                day["blocked"].append(dict(code=c, sku=plan[c]["sku"], want=round(want(c)),
                                    reason="material",
                                    binder=binder, binder_name=items.get(binder, {}).get("name", binder)))
                                blocked_since.setdefault(c, key)
                            elif storage_bound:
                                # THE GODOWN IS THE BINDER. Same shape as a material row so
                                # the day file, the stuck list and the site read it the same
                                # way; the binder code is STORAGE, which is deliberately not
                                # a PM/RM code — nothing may order it and nothing may wait
                                # for it to arrive.
                                day["blocked"].append(dict(code=c, sku=plan[c]["sku"], want=round(want(c)),
                                    reason="storage",
                                    binder=STORAGE_BINDER, binder_name=STORAGE_BINDER_NAME))
                                storage_stopped.add(c)
                            continue
                        if storage_bound and want(c) > cap:
                            storage_capped_l += min(capped_off, want(c) - cap) * lpc(c)
                            storage_capped_runs += 1
                        for ch, per in bom.get(c, []):
                            if ch in blends:
                                for k, kp in blends[ch]: stock[k] -= did * per * kp
                            else: stock[ch] -= did * per
                        oil_day += did * sum(per for ch, per in bom.get(c, []) if ch in oils)
                        book[c]["plan_left"] = max(0.0, book[c]["plan_left"] - did)
                        # real orders are consumed first (they also ship first), spilling to
                        # forecast; po_value drains proportionally with po_left so open-PO
                        # money falls as the committed pieces are built — never a cumulative
                        # counter (it once reached Rs 92.38 Cr by day 30).
                        b_ = book[c]; take = min(did, b_["po_left"])
                        if take > 0:
                            b_["po_value"] -= b_["po_value"] * take / b_["po_left"]
                            b_["po_left"] -= take
                        b_["fc_left"] = max(0.0, b_["fc_left"] - (did - take))
                        fg[c] += did
                        lit = did * lpc(c); made_l += lit; headroom -= lit
                        if change: day["flushes"] += 1
                        if RB is not None and on_code[ln] is not None and c != on_code[ln]:
                            changes[ln] += 1; pchanges[ln] += 1
                            # the first change of a session is B02's own allowance; every one
                            # after it is a lift, numbered so the site can say "the third time
                            # today" instead of counting decision rows.
                            if _li: day["decisions"].append(dict(kind="CHANGE_CAP_LIFTED", line=ln,
                                night=(_sess == "night"), nth=changes[ln] - 1,
                                text=f"{ln} had no more {plan[on_code[ln]]['sku']} to run, so it "
                                     f"changed to {plan[c]['sku']} rather than stand idle "
                                     f"— product change {changes[ln]} on this line this session"))
                        free[ln] -= did * n / rate + fh
                        on_oil[ln] = o; on_slot[ln] = plan[c]["slot"]; on_code[ln] = c
                        on_family[ln] = plan[c].get("family"); on_fills[ln] = n
                        _run = dict(line=ln, code=c, sku=plan[c]["sku"], head=plan[c]["head"], oil=o,
                            pieces=round(did), litres=round(lit), hours=round(did * n / rate, 2),
                            flush_min=round(fh * 60), realise=realise.get(c, DEF_R),
                            rs_per_hour=round(rs_hour(c, rb_rate(c, ln) if RB is not None else sp[plan[c]["slot"]], n)),
                            po_backed=book[c]["po_left"] > 0,
                            value=round(lit * realise.get(c, DEF_R)))
                        if RB is not None:
                            # containers off the PUBLISHED pieces, not off the raw float: with
                            # round(did * n) a 64.5-piece run published 64 pieces and 129
                            # bottles, a day file contradicting itself by one bottle. The
                            # hours and the stock draw still use the exact figure.
                            _run.update(slot=plan[c]["slot"], family=plan[c]["family"], pref=rb_pref(c, ln),
                                        night=(_sess == "night"), fills=n, containers=round(did) * n)
                        day["runs"].append(_run)
                        if c in blocked_since: del blocked_since[c]
                        placed_any = True; break
                if not placed_any: break

    if working or RB is not None:
        # DISPATCH — PO-backed first; goods leave the floor after the measured truck lag.
        # In rulebook mode this runs on Sunday too (R04: Sunday is for dispatch).
        for o in sorted([x for d, xs in orders_by_day.items() if d <= key for x in xs], key=lambda x: x["date"]):
            if o.get("_done") or o["pieces"] < 1: continue
            c = o["code"]; can = min(o["pieces"], fg.get(c, 0.0))
            if can < 1: continue
            fg[c] -= can; lit = can * lpc(c); shipped += lit
            standing.append([today + timedelta(days=LAG), lit])
            o["pieces"] -= can
            if o["pieces"] < 1: o["_done"] = True
            day["dispatched"].append(dict(docnum=o["docnum"], customer=o["customer"][:40], channel=o["channel"],
                                          sku=plan[c]["sku"], pieces=round(can), litres=round(lit)))

    if working:
        # BUY — every material, ideal supply: it lands exactly on its lead time
        days_left = max(1, sum(1 for i in range((D1 - today).days + 1) if (today + timedelta(days=i)).weekday() != 6 or not SUNDAYS_OFF))
        need = collections.Counter()
        for c, b in book.items():
            w = max(b["plan_left"], b["po_left"] + b["fc_left"]) if RB is not None else max(b["plan_left"], b["po_left"])
            if w <= 0: continue
            for ch, per in bom.get(c, []): need[ch] += w * per
        for bl, kids in blends.items():
            if need.get(bl, 0) > 0:
                for ch, per in kids: need[ch] += need[bl] * per
        for m, tot in need.items():
            rate = tot / days_left
            if rate <= 0: continue
            lead = LEAD["oil"] if m.startswith("RM") else LEAD["packaging"]
            pipe = sum(inbound.get((today + timedelta(days=i)).isoformat(), {}).get(m, 0.0) for i in range(1, 40))
            cover = (stock.get(m, 0.0) + pipe) / rate
            if cover >= lead + 3 or days_left < 2: continue
            qty = rate * min(lead + 6, days_left + 1) - stock.get(m, 0.0) - pipe
            if qty <= 0 or (not m.startswith("RM") and qty < 500): continue
            land = today + timedelta(days=lead)
            if land > D1 + timedelta(days=7): continue
            inbound[land.isoformat()][m] += qty
            placed.append(dict(day=key, code=m, qty=round(qty), lands=land.isoformat()))
            day["bought"].append(dict(code=m, name=items.get(m, {}).get("name", m), qty=round(qty),
                                      uom=items.get(m, {}).get("uom", ""), lands=land.isoformat()))
            if stock.get(m, 0.0) < 1 and m not in ordered_for:
                ordered_for[m] = key
                ev(key, "ORDERED_BLOCKER", code=m, name=items.get(m, {}).get("name", m),
                   qty=round(qty), lands=land.isoformat(), lead=lead)

        zpm = [b for b in day["blocked"] if b["binder"].startswith("PM") and stock.get(b["binder"], 0) < 1]
        if zpm: ev(key, "PACKAGING_ZERO", items=[dict(code=z["binder"], name=z["binder_name"], sku=z["sku"], want=z["want"]) for z in zpm[:8]])
        zrm = [b for b in day["blocked"] if b["binder"].startswith("RM")]
        if zrm: ev(key, "OIL_SHORT", items=[dict(code=z["binder"], name=z["binder_name"], sku=z["sku"], want=z["want"]) for z in zrm[:6]])
        # a FORECAST slice must never be announced as a PO, whatever its size
        for n in [x for x in day["new_orders"] if x["value"] >= 5_000_000 and x["channel"] != "FORECAST"]: ev(key, "BIG_PO", **n)
        util = 1 - sum(free.values()) / (sum(hmax.values()) if RB is not None else hrs * len(L))
        if util < 0.5 and day["blocked"]: ev(key, "LINES_IDLE", util=round(util * 100), blocked=len(day["blocked"]))
        ev(key, "BUILD_LIST", lines={ln: [dict(sku=r["sku"], pieces=r["pieces"], hours=r["hours"], oil=r["oil"])
                                          for r in day["runs"] if r["line"] == ln] for ln in L})
        day.update(made_litres=round(made_l), made_value=round(sum(r["value"] for r in day["runs"])),
                   shipped_litres=round(shipped), oil_used_l=round(oil_day), line_util=round(util * 100),
                   line_hours={ln: round(hmax[ln] - free[ln], 1) for ln in L})
        # B20 — what the godown ceiling did TODAY, measured, not inferred. `stopped_products`
        # is how many products it stopped outright (they carry a held-up row naming STORAGE);
        # `capped_l` is the litres it took off runs it still allowed, i.e. how much more the
        # hours and the material on hand would have made with room to put it.
        day.update(storage_cap=dict(
            throttled=bool(throttle), headroom_l_at_open=round(headroom_open),
            headroom_l_at_close=round(max(0.0, headroom)),
            stopped_products=len(storage_stopped),
            stopped_codes=sorted(storage_stopped),
            capped_runs=storage_capped_runs, capped_l=round(storage_capped_l),
            ceiling_l=CEIL, pct_at_open=round((CEIL - headroom_open) / CEIL * 100, 1)))
        if RB is not None:
            # `blocked` is a row per ATTEMPT, and in rulebook mode one SKU is a candidate on
            # up to four lines — 484 rows behind 71 products on the worst day, against 288/50
            # on the legacy path. The row count reads as "484 stuck products" to anybody who
            # has not read this file, so the distinct codes go out beside it and nothing has
            # to be inferred from a length. Rulebook-mode only: the legacy day file is what
            # the August calibration and the -sep path were measured on, key for key.
            # A15/M2 — A NIGHT SESSION IS A ROSTER, THE HOURS ARE WHAT IT WORKED. `hours`
            # was the shift LENGTH the moment a session was opened, so a month of 22 opened
            # sessions printed as 22 night shifts to staff — a crew, a shift, a real labour
            # cost — against 10.5 hours of actual work, 10.0 of it on one day. The two are
            # now separate fields and the day says which is which.
            _night_runs = [r for r in day["runs"] if r.get("night")]
            _night_hours = sum(f(r["hours"]) + f(r.get("flush_min", 0)) / 60 for r in _night_runs)
            # AND WHAT THE SESSION ACTUALLY DID, in the same block as why the line was
            # picked. `reason` is chosen before the night runs — "the most ordered litres
            # still unmade" — and on a night that fills nothing it is the last thing a
            # reader should be left with. `outcome` is written after.
            if night is None:
                _outcome = "no second session tonight — " + (night_note or "nothing left to make")
            elif _night_runs:
                _outcome = (f"{round(_night_hours, 1)} h worked on {night}, "
                            f"{round(sum(f(r['litres']) for r in _night_runs)):,} L in "
                            f"{len(_night_runs)} run(s)")
            else:
                _outcome = (f"the second session on {night} was opened and NOTHING was made "
                            "in it — " + ("there was no room left in the godown (B20)"
                                          if storage_stopped or headroom < 1 else
                                          "no run could be started"))
            day.update(blocked_codes=sorted({b["code"] for b in day["blocked"]}),
                       line_hours_max={ln: round(hmax[ln], 1) for ln in L},
                       product_changes={ln: pchanges[ln] for ln in L},
                       night_line=dict(line=night, picked=night_picked, reason=night_note,
                                       po_backed_l_unmade=night_l,
                                       candidates=night_cands[:6],
                                       hours_rostered=(hrs if night else 0),
                                       hours_used=round(_night_hours, 2),
                                       runs=len(_night_runs),
                                       litres=round(sum(f(r["litres"]) for r in _night_runs)),
                                       worked=bool(_night_runs), outcome=_outcome,
                                       hours=(hrs if night else 0)))
    else:
        day.update(made_litres=0, made_value=0, shipped_litres=round(shipped), oil_used_l=0, line_util=0,
                   line_hours={ln: 0 for ln in L})
        day.update(storage_cap=dict(
            throttled=False, headroom_l_at_open=round(max(0.0, CEIL - physical())),
            headroom_l_at_close=round(max(0.0, CEIL - physical())),
            stopped_products=0, stopped_codes=[], capped_runs=0, capped_l=0,
            ceiling_l=CEIL, pct_at_open=round(physical() / CEIL * 100, 1)))
        if RB is not None:
            day.update(blocked_codes=[],
                       line_hours_max={ln: 0 for ln in L},
                       product_changes={ln: 0 for ln in L},
                       night_line=dict(line=None, picked=None,
                                       reason="Sunday — no production (R04)",
                                       po_backed_l_unmade=0, candidates=[],
                                       hours_rostered=0, hours_used=0.0, runs=0, litres=0,
                                       worked=False, hours=0,
                                       outcome="Sunday — no day session and no night one (R04)"))

    ph = physical()
    day.update(storage=dict(physical_l=round(ph), ceiling_l=CEIL, peak_l=PEAK, pct=round(ph / CEIL * 100, 1),
                            fg_in_godown_l=round(fg_litres()), invoiced_not_trucked_l=round(standing_l()),
                            headroom_l=round(CEIL - ph)),
               book=dict(plan_left_l=round(sum(b["plan_left"] * lpc(c) for c, b in book.items())),
                         po_open_l=round(sum(b["po_left"] * lpc(c) for c, b in book.items())),
                         po_open_value=round(sum(b["po_value"] for b in book.values())),
                         forecast_open_l=round(sum(b["fc_left"] * lpc(c) for c, b in book.items()))),
               oil_on_hand_l=round(sum(v for k, v in stock.items() if k in oils and v > 0)),
               waiting_on=[dict(code=c, name=items.get(c, {}).get("name", c), since=d) for c, d in sorted(ordered_for.items())],
               honesty=HON)
    days.append(day); today += timedelta(days=1)

OUT = f"sim/days{TAG}"
os.makedirs(OUT, exist_ok=True)
# A rolling re-plan writes FEWER day files than the last run (2 Sep: 29, not 30).
# Any day-NN.json left over from before is a stale artifact that a consumer will
# happily read as part of THIS run — clear them first.
import glob as _glob
for _old in _glob.glob(f"{OUT}/day-*.json"): os.remove(_old)
for i, d in enumerate(days, 1): json.dump(d, open(f"{OUT}/day-{i:02d}.json", "w"), indent=1)
json.dump(events, open(f"sim/events{TAG}.json", "w"), indent=1)
_summary = dict(days=[dict(date=d["date"], working=d["working"], made_l=d["made_litres"], value=d["made_value"],
    shipped_l=d["shipped_litres"], util=d["line_util"], storage_pct=d["storage"]["pct"], runs=len(d["runs"]),
    blocked=len(d["blocked"]), new_orders=len(d["new_orders"]), bought=len(d["bought"]),
    unblocked=len(d["unblocked"])) for d in days],
    # the run's OWN shift configuration, so no consumer has to infer the pattern back
    # out of the output (a taper whose tail days are material-bound, not hours-bound,
    # is indistinguishable from a flat run by inspection alone).
    shift=dict(hours=HOURS, schedule=(_os.environ.get("SIM_HOURS_SCHEDULE") or None),
               sundays_off=SUNDAYS_OFF, lines=len(L)),
    totals=dict(made_l=sum(d["made_litres"] for d in days), value=sum(d["made_value"] for d in days),
                shipped_l=sum(d["shipped_litres"] for d in days), orders=len(S["orders"]),
                bought_lines=len(placed), events=len(events),
                oil_used_l=sum(d["oil_used_l"] for d in days),
                negative_stocks={k: round(v) for k, v in sorted(stock.items()) if v < -1},
                actual_made_l=S["actuals_for_scoring"]["made_l"],
                actual_util=S["actuals_for_scoring"]["line_utilisation_pct"]))
# what the rulebook actually did to this run — the site says it out loud, and gen refuses
# to publish a plan whose engine did not apply it (unmapped codes, an hours override).
# a plain SKU that EVERY line refuses is otherwise invisible: it is never a candidate, so
# it is never blocked either, and it simply is not in the plan. A freeze that writes the
# legacy slot key for the Tin Head ({"TIN": …} instead of 15L/3L/5L) takes 12 tin SKUs and
# 493,984 L — 15% of the month — out with no error anywhere. Named, it is a gate.
# the distinct products stuck on a day, beside the attempt count — see day["blocked_codes"]
if RB is not None:
    for _row, _d in zip(_summary["days"], days):
        _row["blocked_codes"] = len(_d["blocked_codes"])
NO_LINE = sorted(c for c in plan if RB is not None and not plan[c].get("manual")
                 and all(rb_pref(c, ln) is None for ln in L)) if RB is not None else []
if RB is not None:
    _prefs = collections.Counter(r["pref"] for d in days for r in d["runs"])
    _summary["rulebook"] = dict(
        version=RB.get("version"), applied=True,
        hours_per_session=HOURS, hours_override=HOURS_OVERRIDE, inputs_shift_hours=R.get("shift_hours"),
        sundays_off=SUNDAYS_OFF, dispatch_on_sunday=True, efficiency_applied=EFF,
        manual_skus=MANUAL, unmapped_codes=sorted(unmapped_codes),
        multi_fill_skus=sorted(c for c in plan if fills(c) > 1),
        multi_fill_no_rate=sorted(c for c in plan if fills(c) > 1 and all(rb_pref(c, ln) is None for ln in L)),
        no_line_skus=NO_LINE,
        trailing_source=TRAIL_SOURCE, no_trailing_codes=NO_TRAILING,
        honesty_dropped=honesty_dropped,
        # A SESSION OPENED IS NOT A NIGHT'S WORK. `night_sessions` counts the roster;
        # `night_sessions_worked`, `night_hours_used` and `night_litres` count what was
        # done in it. A plant manager reads 22 second sessions as 22 crews to staff, and
        # this run's 22 opened sessions did 10.5 hours between them, 10.0 of it on one
        # day. Both numbers go out, named apart, and the site leads with the hours.
        night_sessions=sum(1 for d in days if (d.get("night_line") or {}).get("line")),
        night_sessions_worked=sum(1 for d in days
                                  if (d.get("night_line") or {}).get("hours_used", 0) > 0),
        night_hours_used=round(sum(f((d.get("night_line") or {}).get("hours_used"))
                                   for d in days), 2),
        night_hours_rostered=sum(f((d.get("night_line") or {}).get("hours_rostered"))
                                 for d in days),
        night_litres=round(sum(f((d.get("night_line") or {}).get("litres")) for d in days)),
        night_by_day={d["date"]: {"line": (d.get("night_line") or {}).get("line"),
                                  "hours_used": (d.get("night_line") or {}).get("hours_used"),
                                  "litres": (d.get("night_line") or {}).get("litres"),
                                  "runs": (d.get("night_line") or {}).get("runs")}
                      for d in days},
        night_line_by_day={d["date"]: (d.get("night_line") or {}).get("line") for d in days},
        night_reason_by_day={d["date"]: (d.get("night_line") or {}).get("reason") for d in days},
        prefs_used={str(k): _prefs[k] for k in sorted(_prefs)},
        # which SKUs two machines would fill at the same preference AND the same planning
        # litres an hour. Their home line — the one the night measure counts them on — is
        # the line NAME's choice and nothing else's, so it is published rather than hidden.
        home_ties={c: t for c in sorted(plan) if (t := rb_home_tie(c))},
        change_cap_lifted=sum(1 for d in days for x in d["decisions"] if x["kind"] == "CHANGE_CAP_LIFTED"),
        # R06 asks for ONE product on a line all day; B02 allows one change a session free
        # and logs the rest. Publishing only the lifts understates the distance from R06 by
        # every free change, so the true total and the per-line split go out beside them —
        # and `change_cap_lifted_twice_or_more` is the count B02, read literally, forbids.
        product_changes=sum(sum(d.get("product_changes", {}).values()) for d in days),
        product_changes_by_line={ln: sum(d.get("product_changes", {}).get(ln, 0) for d in days)
                                 for ln in L},
        change_cap_lifted_twice_or_more=sum(1 for d in days for x in d["decisions"]
                                            if x["kind"] == "CHANGE_CAP_LIFTED" and x["nth"] > 1),
        runs_by_family=dict(collections.Counter(r["family"] for d in days for r in d["runs"])),
        lines_used=sorted({r["line"] for d in days for r in d["runs"]}))
json.dump(_summary, open(f"sim/summary{TAG}.json", "w"), indent=1)

# conservation law: bulk oil consumed must reconcile to litres produced
_oil = sum(d["oil_used_l"] for d in days); _made = sum(d["made_litres"] for d in days)
_neg = {k: round(v) for k, v in stock.items() if v < -1}
print(f"  CONSERVATION  oil consumed {_oil:,.0f} L vs produced {_made:,.0f} L "
      f"-> {abs(_oil - _made) / _made * 100 if _made else 0:.2f}% gap; negative stocks: {_neg or 'none'}")

t = sum(d["made_litres"] for d in days); v = sum(d["made_value"] for d in days)
A = S["actuals_for_scoring"]
print(f"=== MARK 4 — rulebook {RB['version']}, {HOURS:.0f} h a session, one line at night ===" if RB
      else f"=== AUGUST v2 — measured 1-Aug opening, {EFF*100:.0f}% observed line speed ===")
print(f"  PLANNED BY THE ALGO   {t:>12,.0f} L    Rs {v/1e7:.2f} Cr")
print(f"  the plant ACTUALLY did{A['made_l']:>12,.0f} L    ({A['line_utilisation_pct']}% utilisation)")
print(f"  vs plan 4,141,400 L   {t/4141400*100:>11.1f}%   (actual was {A['plan_pct']}%)")
print(f"  shipped               {sum(d['shipped_litres'] for d in days):>12,.0f} L")
print(f"  orders placed {len(placed)}   unblock events {sum(len(d['unblocked']) for d in days)}")
if RB is not None:
    _nl = collections.Counter(x for d in days if (x := (d.get("night_line") or {}).get("line")))
    print(f"  night sessions {sum(_nl.values())} — {', '.join(f'{k} x{v}' for k, v in _nl.most_common())}")
    _lift = [x for d in days for x in d["decisions"] if x["kind"] == "CHANGE_CAP_LIFTED"]
    print(f"  hand-filled, never scheduled: {', '.join(MANUAL) or 'none'}")
    print(f"  product changes {sum(sum(d.get('product_changes', {}).values()) for d in days)} — "
          f"{len(_lift)} of them lifted the one-a-session cap to keep a line busy, "
          f"{sum(1 for x in _lift if x['nth'] > 1)} of those a second lift or more (R06/B02)")
    print(f"  expected-only SKUs ranked on {TRAIL_SOURCE}"
          + (f"   ·   {len(NO_TRAILING)} with no sales behind them go last (R19): "
             f"{', '.join(NO_TRAILING[:6])}{' …' if len(NO_TRAILING) > 6 else ''}" if NO_TRAILING else ""))
    if NO_LINE:
        print(f"  !! NO MACHINE FILLS THESE {len(NO_LINE)} SKU(s), so they are in no day of the "
              f"plan: {', '.join(NO_LINE)}")
    if honesty_dropped:
        print(f"  !! {len(honesty_dropped)} carried honesty line(s) dropped — the freeze tagged "
              f"them for the legacy path, and this is a rulebook run")
print("")
print(f"  {'DAY':<12}{'MADE L':>10}{'SHIP L':>10}{'UTIL':>6}{'STORE':>7}{'RUNS':>5}{'BLK':>4}{'PO+':>4}{'BUY':>4}{'UNBL':>5}")
for d in days:
    print(f"  {d['date']:<12}{d['made_litres']:>10,}{d['shipped_litres']:>10,}{d['line_util']:>5}%"
          f"{d['storage']['pct']:>6}%{len(d['runs']):>5}{len(d['blocked']):>4}{len(d['new_orders']):>4}"
          f"{len(d['bought']):>4}{len(d['unblocked']):>5}")
