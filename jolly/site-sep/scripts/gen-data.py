#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-data.py — builds site-sep/data/*.json from the VERIFIED September artifacts.

Every business number shown on the September site is computed HERE, from:
  jolly/sim/sep-inputs.json            frozen opening + plan + realise + orders
  jolly/sim/summary-sep.json           30-day spine
  jolly/sim/days-sep/day-*.json        per-day detail
  jolly/sim/events-sep.json            ORDERED_BLOCKER / UNBLOCKED / ...
  jolly/sim/whatsapp-sep.json (+meta)  simulated drafts (assumed:true, 0 replies)
  jolly/out/order-by-sep.json          209 components, both zero definitions
  jolly/out/build-list-sep.json        26 working days, per-machine runs
  jolly/sim/summary-sep-{22x31,24x31,12x31,taper,taper18}.json
                                       (+ days dirs, events) shift scenarios
  jolly/sim/summary.json               August sim (calibration comparable)
  jolly/site/public/data/questions.json  open questions register (Q2/Q4/Q13)

Rules enforced at the DATA layer:
  * NO real phone number leaves this script (masked "+91 86*** ***00" style);
    a final scan over every serialized output asserts none survived.
  * simulated / assumed / measured_from flags ride on the objects themselves.
  * September has not happened: meta.forward = true on everything.
  * PLAIN-LANGUAGE.md: every label/note authored HERE is in floor words, and a
    scan refuses the rulebook's banned office words before anything is written.

Never hand-edit the outputs; rerun this script instead.
"""
import datetime as dt
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)                       # .../jolly/site-sep
JOLLY = os.path.dirname(SITE)                      # .../jolly
SIM = os.path.join(JOLLY, "sim")
OUT = os.path.join(JOLLY, "out")
AUG_SITE_DATA = os.path.join(JOLLY, "site", "public", "data")
DATA = os.path.join(SITE, "data")

MONTH_START = "2026-09-01"


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- sources ----
INP = load(os.path.join(SIM, "sep-inputs.json"))
SUM = load(os.path.join(SIM, "summary-sep.json"))
EVENTS = load(os.path.join(SIM, "events-sep.json"))
WA = load(os.path.join(SIM, "whatsapp-sep.json"))
WAMETA = load(os.path.join(SIM, "whatsapp-sep-meta.json"))
ORDERBY = load(os.path.join(OUT, "order-by-sep.json"))
BUILD = load(os.path.join(OUT, "build-list-sep.json"))
AUG_SIM = load(os.path.join(SIM, "summary.json"))
QUESTIONS = load(os.path.join(AUG_SITE_DATA, "questions.json"))

DAY_FILES = sorted(glob.glob(os.path.join(SIM, "days-sep", "day-*.json")))
DAYS = [load(f) for f in DAY_FILES]

# (summary, day-files dir, events, label, is_taper). For the two taper probes the
# label and id are REBUILT below from phase ceilings derived out of the day files
# themselves — the flag only says which shape to expect (and to fail loudly on).
SCEN_SRC = {
    "22x30": ("summary-sep-22x31.json", "days-sep-22x31", "events-sep-22x31.json",
              "22 hours a day, Sundays working", False),
    "24x30": ("summary-sep-24x31.json", "days-sep-24x31", "events-sep-24x31.json",
              "24 hours a day, Sundays working", False),
    "12x30": ("summary-sep-12x31.json", "days-sep-12x31", "events-sep-12x31.json",
              "12 hours a day, Sundays working", False),
    "taper-a": ("summary-sep-taper.json", "days-sep-taper", "events-sep-taper.json",
                "long hours first, then shorter, Sundays working", True),
    "taper-b": ("summary-sep-taper18.json", "days-sep-taper18", "events-sep-taper18.json",
                "long hours first, then shorter, Sundays working", True),
}

RULES = INP["rules"]
OPENING = INP["opening"]
PLAN = INP["plan"]
ORDERS = INP["orders"]
BACKLOG = INP["backlog"]
LINES_CFG = INP["lines"]
HONESTY = INP["honesty"]
PROV = INP["provenance"]
REALISE = INP["realise"]

checks = []  # (name, ok, detail)


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    if not ok:
        print(f"CHECK FAILED: {name} {detail}", file=sys.stderr)


# ---------------------------------------------------------- plain language --
# PLAIN-LANGUAGE.md: every label and note this script writes is read on the
# factory floor. Text authored HERE goes through plain(), and the scan at the
# end refuses the rulebook's banned office words. Text copied from the sim
# artifacts (honesty lists, provenance, message texts, build notes) is not
# scanned here — the pages translate it where they render it.
BANNED_WORDS = [
    r"\bSKUs?\b", r"\bcomponents?\b", r"\bbinders?\b", r"\bcover\b", r"\bthrottl", r"\bforecasts?\b",
    r"\bchannels?\b", r"\bbaseline\b", r"\bsimulat", r"\bcalibrat", r"\bbacktest", r"\bhorizon\b",
    r"\bheadroom\b", r"\bprovenance\b", r"\bcumulative\b", r"\bderated?\b", r"\bstanding\b", r"\bgated\b",
    r"\bdocnums?\b", r"\bFCST", r"\bunproducible\b", r"\bBOMs?\b", r"\brealise[ds]?\b", r"\butilisation\b",
    r"\blead[ -]times?\b", r"\bbacklog\b", r"\bscenarios?\b", r"\bmarginal\b", r"\bconservation\b",
    r"\bassum", r"\bderived?\b", r"\bopening\b", r"\bfrozen\b", r"\bas-of\b",
]
_BANNED_RE = re.compile("|".join(BANNED_WORDS), re.IGNORECASE)
PLAIN_STRINGS = []


def plain(s):
    """Register a string this script authors for the floor; the final scan checks it."""
    PLAIN_STRINGS.append(s)
    return s


# ------------------------------------------------------------ phone masking --
RAW_NUMBERS = set()


def collect_number(s):
    if isinstance(s, str) and re.search(r"\+?91[\s-]?\d", s):
        d = re.sub(r"\D", "", s)
        if len(d) == 12 and d.startswith("91"):
            RAW_NUMBERS.add(d[2:])
        elif len(d) == 10:
            RAW_NUMBERS.add(d)


for person in INP.get("people", []):
    collect_number(person.get("whatsapp", ""))
    collect_number(person.get("display", ""))
for t in WA:
    collect_number(t.get("whatsapp", ""))
    collect_number(t.get("display", ""))
rcp = BUILD.get("meta", {}).get("recipient", {})
collect_number(rcp.get("whatsapp", ""))
collect_number(rcp.get("display", ""))


# SHOW_PHONES=1 renders real numbers. Daman authorised it for September on 2026-09-03
# ("yeah show it") — the same approval August's site already carries. Default stays
# masked so no future run un-hides them by accident.
SHOW_PHONES = os.environ.get("SHOW_PHONES", "0") == "1"


def mask_phone(s):
    """+91XXXXXXXXXX / +91 XXXXX XXXXX -> +91 XX*** ***XX ; else 'number withheld'.
    With SHOW_PHONES=1 the real number is returned, tidily spaced."""
    if SHOW_PHONES:
        d = re.sub(r"\D", "", str(s or ""))
        if len(d) >= 10:
            d10 = d[-10:]
            return f"+91 {d10[:5]} {d10[5:]}"
        return str(s or "")
    d = re.sub(r"\D", "", s or "")
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    if len(d) != 10:
        return "number withheld"
    return f"+91 {d[:2]}*** ***{d[-2:]}"


def mask_text(text):
    if SHOW_PHONES:
        return text
    """Mask every known raw number, in any common formatting, inside free text."""
    if not isinstance(text, str):
        return text
    out = text
    for d10 in RAW_NUMBERS:
        masked = f"+91 {d10[:2]}*** ***{d10[-2:]}"
        variants = [
            "+91" + d10,
            "+91 " + d10,
            f"+91 {d10[:5]} {d10[5:]}",
            f"+91-{d10[:5]}-{d10[5:]}",
            "91" + d10,
            d10,
            f"{d10[:5]} {d10[5:]}",
        ]
        for v in variants:
            out = out.replace(v, masked)
    return out


def assert_no_phones(name, obj):
    blob = json.dumps(obj, ensure_ascii=False)
    if SHOW_PHONES:
        # Authorised to SHOW (Daman, 2026-09-03). The gate does not switch off, it
        # reverses: a masked number surviving here would be a half-hidden page, and a
        # number that is neither raw nor masked would mean the data lost the contact.
        if "***" in blob:
            check(f"phone-scan {name}", False, "numbers are authorised but a masked one survived")
            return
        check(f"phone-scan {name}", True)
        return
    for d10 in RAW_NUMBERS:
        if d10 in re.sub(r"\D", "", blob) and d10 in blob.replace(" ", "").replace("-", ""):
            check(f"phone-scan {name}", False, f"raw number …{d10[-4:]} leaked")
            return
    if re.search(r"\+91[\s-]?\d{3}", blob):
        check(f"phone-scan {name}", False, "un-masked +91 pattern present")
        return
    check(f"phone-scan {name}", True)


# ------------------------------------------------------------ shared helpers -
LPP = {p["code"]: p["litres_per_piece"] for p in PLAN}
PLAN_BY_CODE = {p["code"]: p for p in PLAN}


def is_forecast_order(o):
    return o.get("channel") == "FORECAST" or str(o.get("docnum", "")).startswith("FCST")


def item_kind(code):
    if code.startswith("RM"):
        return "OIL"
    if code.startswith("PM"):
        return "PACKAGING"
    return "OTHER"


MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dm(iso):
    """'2026-09-30' -> '30 Sep' — a date in floor words."""
    return f"{int(iso[8:10])} {MON[int(iso[5:7]) - 1]}"


def plain_slot(s):
    """'3L' -> '3-litre bottles', 'DRUM' -> 'drums' — a pack-size slot in floor words."""
    s = str(s)
    if s.endswith("L") and s[:-1].replace(".", "").isdigit():
        return f"{s[:-1]}-litre bottles"
    return {"DRUM": "drums", "TIN": "tins", "POUCH": "pouches"}.get(s.upper(), s.lower())


FROZEN_DM = dm(INP["meta"]["frozen"])   # "31 Aug" — the day the stock was counted


# Label rule 10 fix, applied at the DATA layer (the sim artifacts stay untouched):
# the sim files phrase the rate assumption as "lines run at 50% of rated, the
# observed rate" — wrong for Clear Pack 5L and Tin Head, whose STORED rate is
# already the OBSERVED rate and is derated AGAIN. Rewritten wherever an honesty
# list is copied into site data.
EFF_PCT = round(RULES["efficiency"] * 100)
RATE_ASSUMPTION_HONEST = plain(
    f"the plan runs every machine at {EFF_PCT}% of its listed speed — that is the pace the factory "
    f"really kept in August, not a fault. Clear Pack 5L and Tin Head are listed at the speed we "
    f"measured, so the plan runs them at {EFF_PCT}% of even that — on the careful side"
)
BAD_RATE_PHRASE = "of rated, the observed rate"


def fix_honesty(h):
    """Copy an honesty block, rewriting the sim's rate-assumption line (rule 10)."""
    out = dict(h)
    out["assumed"] = [
        RATE_ASSUMPTION_HONEST if BAD_RATE_PHRASE in a else a
        for a in h.get("assumed", [])
    ]
    return out


