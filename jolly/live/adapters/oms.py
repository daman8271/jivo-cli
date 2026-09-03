"""OMS adapter — sales orders (GT/MT) from oms.jivo.in, via oms-cli/oms-pp-cli.

Read-only. Obeys live/README.md. Account: Daman@oms.com (role `billing`, user_id 94),
kept in its OWN config file so the default ~/.config/oms-pp-cli/config.toml (paramjot's
token) is never touched.

WHY THE CURSOR EXISTS
    `orders list` returns only 3 orders for this billing account, but `orders detail <id>`
    has NO role filter and the ids are dense + sequential (3090 = ORD-20260902-0015).
    So the order book is walked forward one id at a time from a persisted cursor.

CADENCE
    Every cycle : probe detail for cursor+1, +2, … until 3 consecutive misses (cap 40 new
                  ids), then `orders dashboard` + `dashboard summary`.
    Every 30 min: `invoices logs` (95 KB) + `orders status`.
    Never       : `account profile` — its response body carries the user's PBKDF2 password
                  hash. It is blocked by the allowlist in _run(), not merely avoided.

UNITS — every number below is one of: L (litres), pcs (pieces = bottles/pouches, NOT
cartons, C-0001), boxes (cartons), INR (rupees), or a count.

============================  data  ============================

data.cursor : dict — the walk's own state
    .value              int   — highest order id settled (found, or a gap seen GAP_SETTLE cycles)
    .previous           int   — the cursor this cycle started from
    .seeded             bool  — true on the very first run (no cursor file existed)
    .probed_ids         [int] — every id asked for this cycle
    .found_ids          [int] — ids that returned an order this cycle
    .missing_ids        [int] — ids that returned "not found" (CLI exit 3) this cycle
    .errored_ids        [int] — ids whose probe failed for any OTHER reason. NEVER settled
                                as a gap — a 5xx must not be mistaken for a deleted order.
    .gaps_pending       {id: misses} — ids missed BELOW a known-higher id, i.e. real holes,
                                counted across cycles and settled at GAP_SETTLE. An id past
                                the top of the book is never listed: it is tomorrow's order,
                                not a hole, and settling it would skip real orders forever.
    .stopped_because    str   — "consecutive_misses" | "cap"
    .miss_stop          int   — consecutive misses that ended this walk (3, or 25 on a deep probe)
    .deep_probe         bool  — this cycle probed deeper than usual. After STALL_CYCLES (20)
                                cycles that found nothing, ONE cycle probes DEEP_MISS_STOP (25)
                                ids ahead. Without it, MISS_STOP consecutive DELETED ids would
                                stop the walk short of every later order, forever — the loop
                                would look healthy and silently go blind.
    .idle_cycles        int   — cycles in a row that found no order, before this one
    .cap                int   — max new ids this cycle (OMS_MAX_NEW, default 40)

data.orders_new_this_cycle : [order] — orders first seen on THIS cycle (newest id last)
data.orders_recent         : [order] — the last RECENT_N (200) orders by id, newest first,
                                       persisted across cycles in live/state/oms.orders.json

    order (each element of both lists):
        id                int   — OMS order id (the cursor walks these)
        order_number      str   — "ORD-YYYYMMDD-NNNN"; the date in it is the ORDER date
        customer          str   — card_name
        card_code         str   — SAP-style CardCode, e.g. CUSTA000169
        company           str   — OMS's own company id on the header, RAW ("1" = Jivo
                                  Wellness / Oil). oms-pp-cli has no --company flag, so
                                  this is how company scoping is CHECKED, not assumed —
                                  rolled up in data.company_scope.
        created           str   — created_at, server ISO (UTC "Z")
        updated           str   — updated_at, server ISO (UTC "Z")
        delivery_date     str   — "YYYY-MM-DD", the promised date
        status_code       str   — machine status, e.g. "COMPLETED" (key for open_by_status)
        status_name       str   — status_display, e.g. "Completed"
        is_terminal       bool  — status_code in TERMINAL (an ASSUMED set — see .note)
        dispatch_from_id  int   — 2 = FACTORY. Does NOT match `orders dispatches` ids.
        dispatch_from_name str  — "FACTORY"
        party_state       str
        created_by_name   str
        po_number         str|None
        warehouse_code    str|None
        is_foc            bool  — free-of-cost order
        sap_created       bool
        sap_doc_number    str|None
        total_amount      INR   — order value as OMS states it
        litres            L     — sum of line.ltrs (OMS's own figure, never a parsed pack size).
                                  ALL categories together — see litres_by_category before
                                  treating this as oil.
        litres_by_category {cat: L} — the same litres split by OMS's own line `category`.
                                  Live on 2026-09-03: OIL, BEVERAGES (packaged drinking
                                  water) and MART all appear in this one order book.
        lines_count       int
        last_seen_at      str   — when WE last read this order (ISO, IST)
        channel/main_group* — copied through only if the header carries them (usually absent)
        lines : [
            code       str  — item_code, e.g. FG0000359
            name       str  — item_name, e.g. "SOYABEAN OIL 750 GMS 12 PCS POUCH"
            qty        pcs  — PIECES (bottles/pouches). boxes = qty / pcs. Multiplying qty by
                              the "12 PCS" in the name inflates volume 12x (C-0001).
            pcs        int  — pieces per box
            boxes      int  — cartons
            ltrs       L    — OMS-computed litres for the line
            qty_scheme pcs  — scheme give-away pieces (0 on every line seen so far, but
                              it is volume the plant still fills — never dropped)
            rate       INR  — basic_price, per piece
            total      INR  — line value
            tax_rate   %    — GST rate
            variety / sub_group / item_type / category / brand : str
        ]

data.open_by_status : {status_code: {...}} — EVERY status bucket over EVERY persisted order
        status_name    str
        count          int
        litres         L    — sum of order.litres in the bucket (ALL categories)
        litres_by_category {cat: L} — that same total split by line category. The Oil order
                            book is not all oil: 29 orders read live on 2026-09-03 held
                            2,460,201 L OIL, 91,656 L BEVERAGES (water) and 42,000 L MART.
        amount_inr     INR
        terminal       bool
        oldest_seen_at str  — the staleness badge: this bucket is only as fresh as this
    NOTE: an order's status is whatever it was when we last read it. By default the loop
    does NOT re-poll orders it has already seen (OMS_REFRESH_OPEN=0), so a non-terminal
    bucket ages. Set OMS_REFRESH_OPEN=N to re-poll the N stalest non-terminal orders per
    cycle (costs N extra live calls); `oldest_seen_at` is the honest badge either way.

data.open_total : {count, litres L, litres_by_category {cat: L}, amount_inr INR,
                   amount_inr_ex_outliers INR, litres_ex_outliers L, rs_per_l INR/L,
                   rs_per_l_ex_outliers INR/L, headline_note str}
    — non-terminal buckets only.
    `amount_inr` and `litres` are RAW: exactly what OMS holds, never corrected. The
    `*_ex_outliers` pair is the same total with every price_outliers line on a
    NON-TERMINAL order deducted, published BESIDE the raw one so a Rs/L headline is not
    built on a bad rate. Live 2026-09-03: Rs 74,55,619 / 16,710 L = Rs 446/L raw, of
    which Rs 48,35,715 is three orders (3117/3118/3119) pricing FG0000030 MUSTARD KACHI
    GHANI 1 LTR at Rs 3,223.81/L against Rs 160/L for the same SKU on order 3106 —
    Rs 26,19,904 / 15,210 L = Rs 172/L once they are out. `headline_note` says in words
    how many orders and lines came out and why. Flags on TERMINAL orders are never
    deducted: open_total never counted them. `rs_per_l` is null when litres is 0.

data.stale : bool — true when NO live call was possible this cycle (binary or config
    gone) and every figure below is the persisted book from an earlier cycle. The keys
    keep their shape either way, so a panel degrades to a stale badge, never a KeyError.

data.company_scope : {expected, by_company {company: orders}, clean, foreign_orders,
    unknown_orders, note}
    live/README.md wants `--company oil` on every OMS call; oms-pp-cli HAS NO SUCH FLAG
    (checked --help globally and per command). Scoping is server-side on this account, so
    this counts the company OMS stamps on each order header instead. `clean: false` means
    a foreign-company order entered the book and every litre/rupee total here is mixed.

data.price_outliers : [ {...} ] — every line in orders_recent whose implied INR/L falls
    outside PRICE_MIN_PER_L..PRICE_MAX_PER_L (default 3..1000 INR/L; real oil runs
    Rs 32-360/L and real packaged water Rs 5.6-12.7/L). Carries order_id, order_number, customer, status_code, code,
    name, inr_per_litre, ltrs L, total_inr, band_inr_per_litre. A FLAG, never a correction:
    nothing is altered or dropped. Live example — order 3118 prices FG0000030 MUSTARD KACHI
    GHANI 1 LTR at Rs 3,223.81/L while order 3106 prices the same SKU at Rs 160/L, and OMS's
    own total agrees with the outlier. Never headline an INR/L figure without checking this
    list is empty.

data.dashboards : dict
    .orders_dashboard  raw `orders dashboard` payload (or null + an error)
    .dashboard_summary raw `dashboard summary` payload (or null + an error)
    .agree             {checked, total_orders_match, total_revenue_match, each endpoint's
                       total_orders + total_revenue INR, and the WINDOW each was asked
                       for — `dashboard summary` self-reports {"year":2026,"month":0} =
                       all of 2026, `orders dashboard` states none} — recomputed EVERY
                       cycle. The two were seen 3 orders / ₹56,50,581 vs 4 orders /
                       ₹60,35,957 minutes apart on 2026-08-22, and identical on 2026-09-03.
                       Intermittent, so check this rather than assuming either way.
    .note              str — BOTH are scoped to this billing user (an admin token saw 2,468
                       orders), so NEITHER is a company total. Never mix them in one panel;
                       the site must label whichever it shows.

data.statuses : [{id, name}] — the order-status master, refreshed on the heavy cycle and
    cached. 12 statuses, not the 11 every repo doc claims — id 12 is "Mart Approval".
    Never hard-code 11. null until the first heavy cycle of a fresh state dir.
data.statuses_fetched_at : str — when that master was last read (ISO, IST)

data.so_to_invoice_map : PRESENT ONLY ON A HEAVY CYCLE (else the key is absent)
    [ {so_number, sap_doc_num, sap_doc_entry, party_name, total_amount INR, warehouse,
       branch, status, created_at, log_id, error_message, is_latest_for_so} ]
    One entry per SO NUMBER, not per log row: `so_number` arrives as a comma-separated
    string ("1726086864, 1726086755") and is split here. NOT unique on so_number — a SO
    rejected and re-submitted appears once per log row, so keying it as a dict drops one.
    Ordered NEWEST created_at FIRST, and the newest row per SO carries
    `is_latest_for_so: true` — filter on that rather than on position, because {so: row}
    keeps the LAST element in Python while Array.find keeps the FIRST.
    `created_at` is passed through RAW (server UTC "Z"), unlike the IST stamps below.

data.invoice_logs : PRESENT ONLY ON A HEAVY CYCLE
    .rows            int
    .by_status       {status: count}   — POSTED_TO_SAP / APPROVED / REJECTED
    .by_warehouse    {warehouse: count}
    .note            str  — the caveats below, carried in-band to the site
    .first_created_at / .last_created_at  str — IST, converted from the server's UTC
    .fg_stock_latest [ {item_code, item_name, warehouse_code, quantity pcs,
                        warehouse_stock pcs, at} ] — the newest submission-time stock
                        reading per (item_code, warehouse_code), `at` in IST. NOT a live
                        stock figure: it is what the warehouse held when that invoice was
                        submitted, and the newest may be days old. "Newest" is decided by
                        comparing PARSED instants, never ISO strings.
    This queue is low-volume and gappy (35 rows, 2026-07-28 → 08-31). It is the invoice
    REVIEW queue, not every invoice.

TOP-LEVEL server_at is the newest SERVER-side stamp anything read this cycle carried,
converted to IST: the created/updated of orders found this cycle, and on a heavy cycle
the newest `invoices logs` row. It is null on a quiet, non-heavy cycle — OMS's dashboards
carry no server timestamp of their own, and dating them from our own clock would be a lie.

data.heavy_refresh   : bool — did this cycle do the 30-minute work
data.heavy_fetched_at: str  — when the heavy work was last ATTEMPTED (ISO, IST). Stamped
    on the attempt, not the success: stamping only on success turned a failing
    `invoices logs` into 2 extra calls every 3 minutes instead of every 30.
data.heavy_ok_at     : str  — when it last actually RETURNED. If this lags
    heavy_fetched_at, so_to_invoice_map / invoice_logs are absent by failure, not by gate.
data.counts          : {orders_stored, orders_new, probes_this_cycle}
data.calls           : [{cmd, ok, seconds, code, source}] — every live call this cycle
    made. `source` is the CLI's own provenance stamp; anything but "live" means the
    payload was DISCARDED, never published.
data.cli_path        : str  — the oms-pp-cli binary this cycle actually ran. The Mac
    build and the Linux build (oms-pp-cli.linux) sit side by side in oms-cli/; running
    the wrong one is an OSError [Errno 8] Exec format error, not a wrong number.
data.note            : str  — the standing caveats, carried to the site

STATE FILES (live/state/)
    oms.cursor       plain text int — last settled order id
    oms.orders.json  {id: order}    — the persisted book, capped at OMS_STORE_MAX
    oms.meta.json    heavy-cycle cache + gap counters. `heavy_fetched_at` stamps the
                     ATTEMPT (so a failing endpoint cannot become a per-cycle retry
                     storm); `heavy_ok_at` stamps the last one that actually returned.

ENV
    OMS_CONFIG (default ~/.config/oms-pp-cli/oms-daman.toml) · OMS_BIN · OMS_SEED_ID (3089)
    OMS_MAX_NEW (40) · OMS_MISS_STOP (3) · OMS_GAP_SETTLE (3) · OMS_STORE_MAX (2000)
    OMS_RECENT_N (200) · OMS_HEAVY_MINUTES (30) · OMS_REFRESH_OPEN (0) · OMS_TIMEOUT (60)
    OMS_DEEP_MISS_STOP (25) · OMS_STALL_CYCLES (20) · OMS_PRICE_MIN_PER_L (3) ·
    OMS_PRICE_MAX_PER_L (1000) · OMS_EXPECT_COMPANY (1)

NOT APPLICABLE: live/README.md's "--company oil on every factory/OMS call" — oms-pp-cli
has no --company flag (checked `--help`); this account is scoped to category OIL /
company Jivo Wellness / branch FACTORY server-side.
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "oms"
IST = timezone(timedelta(hours=5, minutes=30))

_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[3]
STATE_DIR = _HERE.parents[1] / "state"

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

BIN = Path(_platform_cli(
    str(os.environ.get("OMS_BIN") or (REPO_ROOT / "oms-cli" / "oms-pp-cli"))))
CONFIG = Path(
    os.environ.get("OMS_CONFIG")
    or (Path.home() / ".config" / "oms-pp-cli" / "oms-daman.toml")
)

CURSOR_FILE = STATE_DIR / "oms.cursor"
ORDERS_FILE = STATE_DIR / "oms.orders.json"
META_FILE = STATE_DIR / "oms.meta.json"


def _envint(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


SEED_ID = _envint("OMS_SEED_ID", 3089)
MAX_NEW = _envint("OMS_MAX_NEW", 40)
MISS_STOP = _envint("OMS_MISS_STOP", 3)
# Deadlock guard: MISS_STOP consecutive DELETED ids would stop the walk short of every
# later order, permanently. After STALL_CYCLES quiet cycles, one cycle probes deeper to
# prove the book really has ended rather than assuming it.
DEEP_MISS_STOP = _envint("OMS_DEEP_MISS_STOP", 25)
STALL_CYCLES = _envint("OMS_STALL_CYCLES", 20)
GAP_SETTLE = _envint("OMS_GAP_SETTLE", 3)
STORE_MAX = _envint("OMS_STORE_MAX", 2000)
RECENT_N = _envint("OMS_RECENT_N", 200)
HEAVY_MINUTES = _envint("OMS_HEAVY_MINUTES", 30)
REFRESH_OPEN = _envint("OMS_REFRESH_OPEN", 0)
TIMEOUT = _envint("OMS_TIMEOUT", 60)
# Rate sanity band, INR per litre. Real oil runs Rs 32-360/L, and real packaged WATER
# runs Rs 5.6-12.7/L — the floor must sit under the water or every water line false-
# positives. The ceiling is what catches a genuine bad rate.
PRICE_MIN_PER_L = _envint("OMS_PRICE_MIN_PER_L", 3)
PRICE_MAX_PER_L = _envint("OMS_PRICE_MAX_PER_L", 1000)

# Keys whose value is a QUANTITY (so a numeric string is a number), for _coerce on the
# raw dashboard payloads. Deliberately excludes *_number / *_num / *_code / *_id, which
# are identifiers even when they look numeric.
_NUMERIC_KEY = re.compile(
    r"(^|_)(revenue|amount|total|qty|quantity|ltrs|litres|boxes|pcs|rate|price|count|"
    r"orders|value)(s)?$"
)
_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")

# Read-only by construction: _run refuses anything not on this list. `account profile`
# is deliberately absent — it returns the user's PBKDF2 password hash.
ALLOWED_COMMANDS = {
    ("orders", "detail"),
    ("orders", "dashboard"),
    ("dashboard", "summary"),
    ("orders", "status"),
    ("invoices", "logs"),
}

# ASSUMED, not read from the server: which statuses never change again.
TERMINAL_STATUSES = {"COMPLETED", "REJECTED", "BILLING_REJECTED", "CANCELLED", "CANCELED"}

NOTE = (
    "Order book walked by id via `orders detail` (no role filter); `orders list` shows this "
    "billing account only 3 of ~3,090 orders. qty is PIECES not cartons (C-0001) and ltrs is "
    "OMS's own figure. ONE order can dominate the litres: ORD-20260902-0031 to JIVO MART PVT "
    "LTD is 2,369,000 L / Rs 42.97 Cr on its own — an Oil-to-Mart intercompany transfer, not "
    "GT/MT market demand. Split by card_code before charting litres. "
    "The two dashboards are both user-scoped, never a company total, are asked different "
    "windows (see dashboards.agree), and have been seen disagreeing. Statuses "
    "number 12, not 11 (id 12 = Mart Approval). Order status is as-at last_seen_at, not now. "
    "ASSUMED, not read from OMS: which statuses are terminal — "
    + "/".join(sorted(TERMINAL_STATUSES))
    + ". OMS exposes no is_terminal field, so a wrong guess here moves orders between "
    "open_total and the closed book. Only COMPLETED, AUDITOR_APPROVAL, MART_APPROVAL and "
    "REJECTED have actually been seen. ALSO ASSUMED: the Rs "
    + f"{PRICE_MIN_PER_L}-{PRICE_MAX_PER_L}"
    + "/L band behind price_outliers is derived from observed lines, not a JIVO ruling. "
    "The book covers only ids the cursor has walked (from OMS_SEED_ID up), never orders 1..seed."
)

_CALLS: list = []


# ---------------------------------------------------------------- helpers


def _now():
    return datetime.now(IST)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse_ts(value):
    """Parse a server timestamp. Never slice one — OMS mixes UTC 'Z' with +05:30."""
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _coerce(obj):
    """Recursively coerce the known-numeric string fields of a RAW payload, in place.

    The per-field shaping below calls _num by hand, but the two dashboards are passed
    through raw and OMS states money as a string there: `total_revenue` came back
    "991300.00" on 2026-09-03. A site adding two of those concatenates them. Only keys
    that name a quantity are touched — `po_number`, `so_number` and `sap_doc_num` are
    IDENTIFIERS and must stay strings (coercing them would eat a leading zero).
    """
    if isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, str) and _NUMERIC_KEY.search(key) and _NUM_RE.match(val.strip()):
                obj[key] = _num(val)
            else:
                _coerce(val)
    elif isinstance(obj, list):
        for item in obj:
            _coerce(item)
    return obj


def _num(value):
    """Coerce a numeric string ('3000.000', '5.00') to int/float. Leave anything else."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return float(text)
        except ValueError:
            return value
    return value


