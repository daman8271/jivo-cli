#!/usr/bin/env python3
"""
live/adapters/factory_history.py — ji.jivo.in, the DAYS ALREADY GONE this month.
JIVO_OIL for production, all three books for the gate. No SAP call, ever.

Mark 3's other adapters read the plant's position NOW; freeze_live then plans
the days ahead from it. Nothing anywhere read the days between the 1st of the
month and yesterday, so the site could show a month with its first four days
simply absent. This adapter fills exactly that gap and nothing else: one record
per elapsed day, read off the factory's own systems.

    fetch(hourly=False) -> {source, fetched_at, server_at, ok, error, data}
    python3 -m live.adapters.factory_history [--hourly] [--full]

WHY IT IS ITS OWN ADAPTER, not a block inside factory_production
    * factory_production's hourly phase is already budgeted to 172 s of the
      loop's 175 s cap; a month read does not fit beside it.
    * One `ok` per source. A history page that fails must not mark the plant's
      LIVE position failed — freeze_live would then tag every live stock block
      `live-partial` and write "half-failed this cycle" into honesty.assumed
      over a problem with a record from four days ago.
    * Its records are hours old by design. Sharing factory_production's stamp
      would print "as of 15:04" over a reading of the 1st.

CADENCE AND THE SETTLED CACHE
    Read on the HOURLY slot only. On every other cycle the cached block is
    republished verbatim with `from_cache: true` and ZERO CLI calls — except on
    a cold box with no cache, or after midnight when the cache still says
    yesterday was today, where it reads for real inside BUDGET_S.

    A day is SETTLED once it is SETTLE_AFTER_DAYS old and every read of it came
    back whole. Settled days are never re-read; unsettled ones are re-read every
    hour. That is not an optimisation — yesterday's figures genuinely keep
    moving: a goods receipt posts 0-1 day after the filling it books, and a
    segment left open by an operator reports 0 cases until they close it.

    Cold start mid-month: the budget stops the read part-way, the days it did
    reach settle, and the next hourly cycle carries on. Unread days are named in
    `missing_dates` — never published as a zero day.

CALLS
    per unsettled day : 2   (reports-daily-production, reports-production-movement)
    per cycle, once   : 1-N gate pages (gate-core sales-dispatch, --page paged)
    steady state      : 2 days x 2 + 1-2 gate pages ~ 3-4 s
    cold, whole month : capped by BUDGET_S (60 s), the rest left for next hour

=============================================================================
data — EVERY KEY AND ITS UNIT
=============================================================================
company        str   "JIVO_OIL" — the production half. The gate half reads all
                     three books and splits them; Oil is always stated on its own.
month          str   "2026-09", the month these records belong to.
through        str   the last elapsed date, YYYY-MM-DD, or "—" on the 1st.
today          str   the plant's today. NO record for it — that is the live
                     adapters' day, and reading it here would double it.
status         str   complete | partial | unavailable.
from_cache     bool  true = republished, no CLI call this cycle.
read_at        str   when the records on this block were actually read.
days           list  one row per elapsed day, oldest first (below).
missing_dates  list  elapsed dates with NO record at all — "not read", never 0.
undated_dispatched_rows int  gate rows that were DISPATCHED but carried no
                     parseable date, so they are in no day's figure.
basis          dict  one plain sentence per figure — what it counts and does not.
notes          list  caveats the site must be able to surface.
calls          list  every CLI call: {name, args, ok, seconds, error, data_source}.
cli_path       str   which binary answered (Mac and Linux builds sit side by side).

A DAY ROW. Every figure is null when its read failed — NEVER 0. A zero day and
an unread day look identical otherwise, and only one of them is a fact.
  date, day_of_month, weekday   str/int/str
  working                bool  false on a Sunday. The record is NOT zeroed to
                              match: a Sunday the plant filled shows what it filled.
  made_mes_l             float LITRES per the machine log (closed segments only).
  made_mes_cases         float CASES, same source.
  runs                   int   production runs dated that day.
  open_segments          int   segments still open on those runs — each one
                              reports 0 cases, so made_mes_* is a FLOOR.
  made_booked_l          float LITRES booked into BH-PF as goods receipts.
  made_booked_pcs        float PIECES, same receipts.
  booked_receipts        int   goods-receipt LINES.
  booked_unparsed_pcs    float PIECES whose pack size did not parse from the
                              item name and so added 0 L.
  booked_truncated       bool  the --limit page filled: every booked figure is a FLOOR.
  booked_by_item         dict  {item_code: pieces} — Phase 2's input (netting the
                              plan by what is already made). Not published to the site.
  billed_out_l           float LITRES invoiced OUT of BH-PF (TransType 13, AR Invoice).
  billed_out_pcs         float PIECES, same lines.
  billed_lines           int   invoice lines.
  billed_unparsed_pcs    float PIECES that did not parse to litres.
  dispatched_oil_l       float LITRES that left the gate on JIVO_OIL rows.
  dispatched_all_l       float LITRES that left the gate on ALL THREE books.
  trucks_oil / trucks_all int  trucks, de-duplicated on the vehicle (3 Sep: the
                              same plate appears once per company).
  rows_oil               int   Oil gate rows.
  bills_oil              int   documents named on those rows.
  by_company             dict  the gate split per book. Not published to the site.
  settled                bool  this row is final and will not be re-read.
  complete               bool  every read behind this row came back whole.
  read_at                str   when THIS row was read.
  notes                  list  what was incomplete about this row, in words.

=============================================================================
CAVEATS — each one has already cost somebody a wrong answer
=============================================================================
1. TWO WAYS OF COUNTING THE SAME PRODUCTION, NEVER ADDED. made_mes_* is the
   machine log and sees ~two-thirds of the plant; made_booked_* is the goods
   receipt into BH-PF and is the fuller figure. They are the same oil counted
   twice. Nothing in this file ever sums them, and gen_live.py refuses to write
   a history file that contains a key merging them.
2. THE RECEIPT DATE IS NOT THE FILLING DATE. A goods receipt posts 0-1 day
   after the run it books, so made_booked_l on a given day is what was BOOKED
   that day. Yesterday's figure moves for up to 48 hours — that is why a day
   settles only after two.
3. BILLED OUT IS A FLOOR. Only BH-PF is read (the room the live tile reads) and
   litres come from parsing the pack size out of the item name. BH-BT is not
   read at all. Never compare it to the plan's billed litres as an equal.
4. THE GATE IS THREE COMPANIES. 3 Sep 2026: 47,182 L "dispatched" was 89%
   Beverages. Oil is stated on its own on every row; the merged figure never
   travels without it.
5. NO IDENTIFIERS LEAVE THIS FILE. Vehicles are counted, never named; documents
   are counted, never numbered; no driver field is read at all. The cache file
   sits in live/state/ and state_server.py serves every *.json in there over
   plain HTTPS.
6. DATES ARE PARSED, NEVER SLICED. The movement endpoint returns a naive
   plant-local "2026-09-04T00:00:00"; the gate mixes Z and +05:30 for the same
   instant. `elapsed` is computed in IST.
7. AN ANSWER NOBODY CAN READ IS NOT AN EMPTY DAY. Every body is checked against
   the shape it is supposed to have (a list of runs, a page with a `data` list,
   a gate page) BEFORE it is counted. An exit-0 answer in an unknown shape is
   published as unread — nulls, a note, `ok:false` and the shape named in
   `error` — never as zeros. Counting it as zero is the one failure mode that
   would settle a whole month at nothing and cache it: ok:true, status
   "complete", every downstream check satisfied, and a page of empty bars
   badged HAPPENED with nobody to notice.
8. NOTHING TO READ IS A SUCCESS. On the 1st there is no elapsed day, so there
   is no call: `days: []`, `status: "complete"`, `ok: true`. It is cached like
   any other answer so the other nineteen cycles an hour stay free.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_LIVE_DIR = os.path.dirname(_HERE)                       # …/jolly/live
_JOLLY = os.path.dirname(_LIVE_DIR)                      # …/jolly


def _sibling(name):
    """Import a sibling adapter the way collect.py imports _mask: by package
    name first, then straight off disk. Standalone runs (`python3
    live/adapters/factory_history.py`) have no `live` package on the path."""
    try:
        return importlib.import_module("live.adapters." + name)
    except Exception:                                    # noqa: BLE001
        spec = importlib.util.spec_from_file_location(
            "_mark3_" + name, os.path.join(_HERE, name + ".py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)                     # type: ignore[union-attr]
        return mod


if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)

_prod = _sibling("factory_production")
_disp = _sibling("factory_dispatch")

# The production half — one CLI runner, the run-row maths and the goods-receipt
# reader, all reused rather than re-derived. `_run_row` in particular carries
# the "app's pieces_per_case x litres_per_piece WINS over the name" rule that a
# second implementation would get wrong by a factor of ten.
_cli = _prod._cli
_CallLog = _prod._CallLog
_day_rows = _prod._day_rows
_totals = _prod._totals
_booked = _prod._booked
_results = _prod._results
_num = _prod._num
_int = _prod._int
pack_litres = _prod.pack_litres
GOODS_RECEIPT_TRANSTYPE = _prod.GOODS_RECEIPT_TRANSTYPE
MES_COVERAGE_NOTE = _prod.MES_COVERAGE_NOTE
GR_LAG_NOTE = _prod.GR_LAG_NOTE

# The gate half — a different CLI runner with --all-companies in its base flags.
_run = _disp._run
_parse_ts = _disp._parse_ts
_parse_date = _disp._parse_date
COMPANIES = _disp.COMPANIES

SOURCE = "factory_history"
COMPANY = "JIVO_OIL"
IST = timezone(timedelta(hours=5, minutes=30), "IST")

STATE_DIR = os.environ.get("MARK3_STATE_DIR") or os.path.join(_LIVE_DIR, "state")
CACHE_FILE = os.path.join(STATE_DIR, "factory_history.month.json")

# A day is final once it is this old AND every read of it came back whole.
# Two days, not one: the goods receipt lags the filling by 0-1 day, and a
# segment an operator left open yesterday still reports 0 cases today.
SETTLE_AFTER_DAYS = 2

# Wall clock for the WHOLE read. Steady state is 2 days x 2 calls plus a gate
# page or two; this only ever bites on a cold box reading a month from scratch,
# where it stops part-way ON PURPOSE and the next hourly cycle carries on.
BUDGET_S = int(os.environ.get("MARK3_HISTORY_BUDGET_S") or 60)
DAY_CALL_TIMEOUT_S = 16
GATE_CALL_TIMEOUT_S = 40
GATE_PAGE_SIZE = 100
GATE_MAX_PAGES = 12
# The gate window is padded two days to the LEFT of the oldest day wanted: a
# truck docked on the 31st and gated out on the 1st must land whichever date the
# server filters on. Which one it filters on is unverified; the pad covers both.
GATE_PAD_DAYS = 2
MOVEMENT_LIMIT = 1000
AR_INVOICE_TRANSTYPE = 13

FULL = os.environ.get("MARK3_HISTORY_FULL") == "1"

# Bumped whenever a reader change makes an older cache untrustworthy. A settled
# day is kept for the rest of the month, so a month cached by a reader that
# counted an unrecognised answer as zero would go on being served all month with
# nobody to notice. A bump costs one full re-read on the first cycle after a
# deploy; not bumping costs a month of wrong records.
#   1 -> the first release
#   2 -> an exit-0 answer in an unknown shape is unread, not zero (2026-09-05)
CACHE_READER = 2

BILLED_NOTE = (
    "A/R invoice lines going OUT of BH-PF only, litres from the pack size in the item "
    "name. A FLOOR: BH-BT is not read here, and a name that does not parse adds 0 L."
)
GATE_NOTE = (
    "gate rows with status DISPATCHED, all three books, placed on the day of their "
    "gate-out date. Oil is the JIVO_OIL rows only; trucks are de-duplicated on the "
    "vehicle, which appears once per company."
)
SETTLE_NOTE = (
    "a day is read again every hour until it is %d days old and every read of it came "
    "back whole; after that it is kept as it stands." % SETTLE_AFTER_DAYS
)
SUNDAY_NOTE = (
    "a Sunday is a closed day, but its record is never zeroed to match — if the plant "
    "filled anything it is shown."
)
TWO_BASES_NOTE = (
    "the machine log and the goods receipts are the same production counted two ways — "
    "never add them together."
)


# ------------------------------------------------------------------- cache --
def _write_cache(obj):
    """Best effort. A cache-write failure must never take the adapter down."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        tmp = CACHE_FILE + ".tmp.%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, default=str)
        os.replace(tmp, CACHE_FILE)
    except OSError:
        pass