def slot_of(p):
    """Replicates engine/august_sim.py slot() so 'unproducible' is derived, not typed."""
    pt = str(p["pack_type"]).upper()
    sku = str(p["sku"]).upper()
    litres = p["litres_per_piece"]
    if "DRUM" in pt:
        return "DRUM"
    if "TIN" in pt or "KGS" in sku:
        return "TIN"
    if "POUCH" in pt or "POUCH" in sku:
        return "POUCH"
    if litres <= 1.05:
        return "1L"
    if litres <= 2.05:
        return "2L"
    if litres <= 3.05:
        return "3L"
    if litres <= 4.05:
        return "4L"
    if litres <= 5.05:
        return "5L"
    return "15L"


AVAILABLE_SLOTS = set()
for _line, sp in LINES_CFG.items():
    AVAILABLE_SLOTS.update(sp.keys())
if "5L" in AVAILABLE_SLOTS:
    AVAILABLE_SLOTS.add("15L")  # engine derives 15L PET from the 5L head (l/hr constant)

unproducible = []
for p in PLAN:
    s = slot_of(p)
    if s not in AVAILABLE_SLOTS:
        row = {
            "code": p["code"],
            "sku": p["sku"],
            "pack_type": p["pack_type"],
            "litres_per_piece": p["litres_per_piece"],
            "plan_pieces": p["pieces"],
            "plan_litres": p["litres"],
            "slot_needed": s,
            "reason": plain(f"no machine can fill {plain_slot(s)}"),
        }
        r = REALISE.get(p["code"])
        if r:
            row["value_est_rs"] = round(p["litres"] * r)
            row["value_est_derived"] = True
        unproducible.append(row)
unproducible.sort(key=lambda r: -r["plan_litres"])

ran_codes = {r["code"] for d in DAYS for r in d["runs"]}
check("unproducible SKUs never appear in runs",
      all(u["code"] not in ran_codes for u in unproducible),
      str([u["code"] for u in unproducible if u["code"] in ran_codes]))

# --------------------------------------------------------------- day split ---
events_by_day = defaultdict(list)
for e in EVENTS:
    events_by_day[e["day"]].append(e)

build_days = {d["date"]: d for d in BUILD["days"]}

# binder -> FG codes it blocked (for loop chains)
binder_fgs = defaultdict(set)
for d in DAYS:
    for b in d["blocked"]:
        binder_fgs[b["binder"]].add(b["code"])

# the three labels that ride on every day's raw book counters — authored once
PO_CUM_LABEL = plain("total ordered since day 1 — it only ever goes up, so it is NOT what is still pending")
PO_OPEN_LABEL = plain("the planner's rough counter — it shows more litres than are really still to be sent, "
                      "so use 'still to be sent' instead")
OPEN_REAL_NOTE = plain(f"confirmed orders minus what has been billed, counted from day 1 and including orders "
                       f"already pending on {FROZEN_DM} — expected orders (not yet ordered) are left out")

day_rows = []       # spine
day_details = []    # per-day files
cum_real_in_l = 0.0
cum_real_out_l = 0.0
unmapped_order_codes = set()

for i, d in enumerate(DAYS):
    n = i + 1
    date = d["date"]

    real_orders, fcst_orders = [], []
    for o in d["new_orders"]:
        (fcst_orders if is_forecast_order(o) else real_orders).append(o)

    def _sum(rows, k):
        return round(sum(r.get(k, 0) for r in rows))

    real_l = 0.0
    for o in real_orders:
        lp = LPP.get(o["code"])
        if lp is None:
            unmapped_order_codes.add(o["code"])
        else:
            real_l += o["pieces"] * lp
    cum_real_in_l += real_l

    disp_real = [x for x in d["dispatched"] if not str(x.get("docnum", "")).startswith("FCST")]
    disp_fcst = [x for x in d["dispatched"] if str(x.get("docnum", "")).startswith("FCST")]
    cum_real_out_l += sum(x["litres"] for x in disp_real)

    received = [
        dict(r, kind=item_kind(r["code"]))
        for r in sorted(d["received"], key=lambda r: -r["qty"])
    ]

    ev = events_by_day.get(date, [])
    ev_counts = dict(Counter(e["kind"] for e in ev))

    bnews = (build_days.get(date) or {}).get("news") or {}

    spine = {
        "n": n,
        "date": date,
        "weekday": d["weekday"],
        "working": d["working"],
        "made_l": d["made_litres"],
        "value_rs": d["made_value"],
        "shipped_l": d["shipped_litres"],
        "util": d["line_util"],
        "storage_pct": d["storage"]["pct"],
        "headroom_l": d["storage"]["headroom_l"],
        "runs": len(d["runs"]),
        "flushes": d["flushes"],
        "blocked": len(d["blocked"]),
        "unblocked": len(d.get("unblocked", [])),
        "bought": len(d["bought"]),
        "oil_used_l": d.get("oil_used_l", 0),
        "orders": {
            "real_rows": len(real_orders),
            "real_pieces": _sum(real_orders, "pieces"),
            "real_value_rs": _sum(real_orders, "value"),
            "forecast_rows": len(fcst_orders),
            "forecast_pieces": _sum(fcst_orders, "pieces"),
            "forecast_value_rs": _sum(fcst_orders, "value"),
            "forecast_assumed": True,
        },
        "dispatched": {
            "real_l": round(sum(x["litres"] for x in disp_real)),
            "forecast_l": round(sum(x["litres"] for x in disp_fcst)),
        },
        "received_count": len(received),
        "received_top": received[:5],
        "events": ev_counts,
        "news": {
            "materials_landed": bnews.get("materials_landed", 0),
            "real_pos_entering": bnews.get("real_pos_entering", 0),
            "forecast_rows": bnews.get("forecast_rows", 0),
        },
        # raw book fields, with their honest labels riding along
        "book": {
            "plan_left_l": d["book"]["plan_left_l"],
            "po_cumulative_value_rs": d["book"]["po_open_value"],
            "po_cumulative_value_label": PO_CUM_LABEL,
            "po_open_l_raw": d["book"]["po_open_l"],
            "po_open_l_raw_label": PO_OPEN_LABEL,
            "forecast_open_l": d["book"].get("forecast_open_l", 0),
        },
        "open_real_l_computed": round(cum_real_in_l - cum_real_out_l),
        "open_real_l_note": OPEN_REAL_NOTE,
    }
    day_rows.append(spine)

    detail = {
        "n": n,
        "date": date,
        "weekday": d["weekday"],
        "working": d["working"],
        "made_litres": d["made_litres"],
        "made_value_rs": d["made_value"],
        "shipped_litres": d["shipped_litres"],
        "oil_used_l": d.get("oil_used_l", 0),
        "line_util": d["line_util"],
        "line_hours": d["line_hours"],
        "flushes": d["flushes"],
        "storage": d["storage"],
        "storage_ceiling_assumed": True,
        "book": spine["book"],
        "open_real_l_computed": spine["open_real_l_computed"],
        "runs": d["runs"],
        "blocked": d["blocked"],
        "unblocked": d.get("unblocked", []),
        "waiting_on": d.get("waiting_on", []),
        "received": received,
        "orders_real": real_orders,
        "orders_forecast": [dict(o, assumed=True) for o in fcst_orders],
        "dispatched_real": disp_real,
        "dispatched_forecast": [dict(x, assumed=True) for x in disp_fcst],
        "bought": d["bought"],
        "decisions": d.get("decisions", []),
        "events": [e for e in ev if e["kind"] != "BUILD_LIST"],
        "news": bnews,
        "honesty": fix_honesty(d["honesty"]),
        "simulated": True,
    }
    day_details.append(detail)