def _run(args, timeout: int = TIMEOUT) -> dict:
    """The ONE way this module talks to OMS.

    Returns {ok, payload, meta, error, code}. Never raises. Never echoes stderr (the CLI
    prints warnings before the JSON). Slices stdout from the first '{' or '['.
    """
    cmd = " ".join(args)
    key = tuple(args[:2])
    if key not in ALLOWED_COMMANDS:
        return {"ok": False, "payload": None, "meta": None, "code": None, "source": None,
                "error": f"{cmd}: blocked, not on the read-only allowlist"}

    # --json --no-input --no-color --yes, NEVER --agent (it implies --compact, which strips
    # qty/ltrs/boxes). --data-source live --no-cache so `auto` can never serve the local
    # SQLite mirror. No --company: oms-pp-cli has no such flag, global or per-command
    # (checked `--help` on the binary and on every command used here) — this account is
    # scoped server-side, and _company_scope() below checks that from the payload instead.
    # The CLI's own --timeout is set BELOW the subprocess guard so the CLI loses the race
    # and returns a legible error rather than being killed mid-write.
    argv = [str(BIN)] + [str(a) for a in args] + [
        "--config", str(CONFIG),
        "--json", "--no-input", "--no-color", "--yes",
        "--data-source", "live", "--no-cache",
        "--timeout", f"{max(timeout - 5, 5)}s",
    ]
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        _CALLS.append({"cmd": cmd, "ok": False, "seconds": round(time.monotonic() - started, 2),
                       "code": None, "source": None})
        return {"ok": False, "payload": None, "meta": None, "code": None, "source": None,
                "error": f"{cmd}: timed out after {timeout}s"}
    except OSError as exc:
        _CALLS.append({"cmd": cmd, "ok": False, "seconds": round(time.monotonic() - started, 2),
                       "code": None, "source": None})
        return {"ok": False, "payload": None, "meta": None, "code": None, "source": None,
                "error": f"{cmd}: cannot run {BIN} ({exc})"}

    seconds = round(time.monotonic() - started, 2)
    out = proc.stdout.decode("utf-8", "replace")
    starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
    if not starts:
        _CALLS.append({"cmd": cmd, "ok": False, "seconds": seconds, "code": proc.returncode,
                       "source": None})
        return {"ok": False, "payload": None, "meta": None, "code": proc.returncode,
                "source": None, "error": f"{cmd}: exit {proc.returncode}, no JSON on stdout"}
    try:
        raw = json.loads(out[min(starts):])
    except json.JSONDecodeError as exc:
        _CALLS.append({"cmd": cmd, "ok": False, "seconds": seconds, "code": proc.returncode,
                       "source": None})
        return {"ok": False, "payload": None, "meta": None, "code": proc.returncode,
                "source": None, "error": f"{cmd}: exit {proc.returncode}, unparseable JSON ({exc})"}

    meta = None
    payload = raw
    if isinstance(raw, dict) and "results" in raw:
        meta = raw.get("meta")
        payload = raw.get("results")

    error = None
    source = meta.get("source") if isinstance(meta, dict) else None
    if proc.returncode != 0:
        error = f"{cmd}: exit {proc.returncode}"
    elif source not in (None, "live"):
        # --data-source live should make this impossible. If it ever isn't, say so loudly
        # AND THROW THE PAYLOAD AWAY: publishing the local SQLite mirror is the exact
        # failure this loop exists to eliminate (live/README.md). A dropped payload
        # surfaces as an error; a kept one surfaces as a plausible, stale number.
        error = f"{cmd}: served from '{source}', not live — payload discarded"
        payload = None

    _CALLS.append({"cmd": cmd, "ok": error is None, "seconds": seconds, "code": proc.returncode,
                   "source": source})
    return {"ok": error is None, "payload": payload, "meta": meta,
            "code": proc.returncode, "error": error, "source": source}


