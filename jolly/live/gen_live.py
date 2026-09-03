#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_live.py — site data for the LIVE ROLLING re-plan (Mark 3).

    cd jolly && python3 live/gen_live.py            # writes live/state/plan/*.json
    python3 live/gen_live.py --dry-run              # run every check, write nothing
    python3 live/gen_live.py --out /tmp/plan        # somewhere else

WHY THIS FILE EXISTS INSTEAD OF site-sep/scripts/gen-data.py
    gen-data.py is hard-wired to the 31-August FROZEN September plan: it loads
    sim/sep-inputs.json, sim/summary-sep.json, sim/days-sep/, sim/events-sep.json,
    five -sep scenario runs, out/order-by-sep.json, out/build-list-sep.json and
    sim/whatsapp-sep.json by NAME, with no tag knob. Left in the loop it re-emits
    the frozen plan every cycle wearing today's timestamp (loop.sh says so out
    loud today). It is also NOT importable: every one of those loads, and the
    whole build, sits at module level, so `import gen_data` would run the entire
    -sep generation and overwrite site-sep/data/ as a side effect. VERIFIED by
    reading it, not assumed — so nothing here imports it. Shapes and field names
    were copied by hand from it and from site-sep/lib/data.ts.

    Mark 2 stays exactly as it is. This writes the live-horizon twin beside it.

WHAT IT READS  (whatever engine/august_sim.py wrote for SIM_TAG, default -live)
    sim/live-inputs.json      the rolling opening, written by live/freeze_live.py
    sim/summary-live.json     the per-day spine + month totals
    sim/days-live/day-NN.json the per-day detail
    sim/events-live.json      ORDERED_BLOCKER / UNBLOCKED / STORAGE_THROTTLE / ...
    out/order-by-live.json    the zero-cover gap list — regenerated here from the
                              same artifacts by engine/sep_gap.py when it is
                              missing or older than the inputs. sep_gap.py with
                              --inputs runs its FROZEN path: no HANA, no SAP, no
                              network (RULE 0 holds).
    sim/summary.json          the August run, for the calibration line only

WHAT IT WRITES  (live/state/plan/, the directory live/publish serves)
    overview.json  spine.json  storage.json  materials.json  loops.json
    honesty.json   lines.json  days/day-NN.json  manifest.json
    Skipped on purpose: scenarios.json + build.json (later), whatsapp.json
    (Mark 3 drops it — the real channel is the Jolly WhatsApp agent).
    manifest.json is the list of the files above. loop.sh's publish step deletes
    any other *.json in live/state/plan/ and live/state/plan/days/, logging each
    one — that is how the four Mark 2 leftovers stop being served.

    Shapes match site-sep/README.md's contract table and site-sep/lib/data.ts.
    spine.json stays a bare ARRAY (`SpineDay[]`), so its stamp rides on each row.

ROLLING, NOT A MONTH
    Only day 1 is observed, and it is re-observed every three minutes. The
    horizon is today..month-end and it gets one day shorter every day, so none
    of gen-data.py's 30-day arithmetic is ported: no "30 days", no five shift
    scenarios, no month-shaped working-day count. Every check here holds for a
    horizon of any length, including one day.

REFUSES TO WRITE ON ANY FAILED CHECK
    Same rule as gen-data.py, for the same reason: a failing check is a wrong
    number, never a check to weaken. The old files stay exactly where they are
    and the site keeps serving the last good plan.

RULE 0 — nothing here touches SAP. Every figure comes from ji.jivo.in, EXIM,
OMS and ecom, through live/state/state.json and live/freeze_live.py.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys
import traceback
from collections import Counter, defaultdict
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))          # .../jolly/live
JOLLY = os.path.dirname(HERE)                              # .../jolly
SIM = os.path.join(JOLLY, "sim")
OUT = os.path.join(JOLLY, "out")
DEFAULT_OUT_DIR = os.path.join(HERE, "state", "plan")

# The files this script owns in the publish directory. Anything else sitting there is
# from another vintage. This file reports them; loop.sh's publish step is what removes
# them, off manifest.json — see the manifest block at the end of build().
OWNED = ("overview.json", "spine.json", "storage.json", "materials.json",
         "loops.json", "honesty.json", "lines.json", "manifest.json")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ checks ---
class Checks:
    """Same contract as gen-data.py's: collect, print failures, gate the write."""

    def __init__(self):
        self.rows = []

    def __call__(self, name, ok, detail=""):
        self.rows.append((name, bool(ok), str(detail)))
        if not ok:
            print(f"CHECK FAILED: {name} {detail}", file=sys.stderr)
        return bool(ok)

    @property
    def failed(self):
        return [r for r in self.rows if not r[1]]

    @property
    def passed(self):
        return [r for r in self.rows if r[1]]


# ---------------------------------------------------------- plain language ---
# PLAIN-LANGUAGE.md, ported verbatim from gen-data.py. Text AUTHORED here is
# registered with plain() and scanned before anything is written; text COPIED
# from the sim artifacts (honesty lists, provenance notes, warnings, item names)
# is not — the pages translate that where they render it.
BANNED_WORDS = [
    r"\bSKUs?\b", r"\bcomponents?\b", r"\bbinders?\b", r"\bcover\b", r"\bthrottl", r"\bforecasts?\b",
    r"\bchannels?\b", r"\bbaseline\b", r"\bsimulat", r"\bcalibrat", r"\bbacktest", r"\bhorizon\b",
    r"\bheadroom\b", r"\bprovenance\b", r"\bcumulative\b", r"\bderated?\b", r"\bstanding\b", r"\bgated\b",
    r"\bdocnums?\b", r"\bFCST", r"\bunproducible\b", r"\bBOMs?\b", r"\brealise[ds]?\b", r"\butilisation\b",
    r"\blead[ -]times?\b", r"\bbacklog\b", r"\bscenarios?\b", r"\bmarginal\b", r"\bconservation\b",
    r"\bassum", r"\bderived?\b", r"\bopening\b", r"\bfrozen\b", r"\bas-of\b",
]
_BANNED_RE = re.compile("|".join(BANNED_WORDS), re.IGNORECASE)
PLAIN_STRINGS: list[str] = []


def plain(s):
    PLAIN_STRINGS.append(s)
    return s


# --------------------------------------------------------------- phone scan --
# Mark 3 shows NO phone number (live/PHASE5-SITE.md). There is no SHOW_PHONES
# escape hatch here on purpose: Mark 2's approval was for Mark 2's pages.
RAW_NUMBERS: set[str] = set()


def collect_number(value):
    if isinstance(value, str) and re.search(r"\+?91[\s-]?\d", value):
        digits = re.sub(r"\D", "", value)
        if len(digits) == 12 and digits.startswith("91"):
            RAW_NUMBERS.add(digits[2:])
        elif len(digits) == 10:
            RAW_NUMBERS.add(digits)


def scan_no_phones(check, name, obj):
    blob = json.dumps(obj, ensure_ascii=False)
    flat = re.sub(r"\D", "", blob)
    for d10 in RAW_NUMBERS:
        if d10 in flat and d10 in blob.replace(" ", "").replace("-", ""):
            return check(f"phone-scan {name}", False, f"raw number ...{d10[-4:]} leaked")
    if re.search(r"\+91[\s-]?\d{3}", blob):
        return check(f"phone-scan {name}", False, "un-masked +91 pattern present")
    return check(f"phone-scan {name}", True)


# ----------------------------------------------------------- number hygiene --
# "no NaN/None where a number is expected". Two nets: every float must be
# finite, and any key that names a quantity must not be null. A handful of
# fields are null BY DESIGN and are named here rather than being papered over.
_QTY_KEY = re.compile(
    r"(_l|_rs|_pct|_pieces|_litres|_days|_count|_min|_minutes|_hr|_per_hr|_per_l|_qty)$"
    r"|^(litres|pieces|value|qty|need|short|made_l|shipped_l|util|pct|hours|rate|count|runs|"
    r"flushes|blocked|unblocked|bought|efficiency|lead|waited_days|value_at_risk|"
    r"litres_at_risk|skus_blocked|on_hand|on_order|cover_pct|n)$"
)
NULL_OK = {
    "pieces_made_mtd",      # freeze_live.py publishes null rather than two days wearing a month's label
    "source_day_n",         # no day that far back inside this run
    "source_date",
    "unblocked_day",        # the item never arrives inside this run
    "server_at",            # not every source stamps its own answer
    "peak_l",
    "oil_changes",          # needs the machine-by-machine running order, not built on this run
    "clearances_only",
    "clears_on_day_n",      # the day-1 pile does not finish clearing inside the run
    # Both come out of factory_dispatch's HEAVY company read. freeze_live.py carries them
    # between heavy cycles, so they are null only on a cold box that has never had one —
    # and a cold start must not wedge the chain. Anything after the first heavy cycle is
    # a real figure or a carried one wearing its own stamp (companions_read_at).
    "wide_14d_all_company_l",
    "godown_rooms_only_all_company_l",
}


def scan_numbers(check, name, obj):
    bad = []

    def walk(node, path):
        if len(bad) >= 6:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                here = f"{path}.{key}" if path else key
                if value is None and key not in NULL_OK and _QTY_KEY.search(key):
                    bad.append(f"{here} is null")
                walk(value, here)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
        elif isinstance(node, float) and not math.isfinite(node):
            bad.append(f"{path} is {node}")

    walk(obj, "")
    return check(f"numbers {name}", not bad, "; ".join(bad))