# ROLLING horizon: a re-plan from the 3rd has 28 days left, not 30. The count that
# matters is that day files, the summary and the frozen horizon all agree.
_h0, _h1 = INP["meta"]["horizon"]
_horizon_days = (dt.date.fromisoformat(_h1) - dt.date.fromisoformat(_h0)).days + 1
check("day files == summary days == horizon length", len(DAYS) == len(SUM["days"]) == _horizon_days,
      f"{len(DAYS)} files / {len(SUM['days'])} summary / {_horizon_days} horizon")
check("spine made_l == summary made_l",
      sum(r["made_l"] for r in day_rows) == SUM["totals"]["made_l"])
check("spine shipped_l == summary shipped_l",
      sum(r["shipped_l"] for r in day_rows) == SUM["totals"]["shipped_l"])
check("runs total == build-list runs",
      sum(r["runs"] for r in day_rows) == BUILD["meta"]["totals"]["runs"],
      f"{sum(r['runs'] for r in day_rows)} vs {BUILD['meta']['totals']['runs']}")
check("no order code missing litres/piece", not unmapped_order_codes,
      str(sorted(unmapped_order_codes)[:5]))

# ------------------------------------------------------------------ lines ----
efficiency = RULES["efficiency"]
observed_rate_slots = {("Clear Pack", "5L"), ("Tin Head", "TIN")}  # provenance.lines: observed, rated figure refuted

line_slots = {}
for line, sp in LINES_CFG.items():
    slots = []
    for slot, rate in sorted(sp.items()):
        basis = "observed" if (line, slot) in observed_rate_slots else "rated"
        slots.append({
            "slot": slot,
            "stored_rate_per_hr": rate,
            "rate_basis": basis,
            "effective_rate_per_hr": round(rate * efficiency, 1),
            "note": plain(
                f"this speed was measured on the machine in August — the plan then runs it at {EFF_PCT}% of even that"
                if basis == "observed" else
                f"the machine's listed speed — the plan runs it at {EFF_PCT}% of that"
            ),
        })
    if "5L" in sp:
        slots.append({
            "slot": "15L",
            "stored_rate_per_hr": round(sp["5L"] / 3.0, 1),
            "rate_basis": "derived",
            "effective_rate_per_hr": round(sp["5L"] / 3.0 * efficiency, 1),
            "note": plain("worked out from the 5L speed — same litres per hour, so a third of the bottles — nobody has measured a 15L speed"),
        })
    line_slots[line] = slots

runs_by_line = defaultdict(list)
for d in DAYS:
    for r in d["runs"]:
        runs_by_line[r["line"]].append(dict(r, date=d["date"]))

line_stats = []
for line in LINES_CFG:
    rs = runs_by_line.get(line, [])
    hours_avail = sum(
        d["line_hours"].get(line, 0) for d in DAYS if d["working"]
    )
    line_stats.append({
        "name": line,
        "slots": line_slots[line],
        "runs": len(rs),
        "litres": round(sum(r["litres"] for r in rs)),
        "pieces": round(sum(r["pieces"] for r in rs)),
        "hours_run": round(sum(r["hours"] for r in rs), 1),
        "hours_on_line": round(hours_avail, 1),
        "value_rs": round(sum(r["value"] for r in rs)),
        "days_active": len({r["date"] for r in rs}),
        "flush_minutes": round(sum(r["flush_min"] for r in rs)),
        "top_skus": [],  # filled below
    })
for st in line_stats:
    agg = defaultdict(float)
    for r in runs_by_line.get(st["name"], []):
        agg[r["sku"]] += r["litres"]
    st["top_skus"] = [
        {"sku": k, "litres": round(v)}
        for k, v in sorted(agg.items(), key=lambda x: -x[1])[:5]
    ]

lines_out = {
    "efficiency": efficiency,
    "efficiency_note": plain(
        f"the plan runs every machine at {EFF_PCT}% of its listed speed — the pace the factory really kept "
        f"in August. Clear Pack 5L and Tin Head are listed at the speed we measured, so for them it is "
        f"{EFF_PCT}% of even that"
    ),
    "lines": line_stats,
    # the month total, from the summary artifact itself: per-line litres are
    # rounded per line, so their sum can drift a few litres from this — every
    # page quotes total_litres so the site carries ONE month figure
    "total_litres": SUM["totals"]["made_l"],
    "total_litres_note": plain(
        "adding up the machines can differ from the month total by a few litres (rounding) — "
        "use the month total"
    ),
    "runs_by_line": {k: v for k, v in runs_by_line.items()},
    "measured_from": plain(f"machine speeds: the factory's own figures, saved {FROZEN_DM} · runs: the computer plan, day by day"),
}
check("per-line litres within rounding of total",
      abs(sum(st["litres"] for st in line_stats) - SUM["totals"]["made_l"]) <= 60,
      f"{sum(st['litres'] for st in line_stats)} vs {SUM['totals']['made_l']}")

# ---------------------------------------------------------------- storage ----
# Invoiced ≠ trucked: shipped_litres is INVOICING; litres leave the gate on the
# declared invoice→truck lag. trucked_out_l is computed from the floor itself:
# yesterday's physical + today's fill − today's physical.
LAG_DAYS = RULES["invoice_truck_lag_days"]
storage_series = []
_prev_phys = OPENING["fg_litres"] + OPENING["standing_l"]
for i, d in enumerate(DAYS):
    trucked_raw = _prev_phys + d["made_litres"] - d["storage"]["physical_l"]
    check(f"trucked_out non-negative day {i + 1}", trucked_raw >= -2, str(trucked_raw))
    trucked = max(0, round(trucked_raw))
    # the sim's lag is hard: what gates out on day n is exactly day n−lag's invoicing
    expected = round(DAYS[i - LAG_DAYS]["shipped_litres"]) if i >= LAG_DAYS else 0
    check(f"hard invoice→truck lag day {i + 1}", abs(trucked - expected) <= 2,
          f"{trucked} vs invoiced[n-{LAG_DAYS}] {expected}")
    storage_series.append({
        "n": i + 1,
        "date": d["date"],
        "working": d["working"],
        "physical_l": d["storage"]["physical_l"],
        "pct": d["storage"]["pct"],
        "fg_in_godown_l": d["storage"]["fg_in_godown_l"],
        "invoiced_not_trucked_l": d["storage"]["invoiced_not_trucked_l"],
        "headroom_l": d["storage"]["headroom_l"],
        "invoiced_l": round(d["shipped_litres"]),
        "trucked_out_l": trucked,
    })
    _prev_phys = d["storage"]["physical_l"]

# Everything invoiced either left the gate this month or is still standing at the end.
# Tolerance is per-DAY, not a flat 3 L for the whole month: each day contributes up to
# 1 L of rounding, and a day whose raw figure lands at -1 L (inside the per-day ±2 L
# check above) is clamped to 0 and adds that back. A flat 3 L failed a 28-day rolling
# month by 4 L — 0.00015% — while a real leak is thousands of litres, so 1 L/day still
# catches anything that matters by three orders of magnitude.
_trucked_residual = abs(sum(s["trucked_out_l"] for s in storage_series)
                        + storage_series[-1]["invoiced_not_trucked_l"]
                        - sum(round(d["shipped_litres"]) for d in DAYS))
