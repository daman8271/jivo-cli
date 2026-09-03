"""ji.jivo.in dispatch & storage — the live adapter.

Reads the factory app (https://factory.jivo.in/api/v1) through the existing
`factory-cli/jivo-factory-pp-cli` binary, which owns the auth. No SAP, no HTTP
client of our own, no write of any kind. See ../README.md for the contract and
../../reference/MARK3-LIVE-SOURCES.md for the evidence behind every trap
handled below.

    from live.adapters.factory_dispatch import fetch
    fetch()             # 4 CLI calls  — the every-cycle (~3 min) poll
    fetch(heavy=True)   # 5 CLI calls  — add the bill-level pile (every 15-30 min)

    python3 -m live.adapters.factory_dispatch [--heavy]

Envelope: {source, fetched_at, server_at, ok, error, data} — `ok` is False when
ANY call failed; `data` still carries whatever the other calls returned.

===============================================================================
data — every key, with its unit
===============================================================================
as_of_date              str   the plant day these figures describe, IST (YYYY-MM-DD)
heavy                   bool  did the bill-level pull run this cycle
companies               list  the three company codes always reported, Oil first
window_days             int   how many days back the heavy bill window reaches
cli_flags               str   the exact flags every call below carried — the company
                              scoping and the live/no-cache proof, in the state file

invoiced_not_dispatched       the storage-pressure pile
  bills                 int   open dispatch plans not yet dispatched — ALL OPEN,
                              UNDATED (the server ignores the date window)
  litres                L     PENDING + BOOKED litres, same all-open basis
  value_inr             INR   backlog amount
  basis                 str   plain-language statement of what the figure counts
  source                str   which endpoint produced bills/litres/value_inr
  weight_kg             None  ALWAYS None — the upstream backlog weight is corrupt
                              (7.85 m kg against 287k L = 27 kg/L). Never restore it.
  by_status             dict  {PENDING|BOOKED: {bills:int, litres:L, value_inr:INR,
                              counted_in_headline:bool}} plan.booking_status —
                              PENDING means NO VEHICLE YET. Only the open buckets
                              (PENDING/BOOKED) are summed into `litres`; a stray
                              DISPATCHED bucket is reported but never added.
  by_status_bills_counted int the bills behind `litres`. When it differs from
                              `bills` (which comes from totals.backlog.count) the
                              two figures describe different populations — warned.
  --- the keys below are populated only when heavy=True (else empty/None) ---
  by_company            dict  {company_code: {bills:int, litres:L, boxes:pcs,
                              value_inr:INR}} — all three keys always present
  by_stage              dict  {pipeline stage: {bills:int, litres:L}}
                              plan.pipeline_status.stage — a DIFFERENT ladder from
                              booking_status; its 'BOOKED' rung is NOT 'on a truck'
  by_warehouse          dict  {warehouse code: {bills:int, litres:L}}
  godown_rooms_only     dict  {bills:int, litres:L} — BH-BT + BH-PF only, the two
                              rooms the declared Oil FG ceiling actually covers
  aged_over_7d          dict  {bills:int, litres:L} — invoice older than 7 days and
                              still undispatched; likely stale plans, see warnings
  window                dict  {from, to} the invoice-date window of the heavy pull
  window_bills          int   every bill in the window, dispatched or not
  window_litres         L     ditto
  window_value_inr      INR   ditto
  window_undispatched_bills   int  bills in the window not yet dispatched
  window_undispatched_litres  L    ditto — DIFFERENT population from `bills`/`litres`
  by_company_basis      str   what by_company/by_stage/by_warehouse are computed over
  by_company_total_bills int  bills summed across by_company
  by_company_total_litres L   litres summed across by_company — this is NOT `litres`
                              above; the two endpoints count different populations
  reconciliation        dict  {headline_litres L, headline_source, by_company_litres L,
                              by_company_source, ratio, note} — why the two figures
                              differ and how to quote them without misleading anyone
  server_fetched_at     str   the bills endpoint's own meta.fetched_at, in IST

dispatched_today              what physically left the gate today
  trucks                int   distinct vehicle numbers with a DISPATCHED gate row
  bills                 int   SAP documents on those rows
  rows                  int   gate rows (one per company per truck)
  litres                L
  boxes                 pcs
  value_inr             INR   sap_doc_total on the dispatched rows
  by_company            dict  {company_code: {trucks, rows, bills, litres, boxes,
                              value_inr}} — all three keys always present
  source                str
  cross_check           dict  the same day straight off the fulfilment summary
                              {bills, trucks, litres, boxes, value_inr, source}

at_gate_today                 every gate row today, not just the ones that left
  rows                  int
  page_size             int   the row cap asked for
  truncated             bool  rows == page_size. This endpoint returns a BARE ARRAY
                              with no count, so a full page is the only evidence the
                              day was cut off — when True, every gate figure reads LOW
  by_status             dict  {status: {rows, trucks, litres, boxes}} — DOCKED and
                              PRINT_COMMITTED litres are loaded but still inside
  loaded_not_gone_litres L    litres on trucks docked/committed but not dispatched.
                              Counts LOADED_INSIDE_STATUSES only — a REJECTED or
                              CANCELLED gate row is not stock sitting in the yard
  loaded_not_gone_basis str   which statuses that figure counts
  latest_event_at       str   newest updated_at on today's gate rows, IST

trucks_inside           list  [{vehicle_no, company (first seen), companies[],
                              in_time (HH:MM:SS), gate_in_date, entries[],
                              bills[] (SAP doc numbers), bill_count}]
                              de-duplicated on vehicle_no; driver name and mobile
                              are deliberately dropped (no real phone number, ever)
trucks_inside_count     int
ghost_rows_dropped      list  [{vehicle_no, entry_no, gate_in_date, days_old}] —
                              gate-ins never closed out, older than 7 days
undated_gate_rows       list  [{vehicle_no, entry_no, gate_in_date}] — rows with no
                              readable gate_in_date, so the ghost filter could not be
                              applied. They are KEPT in trucks_inside and warned about:
                              the filter must never fail open in silence

flow_stages             dict  {stage: count} straight off the pipeline board's own
                              column counts, cards are PER BILL not per vehicle
in_flow                 dict  {cards, vehicles, vehicle_list[], by_stage{}, note}
                              only the non-DISPATCHED, non-REJECTED cards

oil                     dict  Oil's own slice repeated at the top level so a merged
                              total can never hide it: {dispatched_today_litres L,
                              dispatched_today_trucks, undispatched_litres L,
                              undispatched_bills, trucks_inside}

lag_note                dict  invoice-date -> gate-out lag, MEASURED off the gate log
                              {median_days, mean_days, p90_days, max_days, rows,
                              measured_window, measured_on, method, caveat}
warnings                list  plain-language cautions that travel with the numbers
calls                   list  [{name, ok, ms, args, error}] — per-CLI-call health
===============================================================================
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone

SOURCE = "factory_dispatch"

IST = timezone(timedelta(hours=5, minutes=30))

# The three books. Oil first — Oil is the planner's company and must never be
# lost inside a merged cross-company total.
COMPANIES = ["JIVO_OIL", "JIVO_BEVERAGES", "JIVO_MART"]

# The two godown rooms the declared Oil FG storage ceiling actually covers.
GODOWN_ROOMS = {"BH-BT", "BH-PF"}

# One ceiling for every call. Measured 2026-09-03: summary 1.2-2.1 s, gate 0.4 s,
# inside 0.2-1.3 s, pipeline 0.3 s. The heavy `bills` pull is the outlier — it came
# back in 3.1 s at 13:51 and then blew past a minute at 14:00 the same day.
# This MUST sit above the CLI's own --timeout default of 60 s, so that when the
# server stalls the CLI's real error surfaces instead of our generic "timed out":
# a diagnosable failure is worth the extra 15 s inside a 3-minute cycle.
CALL_TIMEOUT_S = 75
HEAVY_WINDOW_DAYS = 14
GHOST_AFTER_DAYS = 7         # a gate-in older than this never closed out
AGED_AFTER_DAYS = 7          # an invoice older than this is still undispatched
GATE_PAGE_SIZE = 100         # gate-core sales-dispatch is a BARE ARRAY without --page,
                             # so this is a hard cap with no count to check it against

# The open pile on the fulfilment summary. Anything else in by_status (a
# DISPATCHED or CANCELLED bucket) is NOT backlog and must never be summed into
# the storage-pressure headline — bills comes from totals.backlog.count, so a
# stray bucket would leave bills and litres describing different populations.
BACKLOG_STATUSES = {"PENDING", "BOOKED"}

# Gate statuses that mean "stock is on a truck but the truck is still inside".
# REJECTED/CANCELLED rows are NOT sitting in the yard and must not be counted
# as storage still on site.
LOADED_INSIDE_STATUSES = {
    "DOCKED", "PHOTO_ATTACHED", "READY_FOR_GATEPASS",
    "GATEPASS_PRINTED", "PRINT_COMMITTED",
}

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_CLI = os.environ.get(
    "JIVO_FACTORY_CLI",
    os.path.join(_REPO_ROOT, "factory-cli", "jivo-factory-pp-cli"),
)

# Agent-safe defaults. --agent is NOT used: it implies --compact, which strips
# the quantity fields. --data-source live --no-cache because `auto` silently
# serves a stale local SQLite mirror on any error. --company oil because the CLI
# defaults to JIVO_MART and returns clean, plausible, wrong-company data;
# verified live that it does NOT suppress the cross-company endpoints.
_BASE_FLAGS = [
    "--json", "--no-input", "--no-color", "--yes",
    "--data-source", "live", "--no-cache",
    "--company", "oil",
]

# Keys whose values are numbers even when the server sends them as strings
# (gate-core sales-dispatch returns total_litres "3000.000"; dispatch-plans
# bills returns the identically-named field as a real float). Identifier-ish
# keys that merely look numeric — doc_num, invoice_number, gatepass_no,
# eway_bill, weighbridge_slip_no, bp_gstin — are deliberately NOT in here.
_NUMERIC_KEYS = {
    "amount", "amount_inr", "billed_amount", "bills", "booked_count", "boxes",
    "cancelled_count", "challan_weight", "count", "dispatched_amount",
    "dispatched_boxes", "dispatched_count", "dispatched_litres",
    "dispatched_weight", "doc_total", "doc_value", "freight", "fulfillment_rate",
    "gateout_count", "gross_weight", "invoice_amount", "invoice_weight",
    "kanta_weight", "line_count", "litres", "net_weight", "pending_count",
    "physical_quantity", "planned_litres", "planned_weight", "quantity",
    "tare_weight", "total", "total_bills", "total_boxes", "total_doc_value",
    "total_freight", "total_gross_amount", "total_line_amount", "total_litres",
    "total_loose", "total_quantity", "total_weight", "trucks", "weight",
}

_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")
_JWT_RE = re.compile(r"\b[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{6,}\b")
_LONGDIGITS_RE = re.compile(r"\b\d{10,}\b")


# ---------------------------------------------------------------------------
# plumbing
# ---------------------------------------------------------------------------

def _sanitize(text: str) -> str:
    """Never let a token or a phone number out of this module."""
    text = _JWT_RE.sub("<redacted-token>", text)
    text = _LONGDIGITS_RE.sub("<redacted-digits>", text)
    return text.strip()


def _coerce(obj):
    """Turn the known-numeric string fields into floats, in place, recursively."""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, str) and key in _NUMERIC_KEYS and _NUM_RE.match(val):
                obj[key] = float(val)
            else:
                _coerce(val)
    elif isinstance(obj, list):
        for item in obj:
            _coerce(item)
    return obj


def _slice_json(out: str):
    """Slice from the first '{' or '[' — the CLIs print chatter before the JSON."""
    starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
    if not starts:
        raise ValueError("no JSON in stdout")
    text = out[min(starts):]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # tolerate trailing junk after the document
        return json.JSONDecoder().raw_decode(text)[0]


def _run(name, args, timeout=CALL_TIMEOUT_S):
    """The ONE place a CLI call happens.

    Builds argv, runs it with a timeout, discards stderr (the CLI warns there
    before printing JSON), slices stdout from the first brace, json-loads it and
    coerces the numeric strings. Returns (payload, call_record). payload is None
    on any failure — no exception escapes.
    """
    argv = [_CLI] + _BASE_FLAGS + list(args)
    record = {"name": name, "ok": False, "ms": None, "args": " ".join(args), "error": None}
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,   # rule: discard stderr
            timeout=timeout,
            cwd=os.path.dirname(_CLI) or None,
            text=True,
        )
        record["ms"] = int((time.monotonic() - started) * 1000)
        if proc.returncode != 0:
            record["error"] = _sanitize(f"exit {proc.returncode}: {(proc.stdout or '')[:300]}")
            return None, record
        payload = _coerce(_slice_json(proc.stdout or ""))
        record["ok"] = True
        return payload, record
    except subprocess.TimeoutExpired:
        record["ms"] = int((time.monotonic() - started) * 1000)
        record["error"] = f"timed out after {timeout}s"
    except FileNotFoundError:
        record["ms"] = int((time.monotonic() - started) * 1000)
        record["error"] = f"CLI not found at {_CLI}"
    except Exception as exc:  # malformed JSON, unreadable payload, anything
        record["ms"] = int((time.monotonic() - started) * 1000)
        record["error"] = _sanitize(f"{type(exc).__name__}: {exc}")[:300]
    return None, record


def _num(value, default=0.0):
    """Coerce anything the server calls a number into a float."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _r(value, places=1):
    return round(_num(value), places)