# ------------------------------------------------------------ small helpers --
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def dm(iso):
    """'2026-09-30' -> '30 Sep' — a date in floor words."""
    return f"{int(iso[8:10])} {MON[int(iso[5:7]) - 1]}"


def item_kind(code):
    if str(code).startswith("RM"):
        return "OIL"
    if str(code).startswith("PM"):
        return "PACKAGING"
    return "OTHER"


def plain_slot(slot):
    """'3L' -> '3-litre bottles', 'DRUM' -> 'drums'."""
    s = str(slot)
    if s.endswith("L") and s[:-1].replace(".", "").isdigit():
        return f"{s[:-1]}-litre bottles"
    return {"DRUM": "drums", "TIN": "tins", "POUCH": "pouches"}.get(s.upper(), s.lower())


def slot_of(row):
    """Replicates engine/august_sim.py slot(), so 'no machine for it' is worked
    out rather than typed. Kept identical to gen-data.py's copy."""
    pack_type = str(row["pack_type"]).upper()
    sku = str(row["sku"]).upper()
    litres = row["litres_per_piece"]
    if "DRUM" in pack_type:
        return "DRUM"
    if "TIN" in pack_type or "KGS" in sku:
        return "TIN"
    if "POUCH" in pack_type or "POUCH" in sku:
        return "POUCH"
    for limit, name in ((1.05, "1L"), (2.05, "2L"), (3.05, "3L"), (4.05, "4L"), (5.05, "5L")):
        if litres <= limit:
            return name
    return "15L"


def is_forecast(order):
    return order.get("channel") == "FORECAST" or str(order.get("docnum", "")).startswith("FCST")


def source_row(value):
    """One provenance entry, whichever shape it arrives in.

    live/freeze_live.py writes a dict per source (source / fetched_at / server_at
    / mode / note). The older engine/freeze_sep.py wrote a plain sentence. Both
    are honest; only one has a .get(). Reading the dict blind crashed this file
    mid-build the first time it met the older shape — and a crash is worse than a
    failed check, because a failed check still says what is wrong and leaves the
    published plan intact.
    """
    if isinstance(value, dict):
        return {"source": value.get("source"), "mode": value.get("mode"),
                "fetched_at": value.get("fetched_at"), "server_at": value.get("server_at")}
    return {"source": str(value), "mode": None, "fetched_at": None, "server_at": None}


# ------------------------------------------------------------- the order-by --
def ensure_order_by(paths, refresh=True):
    """out/order-by<tag>.json, rebuilt from THIS run's artifacts when stale.

    engine/sep_gap.py with --inputs takes its frozen path: it reads the inputs
    JSON, the day files and reference/oil-synonyms.csv, and never opens a HANA
    connection. Verified by reading main_frozen(), which returns before the
    first q() call. It must run with cwd=jolly — the synonyms path is relative.

    A REBUILD LANDS IN A TEMP FILE AND IS MOVED INTO PLACE ONLY WHEN EVERY CHECK HAS
    PASSED. It used to be written straight to out/order-by<tag>.json before build()
    ran, so a refused run left a gap list behind with a fresh mtime — and the NEXT run
    read that mtime, called the list current, skipped the rebuild and built on numbers
    nobody was allowed to publish. Refusing to write and then leaving a file behind is
    not refusing to write.

    Returns (state, path_to_read, [(tmp, final), ...] still to be committed).
    """
    target = paths["order_by"]
    # Newer than BOTH the inputs and the newest day file. Comparing only against the
    # inputs would keep a gap list built before the engine was re-run on the same
    # freeze — a real case, because re-running the sim alone does not touch the inputs.
    newest = max([os.path.getmtime(paths["inputs"])]
                 + [os.path.getmtime(f)
                    for f in glob.glob(os.path.join(paths["days_dir"], "day-*.json"))])
    fresh = os.path.exists(target) and os.path.getmtime(target) >= newest
    if fresh or not refresh:
        return ("on disk" if fresh else "STALE (refresh off)"), target, []
    # sep_gap.py has no --json flag: it derives the JSON path from --csv by swapping the
    # extension (`a.csv.replace(".csv", ".json")`). So naming the temp CSV
    # `.order-by-live.csv.tmp` puts the JSON at `.order-by-live.json.tmp` — both hidden,
    # neither ending in .json or .csv, so nothing downstream mistakes them for the real
    # thing while they are still provisional.
    d, stem = os.path.dirname(target), os.path.basename(target)[:-len(".json")]
    tmp_csv = os.path.join(d, f".{stem}.csv.tmp")
    tmp_json = tmp_csv.replace(".csv", ".json")
    argv = [sys.executable, os.path.join(JOLLY, "engine", "sep_gap.py"),
            "--inputs", paths["inputs"],
            "--days-dir", paths["days_dir"],
            "--csv", tmp_csv,
            "--today", paths["today"]]
    proc = subprocess.run(argv, cwd=JOLLY, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, timeout=300)
    if proc.returncode != 0:
        for junk in (tmp_json, tmp_csv):
            try:
                os.remove(junk)
            except OSError:
                pass
        raise SystemExit(f"gen_live.py: engine/sep_gap.py failed rc={proc.returncode}\n"
                         f"{(proc.stderr or proc.stdout)[-600:]}")
    return ("rebuilt by engine/sep_gap.py (held back until the checks pass)", tmp_json,
            [(tmp_json, target), (tmp_csv, os.path.join(d, f"{stem}.csv"))])


def commit_order_by(pending):
    """Move the held-back gap list into place. Called only after every check passed."""
    done = []
    for tmp, final in pending:
        if os.path.exists(tmp):
            os.replace(tmp, final)
            done.append(os.path.basename(final))
    return done


def drop_order_by(pending):
    """Throw the held-back gap list away — a refused run leaves NOTHING behind."""
    for tmp, _final in pending:
        try:
            os.remove(tmp)
        except OSError:
            pass