def _load_cache(month):
    """The settled-day cache for THIS month, or None.

    A cache that is unparseable, half-written, the WRONG SHAPE, from another
    month or written by an OLDER READER is ignored — the caller then does the
    real read. Same rule as EXIM's slow cache: a blob nobody can prove THIS
    adapter wrote is never served.
    """
    try:
        with open(CACHE_FILE, encoding="utf-8") as fh:
            blob = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(blob, dict) or blob.get("month") != month:
        return None
    if blob.get("reader") != CACHE_READER:
        return None
    if not isinstance(blob.get("days"), dict) or not isinstance(blob.get("settled"), dict):
        return None
    if not isinstance(blob.get("data"), dict):
        return None
    return blob


# ------------------------------------------------------------------ pieces --
def _billed(payload):
    """A/R invoice lines OUT of BH-PF, off the SAME movement payload the goods
    receipts come from. Litres are parsed from the item name, so unparsed pieces
    are counted and reported rather than silently dropped."""
    res = _results(payload)
    empty = {"litres": 0.0, "pcs": 0.0, "lines": 0, "litres_unparsed_pcs": 0.0}
    if not isinstance(res, dict):
        return empty
    rows = res.get("data") or []
    lines, pcs, litres, unparsed = 0, 0.0, 0.0, 0.0
    for row in rows:
        if str(row.get("direction") or "").upper() != "OUT":
            continue
        is_invoice = (_int(row.get("transaction_type")) == AR_INVOICE_TRANSTYPE
                      or str(row.get("transaction_label") or "").strip().lower() == "ar invoice")
        if not is_invoice:
            continue
        qty = _num(row.get("out_qty"))
        if qty <= 0:
            continue
        per_piece, _how = pack_litres(row.get("item_name") or "")
        lines += 1
        pcs += qty
        if per_piece:
            litres += qty * float(per_piece)
        else:
            unparsed += qty
    return {"litres": round(litres, 3), "pcs": round(pcs, 3), "lines": lines,
            "litres_unparsed_pcs": round(unparsed, 3)}