def _results(payload):
    """Unwrap the CLI envelope: {meta, results} where results is list|dict."""
    if payload is None:
        return None
    if isinstance(payload, dict) and "results" in payload:
        return payload["results"]
    return payload


def _rows(payload):
    """Every row-returning endpoint here, normalised to a list."""
    res = _results(payload)
    if res is None:
        return []
    if isinstance(res, list):
        return res
    if isinstance(res, dict):
        for key in ("data", "results", "rows", "cards"):
            if isinstance(res.get(key), list):
                return res[key]
    return []


def _parse_ts(value):
    """Parse a server timestamp into an aware datetime. Never slice a timestamp:
    the same instant comes back as 'Z' from one endpoint and '+05:30' from
    another."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=IST)
    return stamp


def _ist(value):
    stamp = _parse_ts(value)
    return stamp.astimezone(IST).isoformat() if stamp else None


def _parse_date(value):
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _blank_company_map(*fields):
    """Every by_company map carries all three books, zeroed — so a company that
    did nothing today reads as 0 rather than silently vanishing."""
    return {code: {field: 0 for field in fields} for code in COMPANIES}


def _bucket(mapping, key, fields):
    return mapping.setdefault(key, {field: 0 for field in fields})


# ---------------------------------------------------------------------------
# the measured lag — from the discovery run, not an assumption
# ---------------------------------------------------------------------------

LAG_NOTE = {
    "median_days": 2,
    "mean_days": 2.93,
    "p90_days": 6,
    "max_days": 14,
    "rows": 96,
    "measured_window": "2026-08-15..2026-09-03",
    "measured_on": "2026-09-03",
    "method": "gate-core sales-dispatch page 1 of 4 (100 rows, 96 DISPATCHED); "
              "(gate_out_date - sap_doc_date) per row",
    "caveat": "measured off the gate log, not the invoice book; page 1 of 4 only. "
              "The plan assumes the 2-day median and ignores the tail to 14 days.",
    "static": True,
}


# ---------------------------------------------------------------------------
# the five reads
# ---------------------------------------------------------------------------

def _read_summary(today, data, calls):
    """Cross-company headline. The backlog half IGNORES the date window."""
    payload, record = _run(
        "dispatch-fulfilment-summary",
        ["dispatch-plans", "dispatch-fulfilment-summary", "--from", today, "--to", today],
    )
    calls.append(record)
    if payload is None:
        return record["error"]

    res = _results(payload) or {}
    totals = res.get("totals") or {}
    backlog = totals.get("backlog") or {}
    dispatched = totals.get("dispatched") or {}

    # Every status is reported, but ONLY the open ones are summed into the
    # headline. bills comes from totals.backlog.count; if the server ever adds a
    # DISPATCHED bucket here, summing it would silently inflate litres by
    # millions while bills stayed right — two populations under one heading.
    by_status = {}
    litres = 0.0
    counted_bills = 0
    for row in res.get("by_status") or []:
        status = row.get("status") or "UNKNOWN"
        in_backlog = status in BACKLOG_STATUSES
        by_status[status] = {
            "bills": int(_num(row.get("count"))),
            "litres": _r(row.get("litres")),
            "value_inr": _r(row.get("amount"), 2),
            "counted_in_headline": in_backlog,
        }
        if in_backlog:
            litres += _num(row.get("litres"))
            counted_bills += int(_num(row.get("count")))

    pile = data["invoiced_not_dispatched"]
    pile["bills"] = int(_num(backlog.get("count")))
    pile["litres"] = round(litres, 1)
    pile["by_status_bills_counted"] = counted_bills
    pile["value_inr"] = _r(backlog.get("amount"), 2)
    pile["by_status"] = by_status
    pile["source"] = "dispatch-plans dispatch-fulfilment-summary"
    pile["basis"] = ("every open dispatch plan across all three books, ALL OPEN and "
                     "UNDATED — this endpoint's backlog ignores the from/to window")

    data["dispatched_today"]["cross_check"] = {
        "bills": int(_num(dispatched.get("bills"))),
        "trucks": int(_num(dispatched.get("count"))),
        "litres": _r(dispatched.get("litres")),
        "boxes": _r(dispatched.get("boxes")),
        "value_inr": _r(dispatched.get("amount"), 2),
        "source": "dispatch-plans dispatch-fulfilment-summary totals.dispatched "
                  "(cross-company, no per-company split available here)",
    }
    filters = res.get("filters") or {}
    data["_company_count_seen"] = filters.get("company_count")
    return None


def _read_gate(today, data, calls):
    """Today's gate truth. Numbers come back as STRINGS on this endpoint."""
    payload, record = _run(
        "sales-dispatch",
        ["gate-core", "sales-dispatch", "--from-date", today, "--to-date", today,
         "--all-companies", "1", "--page-size", str(GATE_PAGE_SIZE)],
    )
    calls.append(record)
    if payload is None:
        return record["error"]

    rows = _rows(payload)
    fields = ("trucks", "rows", "bills", "litres", "boxes", "value_inr")
    by_company = _blank_company_map(*fields)
    company_trucks = {code: set() for code in COMPANIES}
    by_status, status_trucks = {}, {}
    dispatched_trucks, latest = set(), None
    totals = {"rows": 0, "bills": 0, "litres": 0.0, "boxes": 0.0, "value_inr": 0.0}
    loaded_not_gone = 0.0

    for row in rows:
        company = row.get("company_code") or "UNKNOWN"
        status = row.get("status") or "UNKNOWN"
        vehicle = (row.get("vehicle_no") or row.get("vehicle_number") or "").strip()
        litres = _num(row.get("total_litres"))
        boxes = _num(row.get("total_boxes"))
        value = _num(row.get("sap_doc_total"))
        bills = len(row.get("document_numbers") or []) or (1 if row.get("sap_doc_num") else 0)

        stamp = _parse_ts(row.get("updated_at")) or _parse_ts(row.get("created_at"))
        if stamp and (latest is None or stamp > latest):
            latest = stamp

        bucket = _bucket(by_status, status, ("rows", "trucks", "litres", "boxes"))
        bucket["rows"] += 1
        bucket["litres"] += litres
        bucket["boxes"] += boxes
        if vehicle:
            status_trucks.setdefault(status, set()).add(vehicle)

        if status == "DISPATCHED":
            slot = by_company.setdefault(company, {f: 0 for f in fields})
            slot["rows"] += 1
            slot["bills"] += bills
            slot["litres"] += litres
            slot["boxes"] += boxes
            slot["value_inr"] += value
            if vehicle:
                company_trucks.setdefault(company, set()).add(vehicle)
                dispatched_trucks.add(vehicle)
            totals["rows"] += 1
            totals["bills"] += bills
            totals["litres"] += litres
            totals["boxes"] += boxes
            totals["value_inr"] += value
        elif status in LOADED_INSIDE_STATUSES:
            # docked / print-committed: loaded onto a truck, still inside the gate.
            # A REJECTED or CANCELLED row is NOT stock sitting in the yard.
            loaded_not_gone += litres

    # float(), not just round(): round(0, 1) returns int 0, so a company that did
    # nothing today would come back a different JSON type from one that did.
    for code, slot in by_company.items():
        slot["trucks"] = len(company_trucks.get(code, ()))
        slot["litres"] = round(float(slot["litres"]), 1)
        slot["boxes"] = round(float(slot["boxes"]), 1)
        slot["value_inr"] = round(float(slot["value_inr"]), 2)
    for status, bucket in by_status.items():
        bucket["trucks"] = len(status_trucks.get(status, ()))
        bucket["litres"] = round(float(bucket["litres"]), 1)
        bucket["boxes"] = round(float(bucket["boxes"]), 1)

    out = data["dispatched_today"]
    out["trucks"] = len(dispatched_trucks)
    out["rows"] = totals["rows"]
    out["bills"] = totals["bills"]
    out["litres"] = round(totals["litres"], 1)
    out["boxes"] = round(totals["boxes"], 1)
    out["value_inr"] = round(totals["value_inr"], 2)
    out["by_company"] = by_company
    out["source"] = ("gate-core sales-dispatch --all-companies 1 (one row per company "
                     "per truck; trucks de-duplicated on vehicle_no)")

    # Without --page this endpoint returns a BARE ARRAY — no count, no next link —
    # so a full page is the only evidence the day was cut off. Say so out loud
    # rather than quietly reporting a truncated day as the whole day.
    truncated = len(rows) >= GATE_PAGE_SIZE
    data["at_gate_today"] = {
        "rows": len(rows),
        "page_size": GATE_PAGE_SIZE,
        "truncated": truncated,
        "by_status": by_status,
        "loaded_not_gone_litres": round(loaded_not_gone, 1),
        "loaded_not_gone_basis": "gate rows in " + "/".join(sorted(LOADED_INSIDE_STATUSES)),
        "latest_event_at": latest.astimezone(IST).isoformat() if latest else None,
    }
    data["_server_stamps"].append(latest)
    return None


