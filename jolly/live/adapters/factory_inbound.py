"""ji.jivo.in — gate, GRPO and inbound materials (company JIVO_OIL).

Source id: ``factory_inbound``. Everything comes from the existing factory CLI
``factory-cli/jivo-factory-pp-cli`` (live base URL https://factory.jivo.in/api/v1);
this module never opens its own HTTP connection and never writes.

Cadence
-------
``fetch()``            3 calls  — grpo all-entries (up to 3 pages), quality-control
                                  inspections-counts, gate-core arrivals --open-only
``fetch(heavy=True)``  +2 calls — grpo pending (month), grpo summary

Every call carries ``--company JIVO_OIL`` (the CLI defaults to JIVO_MART and
returns clean, plausible, wrong-company data), ``--data-source live --no-cache``
(the default ``auto`` silently serves a stale 114 MB local SQLite mirror), and
``--json --no-input --no-color --yes`` — never ``--agent``, which implies
``--compact`` and strips the quantity fields.

Units
-----
Quantities keep the unit the server states in ``uom``:
  * ``PCS``  — pieces. Packaging material (item codes ``PM*``): bottles, caps,
               cartons, labels.
  * ``MTS``  — metric tonnes. Bulk oil (item codes ``RM*``) delivered by tanker.
No litre conversion is applied anywhere in this module — MT→L needs an oil
density and this adapter does not guess one. Nothing here is money (₹) or kg.

Partial cycles
--------------
A failed call publishes NO key of its own rather than a zero. `arrived_today_count`
absent means "the board was not read this cycle"; it never means "nothing arrived".
`board_read` (bool) says whether the gate board came back at all, and every call's
outcome is in `calls`. Consumers must treat an absent key as unknown — a confident
0 on a dead call reads exactly like a genuinely quiet plant, which is the failure
this loop exists to eliminate.

data keys
---------
company                     str   — always "JIVO_OIL".
as_of_ist                   str   — ISO IST instant this cycle treated as "now".
today_ist                   str   — YYYY-MM-DD in IST; the date "today" means.
board                       dict  — {year, month} of the all-entries board read.
board_counts                dict  — server's own {ALL, GATE, QC, DONE} entry counts
                                    for that month. GATE is NOT trucks waiting: every
                                    GATE-phase row is an abandoned ARRIVAL_SLIP_REJECTED
                                    record, some six months old. Never show it as inbound.
gate_phase_abandoned        int   — board_counts["GATE"], named for what it is.
board_entries_read          int   — gate entries actually parsed this cycle.
board_pages_read            int   — pages fetched (hard cap 3).
board_pages_available       int   — server's total_pages; > pages_read means truncated.
board_read                  bool  — the gate board came back this cycle. False means
                                    every board-derived key below is ABSENT, not zero.
board_truncated             bool  — the 3-page cap bit. Rows come newest-first, so a
                                    truncated read keeps today and loses the oldest:
                                    arrived_today stays right, in_qc under-reports.
unclassified_uom_lines      int   — item lines whose uom is neither PCS nor MTS. Such
                                    a line falls out of every pcs/mt aggregate, so it
                                    is counted here rather than vanishing silently.
unclassified_uoms           list  — the distinct unexpected uom strings seen.
latest_entry_time           str   — newest gate entry_time seen, ISO IST. Freshness
                                    signal only; it is NOT a server clock.

arrived_today               list  — gate entries whose entry_time falls on today_ist,
                                    phase GATE excluded. Each row:
      entry_no              str   — "GE-2026-2210".
      vehicle_entry_id      int   — key for grpo preview / inspection-report.
      time                  str   — entry_time, ISO IST (parsed, never sliced).
      time_ist              str   — "HH:MM:SS" IST, for display.
      phase                 str   — QC | DONE (GATE filtered out).
      status                str   — QC_PENDING | QC_COMPLETED | COMPLETED | ...
      status_label          str   — server's human label.
      supplier              str   — first supplier name on the entry.
      suppliers             list  — [{code, name}] all suppliers on the entry.
      po_numbers            list  — [str] PO numbers drawn down by this truck.
      items                 list  — [{code, name, received_qty, rejected_qty, uom,
                                      qc_status, usable, accepted_qty_reported,
                                      arrival_slip_id, po_number}]
            received_qty    float — what the gate weighed/counted in, in `uom`.
            rejected_qty    float — what QC threw back on that line (0.000 on every
                                    line on the September Oil board).
            usable          float — received_qty less rejected_qty when qc_status ==
                                    "ACCEPTED", else 0.0. THIS is the usable-inbound
                                    number. Do NOT sum accepted_qty: it reads 0.000 on
                                    9 of 26 ACCEPTED lines on the September Oil board.
            accepted_qty_reported float — the raw, unreliable field, kept for audit.
      usable_pcs            float — sum of `usable` on PCS lines (pieces).
      usable_mt             float — sum of `usable` on MTS lines (tonnes).
      pending_pcs           float — received but not yet QC-accepted, pieces.
      pending_mt            float — received but not yet QC-accepted, tonnes.
arrived_today_count         int
arrived_today_usable_pcs    float — packaging cleared and usable today, pieces.
arrived_today_usable_mt     float — bulk oil cleared and usable today, tonnes.
arrived_today_pending_pcs   float — arrived today, still in QC, pieces.
arrived_today_pending_mt    float — arrived today, still in QC, tonnes.

in_qc                       list  — every entry on the month board holding at least one
                                    item line that is not yet ACCEPTED, same row shape
                                    as arrived_today plus:
      waiting_hours         float — hours from entry_time to as_of_ist.
      pending_items         list  — only the not-yet-accepted lines.
in_qc_count                 int
bulk_oil_pending_mt         float — TOTAL tonnes of bulk oil arrived and NOT released
                                    by QC. Tankers sit in QC for days (a soy tanker
                                    gated 01-Sep was still INSPECTION_PENDING on 03-Sep)
                                    while packaging clears in about an hour. A tanker's
                                    gate date is not its availability date — never count
                                    this MT as usable stock.
bulk_oil_pending_lines      int
bulk_oil_oldest_wait_hours  float — longest a pending tanker line has waited.
packaging_pending_pcs       float — pieces arrived and not yet QC-released.
no_arrival_slip             list  — [{entry_no, code, name, received_qty, uom}] lines
                                    stuck at qc_status NO_ARRIVAL_SLIP: material that
                                    arrived but never entered the QC workflow, so it
                                    will never appear in qc_counts. Stranded, not queued.

qc_counts                   dict  — company-wide QC scoreboard, all-time cumulative:
                                    {not_started, draft, awaiting_chemist, awaiting_qam,
                                     completed, rejected, hold, actionable}. `rejected`
                                    is NOT a quality signal — the only Oil rejection in
                                    34 days was a clerical correction. Do not publish a
                                    reject rate off it.

trucks_open                 list  — open gate arrivals touching JIVO_OIL. gate-core
                                    arrivals IGNORES --company, so rows are filtered
                                    here on gate_ins[].company_code, and rows whose
                                    gate_in_date is older than 7 days are dropped as
                                    ghosts (one truck has been "inside" since 22 June).
                                    Mostly OUTBOUND: status LOADING is a dispatch truck.
      arrival_no, vehicle_no, driver_name, gate_in_date, in_time, status,
      companies             list  — every company code gated in on that truck.
      direction             str   — "outbound (loading)" | "inside" | "other:<status>".
      tare_weight           float — kg as the weighbridge reports it.
      weighbridge_slip_no   str
      age_hours             float
trucks_open_count           int
trucks_ghosts_dropped       int   — stale open arrivals excluded (> 7 days).
trucks_other_company        int   — open arrivals with no JIVO_OIL gate-in, excluded.
trucks_duplicate_regs_dropped int — repeat rows for one registration, collapsed to the
                                    newest gate-in. 0 on every read so far.

month_pending               list  — HEAVY ONLY. grpo pending: entries that cleared QC
                                    and await posting to SAP, this month only.
      entry_no, vehicle_entry_id, status
      entry_time            str   — ISO IST. The server returns this field as UTC "Z"
                                    here but as "+05:30" in all-entries, for the same
                                    instant. Both are parsed, never string-sliced.
      po_date               str   — YYYY-MM-DD of the purchase order.
      po_numbers            list  — [str]
      supplier              str
      pending_po_count      int
      po_age_days_at_gate   int   — po_date → gate date, in days. This is PO AGE AT
                                    DRAWDOWN, not supplier lead time: JIVO's POs are
                                    blanket orders drawn down over many part-loads.
                                    Never label it "lead time".
month_pending_count         int

posting_backlog_all_time    dict  — HEAVY ONLY. grpo summary. Every count in it is
                                    ALL-TIME, not this month (465 pending entries
                                    all-time vs 5 for September). Label it as such.
      pending_entry_count, pending_po_count, posted_count, failed_count,
      posting_pending_count, partially_posted_count   — ints
      qc_accepted_qty, qc_rejected_qty                — floats, MIXED UNITS (PCS and
                                    MTS summed together by the server); a ratio of the
                                    two is meaningless. Kept verbatim, not derived from.
      scope                 str   — "all-time".

heavy                       bool  — whether the heavy calls ran this cycle.
calls                       list  — [{name, ok, seconds, error}] one per CLI invocation.
notes                       dict  — short caveat strings for the UI, no numbers in them.

server_at is always None: this API returns no clock of its own.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time as _time
from datetime import datetime, timedelta, timezone

SOURCE = "factory_inbound"
COMPANY = "JIVO_OIL"

# Resolved from this file's own location so the loop works on the VPS too;
# $JIVO_FACTORY_CLI overrides if the binary ever moves.
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))          # …/jivo-cli
CLI_CWD = os.path.join(_REPO, "factory-cli")
CLI = os.environ.get("JIVO_FACTORY_CLI",
                     os.path.join(CLI_CWD, "jivo-factory-pp-cli"))

IST = timezone(timedelta(hours=5, minutes=30))

CALL_TIMEOUT = 60          # seconds, per CLI invocation
MAX_PAGES = 3              # all-entries: follow "next" at most this far
PAGE_SIZE = 100            # server hard-caps at 100
GHOST_DAYS = 7             # open gate arrivals older than this are abandoned records

# Only these fields are coerced from string to float. Identifiers that merely look
# numeric (po_number, weighbridge_slip_no, entry_no, *_code, *_id) are left alone —
# turning PO "220726072" into an int would silently break every join on it.
_NUM_SUFFIXES = ("_qty", "_weight")
_NUM_EXACT = {"unit_price"}

NOTES = {
    "gate_phase": "Phase GATE rows are abandoned arrival slips, not trucks waiting to "
                  "unload. They are excluded from arrivals.",
    "accepted_qty": "Usable inbound is received_qty gated on QC status ACCEPTED. The "
                    "server's accepted_qty field is blank on many accepted lines and is "
                    "never summed here.",
    "qc_speed": "Bulk oil sits in QC for days; packaging clears in about an hour. A "
                "tanker's gate date is not the date its oil becomes usable.",
    "summary_scope": "Posting backlog counts are all-time, not this month.",
    "po_age": "PO age at drawdown is not supplier lead time — JIVO's purchase orders "
              "are blanket orders drawn down over many part-loads.",
    "gate_company": "The gate arrivals endpoint ignores the company flag; rows are "
                    "filtered here on each gate-in's own company code. Most open "
                    "arrivals are outbound dispatch trucks, not inbound material.",
    "qc_rejects": "The QC rejection count is a clerical field, not a quality signal.",
    "summary_units": "The backlog's accepted/rejected quantities add pieces and tonnes "
                     "together on the server. They are carried verbatim; no ratio or "
                     "reject rate can be taken from them.",
    "absent_means_unknown": "A missing key means that call did not come back this "
                            "cycle. It never means zero — check `ok` and `calls`.",
    "dedupe": "Open gate arrivals are de-duplicated on vehicle registration; one truck "
              "can only be inside once.",
}


# --------------------------------------------------------------------------- #
# the one CLI helper                                                          #
# --------------------------------------------------------------------------- #

class CliError(RuntimeError):
    """A single CLI invocation failed. Never fatal to fetch()."""


def _coerce(obj):
    """Turn the server's quantity strings ("2100.000") into floats, in place-ish.

    Only quantity-shaped keys are touched — see _NUM_SUFFIXES / _NUM_EXACT.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str) and (k.endswith(_NUM_SUFFIXES) or k in _NUM_EXACT):
                try:
                    out[k] = float(v)
                    continue
                except ValueError:
                    out[k] = v
                    continue
            out[k] = _coerce(v)
        return out
    if isinstance(obj, list):
        return [_coerce(v) for v in obj]
    return obj


