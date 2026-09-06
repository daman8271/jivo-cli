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
    assumptions.json — MARK 4 ONLY, when the freeze carried reference/mark4-rulebook.json
                       inside the inputs. Every settled ruling, every guess with what
                       would change it, every choice made while building it, the speed
                       table, the eligibility matrix, how fresh each input is, the
                       acceptance list with a pass flag, and the open questions for
                       Gurvinder with a status read out of the file he answers into.
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
import copy
import glob
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import traceback
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))          # .../jolly/live
JOLLY = os.path.dirname(HERE)                              # .../jolly
SIM = os.path.join(JOLLY, "sim")
OUT = os.path.join(JOLLY, "out")
REFERENCE = os.path.join(JOLLY, "reference")
DEFAULT_OUT_DIR = os.path.join(HERE, "state", "plan")

# The one masker, not a second copy of it. The open questions come out of a markdown
# file a person edits by hand, and question 14 asks for WhatsApp numbers — so the
# answers will one day carry one. It is masked on the way into assumptions.json by
# the same code that masks the live feed (live/adapters/_mask.py), and THEN the
# phone scan runs over the file like every other. Masking at the door is not
# weakening the scan; it is what the scan is there to catch when it is missed.
if JOLLY not in sys.path:
    sys.path.insert(0, JOLLY)
from live.adapters._mask import MASK, mask_phones, scan_phones   # noqa: E402

# WHICH FILES THIS SCRIPT OWNS IN THE PUBLISH DIRECTORY is not a constant any more.
# It was one (`OWNED`), and nothing read it — the list that matters is manifest.json,
# built at the end of build() from what the run actually produced, which is how
# assumptions.json can be there in rulebook mode and absent on the -sep path without
# a second list to keep in step. loop.sh's publish step deletes anything not on the
# manifest and logs each one.

# The acceptance lines this file cannot finish, and who does. AC11's other three
# clauses and the whole of AC12 are the site's build and the chain end to end, so
# neither gets a verdict here — see the acceptance list at the end of build().
CHECKED_ELSEWHERE = {
    "AC11": "the site's own build — `npm run build` and `npm run check:numbers`",
    "AC12": "running the whole chain end to end on the committed fixtures",
}

# ...and the acceptance lines this file checks only PART of, clause by clause. AC10 is
# one sentence with FOUR clauses joined by semicolons, and two of them are not this
# file's to pass: `/assumptions` renders them is the site's build, and `check:numbers`
# is the site's own scan over app/ and components/. It was publishing
# `checked_here: true, passed: true` across all four — the same shape AC11 was fixed
# out of, one line further down the list. The clause text below must be a substring of
# the rulebook's own sentence; a clause that stops matching is caught by a check.
# {ac: {phrase in the clause: (is the WHOLE clause elsewhere?, who does it)}}
CHECKED_ELSEWHERE_CLAUSES = {
    "AC10": {
        "the site's /assumptions renders them": (
            True, "the site's own build — `npm run build` renders /assumptions from this file"),
        # this clause is two checks in one sentence: the phone-mask scan below IS this
        # file's and it runs over every file it is about to write; `check:numbers` is
        # the site's own scan over app/ and components/ and this file never sees it.
        "check:numbers": (
            False, "half this file's: the phone-mask scan runs here over every file this "
                   "run writes, and `check:numbers` is the site's own scan over app/ and "
                   "components/"),
    },
}

# B20 — the binder code engine/august_sim.py writes on a held-up row when the GODOWN
# is what stopped the product, not a bottle. Kept in step with STORAGE_BINDER there.
STORAGE_BINDER = "STORAGE"


def split_clauses(text):
    """An acceptance line, clause by clause. They are written as one sentence joined by
    semicolons, and a verdict has to be able to point at the clause it is about."""
    body = text[5:] if text[:2] == "AC" else text
    return [c.strip() for c in body.split(";") if c.strip()]


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ----------------------------------------------------- the August calibration ---
# The site's one trust sentence rests on a single number, and it used to be read
# straight out of sim/summary.json — a WORKING FILE that a bare
# `python3 engine/august_sim.py` overwrites. It had drifted: the committed summary
# said 2,122,639 L (0.16%) while the committed engine on the committed inputs made
# 2,124,866 L (0.27%), and none of the checks looked. So the claim is now an
# artefact with the sha256 of every file it depends on, written by
# engine/calibrate_august.py. If the tree has moved since it was measured the
# number is still published — the site does not go dark over this — but it is
# published as NOT reproducible, with the file that moved named.
CALIBRATION = os.path.join(REFERENCE, "august-calibration.json")


def august_calibration():
    """(figures, [warning, ...]). Never raises: a missing or stale artefact is a
    thing to say out loud, not a reason to refuse the whole re-plan."""
    if not os.path.exists(CALIBRATION):
        return None, ["The August calibration has not been measured on this checkout — "
                      "run `python3 engine/calibrate_august.py`. The site says so instead "
                      "of showing a number nobody re-measured."]
    art = load(CALIBRATION)
    moved = []
    for rel, was in (art.get("depends_on") or {}).items():
        p = os.path.join(JOLLY, rel)
        if not os.path.exists(p):
            moved.append(rel)
            continue
        with open(p, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != was:
                moved.append(rel)
    warn = []
    if moved:
        warn.append("The August calibration was measured against a different %s — re-measure it with "
                    "`python3 engine/calibrate_august.py` before quoting it."
                    % (", ".join(sorted(moved))))
    art["reproducible"] = not moved
    art["changed_since_measured"] = sorted(moved)
    return art, warn


# ------------------------------------------------------------------ checks ---
class Checks:
    """Same contract as gen-data.py's: collect, print failures, gate the write."""

    def __init__(self):
        self.rows = []
        # which acceptance check (AC01..AC12) a row is enforcing, so plan/assumptions.json
        # can publish the list with a pass flag per item instead of a promise.
        self.by_ac = defaultdict(list)

    def __call__(self, name, ok, detail="", ac=None):
        self.rows.append((name, bool(ok), str(detail)))
        for one in ([ac] if isinstance(ac, str) else list(ac or ())):
            self.by_ac[one].append(bool(ok))
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
    """Three nets over one file, and the third one is the masker's own.

    The first two only know the numbers already in `inp["people"]` and a literal
    `+91` — which is how `Ravi.9876543210` reached a published assumptions.json
    with 274/274 green (round B, item 19). `_mask.scan_phones` is the guard half
    of the module that masks the live feed, so what it calls a phone number and
    what the masker masks can never drift apart. Masking at the door is not a
    reason to skip it: this is what catches the door that was missed.
    """
    blob = json.dumps(obj, ensure_ascii=False)
    flat = re.sub(r"\D", "", blob)
    for d10 in RAW_NUMBERS:
        if d10 in flat and d10 in blob.replace(" ", "").replace("-", ""):
            return check(f"phone-scan {name}", False, f"raw number ...{d10[-4:]} leaked")
    if re.search(r"\+91[\s-]?\d{3}", blob):
        return check(f"phone-scan {name}", False, "un-masked +91 pattern present")
    shaped = scan_phones(obj)
    if shaped:
        return check(f"phone-scan {name}", False,
                     "mobile-shaped run at " + ", ".join(p for p, _v in shaped[:3]))
    return check(f"phone-scan {name}", True)


# --------------------------------------------- the questions file, in particular
# The open questions come out of a markdown file GURVINDER edits by hand on an
# iPad, and question 14 asks him for WhatsApp numbers. `_mask` is tuned for the
# live feed, where a ten-digit run is often a PO or a GRPO number and must
# survive; this document has NO legitimate ten-digit identifier in it, so here the
# net is wider on purpose: any run of ten or more digits is masked, whatever it
# starts with and however he spaced it.
#
# A DATE IS NOT A LONG NUMBER. "2026-09-15 14:30" is thirteen digits once the
# separators are allowed, and a plan that refuses to publish because he answered
# with a date would take the site dark on a three-minute loop. Dates and
# date-times are blanked to their own length before the net runs, so offsets into
# the real string still line up and only what is left is masked.
_LONG_DIGITS_RE = re.compile(r"(?<!\d)\d(?:[\s.\-]?\d){9,}(?!\d)")
_DATE_TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?")


def _dateless(text):
    return _DATE_TIME_RE.sub(lambda m: "#" * len(m.group(0)), text)


def find_long_digit_runs(text):
    """Every run of 10+ digits that is not part of a date, as match objects."""
    return list(_LONG_DIGITS_RE.finditer(_dateless(text)))


def mask_long_digit_runs(text):
    """`text` with every such run replaced by •••• and its last two digits."""
    out, at = [], 0
    for m in find_long_digit_runs(text):
        out.append(text[at:m.start()])
        out.append(MASK + re.sub(r"\D", "", text[m.start():m.end()])[-2:])
        at = m.end()
    out.append(text[at:])
    return "".join(out)


def mask_questions(questions):
    """The parsed questions, with the live masker run over them AND every other
    long digit run masked. Numbers (the question number) are left alone."""
    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str):
            return mask_long_digit_runs(node)
        return node
    return walk(mask_phones(copy.deepcopy(questions)))


def question_digit_leaks(questions):
    """[(path, what)] — a phone number or a long digit run still on the page."""
    leaks = [(path, value) for path, value in scan_phones(questions)]
    for i, q in enumerate(questions or []):
        for key, value in (q or {}).items():
            if not isinstance(value, str):
                continue
            for m in find_long_digit_runs(value):
                leaks.append((f"open_questions[{i}].{key}", m.group(0)))
    return leaks


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


# THE LIVE DISPATCH AND BOOKING READS, in the two files that carry them. Each of
# these is honestly null on a box whose records start today or on a cycle where the
# read failed, and none of them is a figure the front page refuses without (the
# rupee ones are, and they are checked by name in check_overview).
#
# Scoped to those two files ON PURPOSE (round B, items 25 and 29). Two things went
# wrong with one global set: `pendency_days_*` became null-permitted in EVERY file,
# including history.json and the day files where a null is a fault; and
# `today_booked_pieces` was left out of it while `pieces_booked_today` — the same
# number, from the same read, in the same file — was allowed, so a failed
# factory-history read took the whole site dark (rc=1) over a figure nothing needs.
# The `lag_median_days is None` branch in the dispatch headline was unreachable for
# the same reason: the scan refused the file before the sentence could be read.
DISPATCH_NULL_OK = {
    # Days of work in the open dispatch book, at the pace the gate really kept. The
    # divisor is the last few RECORDED days off ji.jivo.in, and on a box whose
    # records start today there is no recorded day yet. Null with the reason beside
    # it is the honest answer; a zero would read as "the book is empty" and a made-up
    # divisor would read as a measurement.
    "pendency_days_all",
    "pendency_days_oil",
    # How long a bill waits for a gate: measured daily off the gate log, and absent
    # until the daily job has run once. gen writes a different headline when it is.
    "lag_median_days",
    "lag_p90_days",
    # The pieces behind today's booked rupees. freeze_live.py always computes the
    # rupees; the piece count comes straight off the factory read and can be missing.
    "today_booked_pieces",
}


# history.json is the one file where a null quantity is the POINT: a day the
# plant's systems did not answer for must read UNKNOWN, and a zero would say the
# plant did nothing. These keys are allowed to be null in that file ONLY — the
# plan files keep the strict global set above, where a null litre is a fault.
HISTORY_NULL_OK = {
    "made_mes_l", "made_mes_cases", "runs", "open_segments",
    "made_booked_l", "made_booked_pcs", "booked_receipts", "booked_unparsed_pcs",
    "billed_out_l", "billed_out_pcs", "billed_lines", "billed_unparsed_pcs",
    "dispatched_oil_l", "dispatched_all_l", "trucks_oil", "trucks_all",
    "rows_oil", "bills_oil",
}


def scan_numbers(check, name, obj, null_ok=None):
    bad = []
    allowed = NULL_OK | set(null_ok or ())

    def walk(node, path):
        if len(bad) >= 6:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                here = f"{path}.{key}" if path else key
                if value is None and key not in allowed and _QTY_KEY.search(key):
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


# ================================================================== MARK 4 ===
# THE RULEBOOK IS THE SWITCH. reference/mark4-rulebook.json rides inside the inputs
# as `rulebook` (the freeze embeds it verbatim), and everything below runs only when
# it is there. With no rulebook this file behaves exactly as it did in Mark 3 — the
# -sep path, the legacy basis words and the derived 15 L slot are all untouched.
#
# What changes when it IS there:
#   * what a machine may fill comes from rulebook.lines[line].slots[slot][family],
#     the same table engine/august_sim.py schedules from — never from a slot-key
#     guess. Mark 3 asked "is there a TIN key in `lines`?", and Mark 4 keys the Tin
#     Head 15L/3L/5L, so the old question answered "no machine fills a tin" about
#     four products the plant filled that day.
#   * the speed table is published with the rulebook's own basis words, and gen
#     RECOMPUTES `planning` from the structured planning_rule (AC05) rather than
#     believing the number beside the prose.
#   * gen never derives a 15 L speed from the 5 L slot (AC02): the rulebook names
#     every slot a line has, and 15 L is a tin on the Tin Head.
#   * the acceptance list AC01-AC10 is enforced as refusing cross-checks, exactly
#     like every other check here — a failure writes nothing at all.
RULEBOOK_FILE = os.path.join(REFERENCE, "mark4-rulebook.json")

# The Mark 4 words for where a planning speed came from, published per line-slot.
# The site renders the word, so a word nobody defined must not reach it — the check
# is on this set plus the legacy one, which is a vocabulary, not a strictness.
RULEBOOK_BASIS_WORDS = {"capped", "rated", "typical", "carried", "derived"}
LEGACY_BASIS_WORDS = {"observed", "rated", "derived", "carried"}


def rulebook_on_disk():
    """The rulebook this checkout carries, for the version cross-check. Never raises:
    a missing or broken file is a failed check with a sentence, not a traceback."""
    try:
        return load(RULEBOOK_FILE)
    except (OSError, ValueError):
        return None


def rb_rate(lines_cfg, lines_multi, line, slot, fills=1):
    """Containers an hour for this pack on this line, or None when nobody has a speed
    for it. Mirrors engine/august_sim.py rb_rate(): a SKU that fills more than one
    container per piece takes its speed from the multi table, never the plain one."""
    table = (lines_multi if (fills or 1) > 1 else lines_cfg).get(line) or {}
    return table.get(slot)


def eligible_lines(rb, lines_cfg, lines_multi, slot, family, fills=1):
    """{line: preference} — every machine the rulebook lets this pack and bottle run
    on, and how much it wants to. This is engine/august_sim.py rb_pref() reading the
    same table, so gen and the planner cannot disagree about what has a machine.

    A line needs BOTH halves: the rulebook must name the bottle family (or ANY) in
    that slot, AND there must be a planning speed for it. A slot nobody has a speed
    for is not a machine that can fill it (B16) — Clear Pack 2 L and 6 Head 3 L are
    both in that state today and are published as such rather than scheduled.
    """
    out = {}
    for line, spec in (rb.get("lines") or {}).items():
        fams = ((spec.get("slots") or {}).get(slot)) or {}
        pref = fams.get(family, fams.get("ANY"))
        if pref is None or rb_rate(lines_cfg, lines_multi, line, slot, fills) is None:
            continue
        out[line] = pref
    return out


def recompute_planning(rule, planning_by_slot=None):
    """`planning` worked out again from planning_rule alone — AC05.

    The rulebook publishes both the sentence (planning_basis) and the same thing as
    data (planning_rule), so this can be an arithmetic check instead of a prose
    match. One branch per kind, and they are the branches in
    reference/build_mark4_rulebook.py speed_block():

        capped   min(factor x rated, the best August run of 3 h+)
        rated    factor x rated
        typical  the median August run of 3 h+ (no factor: a typical run already
                 carries the inefficiency)
        carried  factor x the Mark 3 carried table
        derived  the planning speed of another line-slot, unchanged
        none     no speed at all — nothing may be scheduled on that slot

    `planning_by_slot` is {(line, slot): planning} for the derived branch.
    Returns None when the rule cannot be worked out, which the caller reads as
    "cannot be re-checked" and refuses.
    """
    rule = rule or {}
    kind = rule.get("kind")
    factor, rated, best = rule.get("factor"), rule.get("rated"), rule.get("best")
    if kind == "capped":
        if factor is None or rated is None or best is None:
            return None
        return min(factor * rated, best)
    if kind == "rated":
        return None if (factor is None or rated is None) else factor * rated
    if kind == "typical":
        return rule.get("median_sustained")
    if kind == "carried":
        carried = rule.get("carried_from")
        return None if (factor is None or carried is None) else factor * carried
    if kind == "derived":
        src = rule.get("derived_from") or []
        return (planning_by_slot or {}).get(tuple(src)) if len(src) == 2 else None
    return None                                  # kind "none": no speed exists