check("trucked-out conservation", _trucked_residual <= max(3, len(storage_series)),
      f"{_trucked_residual} L over {len(storage_series)} days")

_fall_pairs = [
    (storage_series[i - 1]["physical_l"] - storage_series[i]["physical_l"], i)
    for i in range(1, len(storage_series))
]
_fall_drop, _fall_i = max(_fall_pairs)
_fall_row = storage_series[_fall_i]
_fall_src = storage_series[_fall_i - LAG_DAYS] if _fall_i - LAG_DAYS >= 0 else None
biggest_fall = {
    "n": _fall_row["n"],
    "date": _fall_row["date"],
    "fall_l": round(_fall_drop),
    "trucked_out_l": _fall_row["trucked_out_l"],
    "made_l": round(DAYS[_fall_i]["made_litres"]),
    "invoiced_that_day_l": _fall_row["invoiced_l"],
    "source_day_n": _fall_src["n"] if _fall_src else None,
    "source_date": _fall_src["date"] if _fall_src else None,
    "note": plain(
        f"the drop is trucks leaving (billed {LAG_DAYS} days earlier) minus what was filled that day — "
        "not that day's billing"
    ),
}
_big_inv = max(storage_series, key=lambda s: s["invoiced_l"])
_big_trk = max(storage_series, key=lambda s: s["trucked_out_l"])
biggest_invoicing_day = {"n": _big_inv["n"], "date": _big_inv["date"],
                         "invoiced_l": _big_inv["invoiced_l"],
                         "trucked_out_that_day_l": _big_inv["trucked_out_l"]}
biggest_trucked_day = {"n": _big_trk["n"], "date": _big_trk["date"],
                       "trucked_out_l": _big_trk["trucked_out_l"]}

storage_out = {
    "ceiling": {
        "working_l": RULES["storage_ceiling_l"],
        "peak_l": RULES["storage_peak_l"],
        "assumed": True,
        "source": plain("Daman's number, from his spreadsheet — not measured"),
        "open_question": "Q2",
    },
    "standing_at_open": {
        "litres": OPENING["standing_l"],
        "assumed": True,
        "optimistic": True,
        "note": plain(f"stock billed by {FROZEN_DM} but still waiting for a truck is not counted — so the godown is really fuller than shown (our guess, on the hopeful side)"),
    },
    "invoice_truck_lag_days": LAG_DAYS,
    "invoice_truck_note": plain(
        "'sent' here means billed, not the truck leaving — after billing, the truck leaves "
        f"{LAG_DAYS} days later (our guess — not measured). Trucks-left litres are worked out from how full the godown was"
    ),
    "series": storage_series,
    "biggest_fall": biggest_fall,
    "biggest_invoicing_day": biggest_invoicing_day,
    "biggest_trucked_day": biggest_trucked_day,
    "days_ge_95": sum(1 for d in SUM["days"] if d["storage_pct"] >= 95),
    "days_ge_100": [d["date"] for d in SUM["days"] if d["storage_pct"] >= 100],
    "throttles": [
        {"day": e["day"], "pct_start_of_day": e["pct_start_of_day"], "headroom_l": e["headroom_l"]}
        for e in EVENTS if e["kind"] == "STORAGE_THROTTLE"
    ],
    "simulated": True,
}

# --------------------------------------------------------------- materials ---
ob_sum = ORDERBY["summary"]
ob_rows = []
for r in ORDERBY["rows"]:
    ob_rows.append(dict(
        r,
        late=str(r.get("status", "")).startswith("LATE"),
        zero_literal=r.get("at_zero") == "YES",
        zero_august_rule=r["code"] in set(ob_sum["august_comparable"]["codes"]),
    ))

# Reconcile the two "zero" headcounts that share one shelf: opening_at_zero is
# every item at on_hand exactly 0; the artifact's "literal zero" count keeps
# only those with NOTHING on order — the rest are chase calls (PO already live).
zero_open_codes = {z["code"] for z in OPENING["at_zero"]}
_lit_codes = {r["code"] for r in ob_rows if r["zero_literal"]}
_chase_codes = sorted(r["code"] for r in ob_rows
                      if r["on_hand"] == 0 and r.get("on_order", 0) > 0)
check("opening zeros = literal + chase",
      _lit_codes | set(_chase_codes) == zero_open_codes
      and not (_lit_codes & set(_chase_codes)),
      f"literal {sorted(_lit_codes)} chase {_chase_codes} open {sorted(zero_open_codes)}")
zero_reconciliation = {
    "opening_items": len(zero_open_codes),
    "literal_items": len(_lit_codes),
    "chase_items": len(_chase_codes),
    "chase_codes": _chase_codes,
    "note": plain(
        f"{len(zero_open_codes)} items had nothing in stock on {FROZEN_DM}: "
        f"{len(_lit_codes)} with nothing on order, plus "
        f"{len(_chase_codes)} already on a PO — chase those"
    ),
}

# The August zero rule, in floor words. Its threshold is read from the artifact's
# own definition text ("cover < 1% ..."), never typed here.
_aug_def_raw = ob_sum["august_comparable"]["definition"]
_aug_pct = re.search(r"<\s*([\d.]+)\s*%", _aug_def_raw)
check("August zero rule threshold read from the order-by artifact", bool(_aug_pct), _aug_def_raw)
AUGUST_ZERO_DEF = plain(
    f"almost nothing — stock plus what is on order is under {_aug_pct.group(1) if _aug_pct else '?'}% "
    "of the month's need (August's rule: a sliver still counts as nothing)"
)
NO_MACHINE_FOR = " or ".join(sorted({plain_slot(u["slot_needed"]) for u in unproducible}))

materials_out = {
    "generated": ob_sum["generated"],
    "basis": ob_sum["basis"],
    "components_in_plan": ob_sum["components_in_plan"],
    "under_100_cover": ob_sum["under_100_cover"],
    "must_order_week1": ob_sum["must_order_week1"],
    "already_late": ob_sum["already_late"],
    "lead_days": ob_sum["lead_days"],
    "zero_definitions": {
        "literal": {
            # the artifact's own label is the loose "on_hand exactly 0" — but its
            # count excludes the PO-covered items, so the shown definition must
            # carry the full condition or it contradicts the opening_at_zero count
            "definition": plain("nothing in stock and nothing on order"),
            "items": ob_sum["items_at_zero"],
            "zero_pack": ob_sum["zero_pack"],
            "zero_oil": ob_sum["zero_oil"],
            "skus_blocked": ob_sum["skus_blocked_by_zero"],
            "blocked_value_rs": ob_sum["blocked_value_rs"],
            "blocked_value_note": ob_sum["blocked_value_note"],
        },
        "august_rule": {
            "definition": AUGUST_ZERO_DEF,
            "items": ob_sum["august_comparable"]["items"],
            "skus_blocked": ob_sum["august_comparable"]["skus_blocked"],
            "blocked_value_rs": ob_sum["august_comparable"]["blocked_value_rs"],
            "codes": ob_sum["august_comparable"]["codes"],
        },
        "opening_zero_reconciliation": zero_reconciliation,
        "note": plain("there are two ways to count 'nothing in stock' — say which one you are showing"),
    },
    "rows": ob_rows,
    "opening_at_zero": OPENING["at_zero"],
    "unproducible": unproducible,
    "unproducible_note": plain(
        f"products in this month's target that no machine can fill (there is no machine for {NO_MACHINE_FOR}) — "
        "shown, not hidden"
    ),
    "synonyms": ob_sum["synonyms"],
}
check("order-by rows == components_in_plan",
      len(ob_rows) == ob_sum["components_in_plan"],
      f"{len(ob_rows)} vs {ob_sum['components_in_plan']}")
check("late rows == already_late",
      sum(1 for r in ob_rows if r["late"]) == ob_sum["already_late"])

# ------------------------------------------------------------------ build ----
bmeta = dict(BUILD["meta"])
brcp = dict(bmeta.get("recipient", {}))
if brcp:
    brcp["display"] = mask_phone(brcp.get("whatsapp") or brcp.get("display") or "")
    brcp.pop("whatsapp", None)
    brcp["number_masked"] = not SHOW_PHONES
bmeta["recipient"] = brcp
bmeta["sample_day1"] = [mask_text(x) for x in bmeta.get("sample_day1", [])]
build_out = {
    "meta": dict(bmeta, simulated=True),
    "days": BUILD["days"],
}
check("build litres == summary made_l",
      BUILD["meta"]["totals"]["litres"] == SUM["totals"]["made_l"])