def _cli(name, args, timeout=CALL_TIMEOUT):
    """Run one factory-CLI read and return its parsed payload.

    Builds argv with the mandatory company/live/json flags, runs it with a hard
    timeout, discards stderr (the CLI prints warnings before the JSON), slices
    stdout from the first '{' or '[', json-loads it and coerces numeric strings.

    Returns (payload, meta_source, seconds). Raises CliError on any failure.
    """
    argv = [CLI] + list(args) + [
        "--company", COMPANY,
        "--json", "--no-input", "--no-color", "--yes",
        "--data-source", "live", "--no-cache",
    ]
    t0 = _time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=CLI_CWD,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise CliError("%s: timed out after %ss" % (name, timeout))
    except OSError as exc:
        raise CliError("%s: cannot run CLI (%s)" % (name, exc))
    secs = round(_time.monotonic() - t0, 2)

    out = proc.stdout.decode("utf-8", "replace")
    starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
    if not starts:
        raise CliError("%s: no JSON in output (exit %s)" % (name, proc.returncode))
    try:
        payload = json.loads(out[min(starts):])
    except ValueError as exc:
        raise CliError("%s: unparseable JSON (%s)" % (name, exc))

    meta_source = None
    if isinstance(payload, dict):
        meta = payload.get("meta")
        if isinstance(meta, dict):
            meta_source = meta.get("source")
        payload = payload.get("results", payload)
    return _coerce(payload), meta_source, secs