# ------------------------------------------------- the questions for Gurvinder
# He answers by editing the markdown and pushing it back, so the file is the
# channel and the parser has to survive whatever prose he adds. It looks for two
# things only: a `**N. Title**` heading, and a line under it starting `Answer:`.
# The convention is written at the top of the file itself so nobody has to know it
# from here.
QUESTION_RE = re.compile(r"^\*\*(\d+)\.\s*(.*?)\*\*(.*)$")
ANSWER_RE = re.compile(r"^(\*\*)?answer\b", re.IGNORECASE)
# He is answering in prose on an iPad, in a markdown file, and three shapes that
# obviously ARE an answer used to read as "open" (round B, item 27): on the heading
# line itself, quoted with `>`, and as a bullet — and the bullet is the one that
# matters, because the file's own "already settled" section is written in bullets,
# so that is the shape in front of him. Everything a markdown editor puts in front
# of the word is stripped before the word is looked for.
_ANSWER_LEAD = "> \t-*+•"
# The floor, declared in the file he edits, read back here. See AC10 below.
QUESTION_FLOOR_RE = re.compile(r"<!--\s*questions:\s*(\d+)\b")


def parse_questions(text):
    """[{number, section, title, question, status, answer}] — open questions, in order.

    A question runs from its heading to the next heading or the next `## ` section.
    Status is `answered` the moment a line in its body starts with `Answer:` (or
    `**Answer`, `> Answer`, `- Answer`, or the same word on the heading line),
    because that is how the answer arrives — there is no second system to look in.
    Everything is copied verbatim; nothing here is authored.
    """
    def answer_of(line):
        probe = line.strip().lstrip(_ANSWER_LEAD).strip()
        return probe if ANSWER_RE.match(probe) else None

    section, rows, cur = None, [], None
    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            section, cur = line[3:].strip(), None
            continue
        match = QUESTION_RE.match(line)
        if match:
            tail = match.group(3).strip()
            cur = {"number": int(match.group(1)), "section": section,
                   "title": match.group(2).strip().rstrip(".").strip(),
                   "body": [t for t in [tail] if t], "answers": []}
            on_the_heading = answer_of(tail)
            if on_the_heading:
                cur["answers"].append(on_the_heading)
            rows.append(cur)
            continue
        if cur is None:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        answer = answer_of(stripped)
        if answer:
            cur["answers"].append(answer)
        cur["body"].append(stripped)
    return [{"number": q["number"], "section": q["section"], "title": q["title"],
             "question": "\n".join(q["body"]).strip(),
             "status": "answered" if q["answers"] else "open",
             "answer": "\n".join(q["answers"]).strip() or None}
            for q in rows]


# A NET THAT IS WIDER THAN THE PARSER, ON PURPOSE (round B, item 23). The old
# counter keyed on `^\*\*(\d+)\.` — the parser's own shape — so anything that broke
# the shape dropped the question out of BOTH and the two agreed on 13. Measured:
# bold broken on question 14, a stray leading space, or bullet form each gave
# parser 13, headings 13, check passed, and question 14 — the one that asks for
# WhatsApp numbers — was gone with rc=0. This one accepts a bullet, an indent, a
# single asterisk or none at all, so a heading the parser cannot read is still
# COUNTED, and the difference is what refuses the run.
WIDE_HEADING_RE = re.compile(r"^\s{0,3}(?:[-*+]\s+)?\*{0,2}(\d{1,2})\.(?:\s|\*|$)",
                             re.MULTILINE)


def count_question_headings(text):
    """How many `**N.` headings the file really has, read with a WIDER net than the
    parser uses, so a question the parser silently swallowed refuses the run."""
    return len(WIDE_HEADING_RE.findall(text or ""))


def heading_numbers(text):
    """The numbers that wider net found, in order."""
    return [int(n) for n in WIDE_HEADING_RE.findall(text or "")]


def question_floor(text):
    """The number of questions the file itself declares it has, or None.

    It is a floor, not an equality: adding a question must never take the site
    dark, losing one must. The rulebook would be the better home for it, but the
    rulebook is generated by reference/build_mark4_rulebook.py and this round does
    not touch that file — so it is declared in the document it guards, in a comment
    a markdown reader never shows.
    """
    found = QUESTION_FLOOR_RE.search(text or "")
    return int(found.group(1)) if found else None


# ------------------------------------------------------- AC01-AC10, as checks
# Every one of these is a REFUSING cross-check with the same contract as the rest of
# this file: it takes the `check` collector, and a failure means nothing is written.
# They are separate functions so live/_gen_mark4_test.py can put a passing and a
# failing dict through each one without running the whole chain.

def check_engine_gates(check, rb, summary_rulebook, disk_version):
    """The planner's own report on the run, read as a gate rather than as a note.

    Each of these is the engine saying "I could not place this the way the rulebook
    says" — a plan built over one of them is a plan with a hole in it, and the site
    would show it as if it were whole.
    """
    srb = summary_rulebook or {}
    check("the plan was made with the rulebook in effect", srb.get("applied") is True,
          f"summary says applied={srb.get('applied')}", ac="AC11")
    check("the plan was built on the rulebook this checkout carries",
          bool(disk_version) and srb.get("version") == disk_version
          and (rb or {}).get("version") == disk_version,
          f"the plan was built on {srb.get('version')} / the freeze carried "
          f"{(rb or {}).get('version')} and this checkout carries {disk_version} — "
          f"the next freeze fixes it", ac="AC11")
    check("every product in the month's target is one the recipe knows",
          not srb.get("unmapped_codes"), str((srb.get("unmapped_codes") or [])[:6]),
          ac="AC06")
    check("every product the plan must make has a machine that can fill it",
          not srb.get("no_line_skus"), str((srb.get("no_line_skus") or [])[:6]), ac="AC03")
    check("every set-of-two product has a speed for filling it as a set",
          not srb.get("multi_fill_no_rate"), str((srb.get("multi_fill_no_rate") or [])[:6]),
          ac="AC05")
    check("the machines are planned at their planning speed and nothing is slowed twice",
          srb.get("efficiency_applied") == 1.0,
          f"the planner ran at {srb.get('efficiency_applied')} — the planning speeds "
          f"already carry the factory's own pace", ac="AC05")
    check("nobody stretched the shift by hand on this run",
          srb.get("hours_override") is None,
          f"hours were overridden to {srb.get('hours_override')}", ac="AC04")
    check("the past-sales figure the plan ranks by says where it came from",
          bool(srb.get("trailing_source")), str(srb.get("trailing_source")), ac="AC08")
    check("every product the plan ranks by past sales has one",
          not srb.get("no_trailing_codes"), str((srb.get("no_trailing_codes") or [])[:6]),
          ac="AC08")


def run_faults(rb, lines_cfg, lines_multi, days, sku_pack):
    """{rule: [where, ...]} — every scheduled run measured against the rulebook.

    Two layers on purpose. The TABLE layer asks the rulebook's own eligibility map
    (so gen and the engine read one source), and the NAMED layer restates the
    meeting's rulings literally — 15 L is a tin, a tin runs on the Tin Head, no 3 L
    on Clear Pack, pouches only on the pouch machine, drums never. If someone edits
    the table, the named layer still refuses; if someone adds a machine, the table
    layer still refuses. Neither can quietly allow what the other forbids.
    """
    drum_codes = set((rb.get("drums") or {}).get("skus") or [])
    faults = defaultdict(list)
    for day in days:
        for run in day.get("runs") or []:
            line, code = run.get("line"), run.get("code")
            where = f"{day.get('date')} {line} {code}"
            pack = sku_pack.get(code) or {}
            slot = run.get("slot", pack.get("slot"))
            family = run.get("family", pack.get("family"))
            fills = int(pack.get("fills_per_piece") or run.get("fills") or 1)
            prefs = eligible_lines(rb, lines_cfg, lines_multi, slot, family, fills)
            if line not in prefs:
                faults["off the table"].append(f"{where} {slot}/{family}")
            elif run.get("pref") is not None and run["pref"] != prefs[line]:
                faults["wrong preference"].append(
                    f"{where} says {run['pref']}, the rulebook says {prefs[line]}")
            if family == "TIN" and not (line == "Tin Head"
                                        or (line == "6 Head" and slot in ("3L", "5L"))):
                faults["a tin off the Tin Head"].append(f"{where} {slot}")
            if slot == "15L" and line != "Tin Head":
                faults["15 litres off the Tin Head"].append(where)
            if slot == "3L" and line == "Clear Pack":
                faults["3 litres on Clear Pack"].append(where)
            if slot == "POUCH" and line != "Pouch Machine":
                faults["a pouch off the pouch machine"].append(where)
            if slot == "DRUM" or code in drum_codes:
                faults["a drum on a machine"].append(where)
            if line == "JP Machine" and slot == "1L" and family not in (
                    "26G", "ROUND-23.8G", "SMALL", "52G"):
                faults["a bottle JP does not run"].append(f"{where} {family}")
            if line == "Clear Pack" and family in ("75G", "26G", "ROUND-23.8G"):
                faults["a bottle Clear Pack does not run"].append(f"{where} {family}")
            if line == "JP Machine" and family in ("40G", "75G"):
                faults["a bottle JP does not run"].append(f"{where} {family}")
    return {k: v for k, v in faults.items() if v}


def check_runs(check, rb, lines_cfg, lines_multi, days, sku_pack):
    """AC01, AC02, AC03, AC07 — what ran, where."""
    faults = run_faults(rb, lines_cfg, lines_multi, days, sku_pack)

    def one(name, keys, ac):
        hits = [w for k in keys for w in faults.get(k, [])]
        check(name, not hits, str(hits[:4]), ac=ac)

    one("every tin was filled on a tin machine",
        ["a tin off the Tin Head", "15 litres off the Tin Head"], "AC01")
    one("nothing ran on a machine that cannot fill it",
        ["3 litres on Clear Pack", "a pouch off the pouch machine",
         "15 litres off the Tin Head"], "AC02")
    one("no drum was ever put on a machine", ["a drum on a machine"], "AC03")
    one("every run used a bottle its machine handles",
        ["a bottle JP does not run", "a bottle Clear Pack does not run"], "AC07")
    one("every run is one the rulebook allows, at the choice it names",
        ["off the table", "wrong preference"], ["AC01", "AC02", "AC07"])


def check_hours_and_nights(check, days, hours_per_session, sundays_off=True):
    """AC04 — 10 hours a machine, one machine to 20, no Sunday, and the night machine
    named every day with the reason it was picked.

    TWO OF THESE STOPPED BEING CHECKS WHEN THE DATA MOVED (round B, item 20), which
    is the failure mode a check exists to prevent:

      * `if line in cap` — delete `line_hours_max` from the day files and the
        hours-it-had test became a loop over nothing. Measured: rc=0, everything
        green, /assumptions telling Gurvinder AC04 passed, and the front page
        showing no hours at all for any of the six machines. So the cap is now
        REQUIRED to be there and to cover every machine that ran.
      * `sundays_off` was read out of the freeze. Set it to False and the Sunday
        half of AC04 simply vanished, still green. R04 ("Sunday closed. Sunday is
        for dispatch.") is a settled ruling, not a knob this file defers to — so
        the flag being off is itself a refusal, and the loop below still uses it
        so the failure names both things at once.
    """
    over, over_night, unnamed, sunday, mismatch, uncapped = [], [], [], [], [], []
    for day in days:
        night = day.get("night_line") or {}
        night_line = night.get("line")
        if not isinstance(day.get("night_line"), dict) or not night.get("reason"):
            unnamed.append(day.get("date"))
        hours = day.get("line_hours") or {}
        cap = day.get("line_hours_max")
        if not isinstance(cap, dict):
            uncapped.append(f"{day.get('date')} has no line_hours_max at all")
            cap = {}
        for line, ran in hours.items():
            limit = hours_per_session * (2 if line == night_line else 1)
            if ran > limit + 0.05:
                (over_night if line == night_line else over).append(
                    f"{day.get('date')} {line} {ran} h")
            if not isinstance(cap.get(line), (int, float)):
                uncapped.append(f"{day.get('date')} {line} ran {ran} h against no limit")
            elif ran > cap[line] + 0.05:
                mismatch.append(f"{day.get('date')} {line} {ran} h of {cap[line]} h")
        if sundays_off and day.get("weekday") == "Sunday":
            if (day.get("made_litres") or 0) > 0 or any(v > 0 for v in hours.values()) \
                    or (day.get("runs") or []):
                sunday.append(day.get("date"))
    check("no machine runs longer than a full shift", not over, str(over[:4]), ac="AC04")
    check("the one machine that runs at night stops at two shifts",
          not over_night, str(over_night[:4]), ac="AC04")
    check("every day says how many hours each machine had", not uncapped,
          str(uncapped[:4]), ac="AC04")
    check("no machine runs longer than the hours it had that day",
          not mismatch, str(mismatch[:4]), ac="AC04")
    check("every day says which machine runs at night, and why",
          not unnamed, str(unnamed[:4]), ac="AC04")
    check("the plan was built with Sunday closed", sundays_off is True,
          "the freeze says Sundays are worked — R04 says they are not", ac="AC04")
    check("nothing is filled on a Sunday", not sunday, str(sunday[:4]), ac="AC04")


def check_pack_class(check, rb, plan):
    """AC06 — the pack of every product comes from its recipe, and the eight the
    plan sheet calls plastic are tins."""
    sku_pack = rb.get("sku_pack") or {}
    slots = set((rb.get("pack_class") or {}).get("slots") or [])
    missing = [p["code"] for p in plan if p["code"] not in sku_pack]
    check("every product in the month's target says which container it fills",
          not missing, str(missing[:6]), ac="AC06")
    bad_slot = [c for c, v in sku_pack.items() if v.get("slot") not in slots]
    check("every container is one of the sizes the machines know",
          not bad_slot, str(bad_slot[:6]), ac="AC06")
    disagree = sorted(c for c, v in sku_pack.items() if v.get("sheet_disagrees"))
    not_tin = [c for c in disagree if sku_pack[c].get("family") != "TIN"]
    check("where the sheet and the recipe disagree, the recipe says tin",
          bool(disagree) and not not_tin,
          f"{len(disagree)} disagree, {not_tin[:4]} are not tins", ac="AC06")
    # AC06 does not just say "some rows disagree", it says WHICH: the 15-litre rows
    # plus one named 5-litre one. Non-empty was the whole test, so seven of them could
    # go quiet and it still passed. The shape is read out of the acceptance line
    # itself — nothing here is typed, and a reworded line refuses loudly instead of
    # checking nothing.
    ac06 = next((t for t in (rb.get("acceptance_checks") or []) if t.startswith("AC06")), "")
    named = {code for code in sku_pack if code and code in ac06}
    count = re.search(r"(\d+)\s*['\u2018\u2019\"]?15 LTR", ac06)
    if named and count:
        want = int(count.group(1)) + len(named)
        check("the products the sheet calls plastic and the recipe calls tin are the ones "
              "the acceptance list names",
              len(disagree) == want and named <= set(disagree),
              f"{len(disagree)} disagree against {want}; missing {sorted(named - set(disagree))}",
              ac="AC06")
    else:
        check("the acceptance list still says which products the sheet gets wrong",
              False, f"AC06 does not name them any more: {ac06[:80]}", ac="AC06")


def check_planning_speeds(check, rows, planning_factor=None):
    """AC05 — every published speed worked out again from its own rule, and every
    rule that multiplies by the plant's factor multiplies by THE factor.

    `planning_factor` used to be passed in and never read, so a speed rule carrying
    0.9 while the page said the plant plans at 80% would have gone out unremarked."""
    by_slot = {(r["line"], r["slot"]): r["planning"] for r in rows if not r.get("multi")}
    bad, unknown = [], []
    for row in rows:
        again = recompute_planning(row.get("planning_rule"), by_slot)
        if again is None:
            unknown.append(f"{row['line']} {row['slot']} "
                           f"({(row.get('planning_rule') or {}).get('kind')})")
        elif abs(again - (row.get("planning") or 0)) > 1:
            bad.append(f"{row['line']} {row['slot']} says {row.get('planning')}, "
                       f"the rule works out to {round(again, 1)}")
    check("every machine speed is the rule it says it followed", not bad, str(bad[:4]),
          ac="AC05")
    check("every machine speed on the plan can be worked out again", not unknown,
          str(unknown[:4]), ac="AC05")
    if planning_factor is not None:
        off = [f"{r['line']} {r['slot']} multiplies by "
               f"{(r.get('planning_rule') or {}).get('factor')}"
               for r in rows
               if (r.get("planning_rule") or {}).get("factor") is not None
               and abs(r["planning_rule"]["factor"] - planning_factor) > 1e-9]
        check("every machine speed that takes a share of its listed speed takes the same "
              "share", not off, f"the plan says {planning_factor}: {off[:4]}", ac="AC05")
    words = {r["rate_basis"] for r in rows}
    # NOT THE SAME CHECK as the one over the whole lines.json further down, which is
    # strict per mode; this one is the union, because it is driven with hand-built
    # rows that do not know which mode they are in. Two checks with one name are two
    # checks nobody can tell apart in a failure.
    check("every machine speed on this table says where it came from, in a word the "
          "site knows", words <= (RULEBOOK_BASIS_WORDS | LEGACY_BASIS_WORDS),
          str(sorted(words)), ac="AC05")