def _inner(payload):
    """Step past the CLI's own {meta, results} wrapper, if it is there."""
    if isinstance(payload, dict) and isinstance(payload.get("meta"), dict) and "results" in payload:
        return payload["results"]
    return payload


def _shape_of(payload):
    """A short description of a body this reader does not recognise — its type
    and its top-level FIELD NAMES, never any of its contents. It is published in
    `error`, so it must be safe to read on a public page."""
    node = _inner(payload)
    if isinstance(node, dict):
        keys = sorted(str(k) for k in node)[:6]
        return "an object with keys %s" % (", ".join(keys) if keys else "(none)")
    if isinstance(node, list):
        return "a list"
    return "a %s" % type(node).__name__


def _is_run_list(payload):
    """True only when the body is what reports-daily-production returns: a LIST
    of runs (empty is a real answer — no run was dated that day)."""
    return isinstance(_inner(payload), list)


def _is_movement_page(payload):
    """True only when the body is what reports-production-movement returns: an
    object carrying a `data` LIST of movement rows (empty is a real answer)."""
    res = _inner(payload)
    return isinstance(res, dict) and isinstance(res.get("data"), list)


def _gate_page(payload):
    """(rows, paging, recognised) out of whatever shape --page came back as.

    Sending --page SWITCHES this endpoint from a bare array to an envelope, and
    the CLI wraps that envelope in its own {meta, results}. VERIFIED live
    2026-09-05, and it is NOT the DRF shape the reference doc implies: the inner
    envelope is {count, num_pages, page, page_size, results} — there is no
    `next` link at all. So paging is driven off page/num_pages, `next` is only
    honoured if a future version starts sending one, and a bare array (no
    envelope) falls back to "a full page is the only evidence of a cut-off".

    `recognised` is False when the body is NEITHER — an exit-0 answer this
    reader cannot read. That is not "no truck left the gate": returning an empty
    list for it is what would publish a whole month of settled zeros.
    """
    node = _inner(payload)
    if isinstance(node, list):
        return node, {}, True
    if isinstance(node, dict):
        for key in ("results", "data", "rows", "cards"):
            if isinstance(node.get(key), list):
                return node[key], {"next": node.get("next"),
                                   "page": node.get("page"),
                                   "num_pages": node.get("num_pages"),
                                   "count": node.get("count")}, True
    return [], {}, False


