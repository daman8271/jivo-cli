"""'asof' command -- price/availability rows as of any past date, via git.

The ecom-intel checkout commits every sweep, overwriting
``platforms/<p>/result.json`` each time. So the rows a platform showed on any
past day are still recoverable: find the newest commit at or before that day,
read that commit's ``result.json`` blob, and parse it exactly the way a live
sweep is parsed.

    jivo-scrape asof --platform flipkart
    jivo-scrape asof --platform blinkit --date 2026-07-12
    jivo-scrape asof --platform amazon --sku JID-0016 --date 2026-07-10 --json

If ``result.json`` was not tracked at that commit, we fall back to
``result.last-good.json``, and failing that to the newest DATED sweep snapshot
tracked at that commit -- ``platforms/<p>/**/<p>-YYYY-MM-DD.result.json`` -- and
say which we served. Many checkouts gitignore the canonical ``result.json``
(runtime data), so the recoverable rows live only at these dated-drop paths. If
none of those is present (or there is no commit that early), we degrade to an
empty result with a note -- never a crash. When the root is not a git checkout,
gittime raises and the dispatcher exits 3.
"""

import json
import os
import re
import sys

from jivo_scrape import util
from jivo_scrape.sources import gittime, sweeps

# A dated sweep drop is named ``<something>-YYYY-MM-DD.result.json`` (the
# ``.result.json`` suffix distinguishes it from pincode/bad/salvage exports).
_ISO_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def register(sub):
    p = sub.add_parser(
        "asof", help="rows a platform showed as of a past date (recovered via git)"
    )
    p.add_argument("--platform", required=True, help="platform to time-travel")
    p.add_argument(
        "--sku", help="case-insensitive substring filter over id / jid / product"
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _extract_rows(data):
    """Rows + shape label from a parsed result.json (allRows canonical; perPin fallback)."""
    if not isinstance(data, dict):
        return [], None
    rows = data.get("allRows")
    if isinstance(rows, list):
        return rows, "allRows"
    per = data.get("perPin")
    if isinstance(per, list):
        flat = []
        for pin in per:
            if isinstance(pin, dict) and isinstance(pin.get("rows"), list):
                flat.extend(pin["rows"])
        return flat, "perPin"
    return [], None


def _pick_snapshot(root, sha, platform, iso):
    """Path of the newest dated sweep snapshot for `platform` tracked at `sha`.

    Discovers ``platforms/<platform>/**/*.result.json`` files whose basename
    carries an ISO date (the dated-drop convention), keeps those dated at or
    before ``iso`` (string compare is chronological for ISO dates), and returns
    the newest one's path (tie-break by path, descending). Returns None when no
    such snapshot is tracked at that commit. Read-only tree listing only.
    """
    prefix = "platforms/%s/" % platform
    candidates = []
    for path in gittime.list_tree(root, sha, prefix):
        base = path.rsplit("/", 1)[-1].lower()
        if not base.endswith(".result.json"):
            continue
        m = _ISO_DATE_RE.search(base)
        if not m:
            continue
        d = m.group(1)
        if d <= iso:
            candidates.append((d, path))
    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return candidates[0][1]


def _sku_match(row, needle):
    hay = " ".join(
        str(row.get(k) or "")
        for k in ("listing_id", "listing_key", "jid", "product")
    ).lower()
    return needle in hay


def run(args):
    iso, label = util.resolve_date(args.date)

    platform = str(args.platform).strip().lower()
    if platform not in util.PLATFORMS:
        print(
            "jivo-scrape asof: unknown platform %r; choose one of: %s"
            % (args.platform, ", ".join(util.PLATFORMS)),
            file=sys.stderr,
        )
        return 2

    root = util.ECOM
    # commit_at / show_file raise FileNotFoundError if root is not a git
    # checkout -> dispatcher prints "source missing" and exits 3 (clean).
    sha, committed, subject = gittime.commit_at(root, iso)

    notes = []
    source_path = None
    fell_back = False
    from_snapshot = False
    shape = None
    rows = []

    if sha is None:
        notes.append(
            "no commit at or before %s in this checkout -- nothing to recover" % iso
        )
    else:
        rel_live = "platforms/%s/result.json" % platform
        rel_good = "platforms/%s/result.last-good.json" % platform
        blob = gittime.show_file(root, sha, rel_live)
        source_path = rel_live
        if blob is None:
            blob = gittime.show_file(root, sha, rel_good)
            if blob is not None:
                source_path = rel_good
                fell_back = True
                notes.append(
                    "result.json absent at %s; served result.last-good.json"
                    % sha[:12]
                )
        if blob is None:
            # Canonical result.json / last-good are commonly gitignored (runtime
            # data), so they were never committed. Recover from the newest dated
            # sweep snapshot tracked at this commit instead.
            snap = _pick_snapshot(root, sha, platform, iso)
            if snap is not None:
                blob = gittime.show_file(root, sha, snap)
                if blob is not None:
                    source_path = snap
                    from_snapshot = True
                    notes.append(
                        "result.json not tracked at %s; recovered dated snapshot %s"
                        % (sha[:12], snap)
                    )
        if blob is None:
            source_path = None
            notes.append(
                "neither result.json, result.last-good.json, nor a dated snapshot "
                "tracked for '%s' at or before %s" % (platform, iso)
            )
            # Point at what the archive DOES keep for that date: the tracked
            # per-platform view, and row-grade data in data/<p>/history.csv.
            view = "today/platforms/%s.md" % platform
            if gittime.show_file(root, sha, view) is not None:
                notes.append(
                    "tracked view exists at this commit: %s (git -C <root> "
                    "show %s:%s)" % (view, sha[:12], view)
                )
            notes.append(
                "row-grade rows for that date: jivo-scrape history --platform "
                "%s --from %s --to %s" % (platform, iso, iso)
            )
        else:
            try:
                data = json.loads(blob.decode("utf-8", "replace"))
            except ValueError:
                data = None
                notes.append(
                    "recovered blob at %s is not valid JSON" % sha[:12]
                )
            raw_rows, shape = _extract_rows(data)
            if shape == "perPin":
                notes.append("legacy result.json shape: flattened perPin rows")
            for raw in raw_rows:
                rows.append(sweeps.normalize(raw, platform))

    if args.sku:
        needle = str(args.sku).strip().lower()
        rows = [r for r in rows if _sku_match(r, needle)]

    # cheapest first (nulls last), then product -- same ordering as `price`.
    rows.sort(
        key=lambda r: (
            r["price"] is None,
            r["price"] if r["price"] is not None else 0,
            r["product"] or "",
        )
    )

    head_path = os.path.join(root, ".git", "HEAD")
    meta = {
        "command": "asof",
        "date": label,
        "date_iso": iso,
        "platform": platform,
        "sku": args.sku,
        "commit": sha,
        "committed": committed,
        "subject": subject,
        "row_count": len(rows),
        "source_path": source_path,
        "fallback_last_good": fell_back,
        "recovered_from_snapshot": from_snapshot,
        "freshness": {
            "commit_committed": committed,
            "git_head": util.freshness(head_path),
        },
        "notes": notes,
    }

    def human(results):
        print(
            "asof · %s (%s) · platform=%s%s"
            % (
                label,
                iso,
                platform,
                "" if not args.sku else " · sku~%r" % args.sku,
            )
        )
        if sha:
            print(
                "  commit: %s · %s · %s"
                % (sha[:12], committed or "?", subject or "")
            )
        else:
            print("  commit: (none at or before this date)")
        if not results:
            print("  no rows recovered.")
        else:
            trows = [
                [
                    r["platform"],
                    r["listing_id"] or "-",
                    r.get("jid") or "-",
                    (r["product"] or "-")[:52],
                    sweeps.fmt_price(r["price"]),
                    sweeps.fmt_price(r["mrp"]),
                    r["pincode"] or "national",
                    sweeps.fmt_stock(r["in_stock"]),
                ]
                for r in results
            ]
            print(
                sweeps.table(
                    [
                        "PLATFORM",
                        "LISTING ID",
                        "JID",
                        "PRODUCT",
                        "PRICE",
                        "MRP",
                        "PINCODE",
                        "STOCK",
                    ],
                    trows,
                )
            )
            print("  %d row(s)." % len(results))
        for n in notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, rows, meta, human)
    return 0