def _read_inside(today_d, data, calls):
    """Trucks parked inside right now. Cross-company with no flag; contains a
    2.5-month-old ghost, and the same truck appears once per company."""
    payload, record = _run("inside-dispatch-vehicles", ["gate-core", "inside-dispatch-vehicles"])
    calls.append(record)
    if payload is None:
        return record["error"]

    trucks, ghosts, undated = {}, [], []
    for row in _rows(payload):
        vehicle = (row.get("vehicle_number") or row.get("vehicle_no") or "").strip()
        gate_in = _parse_date(row.get("gate_in_date"))
        age = (today_d - gate_in).days if gate_in else None
        if age is None:
            # No parseable gate_in_date: the ghost filter CANNOT be applied to this
            # row. Keep the truck (we cannot prove it is stale) but never let the
            # filter fail open in silence — HR67C6723 has been "inside" since June.
            undated.append({"vehicle_no": vehicle, "entry_no": row.get("entry_no"),
                            "gate_in_date": row.get("gate_in_date")})
        if age is not None and age > GHOST_AFTER_DAYS:
            ghosts.append({
                "vehicle_no": vehicle,
                "entry_no": row.get("entry_no"),
                "gate_in_date": row.get("gate_in_date"),
                "days_old": age,
            })
            continue
        bills = [b.get("sap_doc_num") for b in (row.get("bills") or []) if b.get("sap_doc_num")]
        # de-duplicate on vehicle_no: one truck, however many company rows
        entry = trucks.setdefault(vehicle or (row.get("entry_no") or "?"), {
            "vehicle_no": vehicle,
            "company": row.get("company_code"),
            "companies": [],
            "in_time": row.get("in_time"),
            "gate_in_date": row.get("gate_in_date"),
            "entries": [],
            "bills": [],
            "bill_count": 0,
        })
        if row.get("company_code") and row["company_code"] not in entry["companies"]:
            entry["companies"].append(row["company_code"])
        if row.get("entry_no"):
            entry["entries"].append(row["entry_no"])
        for bill in bills:
            if bill not in entry["bills"]:
                entry["bills"].append(bill)
        # earliest gate-in time wins — that is when the truck actually arrived
        if row.get("in_time") and (entry["in_time"] is None or row["in_time"] < entry["in_time"]):
            entry["in_time"] = row["in_time"]

    for entry in trucks.values():
        entry["bill_count"] = len(entry["bills"])

    inside = sorted(trucks.values(), key=lambda e: (e.get("in_time") or "", e["vehicle_no"]))
    data["trucks_inside"] = inside
    data["trucks_inside_count"] = len(inside)
    data["ghost_rows_dropped"] = ghosts
    data["undated_gate_rows"] = undated
    return None