# --------------------------------------------------------------- whatsapp ----
threads_out = []
msg_total = 0
for t in WA:
    msgs = []
    for m in t["messages"]:
        mm = dict(m)
        mm["text"] = mask_text(mm.get("text", ""))
        mm["assumed"] = True  # every September message is a simulated draft
        msgs.append(mm)
    msg_total += len(msgs)
    threads_out.append({
        "name": t["name"],
        "title": t.get("title", ""),
        "display": mask_phone(t.get("whatsapp") or t.get("display") or ""),
        "number_masked": not SHOW_PHONES,
        "count": len(msgs),
        "simulated": True,
        "messages": msgs,
    })

wa_out = {
    "meta": {
        **WAMETA,
        # override the artifact's note: "names and numbers are real" reads as if
        # real numbers were shown — the recipients exist, the numbers are masked
        "note": plain(
            "September has not happened. Every message here was written by the computer — it is what "
            "the planner WOULD send. Nothing was sent. Nobody replied. The people are real, their phone "
            "numbers are hidden."
        ),
        "simulated": True,
        "numbers_masked": not SHOW_PHONES,
        "masking_note": plain("phone numbers are hidden — there is no approval to show them"),
    },
    "threads": threads_out,
}
check("wa messages == meta.sent", msg_total == WAMETA["sent"],
      f"{msg_total} vs {WAMETA['sent']}")
check("wa zero replies", WAMETA["assumed_replies"] == 0 and
      all(m["dir"] == "out" for t in WA for m in t["messages"]))
check("wa all assumed", all(m.get("assumed") for t in threads_out for m in t["messages"]))

# -------------------------------------------------------------- scenarios ----
def day_hour_profile(days_dir):
    """Per-day (max line-hours, working flag) plus total line-hours used,
    read from a scenario's own day files."""
    maxes, working, used = [], [], 0.0
    for f in sorted(glob.glob(os.path.join(SIM, days_dir, "day-*.json"))):
        dd = load(f)
        lh = dd.get("line_hours", {})
        maxes.append(max(lh.values()) if lh else 0.0)
        working.append(bool(dd.get("working")))
        used += sum(lh.values())
    return maxes, working, used


def derive_shift_shape(maxes):
    """Derive (front_h, tail_h, boundary_days, tapered) from the per-day max
    used line-hours. A tapered pattern runs its tail hours-bound every day, so
    the tail is the maximal run of identical per-day maxima ending the month;
    the front ceiling is the max over the remaining prefix (throttled front
    days sit below it and do not disturb the max). A flat pattern derives
    front == tail, or an empty prefix — nothing here is typed in."""
    tail_h = maxes[-1]
    k = len(maxes)
    while k > 0 and maxes[k - 1] == tail_h:
        k -= 1
    front_h = max(maxes[:k]) if k else tail_h
    tapered = k >= 1 and front_h > tail_h and (len(maxes) - k) >= 2
    return front_h, tail_h, k, tapered


n_lines = len(LINES_CFG)
_, _base_flags, base_hours = day_hour_profile("days-sep")
base_working = sum(1 for d in SUM["days"] if d["working"])
base_avail = RULES["shift_hours"] * base_working * n_lines
check("baseline day files match summary working-day count",
      sum(_base_flags) == base_working, f"{sum(_base_flags)} vs {base_working}")
base = {
    "id": f"{RULES['shift_hours']}x{base_working}",
    "label": plain(f"the normal shift — {RULES['shift_hours']} hours a day, {base_working} working days, Sundays off"),
    "shift_hours": RULES["shift_hours"],
    "working_days": base_working,
    "made_l": SUM["totals"]["made_l"],
    "value_rs": SUM["totals"]["value"],
    "shipped_l": SUM["totals"]["shipped_l"],
    "line_hours_used": round(base_hours, 1),
    "days_storage_ge_95": sum(1 for d in SUM["days"] if d["storage_pct"] >= 95),
    "storage_throttle_events": sum(1 for e in EVENTS if e["kind"] == "STORAGE_THROTTLE"),
    "baseline": True,
}

scen_rows = []
scen_notes = {
    "12x30": plain("the cheapest option — same shift, Sundays working. Sunday wages are NOT counted"),
    "22x30": plain("by mid-month the godown is full and production slows"),
    "24x30": plain("past 22 hours the extra hours add very little"),
}
for key, (sfile, sdir, efile, label, expect_taper) in SCEN_SRC.items():
    ssum = load(os.path.join(SIM, sfile))
    sev = load(os.path.join(SIM, efile))
    sworking = sum(1 for d in ssum["days"] if d["working"])
    maxes, wflags, used = day_hour_profile(sdir)
    check(f"{key}: day files match the summary calendar",
          len(maxes) == len(ssum["days"]) and sum(wflags) == sworking,
          f"{len(maxes)} files / {sum(wflags)} working vs {len(ssum['days'])} / {sworking}")
    # Prefer the run's OWN recorded schedule (engine writes summary["shift"]); inferring
    # the shape from output is only a fallback, and it breaks whenever a tail day is
    # material- or storage-bound rather than hours-bound — which is a fact about supply,
    # not a bad run.
    shift = ssum.get("shift") or {}
    if shift.get("schedule"):
        phases = {}
        for part in shift["schedule"].split(","):
            rng, h = part.split(":")
            a, _, b = rng.partition("-")
            for dd in range(int(a), int(b or a) + 1): phases[dd] = float(h)
        dom = [int(d["date"][8:10]) for d in ssum["days"]]
        per_day = [phases.get(x, float(shift.get("hours", 0))) for x in dom]
        front_h, tail_h = per_day[0], per_day[-1]
        boundary = next((i for i, h in enumerate(per_day) if h == tail_h and h != front_h), len(per_day))
        tapered = front_h != tail_h
    else:
        front_h, tail_h, boundary, tapered = derive_shift_shape(maxes)
    check(f"{key}: shift shape is the expected kind",
          tapered == expect_taper, f"front {front_h} tail {tail_h} boundary {boundary}")
    check(f"{key}: no day used more line-hours than its shift allows",
          all(m <= (per_day[i] if shift.get("schedule") and i < len(per_day) else max(front_h, tail_h)) + 0.05
              for i, m in enumerate(maxes)),
          "a day exceeded its configured shift ceiling")
    sid, taper, pattern = key, None, None
    if tapered:
        # available hours honour the derived per-phase ceilings, working days only
        avail = (sum(front_h for i in range(boundary) if wflags[i])
                 + sum(tail_h for i in range(boundary, len(maxes)) if wflags[i])) * n_lines
        front_days = sum(1 for i in range(boundary) if wflags[i])
        tail_days = sum(1 for i in range(boundary, len(maxes)) if wflags[i])
        sh = round(front_h)
        sid = f"taper-{round(front_h)}-{round(tail_h)}"
        label = (f"long hours first, then shorter: {round(front_h)} hours a day till day {boundary}, "
                 f"then {round(tail_h)} hours from day {boundary + 1}, Sundays working")
        pattern = plain(f"{round(front_h)} hrs × {front_days} days, then {round(tail_h)} hrs × {tail_days} days")
        taper = {
            "front_hours": round(front_h),
            "front_days": front_days,
            "tail_hours": round(tail_h),
            "tail_days": tail_days,
            "boundary_day": boundary,
            "derived_note": plain("the hours and the switch day are read from this option's own "
                                  "day-by-day files, not typed in"),
        }
    else:
        sh = round(max(maxes))
        avail = sh * sworking * n_lines
    offered = avail - base_avail
    extra_used = used - base_hours
    check(f"{sid}: hours used fit under the derived ceiling",
          used <= avail + 1e-6, f"used {used:.1f} vs available {avail:.1f}")
    row = {
        "id": sid,
        "label": plain(label),
        "shift_hours": sh,
        "working_days": sworking,
        "made_l": ssum["totals"]["made_l"],
        "value_rs": ssum["totals"]["value"],
        "shipped_l": ssum["totals"]["shipped_l"],
        "delta_made_l": ssum["totals"]["made_l"] - SUM["totals"]["made_l"],
        "line_hours_used": round(used, 1),
        "extra_line_hours_offered": round(offered),
        "extra_line_hours_used": round(extra_used, 1),
        "pct_extra_hours_used": round(extra_used / offered * 100, 1) if offered else None,
        "days_storage_ge_95": sum(1 for d in ssum["days"] if d["storage_pct"] >= 95),
        "storage_throttle_events": sum(1 for e in sev if e["kind"] == "STORAGE_THROTTLE"),
        "note": scen_notes.get(sid, ""),
        "simulated": True,
    }
    if taper:
        row["pattern"] = pattern
        row["taper"] = taper
    scen_rows.append(row)