def check_demand_baseline(check, rb, baseline, assumed, expected_used):
    """AC08 — where the expected orders came from, published with its own arithmetic."""
    baseline = baseline or {}
    want_months = ((rb.get("demand") or {}).get("months"))
    if baseline.get("present") and baseline.get("used_for_forecast"):
        check("the expected orders look back the number of months the rulebook says",
              baseline.get("months") == want_months,
              f"{baseline.get('months')} vs {want_months}", ac="AC08")
        check("the customer groups counted and left out are both named",
              bool(baseline.get("channels_included")) and bool(baseline.get("channels_excluded"))
              and bool(baseline.get("intercompany_excluded")), "one of the three lists is empty",
              ac="AC08")
        # each figure is that block's litres as a % of the window total, so a perfect
        # split reads 100% — the rule is 0.5% either side of adding back up.
        recon = baseline.get("reconciliation") or {}
        off = {k: v for k, v in recon.items()
               if k.endswith("_pct") and isinstance(v, (int, float)) and abs(100.0 - v) > 0.5}
        check("the past sales add back up to their own total", not off, str(off), ac="AC08")
        check("the plan says out loud that it used them", expected_used is True,
              f"used={expected_used}", ac="AC08")
    else:
        fallback = [a for a in (assumed or []) if "plan sheet's weekly buckets" in a]
        check("when past sales could not be read, the plan says what it used instead",
              bool(fallback), "no line in the honesty list names the fallback", ac="AC08")
        check("and it does not claim it used them", expected_used is False,
              f"used={expected_used}", ac="AC08")


# What R21 actually rules: the dispatch headline is how many days of work are in the
# open book and how long a bill takes to reach the gate — the COUNT OF TRUCKS THAT
# LEFT TODAY is the number Gurvinder said to remove. Two nets, and both are about
# that number rather than about a word:
#   * a key anywhere in the file that carries it, and
#   * a headline that puts a figure in front of "truck".
# It used to be `re.findall(r'[^"]*trucks[^"]*', json.dumps(overview))` over the whole
# blob — lowercase, plural, substring. "41 Trucks left today" and "41 truck left
# today" both walked past it while gen's own honest "a bill reaches a truck in about
# 2 day(s)" only survived by the same accident; and one warning about EXIM tankers
# carrying the word refused the ENTIRE cycle, which on a three-minute loop is the
# site freezing on its last good plan because of one word in an adapter note. That
# blanket scan is why `warnings` was amputated from this file; with the rule scoped
# to what R21 says, the warnings come back (honesty.json still carries them in full,
# and that is the copy the footer reads).
TRUCKS_KEY_RE = re.compile(r"trucks|dispatched_today", re.IGNORECASE)
TRUCK_COUNT_RE = re.compile(r"\d[\d,.]*\s*(?:trucks?|lorr(?:y|ies))\b", re.IGNORECASE)


def check_overview(check, overview):
    """AC09 — the front page carries the money, the machines and the dispatch book."""
    money = overview.get("money") or {}
    need = ("today_plan_rs", "today_booked_rs", "mtd_made_rs",
            "target_rs_per_day", "floor_rs_per_day")
    missing = [k for k in need if not isinstance(money.get(k), (int, float))]
    check("the front page says what today's filling is worth, against the target and the floor",
          not missing, str(missing), ac="AC09")
    lines_today = overview.get("lines_today") or []
    working = bool((overview.get("day1") or {}).get("working", True))
    check("the front page has a strip per machine", bool(lines_today) or not working,
          f"{len(lines_today)} machines on a working day", ac="AC09")
    # A strip that says nothing is not a strip. This is the front-page half of item
    # 20: with `line_hours_max` gone from the day files every machine showed
    # `hours_available: null` and the only check that looked was this one, which
    # could not fail on real data because the rows are built one per machine.
    silent = [row.get("line") for row in lines_today
              if not row.get("line")
              or not isinstance(row.get("hours_planned"), (int, float))
              or not isinstance(row.get("hours_available"), (int, float))]
    check("every machine on the front page says its name, its hours and the hours it had",
          not silent, str(silent[:4]), ac="AC09")
    dispatch = overview.get("dispatch") or {}
    for key in ("pendency_days_all", "pendency_days_oil", "lag_median_days",
                "lag_p90_days", "lag_basis", "headline"):
        if key not in dispatch:
            check("the dispatch headline is days of work in the book and how long a bill "
                  "waits", False, f"{key} is missing", ac="AC09")
            break
    else:
        check("the dispatch headline is days of work in the book and how long a bill waits",
              True, "", ac="AC09")

    def paths(node, at=""):
        if isinstance(node, dict):
            for k, v in node.items():
                here = f"{at}.{k}" if at else k
                yield here
                yield from paths(v, here)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from paths(v, f"{at}[{i}]")

    bad_keys = [p for p in paths(overview) if TRUCKS_KEY_RE.search(p.split(".")[-1])]

    def headlines(node, at=""):
        """Every string this file publishes AS a headline, wherever it sits."""
        if isinstance(node, dict):
            for k, v in node.items():
                here = f"{at}.{k}" if at else k
                if isinstance(v, str) and k.endswith("headline"):
                    yield here, v
                else:
                    yield from headlines(v, here)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from headlines(v, f"{at}[{i}]")

    counted = [f"{where}: {TRUCK_COUNT_RE.search(text).group(0)}"
               for where, text in headlines(overview) if TRUCK_COUNT_RE.search(text)]
    check("the trucks that left today are not the headline any more",
          not bad_keys and not counted, str((bad_keys + counted)[:3])[:220], ac="AC09")


def check_stuck_counts(check, spine, day1_blocked):
    """The two ways to count what could not start, kept apart.

    `blocked` is an ATTEMPT count — one product tried on four machines and stopped on
    all four is four rows — and `blocked_products` is how many different products those
    rows are. On 7 Sep that is 87 rows behind 33 products, and the page that quoted the
    rows said 87 stuck products. So: never more products than attempts, never products
    without attempts (or the other way round), and day 1 must say the same thing in the
    spine as `overview.day1_blocked` says on the front page."""
    bad = [f"{r['date']} {r.get('blocked_products')} of {r.get('blocked')}"
           for r in spine
           if r.get("blocked_products") is None
           or r["blocked_products"] > r["blocked"]
           or (r["blocked_products"] == 0) != (r["blocked"] == 0)]
    check("the spine counts stuck attempts and stuck products apart", not bad,
          "; ".join(bad[:5]))
    if not spine:
        return check("day 1 is in the spine", False, "the spine is empty")
    day1 = spine[0]
    check("day 1 says the same stuck counts in the spine and on the front page",
          day1["blocked"] == day1_blocked["attempts"]
          and day1.get("blocked_products") == day1_blocked["products"],
          f"spine {day1['blocked']} attempts / {day1.get('blocked_products')} products vs "
          f"front page {day1_blocked['attempts']} / {day1_blocked['products']}")


def check_assumptions(check, rb, assumptions, raw_questions_text):
    """AC10 — every ruling, every guess and every open question, on one page."""
    ids = {r["id"] for r in assumptions.get("settled") or []}
    want = {r["id"] for r in rb.get("settled") or []}
    check("every settled ruling is on the page", ids == want,
          f"missing {sorted(want - ids)[:4]}, extra {sorted(ids - want)[:4]}", ac="AC10")
    ids = {r["id"] for r in assumptions.get("assumed") or []}
    want = {r["id"] for r in rb.get("assumed") or []}
    check("every guess the plan makes is on the page", ids == want,
          f"missing {sorted(want - ids)[:4]}, extra {sorted(ids - want)[:4]}", ac="AC10")
    ids = {r["id"] for r in assumptions.get("build_choices") or []}
    want = {r["id"] for r in rb.get("build_choices") or []}
    check("every choice made while building it is on the page", ids == want,
          f"missing {sorted(want - ids)[:4]}, extra {sorted(ids - want)[:4]}", ac="AC10")
    questions = assumptions.get("open_questions") or []
    headings = count_question_headings(raw_questions_text)
    check("every question in the file for Gurvinder is on the page",
          len(questions) == headings,
          f"{len(questions)} read, {headings} in the file — "
          f"{sorted(set(heading_numbers(raw_questions_text)) - {q['number'] for q in questions})}"
          f" got past the reader", ac="AC10")
    numbers = [q["number"] for q in questions]
    # 1, 2, 3 … with nothing missing off either end. The old form allowed any
    # ascending set, so losing the LAST question — number 14, the phone one — left a
    # list that was still unique and still sorted, and still passed.
    check("every question is numbered once, 1 upwards, with none missing",
          numbers == list(range(1, len(numbers) + 1)), str(numbers), ac="AC10")
    floor = question_floor(raw_questions_text)
    check("the file still has every question it says it has",
          floor is not None and len(questions) >= floor,
          f"{len(questions)} read against a declared floor of {floor} — a floor of None "
          f"means the `<!-- questions: N -->` line was removed from the file", ac="AC10")
    bad = [q["number"] for q in questions if q.get("status") not in ("open", "answered")]
    check("every question is either open or answered", not bad, str(bad[:4]), ac="AC10")
    # THE ONE THAT BLOCKED THE DEPLOY (round B, item 19). Question 14 asks Gurvinder
    # for WhatsApp numbers; he answers in prose, in this file, and this file is
    # published at a public hostname. Two nets, over what is about to be written:
    # the masker's own guard, and the wider "any ten digits at all" scan the
    # document can afford. Masking runs first, so a failure here means the door was
    # missed — never a reason to soften either net.
    leaks = question_digit_leaks(questions)
    check("no phone number and no long run of digits is on the questions page",
          not leaks, str([f"{path}: {value[:24]}" for path, value in leaks[:3]]),
          ac="AC10")


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
# ------------------------------------------------------- the days gone -------
# plan/history.json. The ONE file on this site that looks backwards: a record
# per day between the 1st of the month and yesterday, read off the factory's own
# systems by live/adapters/factory_history.py and passed through the freeze.
#
# It is not the plan and it is never mixed into it. Two rules hold it together:
#   * a figure that was not read is NULL, and the page draws a null as "not
#     read" — never as a bar of height zero, which is the plant idle.
#   * the machine log and the goods receipts are the same production counted two
#     ways, so they travel side by side, both labelled, and this file refuses to
#     be written if any key ever merges them.
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]

# The numbers a day record carries, and the only ones. by_company and
# booked_by_item stay in state.json: nothing on the site reads them, and this
# file is fetched by every browser on the /days page every three minutes.
HISTORY_DAY_NUMBERS = ("made_mes_l", "made_mes_cases", "runs", "open_segments",
                       "made_booked_l", "made_booked_pcs", "booked_receipts",
                       "booked_unparsed_pcs", "billed_out_l", "billed_out_pcs",
                       "billed_lines", "billed_unparsed_pcs",
                       "dispatched_oil_l", "dispatched_all_l",
                       "trucks_oil", "trucks_all", "rows_oil", "bills_oil")
HISTORY_SUMS = ("made_mes_l", "made_booked_l", "billed_out_l",
                "dispatched_oil_l", "dispatched_all_l", "runs")
# A key that would mean "the two ways of counting, added". None may ever exist.
HISTORY_BANNED_KEYS = ("made_l", "made_total_l", "filled_l", "total_made_l",
                       "produced_l")


def build_history(inp, meta, stamp, check):
    """The days already gone this month, as records. Returns the file to write."""
    h0 = meta["horizon"][0]
    d0 = date.fromisoformat(h0)
    first = d0.replace(day=1)
    expected = [(first + timedelta(days=i)).isoformat() for i in range((d0 - first).days)]
    through = expected[-1] if expected else "—"

    block = inp.get("history") if isinstance(inp.get("history"), dict) else {}
    data = block.get("data") if isinstance(block.get("data"), dict) else None
    mode = block.get("mode") or "missing"

    rule = plain(
        "the days before today are records read off the factory's own systems — what was "
        "filled, and what left the gate. Nothing on them was worked out by the computer, "
        "and the two ways of counting what was filled are never added together.")
    mes_label = plain("filled, per the machine log — it sees about two-thirds of the plant")
    booked_label = plain("booked into the godown — a day's booking can land a day after "
                         "the filling it books")

    days, trimmed, notes = [], [], []
    if data is not None:
        for row in data.get("days") or []:
            if not isinstance(row, dict) or not isinstance(row.get("date"), str):
                continue
            iso = row["date"]
            if iso >= h0:
                # A cycle that straddled midnight read a day the plan calls today.
                # Report it and drop it; the next cycle heals itself.
                trimmed.append(iso)
                continue
            if iso not in expected:
                trimmed.append(iso)
                continue
            day = date.fromisoformat(iso)
            out = {"date": iso, "day_of_month": day.day,
                   "weekday": WEEKDAY_NAMES[day.weekday()],
                   "working": day.weekday() != 6, "happened": True}
            for key in HISTORY_DAY_NUMBERS:
                out[key] = row.get(key)
            out["booked_truncated"] = bool(row.get("booked_truncated"))
            out["complete"] = bool(row.get("complete"))
            out["settled"] = bool(row.get("settled"))
            out["read_at"] = row.get("read_at")
            out["notes"] = [n for n in (row.get("notes") or []) if isinstance(n, str)]
            out["made_mes_label"] = mes_label
            out["made_booked_label"] = booked_label
            days.append(out)
        notes = [n for n in (data.get("notes") or []) if isinstance(n, str)]

    days.sort(key=lambda r: r["date"])
    have = {r["date"] for r in days}
    missing = [d for d in expected if d not in have]

    sums = {k: None for k in HISTORY_SUMS}
    covers = {k: 0 for k in HISTORY_SUMS}
    for row in days:
        for key in HISTORY_SUMS:
            value = row.get(key)
            if isinstance(value, (int, float)):
                sums[key] = (sums[key] or 0) + value
                covers[key] += 1
    for key, value in sums.items():
        if isinstance(value, float):
            sums[key] = round(value, 1)

    status = ("unavailable" if data is None
              else "complete" if days and not missing and all(r["complete"] for r in days)
              else "complete" if not expected
              else "partial")

    reason = None
    if data is None:
        reason = plain("the days already gone could not be read this cycle "
                       f"(the factory records came back {mode})")

    out = {
        "meta": dict(stamp,
                     month=h0[:7],
                     first=first.isoformat(),
                     through=through,
                     status=status,
                     records_mode=mode,
                     records_read_at=(data or {}).get("read_at"),
                     records_through=(data or {}).get("through"),
                     records_from_cache=bool((data or {}).get("from_cache")),
                     source=(inp.get("provenance") or {}).get("history")),
        "rule": rule,
        "days": days,
        "missing_dates": missing,
        "trimmed_dates": sorted(set(trimmed)),
        "totals": dict(sums,
                       days_with_records=len(days),
                       days_not_read=len(missing),
                       working_days=sum(1 for r in days if r["working"]),
                       covers=covers),
        "basis": (data or {}).get("basis") or {},
        "notes": notes,
        "unavailable_reason": reason,
    }

    # ---- the checks. Every one refuses the whole run. ---------------------
    check("the days gone belong to the month the plan is in",
          data is None or data.get("month") == h0[:7],
          f"records say {(data or {}).get('month')}, the plan is in {h0[:7]}")
    accounted = sorted(have | set(missing))
    check("every day between the 1st and today is accounted for exactly once",
          accounted == expected,
          f"{len(accounted)} accounted vs {len(expected)} expected; "
          f"first gap {next((d for d in expected if d not in accounted), '-')}")
    check("the number of days gone matches the calendar",
          len(days) + len(missing) == (d0 - first).days,
          f"{len(days)} + {len(missing)} vs {(d0 - first).days}")
    check("no record is dated today or later",
          all(r["date"] < h0 for r in days),
          str([r["date"] for r in days if r["date"] >= h0][:3]))
    check("the last day gone is the day before today",
          through == (expected[-1] if expected else "—")
          and (not expected or through == (d0 - timedelta(days=1)).isoformat()),
          f"{through} vs {h0}")
    bad_num = [f"{r['date']}.{k}" for r in days for k in HISTORY_DAY_NUMBERS
               if r[k] is not None and not (isinstance(r[k], (int, float)) and r[k] >= 0)]
    check("every figure in a record is zero or more, or not read at all",
          not bad_num, str(bad_num[:5]))
    bad_day = [r["date"] for r in days
               if r["working"] != (date.fromisoformat(r["date"]).weekday() != 6)
               or r["weekday"] != WEEKDAY_NAMES[date.fromisoformat(r["date"]).weekday()]]
    check("a working day is any day that is not a Sunday, on every record",
          not bad_day, str(bad_day[:5]))
    bad_oil = [r["date"] for r in days
               if (r["dispatched_oil_l"] is not None and r["dispatched_all_l"] is not None
                   and r["dispatched_oil_l"] > r["dispatched_all_l"])
               or (r["trucks_oil"] is not None and r["trucks_all"] is not None
                   and r["trucks_oil"] > r["trucks_all"])]
    check("what left the gate for Oil never exceeds all three companies together",
          not bad_oil, str(bad_oil[:5]))
    # Over the raw records AND over the whole file about to be written: a key
    # that merges the machine log with the goods receipts must not exist
    # anywhere, not in the adapter's row and not in anything built from it.
    def merged_keys(node):
        found = set()
        if isinstance(node, dict):
            found |= {k for k in node if k in HISTORY_BANNED_KEYS}
            for value in node.values():
                found |= merged_keys(value)
        elif isinstance(node, list):
            for value in node:
                found |= merged_keys(value)
        return found

    merged = sorted(merged_keys(out) | merged_keys((data or {}).get("days") or []))
    check("the two ways of counting what was filled are never added together",
          not merged, str(merged))
    check("the days gone say complete only when every one of them is whole",
          (status != "complete") or (not missing and all(r["complete"] for r in days)),
          f"status {status}, {len(missing)} not read, "
          f"{sum(1 for r in days if not r['complete'])} part-read")
    return out


