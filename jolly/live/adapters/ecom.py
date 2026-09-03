"""ecom.jivo.in — the open e-commerce purchase-order book, live.

Feeds Mark 3's demand side for the q-commerce + marketplace channel. Everything
here comes out of the `ecom` wrapper (~/.local/bin/ecom -> jivo-ecom-pp-cli),
which owns auth and renews its own 1-hour token. No SAP is touched, ever.

Run standalone:      cd jolly && python3 -m live.adapters.ecom

CADENCE
    Every cycle (3 cheap calls, ~200 B):  doctor, primary-summary-version,
    secondary-summary-version. The heavy pull runs ONLY when either version
    stamp moves, or 30 minutes have passed, or there is no cached pull yet.
    Between heavy pulls `data` is served from live/state/ecom.heavy.json and
    `heavy_from_cache` is True — the numbers are real, just not re-fetched.

    The (format, format_sku_code) -> FG map is refreshed hourly, as is Amazon's
    all-time fill rate (both are slow-moving master/cumulative data).

STATE FILES (all under live/state/)
    ecom.versions.json   last seen version stamps + when the heavy pull last ran
    ecom.heavy.json      the last good heavy payload (served on skip cycles)
    ecom.products.json   the hourly SKU->FG map + Amazon all-time fill rate

EVERY KEY IN data, WITH ITS UNIT
    month                    int    the plan month these month-scoped calls used
    year                     int    ditto
    versions                 dict   {primary: str|None, secondary: str|None}
                                    opaque change-detector stamps, not counts
    version_changed          bool   either stamp moved since the previous cycle
    heavy_from_cache         bool   True = the big pull was skipped this cycle
    heavy_fetched_at         str    ISO+05:30 when the heavy pull actually ran
    heavy_age_s              s      how old those figures are, in seconds

    -- open PO book, rolled up to factory FG codes -------------------------
    open_po_litres_by_fg     {FG code: L}  q-commerce OPEN + Amazon-September,
                                    litres still to deliver. Joined ONLY on
                                    (format, format_sku_code); never by name.
    open_po_litres_by_fg_qcomm      {FG code: L}  the 8 q-comm formats alone
    open_po_litres_by_fg_amazon_sep {FG code: L}  Amazon, current month only
    unmapped_l               L      open litres that reached no FG code
    unmapped_top             list   [{format, sku_code, item, litres L}] worst 10
    open_total_l             L      = sum(open_po_litres_by_fg) + unmapped_l
    open_qcomm_l             L      q-commerce open litres (all 8 formats)
    open_amazon_sep_l        L      Amazon open litres dated to the plan month
    open_value_ex_gst_inr    Rs     q-comm open value, PRE-TAX (never mix with
                                    overall-pendency's GST-inclusive figure)

    -- per platform -------------------------------------------------------
    open_by_platform         {PLATFORM: {pos: int, lines: int, litres: L}}
                                    from master_po; AMAZON row is month-scoped
    pendency_check           {platform: {pos, litres L, max_po_date, min_po_date}}
                                    the 4 platforms with a pendency dashboard,
                                    kept as an independent cross-check only
    pendency_vs_master_po_l  L      those 4 platforms: pendency minus master_po

    -- dated demand (replaces Mark 2's even monthly spread) ---------------
    dated_demand             list   [{date 'YYYY-MM-DD', litres L, platform}]
                                    aggregated, sorted; required-by dates
    dated_demand_total_l     L      sum of the above
    dated_demand_overdue_l   L      of that, already past its required-by date
    dated_demand_in_month_l  L      of that, dated inside the plan month
    dated_demand_undated_l   L      open litres with no usable date
    dated_demand_date_basis  str    which field supplied each date

    -- Amazon (a separate feed; NOT in master_po) -------------------------
    amazon.september_l       L      open litres whose po_month == plan month
    amazon.august_stale_l    L      open litres dated to the PREVIOUS month --
                                    stale backlog, never September demand
    amazon.other_month_l     L      open litres from any other month
    amazon.ordered_l         L      PENDING book, total ordered
    amazon.delivered_l       L      PENDING book, delivered so far
    amazon.pending_fill_rate_pct  % delivered/ordered on the PENDING book only
    amazon.fill_rate_pct     %      ALL-TIME Amazon fill rate (55.4 today) from
                                    reports amazon-po-summary, refreshed hourly
    amazon.lines / amazon.pos  int  the WHOLE PENDING book (all months)
    amazon.september_lines / amazon.september_pos  int  the plan-month slice --
                                    these are the counts that go with
                                    open_by_platform['AMAZON']['litres']
    amazon.unmapped_l        L      Amazon open litres with no sap_sku_code

    -- targets and month to date ------------------------------------------
    targets.premium_l        L      month PRIMARY (sell-in) target, premium
    targets.commodity_l      L      ditto, commodity
    targets.total_l          L      premium + commodity
    targets.carried_from     str    'YYYY-MM' the targets were carried FROM --
                                    non-null means these are NOT this month's
    targets.carried_rows_pct %      share of platform rows flagged carried
    targets.open_pending_premium_l / _commodity_l   L  whole-book open pendency
                                    (this pair DOES include Amazon)
    targets.drr_l_per_day    L/day  achieved daily run rate
    targets.require_drr_l_per_day  L/day  rate needed to hit target
    mtd_delivered_l          L      month-to-date sell-in delivered
    mtd_by_platform          {FORMAT: L}
    mtd_complete             bool   False when the server dropped a source
    mtd_missing_sources      list   e.g. ['amazon_po'] -- Amazon is usually here

    products.rows / mapped_rows  int   master-products size and FG coverage
    products.fetched_at / from_cache   hourly map freshness

    -- integrity ----------------------------------------------------------
    feeds                    dict   which calls answered this heavy pull:
                                    {master_po: bool, amazon_po: bool,
                                     pendency: int(0-4), targets: bool,
                                     mtd: bool}
    heavy_complete           bool   master_po AND amazon_po both answered. Only
                                    a complete pull is allowed to replace the
                                    cache -- an incomplete one looks like a
                                    real position (open_qcomm_l 0.0) and would
                                    be served as one for the next 30 minutes.
    server_at_basis          str    what the top-level server_at actually is
    warnings                 list   plain-language flags for the planner
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "ecom"

IST = timezone(timedelta(hours=5, minutes=30), "IST")
STATE_DIR = Path(__file__).resolve().parents[1] / "state"
VERSIONS_FILE = STATE_DIR / "ecom.versions.json"
HEAVY_FILE = STATE_DIR / "ecom.heavy.json"
PRODUCTS_FILE = STATE_DIR / "ecom.products.json"

CALL_TIMEOUT = 60          # seconds, our wall
CLI_TIMEOUT = "45s"        # the CLI gives up first, so we get its error not ours
HEAVY_MAX_AGE_S = 30 * 60  # re-pull at least every 30 minutes
PRODUCTS_MAX_AGE_S = 60 * 60

MASTER_PO_PAGE = 1000
AMAZON_PAGE = 200
MAX_PAGES = 12             # hard stop; 1,617 rows is 2 pages, 637 is 4

PENDENCY_PLATFORMS = ("blinkit", "zepto", "swiggy", "bigbasket")

# Global flags on every call. --data-source live + --no-cache because the
# default 'auto' silently serves the local SQLite mirror on any API failure.
# Never --agent: it implies --compact and strips the litre fields.
GLOBAL_FLAGS = [
    "--json", "--no-input", "--no-color", "--yes",
    "--data-source", "live", "--no-cache",
    "--timeout", CLI_TIMEOUT,
]


class EcomError(RuntimeError):
    """One CLI call did not come back usable. Never fatal to fetch()."""


# --------------------------------------------------------------------------
# the one call helper
# --------------------------------------------------------------------------

def _cli_path() -> str:
    override = os.environ.get("JIVO_ECOM_WRAPPER")
    if override:
        return override
    wrapper = Path.home() / ".local" / "bin" / "ecom"
    if wrapper.exists():
        return str(wrapper)
    return "ecom"


def _slice_json(text: str):
    """Take stdout, find where the JSON starts, decode it.

    The CLI prints informational warnings before the payload; stderr is
    discarded by the caller but stdout can still carry a leading line.
    """
    if not text:
        return None
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        return None
    start = min(starts)
    body = text[start:]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        try:
            obj, _ = json.JSONDecoder().raw_decode(body)
            return obj
        except json.JSONDecodeError:
            return None


def _run(args, timeout: int = CALL_TIMEOUT):
    """Run one ecom command and return its parsed stdout. stderr is dropped."""
    argv = [_cli_path()] + list(args) + GLOBAL_FLAGS
    label = " ".join(str(a) for a in args[:3])
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,   # stderr captured then thrown away
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise EcomError("%s: timed out after %ss" % (label, timeout))
    except FileNotFoundError:
        raise EcomError("ecom CLI not found at %s" % argv[0])
    except OSError as exc:
        raise EcomError("%s: %s" % (label, exc))

    doc = _slice_json(proc.stdout or "")
    if doc is None:
        raise EcomError("%s: no JSON on stdout (exit %s)" % (label, proc.returncode))
    return doc


def _results(doc, label: str):
    """Unwrap {meta:{source}, results:{...}} and refuse anything not live."""
    if not isinstance(doc, dict):
        return doc
    meta = doc.get("meta")
    if isinstance(meta, dict):
        src = meta.get("source")
        if src is not None and str(src).lower() != "live":
            raise EcomError("%s: CLI served '%s' data, not live" % (label, src))
    return doc.get("results", doc)


# --------------------------------------------------------------------------
# coercion — the CLIs hand back "3000.000" as a string
# --------------------------------------------------------------------------

def _f(value, default: float = 0.0) -> float:
    if value is None or value is True or value is False:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _i(value, default=None):
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _s(value) -> str:
    """Join keys stay opaque strings — Zepto uses GUIDs, Amazon uses ASINs."""
    if value is None:
        return ""
    return str(value).strip()


def _iso_date(value):
    """Parse a date, never slice one.

    master_po gives '2026-08-31' (ISO); the pendency dashboard gives
    '02-09-2026' (DD-MM-YYYY) for the same kind of field.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in ("none", "null", "nan", "-"):
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _now_ist() -> datetime:
    return datetime.now(IST)


