#!/usr/bin/env python3
"""
live/adapters/exim.py — EXIM (https://eximbe.jivo.in): bulk oil, tanks, the inbound
pipeline and the monthly production plan.

Run standalone:  python3 -m live.adapters.exim

Contract: fetch() -> {source, fetched_at, server_at, ok, error, data}
(see live/README.md). A single failing call never kills fetch(): its slice of `data`
is left empty/None, the message is appended to `error`, and `ok` goes False.

----------------------------------------------------------------------------------
READ-ONLY / SAFETY
----------------------------------------------------------------------------------
GET IS NOT SAFE ON EXIM — several GETs write (the app fires them on page load to
push SAP). This module therefore:
  * only ever issues the seven read routes listed in CADENCE below
    (9 requests in the heaviest cycle);
  * ports the `exim` bash wrapper's BLOCK list verbatim (_BLOCKED) AND adds a hard
    allowlist (_RAW_ALLOWED) so the raw shim can only ever reach three paths;
  * refuses any path with an underscore namespace (/sap_sync/, /sync_logs/, ...).
Never /sap_sync/*, /daily-price/fetch/, /jivo-rate/fetch/, /account/logout/,
/stock-status/opening-stock/. The only non-GET anywhere in the chain is the CLI's
own login/refresh, owned by exim/scripts/eximapi.py.

----------------------------------------------------------------------------------
CADENCE — what this module actually calls, and how often
----------------------------------------------------------------------------------
EVERY cycle (2 x CLI + 1 raw, all cheap):
  exim tank get-summary                -> tanks.total_l / capacity_l / utilisation_pct
  exim tank get-item-wise-summary      -> tanks.by_oil
  raw GET /planning/uploads/  (~400 B) -> plan_version  (the plan-freshness probe)

EVERY 30 min (4 x CLI + 1 raw; cached in live/state/exim.slow.json between refreshes,
              override with $EXIM_SLOW_MAX_AGE_S, force with $EXIM_FORCE_SLOW=1):
  exim director-inventorty             -> inbound.director   (a trailing `get` is
                                          swallowed, so the source map's
                                          `director-inventorty get` also works)
  exim stock-status get --status ON_THE_WAY / UNDER_LOADING / IN_CONTRACT
                                       -> inbound.on_the_way / under_loading / in_contract
  raw GET /pos/  (~390 KB, 623 lines)  -> open_bulk_pos

ONLY when /planning/uploads/ reports a new id/version/grand_total/uploaded_at:
  raw GET /planning/latest/            -> the full 186-row plan, written to
                                          live/state/exim.plan.json (NOT into `data`)

So a steady-state cheap cycle = 3 live GETs; a 30-min cycle = 8; a cycle that also
catches a new plan upload = 9.

----------------------------------------------------------------------------------
data — EVERY KEY, WITH ITS UNIT
----------------------------------------------------------------------------------
data.tanks                       bulk oil in the EXIM storage tanks. LITRES throughout.
  .total_l              L        litres in all tanks right now (/tank/tank-summary/ current_stock)
  .capacity_l           L        combined tank capacity (total_tank_capacity)
  .utilisation_pct      %        total_l / capacity_l as EXIM computes it (utilisation_rate)
  .free_headroom_l      L        DERIVED = capacity_l - total_l
  .tank_count           count    number of tanks (32: 28 TANK + 4 TOTE)
  .oil_count            count    distinct oils currently held
  .by_oil[]                      one row per oil currently in a tank, litres desc
     .oil               text     EXIM tank item NAME (e.g. "CANOLA")
     .code              text     EXIM tank item CODE (e.g. "RM00CN") — NOT a SAP RM code
     .litres            L        litres of this oil in tanks
     .capacity_l        L        combined capacity of the tanks assigned to it
     .tank_count        count    how many tanks hold it
     .tanks[]           text     tank codes, e.g. ["TNK010","TNK0025"]
  .by_oil_note          text     the synonym/vocabulary warning (see TRAPS)
  .reading_at           IST iso  the NEWEST per-tank updated_at (/tank/ rows) — when a
                                 human last entered a dip for ANY tank. This is the
                                 reading's own age; fetched_at is only when we asked.
  .reading_oldest_at    IST iso  the oldest per-tank updated_at still on the board
  .reading_age_hours    h        now - reading_at. Over ~30 h the daily dip is overdue.
  .tanks_updated_today  count    tanks whose updated_at falls on today's IST date
  .reading_note         text     "manual daily dip reading, updated 10:45-13:35 IST
                                  — NOT a live sensor". Say this wherever levels show.
  .total_quantity_l     L        the same total as EXIM reports on item-wise-summary
                                 (cross-check against total_l; they should match)

data.inbound                     the import pipeline. LITRES unless the key says _kg.
  .on_the_way[]                  trucks in transit to the factory (status ON_THE_WAY)
  .under_loading[]               trucks loading at origin (status UNDER_LOADING)
  .in_contract[]                 booked, not yet shipped (status IN_CONTRACT)
     each row: id (int) · vendor (text) · vendor_code (text) · oil (text) ·
       rm_code (text, EXIM item code) · litres (L, quantity_in_litre) ·
       kg (kg, quantity) · rate_per_kg (INR/kg) · rate_per_litre (INR/L) ·
       eta (date or null) · days_late (DERIVED int, +ve = ETA already past, else null) ·
       vehicle (text or null) · transporter (text or null) · location (text) ·
       contract_start / contract_end (date) · created_at (ISO, EXIM's own row stamp) ·
       payment_status (text) · grpo_number (text or null)
  .totals_l             L        {on_the_way, under_loading, in_contract} litre sums
  .totals_kg            kg       the same three, in kilograms
  .kg_per_litre         kg/L     0.91 — EXIM applies this FLAT to every oil (see TRAPS)
  .latest_row_created_at ISO     newest created_at across the three lists = how fresh
                                 the pipeline data actually is
  .director                      the /director-inventorty/ one-shot rollup
     .in_tank_l, .outside_factory_l, .at_factory_total_l, .in_contract_l, .otw_l,
     .under_loading_l, .on_the_sea_l, .mundra_port_l, .at_refinery_l, .finished_l   [all L]
     .finished_by_warehouse {WH: L}   finished goods by SAP warehouse (BH-EC, GP-FG)
     .mt {same keys}              MT — EXIM's own metric-tonne column, not derived here
  .fetched_at           ISO      when this 30-min block was actually pulled
  .from_cache           bool     True = served from live/state/exim.slow.json, not re-pulled
                                 (the cache is only ever written after a CLEAN slow
                                  fetch, so a failed cycle can never poison it)

data.open_bulk_pos[]             bulk-oil PO lines still OPEN (status != 'C'), oldest first
  .po_number, .po_date, .rm_code (SAP RM code, e.g. RM0000025), .name (product_name),
  .vendor, .contract_qty (see unit warning), .load_qty (this truck's load, same unit),
  .status ('O' = open in SAP; 'C' = closed, dropped), .vehicle_no, .transporter,
  .grpo_no, .grpo_date, .contract_rate (INR per contract_qty unit), .basic_amount (INR),
  .po_age_days (DERIVED days, count) — /pos/ is EVERY raw-material PO, not oil-only
data.open_bulk_pos_note   text   the double-count + unit warning (see TRAPS)
data.pos_line_count       count  total lines returned by /pos/ before the open filter

data.plan_version                header of the LATEST monthly plan upload
  .id, .version (int) · .month (date) · .title, .source_file, .uploaded_by (text) ·
  .uploaded_at (ISO) · .row_count (count) · .is_latest (bool) ·
  .grand_total (L) · .commodity_total (L) · .premium_total (L) · .ecom_total (L)
data.plan                        what happened to the full plan this cycle
  .changed (bool)        True = a new version landed and was re-pulled this cycle
  .state_file (path)     live/state/exim.plan.json — the full 186 rows live there
  .row_count (count) · .grand_total (L) · .weekly_bucketed_l (L) · .ecom_unbucketed_l (L)
  .reconciles (bool)     grand_total == commodity+premium+ecom AND == sum(total_planning)

data.freshness                   plain-language staleness, per slice (text)

server_at                        EXIM stamps no RESPONSE with its own clock, so this
                                 carries the newest stamp EXIM ITSELF wrote — the
                                 latest stock-status created_at, or the plan's
                                 uploaded_at, whichever is newer, in IST. Same
                                 convention as the factory/OMS adapters. It moves
                                 when the pipeline moves, NOT every cycle.

----------------------------------------------------------------------------------
TRAPS (each already bit this project)
----------------------------------------------------------------------------------
* KG vs LITRES. /tank/* and /director-inventorty/.liter are LITRES.
  /stock-status/ rows carry BOTH (quantity = kg, quantity_in_litre = L). EXIM applies
  a FLAT 0.91 kg/L to every oil — that is EXIM's convention, not physics. Substituting
  per-oil densities stops the numbers reconciling with the app.
* TANK LEVELS ARE A HUMAN'S DAILY DIP READING. All 32 tanks' updated_at cluster
  05:15-08:05 UTC. A 3-minute page that renders them as "live" is lying.
* /tank/log/ HAS NO OUTWARD ROWS. Oil leaving a tank is invisible; the level just
  drops. EXIM cannot answer "what did production draw today".
* EXIM TANK ITEM CODES ARE A DIFFERENT VOCABULARY from SAP RM codes (RM00CN vs
  RM0000002). Merge via jolly/reference/oil-synonyms.csv before ANY shortage maths —
  unmerged synonyms invented a 522,373 L phantom groundnut shortage. RM0000013 pomace
  is NOT RM0000012 extra light; never merge those two.
* /pos/ IS ONE LINE PER TRUCK, NOT PER PO. contract_qty is the PO-header quantity
  REPEATED on every line (PO 220626079 carries 250 three times). Summing contract_qty
  across lines double-counts. Sum load_qty, or de-duplicate on po_number first.
* /pos/ IS NOT OIL-ONLY. It is every raw-material PO. Two of the 18 lines open on
  2026-09-03 are stale 2025 FOOD lines (RM0000057 KALI DRAKH, RM0000050 MUESLI
  WALNUT) that were simply never closed. Filter on rm_code; do not treat the list
  as "the bulk oils on order". RM0000066 is PEANUT OIL — a groundnut synonym.
* /pos/ QUANTITY UNITS ARE NOT DECLARED. For bulk oil the rate reads as INR/MT
  (149,000-173,500) so contract_qty/load_qty are METRIC TONNES — but two 2025 lines
  price at 165 and 345, i.e. a different unit. Pass the numbers through; do not convert.
* ONLY 43.7% OF THE PLAN IS WEEKLY-BUCKETED. commodity_w1..w4 + premium_w1..w4 =
  1,890,300 L. The 2,433,000 L ecom half is monthly only. Any weekly view of September
  is a view of less than half the plan.
* `sap-sync get-monthly-planning` IS NOT THE SEPTEMBER PLAN (11 sub-group rows,
  3,053,094, no FG codes). This module never calls it.
* AT_REFINERY / ON_THE_SEA / MUNDRA_PORT are real statuses that are simply empty
  today. Zero is a state, not a broken feed — but it must be re-checked, not cached
  as "always zero".
* `exim director-inventorty` is a LEAF command: it swallows any positional arg,
  so `director-inventorty get` issues the identical GET (checked with --dry-run,
  zero live hits). MARK3-LIVE-SOURCES.md's form is fine; this module drops the
  `get` only because it is noise.
* --agent implies --compact, which strips fields. This module uses
  --json --no-input --no-color --yes and never --agent (live/README.md).
* NEVER SLICE A TIMESTAMP. stock-status created_at is UTC 'Z'; eta / po_date are
  bare dates. Both go through _ts() and come out IST-aware, so nothing gets read
  5h30 early and max() ranks instants, not strings.
* EXIM IS NOT COMPANY-SCOPED. There is no --company flag anywhere in this CLI
  (checked: `exim-pp-cli --help`); the app is one book covering JIVO's imports.
  The --company oil rule in live/README.md is a factory/OMS rule.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

SOURCE = "exim"

IST = timezone(timedelta(hours=5, minutes=30), "IST")

_HERE = os.path.dirname(os.path.abspath(__file__))
LIVE_DIR = os.path.dirname(_HERE)                       # jolly/live
STATE_DIR = os.path.join(LIVE_DIR, "state")
REPO = os.path.dirname(os.path.dirname(LIVE_DIR))       # jivo-cli
EXIM_DIR = os.path.join(REPO, "exim")
EXIM_WRAPPER = os.path.join(EXIM_DIR, "exim")
EXIM_SCRIPTS = os.path.join(EXIM_DIR, "scripts")        # holds eximapi.py

PLAN_FILE = os.path.join(STATE_DIR, "exim.plan.json")
SLOW_FILE = os.path.join(STATE_DIR, "exim.slow.json")

TIMEOUT_S = 60
SLOW_MAX_AGE_S = int(os.environ.get("EXIM_SLOW_MAX_AGE_S", "1800"))   # 30 min
FORCE_SLOW = os.environ.get("EXIM_FORCE_SLOW", "") not in ("", "0", "false", "no")

KG_PER_LITRE = 0.91          # EXIM's flat convention for every oil

READING_NOTE = ("manual daily dip reading, updated 10:45-13:35 IST "
                "— NOT a live sensor")
BY_OIL_NOTE = ("EXIM tank item codes (RM00CN, RM0MKG) are a DIFFERENT vocabulary from "
               "SAP RM codes. Merge via jolly/reference/oil-synonyms.csv before any "
               "shortage maths; never merge RM0000013 pomace with RM0000012 extra light.")
POS_NOTE = ("one line per TRUCK, not per PO: contract_qty is the PO-header quantity "
            "repeated on every line — summing it double-counts (sum load_qty, or "
            "de-duplicate on po_number first). Quantities are undeclared units "
            "(bulk-oil lines read as METRIC TONNES at INR/MT rates); passed through "
            "unconverted. And /pos/ is EVERY raw-material PO, not oil-only — 2 of "
            "today's 18 open lines are stale 2025 food lines (KALI DRAKH, MUESLI "
            "WALNUT) that were never closed. Filter on rm_code, not on this list "
            "being 'the oils'.")

# ---- read-only guard -------------------------------------------------------
# Ported verbatim from the `exim` bash wrapper (BLOCK=...). A hand-rolled client
# has no such guard, which is exactly how a 2026-08-22 probe wrote 19 sync_logs
# rows and UPDATED two production business partners.
_BLOCKED = (
    "/sap_sync/",
    "/daily-price/fetch/",
    "/jivo-rate/fetch/",
    "/account/logout/",
    "/stock-status/opening-stock/",
)
# Hard allowlist: the raw shim may reach nothing else, ever.
_RAW_ALLOWED = ("/planning/uploads/", "/planning/latest/", "/pos/")

# Full body, no truncation. eximapi.py's own __main__ prints only the first 2000
# chars, which silently decapitates /pos/ (390 KB) and /planning/latest/ (186 rows).
# This runs the SAME client the `exim raw` wrapper execs — it does not add an HTTP
# client, it just skips that print cap. Auth stays owned by eximapi.py.
_RAW_SHIM = (
    "import json,sys;"
    "sys.path.insert(0, sys.argv[1]);"
    "import eximapi;"
    "st,d = eximapi.get(sys.argv[2]);"
    "sys.stdout.write(json.dumps({'_http': st, '_body': d}))"
)


def _guard(path: str) -> None:
    """Refuse anything that mutates, or that we simply have no business calling."""
    for b in _BLOCKED:
        if b in path:
            raise ValueError("REFUSED: %r mutates data (read-only rule)" % path)
    for seg in path.strip("/").split("/"):
        if "_" in seg:
            raise ValueError("REFUSED: %r has an underscore namespace" % path)
    if path not in _RAW_ALLOWED:
        raise ValueError("REFUSED: %r is not on the raw allowlist" % path)


# ---- one helper for every subprocess call ----------------------------------
def _run(argv, timeout=TIMEOUT_S):
    """Run argv, discard stderr, slice stdout from the first '{' or '[', json-load.

    Returns the parsed object. Raises RuntimeError with a short message on any
    failure — callers turn that into a partial-data error, never a crash.
    """
    try:
        p = subprocess.run(
            argv,
            cwd=EXIM_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,     # the CLIs print warnings before the JSON
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("timeout after %ss" % timeout)
    except OSError as e:
        raise RuntimeError("exec failed: %s" % e)

    out = (p.stdout or b"").decode("utf-8", "replace")
    starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
    if not starts:
        raise RuntimeError("rc=%s, no JSON in stdout (%r)" % (p.returncode, out[:160]))
    try:
        return json.loads(out[min(starts):])
    except ValueError as e:
        raise RuntimeError("rc=%s, bad JSON: %s" % (p.returncode, e))


def _cli(*args):
    """`exim <args>` through the bash wrapper (it owns auth AND the block guard)."""
    argv = [EXIM_WRAPPER] + list(args) + [
        "--json", "--no-input", "--no-color", "--yes",   # never --agent: it implies --compact
        "--data-source", "live", "--no-cache",           # never the stale local SQLite mirror
    ]
    obj = _run(argv)
    # The CLI echoes which source answered in meta.source. --data-source live is
    # supposed to make a local answer impossible; this asserts it rather than
    # trusting it, because "auto silently served the SQLite mirror" is the exact
    # failure this loop exists to eliminate.
    meta = obj.get("meta") if isinstance(obj, dict) else None
    src = meta.get("source") if isinstance(meta, dict) else None
    if src is not None and str(src).lower() != "live":
        raise RuntimeError("meta.source=%r — answered from the local mirror, not the API"
                           % src)
    return _unwrap(obj)


def _raw(path):
    """GET one of the three routes the generated CLI does not wrap. Guarded."""
    _guard(path)
    py = sys.executable or "python3"
    body = _run([py, "-c", _RAW_SHIM, EXIM_SCRIPTS, path])
    http = body.get("_http") if isinstance(body, dict) else None
    if http != 200:
        raise RuntimeError("HTTP %s on %s" % (http, path))
    return body.get("_body")


def _unwrap(obj):
    """The Go CLI wraps every body as {"meta": {...}, "results": <body>}."""
    if isinstance(obj, dict) and "results" in obj and "meta" in obj:
        return obj["results"]
    return obj


# ---- coercion --------------------------------------------------------------
def _num(v, default=None):
    """'3000.000' -> 3000.0. None/''/garbage -> default."""
    if v is None or v == "":
        return default
    if isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _int(v, default=None):
    n = _num(v)
    return default if n is None else int(n)


def _txt(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


# ---- timestamps ------------------------------------------------------------
# NEVER slice a timestamp. EXIM hands back '2026-09-02T13:59:00.617839Z' (UTC)
# on stock-status rows and plain '2026-09-04' dates on eta — the same adapter
# renders both next to an IST fetched_at, and a raw 'Z' string read as local
# time is 5h30 wrong. Everything server-side is parsed, then converted to IST.
def _ts(value):
    """Any EXIM stamp -> an aware datetime, or None. Naive input is read as IST."""
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
    """Any EXIM stamp -> IST ISO string, or None."""
    stamp = _ts(value)
    return stamp.astimezone(IST).isoformat() if stamp else None


def _days_late(eta, today):
    """+ve int when the ETA is already in the past. DERIVED, not from EXIM."""
    stamp = _ts(_txt(eta))
    if stamp is None:
        return None
    delta = (today - stamp.astimezone(IST).date()).days
    return delta if delta > 0 else None


# ---- per-slice fetchers ----------------------------------------------------
def _tanks(errors):
    out = {
        "total_l": None, "capacity_l": None, "utilisation_pct": None,
        "free_headroom_l": None, "tank_count": None, "oil_count": None,
        "by_oil": [], "total_quantity_l": None,
        "by_oil_note": BY_OIL_NOTE, "reading_note": READING_NOTE,
    }
    try:
        s = _unwrap(_cli("tank", "get-summary"))
        if isinstance(s, list) and s:
            s = s[0]
        s = (s or {}).get("summary", s) or {}
        out["total_l"] = _num(s.get("current_stock"))
        out["capacity_l"] = _num(s.get("total_tank_capacity"))
        out["utilisation_pct"] = _num(s.get("utilisation_rate"))
        out["tank_count"] = _int(s.get("tank_count"))
        out["oil_count"] = _int(s.get("item_count"))
        if out["total_l"] is not None and out["capacity_l"] is not None:
            out["free_headroom_l"] = round(out["capacity_l"] - out["total_l"], 2)
    except Exception as e:                                    # noqa: BLE001
        errors.append("tank get-summary: %s" % e)

    try:
        w = _unwrap(_cli("tank", "get-item-wise-summary"))
        if isinstance(w, list) and w:
            w = w[0]
        w = w or {}
        out["total_quantity_l"] = _num(w.get("total_quantity"))
        rows = []
        for it in (w.get("items") or []):
            rows.append({
                "oil": _txt(it.get("tank_item_name")),
                "code": _txt(it.get("tank_item_code")),
                "litres": _num(it.get("quantity_in_liters"), 0.0),
                "capacity_l": _num(it.get("total_capacity")),
                "tank_count": _int(it.get("tank_count")),
                "tanks": [t for t in (it.get("tank_numbers") or []) if t],
            })
        rows.sort(key=lambda r: (r["litres"] or 0), reverse=True)
        out["by_oil"] = rows
        if out["oil_count"] is None:
            out["oil_count"] = len(rows)
    except Exception as e:                                    # noqa: BLE001
        errors.append("tank get-item-wise-summary: %s" % e)

    # WHEN was the dip taken? The summaries carry no stamp, so the level read
    # 754,900 L on every cycle from 3 Sep to 5 Sep 2026 and the site said "as of
    # <fetch time>" over a reading nobody had touched for two days. /tank/ rows
    # carry updated_at per tank; the newest one is when a human last entered a
    # dip for anything, and that — not fetched_at — is this block's honest age.
    out.update({"reading_at": None, "reading_oldest_at": None,
                "reading_age_hours": None, "tanks_updated_today": None})
    try:
        t = _unwrap(_cli("tank", "get"))
        stamps = [_ts(_txt(r.get("updated_at"))) for r in (t or []) if isinstance(r, dict)]
        stamps = [s for s in stamps if s is not None]
        if stamps:
            now = datetime.now(IST)
            newest, oldest = max(stamps), min(stamps)
            out["reading_at"] = newest.astimezone(IST).isoformat()
            out["reading_oldest_at"] = oldest.astimezone(IST).isoformat()
            out["reading_age_hours"] = round((now - newest).total_seconds() / 3600, 1)
            out["tanks_updated_today"] = sum(
                1 for s in stamps if s.astimezone(IST).date() == now.date())
    except Exception as e:                                    # noqa: BLE001
        errors.append("tank get (per-tank updated_at): %s" % e)
    return out


def _stock_rows(status, today, errors):
    try:
        rows = _unwrap(_cli("stock-status", "get", "--status", status))
    except Exception as e:                                    # noqa: BLE001
        errors.append("stock-status %s: %s" % (status, e))
        return []
    if isinstance(rows, dict):
        rows = rows.get("results") or rows.get("data") or []
    out = []
    for r in rows or []:
        if not isinstance(r, dict) or r.get("deleted"):
            continue
        eta = _txt(r.get("eta"))
        out.append({
            "id": _int(r.get("id")),
            "vendor": _txt(r.get("vendor_name")),
            "vendor_code": _txt(r.get("vendor_code")),
            "oil": _txt(r.get("item_name")),
            "rm_code": _txt(r.get("item_code")),
            "litres": _num(r.get("quantity_in_litre"), 0.0),
            "kg": _num(r.get("quantity"), 0.0),
            "rate_per_kg": _num(r.get("rate")),
            "rate_per_litre": _num(r.get("rate_in_litres")),
            "eta": eta,
            "days_late": _days_late(eta, today),
            "vehicle": _txt(r.get("vehicle_number")),
            "transporter": _txt(r.get("transporter")),
            "location": _txt(r.get("location")),
            "contract_start": _txt(r.get("contract_start")),
            "contract_end": _txt(r.get("contract_end")),
            # EXIM stamps this UTC 'Z'; normalised to IST so it can sit beside
            # fetched_at without being read 5h30 early.
            "created_at": _ist(r.get("created_at")) or _txt(r.get("created_at")),
            "payment_status": _txt(r.get("payment_status")),
            "grpo_number": _txt(r.get("grpo_number")),
        })
    out.sort(key=lambda x: (x["eta"] or "9999-99-99", -(x["litres"] or 0)))
    return out


def _director(errors):
    keys = ("in_tank_l outside_factory_l at_factory_total_l in_contract_l otw_l "
            "under_loading_l on_the_sea_l mundra_port_l at_refinery_l finished_l").split()
    out = {k: None for k in keys}
    out["finished_by_warehouse"] = {}
    out["mt"] = {}
    try:
        d = _unwrap(_cli("director-inventorty"))     # NB: no `get` subcommand
        if isinstance(d, list) and d:
            d = d[0]
        d = d or {}
    except Exception as e:                                    # noqa: BLE001
        errors.append("director-inventorty: %s" % e)
        return out

    def leaf(node, lkey="liter", mkey="mts"):
        if not isinstance(node, dict):
            return None, None
        lit = node.get(lkey)
        if isinstance(lit, dict):                    # in_tank nests {"liter":{"total_liter":..}}
            lit = lit.get("total_liter")
        return _num(lit), _num(node.get(mkey))

    fac = d.get("at_factory") or {}
    tot = fac.get("total") or {}
    out["at_factory_total_l"] = _num(tot.get("total_lts"))
    out["mt"]["at_factory_total"] = _num(tot.get("total_mts"))
    for src, dst in (("in_tank", "in_tank"), ("outside_factory", "outside_factory")):
        l, m = leaf(fac.get(src))
        out[dst + "_l"] = l
        out["mt"][dst] = m
    for k in ("otw", "under_loading", "at_refinery", "mundra_port", "on_the_sea",
              "in_contract"):
        l, m = leaf(d.get(k))
        out[k + "_l"] = l
        out["mt"][k] = m
    fin = d.get("finished") or {}
    l, m = leaf(fin.get("total"))
    out["finished_l"] = l
    out["mt"]["finished"] = m
    for wh, node in fin.items():
        if wh == "total":
            continue
        wl, _ = leaf(node)
        out["finished_by_warehouse"][wh] = wl
    return out


def _open_pos(errors, today=None):
    """/pos/ -> the OPEN raw-material PO lines. status 'C' = closed in SAP, dropped."""
    today = today or datetime.now(IST).date()
    try:
        rows = _raw("/pos/")
    except Exception as e:                                    # noqa: BLE001
        errors.append("/pos/: %s" % e)
        return [], None
    if isinstance(rows, dict):
        rows = rows.get("results") or rows.get("pos") or []
    total = len(rows or [])
    closed = {"C", "CLOSED", "COMPLETED"}
    out = []
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        st = (_txt(r.get("status")) or "").upper()
        if st in closed:
            continue
        out.append({
            "po_number": _txt(r.get("po_number")),
            "po_date": _txt(r.get("po_date")),
            "rm_code": _txt(r.get("product_code")),
            "name": _txt(r.get("product_name")),
            "vendor": _txt(r.get("vendor")),
            "contract_qty": _num(r.get("contract_qty")),
            "load_qty": _num(r.get("load_qty")),
            "status": st or None,
            "vehicle_no": _txt(r.get("vehicle_no")),
            "transporter": _txt(r.get("transporter")),
            "grpo_no": _txt(r.get("grpo_no")),
            "grpo_date": _txt(r.get("grpo_date")),
            "contract_rate": _num(r.get("contract_rate")),
            "basic_amount": _num(r.get("basic_amount")),
            "po_age_days": _days_late(_txt(r.get("po_date")), today),
        })
    out.sort(key=lambda x: (x["po_date"] or "", x["po_number"] or ""))
    return out, total


def _plan_version(errors):
    try:
        body = _raw("/planning/uploads/")
    except Exception as e:                                    # noqa: BLE001
        errors.append("/planning/uploads/: %s" % e)
        return None
    ups = body.get("uploads") if isinstance(body, dict) else body
    # A 200 carrying an HTML/text body (a proxy interstitial — this host is
    # documented as flaky from the Mac) is NOT a plan: iterating it yields
    # characters, and .get() on a character used to kill the whole adapter.
    ups = [u for u in ups if isinstance(u, dict)] if isinstance(ups, list) else []
    if not ups:
        errors.append("/planning/uploads/: no upload rows returned "
                      "(body was %s)" % type(body).__name__)
        return None
    latest = next((u for u in ups if u.get("is_latest")), ups[0])
    return {
        "id": _int(latest.get("id")),
        "version": _int(latest.get("version")),
        "month": _txt(latest.get("month")),
        "title": _txt(latest.get("title")),
        "source_file": _txt(latest.get("source_file")),
        "uploaded_by": _txt(latest.get("uploaded_by")),
        "uploaded_at": _txt(latest.get("uploaded_at")),
        "row_count": _int(latest.get("row_count")),
        "is_latest": bool(latest.get("is_latest")),
        "grand_total": _num(latest.get("grand_total")),
        "commodity_total": _num(latest.get("commodity_total")),
        "premium_total": _num(latest.get("premium_total")),
        "ecom_total": _num(latest.get("ecom_total")),
    }


def _plan_summary(plan_body, pv):
    if not isinstance(plan_body, dict):        # a text/HTML 200, or a corrupt cache
        plan_body = {}
    rows = [r for r in (plan_body.get("rows") or []) if isinstance(r, dict)]
    wk = 0.0
    for r in rows:
        for k in ("commodity_w1", "commodity_w2", "commodity_w3", "commodity_w4",
                  "premium_w1", "premium_w2", "premium_w3", "premium_w4"):
            wk += _num(r.get(k), 0.0)
    tot = float(sum(_num(r.get("total_planning"), 0.0) for r in rows))
    gt = _num((plan_body or {}).get("grand_total")) or (pv or {}).get("grand_total")
    parts = sum(_num((plan_body or {}).get(k), 0.0)
                for k in ("commodity_total", "premium_total", "ecom_total"))
    return {
        "row_count": len(rows),
        "grand_total": gt,
        "weekly_bucketed_l": round(wk, 2),
        "ecom_unbucketed_l": _num((plan_body or {}).get("ecom_total")),
        "rows_total_l": round(tot, 2),
        "reconciles": bool(gt is not None
                           and abs(parts - gt) < 1.0
                           and abs(tot - gt) < 1.0),
    }


def _plan(pv, errors):
    """Re-pull the 186-row plan ONLY when the uploads header moved. It is a monthly
    Excel upload — polling it on a timer is pointless."""
    out = {"changed": False, "state_file": PLAN_FILE, "row_count": None,
           "grand_total": None, "weekly_bucketed_l": None,
           "ecom_unbucketed_l": None, "rows_total_l": None, "reconciles": None}
    if not pv:
        return out
    stamp = [pv.get("id"), pv.get("version"), pv.get("grand_total"), pv.get("uploaded_at")]
    cached = None
    try:
        with open(PLAN_FILE) as fh:
            cached = json.load(fh)
    except (OSError, ValueError):
        cached = None
    if cached and cached.get("_stamp") == stamp:
        out.update(_plan_summary(cached.get("plan") or {}, pv))
        return out
    try:
        body = _raw("/planning/latest/")
    except Exception as e:                                    # noqa: BLE001
        errors.append("/planning/latest/: %s" % e)
        if cached:
            out.update(_plan_summary(cached.get("plan") or {}, pv))
        return out
    out["changed"] = True
    out.update(_plan_summary(body, pv))
    _write_state(PLAN_FILE, {"_stamp": stamp,
                             "_written_at": datetime.now(IST).isoformat(timespec="seconds"),
                             "plan": body})
    return out


# ---- state -----------------------------------------------------------------
def _write_state(path, obj):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(obj, fh, indent=1, sort_keys=False)
        os.replace(tmp, path)
    except OSError:
        pass          # a state-write failure must never take the adapter down


def _load_slow():
    """The 30-min cache, or None. A cache that is stale, unparseable OR the wrong
    SHAPE is ignored — the caller then does the real fetch. A half-written file
    must never be able to crash the loop, and must never be served as data."""
    try:
        with open(SLOW_FILE) as fh:
            blob = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(blob, dict) or not isinstance(blob.get("inbound"), dict):
        return None
    if not isinstance(blob["inbound"].get("totals_l"), dict):
        return None            # not a block this adapter wrote — do not serve it
    stamp = _ts(blob.get("fetched_at"))
    if stamp is None:
        return None
    age = (datetime.now(IST) - stamp).total_seconds()
    return blob if 0 <= age <= SLOW_MAX_AGE_S else None


# ---- the contract ----------------------------------------------------------
def fetch() -> dict:
    now = datetime.now(IST)
    today = now.date()
    errors: list = []

    data = {
        "tanks": _tanks(errors),
        "inbound": None,
        "open_bulk_pos": [],
        "open_bulk_pos_note": POS_NOTE,
        "pos_line_count": None,
        "plan_version": None,
        "plan": None,
        "freshness": {},
    }

    pv = _plan_version(errors)
    data["plan_version"] = pv
    data["plan"] = _plan(pv, errors)

    cached = None if FORCE_SLOW else _load_slow()
    slow_errors_before = len(errors)
    if cached:
        data["inbound"] = cached.get("inbound")
        data["inbound"]["from_cache"] = True
        data["open_bulk_pos"] = cached.get("open_bulk_pos") or []
        data["pos_line_count"] = cached.get("pos_line_count")
    else:
        otw = _stock_rows("ON_THE_WAY", today, errors)
        ul = _stock_rows("UNDER_LOADING", today, errors)
        ic = _stock_rows("IN_CONTRACT", today, errors)
        # max() over PARSED stamps, not over strings: a string max would rank
        # '2026-09-02T13:59Z' above '2026-09-02T19:00+05:30' (the same instant).
        stamps = [s for s in (_ts(r.get("created_at")) for r in otw + ul + ic) if s]
        inbound = {
            "on_the_way": otw,
            "under_loading": ul,
            "in_contract": ic,
            # float(...) so an empty bucket is 0.0, not int 0 — the type of a
            # litre field must not change with the day's traffic.
            "totals_l": {
                "on_the_way": round(float(sum(r["litres"] or 0 for r in otw)), 2),
                "under_loading": round(float(sum(r["litres"] or 0 for r in ul)), 2),
                "in_contract": round(float(sum(r["litres"] or 0 for r in ic)), 2),
            },
            "totals_kg": {
                "on_the_way": round(float(sum(r["kg"] or 0 for r in otw)), 2),
                "under_loading": round(float(sum(r["kg"] or 0 for r in ul)), 2),
                "in_contract": round(float(sum(r["kg"] or 0 for r in ic)), 2),
            },
            "kg_per_litre": KG_PER_LITRE,
            "latest_row_created_at": (max(stamps).astimezone(IST).isoformat()
                                      if stamps else None),
            "director": _director(errors),
            "fetched_at": now.isoformat(timespec="seconds"),
            "from_cache": False,
        }
        pos, pos_total = _open_pos(errors, today)
        data["inbound"] = inbound
        data["open_bulk_pos"] = pos
        data["pos_line_count"] = pos_total
        # Only cache a CLEAN slow block. A failed cycle that writes its zeros here
        # would be served for the next 30 minutes as if it were data — the exact
        # stale-mirror failure this loop exists to eliminate.
        if len(errors) == slow_errors_before:
            _write_state(SLOW_FILE, {
                "fetched_at": inbound["fetched_at"],
                "inbound": inbound,
                "open_bulk_pos": pos,
                "pos_line_count": pos_total,
            })

    data["freshness"] = {
        "tanks": READING_NOTE,
        "tanks_reading_at": (data["tanks"] or {}).get("reading_at"),
        "inbound": ("event-driven as trucks move, keyed by one EXIM user; "
                    "same-day to 1-day resolution"),
        "open_bulk_pos": "GRPO-driven, lags receipts by a day or two",
        "plan_version": "monthly Excel upload — not live",
    }

    # server_at — EXIM stamps no RESPONSE with its own clock (eximapi.get() hands
    # back (status, body) and no headers), so the honest server-side stamp is the
    # newest row EXIM itself wrote: the latest stock-status created_at, or the
    # plan's uploaded_at. Same convention as the factory/OMS adapters.
    srv = [s for s in (_ts((data["inbound"] or {}).get("latest_row_created_at")),
                       _ts((pv or {}).get("uploaded_at"))) if s]

    return {
        "source": SOURCE,
        "fetched_at": now.isoformat(timespec="seconds"),
        "server_at": max(srv).astimezone(IST).isoformat() if srv else None,
        "ok": not errors,
        "error": "; ".join(errors) if errors else None,
        "data": data,
    }


if __name__ == "__main__":
    print(json.dumps(fetch(), indent=2, default=str))