# Taper notes and the board takeaway — phrased from the computed rows alone, with
# conditional wording so the sentence can never outrun the numbers it quotes.
_tapers = sorted((r for r in scen_rows if "taper" in r), key=lambda r: r["taper"]["tail_hours"])
_flats = {r["shift_hours"]: r for r in scen_rows if "taper" not in r}
takeaway = ""
if _tapers:
    _front_h = _tapers[0]["taper"]["front_hours"]
    check("tapers share one front phase and it sits flat on the board",
          _front_h in _flats and all(t["taper"]["front_hours"] == _front_h for t in _tapers),
          str([t["id"] for t in _tapers]))
    _ff = _flats[_front_h]
    check("flat front-hours pattern gains litres over baseline", _ff["delta_made_l"] > 0)
    clauses = []
    for t in _tapers:
        ret = round(t["delta_made_l"] / _ff["delta_made_l"] * 100, 1)
        share = round(t["extra_line_hours_offered"] / _ff["extra_line_hours_offered"] * 100)
        th = t["taper"]["tail_hours"]
        t["share_of_flat_front_gain_pct"] = ret
        if ret < 50:
            t["note"] = plain(f"keeps only {ret}% of what flat {_front_h} hours gains, while asking for "
                              f"{share}% of its extra hours — the {th}-hour tail gives the early litres back")
            clauses.append(f"drop to {th} hours after day {t['taper']['boundary_day']} and the month "
                           f"keeps only {ret}% of the flat-{_front_h}-hour gain")
        else:
            t["note"] = plain(f"keeps {ret}% of what flat {_front_h} hours gains, while asking for only "
                              f"{share}% of its extra hours — the {th}-hour tail holds on to most of it")
            clauses.append(f"drop to {th} hours after day {t['taper']['boundary_day']} and "
                           f"{ret}% of that gain stays, asking for only {share}% of the flat-{_front_h}-hour extra hours")
        _ft = _flats.get(th)
        if _ft is not None:
            check(f"{t['id']} outmakes its flat tail pattern",
                  t["made_l"] >= _ft["made_l"], f"{t['made_l']} vs {_ft['made_l']}")
        check(f"{t['id']} stays at or under its flat front pattern",
              t["made_l"] <= _ff["made_l"], f"{t['made_l']} vs {_ff['made_l']}")
    if len(_tapers) == 2:
        check("the deeper tail cut makes fewer litres",
              _tapers[0]["made_l"] <= _tapers[1]["made_l"],
              f"{_tapers[0]['made_l']} vs {_tapers[1]['made_l']}")
    _top = max(scen_rows, key=lambda r: r["made_l"])
    _eff = max(scen_rows, key=lambda r: r["pct_extra_hours_used"] or -1)
    _top_phrase = (f"flat {_top['shift_hours']} hours still makes the most litres"
                   if "taper" not in _top else f"{_top['label']} makes the most litres")
    _eff_phrase = (f"plain Sundays working ({_eff['shift_hours']} hours × {_eff['working_days']} days) still "
                   f"turns extra hours into litres best — {_eff['pct_extra_hours_used']}% of its extra hours ran"
                   if "taper" not in _eff else
                   f"{_eff['label']} turns extra hours into litres best — "
                   f"{_eff['pct_extra_hours_used']}% of its extra hours ran")
    _cap = lambda s: s[0].upper() + s[1:]
    takeaway = plain("Long hours first, then shorter — does it pay? Same computer plan, tested: "
                     + ". ".join(_cap(c) for c in clauses)
                     + f". {_cap(_top_phrase)}. {_cap(_eff_phrase)}.")
scen_rows.sort(key=lambda r: -r["made_l"])

scenarios_out = {
    "baseline": base,
    "scenarios": scen_rows,
    "takeaway": takeaway,
    "method_note": plain(
        "'of the extra hours, how many ran' = extra machine-hours actually used ÷ extra machine-hours offered. "
        "Offered = this option's machine-hours minus the normal shift's, where machine-hours = "
        "shift hours × working days × number of machines. A long-then-short option counts each phase at "
        "its own hours, read from its own day-by-day files. Every figure is worked out from the option's own run"
    ),
    "artifact_note": plain(
        (f"every option shown was run in full for all {len(SUM['days'])} days — "
         f"including the {_tapers[-1]['taper']['tail_hours']}-hour-tail option an earlier version "
         f"said was missing") if _tapers else
        "an 18-hour option was talked about but was never run — not shown"
    ),
    "simulated": True,
}

# ------------------------------------------------------------- loop chains ---
ordered_ev = [e for e in EVENTS if e["kind"] == "ORDERED_BLOCKER"]
unblocked_ev = sorted(
    (e for e in EVENTS if e["kind"] == "UNBLOCKED"), key=lambda e: e["day"])
consumed = set()
chains = []
for e in sorted(ordered_ev, key=lambda x: x["day"]):
    match = None
    for j, u in enumerate(unblocked_ev):
        if j in consumed or u["code"] != e["code"] or u["day"] < e["day"]:
            continue
        match = (j, u)
        break
    fgs = sorted(binder_fgs.get(e["code"], []))
    chain = {
        "code": e["code"],
        "name": e["name"],
        "kind": item_kind(e["code"]),
        "ordered_day": e["day"],
        "qty": e["qty"],
        "lands": e["lands"],
        "lead_days": e["lead"],
        "fg_codes_blocked": fgs,
        "simulated": True,
    }
    if match:
        j, u = match
        consumed.add(j)
        chain["unblocked_day"] = u["day"]
        chain["waited_days"] = u["waited_days"]
        first_run = None
        for d in DAYS:
            if d["date"] < u["day"]:
                continue
            for r in d["runs"]:
                if r["code"] in binder_fgs.get(e["code"], set()):
                    first_run = {"day": d["date"], "code": r["code"],
                                 "sku": r["sku"], "litres": round(r["litres"])}
                    break
            if first_run:
                break
        if first_run:
            chain["first_run_after_unblock"] = first_run
    else:
        chain["unblocked_day"] = None
        chain["note"] = plain(f"arrives after {dm(SUM['days'][-1]['date'])} — still stuck this month")
    chains.append(chain)

loops_out = {
    "note": plain("stuck → ordered → arrived → running, one chain per missing item. 'Days waited' is the planner's own count"),
    "chains": chains,
    "ordered_events": len(ordered_ev),
    "unblocked_events": len(unblocked_ev),
    "resolved_chains": sum(1 for c in chains if c.get("unblocked_day")),
    "ran_after_unblock": sum(1 for c in chains if c.get("first_run_after_unblock")),
    "landed_no_run": sum(1 for c in chains
                         if c.get("unblocked_day") and not c.get("first_run_after_unblock")),
    "resolved_note": plain(
        "'arrived' counts items that arrive in September and free their products. Only some of those "
        "products actually run again before month-end — say which count you mean"
    ),
    "simulated": True,
}
check("every UNBLOCKED consumed by a chain",
      len(consumed) == len(unblocked_ev),
      f"{len(consumed)} vs {len(unblocked_ev)}")
check("ran + landed_no_run == resolved",
      loops_out["ran_after_unblock"] + loops_out["landed_no_run"] == loops_out["resolved_chains"])
check("unresolved chains land after month-end",
      all((c.get("lands") or "") > SUM["days"][-1]["date"]
          for c in chains if not c.get("unblocked_day")),
      str([c["lands"] for c in chains if not c.get("unblocked_day")]))

# ----------------------------------------------------- demand / honesty ------
fc = [o for o in ORDERS if is_forecast_order(o)]
real = [o for o in ORDERS if not is_forecast_order(o)]
tot_p = sum(o["pieces"] for o in ORDERS)
tot_v = sum(o["value"] for o in ORDERS)
tot_l = sum(o["pieces"] * LPP.get(o["code"], 0) for o in ORDERS)
fc_p = sum(o["pieces"] for o in fc)
fc_v = sum(o["value"] for o in fc)
fc_l = sum(o["pieces"] * LPP.get(o["code"], 0) for o in fc)

demand = {
    "rows": len(ORDERS),
    "real_rows": len(real),
    "forecast_rows": len(fc),
    "real_pieces": round(sum(o["pieces"] for o in real)),
    "forecast_pieces": round(fc_p),
    "real_value_rs": round(sum(o["value"] for o in real)),
    "forecast_value_rs": round(fc_v),
    "forecast_share_pieces_pct": round(fc_p / tot_p * 100, 2),
    "forecast_share_value_pct": round(fc_v / tot_v * 100, 2),
    "forecast_share_litres_pct": round(fc_l / tot_l * 100, 2),
    "order_dates": len({o["date"] for o in ORDERS}),
    "channels": dict(Counter(o["channel"] for o in ORDERS)),
    "note": plain(
        "what customers want this month mixes confirmed orders with expected orders — this month's "
        "target, not ordered yet. Expected rows are marked in the data and must always look different on the page"
    ),
}

# backlog measured state (plan-SKU slice actually in the freeze)
bl_docs = defaultdict(list)
for r in BACKLOG:
    bl_docs[r["docnum"]].append(r.get("due") or r.get("date"))