# --------------------------------------------------------------------------- #
# small parsers                                                               #
# --------------------------------------------------------------------------- #

def _parse_ts(raw):
    """Parse a server timestamp to an aware datetime. Never slice these strings:
    grpo pending returns UTC 'Z' and grpo all-entries '+05:30' for the same instant.
    """
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt


def _ist(dt):
    return dt.astimezone(IST) if dt else None


def _num(v, default=0.0):
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return default


def _rows(payload):
    """Unwrap either a paginated {results: [...]} block or a bare list."""
    if isinstance(payload, dict):
        r = payload.get("results")
        return r if isinstance(r, list) else []
    return payload if isinstance(payload, list) else []


# --------------------------------------------------------------------------- #
# entry shaping                                                               #
# --------------------------------------------------------------------------- #

def _shape_entry(row, now_ist):
    """One gate entry from grpo all-entries → the row shape documented above."""
    ts = _ist(_parse_ts(row.get("entry_time")))
    items = []
    for receipt in row.get("po_receipts") or []:
        for it in receipt.get("items") or []:
            qc = it.get("qc_status") or ""
            recv = _num(it.get("received_qty"))
            rej = _num(it.get("rejected_qty"))
            items.append({
                "code": it.get("item_code"),
                "name": it.get("item_name"),
                "received_qty": recv,
                "rejected_qty": rej,
                "uom": it.get("uom"),
                "qc_status": qc,
                # usable = received_qty gated on ACCEPTED, less anything QC threw
                # back on that same line. accepted_qty is NOT used: it reads 0.000
                # on 9 of 26 ACCEPTED lines live. rejected_qty is 0.000 on every
                # line today, so this subtraction is a no-op now and a guard against
                # over-stating usable stock if a part-rejected line ever appears.
                "usable": max(recv - rej, 0.0) if qc == "ACCEPTED" else 0.0,
                "accepted_qty_reported": _num(it.get("accepted_qty")),
                "arrival_slip_id": it.get("arrival_slip_id"),
                "po_number": receipt.get("po_number"),
            })

    def _sum(uom, key):
        return round(sum(i[key] for i in items if i.get("uom") == uom), 3)

    pending = [i for i in items if i["qc_status"] != "ACCEPTED"]
    suppliers = [
        {"code": s.get("supplier_code"), "name": s.get("supplier_name")}
        for s in row.get("suppliers") or []
    ]
    return {
        "entry_no": row.get("entry_no"),
        "vehicle_entry_id": row.get("vehicle_entry_id"),
        "time": ts.isoformat() if ts else None,
        "time_ist": ts.strftime("%H:%M:%S") if ts else None,
        "date_ist": ts.date().isoformat() if ts else None,
        "phase": row.get("phase"),
        "status": row.get("status"),
        "status_label": row.get("status_label"),
        "supplier": suppliers[0]["name"] if suppliers else None,
        "suppliers": suppliers,
        "po_numbers": list(row.get("po_numbers") or []),
        "items": items,
        "usable_pcs": _sum("PCS", "usable"),
        "usable_mt": _sum("MTS", "usable"),
        "pending_pcs": round(sum(i["received_qty"] for i in pending
                                 if i.get("uom") == "PCS"), 3),
        "pending_mt": round(sum(i["received_qty"] for i in pending
                                if i.get("uom") == "MTS"), 3),
        "waiting_hours": (round((now_ist - ts).total_seconds() / 3600.0, 1)
                          if ts else None),
        "_pending_items": pending,
    }