def _read_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def _read_cursor():
    try:
        return int(CURSOR_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _write_cursor(value: int) -> None:
    CURSOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CURSOR_FILE.with_suffix(".cursor.tmp")
    tmp.write_text(str(int(value)) + "\n", encoding="utf-8")
    os.replace(tmp, CURSOR_FILE)


# ---------------------------------------------------------------- shaping


def _order_record(raw: dict, seen_at: str) -> dict:
    lines = []
    for item in raw.get("items") or []:
        if not isinstance(item, dict):
            continue
        lines.append({
            "code": item.get("item_code"),
            "name": item.get("item_name"),
            "qty": _num(item.get("qty")),            # pcs
            "pcs": _num(item.get("pcs")),            # pcs per box
            "boxes": _num(item.get("boxes")),
            "ltrs": _num(item.get("ltrs")),          # L
            # Scheme give-away pieces. 0 on every line read so far, but it is a QUANTITY
            # the plant still has to fill — never drop it silently.
            "qty_scheme": _num(item.get("qty_scheme")),
            "rate": _num(item.get("basic_price")),   # INR per piece
            "total": _num(item.get("total")),        # INR
            "tax_rate": _num(item.get("tax_rate")),  # %
            "variety": item.get("variety"),
            "sub_group": item.get("sub_group"),
            "item_type": item.get("item_type"),
            "category": item.get("category"),
            "brand": item.get("brand"),
        })

    litres = 0.0
    for line in lines:
        value = line.get("ltrs")
        if isinstance(value, (int, float)):
            litres += float(value)

    status_code = (raw.get("status") or "").strip().upper() or "UNKNOWN"
    record = {
        "id": _num(raw.get("id")),
        "order_number": raw.get("order_number"),
        "customer": raw.get("card_name"),
        "card_code": raw.get("card_code"),
        # The company scoping the CLI cannot express as a flag. Kept as the RAW string
        # OMS sends ("1" = Jivo Wellness / Oil) and rolled up in data.company_scope, so a
        # foreign-company order is visible instead of assumed away.
        "company": raw.get("company"),
        "created": raw.get("created_at"),
        "updated": raw.get("updated_at"),
        "delivery_date": raw.get("delivery_date"),
        "status_code": status_code,
        "status_name": raw.get("status_display") or raw.get("status"),
        "is_terminal": status_code in TERMINAL_STATUSES,
        "dispatch_from_id": _num(raw.get("dispatch_from_id")),
        "dispatch_from_name": raw.get("dispatch_from_name"),
        "party_state": raw.get("party_state"),
        "created_by_name": raw.get("created_by_name"),
        "po_number": raw.get("po_number") or None,
        "warehouse_code": raw.get("warehouse_code") or None,
        "is_foc": raw.get("is_foc"),
        "sap_created": raw.get("sap_created"),
        "sap_doc_number": raw.get("sap_doc_number"),
        "total_amount": _num(raw.get("total_amount")),   # INR
        "litres": round(litres, 2),                      # L, ALL categories together
        "lines_count": len(lines),
        "lines": lines,
        "last_seen_at": seen_at,
    }
    record["litres_by_category"] = _litres_by_category(record)
    # Channel / main-group only if the header actually carries it (usually it does not).
    for key in ("main_group", "main_group_id", "main_group_name", "channel",
                "channel_id", "channel_name"):
        if raw.get(key) is not None:
            record[key] = raw[key]
    return record


def _fetch_order(order_id: int, seen_at: str):
    """-> (record|None, kind, error). kind is 'found' | 'missing' | 'error'."""
    result = _run(["orders", "detail", str(order_id)])
    payload = result.get("payload")
    if isinstance(payload, dict) and payload.get("id") is not None:
        return _order_record(payload, seen_at), "found", None
    if result.get("code") == 3:
        # CLI exit 3 with no body = "no such order". Verified live against id 999999.
        return None, "missing", None
    return None, "error", result.get("error") or f"orders detail {order_id}: no order in payload"


def _walk_forward(store: dict, gaps: dict, seen_at: str, errors: list,
                  miss_stop: int = MISS_STOP) -> dict:
    seeded = _read_cursor() is None
    cursor = _read_cursor()
    if cursor is None:
        cursor = SEED_ID
    start_cursor = cursor

    probed, found_ids, missing_ids, errored_ids = [], [], [], []
    new_orders = []
    # Anything already in the store is settled by definition — otherwise an id found on an
    # EARLIER cycle blocks the cursor for a whole extra cycle after a hole clears.
    settled = {int(k) for k in store if str(k).lstrip("-").isdigit()}
    consecutive_misses = 0
    stopped = "cap"
    next_id = cursor + 1

    while len(probed) < MAX_NEW:
        if consecutive_misses >= miss_stop:
            stopped = "consecutive_misses"
            break
        probed.append(next_id)
        record, kind, error = _fetch_order(next_id, seen_at)
        if kind == "found":
            consecutive_misses = 0
            found_ids.append(next_id)
            settled.add(next_id)
            gaps.pop(str(next_id), None)
            if str(next_id) not in store:
                new_orders.append(record)
            store[str(next_id)] = record
        elif kind == "missing":
            consecutive_misses += 1
            missing_ids.append(next_id)
        else:
            consecutive_misses += 1
            errored_ids.append(next_id)
            if error:
                errors.append(error)
            # An error is NEVER settled: a 5xx must not be read as a deleted order.
        next_id += 1
    else:
        stopped = "cap"

    # A missing id counts as a HOLE only when something ABOVE it exists. Ids past the top
    # of the book are simply not created yet: settling those would march the cursor into
    # the future and silently skip every order raised later today.
    known = [int(k) for k in store if str(k).lstrip("-").isdigit()]
    max_known = max(known) if known else start_cursor
    for missed in missing_ids:
        key = str(missed)
        if missed < max_known:
            gaps[key] = int(gaps.get(key, 0)) + 1
            if gaps[key] >= GAP_SETTLE:
                # Missed on GAP_SETTLE separate cycles, below a known-higher id — a real hole.
                settled.add(missed)
                gaps.pop(key, None)
        else:
            gaps.pop(key, None)

    # The cursor may only cross a contiguous run of settled ids.
    walker = start_cursor
    while (walker + 1) in settled:
        walker += 1
    cursor = walker
    if cursor != start_cursor:
        _write_cursor(cursor)
    elif seeded:
        _write_cursor(cursor)

    return {
        "value": cursor,
        "previous": start_cursor,
        "seeded": seeded,
        "probed_ids": probed,
        "found_ids": found_ids,
        "missing_ids": missing_ids,
        "errored_ids": errored_ids,
        "gaps_pending": {k: v for k, v in sorted(gaps.items(), key=lambda kv: int(kv[0]))},
        "stopped_because": stopped,
        "cap": MAX_NEW,
        "miss_stop": miss_stop,
    }, new_orders


def _refresh_open(store: dict, seen_at: str, errors: list) -> list:
    """Optional (OMS_REFRESH_OPEN=N): re-read the N stalest non-terminal orders."""
    if REFRESH_OPEN <= 0:
        return []
    stale = [r for r in store.values() if not r.get("is_terminal")]
    stale.sort(key=lambda r: (r.get("last_seen_at") or "", r.get("id") or 0))
    touched = []
    for record in stale[:REFRESH_OPEN]:
        order_id = record.get("id")
        if not isinstance(order_id, int):
            continue
        fresh, kind, error = _fetch_order(order_id, seen_at)
        if kind == "found":
            store[str(order_id)] = fresh
            touched.append(order_id)
        elif error:
            errors.append(error)
    return touched


def _litres_by_category(order: dict) -> dict:
    """Split an order's litres by OMS's OWN `category` on each line.

    The Oil order book is NOT all oil. Across the first 29 orders read live on 2026-09-03
    the lines carried three categories: OIL, BEVERAGES (packaged drinking water — JIVO
    NATURAL MINERAL / SANO WATER in 250/500/1000 ml PET) and MART. Summing `litres` as
    "oil demand" silently folds water and Mart volume into the plan.
    """
    split: dict = {}
    for line in order.get("lines") or []:
        value = line.get("ltrs")
        if not isinstance(value, (int, float)):
            continue
        key = line.get("category") or "UNKNOWN"
        split[key] = round(split.get(key, 0.0) + float(value), 2)
    return split


def _company_scope(store: dict) -> dict:
    """Prove company scoping from the payload, because the CLI has no --company flag.

    live/README.md demands `--company oil` on every factory/OMS call — the factory CLI
    takes it, oms-pp-cli does not (no such flag globally or on any command used here).
    The scoping is server-side on the Daman@oms.com account: category OIL, company Jivo
    Wellness (id 1), branch FACTORY. That is an assumption until something checks it, so
    this counts the `company` OMS puts on each order header. `clean` false means an order
    from another company entered the book and every litre total below is mixed.
    """
    counts: dict = {}
    unknown = 0
    for record in store.values():
        value = record.get("company")
        if value is None:
            # Read before this field was captured (or OMS omitted it). UNKNOWN IS NOT
            # FOREIGN — calling it foreign turned an un-upgraded store into a false alarm
            # on every panel. It ages out as the cursor re-reads the book.
            unknown += 1
            continue
        counts[str(value)] = counts.get(str(value), 0) + 1
    expected = os.environ.get("OMS_EXPECT_COMPANY", "1")
    foreign = {k: v for k, v in counts.items() if k != expected}
    return {
        "expected": expected,
        "by_company": counts,
        "clean": not foreign,
        "foreign_orders": sum(foreign.values()),
        "unknown_orders": unknown,
        "note": ("oms-pp-cli has NO --company flag — scoping is server-side on this "
                 "account (category OIL / company Jivo Wellness id 1 / branch FACTORY). "
                 "This counts the company OMS stamps on each order header instead. "
                 "`clean: false` means a FOREIGN company is in the book and the litre and "
                 "rupee totals here are mixed. `unknown_orders` is only 'we have not "
                 "re-read that order since this check existed' — not a scoping failure."),
    }


def _price_outliers(orders: list) -> list:
    """Bound-check every line's implied INR/L. Flags only — nothing is altered or dropped.

    Order 3118 (2026-09-03) carries FG0000030 MUSTARD KACHI GHANI 1 LTR at basic_price
    3223.81 = Rs 3,224/L, where the same SKU on order 3106 is Rs 160/L. OMS's own totals
    agree with the outlier, so it is a real field, not a parse error — but a Rs/L chart
    built on it is a lie. Surface it, never silently average it in.
    """
    flagged = []
    for order in orders:
        for line in order.get("lines") or []:
            litres = line.get("ltrs")
            total = line.get("total")
            if not isinstance(litres, (int, float)) or not isinstance(total, (int, float)):
                continue
            if litres <= 0 or total <= 0:
                continue
            per_litre = total / float(litres)
            if PRICE_MIN_PER_L <= per_litre <= PRICE_MAX_PER_L:
                continue
            flagged.append({
                "order_id": order.get("id"),
                "order_number": order.get("order_number"),
                "customer": order.get("customer"),
                "status_code": order.get("status_code"),
                "code": line.get("code"),
                "name": line.get("name"),
                "inr_per_litre": round(per_litre, 2),
                "ltrs": litres,
                "total_inr": total,
                "band_inr_per_litre": [PRICE_MIN_PER_L, PRICE_MAX_PER_L],
            })
    return sorted(flagged, key=lambda f: -(f["inr_per_litre"] or 0))


def _dashboards(orders_dash, summary_dash) -> dict:
    """Both dashboards, plus a LIVE check of whether they still disagree.

    On 2026-08-22 discovery they returned 3 orders / Rs 56,50,581 and 4 orders /
    Rs 60,35,957 minutes apart on the same account. On 2026-09-03 13:47 IST they agreed
    exactly (2 orders / Rs 9,91,300). So the disagreement is intermittent, not constant —
    which is worse, because a panel built on either one looks right most of the time.
    `agree` is recomputed every cycle rather than asserted, so the site can badge the
    moment they diverge instead of trusting a note written weeks ago.
    """
    # Raw passthrough — so coerce it, or "991300.00" (a STRING, seen live 2026-09-03)
    # reaches the site and two revenues concatenate instead of adding.
    orders_dash = _coerce(orders_dash)
    summary_dash = _coerce(summary_dash)

    def _pair(payload):
        if not isinstance(payload, dict):
            return None, None
        return _num(payload.get("total_orders")), _num(payload.get("total_revenue"))

    a_orders, a_revenue = _pair(orders_dash)
    b_orders, b_revenue = _pair(summary_dash)
    checked = a_orders is not None and b_orders is not None
    # None == None is True, which reported "the two dashboards agree" on a cycle where
    # BOTH of them failed or were discarded as non-live. A false green is worse than a
    # red: null means "not compared", never "compared and equal".
    agree = {
        "checked": checked,
        "total_orders_match": (a_orders == b_orders) if checked else None,
        "total_revenue_match": (a_revenue == b_revenue)
        if (a_revenue is not None and b_revenue is not None) else None,
        "orders_dashboard": {"total_orders": a_orders, "total_revenue": a_revenue},
        "dashboard_summary": {"total_orders": b_orders, "total_revenue": b_revenue},
        # The two are NOT asked the same question: `dashboard summary` self-reports its
        # window (live 2026-09-03: {"year": 2026, "month": 0} = all of 2026) and `orders
        # dashboard` states none at all. Comparing them without the window is what makes
        # the disagreement look random. Never chart them on one axis.
        "dashboard_summary_window": (summary_dash or {}).get("filter")
        if isinstance(summary_dash, dict) else None,
        "orders_dashboard_window": None,
    }
    return {
        "orders_dashboard": orders_dash,
        "dashboard_summary": summary_dash,
        "agree": agree,
        "note": ("TWO endpoints, and they have been seen disagreeing on the same account "
                 "minutes apart (2026-08-22: 3 orders / Rs 56,50,581 vs 4 orders / "
                 "Rs 60,35,957); on 2026-09-03 they agreed. `agree` is checked live every "
                 "cycle — trust that, not this sentence. BOTH are scoped to the billing user "
                 "(an admin token saw 2,468 orders), so NEITHER is a company total. Show one, "
                 "label which, never add them."),
    }


def _by_status(store: dict) -> tuple:
    buckets: dict = {}
    for record in store.values():
        code = record.get("status_code") or "UNKNOWN"
        bucket = buckets.setdefault(code, {
            "status_name": record.get("status_name") or code,
            "count": 0, "litres": 0.0, "litres_by_category": {}, "amount_inr": 0.0,
            "terminal": code in TERMINAL_STATUSES,
            "oldest_seen_at": record.get("last_seen_at"),
        })
        bucket["count"] += 1
        litres = record.get("litres")
        if isinstance(litres, (int, float)):
            bucket["litres"] += float(litres)
        split = record.get("litres_by_category") or _litres_by_category(record)
        for category, value in split.items():
            bucket["litres_by_category"][category] = round(
                bucket["litres_by_category"].get(category, 0.0) + value, 2)
        amount = record.get("total_amount")
        if isinstance(amount, (int, float)):
            bucket["amount_inr"] += float(amount)
        seen = record.get("last_seen_at")
        if seen and (bucket["oldest_seen_at"] is None or seen < bucket["oldest_seen_at"]):
            bucket["oldest_seen_at"] = seen

    open_total = {"count": 0, "litres": 0.0, "litres_by_category": {}, "amount_inr": 0.0}
    for code, bucket in buckets.items():
        bucket["litres"] = round(bucket["litres"], 2)
        bucket["amount_inr"] = round(bucket["amount_inr"], 2)
        if not bucket["terminal"]:
            open_total["count"] += bucket["count"]
            open_total["litres"] += bucket["litres"]
            open_total["amount_inr"] += bucket["amount_inr"]
            for category, value in bucket["litres_by_category"].items():
                open_total["litres_by_category"][category] = round(
                    open_total["litres_by_category"].get(category, 0.0) + value, 2)
    open_total["litres"] = round(open_total["litres"], 2)
    open_total["amount_inr"] = round(open_total["amount_inr"], 2)
    return buckets, open_total


def _inr(value: float) -> str:
    """Indian grouping for the plain-language note (12,34,567 — not 1,234,567)."""
    try:
        whole = int(round(float(value)))
    except (TypeError, ValueError):
        return str(value)
    sign, digits = ("-" if whole < 0 else ""), str(abs(whole))
    if len(digits) <= 3:
        return sign + digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ",".join(parts + [tail])


def _rate_per_l(amount, litres):
    """INR/L, or None when there are no litres — never a ZeroDivisionError, never 0.0."""
    if not isinstance(amount, (int, float)) or not isinstance(litres, (int, float)):
        return None
    if litres <= 0:
        return None
    return round(float(amount) / float(litres), 2)


def _headline_ex_outliers(open_total: dict, outliers: list) -> dict:
    """Add an ex-outlier headline BESIDE the raw one. Nothing is dropped or corrected.

    `amount_inr` IS what OMS holds and it stays exactly as it is. But on 2026-09-03 the
    open book read Rs 74,55,619 over 16,710 L — Rs 446/L — and Rs 48,35,715 of that was
    three orders (3117/3118/3119) pricing FG0000030 MUSTARD KACHI GHANI 1 LTR at
    Rs 3,223.81/L, where order 3106 prices the same SKU at Rs 160/L. Ex those lines the
    same book runs Rs 172/L. Both figures are published; the site picks, out loud.

    Only flags on NON-TERMINAL orders are deducted, because open_total only ever counted
    non-terminal buckets — deducting a REJECTED order's line (3120, same SKU, same rate)
    would push the headline BELOW the truth. The deduction is line-level and comes from
    the SAME published price_outliers list, so a consumer can reconcile it by hand.
    """
    raw_amount = open_total.get("amount_inr") or 0.0
    raw_litres = open_total.get("litres") or 0.0

    cut_amount, cut_litres, cut_lines = 0.0, 0.0, 0
    cut_orders, skipped_terminal = [], 0
    for flag in outliers or []:
        if (flag.get("status_code") or "UNKNOWN") in TERMINAL_STATUSES:
            skipped_terminal += 1
            continue
        total, litres = flag.get("total_inr"), flag.get("ltrs")
        if isinstance(total, (int, float)):
            cut_amount += float(total)
        if isinstance(litres, (int, float)):
            cut_litres += float(litres)
        cut_lines += 1
        if flag.get("order_id") not in cut_orders:
            cut_orders.append(flag.get("order_id"))

    open_total["amount_inr_ex_outliers"] = round(raw_amount - cut_amount, 2)
    open_total["litres_ex_outliers"] = round(raw_litres - cut_litres, 2)
    open_total["rs_per_l"] = _rate_per_l(raw_amount, raw_litres)
    open_total["rs_per_l_ex_outliers"] = _rate_per_l(
        open_total["amount_inr_ex_outliers"], open_total["litres_ex_outliers"])

    if cut_lines:
        note = (
            f"amount_inr / litres are RAW — Rs {_inr(raw_amount)} over "
            f"{_inr(raw_litres)} L, exactly what OMS holds, nothing corrected. "
            f"amount_inr_ex_outliers takes out {cut_lines} line"
            f"{'' if cut_lines == 1 else 's'} on {len(cut_orders)} open order"
            f"{'' if len(cut_orders) == 1 else 's'} "
            f"({', '.join(str(o) for o in cut_orders)}) — Rs {_inr(cut_amount)} over "
            f"{_inr(cut_litres)} L — because their implied price falls outside the "
            f"Rs {PRICE_MIN_PER_L}-{PRICE_MAX_PER_L}/L sanity band and would otherwise "
            f"set the headline rate on its own. Every one of those lines is still listed "
            f"in price_outliers, with the order number, the SKU and the rate. "
            f"Rs/L: {open_total['rs_per_l']} raw vs "
            f"{open_total['rs_per_l_ex_outliers']} ex-outliers."
        )
        if skipped_terminal:
            note += (
                f" {skipped_terminal} further flagged line"
                f"{'' if skipped_terminal == 1 else 's'} "
                f"{'sits' if skipped_terminal == 1 else 'sit'} on a TERMINAL order and "
                f"{'was' if skipped_terminal == 1 else 'were'} NOT deducted — "
                f"open_total never counted "
                f"{'it' if skipped_terminal == 1 else 'them'}."
            )
    else:
        note = (
            f"No line in the open book prices outside the Rs {PRICE_MIN_PER_L}-"
            f"{PRICE_MAX_PER_L}/L sanity band, so the ex-outlier figures are identical to "
            f"the raw ones. amount_inr / litres are RAW either way."
        )
        if skipped_terminal:
            note += (
                f" {skipped_terminal} flagged line"
                f"{'' if skipped_terminal == 1 else 's'} "
                f"{'sits' if skipped_terminal == 1 else 'sit'} on a TERMINAL order, "
                f"outside open_total already."
            )
    open_total["headline_note"] = note
    return open_total


def _shape_invoice_logs(rows: list) -> tuple:
    """-> (so_to_invoice_map, invoice_logs summary). Drops invoice_payload (heavy)."""
    mapping = []
    by_status: dict = {}
    by_warehouse: dict = {}
    stamps = []
    fg_latest: dict = {}

    for row in rows:
        if not isinstance(row, dict):
            continue
        created_at = row.get("created_at")
        parsed = _parse_ts(created_at)
        if parsed:
            stamps.append(parsed)
        status = row.get("status")
        if status:
            by_status[status] = by_status.get(status, 0) + 1
        warehouse = row.get("warehouse")
        if warehouse:
            by_warehouse[warehouse] = by_warehouse.get(warehouse, 0) + 1

        # so_number arrives as "1726086864, 1726086755" — one entry per SO.
        raw_so = row.get("so_number")
        so_numbers = []
        if isinstance(raw_so, str):
            so_numbers = [s.strip() for s in raw_so.split(",") if s.strip()]
        elif raw_so is not None:
            so_numbers = [str(raw_so)]
        for so_number in so_numbers or [None]:
            mapping.append({
                "so_number": so_number,
                "sap_doc_num": _num(row.get("sap_doc_num")),
                "sap_doc_entry": _num(row.get("sap_doc_entry")),
                "party_name": row.get("party_name"),
                "total_amount": _num(row.get("total_amount")),   # INR
                "warehouse": warehouse,
                "branch": row.get("branch"),
                "status": status,
                "created_at": created_at,
                "log_id": _num(row.get("id")),
                "error_message": row.get("error_message"),
            })

        for stock in row.get("fg_stock") or []:
            if not isinstance(stock, dict):
                continue
            key = f"{stock.get('item_code')}@{stock.get('warehouse_code')}"
            prior = fg_latest.get(key)
            # "Newest wins" must compare INSTANTS, not strings. OMS mixes 'Z' and '+05:30'
            # for the same moment, and "2026-08-31T...Z" < "2026-08-31T...+05:30"
            # lexicographically regardless of which actually came first.
            if prior and parsed and prior.get("_at") and prior["_at"] >= parsed:
                continue
            if prior and not parsed:
                continue
            fg_latest[key] = {
                "item_code": stock.get("item_code"),
                "item_name": stock.get("item_name"),
                "warehouse_code": stock.get("warehouse_code"),
                "quantity": _num(stock.get("quantity")),           # pcs on that invoice
                "warehouse_stock": _num(stock.get("warehouse_stock")),  # pcs at submission
                "at": _iso(parsed.astimezone(IST)) if parsed else created_at,
                "_at": parsed,
            }

    # so_number is NOT unique: a SO rejected then re-approved appears once per log row
    # (seen live — SO 1726096508 as PENDING, then EDITED, then APPROVED). The server's own
    # row order is not chronological, so every naive reduction was silently picking an
    # arbitrary event: {so: row} in Python keeps the LAST, Array.find in JS keeps the
    # FIRST, and no sort order is safe for both. So say it in the data instead of relying
    # on order — filter on is_latest_for_so and the choice is deterministic either way.
    mapping.sort(key=lambda e: _parse_ts(e.get("created_at")) or datetime.min.replace(
        tzinfo=timezone.utc), reverse=True)
    seen_so: set = set()
    for entry in mapping:                       # newest first, so the first one wins
        key = entry.get("so_number")
        entry["is_latest_for_so"] = key not in seen_so
        seen_so.add(key)

    latest = []
    for entry in sorted(fg_latest.values(), key=lambda s: str(s.get("item_code"))):
        entry.pop("_at", None)
        latest.append(entry)

    summary = {
        "rows": len(rows),
        "by_status": by_status,
        "by_warehouse": by_warehouse,
        # IST, like every other stamp in this contract. The server sends UTC 'Z' here;
        # emitting it unconverted put these two 5h30m in the past.
        "first_created_at": _iso(min(stamps).astimezone(IST)) if stamps else None,
        "last_created_at": _iso(max(stamps).astimezone(IST)) if stamps else None,
        "fg_stock_latest": latest,
        "note": ("fg_stock_latest is what the warehouse held WHEN THAT INVOICE WAS "
                 "SUBMITTED, not a live stock figure — the newest reading per "
                 "(item_code, warehouse_code), and the newest may be days old. This is the "
                 "invoice REVIEW queue, low-volume and gappy, not every invoice. "
                 "so_to_invoice_map can carry the same so_number several times when a SO "
                 "moved through the queue (PENDING -> EDITED -> APPROVED, seen live). "
                 "Keyed as a dict, all but one disappear and WHICH one survives depends on "
                 "your language: filter is_latest_for_so instead of reducing on order."),
    }
    return mapping, summary


# ---------------------------------------------------------------- fetch


def fetch() -> dict:
    del _CALLS[:]
    now = _now()
    seen_at = _iso(now)
    errors: list = []

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    store = _read_json(ORDERS_FILE, {})
    if not isinstance(store, dict):
        store, errors = {}, errors + ["oms.orders.json unreadable — starting a fresh store"]
    meta = _read_json(META_FILE, {})
    if not isinstance(meta, dict):
        meta = {}
    gaps = meta.get("gaps") if isinstance(meta.get("gaps"), dict) else {}

    def _degraded(error: str) -> dict:
        """No live call is possible — serve the persisted book, badged, never a blank panel.

        The keys a consumer indexes must still be there: dropping to {note, calls} made
        every OMS panel KeyError instead of showing the last-known book with a stale
        badge. `stale` says the numbers are not from this cycle.
        """
        by_status, totals = _by_status(store)
        recent = sorted(store.values(), key=lambda r: (r.get("id") or 0),
                        reverse=True)[:RECENT_N]
        outliers = _price_outliers(recent)
        _headline_ex_outliers(totals, outliers)
        return {
            "source": SOURCE, "fetched_at": seen_at, "server_at": None, "ok": False,
            "error": error,
            "data": {
                "stale": True,
                "cursor": {"value": _read_cursor(), "probed_ids": [], "found_ids": [],
                           "missing_ids": [], "errored_ids": [], "gaps_pending": {},
                           "stopped_because": "no_live_call"},
                "orders_new_this_cycle": [], "orders_recent": recent,
                "open_by_status": by_status, "open_total": totals,
                "company_scope": _company_scope(store),
                "dashboards": _dashboards(None, None),
                "price_outliers": outliers,
                "statuses": meta.get("statuses"),
                "statuses_fetched_at": meta.get("statuses_fetched_at"),
                "heavy_refresh": False, "heavy_fetched_at": meta.get("heavy_fetched_at"),
                "heavy_ok_at": meta.get("heavy_ok_at"),
                "counts": {"orders_stored": len(store), "orders_new": 0,
                           "probes_this_cycle": 0, "orders_refreshed": 0},
                "calls": [], "cli_path": str(BIN), "note": NOTE,
            },
        }

    if not BIN.exists():
        return _degraded(f"oms-pp-cli not found at {BIN} — serving the persisted book, STALE")
    if not CONFIG.exists():
        return _degraded(
            f"OMS config {CONFIG} missing — run `oms-pp-cli auth login --config {CONFIG}` "
            f"as Daman@oms.com (never overwrite the default config). Serving the persisted "
            f"book, STALE")

    # 1) walk the order book forward from the cursor
    idle = int(meta.get("idle_cycles") or 0)
    deep = idle >= STALL_CYCLES
    cursor_info, new_orders = _walk_forward(
        store, gaps, seen_at, errors, DEEP_MISS_STOP if deep else MISS_STOP)
    cursor_info["deep_probe"] = deep
    cursor_info["idle_cycles"] = idle
    if cursor_info["found_ids"] or deep:
        # Found something, or just spent the deep probe — either way the counter restarts.
        meta["idle_cycles"] = 0
    else:
        meta["idle_cycles"] = idle + 1

    # 2) optional re-read of stale open orders (off by default)
    refreshed = _refresh_open(store, seen_at, errors)

    # 3) both dashboards, every cycle — they disagree, so record both
    dash_orders = _run(["orders", "dashboard"])
    dash_summary = _run(["dashboard", "summary"])
    for result in (dash_orders, dash_summary):
        if result.get("error"):
            errors.append(result["error"])

    # 4) the 30-minute heavy work
    last_heavy = _parse_ts(meta.get("heavy_fetched_at"))
    heavy_due = last_heavy is None or (now - last_heavy) >= timedelta(minutes=HEAVY_MINUTES)
    so_map = None
    invoice_summary = None
    if heavy_due:
        statuses_result = _run(["orders", "status"])
        if statuses_result.get("ok") and isinstance(statuses_result.get("payload"), list):
            meta["statuses"] = [
                {"id": _num(s.get("id")), "name": s.get("name") or s.get("status_name")}
                for s in statuses_result["payload"] if isinstance(s, dict)
            ]
            meta["statuses_fetched_at"] = seen_at
        elif statuses_result.get("error"):
            errors.append(statuses_result["error"])

        invoices_result = _run(["invoices", "logs"])
        if invoices_result.get("ok") and isinstance(invoices_result.get("payload"), list):
            so_map, invoice_summary = _shape_invoice_logs(invoices_result["payload"])
            meta["heavy_ok_at"] = seen_at
        elif invoices_result.get("error"):
            errors.append(invoices_result["error"])
        # Stamp the ATTEMPT, not just the success. Stamping only on success turned a
        # permanently-failing `invoices logs` into 2 extra calls EVERY 3-minute cycle
        # instead of every 30 minutes — a retry storm against a server already in trouble.
        # `heavy_ok_at` above is the one that says the data is real.
        meta["heavy_fetched_at"] = seen_at

    # 5) trim + persist
    if len(store) > STORE_MAX:
        keep = sorted(store.keys(), key=lambda k: int(k))[-STORE_MAX:]
        store = {k: store[k] for k in keep}
    meta["gaps"] = cursor_info["gaps_pending"]
    _write_json(ORDERS_FILE, store)
    _write_json(META_FILE, meta)

    # 6) shape the answer
    open_by_status, open_total = _by_status(store)
    recent = sorted(store.values(), key=lambda r: (r.get("id") or 0), reverse=True)[:RECENT_N]
    # The RAW headline stays; the ex-outlier one is added beside it. See
    # _headline_ex_outliers — three orders at Rs 3,224/L were setting the whole rate.
    price_outliers = _price_outliers(recent)
    _headline_ex_outliers(open_total, price_outliers)

    # The newest SERVER-SIDE event stamp anything read this cycle carried, in IST. Never
    # our own clock — OMS's dashboards carry no stamp of their own, and dating them from
    # our wall clock would be a lie. The invoice-log queue DOES stamp its rows, so a heavy
    # cycle with no new order still has a real server stamp to report instead of null.
    server_stamps = []
    for record in new_orders:
        for key in ("updated", "created"):
            parsed = _parse_ts(record.get(key))
            if parsed:
                server_stamps.append(parsed)
    if invoice_summary and invoice_summary.get("last_created_at"):
        parsed = _parse_ts(invoice_summary["last_created_at"])
        if parsed:
            server_stamps.append(parsed)
    server_at = _iso(max(server_stamps).astimezone(IST)) if server_stamps else None

    data = {
        "stale": False,
        "cursor": cursor_info,
        "orders_new_this_cycle": new_orders,
        "orders_recent": recent,
        "open_by_status": open_by_status,
        "open_total": open_total,
        "company_scope": _company_scope(store),
        "dashboards": _dashboards(dash_orders.get("payload"), dash_summary.get("payload")),
        "price_outliers": price_outliers,
        "statuses": meta.get("statuses"),
        "statuses_fetched_at": meta.get("statuses_fetched_at"),
        "heavy_refresh": bool(heavy_due),
        "heavy_fetched_at": meta.get("heavy_fetched_at"),   # last ATTEMPT
        "heavy_ok_at": meta.get("heavy_ok_at"),             # last one that actually returned
        "counts": {
            "orders_stored": len(store),
            "orders_new": len(new_orders),
            "probes_this_cycle": len(cursor_info["probed_ids"]),
            "orders_refreshed": len(refreshed),
        },
        "calls": list(_CALLS),
        # Which binary actually answered: the Mac and Linux builds sit side by
        # side in oms-cli/, and the wrong one is an Exec format error.
        "cli_path": str(BIN),
        "note": NOTE,
    }
    if so_map is not None:
        data["so_to_invoice_map"] = so_map
    if invoice_summary is not None:
        data["invoice_logs"] = invoice_summary

    return {
        "source": SOURCE,
        "fetched_at": seen_at,
        "server_at": server_at,
        "ok": not errors,
        "error": "; ".join(errors) if errors else None,
        "data": data,
    }


if __name__ == "__main__":
    print(json.dumps(fetch(), ensure_ascii=False, indent=2))