def _blank_gate():
    return {
        "dispatched_oil_l": 0.0, "dispatched_all_l": 0.0,
        "trucks_oil": set(), "trucks_all": set(),
        "rows_oil": 0, "bills_oil": 0,
        "by_company": {code: {"litres": 0.0, "rows": 0, "bills": 0, "boxes": 0.0,
                              "trucks": set()} for code in COMPANIES},
    }


def _finish_gate(bucket):
    """Turn the working sets into counts. NO plate ever leaves this function."""
    out = {
        "dispatched_oil_l": round(bucket["dispatched_oil_l"], 1),
        "dispatched_all_l": round(bucket["dispatched_all_l"], 1),
        "trucks_oil": len(bucket["trucks_oil"]),
        "trucks_all": len(bucket["trucks_all"]),
        "rows_oil": bucket["rows_oil"],
        "bills_oil": bucket["bills_oil"],
        "by_company": {},
    }
    for code, slot in bucket["by_company"].items():
        out["by_company"][code] = {
            "litres": round(float(slot["litres"]), 1),
            "rows": slot["rows"],
            "bills": slot["bills"],
            "boxes": round(float(slot["boxes"]), 1),
            "trucks": len(slot["trucks"]),
        }
    return out


def _read_gate(calls, errors, unreadable, wanted, today, deadline):
    """Gate rows for `wanted` (a set of dates), bucketed by gate-out date.

    Returns (by_date, complete, undated). `complete` is False the moment a page
    fails, comes back in a shape this reader does not know, the budget runs out
    or the page cap is hit — a short read must never be published as a whole day.
    `unreadable` collects the pages that answered in an unknown shape, so the
    envelope can report ok:false over an exit-0 answer nobody could read.
    """
    if not wanted:
        return {}, True, 0
    lo = min(wanted) - timedelta(days=GATE_PAD_DAYS)
    hi = max(wanted)
    by_date, undated, complete = {}, 0, True
    page = 1
    while page <= GATE_MAX_PAGES:
        if time.monotonic() > deadline:
            errors.append("gate: budget spent after page %d" % (page - 1))
            complete = False
            break
        payload, record = _run(
            "gate_p%d" % page,
            ["gate-core", "sales-dispatch",
             "--from-date", lo.isoformat(), "--to-date", hi.isoformat(),
             "--all-companies", "1", "--page", str(page),
             "--page-size", str(GATE_PAGE_SIZE)],
            timeout=GATE_CALL_TIMEOUT_S,
        )
        calls.append({"name": record["name"], "args": record["args"], "ok": record["ok"],
                      "seconds": round((record.get("ms") or 0) / 1000.0, 3),
                      "error": record.get("error"), "data_source": None})
        if payload is None:
            errors.append("gate page %d: %s" % (page, record.get("error")))
            complete = False
            break

        rows, paging, recognised = _gate_page(payload)
        if not recognised:
            # Exit 0, valid JSON, and not a gate answer. Reading it as "no rows"
            # would settle every day in the window at zero and cache that for the
            # rest of the month — the one failure this adapter must never have.
            errors.append("gate page %d: the answer was %s, not a list of gate rows"
                          % (page, _shape_of(payload)))
            unreadable.append("gate page %d" % page)
            complete = False
            break

        for row in rows:
            if str(row.get("status") or "") != "DISPATCHED":
                continue
            day = _parse_date(row.get("gate_out_date"))
            if day is None:
                stamp = _parse_ts(row.get("dispatched_at"))
                day = stamp.astimezone(IST).date() if stamp else None
            if day is None:
                undated += 1
                continue
            if day not in wanted or day >= today:
                continue                    # today's rows belong to factory_dispatch
            bucket = by_date.setdefault(day, _blank_gate())
            company = row.get("company_code") or "UNKNOWN"
            vehicle = (row.get("vehicle_no") or row.get("vehicle_number") or "").strip()
            litres = _num(row.get("total_litres"))
            boxes = _num(row.get("total_boxes"))
            bills = len(row.get("document_numbers") or []) or (1 if row.get("sap_doc_num") else 0)

            slot = bucket["by_company"].setdefault(
                company, {"litres": 0.0, "rows": 0, "bills": 0, "boxes": 0.0, "trucks": set()})
            slot["litres"] += litres
            slot["rows"] += 1
            slot["bills"] += bills
            slot["boxes"] += boxes
            # Litres are per company row, so they are summed straight. Trucks are
            # NOT: the same plate comes back once per company on this endpoint.
            bucket["dispatched_all_l"] += litres
            if vehicle:
                slot["trucks"].add(vehicle)
                bucket["trucks_all"].add(vehicle)
            if company == COMPANY:
                bucket["dispatched_oil_l"] += litres
                bucket["rows_oil"] += 1
                bucket["bills_oil"] += bills
                if vehicle:
                    bucket["trucks_oil"].add(vehicle)

        num_pages = _int(paging.get("num_pages"), 0)
        if num_pages:
            if page >= num_pages:
                break
        elif paging.get("next"):
            pass                        # a future DRF-shaped envelope
        else:
            # No envelope at all: the CLI answered with a bare array, and a FULL
            # page is then the only evidence the window was cut off. Say so
            # rather than assume the day was read whole.
            if len(rows) >= GATE_PAGE_SIZE:
                errors.append("gate page %d came back full and the answer carries no "
                              "page count — the window may be cut off" % page)
                complete = False
            break
        page += 1
    else:
        errors.append("gate: stopped at the %d-page cap" % GATE_MAX_PAGES)
        complete = False

    return {d: _finish_gate(b) for d, b in by_date.items()}, complete, undated