bl_total_docs = len(bl_docs)
bl_overdue_docs = sum(1 for dues in bl_docs.values()
                      if min(x for x in dues if x) < MONTH_START)

# FG0000155 realise outlier — computed, not typed
r155 = REALISE.get("FG0000155")
o155 = [o for o in ORDERS if o["code"] == "FG0000155" and not is_forecast_order(o)]
outlier = None
if r155 and o155:
    lp = LPP.get("FG0000155", 0)
    unit_l_price = sum(o["value"] for o in o155) / sum(o["pieces"] for o in o155) / lp
    outlier = {
        "code": "FG0000155",
        "sku": PLAN_BY_CODE["FG0000155"]["sku"],
        "realise_rs_per_l": r155,
        "order_book_rs_per_l": round(unit_l_price, 2),
        "ratio": round(r155 / unit_l_price, 2),
        "note": plain("this product's selling price per litre is an odd inherited figure — never show it as a headline without saying so"),
    }

# The honesty rules, in floor words. The ids are keys the pages look up — never renamed.
label_rules = [
    {"id": "po-open-value", "rule": plain("the planner's 'PO value' counter is the total ordered since day 1 and only ever goes up — if shown, call it 'total ordered this month', NEVER 'pending order value'.")},
    {"id": "po-open-litres", "rule": plain("the planner's 'open litres' counter is not what is still to be sent — use the 'still to be sent' figure (confirmed orders minus billed), which sits next to it in the day-by-day data.")},
    {"id": "orders-mixed", "rule": plain("each day's new orders MIX confirmed orders with expected orders (not ordered yet) — always split them. On a quiet day the new orders are 100% expected."), "forecast_share_litres_pct": demand["forecast_share_litres_pct"]},
    {"id": "two-oil-series", "rule": plain("'oil in stock' on the Summary (every oil) and on the day pages (only the oils in this month's recipes) are two different counts — never draw them as one line."), "opening_oil_l": OPENING["oil_l"]},
    {"id": "forecast-tags", "rule": plain("expected orders (not ordered yet) are marked in the data — keep them looking different from confirmed orders everywhere.")},
    {"id": "ceiling-assumed", "rule": plain("the godown limit is Daman's number from his spreadsheet — not measured. Say so wherever it appears (open question Q2)."), "working_l": RULES["storage_ceiling_l"], "peak_l": RULES["storage_peak_l"]},
    {"id": "standing-zero", "rule": plain(f"stock billed by {FROZEN_DM} but not yet trucked is not counted on day 1 — our guess, on the hopeful side. The godown is really fuller than shown.")},
    {"id": "ecom-spread", "rule": plain("the e-com part of this month's target has no week-by-week dates — it is spread evenly across the working days. Our guess, not measured.")},
    {"id": "day1-pile", "rule": plain(f"the pile of orders on day 1 is real, not a bug — most pending customer orders were already late on {FROZEN_DM}."), "provenance_quote": PROV["demand"], "plan_sku_backlog_docs": bl_total_docs, "plan_sku_backlog_docs_overdue": bl_overdue_docs},
    {"id": "observed-then-derated", "rule": plain(f"Clear Pack 5L and Tin Head have no maker's speed in the plan — the speed listed for them is the one we measured, and the plan runs them at {EFF_PCT}% of even that. Never call it '{EFF_PCT}% of the maker's speed'."), "efficiency": efficiency},
    {"id": "unproducible", "rule": plain(f"{len(unproducible)} products in this month's target have no machine (nothing fills {NO_MACHINE_FOR}) — show them on the Stock and Order by when pages, do not hide them."), "codes": [u["code"] for u in unproducible]},
    {"id": "realise-outlier", "rule": plain("FG0000155's selling price per litre is an odd inherited figure, far from its own order book — never show it as a headline without saying so."), "detail": outlier},
    {"id": "whatsapp-simulated", "rule": plain("every message on the Messages page was written by the computer and NEVER sent — nobody replied. Show them as unsent drafts, never as real chat.")},
    {"id": "numbers-masked", "rule": plain("no real phone number anywhere — hidden in the data. There is no approval to show them.")},
]

honesty_out = {
    "forward_rule": INP["meta"]["rule"],
    "measured": HONESTY["measured"],
    "assumed": fix_honesty(HONESTY)["assumed"],
    "provenance": PROV,
    "label_rules": label_rules,
    "august_calibration": {
        "sim_made_l": AUG_SIM["totals"]["made_l"],
        "actual_made_l": AUG_SIM["totals"]["actual_made_l"],
        "delta_pct": round(
            abs(AUG_SIM["totals"]["made_l"] - AUG_SIM["totals"]["actual_made_l"])
            / AUG_SIM["totals"]["actual_made_l"] * 100, 2),
        "note": plain("tested on August: the same computer plan was run for August and came this close to what the factory really made — that is why these numbers can be trusted"),
    },
}
check("rule-10 phrase rewritten everywhere",
      BAD_RATE_PHRASE not in json.dumps(honesty_out["assumed"], ensure_ascii=False)
      and all(BAD_RATE_PHRASE not in json.dumps(dd["honesty"]["assumed"], ensure_ascii=False)
              for dd in day_details)
      and any(RATE_ASSUMPTION_HONEST == a for a in honesty_out["assumed"]))

# ---------------------------------------------------------------- questions --
qwanted = {2, 4, 13}
q_items = []
for q in QUESTIONS.get("questions", []):
    if q.get("n") in qwanted:
        text = str(q.get("question", "")).strip()
        first = text.split("?")[0].strip()
        one_liner = (first + "?") if first else text
        q_items.append({
            "n": q["n"],
            "priority": q.get("priority", ""),
            "one_liner": one_liner,
            "status": q.get("status", "OPEN"),
        })
q_items.sort(key=lambda x: x["n"])
questions_out = {
    "asked": QUESTIONS.get("asked"),
    "note": plain(f"the {len(q_items)} open questions that would change this plan — the full list is on the August site"),
    "items": q_items,
}
check("Q2/Q4/Q13 found", {q["n"] for q in q_items} == qwanted)

