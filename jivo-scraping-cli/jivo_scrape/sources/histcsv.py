"""Read-only reader for the long-run price/stock history CSVs.

Each platform keeps a months-long append log at ``data/<platform>/history.csv``.
The column *names* are not uniform across platforms (a header may spell the date
``date_ist`` on one platform and ``obs_ts`` on another; the identifier may be
``canonical_sku`` or ``product_code``; price may be ``price`` or ``sale_price``).
Nothing here assumes a fixed schema — the relevant columns are discovered by
substring against whatever header the file actually carries, and any row that
does not fit the header (wrong column count) is skipped and counted rather than
allowed to raise.

READ-ONLY: this module only ever opens data files for reading. No writes, no
network, stdlib only.

Contract:
    read_history(platform, sku=None, date_from=None, date_to=None)
        -> (rows, freshness, notes)

    rows      : list of {platform, date, sku, price, mrp, avail} dicts.
    freshness : {platform: util.freshness(path) or None} for every csv consulted
                (None marks a platform whose history.csv is absent/unread).
    notes     : {messages, skipped_rows, undated_rows, missing_platforms,
                 unreadable_platforms, row_count} — messages are human note
                strings; the counters let a caller build meta without re-parsing.

``platform`` may be a single platform name or ``"all"`` (loops util.PLATFORMS,
tags each row with its platform, and notes any platform missing a csv).
"""

import csv
import datetime as _dt
import os

from jivo_scrape import util

# Substring candidates (priority order) for the columns whose header names vary
# per platform. Discovery is substring-outer: an earlier substring wins across
# all headers before a later one is tried (so a real "date" column is preferred
# over a stray "...ts..." match).
DATE_SUBSTRINGS = ("date", "day", "ts")
SKU_SUBSTRINGS = ("sku", "product")
PRICE_SUBSTRINGS = ("price", "sale")
MRP_SUBSTRINGS = ("mrp",)
AVAIL_SUBSTRINGS = ("avail", "stock", "oos")


def history_path(platform):
    """Path to a platform's history csv (never opened for writing)."""
    return os.path.join(util.ECOM, "data", platform, "history.csv")


def _find_col(fieldnames, substrings):
    """First header matching any substring (earlier substring wins globally)."""
    lowered = [(n, n.lower()) for n in (fieldnames or []) if n]
    for sub in substrings:
        for name, low in lowered:
            if sub in low:
                return name
    return None


def _is_malformed(raw):
    """True when a DictReader row does not fit the header (column-count mismatch).

    csv.DictReader parks surplus fields (long row) under the None key and fills
    missing fields (short row) with None. Either is a structural defect, so we
    skip and count it rather than emit a half-populated row.
    """
    if not raw:
        return True
    extra = raw.get(None)
    if extra:  # long row: leftover values collected under the None restkey
        return True
    for v in raw.values():
        if v is None:  # short row: a header column had no value
            return True
    return False


def _clean(v):
    """Strip a cell to a non-empty string, else None."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _parse_iso_date(cell):
    """date from the cell's first 10 chars when they look ISO (YYYY-MM-DD), else None."""
    if cell is None:
        return None
    s = str(cell).strip()
    if len(s) < 10:
        return None
    head = s[:10]
    if head[4] != "-" or head[7] != "-":
        return None
    try:
        return _dt.date.fromisoformat(head)
    except ValueError:
        return None


def _as_date(x):
    """Coerce None / date / datetime / ISO-ish string to a date (may raise on garbage)."""
    if x is None:
        return None
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    s = str(x).strip()
    if not s:
        return None
    return _dt.date.fromisoformat(s[:10])  # ValueError bubbles -> dispatcher exit 2