def _gate_in_dt(row):
    """The instant a truck was gated in, as an aware IST datetime.

    gate_in_date is a bare date ("2026-09-03") and in_time a bare clock time, so
    they are joined and parsed rather than compared as strings. If the server ever
    starts sending gate_in_date as a full stamp, the date half is parsed on its own
    — never sliced, because a sliced offset silently shifts the day boundary.
    """
    gin = row.get("gate_in_date")
    if not gin or not isinstance(gin, str):
        return None
    if "T" in gin:                       # already a full timestamp
        return _ist(_parse_ts(gin))
    return _ist(_parse_ts("%sT%s" % (gin, row.get("in_time") or "00:00:00")))


def _shape_truck(row, now_ist):
    companies = [gi.get("company_code") for gi in row.get("gate_ins") or []]
    dt = _gate_in_dt(row)
    status = row.get("status") or ""
    direction = {"LOADING": "outbound (loading)", "INSIDE": "inside"}.get(
        status, "other:%s" % status if status else "other")
    return {
        "arrival_no": row.get("arrival_no"),
        "vehicle_no": row.get("vehicle_no"),
        "driver_name": row.get("driver_name"),
        "gate_in_date": row.get("gate_in_date"),
        "in_time": row.get("in_time"),
        "status": status,
        "direction": direction,
        "companies": companies,
        "tare_weight": _num(row.get("tare_weight")),
        "weighbridge_slip_no": row.get("weighbridge_slip_no"),
        "gate_in_at": dt.isoformat() if dt else None,   # parsed, tz-aware IST
        "age_hours": (round((now_ist - dt).total_seconds() / 3600.0, 1)
                      if dt else None),
    }