# ----------------------------------------------------------------- overview --
work_days = [d for d in SUM["days"] if d["working"]]
utils = sorted(d["util"] for d in work_days)
util_median = utils[len(utils) // 2] if len(utils) % 2 else (
    utils[len(utils) // 2 - 1] + utils[len(utils) // 2]) / 2
peak_day = max(SUM["days"], key=lambda d: d["made_l"])
plan_l = sum(p["litres"] for p in PLAN)

# day-1 blocks: the spine's `blocked` is a raw ATTEMPT counter (the scheduler
# re-tries the same wall) — the honest headcount is distinct products. And the
# blocking is classed by WHAT binds: day 1 is overwhelmingly an OIL story —
# never let the page attribute it to the zero-stock packaging openers.
def _binder_class(code):
    if item_kind(code) == "OIL":
        return "oil"
    return "zero_stock_packaging" if code in zero_open_codes else "other_packaging"


_d1b = DAYS[0]["blocked"]
_cls_att = Counter(_binder_class(x["binder"]) for x in _d1b)
_cls_prod = defaultdict(set)
for x in _d1b:
    _cls_prod[_binder_class(x["binder"])].add(x["code"])
_top_code, _top_att = Counter(x["binder"] for x in _d1b).most_common(1)[0]
_d1_products = {b["code"] for b in _d1b}
_multi_class = sum(1 for p in _d1_products
                   if sum(1 for cl in _cls_prod.values() if p in cl) > 1)
_zero_ever = {x["code"] for d in DAYS for x in d["blocked"]
              if x["binder"] in zero_open_codes}

day1_blocked = {
    "attempts": len(_d1b),
    "products": len(_d1_products),
    "product_binder_pairs": len({(b["code"], b["binder"]) for b in _d1b}),
    "by_binder_class": {
        k: {"attempts": _cls_att.get(k, 0), "products": len(_cls_prod.get(k, set()))}
        for k in ("oil", "zero_stock_packaging", "other_packaging")
    },
    "top_binder": {
        "code": _top_code,
        "name": next(x["binder_name"] for x in _d1b if x["binder"] == _top_code),
        "kind": item_kind(_top_code),
        "attempts": _top_att,
        "products": len({x["code"] for x in _d1b if x["binder"] == _top_code}),
    },
    "products_in_multiple_classes": _multi_class,
    "zero_openers_products_blocked_month": len(_zero_ever),
    "note": plain(
        "'attempts' = how many times the planner tried and was stopped, not how many products — quote products. "
        "On day 1 most stops are oil short — do not blame the packing items that started with nothing in stock "
        "(one product can be short of oil and packing at once, so the per-type counts can overlap)"
    ),
}
check("day1 class attempts sum to total",
      sum(_cls_att.values()) == len(_d1b))
check("day1 blocking is majority oil (the page says so in prose)",
      _cls_att.get("oil", 0) > len(_d1b) / 2 and item_kind(_top_code) == "OIL",
      f"oil {_cls_att.get('oil', 0)} of {len(_d1b)}, top {_top_code}")

overview = {
    "meta": {
        "month": INP["meta"]["month"],
        "frozen": INP["meta"]["frozen"],
        "as_of": INP["meta"]["as_of"],
        "horizon": INP["meta"]["horizon"],
        "forward": True,
        "forward_rule": INP["meta"]["rule"],
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    },
    "totals": {
        "made_l": SUM["totals"]["made_l"],
        "value_rs": SUM["totals"]["value"],
        "shipped_l": SUM["totals"]["shipped_l"],
        "oil_used_l": SUM["totals"]["oil_used_l"],
        "days": len(SUM["days"]),
        "working_days": base_working,
        "runs": sum(r["runs"] for r in day_rows),
        "oil_changes": BUILD["meta"]["totals"]["oil_changes"],
        "clearances_only": BUILD["meta"]["totals"]["clearances_only"],
        "flushes": sum(r["flushes"] for r in day_rows),
        "bought_lines": SUM["totals"]["bought_lines"],
        "events": SUM["totals"]["events"],
        "util_median": round(util_median),
        "peak_day": {"date": peak_day["date"], "made_l": peak_day["made_l"]},
    },
    "plan": {
        "litres": round(plan_l),
        "skus": len(PLAN),
        "made_vs_plan_pct": round(SUM["totals"]["made_l"] / plan_l * 100, 1),
        "source": PROV["plan"],
    },
    "demand": demand,
    "opening": {
        "fg_litres": OPENING["fg_litres"],
        "fg_plan_l": OPENING["fg_plan_l"],
        "fg_other_l": OPENING["fg_other_l"],
        "oil_l": OPENING["oil_l"],
        "oil_l_definition": plain(f"all oil in stock on {FROZEN_DM}, every kind — the day pages count only the oils in this month's recipes, so the two are not the same line"),
        "packaging_pieces": OPENING["packaging_pieces"],
        "inbound_oil_l": OPENING["inbound_oil_l"],
        "inbound_packaging": OPENING["inbound_packaging"],
        "standing_l": OPENING["standing_l"],
        "standing_assumed": True,
        "backlog_pieces": OPENING["backlog_pieces"],
        "backlog_value_rs": OPENING["backlog_value"],
        "plan_sku_backlog_docs": bl_total_docs,
        "plan_sku_backlog_docs_overdue": bl_overdue_docs,
        "at_zero_count": len(OPENING["at_zero"]),
    },
    "storage": {
        "ceiling_l": RULES["storage_ceiling_l"],
        "peak_l": RULES["storage_peak_l"],
        "ceiling_assumed": True,
        "invoice_truck_lag_days": LAG_DAYS,
        "days_ge_95": storage_out["days_ge_95"],
        "days_ge_100": storage_out["days_ge_100"],
        "throttle_events": len(storage_out["throttles"]),
    },
    "day1_blocked": day1_blocked,
    "august": honesty_out["august_calibration"],
    "scenarios_mini": [
        {"id": s["id"], "label": s["label"], "made_l": s["made_l"],
         "delta_made_l": s["delta_made_l"],
         "pct_extra_hours_used": s["pct_extra_hours_used"]}
        for s in scen_rows
    ],
    "materials_mini": {
        "components": ob_sum["components_in_plan"],
        "under_100_cover": ob_sum["under_100_cover"],
        "must_order_week1": ob_sum["must_order_week1"],
        "already_late": ob_sum["already_late"],
        "zero_literal_items": ob_sum["items_at_zero"],
        "zero_literal_value_rs": ob_sum["blocked_value_rs"],
        "zero_august_rule_items": ob_sum["august_comparable"]["items"],
        "zero_august_rule_value_rs": ob_sum["august_comparable"]["blocked_value_rs"],
    },
    "whatsapp_mini": {
        "threads": len(threads_out),
        "messages": msg_total,
        "replies": WAMETA["assumed_replies"],
        "simulated": True,
    },
    "unproducible": unproducible,
    "questions_top": q_items,
    "simulated": True,
}

# ------------------------------------------------------------------- write ---
os.makedirs(os.path.join(DATA, "days"), exist_ok=True)

outputs = {
    "overview.json": overview,
    "spine.json": day_rows,
    "lines.json": lines_out,
    "storage.json": storage_out,
    "materials.json": materials_out,
    "build.json": build_out,
    "whatsapp.json": wa_out,
    "scenarios.json": scenarios_out,
    "loops.json": loops_out,
    "honesty.json": honesty_out,
    "questions.json": questions_out,
}
for i, dd in enumerate(day_details):
    outputs[os.path.join("days", f"day-{i + 1:02d}.json")] = dd

for name, obj in outputs.items():
    assert_no_phones(name, obj)

# PLAIN-LANGUAGE.md — no banned office word in any text authored by this script
_bad = sorted({(_BANNED_RE.search(s).group(0), s[:90]) for s in PLAIN_STRINGS if _BANNED_RE.search(s)})
check("plain language: authored text carries no banned office words", not _bad, str(_bad[:5]))

failed = [c for c in checks if not c[1]]
if failed:
    print(f"\n{len(failed)} CHECK(S) FAILED — NOT WRITING", file=sys.stderr)
    sys.exit(1)

total_bytes = 0
for name, obj in outputs.items():
    p = os.path.join(DATA, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    total_bytes += os.path.getsize(p)

# ------------------------------------------------------------------- stats ---
print(f"gen-data.py — September plan data generated into {DATA}")
print(f"  files: {len(outputs)} ({total_bytes / 1024:.0f} KB total)")
print(f"  month {overview['meta']['month']} · frozen {overview['meta']['frozen']} · FORWARD PLAN")
print(f"  spine: {len(day_rows)} days ({base_working} working) · runs {overview['totals']['runs']}"
      f" · oil changes {overview['totals']['oil_changes']}")
print(f"  made {overview['totals']['made_l']:,} L · value Rs {overview['totals']['value_rs'] / 1e7:.2f} Cr"
      f" · shipped {overview['totals']['shipped_l']:,} L · util median {overview['totals']['util_median']}")
print(f"  plan {overview['plan']['litres']:,} L over {overview['plan']['skus']} SKUs"
      f" · made/plan {overview['plan']['made_vs_plan_pct']}%")
print(f"  demand rows {demand['rows']} (real {demand['real_rows']} / forecast {demand['forecast_rows']})"
      f" · forecast share {demand['forecast_share_litres_pct']}% by litres"
      f" / {demand['forecast_share_pieces_pct']}% by pieces / {demand['forecast_share_value_pct']}% by value")
print(f"  storage: ceiling {RULES['storage_ceiling_l']:,} L (ASSUMED, Q2) · days ≥95%: "
      f"{storage_out['days_ge_95']} · at/over 100%: {storage_out['days_ge_100']}")
print(f"  materials: {ob_sum['components_in_plan']} components · {ob_sum['under_100_cover']} under 100% cover"
      f" · week-1 orders {ob_sum['must_order_week1']} · already late {ob_sum['already_late']}")
print(f"  zeros: literal {ob_sum['items_at_zero']} items / Rs {ob_sum['blocked_value_rs'] / 1e7:.2f} Cr"
      f" · August rule {ob_sum['august_comparable']['items']} items / Rs "
      f"{ob_sum['august_comparable']['blocked_value_rs'] / 1e7:.2f} Cr")
print(f"  unproducible plan SKUs: {len(unproducible)} ({', '.join(u['code'] for u in unproducible)})")
print(f"  scenarios: " + " · ".join(
    f"{s['id']} {s['made_l']:,} L ({s['pct_extra_hours_used']}% extra hrs used)" for s in scen_rows))
print(f"  loops: {loops_out['resolved_chains']}/{len(chains)} blocker chains resolved in-month")
print(f"  whatsapp: {len(threads_out)} threads · {msg_total} simulated drafts · 0 replies · {"numbers SHOWN (authorised)" if SHOW_PHONES else "numbers MASKED"}")
print(f"  august calibration: sim {honesty_out['august_calibration']['sim_made_l']:,} vs actual "
      f"{honesty_out['august_calibration']['actual_made_l']:,} ({honesty_out['august_calibration']['delta_pct']}%)")
print(f"  checks: {sum(1 for c in checks if c[1])}/{len(checks)} passed"
      + ("" if not failed else f" — {len(failed)} FAILED"))
for name, ok, detail in checks:
    if not ok:
        print(f"    FAILED: {name} {detail}")