def _age_s(iso_text) -> float:
    if not iso_text:
        return float("inf")
    try:
        then = datetime.fromisoformat(str(iso_text))
    except ValueError:
        return float("inf")
    if then.tzinfo is None:
        then = then.replace(tzinfo=IST)
    return (_now_ist() - then).total_seconds()


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------

def _read_state(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def _write_state(path: Path, payload) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        pass  # a state write failing must never take the cycle down


# --------------------------------------------------------------------------
# individual calls
# --------------------------------------------------------------------------

def _doctor():
    """Renews the 1-hour token as a side effect. Returns (ok, detail)."""
    doc = _run(["doctor"])
    if not isinstance(doc, dict):
        raise EcomError("doctor: unexpected payload")
    creds = str(doc.get("credentials", "")).lower()
    api = str(doc.get("api", "")).lower()
    ok = creds == "valid" and api == "reachable"
    detail = "credentials=%s api=%s base_url=%s" % (
        doc.get("credentials"), doc.get("api"), doc.get("base_url"))
    return ok, detail


def _version(command: str):
    res = _results(_run(["platform", command]), command)
    if isinstance(res, dict):
        return _s(res.get("version")) or None
    return _s(res) or None


def _paged(args, rows_key: str, page_size: int, label: str):
    """Walk a 0-indexed paginated endpoint until count is satisfied."""
    rows = []
    count = None
    page = 0
    while page < MAX_PAGES:
        res = _results(
            _run(list(args) + ["--page", str(page), "--page-size", str(page_size)]),
            label,
        )
        if not isinstance(res, dict):
            break
        batch = res.get(rows_key) or []
        if not isinstance(batch, list):
            break
        rows.extend(batch)
        if count is None:
            count = _i(res.get("count"))
        if not batch:
            break
        if count is not None and len(rows) >= count:
            break
        if len(batch) < page_size:
            break
        page += 1
    return rows, count


def _fetch_master_po():
    filt = '[{"column":"open_close","values":["OPEN"]}]'
    return _paged(
        ["tables", "data", "--table", "master_po", "--column-filters", filt],
        "data", MASTER_PO_PAGE, "master_po",
    )


def _fetch_amazon_po():
    return _paged(
        ["reports", "amazon-po", "--po-status", "PENDING"],
        "results", AMAZON_PAGE, "amazon-po",
    )


def _fetch_pendency(platform: str):
    return _results(
        _run(["platform", "pendency", "--platform", platform, "--scope", "all"]),
        "pendency/" + platform,
    )


def _fetch_targets(month: int, year: int):
    return _results(
        _run(["platform", "primary-month-targets-dashboard",
              "--month", str(month), "--year", str(year)]),
        "month-targets",
    )


def _fetch_po_litres(month: int, year: int):
    return _results(
        _run(["dashboard", "primary-po-litres",
              "--month", str(month), "--year", str(year)]),
        "primary-po-litres",
    )


def _fetch_products():
    rows, _count = _paged(["master", "products"], "results", MASTER_PO_PAGE, "products")
    return rows


def _fetch_amazon_all_time_fill_rate():
    res = _results(_run(["reports", "amazon-po-summary"]), "amazon-po-summary")
    if isinstance(res, dict):
        summary = res.get("summary") or {}
        if isinstance(summary, dict) and summary.get("fill_rate_pct") is not None:
            return _f(summary.get("fill_rate_pct"))
    raise EcomError("amazon-po-summary: no fill_rate_pct in payload")


# --------------------------------------------------------------------------
# the SKU -> FG map (hourly)
# --------------------------------------------------------------------------

def _build_product_map(rows):
    """(format, format_sku_code) -> FG code.

    Names are NEVER a join key: 19 item names in this table resolve to more
    than one FG code ('MUSTARD 1L' -> FG0000030 or FG0000275).
    """
    exact = {}
    folded = {}
    mapped = 0
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        fmt = _s(row.get("format")).upper()
        sku = _s(row.get("format_sku_code"))
        fg = _s(row.get("sku_sap_code"))
        if not fmt or not sku or not fg:
            continue
        exact.setdefault("%s\x00%s" % (fmt, sku), fg)
        folded.setdefault("%s\x00%s" % (fmt, sku.casefold()), fg)
        mapped += 1
    return {"exact": exact, "folded": folded, "rows": len(rows or []), "mapped": mapped}


def _lookup_fg(pmap, fmt: str, sku: str):
    key = "%s\x00%s" % (_s(fmt).upper(), _s(sku))
    fg = pmap["exact"].get(key)
    if fg:
        return fg, False
    fg = pmap["folded"].get("%s\x00%s" % (_s(fmt).upper(), _s(sku).casefold()))
    if fg:
        return fg, True
    return None, False


def _products(warnings):
    """Hourly: the FG map plus Amazon's all-time fill rate."""
    cached = _read_state(PRODUCTS_FILE) or {}
    fresh_enough = _age_s(cached.get("fetched_at")) < PRODUCTS_MAX_AGE_S
    if fresh_enough and cached.get("rows"):
        pmap = _build_product_map(cached.get("rows"))
        return pmap, cached.get("fetched_at"), True, _f(cached.get("amazon_fill_rate_pct"), 0.0) or None

    rows = _fetch_products()
    fill_rate = None
    try:
        fill_rate = _fetch_amazon_all_time_fill_rate()
    except EcomError as exc:
        warnings.append("amazon all-time fill rate unavailable: %s" % exc)
        fill_rate = _f(cached.get("amazon_fill_rate_pct"), 0.0) or None
    stamp = _now_ist().isoformat()
    _write_state(PRODUCTS_FILE, {
        "fetched_at": stamp,
        "rows": rows,
        "amazon_fill_rate_pct": fill_rate,
    })
    return _build_product_map(rows), stamp, False, fill_rate


# --------------------------------------------------------------------------
# the heavy pull
# --------------------------------------------------------------------------

def _heavy(month: int, year: int):
    """Everything expensive. Returns (data_fragment, errors, server_at)."""
    errors = []
    warnings = []
    data = {"month": month, "year": year}
    server_at = None
    # which feeds actually answered. master_po + amazon-po ARE the demand book;
    # without either one the payload is not a position, and must never be
    # cached as though it were.
    feeds = {"master_po": False, "amazon_po": False,
             "pendency": 0, "targets": False, "mtd": False}

    # ---- the SKU -> FG map (hourly, cached) -------------------------------
    pmap = {"exact": {}, "folded": {}, "rows": 0, "mapped": 0}
    prod_stamp, prod_cached, amazon_fill_rate = None, None, None
    try:
        pmap, prod_stamp, prod_cached, amazon_fill_rate = _products(warnings)
    except EcomError as exc:
        errors.append("products: %s" % exc)
        warnings.append("no SKU->FG map this cycle; every open litre is unmapped")
    data["products"] = {
        "rows": pmap["rows"],
        "mapped_rows": pmap["mapped"],
        "fetched_at": prod_stamp,
        "from_cache": bool(prod_cached),
    }

    # ---- q-commerce open PO book (master_po) ------------------------------
    by_fg_q = defaultdict(float)
    by_platform = {}
    dated = defaultdict(float)
    unmapped_rows = defaultdict(lambda: {"litres": 0.0, "item": ""})
    unmapped_q = 0.0
    undated_l = 0.0
    open_q_l = 0.0
    open_value = 0.0
    casefold_hits = 0
    try:
        rows, count = _fetch_master_po()
        if count is not None and len(rows) < count:
            warnings.append(
                "master_po: pulled %d of %d OPEN rows (page cap)" % (len(rows), count))
        agg = defaultdict(lambda: {"pos": set(), "lines": 0, "litres": 0.0})
        for row in rows:
            if not isinstance(row, dict):
                continue
            fmt = _s(row.get("format")).upper() or "UNKNOWN"
            ordered = _f(row.get("total_order_liters"))
            delivered = _f(row.get("total_delivered_liters"))
            litres = max(ordered - delivered, 0.0)
            open_q_l += litres
            open_value += max(
                _f(row.get("total_order_amt_exclusive"))
                - _f(row.get("total_delivered_amt_exclusive")), 0.0)

            slot = agg[fmt]
            slot["lines"] += 1
            slot["litres"] += litres
            po = _s(row.get("po_number"))
            if po:
                slot["pos"].add(po)

            sku = _s(row.get("sku_code"))
            fg, was_folded = _lookup_fg(pmap, fmt, sku)
            if fg:
                by_fg_q[fg] += litres
                if was_folded:
                    casefold_hits += 1
            else:
                unmapped_q += litres
                key = "%s\x00%s" % (fmt, sku)
                unmapped_rows[key]["litres"] += litres
                unmapped_rows[key]["item"] = _s(row.get("item")) or _s(row.get("sku_name"))

            # required-by date: delivery date if the platform gave one, else
            # the PO's own expiry, else the PO date.
            when = (_iso_date(row.get("delivery_date"))
                    or _iso_date(row.get("po_expiry_date"))
                    or _iso_date(row.get("po_date")))
            if when:
                dated[(when, fmt)] += litres
            else:
                undated_l += litres

        by_platform = {
            fmt: {"pos": len(slot["pos"]), "lines": slot["lines"],
                  "litres": round(slot["litres"], 2)}
            for fmt, slot in sorted(agg.items())
        }
        feeds["master_po"] = True
    except EcomError as exc:
        errors.append("master_po: %s" % exc)

    # ---- Amazon (its own feed; NOT in master_po) --------------------------
    amazon = {
        "september_l": 0.0, "august_stale_l": 0.0, "other_month_l": 0.0,
        "ordered_l": 0.0, "delivered_l": 0.0, "lines": 0, "pos": 0,
        "unmapped_l": 0.0, "pending_fill_rate_pct": None,
        "fill_rate_pct": amazon_fill_rate,
        "fill_rate_basis": "all-time, reports amazon-po-summary (refreshed hourly)",
    }
    by_fg_amz = defaultdict(float)
    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year
    try:
        rows, count = _fetch_amazon_po()
        if count is not None and len(rows) < count:
            warnings.append(
                "amazon-po: pulled %d of %d PENDING rows (page cap)" % (len(rows), count))
        pos = set()
        sep_pos = set()
        sep_lines = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            ordered = _f(row.get("total_order_liters"))
            delivered = _f(row.get("total_delivered_liters"))
            litres = max(ordered - delivered, 0.0)
            amazon["lines"] += 1
            amazon["ordered_l"] += ordered
            amazon["delivered_l"] += delivered
            po = _s(row.get("po_number"))
            if po:
                pos.add(po)

            row_month = _i(row.get("po_month"))
            row_year = _i(row.get("year"), year)
            if row_month == month and row_year == year:
                sep_lines += 1
                if po:
                    sep_pos.add(po)
                amazon["september_l"] += litres
                fg = _s(row.get("sap_sku_code"))
                if fg:
                    by_fg_amz[fg] += litres
                else:
                    amazon["unmapped_l"] += litres
                when = _iso_date(row.get("expiry_date")) or _iso_date(row.get("order_date"))
                if when:
                    dated[(when, "AMAZON")] += litres
                else:
                    undated_l += litres
            elif row_month == prev_month and row_year == prev_year:
                amazon["august_stale_l"] += litres
            else:
                amazon["other_month_l"] += litres
        amazon["pos"] = len(pos)
        if amazon["ordered_l"] > 0:
            amazon["pending_fill_rate_pct"] = round(
                100.0 * amazon["delivered_l"] / amazon["ordered_l"], 2)
        if amazon["august_stale_l"] > amazon["september_l"]:
            warnings.append(
                "Amazon open book is mostly stale backlog: %.0f L dated %04d-%02d vs "
                "%.0f L dated %04d-%02d — never feed the stale share into the plan"
                % (amazon["august_stale_l"], prev_year, prev_month,
                   amazon["september_l"], year, month))
        # pos/lines here are the PLAN-MONTH slice, so the row is internally
        # consistent with its own litres. The whole PENDING book (637 lines /
        # 69 POs, 93% August backlog) stays in data["amazon"].
        amazon["september_pos"] = len(sep_pos)
        amazon["september_lines"] = sep_lines
        by_platform["AMAZON"] = {
            "pos": len(sep_pos), "lines": sep_lines,
            "litres": round(amazon["september_l"], 2),
        }
        feeds["amazon_po"] = True
    except EcomError as exc:
        errors.append("amazon-po: %s" % exc)

    for key in ("september_l", "august_stale_l", "other_month_l", "ordered_l",
                "delivered_l", "unmapped_l"):
        amazon[key] = round(amazon[key], 2)
    data["amazon"] = amazon

    # ---- the FG rollups ---------------------------------------------------
    combined = defaultdict(float)
    for fg, litres in by_fg_q.items():
        combined[fg] += litres
    for fg, litres in by_fg_amz.items():
        combined[fg] += litres

    unmapped_total = unmapped_q + amazon["unmapped_l"]
    data["open_po_litres_by_fg"] = {
        fg: round(v, 2) for fg, v in sorted(combined.items(), key=lambda kv: -kv[1])}
    data["open_po_litres_by_fg_qcomm"] = {
        fg: round(v, 2) for fg, v in sorted(by_fg_q.items(), key=lambda kv: -kv[1])}
    data["open_po_litres_by_fg_amazon_sep"] = {
        fg: round(v, 2) for fg, v in sorted(by_fg_amz.items(), key=lambda kv: -kv[1])}
    data["unmapped_l"] = round(unmapped_total, 2)
    data["unmapped_top"] = [
        {"format": k.split("\x00")[0], "sku_code": k.split("\x00")[1],
         "item": v["item"], "litres": round(v["litres"], 2)}
        for k, v in sorted(unmapped_rows.items(), key=lambda kv: -kv[1]["litres"])[:10]
    ]
    data["open_qcomm_l"] = round(open_q_l, 2)
    data["open_amazon_sep_l"] = amazon["september_l"]
    data["open_total_l"] = round(open_q_l + amazon["september_l"], 2)
    data["open_value_ex_gst_inr"] = round(open_value, 2)
    data["open_by_platform"] = by_platform
    data["open_by_platform_source"] = (
        "master_po open_close=OPEN for the 8 q-commerce formats; "
        "AMAZON from reports amazon-po PENDING scoped to the plan month")
    if casefold_hits:
        warnings.append(
            "%d q-comm lines joined to an FG only after case-folding the SKU code"
            % casefold_hits)
    if open_q_l > 0 and unmapped_q / open_q_l > 0.05:
        warnings.append("%.1f%% of q-comm open litres reached no FG code"
                        % (100.0 * unmapped_q / open_q_l))

    # ---- dated demand -----------------------------------------------------
    data["dated_demand"] = [
        {"date": when, "platform": fmt, "litres": round(litres, 2)}
        for (when, fmt), litres in sorted(dated.items())
    ]
    today = _now_ist().date().isoformat()
    month_prefix = "%04d-%02d" % (year, month)
    data["dated_demand_total_l"] = round(sum(dated.values()), 2)
    data["dated_demand_overdue_l"] = round(
        sum(v for (when, _f2), v in dated.items() if when < today), 2)
    data["dated_demand_in_month_l"] = round(
        sum(v for (when, _f2), v in dated.items() if when.startswith(month_prefix)), 2)
    data["dated_demand_undated_l"] = round(undated_l, 2)
    data["dated_demand_date_basis"] = (
        "q-comm: delivery_date else po_expiry_date else po_date; "
        "Amazon: expiry_date else order_date")

    # ---- independent cross-check: the 4 pendency dashboards ---------------
    pendency = {}
    pend_total = 0.0
    server_stamps = []
    for platform in PENDENCY_PLATFORMS:
        try:
            res = _fetch_pendency(platform)
        except EcomError as exc:
            errors.append("pendency/%s: %s" % (platform, exc))
            continue
        if not isinstance(res, dict):
            continue
        totals = res.get("totals") or {}
        litres = _f(totals.get("pending_ltrs"))
        pend_total += litres
        fmt = _s(res.get("format")).upper() or platform.upper()
        pendency[platform] = {
            "format": fmt,
            "pos": _i(totals.get("open_pos"), 0),
            "litres": round(litres, 2),
            "max_po_date": _iso_date(res.get("max_po_date")),
            "min_po_date": _iso_date(res.get("min_po_date")),
            "server_date": _iso_date(res.get("max_po_date")),
        }
        stamp = _iso_date(res.get("max_po_date"))
        if stamp:
            server_stamps.append(stamp)
        feeds["pendency"] += 1
    data["pendency_check"] = pendency
    if pendency:
        covered = {v["format"] for v in pendency.values()}
        mpo_side = sum(by_platform.get(f, {}).get("litres", 0.0) for f in covered)
        data["pendency_vs_master_po_l"] = round(pend_total - mpo_side, 2)
        if mpo_side > 0 and abs(pend_total - mpo_side) / mpo_side > 0.02:
            warnings.append(
                "pendency dashboards and master_po disagree by %.0f L on the 4 "
                "shared platforms (%.0f vs %.0f)"
                % (pend_total - mpo_side, pend_total, mpo_side))
    else:
        data["pendency_vs_master_po_l"] = None

    # ---- targets ----------------------------------------------------------
    targets = {
        "premium_l": None, "commodity_l": None, "total_l": None,
        "carried_from": None, "carried_rows_pct": None,
        "open_pending_premium_l": None, "open_pending_commodity_l": None,
        "drr_l_per_day": None, "require_drr_l_per_day": None,
    }
    try:
        res = _fetch_targets(month, year)
        if isinstance(res, dict):
            prem = (res.get("premium") or {}).get("total") or {}
            comm = (res.get("commodity") or {}).get("total") or {}
            targets["premium_l"] = round(_f(prem.get("targets")), 2)
            targets["commodity_l"] = round(_f(comm.get("targets")), 2)
            targets["total_l"] = round(targets["premium_l"] + targets["commodity_l"], 2)
            targets["open_pending_premium_l"] = round(_f(prem.get("open_pending_ltrs")), 2)
            targets["open_pending_commodity_l"] = round(_f(comm.get("open_pending_ltrs")), 2)
            targets["drr_l_per_day"] = round(_f(prem.get("drr")) + _f(comm.get("drr")), 2)
            targets["require_drr_l_per_day"] = round(
                _f(prem.get("require_drr")) + _f(comm.get("require_drr")), 2)

            all_rows = []
            for head in ("premium", "commodity"):
                block = res.get(head) or {}
                all_rows.extend(block.get("rows") or [])
            carried = [r for r in all_rows
                       if isinstance(r, dict) and r.get("targets_carried")]
            if all_rows:
                targets["carried_rows_pct"] = round(100.0 * len(carried) / len(all_rows), 1)
            froms = [_s(r.get("targets_carried_from")) for r in carried
                     if _s(r.get("targets_carried_from"))]
            if froms:
                targets["carried_from"] = max(set(froms), key=froms.count)
                warnings.append(
                    "%d%% of platform target rows are CARRIED FORWARD from %s — the "
                    "'%04d-%02d target' was never set for this month"
                    % (targets["carried_rows_pct"], targets["carried_from"], year, month))
            for row in all_rows:
                if isinstance(row, dict):
                    stamp = _iso_date(row.get("date"))
                    if stamp:
                        server_stamps.append(stamp)
                        break
            feeds["targets"] = True
    except EcomError as exc:
        errors.append("month-targets: %s" % exc)
    data["targets"] = targets

    # ---- month-to-date delivered -----------------------------------------
    data["mtd_delivered_l"] = None
    data["mtd_by_platform"] = {}
    data["mtd_complete"] = None
    data["mtd_missing_sources"] = []
    try:
        res = _fetch_po_litres(month, year)
        if isinstance(res, dict):
            by_fmt = {}
            for row in res.get("platforms") or []:
                if isinstance(row, dict):
                    by_fmt[_s(row.get("format")).upper()] = round(
                        _f(row.get("delivered_ltrs")), 2)
            data["mtd_by_platform"] = by_fmt
            data["mtd_delivered_l"] = round(sum(by_fmt.values()), 2)
            # HTTP 200 with a dead source inside: branch on errors[], always.
            bad = [_s(e.get("source")) for e in (res.get("errors") or [])
                   if isinstance(e, dict)]
            data["mtd_missing_sources"] = bad
            data["mtd_complete"] = not bad
            if bad:
                warnings.append(
                    "month-to-date delivered is missing %s — the server returned 200 "
                    "with an error inside" % ", ".join(bad))
            feeds["mtd"] = True
    except EcomError as exc:
        errors.append("primary-po-litres: %s" % exc)

    if server_stamps:
        server_at = max(server_stamps)
    # No ecom response carries a generated-at clock (meta is {"source":"live"}
    # and nothing more), so server_at is the newest PO DATE the server knows
    # about. It is a data-freshness marker, NOT a heartbeat: on a quiet day it
    # stops advancing while the feed is perfectly healthy. Never compute
    # "is the source down" from it -- use fetched_at.
    data["server_at_basis"] = (
        "newest po_date on the server's own book (max of pendency max_po_date "
        "and the targets row date) -- ecom returns no generated-at clock; "
        "this is data freshness, not a heartbeat")

    # ---- is this payload a position at all? -------------------------------
    data["feeds"] = dict(feeds)
    data["heavy_complete"] = bool(feeds["master_po"] and feeds["amazon_po"])
    if not data["heavy_complete"]:
        missing = [n for n in ("master_po", "amazon_po") if not feeds[n]]
        warnings.append(
            "INCOMPLETE: %s did not answer, so the open-PO book is missing a "
            "whole channel — these litres are NOT the position"
            % " and ".join(missing))

    data["warnings"] = warnings
    return data, errors, server_at


# --------------------------------------------------------------------------
# the contract
# --------------------------------------------------------------------------

def fetch() -> dict:
    now = _now_ist()
    fetched_at = now.isoformat()
    errors = []

    month = _i(os.environ.get("ECOM_PLAN_MONTH"), now.month)
    year = _i(os.environ.get("ECOM_PLAN_YEAR"), now.year)

    # --- every cycle: doctor (this is what renews the 1-hour token) --------
    doctor_ok = False
    try:
        doctor_ok, detail = _doctor()
        if not doctor_ok:
            errors.append("doctor: %s" % detail)
    except EcomError as exc:
        errors.append("doctor: %s" % exc)

    # --- every cycle: the two ~60-byte change detectors --------------------
    versions = {"primary": None, "secondary": None}
    reachable = 0
    for key, command in (("primary", "primary-summary-version"),
                         ("secondary", "secondary-summary-version")):
        try:
            versions[key] = _version(command)
            reachable += 1
        except EcomError as exc:
            errors.append("%s: %s" % (command, exc))

    prev = _read_state(VERSIONS_FILE) or {}
    prev_versions = prev.get("versions") or {}
    changed = any(
        versions[k] is not None
        and prev_versions.get(k) is not None
        and versions[k] != prev_versions.get(k)
        for k in ("primary", "secondary"))

    cached_heavy = _read_state(HEAVY_FILE) or {}
    cached_data = cached_heavy.get("data")
    heavy_age = _age_s(cached_heavy.get("fetched_at"))

    forced = os.environ.get("ECOM_FORCE_HEAVY", "").lower() in ("1", "true", "yes")
    want_heavy = forced or changed or cached_data is None or heavy_age >= HEAVY_MAX_AGE_S
    # Two failures already = the server is not answering. Record and move on;
    # never follow them with 15 more calls. The three cheap probes are the
    # canary: one may fail (a flaky doctor still leaves the data routes up),
    # two means stop.
    cheap_failures = (0 if doctor_ok else 1) + (2 - reachable)
    can_reach = reachable > 0 and cheap_failures <= 1
    do_heavy = want_heavy and can_reach
    if want_heavy and not can_reach:
        errors.append(
            "heavy pull skipped: %d of 3 cheap probes failed — not storming ecom"
            % cheap_failures)

    heavy_errors = []
    if do_heavy:
        heavy_data, heavy_errors, server_at = _heavy(month, year)
        errors.extend(heavy_errors)
        # Only a COMPLETE pull may replace the cache. A pull that lost
        # master_po still carries a plausible-looking open_by_platform (the
        # AMAZON row alone) — caching that publishes open_qcomm_l = 0 as a
        # real position for the next 30 minutes.
        if heavy_data.get("heavy_complete"):
            _write_state(HEAVY_FILE, {
                "fetched_at": fetched_at,
                "server_at": server_at,
                "data": heavy_data,
            })
            heavy_fetched_at = fetched_at
            from_cache = False
        elif cached_data is not None:
            # incomplete or empty — keep the last good numbers, say so loudly
            partial = list(heavy_data.get("warnings") or [])
            heavy_data = dict(cached_data)
            heavy_data["warnings"] = list(heavy_data.get("warnings") or []) + [
                w for w in partial if w.startswith("INCOMPLETE:")]
            server_at = cached_heavy.get("server_at")
            heavy_fetched_at = cached_heavy.get("fetched_at")
            from_cache = True
            errors.append("heavy pull was incomplete; serving last good complete pull")
        else:
            heavy_fetched_at = None
            from_cache = False
    elif cached_data is not None:
        heavy_data = cached_data
        server_at = cached_heavy.get("server_at")
        heavy_fetched_at = cached_heavy.get("fetched_at")
        from_cache = True
    else:
        heavy_data = {"month": month, "year": year, "warnings": []}
        server_at = None
        heavy_fetched_at = None
        from_cache = False
        if want_heavy:
            errors.append("ecom unreachable and no cached pull to fall back on")

    data = dict(heavy_data)
    data["versions"] = versions
    data["version_changed"] = changed
    data["heavy_from_cache"] = from_cache
    data["heavy_fetched_at"] = heavy_fetched_at
    data["heavy_age_s"] = round(_age_s(heavy_fetched_at), 1) if heavy_fetched_at else None
    warnings = list(data.get("warnings") or [])
    if from_cache:
        warnings.append("heavy pull skipped this cycle; figures are from %s"
                        % heavy_fetched_at)
    data["warnings"] = warnings

    _write_state(VERSIONS_FILE, {
        "versions": versions,
        "checked_at": fetched_at,
        "heavy_fetched_at": heavy_fetched_at,
        "version_changed": changed,
    })

    ok = doctor_ok and not errors
    return {
        "source": SOURCE,
        "fetched_at": fetched_at,
        "server_at": server_at,
        "ok": bool(ok),
        "error": "; ".join(errors) if errors else None,
        "data": data,
    }


if __name__ == "__main__":
    payload = fetch()
    json.dump(payload, sys.stdout, indent=2, sort_keys=False, default=str)
    sys.stdout.write("\n")
    sys.exit(0 if payload.get("ok") else 1)