def _read_one(path, platform, sku_filter, date_from, date_to):
    """Parse one platform's csv.

    Returns (rows_or_None, skipped, undated, sku_col_missing). rows is None only
    when the file could not be opened or its header could not be parsed (caller
    records it as unreadable). A per-record csv.Error mid-iteration is skipped
    and counted, never raised.
    """
    rows = []
    skipped = 0
    undated = 0
    sku_missing = False
    filtering = bool(date_from or date_to)
    needle = sku_filter.lower() if sku_filter else None
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames or []
            date_col = _find_col(fields, DATE_SUBSTRINGS)
            sku_col = _find_col(fields, SKU_SUBSTRINGS)
            price_col = _find_col(fields, PRICE_SUBSTRINGS)
            mrp_col = _find_col(fields, MRP_SUBSTRINGS)
            avail_col = _find_col(fields, AVAIL_SUBSTRINGS)
            # Iterate record-by-record so a single malformed record (an
            # unterminated quote, or a field exceeding csv's field-size limit)
            # is skipped-and-counted rather than allowed to raise csv.Error and
            # crash the whole command. csv.Error is NOT an OSError, so the outer
            # handler below would miss a mid-iteration raise; catch it here and
            # resume with the next record. The underlying file iterator only ever
            # advances, so this loop always terminates.
            row_iter = iter(reader)
            while True:
                try:
                    raw = next(row_iter)
                except StopIteration:
                    break
                except csv.Error:
                    skipped += 1
                    continue
                if _is_malformed(raw):
                    skipped += 1
                    continue

                sku_val = _clean(raw.get(sku_col)) if sku_col else None
                if needle is not None:
                    if sku_col is None:
                        sku_missing = True
                    else:
                        hay = sku_val.lower() if sku_val else ""
                        if needle not in hay:
                            continue

                date_cell = raw.get(date_col) if date_col else None
                parsed = _parse_iso_date(date_cell)
                if filtering:
                    if parsed is None:
                        undated += 1  # can't range-check it; keep and count
                    else:
                        if date_from and parsed < date_from:
                            continue
                        if date_to and parsed > date_to:
                            continue

                rows.append(
                    {
                        "platform": platform,
                        "date": parsed.isoformat() if parsed else _clean(date_cell),
                        "sku": sku_val,
                        "price": _clean(raw.get(price_col)) if price_col else None,
                        "mrp": _clean(raw.get(mrp_col)) if mrp_col else None,
                        "avail": _clean(raw.get(avail_col)) if avail_col else None,
                    }
                )
    except (OSError, csv.Error):
        # OSError: file vanished/unreadable. csv.Error here (outside the per-row
        # guard) can only come from parsing the header line itself -- treat the
        # whole file as unreadable rather than crash.
        return None, 0, 0, False
    return rows, skipped, undated, sku_missing


def read_history(platform, sku=None, date_from=None, date_to=None):
    """Read + filter the history log for one platform or all platforms."""
    date_from = _as_date(date_from)
    date_to = _as_date(date_to)

    platforms = list(util.PLATFORMS) if platform == "all" else [platform]

    all_rows = []
    freshness = {}
    messages = []
    missing = []
    unreadable = []
    sku_missing_cols = []
    skipped_total = 0
    undated_total = 0

    for p in platforms:
        path = history_path(p)
        fresh = util.freshness(path)
        freshness[p] = fresh
        if fresh is None:
            missing.append(p)
            continue
        rows, skipped, undated, sku_missing = _read_one(
            path, p, sku, date_from, date_to
        )
        if rows is None:
            unreadable.append(p)
            continue
        all_rows.extend(rows)
        skipped_total += skipped
        undated_total += undated
        if sku_missing:
            sku_missing_cols.append(p)

    if missing:
        messages.append("no history.csv for: %s" % ", ".join(missing))
    if unreadable:
        messages.append("history.csv unreadable for: %s" % ", ".join(unreadable))
    if skipped_total:
        messages.append(
            "skipped %d malformed row(s) (column-count mismatch)" % skipped_total
        )
    if undated_total:
        messages.append(
            "%d row(s) had unparseable dates; kept (not range-filtered)"
            % undated_total
        )
    if sku_missing_cols:
        messages.append(
            "no sku/product column to filter on for: %s (rows kept unfiltered)"
            % ", ".join(sku_missing_cols)
        )

    notes = {
        "messages": messages,
        "skipped_rows": skipped_total,
        "undated_rows": undated_total,
        "missing_platforms": missing,
        "unreadable_platforms": unreadable,
        "row_count": len(all_rows),
    }
    return all_rows, freshness, notes