def _read_pipeline(today, data, calls):
    """The stage board. Cards are per BILL, and only the non-DISPATCHED ones are
    'in the flow right now'."""
    payload, record = _run(
        "pipeline",
        ["dispatch-plans", "pipeline", "--all-companies", "--date-from", today, "--date-to", today],
    )
    calls.append(record)
    if payload is None:
        return record["error"]

    res = _results(payload) or {}
    columns = res.get("columns") or []
    cards = res.get("cards") or []

    flow_stages = {col.get("stage"): int(_num(col.get("count"))) for col in columns if col.get("stage")}
    if not flow_stages:
        for card in cards:
            stage = card.get("stage") or "UNKNOWN"
            flow_stages[stage] = flow_stages.get(stage, 0) + 1

    done = {"DISPATCHED", "REJECTED", "CANCELLED"}
    live_cards = [c for c in cards if (c.get("stage") or "") not in done]
    vehicles, by_stage, newest = [], {}, None
    for card in live_cards:
        stage = card.get("stage") or "UNKNOWN"
        by_stage[stage] = by_stage.get(stage, 0) + 1
        vehicle = (card.get("vehicle_no") or "").strip()
        if vehicle and vehicle not in vehicles:
            vehicles.append(vehicle)
    for card in cards:
        stamp = _parse_ts(card.get("stage_at"))
        if stamp and (newest is None or stamp > newest):
            newest = stamp

    data["flow_stages"] = flow_stages
    data["in_flow"] = {
        "cards": len(live_cards),
        "vehicles": len(vehicles),
        "vehicle_list": vehicles,
        "by_stage": by_stage,
        "note": "pipeline cards are per BILL, not per vehicle; DISPATCHED cards are "
                "history, not a queue. Window clipped to today.",
        "board_meta": res.get("meta") or {},
        "newest_stage_at": newest.astimezone(IST).isoformat() if newest else None,
    }
    data["_server_stamps"].append(newest)
    return None