# --------------------------------------------------------------------------- #
# the adapter                                                                 #
# --------------------------------------------------------------------------- #

def fetch(heavy=False):
    """Pull the inbound side of ji.jivo.in for JIVO_OIL.

    heavy=False (every cycle, 3 calls): gate board, QC scoreboard, open trucks.
    heavy=True  (every ~30 min, 5 calls): adds the month posting queue and the
    all-time GRPO backlog.

    A single failing call never kills the rest: it sets ok False, appends to
    `error`, and whatever else came back is still returned in `data`.
    """
    now_ist = datetime.now(IST)
    errors = []
    calls = []
    data = {
        "company": COMPANY,
        "as_of_ist": now_ist.isoformat(),
        "today_ist": now_ist.date().isoformat(),
        "board": {"year": now_ist.year, "month": now_ist.month},
        "heavy": bool(heavy),
        "notes": NOTES,
    }

    def run(name, args):
        """Invoke one CLI read, recording timing and any failure. Returns payload
        or None. Also treats a non-live meta.source as a failure — a silent fall
        back to the stale local mirror is the exact thing this loop exists to
        eliminate, so it must not pass as a good cycle."""
        try:
            payload, meta_source, secs = _cli(name, args)
        except CliError as exc:
            errors.append(str(exc))
            calls.append({"name": name, "ok": False, "seconds": None,
                          "error": str(exc)})
            return None
        entry = {"name": name, "ok": True, "seconds": secs,
                 "source": meta_source, "error": None}
        if meta_source is not None and meta_source != "live":
            msg = "%s: served from '%s', not live" % (name, meta_source)
            errors.append(msg)
            entry["ok"] = False
            entry["error"] = msg
        calls.append(entry)
        return payload

    # ---------------- 1. the month gate board (up to 3 pages) --------------- #
    board_rows = []
    board_counts = {}
    pages_read = 0
    pages_available = None
    page = 1
    while page <= MAX_PAGES:
        payload = run(
            "grpo all-entries p%d" % page,
            ["grpo", "all-entries",
             "--year", str(now_ist.year), "--month", str(now_ist.month),
             "--page-size", str(PAGE_SIZE), "--page", str(page)],
        )
        if payload is None:
            break
        pages_read += 1
        board_rows.extend(_rows(payload))
        if isinstance(payload, dict):
            if not board_counts and isinstance(payload.get("counts"), dict):
                board_counts = payload["counts"]
            if pages_available is None:
                pages_available = payload.get("total_pages")
            if not payload.get("next"):
                break
        else:
            break
        page += 1

    entries = [_shape_entry(r, now_ist) for r in board_rows]
    # Phase GATE rows are abandoned ARRIVAL_SLIP_REJECTED records, some months old.
    live_entries = [e for e in entries if e["phase"] != "GATE"]

    today = data["today_ist"]
    arrived = [e for e in live_entries if e["date_ist"] == today]
    arrived.sort(key=lambda e: e["time"] or "", reverse=True)

    in_qc = [e for e in live_entries if e["_pending_items"]]
    in_qc.sort(key=lambda e: e["time"] or "")

    bulk_lines = [
        (e, i) for e in in_qc for i in e["_pending_items"] if i.get("uom") == "MTS"
    ]
    pack_pending = sum(i["received_qty"] for e in in_qc
                       for i in e["_pending_items"] if i.get("uom") == "PCS")
    no_slip = [
        {"entry_no": e["entry_no"], "code": i["code"], "name": i["name"],
         "received_qty": i["received_qty"], "uom": i["uom"]}
        for e in in_qc for i in e["_pending_items"]
        if i["qc_status"] == "NO_ARRIVAL_SLIP"
    ]

    def _strip(e):
        out = dict(e)
        out["pending_items"] = out.pop("_pending_items")
        return out

    latest = max((e["time"] for e in entries if e["time"]), default=None)

    # An item line whose uom is neither PCS nor MTS would fall out of every
    # aggregate below without a trace. Count it so a new unit is visible.
    odd_lines = [i for e in entries for i in e["items"]
                 if i.get("uom") not in ("PCS", "MTS")]

    # If the board call failed, publish NO board-derived key at all. Emitting
    # arrived_today_count 0 / bulk_oil_pending_mt 0.0 on a dead call is a
    # confident lie that reads exactly like a genuinely quiet plant; an absent
    # key reads as "unknown", which is the truth. Same convention as the heavy
    # block below. Consumers: absent == not read this cycle, never zero.
    data["board_read"] = pages_read > 0
    if pages_read:
        data.update({
            "board_counts": board_counts,
            "gate_phase_abandoned": board_counts.get("GATE", 0),
            "board_entries_read": len(entries),
            "board_pages_read": pages_read,
            "board_pages_available": pages_available,
            "board_truncated": bool(pages_available and pages_available > pages_read),
            "latest_entry_time": latest,
            "arrived_today": [
                {k: v for k, v in _strip(e).items() if k != "pending_items"}
                for e in arrived
            ],
            "arrived_today_count": len(arrived),
            "arrived_today_usable_pcs": round(sum(e["usable_pcs"] for e in arrived), 3),
            "arrived_today_usable_mt": round(sum(e["usable_mt"] for e in arrived), 3),
            "arrived_today_pending_pcs": round(sum(e["pending_pcs"] for e in arrived), 3),
            "arrived_today_pending_mt": round(sum(e["pending_mt"] for e in arrived), 3),
            "in_qc": [_strip(e) for e in in_qc],
            "in_qc_count": len(in_qc),
            "bulk_oil_pending_mt": round(sum(i["received_qty"] for _, i in bulk_lines), 3),
            "bulk_oil_pending_lines": len(bulk_lines),
            "bulk_oil_oldest_wait_hours": max(
                (e["waiting_hours"] for e, _ in bulk_lines
                 if e["waiting_hours"] is not None),
                default=None),
            "packaging_pending_pcs": round(pack_pending, 3),
            "no_arrival_slip": no_slip,
            "unclassified_uom_lines": len(odd_lines),
            "unclassified_uoms": sorted({i.get("uom") for i in odd_lines
                                         if i.get("uom")}),
        })

    # ---------------- 2. QC scoreboard -------------------------------------- #
    qc = run("quality-control inspections-counts",
             ["quality-control", "inspections-counts"])
    if isinstance(qc, dict):          # absent, never {}, when the call failed
        data["qc_counts"] = qc

    # ---------------- 3. open gate arrivals --------------------------------- #
    ga = run("gate-core arrivals", ["gate-core", "arrivals", "--open-only"])
    if ga is not None:                # absent, never 0, when the call failed
        trucks, ghosts, other = [], 0, 0
        cutoff = now_ist - timedelta(days=GHOST_DAYS)
        for row in _rows(ga):
            # The endpoint ignores --company: filter on each gate-in's own code.
            codes = [gi.get("company_code") for gi in row.get("gate_ins") or []]
            if COMPANY not in codes:
                other += 1
                continue
            # Ghosts: gate-ins open for months that never closed. Compared as
            # parsed instants, not sliced strings — gate_in_date is date-only
            # today, but a server that starts returning a full stamp must not
            # silently change what "7 days" means.
            gin_dt = _gate_in_dt(row)
            if gin_dt and gin_dt < cutoff:
                ghosts += 1
                continue
            trucks.append(_shape_truck(row, now_ist))
        trucks.sort(key=lambda t: (t["gate_in_date"] or "", t["in_time"] or ""),
                    reverse=True)
        # De-duplicate on registration: a truck gated in against several bills or
        # several companies comes back once per gate-in on some endpoints, and one
        # physical vehicle can only be inside once. Newest gate-in wins (the list
        # is already newest-first), and the collapse is counted, never silent.
        seen, deduped, dupes = set(), [], 0
        for t in trucks:
            reg = (t.get("vehicle_no") or "").strip().upper()
            if reg and reg in seen:
                dupes += 1
                continue
            if reg:
                seen.add(reg)
            deduped.append(t)
        data.update({
            "trucks_open": deduped,
            "trucks_open_count": len(deduped),
            "trucks_ghosts_dropped": ghosts,
            "trucks_other_company": other,
            "trucks_duplicate_regs_dropped": dupes,
        })

    # ---------------- heavy: month posting queue + all-time backlog --------- #
    if heavy:
        pend = run("grpo pending",
                   ["grpo", "pending",
                    "--year", str(now_ist.year), "--month", str(now_ist.month),
                    "--page-size", str(PAGE_SIZE)])
        month_pending = []
        if pend is not None:
            for row in _rows(pend):
                ts = _ist(_parse_ts(row.get("entry_time")))   # UTC 'Z' here
                po_date = row.get("po_date")
                pos, sup = [], None
                for s in row.get("suppliers") or []:
                    if sup is None:
                        sup = s.get("supplier_name")
                    for r in s.get("po_receipts") or []:
                        if r.get("po_number"):
                            pos.append(r["po_number"])
                        if not po_date and r.get("po_date"):
                            po_date = r["po_date"]
                age = None
                if po_date and ts:
                    try:
                        age = (ts.date() - datetime.strptime(
                            po_date, "%Y-%m-%d").date()).days
                    except ValueError:
                        age = None
                month_pending.append({
                    "entry_no": row.get("entry_no"),
                    "vehicle_entry_id": row.get("vehicle_entry_id"),
                    "status": row.get("status"),
                    "entry_time": ts.isoformat() if ts else None,
                    "po_date": po_date,
                    "po_numbers": pos,
                    "supplier": sup,
                    "pending_po_count": row.get("pending_po_count"),
                    "po_age_days_at_gate": age,   # NOT supplier lead time
                })
            month_pending.sort(key=lambda r: r["entry_time"] or "", reverse=True)
            data["month_pending"] = month_pending
            data["month_pending_count"] = len(month_pending)

        summ = run("grpo summary", ["grpo", "summary"])
        if isinstance(summ, dict):
            backlog = dict(summ)
            backlog["scope"] = "all-time"   # never label these as this month
            data["posting_backlog_all_time"] = backlog

    data["calls"] = calls
    return {
        "source": SOURCE,
        "fetched_at": now_ist.isoformat(),
        "server_at": None,          # this API returns no clock of its own
        "ok": not errors,
        "error": "; ".join(errors) if errors else None,
        "data": data,
    }


if __name__ == "__main__":
    print(json.dumps(fetch(heavy="--heavy" in sys.argv), indent=2, default=str))