def build(paths, check):
    """Everything, in one pass. Returns (outputs, stats)."""
    inp = load(paths["inputs"])
    summary = load(paths["summary"])
    events = load(paths["events"])
    order_by = load(paths.get("order_by_read") or paths["order_by"])
    day_files = sorted(glob.glob(os.path.join(paths["days_dir"], "day-*.json")))
    days = [load(f) for f in day_files]
    august, august_warnings = august_calibration()

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
    warnings = list(inp.get("warnings") or []) + august_warnings

    # ---- MARK 4: the rulebook, or not ---------------------------------------
    # Presence is the switch. Everything below that reads `rb` is skipped entirely
    # when the freeze carried no rulebook, and the Mark 3 path runs untouched.
    rb = inp.get("rulebook") or None
    rb_mode = rb is not None
    summary_rb = (summary.get("rulebook") or {}) if rb_mode else {}
    lines_basis_kind = inp.get("lines_basis_kind") or {}
    lines_speeds = inp.get("lines_speeds") or {}
    lines_multi = inp.get("lines_multi") or {}
    sku_pack = (rb.get("sku_pack") or {}) if rb_mode else {}
    drum_codes = set((rb.get("drums") or {}).get("skus") or []) if rb_mode else set()
    baseline = inp.get("demand_baseline") or {}
    if rb_mode:
        check_engine_gates(check, rb, summary_rb, (rulebook_on_disk() or {}).get("version"))
        check_pack_class(check, rb, plan)
        check_runs(check, rb, lines_cfg, lines_multi, days, sku_pack)
        check_hours_and_nights(check, days, rules["shift_hours"],
                               sundays_off=bool(rules.get("sundays_off", True)))

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

    # THE GODOWN CEILING IS DECLARED, NOT GUESSED (Daman, 2026-09-04).
    # Mark 2 shipped it as "Daman's spreadsheet — not measured (open question Q2)" and
    # every "% of the godown" on the site wore an OUR GUESS badge because of it. Daman
    # ruled the sheet IS the limit: "827,000 L godown = this is correct, no guess now."
    # The sentence below is what the site prints; the litres in it are READ from the
    # inputs, never typed, so the badge can never drift from the number beside it.
    ceiling_declared_by = (rules.get("storage_ceiling_declared_by")
                           or "Daman, 2026-09-04 (capacity sheet 2026-08-29)")
    ceiling_source = (
        f"Daman's capacity sheet, 29 Aug 2026 — {rules['storage_ceiling_l']:,} L working, "
        f"{rules['storage_peak_l']:,} L peak. A declared limit, not a measurement estimate."
    )

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

    # ---- what no machine can fill, and what is filled by hand ---------------
    # MARK 3 GUESSED THE SLOT AND MARK 4 KNOWS IT. The old test asked whether the
    # `lines` table had a key for the slot this file worked out from the plan
    # sheet — with a "TIN" key meaning every tin. Mark 4 keys the Tin Head by size
    # (15L / 3L / 5L), so that question answered "nothing can fill a tin" about four
    # products the planner had just scheduled. In rulebook mode the question is the
    # one the engine asks: does any line name this pack AND this bottle, and does
    # anybody have a speed for it (eligible_lines / rb_pref). Drums are not in this
    # list at all — they are filled by hand and published as such (R14, AC03).
    manual_fill = []
    no_machine = []
    if rb_mode:
        drum_display = (rb.get("drums") or {}).get("display")
        for row in plan:
            pack = sku_pack.get(row["code"]) or {}
            slot, family = pack.get("slot"), pack.get("family")
            if row["code"] in drum_codes or slot == "DRUM":
                manual_fill.append({
                    "code": row["code"], "sku": row["sku"],
                    "litres_per_piece": row["litres_per_piece"],
                    "plan_pieces": row["pieces"], "plan_litres": row["litres"],
                    "display": drum_display,
                })
                continue
            fills = int(pack.get("fills_per_piece") or 1)
            if pack and eligible_lines(rb, lines_cfg, lines_multi, slot, family, fills):
                continue
            entry = {
                "code": row["code"], "sku": row["sku"], "pack_type": row["pack_type"],
                "litres_per_piece": row["litres_per_piece"],
                "plan_pieces": row["pieces"], "plan_litres": row["litres"],
                "slot_needed": slot, "bottle_needed": family,
                "reason": plain(f"no machine can fill {plain_slot(slot)}" if slot
                                else "the recipe does not say what container this goes in"),
            }
            rate = realise.get(row["code"])
            if rate:
                entry["value_est_rs"] = round(row["litres"] * rate)
            no_machine.append(entry)
        manual_fill.sort(key=lambda r: -r["plan_litres"])
    else:
        slots = set()
        for spec in lines_cfg.values():
            slots.update(spec.keys())
        if "5L" in slots:
            slots.add("15L")      # the engine works 15 L PET off the 5 L head
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
    no_machine_for = " or ".join(sorted({plain_slot(u["slot_needed"]) for u in no_machine
                                         if u.get("slot_needed")})) or "-"
    if rb_mode:
        # AC03, the other half: a drum is filled by hand, so it is never a machine's
        # fault that it is not made and it never appears as one.
        blocked_drums = sorted({b["code"] for d in days for b in d["blocked"]
                                if b["code"] in drum_codes})
        check("the drums are shown as filled by hand, never as a machine that is missing",
              sorted(u["code"] for u in manual_fill) == sorted(drum_codes)
              and not [u for u in no_machine if u["code"] in drum_codes]
              and not blocked_drums,
              f"filled by hand {sorted(u['code'] for u in manual_fill)}, "
              f"drums in the rulebook {sorted(drum_codes)}, held up {blocked_drums}",
              ac="AC03")
        check("gen and the planner agree on what no machine can fill",
              sorted(u["code"] for u in no_machine) == sorted(summary_rb.get("no_line_skus") or []),
              f"{sorted(u['code'] for u in no_machine)} vs "
              f"{sorted(summary_rb.get('no_line_skus') or [])}", ac="AC03")

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
    # TWO COUNTS, NAMED APART. `blocked` is one row per ATTEMPT: in rulebook mode a
    # product is a candidate on up to four machines, so one product that cannot start
    # appends a row per machine per pass. The site read that row count as "stuck
    # products" and headlined nearly double the truth. `blocked_products` is the
    # distinct products — the engine's own `blocked_codes` where it publishes them —
    # and that is the one to quote, exactly as overview.day1_blocked already does.
    blocked_label = plain("'blocked' counts ATTEMPTS: one product can be tried on several machines "
                          "in a day and each try that is stopped is its own row. "
                          "'blocked_products' is how many different products could not start. "
                          "Quote products; never add the two together")

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
        # the engine publishes the distinct codes in rulebook mode only; on the legacy
        # path the same set is one line of work, and neither day may be published as a
        # bare row count (see blocked_label).
        blocked_codes = day.get("blocked_codes")
        if blocked_codes is None:
            blocked_codes = sorted({b["code"] for b in day["blocked"]})

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
            "blocked_products": len(blocked_codes),
            "blocked_label": blocked_label,
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
            # the one machine that runs a second shift tonight, by name, so the day
            # list can say it without opening the day file (R03).
            "night_line": (day.get("night_line") or {}).get("line"),
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
            # MARK 4: the hours each machine HAD that day (10, or 20 for the one that
            # runs at night), which machine that was and why, and how many times each
            # machine changed product (R02/R03/R06). On a Mark 3 day file none of the
            # three exists, and each is published here as NULL — not as a zero, which
            # would read as "it had no hours", and not dropped, which would read on the
            # page as a crash. The comment here used to claim they were left out
            # altogether; they never were, and the site's own types make all three
            # optional-or-null. In rulebook mode `line_hours_max` is required and
            # checked — see check_hours_and_nights.
            "line_hours_max": day.get("line_hours_max"),
            "night_line": day.get("night_line"),
            "product_changes": day.get("product_changes"),
            "flushes": day["flushes"],
            "storage": day["storage"],
            "storage_ceiling_declared": True,
            "book": book,
            "open_real_l_computed": row["open_real_l_computed"],
            "runs": day["runs"],
            "blocked": day["blocked"],
            "blocked_products": len(blocked_codes),
            "blocked_label": blocked_label,
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
    check("every expected-order row carries all three marks", not tag_faults, str(tag_faults[:5]),
          ac="AC08")

    # the same tagging rule over the whole demand stream, not just the day files
    stream_faults = [
        o.get("docnum") for o in orders
        if is_forecast(o) and not (o.get("channel") == "FORECAST"
                                   and str(o.get("docnum", "")).startswith("FCST")
                                   and o.get("_src") == "FORECAST")
    ]
    check("every expected row in the demand list is marked", not stream_faults, str(stream_faults[:5]),
          ac="AC08")
    check("no confirmed order is marked as expected",
          not [o.get("docnum") for o in orders
               if not is_forecast(o) and str(o.get("docnum", "")).startswith("FCST")],
          ac="AC08")

    # ---- lines ---------------------------------------------------------------
    # THE SPEED TABLE IS PUBLISHED WITH ITS OWN ARITHMETIC. In rulebook mode every
    # row carries the app's rated speed, what August typically and best did, the
    # planning speed the plan really ran at and the RULE that produced it — and gen
    # works the planning speed out again from that rule (AC05) instead of trusting
    # the number. There is no derived 15 L row here: the rulebook names every slot a
    # line has and 15 litres is a tin on the Tin Head (AC02). Mark 3's 5 L ÷ 3 was
    # the arithmetic that put 15 L tins on Clear Pack.
    basis_words = {"measured": "observed", "rated": "rated", "carried": "carried",
                   "derived": "derived"}
    planning_factor = ((rb.get("efficiency") or {}).get("planning_factor")
                       if rb_mode else None)
    factor_pct = round((planning_factor or 0) * 100)
    # "a run of 3 h or more" is printed once, for every machine. It used to be read
    # off whichever rule happened to be first and published as everyone's; if the
    # rulebook ever gives one machine a different threshold, this refuses instead of
    # quietly labelling the others with it.
    sustained_h, sustained_mins = None, set()
    line_slots, speed_rows, no_speed_slots = {}, [], {}
    for line, spec in lines_cfg.items():
        rows = []
        for slot, rate in sorted(spec.items()):
            raw_basis = str((lines_basis.get(line) or {}).get(slot, "rated"))
            basis = basis_words.get(raw_basis, raw_basis)
            if not rb_mode:
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
                continue
            block = ((lines_speeds.get(line) or {}).get("speeds") or {}).get(slot) or {}
            rule = block.get("planning_rule") or {}
            kind = str((lines_basis_kind.get(line) or {}).get(slot)
                       or rule.get("kind") or basis)
            if rule.get("sustained_min_minutes"):
                sustained_mins.add(rule["sustained_min_minutes"])
                # the notes below need it while the rows are still being built, so it
                # is taken as it is met; the check after the loop is what makes taking
                # the first one safe.
                sustained_h = min(sustained_mins) / 60.0
            row = {
                "slot": slot,
                "families": dict(((rb["lines"].get(line) or {}).get("slots") or {}).get(slot) or {}),
                "rated": block.get("rated"),
                "rated_basis": block.get("rated_basis"),
                "aug_median": block.get("aug_median"),
                "aug_best": block.get("aug_best"),
                "aug_runs": block.get("aug_runs"),
                "aug_runs_sustained": block.get("aug_runs_sustained"),
                "planning": rate,
                "planning_basis": block.get("planning_basis"),
                "planning_rule": rule,
                "rate_basis": kind,
                "rate_basis_raw": raw_basis,
                # the planning speed IS the pace the plan runs at: the factory's own
                # pace is already inside it, and rules.efficiency is 1.0 so nothing
                # is slowed a second time.
                "stored_rate_per_hr": rate,
                "effective_rate_per_hr": rate,
                "note": plain(
                    f"the machine's listed speed cut to {factor_pct}%, then held to the best it "
                    f"kept for {sustained_h or 3:g} hours or more in August — whichever is slower"
                    if kind == "capped" else
                    f"the machine's listed speed cut to {factor_pct}% — August has no run long "
                    f"enough to hold it to"
                    if kind == "rated" else
                    f"the middle of what it really did in August, over runs of {sustained_h or 3:g} "
                    f"hours or more — nobody has a listed speed for it"
                    if kind == "typical" else
                    f"a speed carried over from the last plan, cut to {factor_pct}% — no listed "
                    f"speed, no August run"
                    if kind == "carried" else
                    "the same containers an hour as another pack on this machine — nobody has "
                    "timed this one on its own"),
            }
            multi = (lines_multi.get(line) or {}).get(slot)
            if multi is not None:
                mblock = ((lines_speeds.get(line) or {}).get("speeds_multi") or {}).get(slot) or {}
                row["set_of_two_rate_per_hr"] = multi
                row["set_of_two_basis"] = mblock.get("planning_basis")
                speed_rows.append(dict(line=line, slot=slot, multi=True, planning=multi,
                                       rate_basis=str(mblock.get("planning_rule", {}).get("kind")
                                                      or kind),
                                       planning_rule=mblock.get("planning_rule") or {},
                                       rated=mblock.get("rated"),
                                       aug_median=mblock.get("aug_median"),
                                       aug_best=mblock.get("aug_best"),
                                       aug_runs=mblock.get("aug_runs"),
                                       planning_basis=mblock.get("planning_basis")))
            rows.append(row)
            speed_rows.append(dict(line=line, slot=slot, multi=False, planning=rate,
                                   rate_basis=kind, planning_rule=rule,
                                   rated=row["rated"], aug_median=row["aug_median"],
                                   aug_best=row["aug_best"], aug_runs=row["aug_runs"],
                                   planning_basis=row["planning_basis"]))
        if rb_mode:
            # A slot the rulebook allows that nobody has a speed for. Nothing is
            # scheduled on it (B16) and saying so is the point — it is a question for
            # the plant, not an empty row.
            gaps = []
            for slot, fams in sorted(((rb["lines"].get(line) or {}).get("slots") or {}).items()):
                if slot in spec:
                    continue
                block = ((lines_speeds.get(line) or {}).get("speeds") or {}).get(slot) or {}
                gaps.append({"slot": slot, "families": dict(fams),
                             "why": block.get("planning_basis")
                             or plain("no speed for it, so nothing is put on it")})
            if gaps:
                no_speed_slots[line] = gaps
        elif "5L" in spec:
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
    if rb_mode:
        check_planning_speeds(check, speed_rows, planning_factor)
        check("no machine speed is invented for a pack the rulebook did not name",
              not [r for line, rows in line_slots.items() for r in rows
                   if r["slot"] not in ((rb["lines"].get(line) or {}).get("slots") or {})],
              str([f"{line} {r['slot']}" for line, rows in line_slots.items() for r in rows
                   if r["slot"] not in ((rb["lines"].get(line) or {}).get("slots") or {})][:4]),
              ac="AC02")

    runs_by_line = defaultdict(list)
    for day in days:
        for run in day["runs"]:
            runs_by_line[run["line"]].append(dict(run, date=day["date"]))

    night_days = defaultdict(list)
    for day in days:
        night = (day.get("night_line") or {}).get("line")
        if night:
            night_days[night].append(day["date"])

    line_stats = []
    for line in lines_cfg:
        runs = runs_by_line.get(line, [])
        agg = defaultdict(float)
        for run in runs:
            agg[run["sku"]] += run["litres"]
        stat = {
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
        }
        if rb_mode:
            # the nights this machine is the one that runs a second shift, the hours it
            # has TODAY (10, or 20 if tonight is its night — R02/R03), and the packs the
            # rulebook lets it fill that nobody has given it a speed for (B16).
            stat["night_days"] = night_days.get(line, [])
            stat["hours_max_today"] = (days[0].get("line_hours_max") or {}).get(line)
            stat["no_speed_slots"] = no_speed_slots.get(line, [])
        line_stats.append(stat)

    measured_slots = sorted(f"{line} {slot}" for line, spec in lines_basis.items()
                            for slot, basis in spec.items() if basis == "measured")
    if rb_mode:
        # The Mark 3 sentence says "% of its listed speed" and reads the number out of
        # rules.efficiency, which is 1.0 in Mark 4 — it would print "100% of listed",
        # the exact opposite of what the plan does. The cut lives in the planning
        # speeds now, so the sentence is built from the rulebook's own factor.
        rate_note = plain(
            f"each machine is planned at {factor_pct}% of its listed speed, and never faster "
            f"than the best it kept for {sustained_h or 3:g} hours or more in August")
    else:
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
    if rb_mode:
        check("every machine counts a long run the same way",
              len(sustained_mins) <= 1, f"the rulebook has {sorted(sustained_mins)} minutes",
              ac="AC05")
        lines_out["planning_factor"] = planning_factor
        lines_out["planning_factor_basis"] = (rb.get("efficiency") or {}).get("applies_to")
        lines_out["sustained_hours"] = sustained_h
        lines_out["rulebook_version"] = rb.get("version")
        lines_out["night_line_today"] = days[0].get("night_line")
        lines_out["hours_per_session"] = rules["shift_hours"]
    # site-sep/lib/types.ts types rate_basis as observed | rated | derived. The live
    # freeze can also fall back to a carried table, which is a fourth honest word —
    # and Mark 4 says where a planning speed came from in five (capped / rated /
    # typical / carried / derived). So the check is that the word is one WE define
    # and the site renders, not that it is one of three: a word outside the union
    # means the freeze grew a basis nobody drew.
    seen_basis = {s["rate_basis"] for line in line_stats for s in line["slots"]}
    check("every machine speed says where it came from, in a word the site knows",
          seen_basis <= (RULEBOOK_BASIS_WORDS if rb_mode else LEGACY_BASIS_WORDS),
          str(sorted(seen_basis)))
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
    # over days 2-4 (day 1's pile IS the live count — reconciled below), and it
    # drains its queue by DATE. (Until 2026-09-05 the queue popped head-first, so a
    # day-1 bill waited behind the pile's day-4 tranche and left on day 4; the lower
    # bound below caught that the moment the live pile fell under day-1 billing,
    # 4 Sep 21:39, and refused to publish for 14 hours — the engine was fixed, not
    # the check.) Asserting the old equality here would still report the pile's
    # own departures as a fault. What is true, on any length of run and any size
    # of pile, is a two-sided bound:
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

    # ---- B20: WHAT THE GODOWN CEILING ACTUALLY DID TO THIS RUN ----------------
    # The single biggest hand on this month's sheet, and until 2026-09-06 it was one
    # unnamed line in the engine: `cap = min(cap, headroom / litres per piece)`. It
    # appeared in no ruling, no assumption and no build choice, and the words headroom,
    # throttle and storage ceiling were in this file's output ZERO times. It is B20 now,
    # and this block is the run's own arithmetic beside it — never a claim, always a
    # count off the days the engine just produced.
    cap_days = [d for d in days if d.get("storage_cap")]
    # TWO DIFFERENT DAYS, AND THE BIGGER ONE IS THE ONE THAT MATTERS. `throttled` is the
    # engine's morning flag — the godown was ALREADY nearly full when the day opened.
    # `bit` is the day the cap actually stopped or shortened work, which includes every
    # day that opened with room and filled it: day 1 opens with 146,351 L of room, is
    # not flagged, and still ends at nothing with twenty products stopped. Quoting the
    # morning flag alone understates the cap by the days the plan itself filled.
    throttled_days = [d for d in cap_days if d["storage_cap"].get("throttled")]
    bit_days = [d for d in cap_days
                if d["storage_cap"].get("stopped_products")
                or d["storage_cap"].get("capped_runs")]
    working_days = [d for d in days if d.get("working")]
    made_by_code = defaultdict(float)
    for day in days:
        for run in day["runs"]:
            made_by_code[run["code"]] += float(run["litres"] or 0)
    sheet_codes_all = [r["code"] for r in plan if (r.get("pieces") or 0) > 0]
    never_made = [r for r in plan
                  if (r.get("pieces") or 0) > 0 and made_by_code.get(r["code"], 0) < 1]
    stopped_by_storage = sorted({c for d in cap_days
                                 for c in (d["storage_cap"].get("stopped_codes") or [])})
    capped_l = round(sum(float(d["storage_cap"].get("capped_l") or 0) for d in cap_days))
    sheet_l = sum(float(r["litres"] or 0) for r in plan)
    made_l_month = sum(float(d["made_litres"] or 0) for d in days)
    storage_cap_out = {
        "rule": "B20",
        "in_effect": bool(bit_days),
        "ceiling_l": rules["storage_ceiling_l"],
        "what_it_does": plain(
            "no run may be longer than the room left in the godown. The room left is "
            "the godown limit minus what is physically in there — goods finished and "
            "waiting, plus everything already billed and still waiting for a truck. It "
            "is worked out again every morning and comes down litre for litre as the "
            "day is filled, so when it reaches nothing the plant stops for the day "
            "whatever hours, bottles and orders are left"),
        "days_it_bit": len(bit_days),
        "days_it_bit_dates": [d["date"] for d in bit_days],
        "days_throttled": len(throttled_days),
        "days_throttled_say": plain(
            "the days that OPENED with the godown nearly full. A day that opens with room "
            "and fills it is not counted here — it is counted in the days it bit"),
        "working_days": len(working_days),
        "days_throttled_dates": [d["date"] for d in throttled_days],
        "runs_cut_short": sum(int(d["storage_cap"].get("capped_runs") or 0) for d in cap_days),
        "litres_cut_off_runs_it_allowed": capped_l,
        "products_stopped_outright": len(stopped_by_storage),
        "products_stopped_codes": stopped_by_storage,
        "days_at_zero_headroom": sum(1 for d in cap_days
                                     if float(d["storage_cap"].get("headroom_l_at_close") or 0) < 100),
        # The whole month against the sheet, and how much of the sheet never gets made
        # at all. These two are the size of the thing: they are what the ceiling costs.
        "month_made_l": round(made_l_month),
        "month_sheet_l": round(sheet_l),
        "month_made_pct_of_sheet": round(made_l_month / sheet_l * 100, 1) if sheet_l else None,
        "products_on_the_sheet": len(sheet_codes_all),
        "products_never_made": len(never_made),
        "products_never_made_top": [{"code": r["code"], "sku": r["sku"],
                                     "month_target_litres": round(float(r["litres"] or 0))}
                                    for r in sorted(never_made,
                                                    key=lambda r: -float(r["litres"] or 0))[:12]],
        "why_it_is_a_build_choice": plain(
            "Gurvinder ruled the godown limit and Daman declared the figure, but neither "
            "said what the planner should DO when the plan reaches it. Capping every run "
            "to the room left is the build's answer, not a ruling he gave — so it is a "
            "build choice (B20) and he can overrule it"),
    }
    storage_cap_out["headline"] = plain(
        f"The godown limit is what governs this plan. It held production back on "
        f"{storage_cap_out['days_it_bit']} of the "
        f"{storage_cap_out['working_days']} working days left, the month reaches "
        f"{storage_cap_out['month_made_pct_of_sheet']}% of the sheet, and "
        f"{storage_cap_out['products_never_made']} of the "
        f"{storage_cap_out['products_on_the_sheet']} products on the sheet are never "
        f"made at all. None of that is a machine running slowly or a bottle missing — "
        f"it is that there is nowhere to put what would be filled"
        if bit_days else
        "The godown limit caps every run to the room left in the godown, and on this "
        "run it never bit: no day was held back by it")
    storage_out = {
        "meta": dict(stamp),
        # DECLARED, not assumed. Daman ruled on 2026-09-04 that the ceiling is his own
        # capacity sheet and therefore a fact: "827,000 L godown = this is correct, no
        # guess now." Q2 is closed. The litres are untouched; only the label changed,
        # so the site badges it YOUR LIMIT instead of OUR GUESS.
        "ceiling": {
            "working_l": rules["storage_ceiling_l"],
            "peak_l": rules["storage_peak_l"],
            "declared": True,
            "declared_by": ceiling_declared_by,
            "source": plain(ceiling_source),
            "basis": rules.get("storage_ceiling_l_basis"),
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
        "cap": storage_cap_out,
        "by_day": [{"date": d["date"], "working": d["working"], **d["storage_cap"]}
                   for d in cap_days],
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

    # The ceiling is Daman's declared limit (2026-09-04) and must never drift back to a
    # guess. This is the guard on that: the flag has to be there, it has to say DECLARED,
    # it has to name who declared it, and no "open question" may ride along with it.
    _ceil = storage_out["ceiling"]
    check("the godown limit is published as declared, with who declared it",
          _ceil.get("declared") is True and bool(_ceil.get("declared_by"))
          and bool(_ceil.get("source")) and "assumed" not in _ceil
          and "open_question" not in _ceil,
          str({k: v for k, v in _ceil.items() if k != "basis"})[:160])

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

    # ---- MARK 4: the money, the machines today, the dispatch book, the stuck ---
    # R16 (a rupee figure against a floor and a target), R22 (line by line, never one
    # total), R21 (days of work in the open book and how long a bill waits, instead of
    # the trucks that left today) and R14 (drums are filled by hand, so they are not a
    # missing machine). Every figure is read from the freeze or from day 1; nothing
    # here is typed.
    money_block, dispatch_block, expected_orders_block = None, {}, {}
    lines_today, stuck, rulebook_block, day1_block = [], {}, None, None
    if rb_mode:
        d1 = days[0]
        money_in = inp.get("money") or {}
        target_rs = money_in.get("target_rs_per_day")
        floor_rs = money_in.get("floor_rs_per_day")
        money_block = {
            "today_plan_rs": round(d1["made_value"]),
            "today_booked_rs": money_in.get("today_booked_rs"),
            "today_booked_pieces": money_in.get("today_booked_pcs"),
            "mtd_made_rs": money_in.get("mtd_made_rs"),
            "mtd_days": money_in.get("mtd_days"),
            "target_rs_per_day": target_rs,
            "floor_rs_per_day": floor_rs,
            "on_target_today": bool(target_rs is not None and d1["made_value"] >= target_rs),
            "above_floor_today": bool(floor_rs is not None and d1["made_value"] >= floor_rs),
            "mtd_by_basis": money_in.get("mtd_by_basis"),
            "basis": plain("what today's filling is worth: litres on the plan times the price "
                           "each product sells for. The target and the floor are the plant's own, "
                           "read from the rulebook"),
            "booked_basis": money_in.get("today_booked_basis"),
            "mtd_basis": money_in.get("mtd_basis"),
        }
        # THE MONTH AGAINST THE FLOOR, not just today (R16/F5). `on_target_today` is a
        # statement about ONE day, and day 1 is the one day the godown limit does not
        # bite — so a green tick there sat over a month that misses the ₹2 crore floor
        # on almost every working day it has left. The floor is a daily rule; the
        # honest reading of it is how many days keep it, and how far the month lands
        # from a month of targets.
        work_days = [d for d in days if d.get("working")]
        above_floor = [d for d in work_days
                       if floor_rs is not None and float(d["made_value"]) >= floor_rs]
        on_target = [d for d in work_days
                     if target_rs is not None and float(d["made_value"]) >= target_rs]
        month_rs = round(sum(float(d["made_value"]) for d in days))
        month_target_rs = round(target_rs * len(work_days)) if target_rs is not None else None
        # THE SHEET AT THE SAME PRICES. A12's own words put the month's sheet at
        # ₹75.2 crore, and that sentence was published unqualified beside a plan worth
        # a quarter of it. The sheet's value is computable from the same table the
        # plan is valued with, so it goes out beside the plan's — measured, not quoted.
        def_rate = rules.get("default_realise_rs_per_l")
        sheet_value_rs = round(sum(float(r["litres"] or 0) * realise.get(r["code"], def_rate)
                                   for r in plan))
        money_block["month"] = {
            "sheet_rs_at_the_same_prices": sheet_value_rs,
            "sheet_rows_priced_by_default": sum(1 for r in plan if r["code"] not in realise),
            "default_rs_per_l": def_rate,
            "plan_pct_of_sheet_rs": (round(month_rs / sheet_value_rs * 100, 1)
                                     if sheet_value_rs else None),
            "plan_rs": month_rs,
            "working_days": len(work_days),
            "days_above_floor": len(above_floor),
            "days_below_floor": len(work_days) - len(above_floor),
            "days_on_target": len(on_target),
            "target_rs_if_every_working_day_hit_it": month_target_rs,
            "pct_of_a_month_of_targets": (round(month_rs / month_target_rs * 100, 1)
                                          if month_target_rs else None),
            "worst_day": (min(work_days, key=lambda d: float(d["made_value"]))["date"]
                          if work_days else None),
            "note": plain(
                f"the floor and the target are DAILY rules, and this is the whole month "
                f"against them: {len(above_floor)} of {len(work_days)} working days left "
                f"keep the floor and {len(on_target)} reach the target. Today is one day, "
                f"and it is the one day the godown still has room in it — read the month, "
                f"not the tick"
                if work_days else "no working day is left in this plan"),
        }

        night_today = d1.get("night_line") or {}
        runs_today = defaultdict(list)
        for run in d1["runs"]:
            runs_today[run["line"]].append(run)
        for line in lines_cfg:
            todays = runs_today.get(line, [])
            products = {}
            for run in todays:
                row = products.setdefault(run["code"], {
                    "code": run["code"], "sku": run["sku"], "litres": 0.0, "pieces": 0.0,
                    "hours": 0.0, "family": run.get("family"), "pref": run.get("pref"),
                    "po_backed": False})
                row["litres"] += run["litres"]
                row["pieces"] += run["pieces"]
                row["hours"] += run["hours"]
                row["po_backed"] = row["po_backed"] or bool(run.get("po_backed"))
            for row in products.values():
                row["litres"] = round(row["litres"])
                row["pieces"] = round(row["pieces"])
                row["hours"] = round(row["hours"], 2)
            lines_today.append({
                "line": line,
                "night": line == night_today.get("line"),
                "hours_planned": round((d1.get("line_hours") or {}).get(line, 0), 2),
                "hours_available": (d1.get("line_hours_max") or {}).get(line),
                "runs": len(todays),
                "pieces": round(sum(r["pieces"] for r in todays)),
                "litres": round(sum(r["litres"] for r in todays)),
                "value_rs": round(sum(r["value"] for r in todays)),
                "product_changes": (d1.get("product_changes") or {}).get(line),
                "products": sorted(products.values(), key=lambda r: -r["litres"]),
            })

        book = inp.get("dispatch_book") or {}
        lag = inp.get("lag") or {}
        pend_all, lag_med, lag_p90 = (book.get("pendency_days_all"),
                                      lag.get("median_days"), lag.get("p90_days"))
        dispatch_block = {
            "open_l_all_books": book.get("open_l_all_books"),
            "open_bills": book.get("open_bills"),
            "oil_pile_l": book.get("oil_pile_l"),
            "pendency_days_all": pend_all,
            "pendency_days_oil": book.get("pendency_days_oil"),
            "trailing_days": book.get("trailing_days"),
            "basis": book.get("basis"),
            "basis_missing": book.get("basis_missing"),
            "lag_median_days": lag_med,
            "lag_p90_days": lag_p90,
            "lag_max_days": lag.get("max_days"),
            "lag_mean_days": lag.get("mean_days"),
            "lag_rows": lag.get("rows"),
            "lag_window": lag.get("window"),
            "lag_measured_on": lag.get("measured_on"),
            "lag_static": bool(lag.get("static")),
            "lag_basis": lag.get("source"),
            "lag_caveat": lag.get("caveat"),
            "lag_by_company": lag.get("by_company"),
            # WHICH BOOK THE LAG IS. The gate is one gate carrying three companies and
            # this plan makes Oil, so the engine is fed Oil's own wait. The merged
            # all-books figure is published beside it and labelled, never instead of it.
            "lag_book": lag.get("book"),
            "lag_book_say": lag.get("book_say"),
            "lag_all_books_median_days": (lag.get("all_books") or {}).get("median_days"),
            "lag_all_books_p90_days": (lag.get("all_books") or {}).get("p90_days"),
            "lag_all_books_rows": (lag.get("all_books") or {}).get("rows"),
            "headline": plain(
                (f"the open dispatch book is {pend_all} day(s) of work at the pace the gate has "
                 f"been keeping" if pend_all is not None else
                 "the open dispatch book cannot be turned into days of work yet — no day of "
                 "gate records has been read on this box")
                + (f", and a JIVO Oil bill billed today reaches a truck in about "
                   f"{lag_med} day(s); one Oil bill in ten waits {lag_p90} or more"
                   if lag_med is not None and lag_p90 is not None
                   and lag.get("book") == "JIVO_OIL" else
                   f", and a bill billed today reaches a truck in about {lag_med} day(s); "
                   f"one bill in ten waits {lag_p90} or more"
                   if lag_med is not None and lag_p90 is not None else "")),
        }

        # THE STUCK LIST, IN THE FOUR SHAPES THE RULEBOOK ALLOWS. The meeting called
        # "no machine can fill it" the wrong framing (R14): what actually stops a
        # product is that a material is missing, that nobody has ordered it, or that
        # the machine that fills it ran out of hours — and drums are simply filled by
        # hand. Everything here is worked out from day 1 and from the order book.
        # WHAT COUNTS AS "SOMEBODY WANTS IT" IS THE CONFIRMED BOOK, NOT THE STREAM
        # (round B, item 22). It used to be every order dated on or before today —
        # and the order stream mixes real orders with the month's target dated into
        # weekly buckets (CLAUDE.md: "orders are 64% forecast"). 21 of 39 rows in
        # "somebody wants it and the machine had no hours" were put there by a FCST-*
        # row, each one carrying `ordered: false` next to a sentence saying the
        # opposite. A row nobody has actually ordered belongs in the bucket whose own
        # words are "nobody has asked for it yet — it is only in the month's target",
        # which is exactly what a forecast row is, and it is marked as one.
        # B20 — TWO KINDS OF HELD UP, AND THEY NEED DIFFERENT ANSWERS. A material row
        # is somebody's purchase order; a STORAGE row is a full godown and no order on
        # earth fixes it. Before 2026-09-06 the engine emitted no row at all when the
        # ceiling was the binder, so 11 of this run's 18 throttled days published
        # "nothing is stuck" with five machines standing idle. The rows exist now, and
        # they must not be filed under "short of something it is made from".
        blocked_today_by_code = defaultdict(list)
        storage_today_by_code = defaultdict(list)
        for block in days[0]["blocked"]:
            if block.get("reason") == "storage" or block.get("binder") == STORAGE_BINDER:
                storage_today_by_code[block["code"]].append(block)
            else:
                blocked_today_by_code[block["code"]].append(block)
        ran_today = {r["code"] for r in days[0]["runs"]}
        ordered_now, ordered_later, expected_only = set(), set(), set()
        for order in orders:
            if is_forecast(order):
                expected_only.add(order["code"])
            elif order["date"] <= h0:
                ordered_now.add(order["code"])
            else:
                ordered_later.add(order["code"])
        expected_only -= ordered_now
        ordered_later -= ordered_now
        # WHICH MACHINES WERE ACTUALLY FULL. "the machine that fills it had no hours
        # left today" was never computed: the cause was inferred from "not run and not
        # blocked", and 17 of 39 rows had Clear Pack among their machines on a day
        # Clear Pack finished with 9.5 h free. Now it is measured off day 1's own
        # hours, and the row says which machines could still have taken it.
        free_today = {line: round(max(0.0, (days[0].get("line_hours_max") or {}).get(line, 0)
                                      - (days[0].get("line_hours") or {}).get(line, 0)), 2)
                      for line in lines_cfg}

        def machines_with_room(code):
            pack = sku_pack.get(code) or {}
            prefs = eligible_lines(rb, lines_cfg, lines_multi, pack.get("slot"),
                                   pack.get("family"), int(pack.get("fills_per_piece") or 1))
            return sorted(line for line in prefs if free_today.get(line, 0) > 0.05)

        material_rows, no_order_rows, no_time_rows, storage_rows = [], [], [], []
        for row in plan:
            code = row["code"]
            if code in drum_codes:
                continue
            # THE THREE BUCKETS COUNT LITRES TWO DIFFERENT WAYS, so they are two
            # differently named fields. `want_*` is what the planner tried to fill
            # TODAY; `month_target_*` is this product's whole line on the month's
            # sheet. They were `want_litres` and `plan_litres` in one block with one
            # counts map and nothing saying they meant different things — 356,883 L of
            # day-1 want printed beside 2,329,800 L of month sheet, on a day the plant
            # makes 146,351 L. That is CLAUDE.md's "two different oil series — never
            # chart them as one line", on the front page.
            month = {"month_target_pieces": row["pieces"], "month_target_litres": row["litres"]}
            if code in blocked_today_by_code:
                blocks = blocked_today_by_code[code]
                want = max(b.get("want", 0) for b in blocks)
                material_rows.append(dict(
                    month,
                    code=code, sku=row["sku"],
                    want_pieces=round(want),
                    want_litres=round(want * row["litres_per_piece"]),
                    short_of=[{"code": b["binder"], "name": b["binder_name"]}
                              for b in blocks],
                    ordered=code in ordered_now))
                continue
            if code in storage_today_by_code and code not in ran_today:
                # A missing bottle outranks a full godown when both are true of the same
                # product: the bottle needs ordering, and it would still be missing in an
                # empty warehouse. Storage is what is left when everything else was there.
                blocks = storage_today_by_code[code]
                want = max(b.get("want", 0) for b in blocks)
                storage_rows.append(dict(
                    month,
                    code=code, sku=row["sku"],
                    want_pieces=round(want),
                    want_litres=round(want * row["litres_per_piece"]),
                    ordered=code in ordered_now,
                    machines_with_room=machines_with_room(code)))
                continue
            if code in ran_today or row["pieces"] <= 0:
                continue
            entry = dict(month, code=code, sku=row["sku"])
            if code in ordered_now:
                entry["ordered"] = True
                entry["machines_with_room"] = machines_with_room(code)
                no_time_rows.append(entry)
            else:
                entry["ordered"] = False
                entry["expected_only"] = code in expected_only
                entry["ordered_later"] = code in ordered_later
                no_order_rows.append(entry)
        for rows_ in (material_rows, no_order_rows, no_time_rows, storage_rows):
            rows_.sort(key=lambda r: -(r.get("want_litres")
                                       or r.get("month_target_litres") or 0))
        # A day that starts with the godown nearly full is capped to what can be sent
        # out, so "the machine had no hours left" would be the wrong reason on it. The
        # day says which it was, and the words change with it.
        # "the godown was full today" has to mean it STOPPED something today, not that
        # it opened nearly full. Day 1 opens with room, fills it, and stops twenty
        # products — the old test read False on exactly the day the reader needs it.
        _d1_cap = days[0].get("storage_cap") or {}
        godown_full_today = bool(
            _d1_cap.get("stopped_products") or _d1_cap.get("capped_runs")
            or any(e.get("kind") == "STORAGE_THROTTLE" and e.get("day") == h0
                   for e in events))
        # counted here so the bucket's own sentence and its own counts cannot disagree
        n_later = sum(1 for r in no_order_rows if r.get("ordered_later"))
        n_expected = sum(1 for r in no_order_rows if r.get("expected_only"))
        room_left = [r for r in no_time_rows if r["machines_with_room"]]
        stuck = {
            "material": material_rows,
            "storage": storage_rows,
            "no_order": no_order_rows,
            "no_line_time": no_time_rows,
            "manual": manual_fill,
            "godown_full_today": godown_full_today,
            "definitions": {
                "material": plain("the planner tried to fill it today and something it is made "
                                  "from ran out. The litres beside it are what it tried to fill "
                                  "TODAY"),
                "storage": plain(
                    "the planner tried to fill it today, the machine had hours and the material "
                    "was there — and there was no room left in the godown to put it. The godown "
                    "holds 827,000 L and it is full of goods that are already sold and waiting "
                    "for a truck, so nothing more can be made until something leaves the gate. "
                    "No purchase order fixes this one. The litres beside it are what the planner "
                    "tried to fill TODAY"),
                # "NOBODY HAS ASKED FOR IT" WAS NOT TRUE OF EVERY ROW IN IT. The bucket
                # holds two kinds: nobody has ordered it at all, and somebody HAS ordered
                # it — for a day that has not come yet. The second kind was counted
                # (`no_order_wanted_later`) and then flatly contradicted by the sentence
                # above the rows. Both are named now, and the sentence is written from
                # the rows it sits over.
                "no_order": plain(
                    ("nobody has asked for it TODAY — it is in the month's target, and the "
                     "litres beside it are that whole month's line, not today's want"
                     if n_later else
                     "nobody has asked for it yet — it is only in the month's target, and "
                     "the litres beside it are that whole month's line, not today's want")
                    + (f". {n_later} of these {'is' if n_later == 1 else 'are'} really "
                       f"ordered, just for a later day — nobody is waiting on "
                       f"{'it' if n_later == 1 else 'them'} yet, so "
                       f"{'it is' if n_later == 1 else 'they are'} marked and not counted "
                       f"as unwanted" if n_later else "")
                    + (f". {n_expected} of them nobody has ordered at all — they are only "
                       f"expected" if n_expected else "")),
                "no_line_time": plain(
                    "somebody has really ordered it and the plan did not get to it today"
                    + (f" — {len(room_left)} of them had a machine with hours to spare, so on "
                       f"those it was the running order that left them out, not the hours"
                       if room_left else " — every machine that can fill them was full")
                    + (". The godown was also too full to fill more than can be sent out"
                       if godown_full_today else "")
                    + ". The litres beside it are that product's whole month on the sheet"),
                "manual": (rb.get("drums") or {}).get("display"),
            },
            # THE HEADING IS DATA TOO. The front page carried "The machine had no hours
            # left" in hand-typed JSX above a bucket whose own definition says most of
            # those products HAD a machine with hours to spare — the heading said one
            # thing and the sentence under it said the opposite. It is written here,
            # from the same rows the definition is written from, so the two cannot
            # disagree again.
            "headings": {
                "material": "Short of something it is made from",
                "storage": "The godown was too full to put it anywhere",
                "no_order": ("Nobody has asked for it today" if n_later
                             else "Nobody has asked for it"),
                "no_line_time": ("Ordered, and the plan did not get to it" if room_left
                                 else "Every machine that can fill it was full"),
                "manual": "Filled by hand",
            },
            "counts": {"material": len(material_rows), "storage": len(storage_rows),
                       "no_order": len(no_order_rows),
                       "no_line_time": len(no_time_rows), "manual": len(manual_fill),
                       # inside no_order: nobody has ordered it AT ALL, versus somebody
                       # has ordered it for a later day. Inside no_line_time: how many
                       # had a machine with hours to spare.
                       "no_order_expected_only": n_expected,
                       "no_order_wanted_later": n_later,
                       "no_line_time_with_a_free_machine": len(room_left)},
            "hours_free_today": free_today,
            "litres_note": plain("two different counts sit in this block and they are named "
                                 "apart: what the planner tried to fill today, and the whole "
                                 "month's line off the sheet. Never add them together"),
        }

        expected_orders_block = {
            "present": bool(baseline.get("present")),
            "used": bool(baseline.get("used_for_forecast")),
            "window": baseline.get("window"),
            "months": baseline.get("months"),
            "share_of_demand_pct": demand["forecast_share_litres_pct"],
            "fallback_reason": baseline.get("fallback_reason"),
            "fetched_at": baseline.get("fetched_at"),
            "source": baseline.get("source"),
            "note": plain("what customers are likely to ask for, worked out from what the trade "
                          "really bought over the last few months — read once a day into a file, "
                          "never inside this loop"),
        }
        if baseline.get("age_days") is not None:
            expected_orders_block["age_days"] = baseline["age_days"]
        # A NIGHT SESSION IS A ROSTER; THE HOURS ARE THE WORK. Both go out, and the
        # sentence leads with the hours — "22 second sessions" reads to a plant manager
        # as 22 crews to staff, and this run's night work is measured in hours, not
        # shifts. `night_sessions_worked` is how many of the opened ones filled anything.
        _n_open = summary_rb.get("night_sessions") or 0
        _n_worked = summary_rb.get("night_sessions_worked") or 0
        _n_hours = summary_rb.get("night_hours_used") or 0
        rulebook_block = {"version": rb.get("version"), "written": rb.get("written"),
                          "owner": rb.get("owner"), "applied": summary_rb.get("applied"),
                          "hours_per_session": summary_rb.get("hours_per_session"),
                          "night_sessions": _n_open,
                          "night_sessions_worked": _n_worked,
                          "night_hours_used": _n_hours,
                          "night_litres": summary_rb.get("night_litres"),
                          "night_say": plain(
                              f"{_n_hours:g} hour(s) of second-shift work in the whole of "
                              f"the rest of the month, on {_n_worked} night(s). A second "
                              f"session is opened only where a machine has work it can "
                              f"still put somewhere"
                              if _n_worked else
                              "no machine works a second shift in the rest of this month — "
                              "there is nowhere to put what a night would fill")}
        day1_block = {"date": d1["date"], "weekday": d1["weekday"], "working": d1["working"]}
        check_demand_baseline(check, rb, baseline, honesty.get("assumed"),
                              bool(baseline.get("used_for_forecast")))

    # ---- honesty -------------------------------------------------------------
    bad_rate_phrase = "of rated, the observed rate"
    assumed = [a for a in honesty.get("assumed", []) if bad_rate_phrase not in a]
    assumed.append(rate_note)
    check("no line still says the wrong thing about machine speeds",
          not any(bad_rate_phrase in a for a in honesty.get("assumed", [])),
          str([a for a in honesty.get("assumed", []) if bad_rate_phrase in a][:2]))
    # The godown limit was on this list until 2026-09-04, and everything the site badges
    # OUR GUESS is read off it. It is a declared fact now, so it must not be here.
    _ceil_guesses = [a for a in assumed
                     if "godown ceiling" in a.lower() or "storage ceiling" in a.lower()]
    check("the godown limit is not listed as one of our guesses",
          not _ceil_guesses, str(_ceil_guesses[:2]))
    # The August backtest is the site's one claim to be believed, so it may not come
    # from a file the engine rewrites on every run. It comes from a pinned artefact,
    # and its absence is a broken checkout, not a number to quietly drop. Whether the
    # artefact is still REPRODUCIBLE is a warning, not a gate: the live loop runs every
    # three minutes and must not go dark because somebody edited the engine.
    check("the August backtest comes from the pinned measurement, not from a working file",
          august is not None,
          "reference/august-calibration.json is missing — run python3 engine/calibrate_august.py")

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

    history_out = build_history(inp, meta, stamp, check)
    hist_meta = history_out["meta"]
    hist_days = len(history_out["days"])

    label_rules = [
        {"id": "rolling-replan", "rule": plain(
            "only today is live. The days before it are records read off the factory's own systems — "
            "what was filled and what left the gate. Every later day is worked out by the computer "
            "from today's count plus what the plan decides, and re-worked every few minutes"),
         "as_of": meta["as_of"], "days_left": len(days), "days_gone": hist_days},
        {"id": "happened-days", "rule": plain(
            "the days already gone are records, not the plan: two ways of counting what was filled "
            "are shown side by side, both labelled, and never added together"),
         "through": hist_meta["through"], "days": hist_days,
         "status": hist_meta["status"], "not_read": len(history_out["missing_dates"]),
         "source": prov.get("history")},
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
        {"id": "ceiling-declared", "rule": plain(ceiling_source),
         "working_l": rules["storage_ceiling_l"], "peak_l": rules["storage_peak_l"],
         "declared": True, "declared_by": ceiling_declared_by},
        {"id": "standing-measured", "rule": pile_note,
         "billed_not_gone_l": opening["standing_l"],
         "pct_of_ceiling": round(opening["standing_l"] / rules["storage_ceiling_l"] * 100, 1)},
        {"id": "day1-pile", "rule": plain(
            "the pile of orders on day 1 is real, not a fault — it is the live order book as it stands "
            "right now."), "source": prov.get("orders")},
        {"id": "realise-outlier", "rule": plain(
            "FG0000155's selling price per litre is an odd inherited figure, far from its own order "
            "book — never show it as a headline without saying so."), "detail": outlier},
        {"id": "numbers-masked", "rule": plain(
            "no real phone number anywhere on this site — none is written into the data at all.")},
        {"id": "tank-dip", "rule": plain(
            "bulk oil comes from the tank yard's own daily readings, taken by hand — not a meter, and "
            "not always today's."), "source": prov.get("opening_oil")},
    ]

    # A label the site prints beside a number is a promise about that number, so the
    # Mark 4 ones are added here and the Mark 3 ones that would now be WRONG are not
    # printed at all. "observed, then derated again" describes a plan that multiplies
    # by rules.efficiency; Mark 4's speeds already carry the cut and the engine
    # multiplies by 1.0, so the old label would say the opposite of what happened.
    if rb_mode:
        label_rules += [
            {"id": "speed-planning", "rule": rate_note,
             "planning_factor": planning_factor,
             "min_runs_for_cap": (rb.get("efficiency") or {}).get("min_runs_for_cap"),
             "sustained_hours": sustained_h,
             "efficiency": eff},
            {"id": "night-line", "rule": plain(
                "one machine, and only one, runs a second shift each day. The plan names it and "
                "says why it was picked — the plant can overrule it."),
             "line": (days[0].get("night_line") or {}).get("line"),
             "reason": (days[0].get("night_line") or {}).get("reason"),
             "outcome": (days[0].get("night_line") or {}).get("outcome"),
             "hours_used_today": (days[0].get("night_line") or {}).get("hours_used"),
             "nights_in_this_run": summary_rb.get("night_sessions"),
             "nights_that_worked": summary_rb.get("night_sessions_worked"),
             "night_hours_in_this_run": summary_rb.get("night_hours_used")},
            {"id": "dispatch-pendency", "rule": plain(
                "the dispatch headline is how many days of work sit in the open book at the pace "
                "the gate has been keeping, and how long a bill takes to reach it — not what "
                "left today."),
             "pendency_days_all": dispatch_block.get("pendency_days_all"),
             "lag_median_days": dispatch_block.get("lag_median_days"),
             "lag_p90_days": dispatch_block.get("lag_p90_days"),
             "lag_static": dispatch_block.get("lag_static")},
            {"id": "money-target", "rule": plain(
                "the day is measured in rupees of goods filled, against the plant's own floor "
                "and target — both read from the rulebook, neither typed."),
             "target_rs_per_day": (money_block or {}).get("target_rs_per_day"),
             "floor_rs_per_day": (money_block or {}).get("floor_rs_per_day"),
             "basis": (rb.get("money") or {}).get("basis")},
            {"id": "manual-fill", "rule": plain(
                "the drums are filled by hand and are not put on any machine — show them as "
                "that, never as a machine that is missing."),
             "codes": sorted(u["code"] for u in manual_fill),
             "display": (rb.get("drums") or {}).get("display")},
            {"id": "expected-orders-basis", "rule": plain(
                "orders nobody has placed yet are worked out from what the trade really bought "
                "over the last few months — read once a day, never inside this loop, and marked "
                "three ways wherever they appear."),
             "present": expected_orders_block.get("present"),
             "used": expected_orders_block.get("used"),
             "window": expected_orders_block.get("window"),
             "months": expected_orders_block.get("months"),
             "fallback_reason": expected_orders_block.get("fallback_reason")},
        ]
    else:
        label_rules.append({"id": "observed-then-derated", "rule": rate_note,
                            "efficiency": eff, "measured_slots": measured_slots})
    if no_machine:
        label_rules.append({"id": "unproducible", "rule": plain(
            f"{len(no_machine)} products in this month's target have no machine (nothing fills "
            f"{no_machine_for}) — show them on the Stock and Order by when pages, do not hide them."),
            "codes": [u["code"] for u in no_machine]})

    measured = list(honesty.get("measured", []))
    if hist_meta["status"] != "unavailable" and hist_days:
        measured.append(plain(
            f"the {hist_days} day(s) of this month already gone, to {dm(hist_meta['through'])} "
            f"— records read off the factory's own systems, not the plan"))

    honesty_out = {
        "meta": dict(stamp),
        "forward_rule": meta["rule"],
        "measured": measured,
        "assumed": assumed,
        "provenance": prov,
        "warnings": warnings,
        "label_rules": label_rules,
        "august_calibration": {
            "sim_made_l": august and august["sim_made_l"],
            "actual_made_l": august and august["actual_made_l"],
            "delta_pct": august and august["delta_pct"],
            "measured_on": august and august["measured_on"],
            "reproducible": bool(august and august["reproducible"]),
            "changed_since_measured": (august or {}).get("changed_since_measured") or [],
            "source": "reference/august-calibration.json (engine/calibrate_august.py)",
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
        # THE GODOWN IS NOT PACKAGING (B20). The storage binder falls through
        # item_kind as "OTHER" and landed in `other_packaging` — 20 attempts filed
        # under a bottle nobody is short of, on a page whose whole job is to say what
        # to go and buy. There is nothing to buy here and it gets its own class.
        if code == STORAGE_BINDER:
            return "godown_full"
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
                            for k in ("oil", "zero_stock_packaging", "other_packaging",
                                      "godown_full")},
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
        # THE OLD SENTENCE ENDED "On a day the godown is full nothing is tried at all,
        # and this is zero" — which described the bug, not the plant. The planner DID
        # try; the engine dropped the run without a row, and eleven days of this run
        # published "nothing is stuck" with five machines standing idle. A full godown
        # is a reason now (B20) and it is counted like any other.
        "note": plain(
            "'attempts' = how many times the planner tried and was stopped, not how many products — "
            "quote products. One product can be short of oil and packing at once, so the per-type "
            "counts can overlap. A full godown is one of the reasons: the machine had the hours and "
            "the material was there, and there was nowhere to put what it would fill"),
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
    check_stuck_counts(check, spine, day1_blocked)

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
            "ceiling_declared": True,
            "ceiling_declared_by": ceiling_declared_by,
            "invoice_truck_lag_days": lag_days,
            "invoice_truck_lag_book": rules.get("invoice_truck_lag_book"),
            "days_ge_95": storage_out["days_ge_95"],
            "days_ge_100": storage_out["days_ge_100"],
            "throttle_events": len(storage_out["throttles"]),
            "pct_at_open": open_pct,
        },
        # B20 ON THE FRONT PAGE. This is the rule that makes this plan — it throttles
        # most of the month and it is why two thirds of the sheet is not made — so it
        # goes where the first thing Gurvinder reads is, not three pages in.
        "storage_cap": storage_cap_out,
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

    if rb_mode:
        overview.update({
            "rulebook": rulebook_block,
            "day1": day1_block,
            "money": money_block,
            "lines_today": lines_today,
            "night_line": days[0].get("night_line"),
            "dispatch": dispatch_block,
            "stuck": stuck,
            "manual_fill": manual_fill,
            "manual_fill_note": (rb.get("drums") or {}).get("display"),
            "expected_orders": expected_orders_block,
        })
        overview["plan"].update({
            "sheet_skus": sum(1 for p in plan if p["pieces"] > 0),
            "expected_only_skus": sum(1 for p in plan if p["pieces"] <= 0),
        })
        # The warnings stay. AC09 bans the COUNT OF TRUCKS THAT LEFT TODAY, not the
        # word — see TRUCKS_KEY_RE above — so a warning about EXIM tankers on the way
        # no longer refuses the cycle, and this file no longer has to drop a channel
        # to get past its own check. honesty.json still carries them in full and is
        # what the site's footer reads; the count and the pointer stay here because
        # the front page is where somebody notices there are any.
        overview["warnings_count"] = len(warnings)
        overview["warnings_where"] = plain("the things the planner wants you to know before "
                                           "quoting a number are on the honesty file, in full")
        check_overview(check, overview)
        # the same rule over the files the SITE reads, not just the ones the engine
        # wrote: a day page that cannot say which machine is on tonight is a day page
        # that lost it between here and there.
        no_night = [d["date"] for d in details
                    if not isinstance(d.get("night_line"), dict)
                    or not d["night_line"].get("reason")]
        check("every day the site shows names the machine that runs at night, and why",
              not no_night, str(no_night[:4]), ac="AC04")

    # ---- MARK 4: plan/assumptions.json — what this plan takes as fact --------
    # R26: every guess on its own page, with the data it was made from and what would
    # change it. This is the file Mark 4 exists for — the meeting's rulings, the
    # guesses filling the gaps between them, the choices made while building it, the
    # speed table, the eligibility matrix, how fresh every input is, the acceptance
    # list with a pass flag, and the questions Gurvinder has not answered yet.
    #
    # TEXT FROM THE RULEBOOK IS COPIED VERBATIM and never goes through plain(): it is
    # Daman's and Gurvinder's own wording, written for them, and the floor-word scan
    # would refuse half of it. Only sentences AUTHORED here are registered, and they
    # are written in floor words.
    assumptions = None
    if rb_mode:
        questions_rel = ((rb.get("sources") or {}).get("questions_for_gurvinder")
                         or "out/QUESTIONS-FOR-GURVINDER.md")
        questions_path = os.path.join(JOLLY, questions_rel)
        questions_text = ""
        if os.path.exists(questions_path):
            with open(questions_path, encoding="utf-8") as fh:
                questions_text = fh.read()
        check("the questions for Gurvinder are in this checkout, where the rulebook says",
              bool(questions_text), f"{questions_rel} is not there", ac="AC10")
        # He answers by editing that file, and question 14 asks for phone numbers. The
        # answers are masked BEFORE they are published — with the live feed's own
        # masker, plus the wider ten-digit net this document can afford (it has no
        # legitimate ten-digit identifier in it) — and check_assumptions then scans
        # what came out. `Ravi.9876543210` published clean through the old door.
        questions = mask_questions(parse_questions(questions_text))

        runs_all = [r for d in days for r in d["runs"]]
        fam_runs = Counter(r.get("family") for r in runs_all)
        tin_head_days = sum(1 for d in days if (d.get("line_hours") or {}).get("Tin Head", 0) > 0)
        small_packs = sorted(c for c, v in sku_pack.items() if v.get("family") == "SMALL")
        speeds_by_kind = Counter(r["rate_basis"] for r in speed_rows)
        no_evidence = plain("nothing on this cycle turned this one on or off — the plan is "
                            "shaped by it either way")
        # WHAT `in_effect` MEANS, published beside it (round B, item 26). It was
        # carrying three different meanings on one page with no definition anywhere:
        # "this really did not happen" (A18, honest), "the rule is live in the
        # eligibility table but nothing exercised it this cycle" (A04) and "we did not
        # look". The middle one is None now — the branch below already existed for it —
        # so a `false` on this page means the first thing and only the first thing.
        in_effect_means = {
            "true": plain("this cycle's plan really leans on it — the line beside it is what "
                          "this run did that shows it"),
            "false": plain("it did not happen on this cycle at all, and the line beside it "
                           "says what happened instead"),
            "null": plain("the plan is built on it either way, and nothing on this cycle "
                          "turned it on or off"),
        }
        # A16 NAMES ITS OWN PRODUCTS, so the page can check itself against them instead
        # of counting a family. It published `in_effect: true` with a note saying
        # thirteen products and listing six codes, against an assumption about three
        # named ones — a note that falsifies the sentence it sits under.
        a16 = next((r for r in (rb.get("assumed") or []) if r["id"] == "A16"), {})
        a16_named = sorted(set(re.findall(
            r"FG\d{7}", f"{a16.get('assumption', '')} {a16.get('why', '')}")))
        a16_missing = [c for c in a16_named if c not in small_packs]
        a16_extra = [c for c in small_packs if c not in a16_named]
        tin_head_3l5l_derived = sum(
            1 for r in speed_rows
            if r["line"] == "Tin Head" and r["slot"] in ("3L", "5L")
            and (r.get("planning_rule") or {}).get("kind") == "derived")
        # …and how many times the plan ACTUALLY ran one. The count above is the speed
        # table; this is the work. A15/A05 are verdicts about what this run did.
        tin_head_3l5l_runs = sum(1 for r in runs_all
                                 if r.get("line") == "Tin Head" and r.get("slot") in ("3L", "5L"))
        working_days = sum(1 for d in days if d["working"])

        def only_if(saw, note):
            """True with the evidence, or None when nothing this cycle exercised it.
            Never False — a rule that is live in the tables and simply did not come up
            has not been falsified, and saying so on a page a person reads as a verdict
            is how A04 came to say the eligibility table was off."""
            return (True, note) if saw else (None, no_evidence)
        # what this run can actually SAY about each guess, beside what the freeze
        # already reported. Anything not here is published with no claim rather than
        # with a flag nobody measured.
        seen = {
            "A02": only_if(fam_runs.get("SMALL", 0) > 0,
                    plain(f"{fam_runs.get('SMALL', 0)} run(s) filled a pack under a litre at the "
                          f"1-litre pace; {len(small_packs)} product(s) are classed that way")),
            "A03": only_if(sum(v for k, v in fam_runs.items() if k not in (None, "ANY")) > 0,
                    plain("every run this cycle was placed by the bottle its recipe names: "
                          + ", ".join(f"{k} {v}" for k, v in sorted(fam_runs.items())
                                      if k is not None))),
            # the eligibility table carries the rule whether or not a 3 L tin came up
            "A04": only_if(any(r.get("slot") == "3L" and r.get("family") == "TIN" for r in runs_all),
                    plain(f"{sum(1 for r in runs_all if r.get('slot') == '3L' and r.get('family') == 'TIN')}"
                          f" run(s) of 3-litre tins in this plan")),
            # A05 is about the TIN HEAD's own small tins, so it is read off the Tin
            # Head's rows and not off every derived speed on the site. AND OFF ITS
            # RUNS, not off its speed table: a row in the table is only the rate the
            # plan WOULD use, and it is there on every cycle whatever the plan does.
            # This run put the Tin Head on 15 L and nothing else, so the plan does not
            # lean on the guess at all and the badge must not say it does.
            "A05": only_if(tin_head_3l5l_runs > 0,
                    plain(f"the Tin Head's 3-litre and 5-litre speeds are the same tins an hour as "
                          f"its 15-litre speed, and this plan uses them: {tin_head_3l5l_runs} "
                          f"run(s) of 3- or 5-litre tins on it")),
            # AVAILABLE every working day is the assumption; how many days it is GIVEN
            # WORK is a different number, and the note used to quote the second one
            # against the first ("given work on 5 of 22") as if it agreed with it.
            "A06": (True,
                    plain(f"the plan treats the Tin Head as free to run on all "
                          f"{working_days} working day(s) and gives it work on "
                          f"{tin_head_days} of them")),
            # A SESSION OPENED IS NOT A NIGHT'S WORK, and this line used to quote the
            # roster count on its own — "22 night session(s)" against 10.5 hours of
            # actual work. `in_effect` now needs a night that WORKED, and the hours
            # lead the sentence.
            "A07": only_if((summary_rb.get("night_sessions_worked") or 0) > 0,
                    plain(f"{summary_rb.get('night_hours_used')} hour(s) of second-shift "
                          f"work on {summary_rb.get('night_sessions_worked')} night(s), "
                          f"{summary_rb.get('night_sessions')} second session(s) opened in "
                          f"all — each named with the reason its machine was picked")),
            "A08": (True,
                    plain(f"every change of product costs {rules['line_clearance_min']} minutes and "
                          f"every change of oil throws away {round(rules['flush_litres'])} litres; "
                          f"{sum(d['flushes'] for d in days)} oil change(s) in this plan")),
            "A11": (bool(summary_rb.get("dispatch_on_sunday")),
                    plain("orders keep being filled from stock on a Sunday, and trucks keep "
                          "leaving; nothing is put on a machine")),
            # A12's own text values the WHOLE month's sheet, and that sentence was
            # published on its own beside a plan worth a fraction of it — a reader
            # took the sheet's rupees for the plan's. The note now says what this run
            # is worth against it, and how the month sits against R16's daily floor.
            "A12": (True,
                    plain("what the plan is worth is litres times the price each product sells "
                          "for — the same table the last plan used. This run's whole month "
                          f"comes to {money_block['month']['plan_rs']:,} rupees against the "
                          f"{money_block['month']['sheet_rs_at_the_same_prices']:,} the month's "
                          f"sheet is worth at those same prices "
                          f"({money_block['month']['plan_pct_of_sheet_rs']}% of it), and "
                          f"{money_block['month']['days_below_floor']} of the "
                          f"{money_block['month']['working_days']} working days left fall "
                          f"under the daily floor R16 sets")),
            "A13": only_if(fam_runs.get("75G", 0) > 0 and not any(
                        r.get("line") == "JP Machine" and r.get("family") == "75G"
                        for r in runs_all),
                    plain(f"{fam_runs.get('75G', 0)} run(s) of the 75-gram bottle, none of "
                          f"them on JP")),
            "A14": (True,
                    plain("no 40-gram bottle ran on JP and no 75-gram or 26-gram bottle ran on "
                          "Clear Pack — refused by a check on this run")),
            # THE SPEED TABLE IS NOT THE PLAN. This tested `speed_rows` — a row in the
            # 10 Head's speed table for 3 L, which is there on every single cycle
            # whatever the plan does — and so wore a green "in effect" badge on a run
            # with ZERO 3-litre runs anywhere. The page's own words for `true` are
            # "this cycle's plan really leans on it", so the test is the runs, and a
            # cycle that never fills a 3-litre bottle gets `null` and says so (A04 was
            # fixed this way; this is the same fix one line down).
            "A15": only_if(any(r.get("line") == "10 Head" and r.get("slot") == "3L"
                               for r in runs_all),
                    plain(f"{sum(1 for r in runs_all if r.get('line') == '10 Head' and r.get('slot') == '3L')}"
                          f" run(s) of 3-litre bottles on the 10 Head, at its 5-litre speed")),
            # A LIST THAT SAYS TEN AND SHOWS SIX MUST SAY IT IS SHOWING SIX. `[:6]` was
            # printed straight after `len(a16_extra)`, with nothing between them: the
            # sentence promised ten codes and named six, and the four missing ones read
            # as codes the reader had failed to spot. The full list rides beside the
            # sentence in `a16_products` so nothing is actually withheld.
            "A16": (not a16_missing,
                    plain(f"the {len(a16_named)} product(s) this names have no bottle in their "
                          f"recipe and are filled in the 1-litre slot"
                          + (f"; {len(a16_extra)} more are classed the same way and are not "
                             f"named in it: {', '.join(a16_extra[:6])}"
                             + (f" and {len(a16_extra) - 6} more — all of them are listed "
                                f"under a16_products on this page"
                                if len(a16_extra) > 6 else "")
                             if a16_extra else "")
                          + (f". {', '.join(a16_missing)} is not classed that way at all"
                             if a16_missing else ""))),
        }
        applied = inp.get("rulebook_applied") or {}
        assumed_rows = []
        for row in rb.get("assumed") or []:
            fact = applied.get(row["id"])
            if fact is not None:
                in_effect, note = fact.get("in_effect"), fact.get("note")
            elif row["id"] in seen:
                in_effect, note = seen[row["id"]]
            else:
                in_effect, note = None, no_evidence
            assumed_rows.append(dict(row, in_effect=in_effect, in_effect_note=note))

        speeds_out = []
        for line, spec in (rb.get("lines") or {}).items():
            for slot, block in sorted((spec.get("speeds") or {}).items()):
                speeds_out.append({
                    "line": line, "slot": slot, "set_of_two": False,
                    "rated": block.get("rated"), "aug_median": block.get("aug_median"),
                    "aug_best": block.get("aug_best"), "aug_runs": block.get("aug_runs"),
                    "planning": block.get("planning"), "basis": block.get("planning_basis"),
                    "basis_kind": (block.get("planning_rule") or {}).get("kind"),
                    "used_by_the_plan": (lines_cfg.get(line) or {}).get(slot) is not None,
                })
            for slot, block in sorted((spec.get("speeds_multi") or {}).items()):
                speeds_out.append({
                    "line": line, "slot": slot, "set_of_two": True,
                    "rated": block.get("rated"), "aug_median": block.get("aug_median"),
                    "aug_best": block.get("aug_best"), "aug_runs": block.get("aug_runs"),
                    "planning": block.get("planning"), "basis": block.get("planning_basis"),
                    "basis_kind": (block.get("planning_rule") or {}).get("kind"),
                    "used_by_the_plan": (lines_multi.get(line) or {}).get(slot) is not None,
                })

        lag_in = inp.get("lag") or {}
        fresh_expected = {"present": bool(baseline.get("present")),
                          "fetched_at": baseline.get("fetched_at"),
                          "window": baseline.get("window"),
                          "mode": baseline.get("mode")}
        if baseline.get("age_days") is not None:
            fresh_expected["age_days"] = baseline["age_days"]
        assumptions = {
            "meta": dict(stamp,
                         rulebook_version=rb.get("version"),
                         rulebook_written=rb.get("written"),
                         rulebook_owner=rb.get("owner"),
                         rulebook_sources=rb.get("sources"),
                         note=plain("what this plan takes as fact: what the plant has settled, "
                                    "what the computer has filled in for itself, and what is "
                                    "still a question for Gurvinder")),
            # THE FREEZE COMPUTES A VERDICT ON THE SETTLED RULINGS TOO, and this line
            # used to throw them away. `rulebook_applied` carries R16 and R21 with a
            # note apiece — whether the money floor and the daily-measured lag really
            # governed THIS run — computed every cycle by live/freeze_live.py, and no
            # settled ruling on the page ever said whether the run honoured it. The
            # assumptions get `in_effect` (above) and the rulings did not, on a page
            # whose whole job is "why it says that". Same mechanism, same words: a
            # ruling nothing this cycle exercised gets null, never a false.
            "settled": [dict(r, **({"in_effect": (applied[r["id"]] or {}).get("in_effect"),
                                    "in_effect_note": (applied[r["id"]] or {}).get("note")}
                                   if r["id"] in applied else
                                   {"in_effect": None, "in_effect_note": no_evidence}))
                        for r in rb.get("settled") or []],
            "assumed": assumed_rows,
            "build_choices": [dict(r) for r in rb.get("build_choices") or []],
            "speeds": speeds_out,
            "eligibility": [{"line": line, "slot": slot, "families": dict(fams),
                             "has_a_speed": (lines_cfg.get(line) or {}).get(slot) is not None}
                            for line, spec in (rb.get("lines") or {}).items()
                            for slot, fams in sorted((spec.get("slots") or {}).items())],
            "excluded_lines": rb.get("excluded_lines"),
            "sheet_disagrees": [{"code": code, "sku": v.get("sku"),
                                 "sheet_pack_type": v.get("sheet_pack_type"),
                                 "container_name": v.get("container_name"),
                                 "slot": v.get("slot"), "family": v.get("family")}
                                for code, v in sorted(sku_pack.items())
                                if v.get("sheet_disagrees")],
            "in_effect_means": in_effect_means,
            # A16 in full: the products it names, the ones classed the same way that it
            # does not name, and any it names that are not classed that way. The note
            # above shows the first few of the middle list; this is all of it.
            "a16_products": {"named_in_the_rule": a16_named,
                             "classed_the_same_way_and_not_named": a16_extra,
                             "named_but_not_classed_that_way": a16_missing},
            "open_questions": questions,
            "open_questions_source": questions_rel,
            "open_questions_convention": plain(
                "he answers by writing a line starting Answer: under a question in that file — "
                "that is the whole of it, and this page reads it every cycle"),
            "this_run": {
                "assumed": assumed,
                "warnings": warnings,
                "prefs_used": summary_rb.get("prefs_used"),
                "product_changes": summary_rb.get("product_changes"),
                "product_changes_by_line": summary_rb.get("product_changes_by_line"),
                "second_change_allowed": summary_rb.get("change_cap_lifted"),
                "second_change_allowed_more_than_once": summary_rb.get(
                    "change_cap_lifted_twice_or_more"),
                "night_sessions": summary_rb.get("night_sessions"),
                "night_sessions_worked": summary_rb.get("night_sessions_worked"),
                "night_hours_used": summary_rb.get("night_hours_used"),
                "night_hours_rostered": summary_rb.get("night_hours_rostered"),
                "night_litres": summary_rb.get("night_litres"),
                "filled_by_hand": sorted(u["code"] for u in manual_fill),
                # B20 — the biggest hand on this sheet, with this run's own arithmetic
                # beside the choice. The choice text says what the cap IS; this says
                # what it DID, so the page cannot carry the rule without the damage.
                "storage_cap": storage_cap_out,
            },
            "fallbacks": {
                "expected_orders": {
                    "used": bool(baseline.get("used_for_forecast")),
                    "reason": baseline.get("fallback_reason"),
                    "instead": plain("the month's target, split into weeks, is used when the "
                                     "trade's own buying could not be read"),
                },
                "lag": {
                    "measured_daily": not bool(lag_in.get("static")),
                    "source": lag_in.get("source"),
                    "measured_on": lag_in.get("measured_on"),
                    "instead": plain("a single measurement taken once, in September, is used "
                                     "when the daily one is missing"),
                },
                "night_line": {
                    "line": (days[0].get("night_line") or {}).get("line"),
                    "reason": (days[0].get("night_line") or {}).get("reason"),
                    "candidates": (days[0].get("night_line") or {}).get("candidates"),
                    "instead": plain("with nothing ordered left to fill, the machine with the "
                                     "most work of any kind behind it takes the night"),
                },
            },
            "freshness": {
                "rulebook_written": rb.get("written"),
                "questions_file": questions_rel,
                "questions_file_read_at": (
                    datetime.fromtimestamp(os.path.getmtime(questions_path),
                                           timezone.utc).astimezone().isoformat(timespec="seconds")
                    if os.path.exists(questions_path) else None),
                "state_collected_at": stamp["collected_at"],
                "expected_orders_file": fresh_expected,
                "lag_file": {"measured_on": lag_in.get("measured_on"),
                             "measured_once": bool(lag_in.get("static")),
                             "window": lag_in.get("window"),
                             "rows": lag_in.get("rows")},
                "history_through": hist_meta["through"],
            },
            "preference_semantics": rb.get("preference_semantics"),
            "drums": rb.get("drums"),
            "acceptance": [],
        }
        check_assumptions(check, rb, assumptions, questions_text)

    outputs = {
        "overview.json": overview,
        "spine.json": spine,
        "storage.json": storage_out,
        "materials.json": materials_out,
        "loops.json": loops_out,
        "honesty.json": honesty_out,
        "lines.json": lines_out,
        "history.json": history_out,
    }
    if assumptions is not None:
        # The acceptance list is written LAST, after every check that carries an id has
        # run, so the flag beside each line is this run's own result and not a promise.
        # The scans below are the only checks after it — and a failed scan writes
        # nothing at all, so a published file is one that passed them too.
        rows = []
        for text in (rb.get("acceptance_checks") or []):
            ac = text[:4]
            mine = check.by_ac.get(ac) or []
            # AC11 and AC12 ARE NOT THIS FILE'S TO PASS (round B, item 21). AC11 reads
            # "gen cross-checks pass; `next build` passes; fixtures synced; every
            # existing Mark 3 route still renders" — this file touched the first
            # clause and none of the other three, and it was publishing
            # `checked_here: true, passed: true` against all four off two checks that
            # happen to carry the id. AC12 is the whole chain end to end. Both now say
            # what they really are, and still say how many of this file's checks stood
            # near them.
            # AC10 IS THE SAME SHAPE, ONE LINE UP. Four clauses, two of them the
            # site's — so the whole line is not this file's to pass either, and it
            # says which clause is whose instead of one flag over all four.
            elsewhere = CHECKED_ELSEWHERE_CLAUSES.get(ac) or {}
            clauses = []
            for clause in split_clauses(text):
                hit = next((v for k, v in elsewhere.items() if k in clause), None)
                whole_elsewhere, by = hit if hit else (False, None)
                clauses.append({
                    "clause": clause,
                    "checked_here": hit is None,
                    "checked_here_in_part": bool(hit) and not whole_elsewhere,
                    "verdict_by": by or "this file, as it was built"})
            check(f"{ac}'s clauses are still the ones the rulebook writes",
                  all(any(k in c["clause"] for c in clauses) for k in elsewhere),
                  f"{sorted(k for k in elsewhere if not any(k in c['clause'] for c in clauses))} "
                  f"is not in {ac} any more", ac=ac)
            part = bool(elsewhere) and any(c["checked_here"] for c in clauses)
            here = bool(mine) and ac not in CHECKED_ELSEWHERE and not elsewhere
            rows.append({"id": ac, "text": text, "checked_here": here,
                         "checked_here_in_part": part,
                         "passed": (all(mine) if here else None),
                         "passed_here": (all(mine) if (here or part) and mine else None),
                         "checks": len(mine),
                         "clauses": clauses,
                         "verdict_by": (
                             "this file, as it was built" if here
                             else CHECKED_ELSEWHERE[ac] if ac in CHECKED_ELSEWHERE
                             else "part of this line only — see the clauses beside it")})
        assumptions["acceptance"] = rows
        assumptions["acceptance_note"] = plain(
            "a line marked passed had every one of its checks run while this file was "
            "being built, and every one of them passed. It can never say failed: one "
            "failure and nothing is written at all, and the last good plan keeps being "
            "served — so read it as this plan would not be in front of you if that line "
            "had failed, and read the number beside it as how many checks stood behind "
            "it. The last two are finished outside this file: one by the site's own "
            "build, one by running the whole chain end to end")
        outputs["assumptions.json"] = assumptions
    for i, detail in enumerate(details):
        outputs[os.path.join("days", f"day-{i + 1:02d}.json")] = detail

    # ---- the scans, over what is actually about to be written ----------------
    for name, obj in outputs.items():
        scan_no_phones(check, name, obj)
        # history.json is the one file where a null quantity is the honest answer;
        # overview.json and honesty.json carry the live dispatch reads. Everywhere
        # else — the day files above all — a null quantity is still a fault.
        scan_numbers(check, name, obj, null_ok=(
            HISTORY_NULL_OK if name == "history.json" else
            DISPATCH_NULL_OK if name in ("overview.json", "honesty.json") else None))
    for name in ("overview.json", "storage.json", "materials.json", "loops.json",
                 "honesty.json", "lines.json", "history.json") + (
                     ("assumptions.json",) if assumptions is not None else ()):
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
        "history": {"days": hist_days, "through": hist_meta["through"],
                    "status": hist_meta["status"], "mode": hist_meta["records_mode"],
                    "not_read": len(history_out["missing_dates"]),
                    "trimmed": len(history_out["trimmed_dates"])},
        "august": honesty_out["august_calibration"], "recon": recon,
        "rulebook": ({
            "version": rb.get("version"),
            "night_line": (days[0].get("night_line") or {}).get("line"),
            "night_sessions": summary_rb.get("night_sessions"),
            "night_sessions_worked": summary_rb.get("night_sessions_worked"),
            "night_hours_used": summary_rb.get("night_hours_used"),
            "today_plan_rs": (money_block or {}).get("today_plan_rs"),
            "target_rs_per_day": (money_block or {}).get("target_rs_per_day"),
            "floor_rs_per_day": (money_block or {}).get("floor_rs_per_day"),
            "pendency_days_all": dispatch_block.get("pendency_days_all"),
            "lag_median_days": dispatch_block.get("lag_median_days"),
            "lag_p90_days": dispatch_block.get("lag_p90_days"),
            "manual": [u["code"] for u in manual_fill],
            "questions": Counter(q["status"] for q in (assumptions or {}).get("open_questions", [])),
            "stuck": (stuck or {}).get("counts"),
        } if rb_mode else None),
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
    rbs = stats.get("rulebook")
    if rbs:
        print(f"  rulebook {rbs['version']} · tonight's second shift: "
              f"{rbs['night_line'] or 'none'} ({rbs['night_sessions']} night(s) opened in this "
              f"run, {rbs['night_sessions_worked']} worked, {rbs['night_hours_used']} h in all)"
              f" · filled by hand: {', '.join(rbs['manual']) or 'none'}")
        print(f"  today Rs {(rbs['today_plan_rs'] or 0) / 1e7:.2f} Cr against a target of "
              f"Rs {(rbs['target_rs_per_day'] or 0) / 1e7:.2f} Cr and a floor of "
              f"Rs {(rbs['floor_rs_per_day'] or 0) / 1e7:.2f} Cr")
        # each of these is honestly null on a box with no gate records yet, and the
        # published headline says so in words — so the operator line says it too
        # rather than printing "None day(s)".
        print("  dispatch book: "
              + (f"{rbs['pendency_days_all']} day(s) of work"
                 if rbs['pendency_days_all'] is not None else
                 "no day of gate records read on this box yet")
              + " · " + (f"a bill reaches a gate in {rbs['lag_median_days']} day(s), one in "
                         f"ten in {rbs['lag_p90_days']}"
                         if rbs['lag_median_days'] is not None else
                         "the bill-to-gate wait has not been measured on this box yet"))
        print("  held up: " + " · ".join(f"{k.replace('_', ' ')} {v}"
                                         for k, v in (rbs["stuck"] or {}).items()))
        print(f"  questions for Gurvinder: {rbs['questions'].get('open', 0)} open, "
              f"{rbs['questions'].get('answered', 0)} answered")
    hist = stats["history"]
    print(f"  days already gone: {hist['days']} to {hist['through']} ({hist['status']}, "
          f"read {hist['mode']})"
          + (f" · {hist['not_read']} not read" if hist["not_read"] else "")
          + (f" · {hist['trimmed']} dropped as today or later" if hist["trimmed"] else ""))
    if aug["sim_made_l"] is None:
        print("  August check: NOT MEASURED on this checkout — run python3 engine/calibrate_august.py")
    else:
        print(f"  August check: plan {aug['sim_made_l']:,} L vs actual {aug['actual_made_l']:,} L "
              f"({aug['delta_pct']}%) · measured {aug['measured_on']}"
              + ("" if aug["reproducible"] else
                 " · NOT REPRODUCIBLE, " + ", ".join(aug["changed_since_measured"]) + " has changed"))
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