def _read_bills(today, today_d, data, calls):
    """heavy: the bill-level undispatched pile. NEVER pass --limit — it is a hard
    row cap and the meta totals are recomputed on the capped set."""
    start = (today_d - timedelta(days=HEAVY_WINDOW_DAYS)).isoformat()
    payload, record = _run(
        "bills",
        ["dispatch-plans", "bills", "--date-from", start, "--date-to", today, "--all-companies"],
    )
    calls.append(record)
    if payload is None:
        return record["error"]

    res = _results(payload) or {}
    meta = res.get("meta") if isinstance(res, dict) else {}
    meta = meta or {}
    rows = _rows(payload)

    fields = ("bills", "litres", "boxes", "value_inr")
    by_company = _blank_company_map(*fields)
    by_stage, by_warehouse = {}, {}
    und_bills = und_litres = 0.0
    aged_bills = aged_litres = 0.0
    room_bills = room_litres = 0.0

    for row in rows:
        plan = row.get("plan") or {}
        booking = plan.get("booking_status") or "PENDING"
        if booking in ("DISPATCHED", "CANCELLED"):
            continue
        company = row.get("company_code") or "UNKNOWN"
        litres = _num(row.get("total_litres"))
        boxes = _num(row.get("total_boxes"))
        value = _num(row.get("doc_total"))
        warehouse = (row.get("warehouses") or "").strip() or "(none)"
        stage = ((plan.get("pipeline_status") or {}).get("stage")) or "UNKNOWN"

        slot = by_company.setdefault(company, {f: 0 for f in fields})
        slot["bills"] += 1
        slot["litres"] += litres
        slot["boxes"] += boxes
        slot["value_inr"] += value

        st = _bucket(by_stage, stage, ("bills", "litres"))
        st["bills"] += 1
        st["litres"] += litres

        wh = _bucket(by_warehouse, warehouse, ("bills", "litres"))
        wh["bills"] += 1
        wh["litres"] += litres

        und_bills += 1
        und_litres += litres
        if warehouse in GODOWN_ROOMS:
            room_bills += 1
            room_litres += litres
        doc_date = _parse_date(row.get("doc_date"))
        if doc_date and (today_d - doc_date).days > AGED_AFTER_DAYS:
            aged_bills += 1
            aged_litres += litres

    for slot in by_company.values():
        slot["litres"] = round(float(slot["litres"]), 1)
        slot["boxes"] = round(float(slot["boxes"]), 1)
        slot["value_inr"] = round(float(slot["value_inr"]), 2)
    for bucket in list(by_stage.values()) + list(by_warehouse.values()):
        bucket["litres"] = round(float(bucket["litres"]), 1)

    pile = data["invoiced_not_dispatched"]
    pile["by_company"] = by_company
    pile["by_stage"] = by_stage
    pile["by_warehouse"] = dict(sorted(by_warehouse.items(), key=lambda kv: -kv[1]["litres"]))
    pile["godown_rooms_only"] = {"bills": int(room_bills), "litres": round(room_litres, 1)}
    pile["aged_over_7d"] = {"bills": int(aged_bills), "litres": round(aged_litres, 1)}
    pile["window"] = {"from": start, "to": today}
    pile["window_bills"] = int(_num(meta.get("total_bills")))
    pile["window_litres"] = _r(meta.get("total_litres"))
    pile["window_value_inr"] = _r(meta.get("total_doc_value"), 2)
    pile["window_undispatched_bills"] = int(und_bills)
    pile["window_undispatched_litres"] = round(und_litres, 1)
    pile["by_company_basis"] = (
        f"dispatch-plans bills, invoice dates {start}..{today}, rows whose "
        f"plan.booking_status is not DISPATCHED/CANCELLED. This is a DIFFERENT "
        f"population from the all-open backlog above — the two endpoints disagree."
    )
    pile["by_company_total_bills"] = int(und_bills)
    pile["by_company_total_litres"] = round(und_litres, 1)
    headline = _num(pile.get("litres"))
    pile["reconciliation"] = {
        "headline_litres": pile.get("litres"),
        "headline_source": pile.get("source"),
        "by_company_litres": round(und_litres, 1),
        "by_company_source": "dispatch-plans bills",
        "ratio": round(und_litres / headline, 2) if headline else None,
        "note": "These two do NOT reconcile and are not meant to be added or "
                "differenced. The headline counts open dispatch PLANS with no date "
                "bound; by_company counts BILLS in a "
                f"{HEAVY_WINDOW_DAYS}-day invoice window whose plan never reached "
                "DISPATCHED — which includes bills that physically left but whose "
                "plan was never closed. Quote one, name its source, and say which.",
    }
    pile["server_fetched_at"] = _ist(meta.get("fetched_at"))
    data["_server_stamps"].append(_parse_ts(meta.get("fetched_at")))
    # Silent-zero guard. meta and the row list come from different parts of the
    # envelope ({data, meta}); if the row list ever moves or empties while meta
    # still reports bills, every by_company/by_stage/by_warehouse figure would
    # read a confident ZERO. Say so instead.
    if not rows and int(_num(meta.get("total_bills"))) > 0:
        data["_bills_row_mismatch"] = int(_num(meta.get("total_bills")))
    return None


