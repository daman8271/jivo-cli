"""'history' command — the months-long price/stock log for a platform.

    jivo-scrape history --platform amazon
    jivo-scrape history --platform all --sku canola --from 2026-06-01
    jivo-scrape history --platform blinkit --to 2026-06-30 --limit 100 --json

Reads ``data/<platform>/history.csv`` (append log; column names vary per
platform and are discovered defensively — see sources/histcsv.py). Human output
is an aligned table of (date, platform, sku, price, mrp, avail), capped at
``--limit`` with a note when truncated. A platform with no history.csv degrades
to a note, not a crash.
"""

import datetime as _dt
import sys

from jivo_scrape import util
from jivo_scrape.sources import histcsv


def register(sub):
    p = sub.add_parser(
        "history",
        help="months-long price/stock history from data/<platform>/history.csv",
    )
    p.add_argument(
        "--platform",
        default="all",
        help="one platform or 'all' (default: all)",
    )
    p.add_argument(
        "--sku",
        help="case-insensitive substring filter on the SKU/product column",
    )
    p.add_argument(
        "--from",
        dest="date_from",
        help="earliest date YYYY-MM-DD (inclusive)",
    )
    p.add_argument(
        "--to",
        dest="date_to",
        help="latest date YYYY-MM-DD (inclusive)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=50,
        help="max rows shown in the human table (default: 50)",
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _select(platform_arg):
    """('all' | platform, error_or_None)."""
    if not platform_arg or str(platform_arg).strip().lower() == "all":
        return "all", None
    p = str(platform_arg).strip().lower()
    if p in util.PLATFORMS:
        return p, None
    return None, "unknown platform %r; choose one of: all, %s" % (
        platform_arg,
        ", ".join(util.PLATFORMS),
    )


def _flag_date(spec):
    """Parse a --from/--to value to a date; ValueError bubbles to dispatcher exit 2."""
    if not spec:
        return None
    return _dt.date.fromisoformat(str(spec).strip())


def run(args):
    platform, err = _select(args.platform)
    if err:
        print("jivo-scrape history: %s" % err, file=sys.stderr)
        return 2

    date_from = _flag_date(args.date_from)
    date_to = _flag_date(args.date_to)

    rows, freshness, notes = histcsv.read_history(
        platform, sku=args.sku, date_from=date_from, date_to=date_to
    )
    # oldest first, then platform, then sku — stable, readable ordering.
    rows.sort(key=lambda r: (r.get("date") or "", r.get("platform") or "", r.get("sku") or ""))

    row_count = len(rows)
    limit = args.limit
    shown = rows[:limit] if isinstance(limit, int) and limit >= 0 else rows
    truncated = len(shown) < row_count

    meta_notes = list(notes["messages"])
    if truncated:
        meta_notes.append(
            "showing %d of %d row(s) (--limit %d)" % (len(shown), row_count, limit)
        )

    meta = {
        "command": "history",
        "platform": platform,
        "sku": args.sku,
        "from": date_from.isoformat() if date_from else None,
        "to": date_to.isoformat() if date_to else None,
        "row_count": row_count,
        "shown": len(shown),
        "limit": limit,
        "skipped_rows": notes["skipped_rows"],
        "undated_rows": notes["undated_rows"],
        "missing_platforms": notes["missing_platforms"],
        "unreadable_platforms": notes["unreadable_platforms"],
        "freshness": freshness,
        "notes": meta_notes,
    }

    def human(results):
        parts = ["history", "platform=%s" % platform]
        if args.sku:
            parts.append("sku~%r" % args.sku)
        if date_from or date_to:
            parts.append(
                "%s..%s"
                % (
                    date_from.isoformat() if date_from else "",
                    date_to.isoformat() if date_to else "",
                )
            )
        print(" · ".join(parts))
        if not results:
            print("  no history rows matched.")
        else:
            trows = [
                [
                    r.get("date") or "-",
                    r.get("platform") or "-",
                    r.get("sku") or "-",
                    r.get("price") or "-",
                    r.get("mrp") or "-",
                    r.get("avail") or "-",
                ]
                for r in results
            ]
            print(_table(["DATE", "PLATFORM", "SKU", "PRICE", "MRP", "AVAIL"], trows))
            print("  %d of %d row(s)." % (len(results), row_count))
        for n in meta_notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, shown, meta, human)
    return 0


# --- tiny local table renderer (self-contained, mirrors today.py) ---
def _table(headers, rows):
    heads = [str(h) for h in headers]
    srows = [["" if c is None else str(c) for c in r] for r in rows]
    widths = [len(h) for h in heads]
    for r in srows:
        for i, c in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(c))

    def fmt(cells):
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells))

    lines = ["  " + fmt(heads), "  " + "  ".join("-" * w for w in widths)]
    lines += ["  " + fmt(r) for r in srows]
    return "\n".join(lines)