# =============================================================== the builder ==
def build(paths, check):
    """Everything, in one pass. Returns (outputs, stats)."""
    inp = load(paths["inputs"])
    summary = load(paths["summary"])
    events = load(paths["events"])
    order_by = load(paths.get("order_by_read") or paths["order_by"])
    day_files = sorted(glob.glob(os.path.join(paths["days_dir"], "day-*.json")))
    days = [load(f) for f in day_files]
    august = load(os.path.join(SIM, "summary.json"))

    meta = inp["meta"]
    opening = inp["opening"]
    rules = inp["rules"]
    plan = inp["plan"]
    orders = inp["orders"]
    lines_cfg = inp["lines"]
    lines_basis = inp.get("lines_basis") or {}
    realise = inp["realise"]
    prov = inp["provenance"]
    honesty = inp["honesty"]
    warnings = list(inp.get("warnings") or [])

    for person in inp.get("people") or []:
        collect_number(person.get("whatsapp", ""))
        collect_number(person.get("display", ""))

    h0, h1 = meta["horizon"]
    horizon_days = (date.fromisoformat(h1) - date.fromisoformat(h0)).days + 1
    lpp = {p["code"]: p["litres_per_piece"] for p in plan}
    plan_by_code = {p["code"]: p for p in plan}
    eff = rules["efficiency"]
    eff_pct = round(eff * 100)
    lag_days = rules["invoice_truck_lag_days"]
    day1_dm = dm(h0)

    stamp = {
        "collected_at": meta.get("state_collected_at") or meta.get("as_of"),
        "as_of": meta["as_of"],
        "horizon": meta["horizon"],
        "rolling": True,
        "forward": True,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "live/gen_live.py",
    }

    # ---- the rolling shape itself ------------------------------------------
    check("day files == summary days == run length",
          len(days) == len(summary["days"]) == horizon_days,
          f"{len(days)} files / {len(summary['days'])} summary / {horizon_days} dates")
    check("day 1 is the first day of the run", bool(days) and days[0]["date"] == h0,
          f"{days[0]['date'] if days else '-'} vs {h0}")
    check("last day is the last day of the run", bool(days) and days[-1]["date"] == h1,
          f"{days[-1]['date'] if days else '-'} vs {h1}")
    check("dates run forward with no gap",
          all((date.fromisoformat(days[i]["date"]) - date.fromisoformat(days[i - 1]["date"])).days == 1
              for i in range(1, len(days))))
    check("this file says it is a rolling re-plan", meta.get("rolling") is True,
          f"meta.rolling={meta.get('rolling')} — gen_live.py is for the live re-plan; the "
          f"31-August one is site-sep/scripts/gen-data.py's job")

    # ---- what no machine can fill ------------------------------------------
    slots = set()
    for spec in lines_cfg.values():
        slots.update(spec.keys())
    if "5L" in slots:
        slots.add("15L")          # the engine works 15 L PET off the 5 L head
    no_machine = []
    for row in plan:
        need = slot_of(row)
        if need in slots:
            continue
        entry = {
            "code": row["code"], "sku": row["sku"], "pack_type": row["pack_type"],
            "litres_per_piece": row["litres_per_piece"],
            "plan_pieces": row["pieces"], "plan_litres": row["litres"],
            "slot_needed": need,
            "reason": plain(f"no machine can fill {plain_slot(need)}"),
        }
        rate = realise.get(row["code"])
        if rate:
            entry["value_est_rs"] = round(row["litres"] * rate)
            entry["value_est_derived"] = True
        no_machine.append(entry)
    no_machine.sort(key=lambda r: -r["plan_litres"])
    ran = {r["code"] for d in days for r in d["runs"]}
    check("products with no machine never appear in a run",
          all(u["code"] not in ran for u in no_machine),
          str([u["code"] for u in no_machine if u["code"] in ran]))
    no_machine_for = " or ".join(sorted({plain_slot(u["slot_needed"]) for u in no_machine})) or "-"

    # ---- spine + day files --------------------------------------------------
    events_by_day = defaultdict(list)
    for event in events:
        events_by_day[event["day"]].append(event)
    binder_fgs = defaultdict(set)
    for day in days:
        for block in day["blocked"]:
            binder_fgs[block["binder"]].add(block["code"])

    po_cum_label = plain("total ordered since day 1 — it only ever goes up, so it is NOT what is still pending")
    po_open_label = plain("the planner's rough counter — it shows more litres than are really still to be sent, "
                          "so use 'still to be sent' instead")
    open_real_note = plain(f"confirmed orders minus what has been billed, counted from day 1 and including orders "
                           f"already pending on {day1_dm} — expected orders (not yet ordered) are left out")

    spine, details = [], []
    cum_in = cum_out = 0.0
    unmapped = set()
    tag_faults = []
    for i, day in enumerate(days):
        real_orders, fcst_orders = [], []
        for order in day["new_orders"]:
            (fcst_orders if is_forecast(order) else real_orders).append(order)
            if is_forecast(order) and not (
                    order.get("channel") == "FORECAST"
                    and str(order.get("docnum", "")).startswith("FCST")
                    and "not yet ordered" in str(order.get("customer", ""))):
                tag_faults.append(f"{day['date']} {order.get('docnum')}")

        def total(rows, key):
            return round(sum(r.get(key, 0) for r in rows))

        real_l = 0.0
        for order in real_orders:
            per = lpp.get(order["code"])
            if per is None:
                unmapped.add(order["code"])
            else:
                real_l += order["pieces"] * per
        cum_in += real_l

        disp_real = [x for x in day["dispatched"] if not str(x.get("docnum", "")).startswith("FCST")]
        disp_fcst = [x for x in day["dispatched"] if str(x.get("docnum", "")).startswith("FCST")]
        cum_out += sum(x["litres"] for x in disp_real)

        received = [dict(r, kind=item_kind(r["code"]))
                    for r in sorted(day["received"], key=lambda r: -r["qty"])]
        day_events = events_by_day.get(day["date"], [])

        book = {
            "plan_left_l": day["book"]["plan_left_l"],
            "po_cumulative_value_rs": day["book"]["po_open_value"],
            "po_cumulative_value_label": po_cum_label,
            "po_open_l_raw": day["book"]["po_open_l"],
            "po_open_l_raw_label": po_open_label,
            "forecast_open_l": day["book"].get("forecast_open_l", 0),
        }
        row = {
            "n": i + 1,
            "date": day["date"],
            "weekday": day["weekday"],
            "working": day["working"],
            "made_l": day["made_litres"],
            "value_rs": day["made_value"],
            "shipped_l": day["shipped_litres"],
            "util": day["line_util"],
            "storage_pct": day["storage"]["pct"],
            "headroom_l": day["storage"]["headroom_l"],
            "runs": len(day["runs"]),
            "flushes": day["flushes"],
            "blocked": len(day["blocked"]),
            "unblocked": len(day.get("unblocked", [])),
            "bought": len(day["bought"]),
            "oil_used_l": day.get("oil_used_l", 0),
            "orders": {
                "real_rows": len(real_orders),
                "real_pieces": total(real_orders, "pieces"),
                "real_value_rs": total(real_orders, "value"),
                "forecast_rows": len(fcst_orders),
                "forecast_pieces": total(fcst_orders, "pieces"),
                "forecast_value_rs": total(fcst_orders, "value"),
                "forecast_assumed": True,
            },
            "dispatched": {
                "real_l": round(sum(x["litres"] for x in disp_real)),
                "forecast_l": round(sum(x["litres"] for x in disp_fcst)),
            },
            "received_count": len(received),
            "received_top": received[:5],
            "events": dict(Counter(e["kind"] for e in day_events)),
            # the same three counts engine/build_list.py puts in `news`, worked out
            # from the day file itself — the build list is not run on this cycle, and
            # these never needed it.
            "news": {
                "materials_landed": len(received),
                "real_pos_entering": len(real_orders),
                "forecast_rows": len(fcst_orders),
            },
            "book": book,
            "open_real_l_computed": round(cum_in - cum_out),
            "open_real_l_note": open_real_note,
            # the stamp. spine.json is an array (SpineDay[]), so it rides per row
            # and a single row lifted out of the file still knows its vintage.
            "collected_at": stamp["collected_at"],
            "horizon": stamp["horizon"],
        }
        spine.append(row)

        details.append({
            "meta": dict(stamp, n=i + 1, date=day["date"]),
            "n": i + 1,
            "date": day["date"],
            "weekday": day["weekday"],
            "working": day["working"],
            "made_litres": day["made_litres"],
            "made_value_rs": day["made_value"],
            "shipped_litres": day["shipped_litres"],
            "oil_used_l": day.get("oil_used_l", 0),
            "oil_on_hand_l": day.get("oil_on_hand_l", 0),
            "line_util": day["line_util"],
            "line_hours": day["line_hours"],
            "flushes": day["flushes"],
            "storage": day["storage"],
            "storage_ceiling_assumed": True,
            "book": book,
            "open_real_l_computed": row["open_real_l_computed"],
            "runs": day["runs"],
            "blocked": day["blocked"],
            "unblocked": day.get("unblocked", []),
            "waiting_on": day.get("waiting_on", []),
            "received": received,
            "orders_real": real_orders,
            "orders_forecast": [dict(o, assumed=True) for o in fcst_orders],
            "dispatched_real": disp_real,
            "dispatched_forecast": [dict(x, assumed=True) for x in disp_fcst],
            "bought": day["bought"],
            "decisions": day.get("decisions", []),
            "events": [e for e in day_events if e["kind"] != "BUILD_LIST"],
            "news": dict(row["news"], unblocked=[u["name"] for u in day.get("unblocked", [])]),
            "honesty": day["honesty"],
            "simulated": True,
        })

    check("day totals add up to the month total — made",
          sum(r["made_l"] for r in spine) == summary["totals"]["made_l"],
          f"{sum(r['made_l'] for r in spine)} vs {summary['totals']['made_l']}")
    check("day totals add up to the month total — billed",
          sum(r["shipped_l"] for r in spine) == summary["totals"]["shipped_l"],
          f"{sum(r['shipped_l'] for r in spine)} vs {summary['totals']['shipped_l']}")
    check("every order code has a litres-per-piece", not unmapped, str(sorted(unmapped)[:5]))
    check("every expected-order row carries all three marks", not tag_faults, str(tag_faults[:5]))

    # the same tagging rule over the whole demand stream, not just the day files
    stream_faults = [
        o.get("docnum") for o in orders
        if is_forecast(o) and not (o.get("channel") == "FORECAST"
                                   and str(o.get("docnum", "")).startswith("FCST")
                                   and o.get("_src") == "FORECAST")
    ]
    check("every expected row in the demand list is marked", not stream_faults, str(stream_faults[:5]))
    check("no confirmed order is marked as expected",
          not [o.get("docnum") for o in orders
               if not is_forecast(o) and str(o.get("docnum", "")).startswith("FCST")])

    # ---- lines ---------------------------------------------------------------
    basis_words = {"measured": "observed", "rated": "rated", "carried": "carried",
                   "derived": "derived"}
    line_slots = {}
    for line, spec in lines_cfg.items():
        rows = []
        for slot, rate in sorted(spec.items()):
            raw_basis = str((lines_basis.get(line) or {}).get(slot, "rated"))
            basis = basis_words.get(raw_basis, raw_basis)
            rows.append({
                "slot": slot,
                "stored_rate_per_hr": rate,
                "rate_basis": basis,
                "rate_basis_raw": raw_basis,
                "effective_rate_per_hr": round(rate * eff, 1),
                "note": plain(
                    f"this speed was measured on the machine in August — the plan then runs it at {eff_pct}% of even that"
                    if basis == "observed" else
                    f"the machine's listed speed — the plan runs it at {eff_pct}% of that"
                    if basis == "rated" else
                    f"a speed carried over from the last plan — the plan runs it at {eff_pct}% of that"),
            })
        if "5L" in spec:
            rows.append({
                "slot": "15L",
                "stored_rate_per_hr": round(spec["5L"] / 3.0, 1),
                "rate_basis": "derived",
                "rate_basis_raw": "derived",
                "effective_rate_per_hr": round(spec["5L"] / 3.0 * eff, 1),
                "note": plain("worked out from the 5L speed — same litres per hour, so a third of the "
                              "bottles — nobody has measured a 15L speed"),
            })
        line_slots[line] = rows

    runs_by_line = defaultdict(list)
    for day in days:
        for run in day["runs"]:
            runs_by_line[run["line"]].append(dict(run, date=day["date"]))

    line_stats = []
    for line in lines_cfg:
        runs = runs_by_line.get(line, [])
        agg = defaultdict(float)
        for run in runs:
            agg[run["sku"]] += run["litres"]
        line_stats.append({
            "name": line,
            "slots": line_slots[line],
            "runs": len(runs),
            "litres": round(sum(r["litres"] for r in runs)),
            "pieces": round(sum(r["pieces"] for r in runs)),
            "hours_run": round(sum(r["hours"] for r in runs), 1),
            "hours_on_line": round(sum(d["line_hours"].get(line, 0) for d in days if d["working"]), 1),
            "value_rs": round(sum(r["value"] for r in runs)),
            "days_active": len({r["date"] for r in runs}),
            "flush_minutes": round(sum(r["flush_min"] for r in runs)),
            "top_skus": [{"sku": k, "litres": round(v)}
                         for k, v in sorted(agg.items(), key=lambda x: -x[1])[:5]],
        })

    measured_slots = sorted(f"{line} {slot}" for line, spec in lines_basis.items()
                            for slot, basis in spec.items() if basis == "measured")
    rate_note = plain(
        f"the plan runs every machine at {eff_pct}% of its listed speed — the pace the factory really kept "
        f"in August. Where the listed speed is one we measured ourselves, the plan runs it at {eff_pct}% "
        f"of even that — on the careful side")
    lines_out = {
        "meta": dict(stamp),
        "efficiency": eff,
        "efficiency_note": rate_note,
        "lines": line_stats,
        "total_litres": summary["totals"]["made_l"],
        "total_litres_note": plain("adding up the machines can differ from the month total by a few litres "
                                   "(rounding) — use the month total"),
        "measured_slots": measured_slots,
        "runs_by_line": dict(runs_by_line),
        "measured_from": plain("machine speeds: the factory's own figures, read live this cycle · "
                               "runs: the computer plan, day by day"),
    }
    # site-sep/lib/types.ts types rate_basis as observed | rated | derived. The live
    # freeze can also fall back to a carried table, which is a fourth honest word —
    # so the check is that the word is one WE define, not that it is one of three.
    # A word outside this set means freeze_live.py grew a basis nobody rendered.
    seen_basis = {s["rate_basis"] for line in line_stats for s in line["slots"]}
    check("every machine speed says where it came from, in a word the site knows",
          seen_basis <= {"observed", "rated", "derived", "carried"}, str(sorted(seen_basis)))
    lines_out["rate_basis_words"] = sorted(seen_basis)
    check("machine litres add up to the month total within rounding",
          abs(sum(s["litres"] for s in line_stats) - summary["totals"]["made_l"]) <= 60,
          f"{sum(s['litres'] for s in line_stats)} vs {summary['totals']['made_l']}")

    # ---- storage -------------------------------------------------------------
    # THE PILE CHANGES THESE CHECKS. Mark 2 opened with nothing billed-but-not-
    # gone, so gen-data.py could assert an exact equality: what leaves the gate on
    # day n IS day n-lag's billing, and the month's trucking adds up to the month's
    # billing. Both statements quietly assume an empty yard. Mark 3 opens with a
    # real pile (read live off the dispatch plans), the engine releases it 45/35/20
    # over the first three days, and its release queue is FIFO by insertion rather
    # than sorted by date — so a day-1 bill queued behind the pile's day-3 entry
    # leaves on day 4, not day 3. Asserting the old equality here would report the
    # engine's real, correct behaviour as a fault. What is still true, on any
    # length of run and any size of pile, is a two-sided bound:
    #
    #   billed up to day n-lag  <=  trucked up to day n  <=  pile + billed up to n-lag
    #
    # left: nothing has left before its bill aged the lag. right: nothing left
    # early, and the extra can never exceed the pile we opened with. With an empty
    # yard both sides close on Mark 2's exact equality.
    open_pile = round(opening["standing_l"])
    open_physical = opening["fg_litres"] + opening["standing_l"]
    # AT OPEN means at open. series[0]["pct"] is the END of day 1 — after the day's
    # filling and billing — so pairing it with open_physical shipped a figure and a
    # percentage from two different moments: 672,747 L labelled 95.8% of an 827,000 L
    # ceiling, which is 81.3%. Every "at open" percentage on the site now comes off
    # the same litres it is printed beside.
    open_pct = round(100.0 * open_physical / rules["storage_ceiling_l"], 1) if rules["storage_ceiling_l"] else 0.0
    series = []
    prev = open_physical
    cum_trucked = cum_invoiced = 0
    for i, day in enumerate(days):
        store = day["storage"]
        parts = store["fg_in_godown_l"] + store["invoiced_not_trucked_l"]
        check(f"godown splits into stock + billed-not-gone, day {i + 1}",
              abs(store["physical_l"] - parts) <= 1,
              f"{store['physical_l']} vs {parts}")
        trucked_raw = prev + day["made_litres"] - store["physical_l"]
        check(f"trucks-left never negative, day {i + 1}", trucked_raw >= -2, str(round(trucked_raw)))
        trucked = max(0, round(trucked_raw))
        cum_trucked += trucked
        # billing that has had time to reach a truck by the end of day n
        due = sum(round(d["shipped_litres"]) for d in days[:max(0, i + 1 - lag_days)])
        tol = i + 2                                   # 1 L of rounding a day, each side
        check(f"nothing leaves before its bill is {lag_days} days old, day {i + 1}",
              cum_trucked <= open_pile + due + tol,
              f"{cum_trucked} left vs {open_pile} in the yard + {due} billed")
        check(f"trucks never fall behind the billing queue, day {i + 1}",
              cum_trucked + tol >= due, f"{cum_trucked} left vs {due} billed and due")
        cum_invoiced += round(day["shipped_litres"])
        series.append({
            "n": i + 1, "date": day["date"], "working": day["working"],
            "physical_l": store["physical_l"], "pct": store["pct"],
            "fg_in_godown_l": store["fg_in_godown_l"],
            "invoiced_not_trucked_l": store["invoiced_not_trucked_l"],
            "headroom_l": store["headroom_l"],
            "invoiced_l": round(day["shipped_litres"]),
            "trucked_out_l": trucked,
            "cum_trucked_out_l": cum_trucked,
        })
        prev = store["physical_l"]

    # DAY 1 IS THE ONLY OBSERVED DAY, so it is reconciled to the live counts line by
    # line rather than in one lump. Day 1's godown is recorded at the END of the day
    # and nothing leaves the gate on day 1 (the pile's first release is tomorrow), so
    # all three of these are exact identities on any cycle:
    #     stock in the godown = live count + filled today - billed today
    #     billed-not-gone     = the live pile + billed today
    #     the whole godown    = live count + live pile + filled today
    # An earlier draft of this file checked only "godown == count + pile", which
    # happened to pass while the godown was so full that day 1 filled nothing. It
    # broke the first cycle the plant produced anything — the check was wrong, not
    # the engine. Three identities instead of one lump is the fix.
    d1, s1 = days[0], days[0]["storage"]
    recon = {
        "fg_in_godown": {
            "shown": s1["fg_in_godown_l"],
            "expected": round(opening["fg_litres"] + d1["made_litres"] - d1["shipped_litres"]),
            "from": plain("counted live in the two finished-goods rooms, plus what is filled today, "
                          "less what is billed today"),
        },
        "billed_not_gone": {
            "shown": s1["invoiced_not_trucked_l"],
            "expected": round(open_pile + d1["shipped_litres"]),
            "from": plain("the pile read live off the dispatch plans, plus today's billing — "
                          "no truck leaves on day 1"),
        },
        "whole_godown": {
            "shown": s1["physical_l"],
            "expected": round(opening["fg_litres"] + open_pile + d1["made_litres"]),
            "from": plain("the two above added together"),
        },
    }
    for key, row in recon.items():
        row["delta_l"] = row["shown"] - row["expected"]
        check(f"day 1 reconciles to the live count — {key}", abs(row["delta_l"]) <= 1,
              f"{row['shown']} vs {row['expected']}")
    # every litre either started in the yard, or was billed inside the run; and it
    # either left on a truck or is still waiting for one on the last day.
    residual = abs(cum_trucked + series[-1]["invoiced_not_trucked_l"] - open_pile - cum_invoiced)
    check("nothing appears or vanishes: yard + billed = trucked + still waiting",
          residual <= max(3, len(series)), f"{residual} L over {len(series)} days")
    # how long the day-1 pile takes to clear, worked out from the run itself
    pile_cleared_day = next((s["n"] for s in series if s["cum_trucked_out_l"] >= open_pile), None)

    falls = [(series[i - 1]["physical_l"] - series[i]["physical_l"], i) for i in range(1, len(series))]
    if falls:
        drop, idx = max(falls)
        row = series[idx]
        src = series[idx - lag_days] if idx - lag_days >= 0 else None
        biggest_fall = {
            "n": row["n"], "date": row["date"], "fall_l": round(drop),
            "trucked_out_l": row["trucked_out_l"], "made_l": round(days[idx]["made_litres"]),
            "invoiced_that_day_l": row["invoiced_l"],
            "source_day_n": src["n"] if src else None,
            "source_date": src["date"] if src else None,
            "note": plain(f"the drop is trucks leaving (billed {lag_days} days earlier) minus what was "
                          "filled that day — not that day's billing"),
        }
    else:
        biggest_fall = None
    big_inv = max(series, key=lambda s: s["invoiced_l"])
    big_trk = max(series, key=lambda s: s["trucked_out_l"])

    pile_note = plain(
        "stock billed but not yet on a truck IS counted here — read live off the factory's own dispatch "
        "plans, not guessed at nothing. Mark 2 put it at nothing and said so; this is the real pile")
    storage_out = {
        "meta": dict(stamp),
        "ceiling": {
            "working_l": rules["storage_ceiling_l"],
            "peak_l": rules["storage_peak_l"],
            "assumed": True,
            "source": plain("Daman's number, from his spreadsheet — not measured"),
            "open_question": "Q2",
        },
        # The Mark 2 key, kept so a component copied from site-sep keeps reading —
        # with the flags telling the truth this time: the pile is read live, so it
        # is neither a guess nor the optimistic zero C-0054 warned about.
        "standing_at_open": {
            "litres": opening["standing_l"],
            "assumed": False,
            "optimistic": False,
            "note": pile_note,
        },
        "at_open": {
            "physical_l": round(open_physical),
            "fg_l": opening["fg_litres"],
            "billed_not_gone_l": opening["standing_l"],
            "pct": open_pct,
            "over_ceiling": open_pct >= 100,
            "measured": True,
            "assumed": False,
            "source": prov.get("standing"),
            "alternatives": opening.get("standing_l_alternatives"),
            "reconciliation": recon,
            "clears_on_day_n": pile_cleared_day,
            "clears_note": plain(
                "the planner sends this pile out over the first few days (roughly half, then a third, "
                "then the rest), so the first days show huge truck movements that were billed before "
                "today"),
            "note": pile_note,
        },
        "invoice_truck_lag_days": lag_days,
        "invoice_truck_note": plain(
            f"'sent' here means billed, not the truck leaving — after billing, the truck leaves "
            f"{lag_days} days later, which is the middle of what the gate log really shows. "
            "Trucks-left litres are worked out from how full the godown was"),
        "series": series,
        "biggest_fall": biggest_fall,
        "biggest_invoicing_day": {"n": big_inv["n"], "date": big_inv["date"],
                                  "invoiced_l": big_inv["invoiced_l"],
                                  "trucked_out_that_day_l": big_inv["trucked_out_l"]},
        "biggest_trucked_day": {"n": big_trk["n"], "date": big_trk["date"],
                                "trucked_out_l": big_trk["trucked_out_l"]},
        "days_ge_95": sum(1 for d in summary["days"] if d["storage_pct"] >= 95),
        "days_ge_100": [d["date"] for d in summary["days"] if d["storage_pct"] >= 100],
        "throttles": [{"day": e["day"], "pct_start_of_day": e["pct_start_of_day"],
                       "headroom_l": e["headroom_l"]}
                      for e in events if e["kind"] == "STORAGE_THROTTLE"],
        "simulated": True,
    }
    # Every "at open" percentage must come off the litres printed next to it. This
    # caught nothing when it was written, because it was written as the fix — before
    # it, at_open paired 672,747 L with day 1's END-of-day 95.8%, an implied ceiling
    # of 702,000 L nobody has.
    _ao = storage_out["at_open"]
    check("the at-open percentage is the at-open litres",
          abs(_ao["pct"] - 100.0 * _ao["physical_l"] / storage_out["ceiling"]["working_l"]) <= 0.1,
          f"{_ao['pct']}% against {_ao['physical_l']:,} L of "
          f"{storage_out['ceiling']['working_l']:,} L")
    check("the at-open litres are stock plus the pile it opened with",
          abs(_ao["physical_l"] - (_ao["fg_l"] + _ao["billed_not_gone_l"])) <= 1,
          f"{_ao['physical_l']} vs {_ao['fg_l']} + {_ao['billed_not_gone_l']}")

    # ---- materials (the order-by list) --------------------------------------
    ob_summary = order_by["summary"]
    august_codes = set(ob_summary["august_comparable"]["codes"])
    ob_rows = [dict(r,
                    late=str(r.get("status", "")).startswith("LATE"),
                    zero_literal=r.get("at_zero") == "YES",
                    zero_august_rule=r["code"] in august_codes)
               for r in order_by["rows"]]

    literal = {r["code"] for r in ob_rows if r["zero_literal"]}
    chase = sorted(r["code"] for r in ob_rows if r["on_hand"] == 0 and r.get("on_order", 0) > 0)
    at_zero_now = [{"code": r["code"], "name": r["name"], "kind": r["kind"],
                    "on_order": r.get("on_order", 0)}
                   for r in ob_rows if r["on_hand"] == 0]
    check("nothing counts as both empty-and-unordered and on-its-way",
          not (literal & set(chase)), str(sorted(literal & set(chase))[:5]))
    check("empty shelves = nothing-on-order plus already-on-a-PO",
          len(at_zero_now) == len(literal) + len(chase),
          f"{len(at_zero_now)} vs {len(literal)} + {len(chase)}")

    aug_def = ob_summary["august_comparable"]["definition"]
    aug_pct = re.search(r"<\s*([\d.]+)\s*%", aug_def)
    check("the August 'nothing in stock' rule is read from the list, not typed", bool(aug_pct), aug_def)

    materials_out = {
        "meta": dict(stamp),
        "generated": ob_summary["generated"],
        # engine/sep_gap.py hard-codes the words "sim/sep-inputs.json" into its own
        # basis string whatever --inputs it was handed, so passing it through would
        # put the 31-August file's name on a list built from today's live one. Say
        # where it really came from, and keep the artifact's own claim beside it.
        "basis": plain(f"the live count taken this cycle ({os.path.basename(paths['inputs'])}) "
                       f"and the runs the planner scheduled from it "
                       f"({os.path.basename(paths['days_dir'].rstrip(os.sep))})"),
        "basis_raw": ob_summary["basis"],
        "components_in_plan": ob_summary["components_in_plan"],
        "under_100_cover": ob_summary["under_100_cover"],
        "must_order_week1": ob_summary["must_order_week1"],
        "already_late": ob_summary["already_late"],
        "lead_days": ob_summary["lead_days"],
        "zero_definitions": {
            "literal": {
                "definition": plain("nothing in stock and nothing on order"),
                "items": ob_summary["items_at_zero"],
                "zero_pack": ob_summary["zero_pack"],
                "zero_oil": ob_summary["zero_oil"],
                "skus_blocked": ob_summary["skus_blocked_by_zero"],
                "blocked_value_rs": ob_summary["blocked_value_rs"],
                "blocked_value_note": ob_summary["blocked_value_note"],
            },
            "august_rule": {
                "definition": plain(
                    f"almost nothing — stock plus what is on order is under "
                    f"{aug_pct.group(1) if aug_pct else '?'}% of the month's need "
                    "(August's rule: a sliver still counts as nothing)"),
                "items": ob_summary["august_comparable"]["items"],
                "skus_blocked": ob_summary["august_comparable"]["skus_blocked"],
                "blocked_value_rs": ob_summary["august_comparable"]["blocked_value_rs"],
                "codes": ob_summary["august_comparable"]["codes"],
            },
            "opening_zero_reconciliation": {
                "opening_items": len(at_zero_now),
                "literal_items": len(literal),
                "chase_items": len(chase),
                "chase_codes": chase,
                "note": plain(
                    f"{len(at_zero_now)} items have nothing in stock today: {len(literal)} with nothing "
                    f"on order, plus {len(chase)} already on a PO — chase those"),
            },
            "note": plain("there are two ways to count 'nothing in stock' — say which one you are showing"),
        },
        "rows": ob_rows,
        "opening_at_zero": at_zero_now,
        "unproducible": no_machine,
        "unproducible_note": plain(
            f"products in this month's target that no machine can fill (there is no machine for "
            f"{no_machine_for}) — shown, not hidden"),
        "synonyms": ob_summary["synonyms"],
    }
    check("gap-list rows match its own count",
          len(ob_rows) == ob_summary["components_in_plan"],
          f"{len(ob_rows)} vs {ob_summary['components_in_plan']}")
    check("late rows match its own count",
          sum(1 for r in ob_rows if r["late"]) == ob_summary["already_late"])
    check("the gap list was built from THIS run's days",
          paths["days_dir"].rstrip("/").split(os.sep)[-1] in str(ob_summary.get("basis", "")),
          str(ob_summary.get("basis"))[:120])

    # ---- the stuck -> ordered -> arrived -> running chains --------------------
    ordered_ev = sorted((e for e in events if e["kind"] == "ORDERED_BLOCKER"), key=lambda e: e["day"])
    unblocked_ev = sorted((e for e in events if e["kind"] == "UNBLOCKED"), key=lambda e: e["day"])
    consumed, chains = set(), []
    for event in ordered_ev:
        match = None
        for j, unb in enumerate(unblocked_ev):
            if j in consumed or unb["code"] != event["code"] or unb["day"] < event["day"]:
                continue
            match = (j, unb)
            break
        chain = {
            "code": event["code"], "name": event["name"], "kind": item_kind(event["code"]),
            "ordered_day": event["day"], "qty": event["qty"], "lands": event["lands"],
            "lead_days": event["lead"],
            "fg_codes_blocked": sorted(binder_fgs.get(event["code"], [])),
            "simulated": True,
        }
        if match:
            j, unb = match
            consumed.add(j)
            chain["unblocked_day"] = unb["day"]
            chain["waited_days"] = unb["waited_days"]
            first_run = None
            for day in days:
                if day["date"] < unb["day"]:
                    continue
                for run in day["runs"]:
                    if run["code"] in binder_fgs.get(event["code"], set()):
                        first_run = {"day": day["date"], "code": run["code"],
                                     "sku": run["sku"], "litres": round(run["litres"])}
                        break
                if first_run:
                    break
            if first_run:
                chain["first_run_after_unblock"] = first_run
        else:
            chain["unblocked_day"] = None
            chain["note"] = plain(f"arrives after {dm(days[-1]['date'])} — still stuck inside this plan")
        chains.append(chain)

    loops_out = {
        "meta": dict(stamp),
        "note": plain("stuck → ordered → arrived → running, one chain per missing item. "
                      "'Days waited' is the planner's own count"),
        "chains": chains,
        "ordered_events": len(ordered_ev),
        "unblocked_events": len(unblocked_ev),
        "resolved_chains": sum(1 for c in chains if c.get("unblocked_day")),
        "ran_after_unblock": sum(1 for c in chains if c.get("first_run_after_unblock")),
        "landed_no_run": sum(1 for c in chains
                             if c.get("unblocked_day") and not c.get("first_run_after_unblock")),
        "resolved_note": plain(
            "'arrived' counts items that arrive inside this plan and free their products. Only some of "
            "those products actually run again before the last day — say which count you mean"),
        "simulated": True,
    }
    check("every arrival is matched to a chain", len(consumed) == len(unblocked_ev),
          f"{len(consumed)} vs {len(unblocked_ev)}")
    check("ran + arrived-but-idle = arrived",
          loops_out["ran_after_unblock"] + loops_out["landed_no_run"] == loops_out["resolved_chains"])
    check("chains left stuck really do land after the last day",
          all((c.get("lands") or "") > days[-1]["date"] for c in chains if not c.get("unblocked_day")),
          str([c["lands"] for c in chains if not c.get("unblocked_day")][:5]))

    # ---- demand --------------------------------------------------------------
    fcst = [o for o in orders if is_forecast(o)]
    real = [o for o in orders if not is_forecast(o)]
    tot_pieces = sum(o["pieces"] for o in orders) or 1
    tot_value = sum(o["value"] for o in orders) or 1
    tot_litres = sum(o["pieces"] * lpp.get(o["code"], 0) for o in orders) or 1
    fc_pieces = sum(o["pieces"] for o in fcst)
    fc_value = sum(o["value"] for o in fcst)
    fc_litres = sum(o["pieces"] * lpp.get(o["code"], 0) for o in fcst)
    demand = {
        "rows": len(orders),
        "real_rows": len(real),
        "forecast_rows": len(fcst),
        "real_pieces": round(sum(o["pieces"] for o in real)),
        "forecast_pieces": round(fc_pieces),
        "real_value_rs": round(sum(o["value"] for o in real)),
        "forecast_value_rs": round(fc_value),
        "forecast_share_pieces_pct": round(fc_pieces / tot_pieces * 100, 2),
        "forecast_share_value_pct": round(fc_value / tot_value * 100, 2),
        "forecast_share_litres_pct": round(fc_litres / tot_litres * 100, 2),
        "order_dates": len({o["date"] for o in orders}),
        "channels": dict(Counter(o["channel"] for o in orders)),
        "sources": dict(Counter(o.get("_src", "?") for o in orders)),
        "note": plain(
            "what customers want mixes confirmed orders with expected orders — this month's target, not "
            "ordered yet. Expected rows are marked in the data and must always look different on the page"),
    }

    # ---- honesty -------------------------------------------------------------
    bad_rate_phrase = "of rated, the observed rate"
    assumed = [a for a in honesty.get("assumed", []) if bad_rate_phrase not in a]
    assumed.append(rate_note)
    check("no line still says the wrong thing about machine speeds",
          not any(bad_rate_phrase in a for a in honesty.get("assumed", [])),
          str([a for a in honesty.get("assumed", []) if bad_rate_phrase in a][:2]))

    outlier = None
    r155 = realise.get("FG0000155")
    o155 = [o for o in orders if o["code"] == "FG0000155" and not is_forecast(o)]
    if r155 and o155 and lpp.get("FG0000155"):
        pieces = sum(o["pieces"] for o in o155)
        if pieces:
            per_l = sum(o["value"] for o in o155) / pieces / lpp["FG0000155"]
            if per_l:
                outlier = {
                    "code": "FG0000155",
                    "sku": plan_by_code["FG0000155"]["sku"],
                    "realise_rs_per_l": r155,
                    "order_book_rs_per_l": round(per_l, 2),
                    "ratio": round(r155 / per_l, 2),
                    "note": plain("this product's selling price per litre is an odd inherited figure — "
                                  "never show it as a headline without saying so"),
                }

    label_rules = [
        {"id": "rolling-replan", "rule": plain(
            "only today is real. Every later day on this site is worked out by the computer from today's "
            "count plus what the plan decides — and the whole thing is re-worked every few minutes"),
         "as_of": meta["as_of"], "days_left": len(days)},
        {"id": "po-open-value", "rule": po_cum_label},
        {"id": "po-open-litres", "rule": po_open_label},
        {"id": "orders-mixed", "rule": plain(
            "each day's new orders MIX confirmed orders with expected orders (not ordered yet) — always "
            "split them. On a quiet day the new orders are 100% expected."),
         "forecast_share_litres_pct": demand["forecast_share_litres_pct"]},
        {"id": "two-oil-series", "rule": plain(
            "'oil in stock' on the Summary (every oil) and on the day pages (only the oils in this "
            "month's recipes) are two different counts — never draw them as one line."),
         "opening_oil_l": opening["oil_l"]},
        {"id": "forecast-tags", "rule": plain(
            "expected orders (not ordered yet) are marked in the data — keep them looking different "
            "from confirmed orders everywhere.")},
        {"id": "ceiling-assumed", "rule": plain(
            "the godown limit is Daman's number from his spreadsheet — not measured. Say so wherever it "
            "appears (open question Q2)."),
         "working_l": rules["storage_ceiling_l"], "peak_l": rules["storage_peak_l"]},
        {"id": "standing-measured", "rule": pile_note,
         "billed_not_gone_l": opening["standing_l"],
         "pct_of_ceiling": round(opening["standing_l"] / rules["storage_ceiling_l"] * 100, 1)},
        {"id": "day1-pile", "rule": plain(
            "the pile of orders on day 1 is real, not a fault — it is the live order book as it stands "
            "right now."), "source": prov.get("orders")},
        {"id": "observed-then-derated", "rule": rate_note,
         "efficiency": eff, "measured_slots": measured_slots},
        {"id": "unproducible", "rule": plain(
            f"{len(no_machine)} products in this month's target have no machine (nothing fills "
            f"{no_machine_for}) — show them on the Stock and Order by when pages, do not hide them."),
         "codes": [u["code"] for u in no_machine]},
        {"id": "realise-outlier", "rule": plain(
            "FG0000155's selling price per litre is an odd inherited figure, far from its own order "
            "book — never show it as a headline without saying so."), "detail": outlier},
        {"id": "numbers-masked", "rule": plain(
            "no real phone number anywhere on this site — none is written into the data at all.")},
        {"id": "tank-dip", "rule": plain(
            "bulk oil comes from the tank yard's own daily readings, taken by hand — not a meter, and "
            "not always today's."), "source": prov.get("opening_oil")},
    ]

    honesty_out = {
        "meta": dict(stamp),
        "forward_rule": meta["rule"],
        "measured": honesty.get("measured", []),
        "assumed": assumed,
        "provenance": prov,
        "warnings": warnings,
        "label_rules": label_rules,
        "august_calibration": {
            "sim_made_l": august["totals"]["made_l"],
            "actual_made_l": august["totals"]["actual_made_l"],
            "delta_pct": round(abs(august["totals"]["made_l"] - august["totals"]["actual_made_l"])
                               / max(august["totals"]["actual_made_l"], 1) * 100, 2),
            "note": plain("tested on August: the same computer plan was run for August and came this "
                          "close to what the factory really made — that is why these numbers can be "
                          "trusted"),
        },
        "not_here": {
            "whatsapp": plain("the messages page belongs to the old site — the real one is the Jolly "
                              "WhatsApp helper"),
            "scenarios": plain("what-if shift patterns are not worked out on this run yet"),
            "build_list": plain("the machine-by-machine running order is not worked out on this run yet"),
        },
        "simulated": True,
    }

    # ---- day 1, what stopped it ----------------------------------------------
    blocked_today = days[0]["blocked"]
    zero_codes = literal
    def binder_class(code):
        if item_kind(code) == "OIL":
            return "oil"
        return "zero_stock_packaging" if code in zero_codes else "other_packaging"

    cls_attempts = Counter(binder_class(b["binder"]) for b in blocked_today)
    cls_products = defaultdict(set)
    for block in blocked_today:
        cls_products[binder_class(block["binder"])].add(block["code"])
    top = Counter(b["binder"] for b in blocked_today).most_common(1)
    day1_products = {b["code"] for b in blocked_today}
    day1_blocked = {
        "attempts": len(blocked_today),
        "products": len(day1_products),
        "product_binder_pairs": len({(b["code"], b["binder"]) for b in blocked_today}),
        "by_binder_class": {k: {"attempts": cls_attempts.get(k, 0),
                                "products": len(cls_products.get(k, set()))}
                            for k in ("oil", "zero_stock_packaging", "other_packaging")},
        "top_binder": None,
        "products_in_multiple_classes": sum(
            1 for p in day1_products if sum(1 for s in cls_products.values() if p in s) > 1),
        "zero_openers_products_blocked_run": len(
            {b["code"] for d in days for b in d["blocked"] if b["binder"] in zero_codes}),
        # the Mark 2 name for the same count. This run is a slice of a month, not a
        # month, so `_run` is the honest one; the old key stays so a page copied from
        # site-sep still finds it.
        "zero_openers_products_blocked_month": len(
            {b["code"] for d in days for b in d["blocked"] if b["binder"] in zero_codes}),
        "note": plain(
            "'attempts' = how many times the planner tried and was stopped, not how many products — "
            "quote products. One product can be short of oil and packing at once, so the per-type "
            "counts can overlap. On a day the godown is full nothing is tried at all, and this is zero"),
    }
    if top:
        code, attempts = top[0]
        day1_blocked["top_binder"] = {
            "code": code,
            "name": next(b["binder_name"] for b in blocked_today if b["binder"] == code),
            "kind": item_kind(code),
            "attempts": attempts,
            "products": len({b["code"] for b in blocked_today if b["binder"] == code}),
        }
    check("day-1 stop counts add up", sum(cls_attempts.values()) == len(blocked_today))

    # ---- overview ------------------------------------------------------------
    # What is coming, from the same table the engine reads. RM is litres, PM pieces.
    inbound_oil_l = sum(qty for day_map in inp.get("inbound_prebooked", {}).values()
                        for code, qty in day_map.items() if item_kind(code) == "OIL")
    inbound_pm = sum(qty for day_map in inp.get("inbound_prebooked", {}).values()
                     for code, qty in day_map.items() if item_kind(code) == "PACKAGING")
    # The overdue pile the site headlines. `backlog` holds documents the order cursor
    # never saw; docs it DID see are already in `orders` with their own date. On the
    # live feed this reads 0 because the OMS cursor only started on 2026-09-02 — a
    # real hole, not a quiet day, so it is published rather than left blank.
    backlog_rows = inp.get("backlog") or []
    backlog_docs = defaultdict(list)
    for r in backlog_rows:
        backlog_docs[r["docnum"]].append(r.get("due") or r.get("date"))
    backlog_overdue = sum(1 for dues in backlog_docs.values()
                          if min([d for d in dues if d] or [h1]) < h0)
    early_orders = sorted({o["date"] for o in orders if o["date"] < h0})

    working = [d for d in summary["days"] if d["working"]]
    utils = sorted(d["util"] for d in working)
    util_median = (utils[len(utils) // 2] if len(utils) % 2
                   else (utils[len(utils) // 2 - 1] + utils[len(utils) // 2]) / 2) if utils else 0
    peak = max(summary["days"], key=lambda d: d["made_l"])
    plan_litres = sum(p["litres"] for p in plan)

    overview = {
        "meta": dict(stamp,
                     month=meta["month"],
                     frozen=meta["frozen"],
                     replanned_days=meta.get("replanned_days"),
                     working_days_left=meta.get("working_days_left"),
                     state_completed_at=meta.get("state_completed_at"),
                     forward_rule=meta["rule"],
                     pieces_booked_today=meta.get("pieces_booked_today"),
                     pieces_booked_today_basis=meta.get("pieces_booked_today_basis"),
                     pieces_made_mtd=meta.get("pieces_made_mtd"),
                     pieces_made_mtd_basis=meta.get("pieces_made_mtd_basis")),
        "totals": {
            "made_l": summary["totals"]["made_l"],
            "value_rs": summary["totals"]["value"],
            "shipped_l": summary["totals"]["shipped_l"],
            "oil_used_l": summary["totals"]["oil_used_l"],
            "days": len(summary["days"]),
            "working_days": len(working),
            "runs": sum(r["runs"] for r in spine),
            "flushes": sum(r["flushes"] for r in spine),
            "bought_lines": summary["totals"]["bought_lines"],
            "events": summary["totals"]["events"],
            "util_median": round(util_median),
            "peak_day": {"date": peak["date"], "made_l": peak["made_l"]},
            # Only the machine-by-machine running order knows these, and it is not
            # worked out on this run. Published as nothing-known rather than as a
            # zero somebody would read as "the plant never changes oil".
            "oil_changes": None,
            "clearances_only": None,
            "oil_changes_basis": plain("not worked out on this run — it needs the "
                                       "machine-by-machine running order"),
        },
        "plan": {
            "litres": round(plan_litres),
            "skus": len(plan),
            "made_vs_plan_pct": round(summary["totals"]["made_l"] / max(plan_litres, 1) * 100, 1),
            "source": plain("the month's target, carried from the last plan — it is not re-read every cycle"),
        },
        "demand": demand,
        "opening": {
            "fg_litres": opening["fg_litres"],
            "fg_plan_l": opening["fg_plan_l"],
            "fg_other_l": opening["fg_other_l"],
            "oil_l": opening["oil_l"],
            "oil_mapped_l": opening.get("oil_mapped_l"),
            "oil_unmapped_l": opening.get("oil_unmapped_l"),
            "oil_l_definition": plain(
                "all oil in the tanks right now, every kind — the day pages count only the oils in this "
                "month's recipes, so the two are not the same line"),
            "packaging_pieces": opening["packaging_pieces"],
            "inbound_oil_l": round(inbound_oil_l),
            "inbound_packaging": round(inbound_pm),
            "standing_l": opening["standing_l"],
            "standing_assumed": False,
            "standing_measured": True,
            "standing_note": pile_note,
            "backlog_pieces": round(sum(r.get("pieces", 0) for r in backlog_rows)),
            "backlog_value_rs": round(sum(r.get("value", 0) for r in backlog_rows)),
            "plan_sku_backlog_docs": len(backlog_docs),
            "plan_sku_backlog_docs_overdue": backlog_overdue,
            "backlog_basis": plain(
                "orders that were already on the book before today and that the order reader has not "
                "walked back to yet. It reads low until the reader is walked backwards over the older "
                "order numbers"),
            "orders_dated_before_today": len(early_orders),
            "at_zero_count": len(at_zero_now),
            "physical_l": round(open_physical),
            "physical_pct": open_pct,
        },
        "storage": {
            "ceiling_l": rules["storage_ceiling_l"],
            "peak_l": rules["storage_peak_l"],
            "ceiling_assumed": True,
            "invoice_truck_lag_days": lag_days,
            "days_ge_95": storage_out["days_ge_95"],
            "days_ge_100": storage_out["days_ge_100"],
            "throttle_events": len(storage_out["throttles"]),
            "pct_at_open": open_pct,
        },
        "day1_blocked": day1_blocked,
        "august": honesty_out["august_calibration"],
        "materials_mini": {
            "components": ob_summary["components_in_plan"],
            "under_100_cover": ob_summary["under_100_cover"],
            "must_order_week1": ob_summary["must_order_week1"],
            "already_late": ob_summary["already_late"],
            "zero_literal_items": ob_summary["items_at_zero"],
            "zero_literal_value_rs": ob_summary["blocked_value_rs"],
            "zero_august_rule_items": ob_summary["august_comparable"]["items"],
            "zero_august_rule_value_rs": ob_summary["august_comparable"]["blocked_value_rs"],
        },
        "loops_mini": {
            "chains": len(chains),
            "resolved": loops_out["resolved_chains"],
            "ran_after_unblock": loops_out["ran_after_unblock"],
        },
        # Not on this run, and said so rather than left out: a missing key reads as a
        # crash on the page, an empty list reads as "there are none".
        "scenarios_mini": [],
        "scenarios_basis": plain("what-if shift patterns are not worked out on this run yet"),
        "whatsapp_mini": None,
        "whatsapp_basis": plain("the messages page belongs to the old site — the real one is the "
                                "Jolly WhatsApp helper"),
        "questions_top": [],
        "questions_basis": plain("the open questions list lives on the old site"),
        "unproducible": no_machine,
        "warnings": warnings,
        "sources": {k: source_row(v) for k, v in prov.items()},
        "simulated": True,
    }

    outputs = {
        "overview.json": overview,
        "spine.json": spine,
        "storage.json": storage_out,
        "materials.json": materials_out,
        "loops.json": loops_out,
        "honesty.json": honesty_out,
        "lines.json": lines_out,
    }
    for i, detail in enumerate(details):
        outputs[os.path.join("days", f"day-{i + 1:02d}.json")] = detail

    # ---- the scans, over what is actually about to be written ----------------
    for name, obj in outputs.items():
        scan_no_phones(check, name, obj)
        scan_numbers(check, name, obj)
    for name in ("overview.json", "storage.json", "materials.json", "loops.json",
                 "honesty.json", "lines.json"):
        got = outputs[name].get("meta") or {}
        check(f"{name} is stamped",
              got.get("collected_at") == stamp["collected_at"] and got.get("horizon") == stamp["horizon"],
              str({k: got.get(k) for k in ("collected_at", "horizon")}))
    check("spine rows are stamped",
          all(r.get("collected_at") == stamp["collected_at"] and r.get("horizon") == stamp["horizon"]
              for r in spine))
    check("day files are stamped",
          all((d.get("meta") or {}).get("collected_at") == stamp["collected_at"] for d in details))

    bad_words = sorted({(_BANNED_RE.search(s).group(0), s[:90])
                        for s in PLAIN_STRINGS if _BANNED_RE.search(s)})
    check("floor words only in the text this file writes", not bad_words, str(bad_words[:5]))

    # ---- the manifest: exactly what THIS run writes --------------------------
    # live/state/plan/ is served straight off disk, and four Mark 2 files (build.json,
    # questions.json, scenarios.json, whatsapp.json) sat in it being re-served and
    # re-stamped every cycle long after nothing generated them. This file will not
    # delete them itself — it can be pointed at another --out, it can be a --dry-run,
    # and guessing what belongs to somebody else is how a publisher eats a directory.
    # So it publishes the list and loop.sh's publish step removes anything not on it,
    # naming each deletion in the log. manifest.json lists ITSELF on purpose.
    manifest = {
        "generated_by": "live/gen_live.py",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "collected_at": stamp["collected_at"],
        "horizon": stamp["horizon"],
        "files": sorted([n for n in outputs if os.sep not in n] + ["manifest.json"]),
        "days": sorted(os.path.basename(n) for n in outputs if os.sep in n),
        "note": ("everything live/state/plan/ should hold this cycle. The publish step "
                 "deletes any other *.json there and in days/, and logs each one."),
    }
    outputs["manifest.json"] = manifest
    check("the manifest lists every file this run writes, and nothing else",
          set(manifest["files"]) == {n for n in outputs if os.sep not in n}
          and set(manifest["days"]) == {os.path.basename(n) for n in outputs if os.sep in n},
          str(sorted(manifest["files"])))

    stats = {
        "days": len(days), "working": len(working), "horizon": meta["horizon"],
        "collected_at": stamp["collected_at"], "made_l": summary["totals"]["made_l"],
        "value_rs": summary["totals"]["value"], "shipped_l": summary["totals"]["shipped_l"],
        "plan_l": round(plan_litres), "demand": demand, "runs": overview["totals"]["runs"],
        "pct_at_open": open_pct, "standing_l": opening["standing_l"],
        "zero_items": ob_summary["items_at_zero"], "late": ob_summary["already_late"],
        "chains": len(chains), "resolved": loops_out["resolved_chains"],
        "warnings": len(warnings), "no_machine": [u["code"] for u in no_machine],
        "august": honesty_out["august_calibration"], "recon": recon,
    }
    return outputs, stats


# ------------------------------------------------------------------- write ---
def write_outputs(outputs, out_dir):
    """Atomic per file — live/publish/state_server.py is serving this directory
    while we write, and half a JSON file is worse than the last whole one. The
    temp name does not end in .json, so the server refuses to serve it."""
    os.makedirs(os.path.join(out_dir, "days"), exist_ok=True)
    written = 0
    total = 0
    for name, obj in outputs.items():
        path = os.path.join(out_dir, name)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, allow_nan=False)
        os.replace(tmp, path)
        written += 1
        total += os.path.getsize(path)
    return written, total


def prune_days(outputs, out_dir):
    """Yesterday's run was one day longer. A day file past the end of THIS run
    is a day that no longer exists — drop it, or the site serves a day nobody
    planned. Only day files this script writes are ever removed."""
    keep = {os.path.basename(n) for n in outputs if n.startswith("days" + os.sep)}
    dropped = []
    for path in sorted(glob.glob(os.path.join(out_dir, "days", "day-*.json"))):
        if os.path.basename(path) not in keep:
            os.remove(path)
            dropped.append(os.path.basename(path))
    return dropped


def foreign_files(outputs, out_dir):
    """Top-level JSON in the publish directory that this script does not own —
    Mark 2 leftovers copied there by loop.sh's old publish step. Reported here and
    removed by loop.sh's publish step, which reads manifest.json: this script still
    does not delete other people's files itself, because it can be pointed at another
    --out and can be a --dry-run, and a publisher that guesses eats a directory."""
    mine = {n for n in outputs if os.sep not in n}
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(out_dir, "*.json"))
                  if os.path.basename(p) not in mine)


# -------------------------------------------------------------------- main ---
def main(argv=None):
    ap = argparse.ArgumentParser(description="site data for the live rolling re-plan")
    ap.add_argument("--tag", default="-live",
                    help="the SIM_TAG the engine ran with, with or without its dash "
                         "(default -live; write it as `--tag sep` or `--tag=-sep`, because a "
                         "bare `--tag -sep` looks like a second flag to the argument reader)")
    ap.add_argument("--out", default=DEFAULT_OUT_DIR,
                    help="where to write (default live/state/plan)")
    ap.add_argument("--dry-run", action="store_true",
                    help="run every check, write nothing")
    ap.add_argument("--no-order-by-refresh", action="store_true",
                    help="use out/order-by<tag>.json as it is, even if it is older than the inputs")
    ap.add_argument("--no-prune", action="store_true",
                    help="keep day files left over from a longer run")
    args = ap.parse_args(argv)

    tag = args.tag if args.tag.startswith("-") else "-" + args.tag
    stem = tag[1:]
    paths = {
        "inputs": os.path.join(SIM, f"{stem}-inputs.json"),
        "summary": os.path.join(SIM, f"summary{tag}.json"),
        "days_dir": os.path.join(SIM, f"days{tag}"),
        "events": os.path.join(SIM, f"events{tag}.json"),
        "order_by": os.path.join(OUT, f"order-by{stem and '-' + stem}.json"),
    }
    for key in ("inputs", "summary", "events"):
        if not os.path.exists(paths[key]):
            raise SystemExit(f"gen_live.py: {paths[key]} is not there — run the engine first "
                             f"(SIM_INPUTS={paths['inputs']} SIM_TAG={tag} python3 engine/august_sim.py)")
    if not glob.glob(os.path.join(paths["days_dir"], "day-*.json")):
        raise SystemExit(f"gen_live.py: no day files in {paths['days_dir']}")
    paths["today"] = load(paths["inputs"])["meta"]["horizon"][0]

    check = Checks()
    ob_state, paths["order_by_read"], ob_pending = ensure_order_by(
        paths, refresh=not args.no_order_by_refresh)
    # A NaN or a None reaching round() used to come out of here as a bare traceback.
    # That is the wrong ending for the same event: the run is REFUSED, the published
    # plan is untouched, and the operator needs the sentence that says so — not a stack
    # trace that reads like the loop itself died. It is a failed check like any other,
    # and it leaves through the same door.
    outputs, stats = {}, None
    try:
        outputs, stats = build(paths, check)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError, KeyError) as exc:
        detail = f"{type(exc).__name__}: {exc}"
        if "nan" in str(exc).lower():
            detail += ("  <- a NaN reached a rounding step: the freeze published a number "
                       "that is not a number, and no plan is written on top of one")
        check("the plan builds without an arithmetic fault", False, detail)
        print("".join(traceback.format_exception_only(type(exc), exc)).strip(), file=sys.stderr)
        print("  at " + " <- ".join(
            f"{os.path.basename(fr.filename)}:{fr.lineno} {fr.name}"
            for fr in reversed(traceback.extract_tb(exc.__traceback__)[-4:])), file=sys.stderr)

    if check.failed:
        # Nothing this run produced survives it — not the plan files, and not the gap
        # list, which is still sitting under its temp name and is thrown away here.
        drop_order_by(ob_pending)
        print(f"\n{len(check.failed)} CHECK(S) FAILED — NOT WRITING. "
              f"{args.out} keeps its last good copy, and out/order-by{tag}.json keeps "
              f"the last one that passed.", file=sys.stderr)
        for name, _ok, detail in check.failed:
            print(f"    FAILED: {name} {detail}", file=sys.stderr)
        return 1

    if args.dry_run:
        drop_order_by(ob_pending)                 # a dry run writes NOTHING, gap list included
        written, total, dropped = len(outputs), 0, []
        headline = f"gen_live.py — DRY RUN, every check passed, NOTHING written to {args.out}"
        files_line = f"  files: {written} would be written · gap list: {ob_state} (thrown away)"
    else:
        written, total = write_outputs(outputs, args.out)
        dropped = [] if args.no_prune else prune_days(outputs, args.out)
        committed = commit_order_by(ob_pending)
        headline = f"gen_live.py — live rolling re-plan written to {args.out}"
        files_line = (f"  files: {written} ({total / 1024:.0f} KB) · gap list: {ob_state}"
                      + (" -> " + ", ".join(committed) if committed else ""))

    demand = stats["demand"]
    aug = stats["august"]
    print(headline)
    print(files_line)
    print(f"  as of {stats['collected_at']} · {stats['horizon'][0]} → {stats['horizon'][1]}"
          f" · {stats['days']} days left ({stats['working']} working)")
    print(f"  made {stats['made_l']:,} L · value Rs {stats['value_rs'] / 1e7:.2f} Cr"
          f" · billed {stats['shipped_l']:,} L · runs {stats['runs']}")
    print(f"  target {stats['plan_l']:,} L · demand rows {demand['rows']} "
          f"(confirmed {demand['real_rows']} / expected {demand['forecast_rows']}) · "
          f"expected share {demand['forecast_share_litres_pct']}% by litres")
    print(f"  godown at open {stats['pct_at_open']}% · billed-not-gone {stats['standing_l']:,} L")
    print("  day 1 against the live count: " + " · ".join(
        f"{k} {v['shown']:,} = {v['expected']:,} ({v['delta_l']:+d} L)"
        for k, v in stats["recon"].items()))
    print(f"  nothing in stock and nothing on order: {stats['zero_items']} items · "
          f"already late to order: {stats['late']}")
    print(f"  stuck-item chains {stats['resolved']}/{stats['chains']} clear inside this run")
    print(f"  no machine for: {', '.join(stats['no_machine']) or 'none'}")
    print(f"  August check: plan {aug['sim_made_l']:,} L vs actual {aug['actual_made_l']:,} L "
          f"({aug['delta_pct']}%)")
    print(f"  checks: {len(check.passed)}/{len(check.rows)} passed")
    if stats["warnings"]:
        print(f"  {stats['warnings']} warning(s) carried from the freeze into honesty.json")
    if dropped:
        print(f"  dropped {len(dropped)} day file(s) left over from a longer run: {', '.join(dropped)}")
    strays = foreign_files(outputs, args.out)
    if strays:
        print(f"  !! {len(strays)} file(s) in {args.out} are NOT from this run: "
              f"{', '.join(strays)} — they are not in manifest.json, so the publish step "
              f"removes them and logs each one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