# -------------------------------------------------------------- the contract --
def fetch(hourly: bool = False) -> dict:
    now = datetime.now(IST)
    today = now.date()
    first = today.replace(day=1)
    month = today.strftime("%Y-%m")
    elapsed = [first + timedelta(days=i) for i in range((today - first).days)]

    cache = None if FULL else _load_cache(month)

    # ---- republish, no CLI call ------------------------------------------
    # Only when the cache was built for THIS day: past midnight IST yesterday
    # becomes an elapsed day with no record, and a plan file missing a day it
    # is supposed to account for is refused downstream.
    if not hourly and cache and (cache["data"] or {}).get("today") == today.isoformat():
        data = dict(cache["data"])
        data["from_cache"] = True
        # The read's OWN verdict is replayed, not a fresh ok:true. Republishing
        # a half-failed read as a clean one would launder it: the failure would
        # show for one cycle an hour and be hidden for the other nineteen.
        # (A cache written before this field existed reads as the old ok:true.)
        cached_ok = cache.get("ok")
        return {
            "source": SOURCE,
            "fetched_at": cache.get("read_at") or now.isoformat(timespec="seconds"),
            "server_at": None,
            "ok": True if cached_ok is None else bool(cached_ok),
            "error": cache.get("error"),
            "data": data,
        }

    settled = dict((cache or {}).get("settled") or {})
    cached_days = dict((cache or {}).get("days") or {})
    known = {d: row for d, row in cached_days.items() if d in {x.isoformat() for x in elapsed}}

    # Newest first: yesterday is the day somebody actually wants, and it is also
    # the one the budget must never be the reason we skipped.
    unsettled = [d for d in elapsed if d.isoformat() not in settled]
    unsettled.sort(reverse=True)

    calls = _CallLog()
    errors: list = []
    # Exit-0 answers this reader could not recognise. They are NOT failures the
    # call log knows about — the CLI returned 0 and valid JSON — so they are
    # tracked here and they take `ok` down with them. Without this an endpoint
    # that changes shape publishes a settled month of zeros.
    unreadable: list = []
    deadline = time.monotonic() + BUDGET_S

    # ---- the gate, once for the whole window -----------------------------
    gate_by_date, gate_complete, undated = _read_gate(
        calls, errors, unreadable, set(unsettled), today, deadline)

    # ---- production, two calls a day -------------------------------------
    read_days = []
    for day in unsettled:
        if time.monotonic() > deadline:
            errors.append("stopped at the %ds budget with %d day(s) unread"
                          % (BUDGET_S, len(unsettled) - len(read_days)))
            break
        iso = day.isoformat()
        notes: list = []

        p_daily, e = _cli(calls, "daily_%s" % iso, "production-execution",
                          "reports-daily-production", "--date", iso,
                          timeout=DAY_CALL_TIMEOUT_S)
        if e:
            errors.append(e)
        # An answer with exit 0 that is not a run list is an UNREAD day, not an
        # idle one. Dropping it here keeps every "0" below meaning zero.
        daily_unreadable = e is None and not _is_run_list(p_daily)
        if daily_unreadable:
            errors.append("daily %s: the answer was %s, not a list of runs"
                          % (iso, _shape_of(p_daily)))
            unreadable.append("daily %s" % iso)
            p_daily = None

        p_move, e = _cli(calls, "movement_%s" % iso, "production-execution",
                         "reports-production-movement", "--date-from", iso,
                         "--date-to", iso, "--warehouse", "BH-PF",
                         "--limit", str(MOVEMENT_LIMIT), timeout=DAY_CALL_TIMEOUT_S)
        if e:
            errors.append(e)
        move_unreadable = e is None and not _is_movement_page(p_move)
        if move_unreadable:
            errors.append("movement %s: the answer was %s, not a page of godown movements"
                          % (iso, _shape_of(p_move)))
            unreadable.append("movement %s" % iso)
            p_move = None

        if p_daily is not None:
            rows = _day_rows(p_daily, {})
            made_l, made_cases = _totals(rows)
            runs = len(rows)
            open_segments = sum(int(r["open_segments"]) for r in rows)
            if open_segments:
                notes.append("%d run segment(s) were still open, so the machine-log "
                             "litres for this day are a floor" % open_segments)
        else:
            made_l = made_cases = runs = open_segments = None
            notes.append("the machine log for this day came back in a shape this reader "
                         "does not know, so nothing was counted from it" if daily_unreadable
                         else "the machine log for this day did not come back")

        if p_move is not None:
            booked, _flow = _booked(p_move)
            billed = _billed(p_move)
            if booked["truncated"]:
                notes.append("the movement page filled up, so what was booked into the "
                             "godown on this day is a floor")
            if booked["litres_unparsed_pcs"]:
                notes.append("some booked pieces have no pack size in their name and "
                             "added no litres")
        else:
            booked = billed = None
            notes.append("the godown movement for this day came back in a shape this reader "
                         "does not know, so nothing was counted from it" if move_unreadable
                         else "the godown movement for this day did not come back")

        # A gate bucket absent from a COMPLETE read is a real zero — the window
        # was read to the end and no truck left that day. Absent from an
        # INCOMPLETE read is UNKNOWN, and null is the only honest answer.
        gate = gate_by_date.get(day)
        if gate is None:
            if gate_complete:
                gate = _finish_gate(_blank_gate())
            else:
                notes.append("the gate log for this day was not read to the end")
        elif not gate_complete:
            # rows DID land on this day before the read broke off — what left the
            # gate is a floor, and the row must say so, not carry an empty notes list
            notes.append("the gate log was not read to the end, so what left the gate "
                         "on this day is a floor")

        whole = (p_daily is not None and p_move is not None
                 and gate_complete and open_segments == 0
                 and bool(booked) and not booked["truncated"])
        is_settled = whole and (today - day).days >= SETTLE_AFTER_DAYS

        row = {
            "date": iso,
            "day_of_month": day.day,
            "weekday": day.strftime("%A"),
            "working": day.weekday() != 6,
            "made_mes_l": made_l,
            "made_mes_cases": made_cases,
            "runs": runs,
            "open_segments": open_segments,
            "made_booked_l": booked["litres"] if booked else None,
            "made_booked_pcs": booked["pcs"] if booked else None,
            "booked_receipts": booked["receipts"] if booked else None,
            "booked_unparsed_pcs": booked["litres_unparsed_pcs"] if booked else None,
            "booked_truncated": booked["truncated"] if booked else None,
            "booked_by_item": ({c: v["pcs"] for c, v in booked["by_item"].items()}
                               if booked else None),
            "billed_out_l": billed["litres"] if billed else None,
            "billed_out_pcs": billed["pcs"] if billed else None,
            "billed_lines": billed["lines"] if billed else None,
            "billed_unparsed_pcs": billed["litres_unparsed_pcs"] if billed else None,
            "dispatched_oil_l": (gate or {}).get("dispatched_oil_l"),
            "dispatched_all_l": (gate or {}).get("dispatched_all_l"),
            "trucks_oil": (gate or {}).get("trucks_oil"),
            "trucks_all": (gate or {}).get("trucks_all"),
            "rows_oil": (gate or {}).get("rows_oil"),
            "bills_oil": (gate or {}).get("bills_oil"),
            "by_company": (gate or {}).get("by_company"),
            "settled": bool(is_settled),
            "complete": bool(whole),
            "read_at": now.isoformat(timespec="seconds"),
            "notes": notes,
        }
        # A row with NOTHING behind it is not a record — it is an unread day, and
        # it belongs in missing_dates where the site says "not read". A day whose
        # production reads failed but whose gate window WAS read to the end still
        # has a fact in it (nothing left the gate), so it stays a row with nulls
        # where the reads failed; the site draws a null as "not read", not as a
        # bar of height zero.
        if p_daily is None and p_move is None and gate is None:
            read_days.append(day)
            continue
        known[iso] = row
        if is_settled:
            settled[iso] = row["read_at"]
        read_days.append(day)

    days_out = [known[d.isoformat()] for d in elapsed if d.isoformat() in known]
    missing = [d.isoformat() for d in elapsed if d.isoformat() not in known]
    status = ("complete" if days_out and not missing and all(r["complete"] for r in days_out)
              else "unavailable" if not days_out and elapsed
              else "complete" if not elapsed else "partial")

    notes = [TWO_BASES_NOTE, MES_COVERAGE_NOTE, GR_LAG_NOTE, SUNDAY_NOTE]
    if missing:
        notes.append("no record was read for %s — that is UNKNOWN, not a day the plant "
                     "did nothing" % ", ".join(missing))
    if undated:
        notes.append("%d gate row(s) went out with no date on them and are in no day's "
                     "figure" % undated)

    data = {
        "company": COMPANY,
        "month": month,
        "through": elapsed[-1].isoformat() if elapsed else "—",
        "today": today.isoformat(),
        "status": status,
        "from_cache": False,
        "read_at": now.isoformat(timespec="seconds"),
        "days": days_out,
        "missing_dates": missing,
        "undated_dispatched_rows": undated,
        "basis": {
            "made_mes": MES_COVERAGE_NOTE,
            "made_booked": GR_LAG_NOTE + " Read out of BH-PF only — the same room the "
                                         "live 'booked today' tile reads.",
            "billed_out": BILLED_NOTE,
            "dispatched": GATE_NOTE,
            "sunday": SUNDAY_NOTE,
            "settling": SETTLE_NOTE,
        },
        "notes": notes,
        "cli_path": _prod.CLI,
        "calls": list(calls),
    }

    # On the 1st of the month there is nothing to read, so there is no call to
    # judge: an empty answer is the RIGHT answer and must report ok. Reporting
    # ok:false there made collect.py count a working source as failed and
    # freeze_live write "half-failed this cycle" onto the honesty panel, with an
    # empty reason, on every cycle of every 1st.
    ok = (all(c["ok"] for c in calls) and not unreadable
          and (bool(calls) or not elapsed))
    error = "; ".join(errors) if errors else None

    # Cache what was actually read — and cache the empty month too, or the 1st
    # repeats the whole read every three minutes all day. A cycle that reached
    # for something and got nothing must never overwrite a good month with its
    # own emptiness.
    if any(c["ok"] for c in calls) or (ok and not elapsed):
        _write_cache({"month": month, "reader": CACHE_READER, "read_at": data["read_at"],
                      # replayed on a cheap cycle: a half-failed read that is
                      # republished must not come back as a clean one.
                      "ok": ok, "error": error,
                      "days": known, "settled": settled, "data": data})

    return {
        "source": SOURCE,
        "fetched_at": now.isoformat(timespec="seconds"),
        "server_at": None,          # none of these endpoints stamps its own answer
        "ok": ok,
        "error": error,
        "data": data,
    }


if __name__ == "__main__":
    if "--full" in sys.argv:
        FULL = True
    print(json.dumps(fetch(hourly="--hourly" in sys.argv), indent=2, default=str))
