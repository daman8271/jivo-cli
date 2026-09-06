#!/usr/bin/env python3
"""dispatch_lag.py — how many days a bill waits between SAP and the gate. MEASURED DAILY.

    cd jolly && python3 live/dispatch_lag.py            # writes live/state/dispatch_lag.json
    cd jolly && python3 live/dispatch_lag.py --days 30 --out /tmp/lag.json
    cd jolly && python3 live/dispatch_lag.py --print     # measure, print, write nothing

RULING R21 (Mark 4 rulebook, Daman 2026-09-06): the invoice-to-gate lag is measured off
ji.jivo.in's own gate log — `gate-core sales-dispatch`, `gate_out_date − sap_doc_date` per
DISPATCHED row over the last 30 days — and it is **refreshed daily, never every 3 minutes**.
Mark 3 carried ONE measurement, taken by hand on 2026-09-03 off page 1 of 4
(`factory_dispatch.LAG_NOTE`, 96 rows, median 2 d). That number is now three days old every
three days and nothing was ever going to notice.

WHY THIS IS NOT AN ADAPTER. `live/collect.py` discovers `live/adapters/*.py` and runs each
one inside the 3-minute loop's 175-second budget. Six pages of 100 gate rows is a 30-day
read, not a 3-minute one, and R21 says daily in as many words. So this is a plain script in
`live/`, outside discovery, on its own cron line — exactly like `live/demand_baseline_sap.py`.
It writes the same adapter-shaped envelope (live/README.md), so `freeze_live.py` reads it
with the same freshness rule as the baseline: fresh -> use it, stale/missing -> fall back to
the static 3 Sep note and SAY SO.

RULE 0 (../CLAUDE.md): the factory is ji.jivo.in and nothing here goes near SAP. The call
goes through `factory_dispatch._run`, which owns the CLI path, the agent-safe flags and the
`--company oil` default, so this script cannot drift away from the adapter it borrows from.

WHAT LEAVES THIS FILE — AND WHAT MUST NOT
=========================================
A gate row carries `driver_name`, `driver_mobile_no`, `driver_license_no`, `vehicle_no`,
`document_numbers`, `sap_doc_num`, `customer_name` and a ship-to address. `live/state/` is
published over HTTPS. So this file publishes **statistics and nothing else**: counts, days,
a histogram. No plate, no bill number, no person, no customer. The output is then passed
through `live/adapters/_mask.py` on the way to disk — belt and braces, because the one thing
that can still carry a number out is a CLI error string echoing a failed body.

That last sentence used to be the hole (found 2026-09-06). `factory_dispatch._run` puts up
to 300 characters of the CLI's own stdout into `record["error"]` on a non-zero exit, and its
`_sanitize` only removes JWTs and runs of 10+ digits — so `entry_no` ("DOCK-…-0013") and
`company_name` rode out verbatim, and the plate sat 2,184 characters away from the window
purely by the CLI's current key order. Nothing in the chain decided what may be published.
`_safe_error` below now decides: the exit code and the timing are kept, the body is
described by `factory_history._shape_of` — key NAMES, never contents — and a body this
reader cannot parse is published as a character count and nothing else.

THE ENVELOPE  live/state/dispatch_lag.json
    data.window            {from, to, days}
    data.rows              gate rows read; data.dispatched_rows the ones that count
    data.undated_rows      DISPATCHED rows missing either date — they measure nothing
    data.negative_rows     gate-out BEFORE the document date (a back-dated bill), kept
    data.pages_read        pages actually fetched; data.truncated the cap or budget hit
    data.all               {median_days, p90_days, max_days, mean_days, n}
    data.by_company        the same block per book — Oil is the split, never the headline
    data.histogram         {"0": n, "1": n, …} days -> rows
    data.method / caveat   what was measured and what it does not cover

The three books are NOT one population (factory_dispatch says so itself: on 3 Sep 89% of
"dispatched" litres were Beverages). `by_company.JIVO_OIL` is the plan's lag; `all` is
published beside it because the gate is one gate.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))          # …/jolly/live
_JOLLY = os.path.dirname(_HERE)                             # …/jolly
if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)

# Borrowed, never re-implemented: _run owns the CLI path and the agent-safe flags,
# _parse_date/_parse_ts own "never slice a timestamp", _gate_page owns the fact that
# --page switches this endpoint from a bare array to an envelope, and _shape_of owns
# describing an unreadable body by its KEY NAMES and never its contents.
from live.adapters.factory_dispatch import (            # noqa: E402
    COMPANIES, _parse_date, _parse_ts, _run,
)
from live.adapters.factory_history import _gate_page, _shape_of      # noqa: E402
from live.adapters._mask import mask_phones                          # noqa: E402

SOURCE = "dispatch_lag"
IST = timezone(timedelta(hours=5, minutes=30), "IST")
STATE_DIR = os.environ.get("MARK3_STATE_DIR") or os.path.join(_HERE, "state")
OUT_PATH = os.environ.get("MARK4_DISPATCH_LAG_OUT") or os.path.join(STATE_DIR, "dispatch_lag.json")

WINDOW_DAYS = 30
PAGE_SIZE = 100
MAX_PAGES = 10                 # 1,000 rows; the 30-day window ran 261 rows / 3 pages on 6 Sep
BUDGET_S = 40                  # whole-script wall clock, R21 is a daily job not a fast one
PAGE_TIMEOUT_S = 30

METHOD = ("ji.jivo.in gate-core sales-dispatch, --all-companies 1, paged; per DISPATCHED "
          "row lag = gate_out_date - sap_doc_date in whole days")
CAVEAT = ("the gate log, not the invoice book: a bill that never reached a gate row is not "
          "in here at all, so this measures how long the bills that LEFT took to leave. "
          "The plan uses the median and the p90 is published beside it; the tail is real.")


# ------------------------------------------------------------------ statistics
def _pct(values, q):
    """Nearest-rank percentile of an already-sorted list. q in 0..1.

    Nearest rank, not interpolation: a lag is a whole number of days and the p90 has to
    be a day somebody's bill actually waited, not 5.7.
    """
    if not values:
        return None
    i = max(0, min(len(values) - 1, math.ceil(q * len(values)) - 1))
    return values[i]


def stats(values):
    """{median_days, p90_days, max_days, mean_days, n} — every key present, null when n=0.

    Nulls rather than zeros: "no row measured a lag" and "every bill left the same day"
    are different facts and the site has to be able to tell them apart.
    """
    vals = sorted(values)
    n = len(vals)
    if not n:
        return {"median_days": None, "p90_days": None, "max_days": None,
                "mean_days": None, "n": 0}
    mid = n // 2
    median = vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2.0
    return {"median_days": round(median, 1), "p90_days": _pct(vals, 0.90),
            "max_days": vals[-1], "mean_days": round(sum(vals) / n, 2), "n": n}


def row_lag(row):
    """(lag_days, company) for one gate row, or (None, company) when it measures nothing.

    Only a DISPATCHED row counts — a PENDING or DOCKED row has not left, so the days it
    has waited so far are not the lag, they are the pendency (that is factory_dispatch's
    `invoiced_not_dispatched`, a different question).
    """
    company = row.get("company_code") or "UNKNOWN"
    if str(row.get("status") or "") != "DISPATCHED":
        return None, None
    out = _parse_date(row.get("gate_out_date"))
    if out is None:
        stamp = _parse_ts(row.get("dispatched_at"))
        out = stamp.astimezone(IST).date() if stamp else None
    doc = _parse_date(row.get("sap_doc_date"))
    if out is None or doc is None:
        return None, company
    return (out - doc).days, company


# ------------------------------------------------------------------ failures
_EXIT_RE = re.compile(r"^exit (-?\d+):\s*(.*)$", re.S)
_TIMEOUT_RE = re.compile(r"^timed out after \d+s$")
_NOT_FOUND_RE = re.compile(r"^CLI not found at \S+$")
_EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*):")


def _describe_body(body):
    """What a failed CLI body may say on a public page — its SHAPE, never its contents.

    Parseable: `_shape_of` names the top-level keys and stops there. Not parseable — which
    is the usual case, because `_run` cuts stdout at 300 characters and a gate page is
    thousands — the only thing published is how long it was. A gate row is `entry_no`,
    `vehicle_no`, `driver_name`, `customer_name`; there is no prefix of it that is safe to
    quote, so none of it is quoted.
    """
    body = (body or "").strip()
    if not body:
        return "empty"
    try:
        return _shape_of(json.loads(body))
    except (ValueError, TypeError):
        return "%d characters this reader could not parse (not published)" % len(body)


def _safe_error(record):
    """A CLI failure record -> the one sentence this file is willing to publish.

    Everything an operator needs to act — did it exit, time out, or is the CLI missing,
    and with what code — is kept. The CLI's own stdout is not, because its key order and
    pretty-printing decide what lands in `_run`'s 300-character window and neither of
    those is under this project's control. Returns None when the page did not fail.
    """
    text = (record.get("error") or "").strip()
    if not text:
        return None
    hit = _EXIT_RE.match(text)
    if hit:
        return "the CLI exited %s and its output was %s" % (hit.group(1),
                                                            _describe_body(hit.group(2)))
    if _TIMEOUT_RE.match(text) or _NOT_FOUND_RE.match(text):
        return text                         # bounded, and carries no gate data
    hit = _EXC_RE.match(text)
    if hit:
        return "the read raised %s (message not published)" % hit.group(1)
    return "the page failed and the CLI's message is not published"


# --------------------------------------------------------------------- reading
def read_pages(lo, hi, deadline, runner=None, max_pages=MAX_PAGES):
    """Page the gate log. Returns (rows, pages_read, truncated, errors, calls).

    `truncated` is True whenever the window may have been cut short — the page cap, a
    spent budget, a failed page, an answer in a shape this reader does not know, or a
    full page from a build that sends no page count. A short read published as the whole
    window would quietly halve the tail, which is the half that matters.
    """
    run = runner or _run
    rows, errors, calls = [], [], []
    pages_read, truncated = 0, False
    page = 1
    while page <= max_pages:
        if time.monotonic() > deadline:
            errors.append("budget spent after page %d" % pages_read)
            truncated = True
            break
        payload, record = run(
            "gate_p%d" % page,
            ["gate-core", "sales-dispatch",
             "--from-date", lo.isoformat(), "--to-date", hi.isoformat(),
             "--all-companies", "1", "--page", str(page), "--page-size", str(PAGE_SIZE)],
            timeout=PAGE_TIMEOUT_S,
        )
        # NEVER record.get("error") — that string is up to 300 characters of the CLI's
        # own stdout, i.e. the head of a gate page. _safe_error keeps the exit code.
        failure = _safe_error(record)
        calls.append({"name": record.get("name"), "args": record.get("args"),
                      "ok": record.get("ok"),
                      "seconds": round((record.get("ms") or 0) / 1000.0, 3),
                      "error": failure})
        if payload is None:
            errors.append("page %d: %s" % (page, failure or "no rows and no error"))
            truncated = True
            break
        page_rows, paging, recognised = _gate_page(payload)
        if not recognised:
            # Exit 0, valid JSON, and not a gate answer. Reading it as "no rows" would
            # publish a lag measured on nothing at all.
            errors.append("page %d: the answer was %s, not a list of gate rows"
                          % (page, _shape_of(payload)))
            truncated = True
            break
        rows.extend(page_rows)
        pages_read = page
        num_pages = paging.get("num_pages")
        try:
            num_pages = int(num_pages)
        except (TypeError, ValueError):
            num_pages = 0
        if num_pages:
            if page >= num_pages:
                break
        elif paging.get("next"):
            pass                                # a future DRF-shaped envelope
        else:
            # No envelope: a bare array, where a FULL page is the only evidence of a cut-off.
            if len(page_rows) >= PAGE_SIZE:
                errors.append("page %d came back full and the answer carries no page count "
                              "— the window may be cut off" % page)
                truncated = True
            break
        page += 1
    else:
        errors.append("stopped at the %d-page cap" % max_pages)
        truncated = True
    return rows, pages_read, truncated, errors, calls


def summarise(rows, lo, hi, pages_read, truncated):
    """Gate rows -> the published data block. Pure: no I/O, no clock, no network."""
    all_lags, by_company = [], {c: [] for c in COMPANIES}
    histogram = {}
    dispatched = undated = negative = 0
    latest = None
    for row in rows:
        stamp = _parse_ts(row.get("dispatched_at")) or _parse_ts(row.get("updated_at"))
        if stamp and (latest is None or stamp > latest):
            latest = stamp
        lag, company = row_lag(row)
        if company is None:
            continue                            # not DISPATCHED — not this measurement
        dispatched += 1
        if lag is None:
            undated += 1
            continue
        if lag < 0:
            negative += 1
        all_lags.append(lag)
        by_company.setdefault(company, []).append(lag)
        key = str(lag)
        histogram[key] = histogram.get(key, 0) + 1
    return {
        "window": {"from": lo.isoformat(), "to": hi.isoformat(),
                   "days": (hi - lo).days + 1},
        "rows": len(rows),
        "dispatched_rows": dispatched,
        "undated_rows": undated,
        "negative_rows": negative,
        "pages_read": pages_read,
        "page_size": PAGE_SIZE,
        "truncated": truncated,
        "all": stats(all_lags),
        "by_company": {c: stats(v) for c, v in sorted(by_company.items())},
        "histogram": {k: histogram[k] for k in sorted(histogram, key=lambda s: int(s))},
        "measured_on": hi.isoformat(),
        "method": METHOD,
        "caveat": CAVEAT,
        "static": False,
        "_server_stamp": latest.astimezone(IST).isoformat() if latest else None,
    }


def measure(today=None, days=WINDOW_DAYS, budget_s=BUDGET_S, runner=None, max_pages=MAX_PAGES):
    """The whole read, as an adapter-shaped envelope. Never raises."""
    now = datetime.now(IST)
    hi = today or now.date()
    lo = hi - timedelta(days=days)
    deadline = time.monotonic() + budget_s
    rows, pages_read, truncated, errors, calls = read_pages(
        lo, hi, deadline, runner=runner, max_pages=max_pages)
    data = summarise(rows, lo, hi, pages_read, truncated)
    server_at = data.pop("_server_stamp")
    data["errors"] = errors
    data["calls"] = calls
    # ok is about the MEASUREMENT, not about a clean run: pages can fail and still leave
    # enough rows to measure a median. n = 0 is the one thing that is not a lag.
    ok = data["all"]["n"] > 0
    return {
        "source": SOURCE,
        "fetched_at": now.isoformat(),
        "server_at": server_at,
        "ok": ok,
        "error": None if ok else ("; ".join(errors) or "no DISPATCHED row in the window "
                                  "carried both a gate-out date and a document date"),
        "data": data,
    }


def write(envelope, path=None):
    """Mask, then write atomically. The mask is the last thing that touches the object."""
    path = path or OUT_PATH
    mask_phones(envelope)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(envelope, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=WINDOW_DAYS, help="window length (default 30)")
    ap.add_argument("--budget", type=int, default=BUDGET_S, help="wall-clock budget in seconds")
    ap.add_argument("--out", default=OUT_PATH, help="where to write the envelope")
    ap.add_argument("--print", dest="print_only", action="store_true",
                    help="print the envelope and write nothing")
    a = ap.parse_args(argv)
    env = measure(days=a.days, budget_s=a.budget)
    if a.print_only:
        print(json.dumps(mask_phones(env), indent=1, ensure_ascii=False))
        return 0 if env["ok"] else 1
    path = write(env, a.out)
    d = env["data"]
    print("dispatch_lag: %s .. %s — %d gate rows, %d dispatched, %d undated, %d page(s)%s"
          % (d["window"]["from"], d["window"]["to"], d["rows"], d["dispatched_rows"],
             d["undated_rows"], d["pages_read"], " (TRUNCATED)" if d["truncated"] else ""))
    print("  all books   median %s d   p90 %s d   max %s d   mean %s   n=%d"
          % (d["all"]["median_days"], d["all"]["p90_days"], d["all"]["max_days"],
             d["all"]["mean_days"], d["all"]["n"]))
    for c, s in d["by_company"].items():
        print("  %-16s median %s d   p90 %s d   max %s d   n=%d"
              % (c, s["median_days"], s["p90_days"], s["max_days"], s["n"]))
    for e in d["errors"]:
        print("  ! %s" % e)
    print("  -> %s" % path)
    return 0 if env["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
