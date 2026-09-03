#!/usr/bin/env python3
"""
live/adapters/factory_production.py — ji.jivo.in (factory MES + SAP stock bridge),
the PRODUCTION / LINES / STOCK side of the Mark 3 loop. JIVO_OIL only.

Every read goes through factory-cli/jivo-factory-pp-cli. No SAP call, no HTTP client,
read-only, `--company oil` on every request (the CLI defaults to JIVO_MART and returns
clean, plausible, WRONG-company data), `--data-source live --no-cache` so the local
SQLite mirror can never be served as if it were live.

    fetch(hourly=False) -> {source, fetched_at, server_at, ok, error, data}
    python3 -m live.adapters.factory_production [--hourly]

CALLS PER CYCLE
    hourly=False : 4 calls  (reports-daily-production x2, reports-production-movement, runs)
    hourly=True  : 8 calls  (+ lines, line-configs, dashboards stock x2 — one per warehouse)
    Masters (lines, line-configs) and stock change slowly; that is why they are hourly.

=============================================================================
data — EVERY KEY AND ITS UNIT
=============================================================================

TOP LEVEL
  company                str   always "JIVO_OIL".
  date                   str   the plant's today, YYYY-MM-DD, Asia/Kolkata.
  date_yesterday         str   YYYY-MM-DD.
  hourly                 bool  whether the hourly block (lines/line_configs/fg_stock) was fetched.
  calls                  list  [{name, args, ok, seconds, error, data_source}] — one row per
                               CLI call. `args` is the FULL argv (so --company oil and
                               --data-source live are auditable here, not just in this file);
                               `data_source` is the CLI's own meta.source and MUST read
                               "live" — a call that came off the local SQLite mirror is
                               refused outright and lands in `unavailable`.
  unavailable            list  names of the data keys below whose source CLI call FAILED this
                               cycle. Those keys are null, NEVER 0 — a dead call must read
                               UNKNOWN, never "the plant made nothing". Empty list = all good.
  notes                  list  strings the site MUST be able to surface; each is a live-data
                               caveat that has already burned this project (see CAVEATS below).

EVERY key below is null when its source call failed (and named in `unavailable`).

running_now   list — the runs that are LIVE right now (live_status RUNNING/BREAKDOWN, or a
              segment still open). One row per run:
  line                   str   line name, e.g. "Clear Pack". (Line, not machine — the machine
                               master is empty on all three companies.)
  line_id                int   factory line id.
  run_id                 int   MES run id.
  sku_code               str   SAP FG item code, e.g. "FG0000081".
  sku                    str   SKU name as the MES holds it.
  cases                  float CASES closed so far today on this run (sum of closed segments).
  litres                 float LITRES (L) = cases x pieces_per_case x litres_per_piece.
  litres_basis           str   "app" (the app's own pieces_per_case x litres_per_piece) or
                               "sku_name" (engine/plan_units.pack_litres fallback) or "unknown".
  started                str   ISO +05:30, PARSED and re-stamped in IST — earliest segment
                               start, else the run's created_at. null if neither parses.
  live                   bool  True when the run is RUNNING/BREAKDOWN or has an open segment.
  live_status            str   RUNNING | BREAKDOWN | STOPPED | DRAFT | COMPLETED | null.
  open_segments          int   segments still open. AN OPEN SEGMENT REPORTS 0 CASES until the
                               operator closes it — so `cases`/`litres` UNDERSTATE by up to a
                               whole segment (caught live at 800 cases = 12,000 L on one line).
  running_minutes        int   MINUTES, the run's own total_running_minutes (same open-segment hole).
  breakdown_minutes      int   MINUTES. Barely logged — 0 on every live run seen.
  rated_speed            float PIECES/HOUR the run was raised at. NOT a ceiling and sometimes
                               nonsense (Tin Head 15 L measured 327% of it). Never plan on it.
  required_qty           float CASES the run was raised for.
  supervisor, operators  str   free text, may be "".
  warehouse_approval_status str NOT_REQUESTED|PENDING|APPROVED|PARTIALLY_APPROVED|REJECTED.

runs_today    list — the SAME row shape as running_now, but EVERY run dated today
              (live or stopped). running_now is a subset of this.

made_today_l           float LITRES made today per the MES (closed segments only).
made_yesterday_l       float LITRES made yesterday per the MES.
made_today_cases       float CASES today (MES).
made_yesterday_cases   float CASES yesterday (MES).
mes_coverage_note      str   MES sees ~2/3 of the plant — say so wherever these appear.

by_line_today  dict line name -> {
  line_id              int
  runs                 int    runs on that line today
  cases                float  CASES
  litres               float  LITRES (L)
  skus                 list   [{sku_code, sku, cases, litres}]
  live                 bool   any run on this line live right now
  running_minutes      int    MINUTES
  breakdown_minutes    int    MINUTES
}

booked_today  dict — the SAP-side truth read THROUGH the factory app (no sapb1 call):
              goods receipts (TransType 59) into BH-PF dated today.
  receipts             int    number of goods-receipt LINES today.
  pcs                  float  PIECES (bottles/tins/drums) received into BH-PF.
  litres               float  LITRES (L) = pcs x pack_litres(item name).
  value_inr            float  RUPEES (INR), SAP transaction value of those receipts.
  litres_unparsed_pcs  float  PIECES whose pack size could not be parsed from the name and so
                              contributed 0 L. Non-zero means `litres` is an UNDERSTATEMENT.
  by_item              dict   item_code -> {name, group, pcs, litres, value_inr}
  truncated            bool   True = the --limit page filled up, so every figure above is a
                              FLOOR. --limit is a hard row cap and the summary is recomputed
                              on the capped set, so it cannot be trusted to reveal this.
  note                 str    the goods-receipt DATE lags the production date by 0-1 day and
                              varies by SKU. This is production BOOKED, never "produced today".

warehouse_flow_today  dict — BH-PF movement summary for today, from the same call:
  opening_pcs, in_pcs, out_pcs, closing_pcs   float  PIECES
  total_value_inr                             float  RUPEES (INR)
  entries, inward_entries, outward_entries    int    line counts

recent_runs  list — every run in the last 3 days (today-2..today), lightweight:
  {run_id, date, line, line_id, sku_code, sku, live_status, status, running_minutes,
   breakdown_minutes}  — minutes are MINUTES. total_production is DELIBERATELY NOT carried:
   it is a roll-up written only at run close and reads 0.0 on every open run.

HOURLY BLOCK (present and non-null only when hourly=True; null otherwise)
lines        list — {id, name, standard_hours_per_day (HOURS), standard_hours_per_month (HOURS),
                     electricity_units_per_hour (kWh/h, null on every line), is_active,
                     has_config (bool)}
             7 active lines. TIN HEAD AND MANUAL HAVE NO line-config ROW — has_config False
             does NOT mean the line fills nothing (Tin Head runs 15 L daily).
line_configs list — {id, line_id, line_name, config_name, sku_code, sku_name,
                     rated_speed (PIECES/HOUR), pieces_per_case, labour_count,
                     other_manpower_count, is_active}
fg_stock     dict warehouse -> {item_code: on_hand}  — on_hand is in that item's own UOM,
             which is PIECES for finished goods (see fg_stock_detail for the UOM per row).
             Only NON-ZERO rows are carried. Warehouses: BH-PF, BH-BT — fetched ONE PER CALL,
             never as a CSV (a CSV silently SUMS them into a row labelled "2 warehouses").
fg_stock_detail dict warehouse -> [{item_code, item_name, on_hand, uom}] sorted desc.
             uom seen: PCS, LTR, KGS, GMS, DRM, SET, "".
fg_stock_meta   dict warehouse -> {total_items, rows_returned, nonzero_rows, non_fg_rows,
                     non_fg_codes, page_size, page, total_pages, truncated (bool — True only
                     if the page FILLED UP and its last row still had stock), fetched_at
                     (the server's own stamp, PARSED from +00:00 and re-stamped IST)}
             NOT FG-ONLY: FA fixed assets (FA0000207 induction cap sealing machine,
             FA0000208 weighbridge 100 ton), PM packaging and CF/SL/CG/SF codes share this
             list, and the endpoint returns no item_group to filter on. non_fg_rows /
             non_fg_codes name the ones currently holding stock — never total fg_stock and
             call it "finished goods".
             stock_status / min_stock / health_ratio are DELIBERATELY DROPPED: the benchmark is
             unmaintained (min_stock 0.0 and status "unset" on effectively every row). on_hand
             is real; nothing else on that endpoint is.

=============================================================================
CAVEATS BAKED INTO THIS ADAPTER (each one already produced a wrong number here)
=============================================================================
1. NEVER reports-analytics / total_production / OEE. No run has been marked COMPLETED since
   2026-08-26, and every COMPLETED-filtered report therefore returns a confident ZERO while
   the plant is demonstrably running. This adapter reads reports-daily-production SEGMENTS.
2. An OPEN segment reports 0 cases and 0 minutes until closed — the live figure is a floor,
   not a total. open_segments says how much is in flight.
3. The MES sees ~2/3 of the plant (1.44 M L of MES runs in August vs ~2.12 M L actual).
   Use MES for line mix and pace; use booked_today for quantity.
4. Goods-receipt date != production date (0-1 day lag, SKU-dependent).
5. Litres: the app's own pieces_per_case x litres_per_piece WINS over the SKU name.
   Proved live — run 306 "REFINED OIL 2 LTR" is pieces_per_case 1 x litres_per_piece 20,
   so the name would have given 2 L against the true 20 L per case, a 10x error.
   pack_litres() is the fallback and the ONLY other sanctioned source of litres.
6. `dashboards stock` silently aggregates a CSV of warehouses — one warehouse per call.
7. The factory JWT lives ~24 h. A 401 means AUTH DEAD, never "plant idle": a failed call sets
   ok False, names its section in data.unavailable, and leaves that section NULL. It never
   becomes a zero, because a zero here is indistinguishable from an idle plant.
8. Litres from a name are best-effort. booked_today.litres_unparsed_pcs is the honest tell that
   some pieces contributed 0 L; a non-zero there means booked_today.litres is a floor.
9. PROVENANCE IS ENFORCED, not assumed. Every envelope carries meta.source; --data-source live
   is supposed to make it "live", and any other value is refused as a failed call rather than
   served as if it were current. Passing the flag is not the same as checking it landed.
10. TIMESTAMPS ARE PARSED, NEVER SLICED OR STRING-SORTED. This source mixes offsets for the
   same instant — segments come back +05:30, the stock endpoint's meta.fetched_at +00:00 —
   so everything emitted is re-stamped IST.
11. rated_speed is carried because the site wants it, but it is NOT a ceiling: measured August
   rates ran 17%-327% of it. RATED_SPEED_NOTE ships in data.notes every cycle.
12. data.cli_path names the jivo-factory-pp-cli binary that actually answered. The Mac build
   and the Linux build (<name>.linux) sit side by side in the repo; running the wrong one is
   an OSError [Errno 8] Exec format error, so the binary is resolved per platform and the
   answer is published rather than assumed.
13. server_at is null on a normal 3-minute cycle and that is CORRECT — none of the four
   per-cycle endpoints stamps its response (their meta is only {"source": "live"}). Only the
   hourly stock call returns meta.fetched_at.
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "factory_production"
COMPANY = "JIVO_OIL"
IST = timezone(timedelta(hours=5, minutes=30), "IST")
# 8 calls x TIMEOUT_S must stay under the 3-minute loop period in live/loop.sh.
# Observed latency is 0.12-2.4 s; 20 s is ~80x the median and 8 x 20 = 160 s < 180 s.
TIMEOUT_S = 20
FG_WAREHOUSES = ("BH-PF", "BH-BT")
STOCK_PAGE_SIZE = 200
GOODS_RECEIPT_TRANSTYPE = 59

_REPO_ROOT = Path(__file__).resolve().parents[3]          # …/jivo-cli
_JOLLY = Path(__file__).resolve().parents[2]              # …/jivo-cli/jolly
def _platform_cli(base: str) -> str:
    """Prefer the Linux build of the CLI when we are actually on Linux.

    The repo ships the MAC binary under its bare name and the Linux build beside
    it as `<name>.linux`. On the VPS the bare name is a Mach-O, so exec() dies
    with OSError [Errno 8] Exec format error — which took four adapters down in
    one cycle on 2026-09-03 while the loop still reported itself alive. Applied
    to whatever path resolution produced, an env override included, so pointing
    the override at the base name keeps working on both boxes; naming the
    `.linux` file directly is idempotent (there is no `.linux.linux`).
    """
    if platform.system() == "Linux":
        linux = base + ".linux"
        if os.path.isfile(linux) and os.access(linux, os.X_OK):
            return linux
    return base

CLI = _platform_cli(os.environ.get(
    "JIVO_FACTORY_CLI", str(_REPO_ROOT / "factory-cli" / "jivo-factory-pp-cli")
))

# engine/plan_units.pack_litres() is the ONLY sanctioned way to derive litres from a name.
sys.path.insert(0, str(_JOLLY / "engine"))
try:
    from plan_units import pack_litres  # type: ignore
except Exception:  # pragma: no cover - engine must be present; degrade rather than crash
    def pack_litres(sku):  # type: ignore
        return None, "plan_units unavailable"

MES_COVERAGE_NOTE = (
    "MES view only — roughly two-thirds of the plant. About a third of output never "
    "appears as a run (Aug: 1.44 M L of MES runs vs ~2.12 M L actual). Use it for line "
    "mix and pace, not for plant quantity."
)
OPEN_SEGMENT_NOTE = (
    "An open segment reports 0 cases until the operator closes it, so today's MES figure "
    "is a floor — open_segments says how much is still in flight."
)
GR_LAG_NOTE = (
    "booked_today is goods receipts into BH-PF dated today. The receipt date lags the "
    "production date by 0-1 day and varies by SKU — this is production BOOKED, not "
    "'produced today'."
)
STOCK_NOTE = (
    "fg_stock on_hand is live and trustworthy; stock_status, min_stock and health_ratio "
    "are unmaintained and are not carried."
)
NO_CONFIG_NOTE = (
    "Tin Head and Manual carry no line-config row. has_config False does NOT mean the line "
    "fills nothing — Tin Head runs 15 L every day."
)

_DECIMAL_STR = re.compile(r"^-?\d+\.\d+$")

RATED_SPEED_NOTE = (
    "rated_speed (on every run row and every line_config) is NOT a ceiling and is wrong "
    "in both directions — measured August rates ran from 17% (Clear Pack 5 L) to 327% "
    "(Tin Head 15 L) of it. Never size capacity from it."
)
NON_FG_STOCK_NOTE = (
    "fg_stock is every item the warehouse holds, not only FG codes. FA (fixed assets — "
    "FA0000207 induction cap sealing machine, FA0000208 weighbridge), PM, CF, SL and SF "
    "codes share the list and the endpoint returns no item_group to filter on. "
    "fg_stock_meta[wh].non_fg_rows counts the non-FG rows carrying stock — never total "
    "fg_stock as 'finished goods'."
)


# --------------------------------------------------------------------------- helpers
def _coerce(obj):
    """Turn decimal STRINGS into floats ('3000.000' -> 3000.0, '1.0000' -> 1.0).

    A decimal point is required, so identifiers that happen to be digits — doc_num
    '538747', created_by '12770', reference '926596515' — stay strings.
    """
    if isinstance(obj, dict):
        return {k: _coerce(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_coerce(v) for v in obj]
    if isinstance(obj, str) and _DECIMAL_STR.match(obj):
        try:
            return float(obj)
        except ValueError:
            return obj
    return obj


def _num(v, default=0.0):
    """Any of None / '' / '12.5' / 12 -> float."""
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int(v, default=0):
    return int(_num(v, default))


def _iso(ts):
    """Parse an API timestamp and re-stamp it in IST. Returns None on anything unparseable.

    Never sliced, never string-compared: this source mixes offsets for the same instant
    (segments come back +05:30, the stock endpoint's meta.fetched_at comes back +00:00),
    so a raw string is the wrong thing to sort on OR to show next to fetched_at.
    """
    if not isinstance(ts, str) or not ts.strip():
        return None
    try:
        dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:                     # naive stamps from this API are plant-local
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def _iso_str(ts):
    dt = _iso(ts)
    return dt.isoformat() if dt else None


def _slice_json(text: str):
    """Slice stdout from the first '{' or '[' — the CLI prints warnings before the JSON."""
    if not text:
        raise ValueError("empty stdout")
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON in stdout: " + text.strip()[:200])
    return json.loads(text[min(starts):])


class _CallLog(list):
    """Records every CLI call; a failure is recorded, never raised."""

    def record(self, name, args, ok, seconds, error=None, data_source=None):
        self.append(
            {
                "name": name,
                # the FULL argv (minus the binary path) so --company oil and
                # --data-source live are auditable from the payload itself,
                # not only by reading this file.
                "args": " ".join(args),
                "ok": ok,
                "seconds": round(seconds, 3),
                "error": error,
                # the CLI's own provenance stamp: meta.source, "live" or "local".
                "data_source": data_source,
            }
        )


def _cli(calls: _CallLog, name: str, *args: str, timeout: int | None = None):
    """Run one factory-cli read. Returns (payload, error). NEVER raises.

    Builds argv with the mandatory globals, discards stderr, slices stdout from the
    first '{'/'[', json-loads it, coerces numeric strings, and REFUSES any payload
    the CLI did not fetch live.

    --timeout is handed to the CLI as well so it fails cleanly with a JSON body a
    beat before subprocess kills it; `timeout` is read at call time, not bound at
    import, so a caller (or a test) can lower it.
    """
    timeout = int(timeout or TIMEOUT_S)
    flags = ["--company", "oil", "--json", "--no-input", "--no-color", "--yes",
             "--data-source", "live", "--no-cache", "--timeout", f"{max(timeout - 3, 5)}s"]
    argv = [CLI, *args, *flags]
    logged = (*args, *flags)
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,          # the CLI warns on stderr before the JSON
            timeout=timeout,
            check=False,
        )
        out = proc.stdout.decode("utf-8", "replace")
        payload = _slice_json(out)
    except subprocess.TimeoutExpired:
        err = f"{name}: timed out after {timeout}s"
        calls.record(name, logged, False, time.monotonic() - t0, err)
        return None, err
    except FileNotFoundError:
        err = f"{name}: factory CLI not found at {CLI}"
        calls.record(name, logged, False, time.monotonic() - t0, err)
        return None, err
    except Exception as e:                                    # bad/empty/non-JSON stdout
        err = f"{name}: {type(e).__name__}: {e}"
        calls.record(name, logged, False, time.monotonic() - t0, err)
        return None, err

    payload = _coerce(payload)
    # The CLI exits non-zero on an API error but still prints the body — surface it.
    if proc.returncode != 0:
        detail = None
        if isinstance(payload, dict):
            detail = payload.get("detail") or payload.get("error") or payload.get("message")
        err = f"{name}: CLI exit {proc.returncode}" + (f": {detail}" if detail else "")
        calls.record(name, logged, False, time.monotonic() - t0, err)
        return None, err

    # PROVENANCE. Every envelope carries meta.source — the CLI saying whether this
    # came off the API or out of its local SQLite mirror. --data-source live is
    # supposed to guarantee "live"; this checks that it did, because a mirror read
    # dressed as a live one is the exact failure this whole loop exists to kill.
    src = None
    if isinstance(payload, dict) and isinstance(payload.get("meta"), dict):
        src = payload["meta"].get("source")
    if src is not None and str(src).lower() != "live":
        err = f"{name}: NOT LIVE — CLI served data-source {src!r}; refusing it"
        calls.record(name, logged, False, time.monotonic() - t0, err, src)
        return None, err

    calls.record(name, logged, True, time.monotonic() - t0, None, src)
    return payload, None


def _results(payload):
    """Unwrap the CLI envelope {meta, results}. Returns results, or the payload itself."""
    if isinstance(payload, dict) and "results" in payload:
        return payload["results"]
    return payload


def _litres_per_case(run):
    """Litres in ONE case of this run's SKU, and where the number came from.

    The app's own pieces_per_case x litres_per_piece WINS: run 306 'REFINED OIL 2 LTR'
    is 1 x 20 L, while the name alone would say 2 L — a 10x error.
    """
    ppc = _num(run.get("pieces_per_case"))
    lpp = _num(run.get("litres_per_piece"))
    if ppc > 0 and lpp > 0:
        return ppc * lpp, "app"
    v, _how = pack_litres(run.get("product") or "")
    if v:
        # No pieces_per_case to lean on: treat the case as one saleable pack.
        return float(v) * (ppc if ppc > 0 else 1.0), "sku_name"
    return 0.0, "unknown"


def _run_row(run, live_status_by_id):
    segs = run.get("segments") or []
    cases = sum(_num(s.get("produced_cases")) for s in segs)
    open_segs = [s for s in segs if s.get("is_active")]
    l_per_case, basis = _litres_per_case(run)
    # PARSED, not string-sorted: min() over real datetimes, re-stamped in IST.
    starts = sorted(d for d in (_iso(s.get("start_time")) for s in segs) if d)
    live_status = live_status_by_id.get(run.get("id"))
    live = bool(open_segs) or live_status in ("RUNNING", "BREAKDOWN")
    return {
        "line": run.get("line_name"),
        "line_id": run.get("line"),
        "run_id": run.get("id"),
        "sku_code": run.get("item_code"),
        "sku": run.get("product"),
        "cases": round(cases, 3),
        "litres": round(cases * l_per_case, 3),
        "litres_basis": basis,
        "started": starts[0].isoformat() if starts else _iso_str(run.get("created_at")),
        "live": live,
        "live_status": live_status,
        "open_segments": len(open_segs),
        "running_minutes": _int(run.get("total_running_minutes")),
        "breakdown_minutes": _int(run.get("total_breakdown_time")),
        "rated_speed": _num(run.get("rated_speed")),
        "required_qty": _num(run.get("required_qty")),
        "supervisor": run.get("supervisor") or "",
        "operators": run.get("operators") or "",
        "warehouse_approval_status": run.get("warehouse_approval_status"),
    }


def _day_rows(payload, live_status_by_id):
    runs = _results(payload)
    if not isinstance(runs, list):
        return []
    return [_run_row(r, live_status_by_id) for r in runs if isinstance(r, dict)]


def _totals(rows):
    return (
        round(sum(r["litres"] for r in rows), 3),
        round(sum(r["cases"] for r in rows), 3),
    )


def _by_line(rows):
    out = {}
    for r in rows:
        b = out.setdefault(
            r["line"] or "(unnamed line)",
            {"line_id": r["line_id"], "runs": 0, "cases": 0.0, "litres": 0.0,
             "skus": [], "live": False, "running_minutes": 0, "breakdown_minutes": 0},
        )
        b["runs"] += 1
        b["cases"] += r["cases"]
        b["litres"] += r["litres"]
        b["live"] = b["live"] or r["live"]
        b["running_minutes"] += r["running_minutes"]
        b["breakdown_minutes"] += r["breakdown_minutes"]
        b["skus"].append(
            {"sku_code": r["sku_code"], "sku": r["sku"],
             "cases": r["cases"], "litres": r["litres"]}
        )
    for b in out.values():
        b["cases"] = round(b["cases"], 3)
        b["litres"] = round(b["litres"], 3)
    return out


def _booked(payload):
    """Goods receipts (TransType 59) into BH-PF, dated today, in PCS and LITRES."""
    res = _results(payload)
    empty = {
        "receipts": 0, "pcs": 0.0, "litres": 0.0, "value_inr": 0.0,
        "litres_unparsed_pcs": 0.0, "by_item": {}, "truncated": False,
        "note": GR_LAG_NOTE,
    }
    if not isinstance(res, dict):
        return empty, {}
    rows = res.get("data") or []
    by_item, receipts, pcs, litres, value, unparsed = {}, 0, 0.0, 0.0, 0.0, 0.0
    # --limit is a hard row cap on this family of endpoints and the summary is
    # recomputed on the capped set, so a full page means "there may be more".
    row_limit = _int((res.get("meta") or {}).get("limit"))
    truncated = bool(row_limit) and len(rows) >= row_limit
    for row in rows:
        if _int(row.get("transaction_type")) != GOODS_RECEIPT_TRANSTYPE:
            continue
        qty = _num(row.get("in_qty"))
        if qty <= 0:
            continue
        code = row.get("item_code") or "(unknown)"
        name = row.get("item_name") or ""
        per_piece, _how = pack_litres(name)
        row_l = qty * float(per_piece) if per_piece else 0.0
        if not per_piece:
            unparsed += qty
        val = _num(row.get("transaction_value"))
        receipts += 1
        pcs += qty
        litres += row_l
        value += val
        it = by_item.setdefault(
            code, {"name": name, "group": row.get("item_group"),
                   "pcs": 0.0, "litres": 0.0, "value_inr": 0.0}
        )
        it["pcs"] += qty
        it["litres"] += row_l
        it["value_inr"] += val
    for it in by_item.values():
        it["pcs"] = round(it["pcs"], 3)
        it["litres"] = round(it["litres"], 3)
        it["value_inr"] = round(it["value_inr"], 2)

    summary = res.get("summary") or {}
    flow = {
        "opening_pcs": _num(summary.get("opening_qty")),
        "in_pcs": _num(summary.get("total_in_qty")),
        "out_pcs": _num(summary.get("total_out_qty")),
        "closing_pcs": _num(summary.get("closing_qty")),
        "total_value_inr": _num(summary.get("total_value")),
        "entries": _int(summary.get("total_entries")),
        "inward_entries": _int(summary.get("inward_entries")),
        "outward_entries": _int(summary.get("outward_entries")),
    }
    return (
        {
            "receipts": receipts,
            "pcs": round(pcs, 3),
            "litres": round(litres, 3),
            "value_inr": round(value, 2),
            "litres_unparsed_pcs": round(unparsed, 3),
            "by_item": by_item,
            # True = the --limit page filled up, so these totals are a FLOOR.
            "truncated": truncated,
            "note": GR_LAG_NOTE,
        },
        flow,
    )


def _stock(payload):
    """One warehouse's stock page -> ({code: on_hand}, detail rows, meta). Non-zero only."""
    res = _results(payload)
    if not isinstance(res, dict):
        return {}, [], {}
    rows = res.get("data") or []
    meta = res.get("meta") or {}
    codes, detail = {}, []
    for row in rows:
        qty = _num(row.get("on_hand"))
        if qty <= 0:
            continue
        code = row.get("item_code")
        if not code:
            continue
        codes[code] = codes.get(code, 0.0) + qty
        detail.append(
            {
                "item_code": code,
                "item_name": row.get("item_name"),
                "on_hand": qty,
                "uom": row.get("uom") or "",
            }
        )
    detail.sort(key=lambda r: r["on_hand"], reverse=True)
    last_on_hand = _num(rows[-1].get("on_hand")) if rows else 0.0
    page_size = _int(meta.get("page_size"))
    # This list is NOT FG-only: FA fixed assets, PM packaging, CF/SL/CG/SF codes
    # share it and the endpoint returns no item_group to filter on.
    non_fg = [r for r in detail if not str(r["item_code"]).upper().startswith("FG")]
    return (
        codes,
        detail,
        {
            "total_items": _int(meta.get("total_items")),
            "rows_returned": len(rows),
            "nonzero_rows": len(detail),
            "non_fg_rows": len(non_fg),
            "non_fg_codes": sorted(r["item_code"] for r in non_fg),
            "page_size": page_size,
            "page": _int(meta.get("page")),
            "total_pages": _int(meta.get("total_pages")),
            # sorted on_hand desc, so more stock exists only if the page filled up
            # AND its last row still had some. A short page is complete by definition.
            "truncated": bool(page_size) and len(rows) >= page_size and last_on_hand > 0,
            "fetched_at": _iso_str(meta.get("fetched_at")),
        },
    )


# --------------------------------------------------------------------------- fetch
def fetch(hourly: bool = False) -> dict:
    now = datetime.now(IST)
    today = now.date()
    yesterday = today - timedelta(days=1)
    d_today, d_yday = today.isoformat(), yesterday.isoformat()
    d_from3 = (today - timedelta(days=2)).isoformat()

    calls = _CallLog()
    errors = []

    def note_err(e):
        if e:
            errors.append(e)

    # ---- every cycle -------------------------------------------------------
    # 4) runs first: it is the only endpoint carrying live_status, which the daily
    #    report needs in order to say what is actually running.
    p_runs, e = _cli(calls, "runs", "production-execution", "runs",
                     "--date-from", d_from3, "--date-to", d_today)
    note_err(e)
    runs_recent = _results(p_runs) if p_runs is not None else []
    if not isinstance(runs_recent, list):
        runs_recent = []
    live_status_by_id = {
        r.get("id"): r.get("live_status") for r in runs_recent if isinstance(r, dict)
    }

    # 1) today's per-line, per-SKU output, with segments
    p_today, e = _cli(calls, "daily_today", "production-execution",
                      "reports-daily-production", "--date", d_today)
    note_err(e)
    # 2) yesterday — still open, so it keeps moving
    p_yday, e = _cli(calls, "daily_yesterday", "production-execution",
                     "reports-daily-production", "--date", d_yday)
    note_err(e)
    # 3) what SAP actually booked into the FG godown today
    p_move, e = _cli(calls, "movement", "production-execution",
                     "reports-production-movement", "--date-from", d_today,
                     "--date-to", d_today, "--warehouse", "BH-PF", "--limit", "500")
    note_err(e)

    # A failed call yields NULL, never 0 — a zero is indistinguishable from an idle plant.
    unavailable = []

    if p_today is not None:
        rows_today = _day_rows(p_today, live_status_by_id)
        made_today_l, made_today_cases = _totals(rows_today)
        running_now, by_line = [r for r in rows_today if r["live"]], _by_line(rows_today)
    else:
        rows_today, running_now, by_line = None, None, None
        made_today_l = made_today_cases = None
        unavailable += ["running_now", "runs_today", "made_today_l",
                        "made_today_cases", "by_line_today"]

    if p_yday is not None:
        made_yday_l, made_yday_cases = _totals(_day_rows(p_yday, live_status_by_id))
    else:
        made_yday_l = made_yday_cases = None
        unavailable += ["made_yesterday_l", "made_yesterday_cases"]

    if p_move is not None:
        booked, flow = _booked(p_move)
    else:
        booked, flow = None, None
        unavailable += ["booked_today", "warehouse_flow_today"]

    if p_runs is not None:
        recent = [
            {
                "run_id": r.get("id"),
                "date": r.get("date"),
                "line": r.get("line_name"),
                "line_id": r.get("line"),
                "sku_code": r.get("item_code"),
                "sku": r.get("product"),
                "live_status": r.get("live_status"),
                "status": r.get("status"),
                "running_minutes": _int(r.get("total_running_minutes")),
                "breakdown_minutes": _int(r.get("total_breakdown_time")),
            }
            for r in runs_recent
            if isinstance(r, dict)
        ]
    else:
        recent = None
        unavailable.append("recent_runs")

    server_at = None
    # rated_speed rides on every run row every cycle, so its caveat is unconditional.
    notes = [MES_COVERAGE_NOTE, OPEN_SEGMENT_NOTE, GR_LAG_NOTE, RATED_SPEED_NOTE]

    data = {
        "company": COMPANY,
        "date": d_today,
        "date_yesterday": d_yday,
        "hourly": hourly,
        "running_now": running_now,
        "runs_today": rows_today,
        "made_today_l": made_today_l,
        "made_yesterday_l": made_yday_l,
        "made_today_cases": made_today_cases,
        "made_yesterday_cases": made_yday_cases,
        "mes_coverage_note": MES_COVERAGE_NOTE,
        "by_line_today": by_line,
        "booked_today": booked,
        "warehouse_flow_today": flow,
        "recent_runs": recent,
        "lines": None,
        "line_configs": None,
        "fg_stock": None,
        "fg_stock_detail": None,
        "fg_stock_meta": None,
    }

    # ---- hourly ------------------------------------------------------------
    if hourly:
        p_lines, e = _cli(calls, "lines", "production-execution", "lines")
        note_err(e)
        p_cfg, e = _cli(calls, "line_configs", "production-execution", "line-configs")
        note_err(e)

        if p_lines is None:
            unavailable.append("lines")
        if p_cfg is None:
            unavailable.append("line_configs")

        cfgs = _results(p_cfg) if p_cfg is not None else None
        if isinstance(cfgs, list):
            data["line_configs"] = [
                {
                    "id": c.get("id"),
                    "line_id": c.get("line"),
                    "line_name": c.get("line_name"),
                    "config_name": c.get("config_name"),
                    "sku_code": c.get("sku_code") or "",
                    "sku_name": c.get("sku_name") or "",
                    "rated_speed": _num(c.get("rated_speed")),
                    "pieces_per_case": c.get("pieces_per_case"),
                    "labour_count": _int(c.get("labour_count")),
                    "other_manpower_count": _int(c.get("other_manpower_count")),
                    "is_active": bool(c.get("is_active")),
                }
                for c in cfgs
                if isinstance(c, dict)
            ]
        configured = {c["line_id"] for c in (data["line_configs"] or [])}

        lines = _results(p_lines) if p_lines is not None else None
        if isinstance(lines, list):
            data["lines"] = [
                {
                    "id": ln.get("id"),
                    "name": ln.get("name"),
                    "standard_hours_per_day": _num(ln.get("standard_hours_per_day")),
                    "standard_hours_per_month": _num(ln.get("standard_hours_per_month")),
                    "electricity_units_per_hour": ln.get("electricity_units_per_hour"),
                    "is_active": bool(ln.get("is_active")),
                    # False here means "no config row", NOT "fills nothing" — Tin Head runs 15 L.
                    "has_config": ln.get("id") in configured,
                }
                for ln in lines
                if isinstance(ln, dict)
            ]
            notes.append(NO_CONFIG_NOTE)

        stock, detail, meta = {}, {}, {}
        for wh in FG_WAREHOUSES:               # ONE warehouse per call — a CSV sums them
            p_st, e = _cli(calls, f"stock_{wh}", "dashboards", "stock",
                           "--warehouse", wh, "--sort-by", "on_hand",
                           "--sort-dir", "desc", "--page-size", str(STOCK_PAGE_SIZE))
            note_err(e)
            if p_st is None:
                unavailable.append(f"fg_stock[{wh}]")
                continue
            codes, det, m = _stock(p_st)
            stock[wh], detail[wh], meta[wh] = codes, det, m
            if m.get("fetched_at") and not server_at:
                server_at = m["fetched_at"]
        if stock:
            data["fg_stock"] = stock
            data["fg_stock_detail"] = detail
            data["fg_stock_meta"] = meta
            notes.append(STOCK_NOTE)
            notes.append(NON_FG_STOCK_NOTE)
        else:
            unavailable.append("fg_stock")
    else:
        # not an outage — simply not fetched this cycle
        notes.append("lines / line_configs / fg_stock are hourly; not fetched this cycle.")

    data["unavailable"] = unavailable
    data["notes"] = notes
    # Which binary actually answered: the Mac and Linux builds sit side by side
    # in the repo, and the wrong one is an Exec format error, not a bad number.
    data["cli_path"] = CLI
    data["calls"] = list(calls)

    ok = all(c["ok"] for c in calls) and bool(calls)
    return {
        "source": SOURCE,
        "fetched_at": now.isoformat(),
        "server_at": server_at,
        "ok": ok,
        "error": "; ".join(errors) if errors else None,
        "data": data,
    }


if __name__ == "__main__":
    print(json.dumps(fetch(hourly="--hourly" in sys.argv), indent=2, default=str))