# ---------------------------------------------------------------------------
# public
# ---------------------------------------------------------------------------

def fetch(heavy: bool = False) -> dict:
    """Pull the plant's dispatch & storage position. 4 CLI calls, 5 when heavy."""
    now = datetime.now(IST)
    today_d = now.date()
    today = today_d.isoformat()

    data = {
        "as_of_date": today,
        "heavy": bool(heavy),
        "companies": list(COMPANIES),
        "window_days": HEAVY_WINDOW_DAYS if heavy else None,
        # The scoping proof, in the state file and not just in the source: every
        # call in `calls` below was made with exactly these flags in front of it.
        "cli_flags": " ".join(_BASE_FLAGS),
        "invoiced_not_dispatched": {
            "bills": None, "litres": None, "value_inr": None,
            "basis": None, "source": None,
            "weight_kg": None,          # upstream backlog weight is corrupt; never show it
            "by_status": {}, "by_status_bills_counted": None,
            "by_company": {}, "by_stage": {}, "by_warehouse": {},
            "godown_rooms_only": {}, "aged_over_7d": {},
            "window": None, "window_bills": None, "window_litres": None,
            "window_value_inr": None, "window_undispatched_bills": None,
            "window_undispatched_litres": None, "by_company_basis": None,
            "by_company_total_bills": None, "by_company_total_litres": None,
            "reconciliation": None, "server_fetched_at": None,
        },
        "dispatched_today": {
            "trucks": None, "rows": None, "bills": None, "litres": None,
            "boxes": None, "value_inr": None,
            "by_company": _blank_company_map("trucks", "rows", "bills", "litres", "boxes", "value_inr"),
            "source": None, "cross_check": None,
        },
        "at_gate_today": {},
        "trucks_inside": [],
        "trucks_inside_count": None,
        "ghost_rows_dropped": [],
        "undated_gate_rows": [],
        "flow_stages": {},
        "in_flow": {},
        "oil": {},
        "lag_note": dict(LAG_NOTE),
        "warnings": [],
        "calls": [],
        "_server_stamps": [],
    }

    calls, errors = data["calls"], []

    # Each read is independent: one failure must not take the others down.
    for err in (
        _read_summary(today, data, calls),
        _read_gate(today, data, calls),
        _read_inside(today_d, data, calls),
        _read_pipeline(today, data, calls),
    ):
        if err:
            errors.append(err)
    if heavy:
        err = _read_bills(today, today_d, data, calls)
        if err:
            errors.append(err)

    # Oil, restated at the top level so a merged total can never hide it.
    # `source` is only set when that read succeeded — without it a zeroed map
    # would report "Oil dispatched 0 L" when the truth is "we did not get to ask".
    gate_ok = data["dispatched_today"].get("source") is not None
    oil_disp = (data["dispatched_today"]["by_company"] or {}).get("JIVO_OIL", {}) if gate_ok else {}
    oil_pile = (data["invoiced_not_dispatched"]["by_company"] or {}).get("JIVO_OIL", {})
    data["oil"] = {
        "company": "JIVO_OIL",
        "dispatched_today_litres": oil_disp.get("litres"),
        "dispatched_today_trucks": oil_disp.get("trucks"),
        "undispatched_litres": oil_pile.get("litres"),
        "undispatched_bills": oil_pile.get("bills"),
        "undispatched_basis": data["invoiced_not_dispatched"]["by_company_basis"],
        "trucks_inside": (sum(1 for t in data["trucks_inside"]
                              if "JIVO_OIL" in (t.get("companies") or []))
                          if data["trucks_inside_count"] is not None else None),
    }

    data["warnings"] = [
        "invoiced_not_dispatched.bills/litres are the ALL-OPEN, UNDATED backlog — the "
        "server ignores the date window. Never present it as 'today's' pile.",
        "The two fulfilment endpoints disagree on the size of that backlog; only the "
        "summary is read here, and by_company comes from a different endpoint over a "
        f"{HEAVY_WINDOW_DAYS}-day invoice window. Do not add the two together.",
        "backlog weight is corrupt upstream (27 kg per litre) and is reported as null. "
        "Use litres.",
        "plan.booking_status (PENDING = no vehicle yet) and plan.pipeline_status.stage "
        "(BOOKED = first rung) are different ladders that both say 'BOOKED'.",
        "Only BH-BT and BH-PF sit inside the declared Oil FG godown ceiling, and that "
        "ceiling (827,000 L working / 923,000 L peak) is ASSUMED, never measured.",
        "Oil->Jivo Mart intercompany stock transfers are INCLUDED here (API default); "
        "the planner's own ji.jivo.in screen hides them, so Oil reads higher here.",
        "Dates are SAP invoice dates, not planned dispatch dates.",
        "lag_note is static and measured once on 2026-09-03 — it is not re-read each cycle.",
    ]
    if data["ghost_rows_dropped"]:
        ghosts = ", ".join(sorted({g["vehicle_no"] for g in data["ghost_rows_dropped"] if g["vehicle_no"]}))
        data["warnings"].append(
            f"{len(data['ghost_rows_dropped'])} stale gate-in row(s) dropped from "
            f"trucks_inside (never closed out, older than {GHOST_AFTER_DAYS} days): {ghosts}."
        )
    if data["undated_gate_rows"]:
        data["warnings"].append(
            f"{len(data['undated_gate_rows'])} gate-in row(s) carry no readable gate_in_date, "
            "so the stale-ghost filter could NOT be applied to them; they are counted as "
            "trucks inside and may not be. See undated_gate_rows."
        )
    if data["at_gate_today"].get("truncated"):
        data["warnings"].append(
            f"today's gate read came back exactly full ({GATE_PAGE_SIZE} rows) and this "
            "endpoint returns a bare array with no row count — dispatched_today and "
            "at_gate_today are probably TRUNCATED and read low."
        )
    pile_bills = data["invoiced_not_dispatched"].get("bills")
    counted = data["invoiced_not_dispatched"].get("by_status_bills_counted")
    if pile_bills is not None and counted is not None and pile_bills != counted:
        data["warnings"].append(
            f"the summary's open by_status buckets total {counted} bills but totals.backlog "
            f"says {pile_bills}: bills and litres in invoiced_not_dispatched are no longer "
            "the same population. Quote neither without checking by_status."
        )
    mismatch = data.pop("_bills_row_mismatch", None)
    if mismatch:
        data["warnings"].append(
            f"the bill-level pull returned NO rows while its own meta reported {mismatch} "
            "bills — every by_company / by_stage / by_warehouse figure below is a false "
            "zero, not an empty pile. The row list moved or the response was clipped."
        )
    seen = data.pop("_company_count_seen", None)
    if seen is not None and int(_num(seen)) != len(COMPANIES):
        data["warnings"].append(
            f"the fulfilment summary answered for {seen} company book(s), not {len(COMPANIES)} — "
            "treat the cross-company totals as incomplete."
        )

    stamps = [s for s in data.pop("_server_stamps", []) if s]
    server_at = max(stamps).astimezone(IST).isoformat() if stamps else None

    return {
        "source": SOURCE,
        "fetched_at": now.isoformat(),
        "server_at": server_at,
        "ok": not errors,
        "error": "; ".join(errors) if errors else None,
        "data": data,
    }


if __name__ == "__main__":
    heavy_flag = "--heavy" in sys.argv[1:] or os.environ.get("FACTORY_DISPATCH_HEAVY") == "1"
    print(json.dumps(fetch(heavy=heavy_flag), indent=2, ensure_ascii=False, default=str))
