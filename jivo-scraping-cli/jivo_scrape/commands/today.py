"""'today' command — the landing report.

For the resolved date, per platform: did the daily sweep land, how many rows,
was it served from last-good (partial), and what did QC say — plus the
today/_manifest.json highlights.

    jivo-desk today
    jivo-desk today --date yesterday
    jivo-desk today --platform blinkit --json

``--date today``    reads the live result.json files + today/_manifest.json.
``--date yesterday`` reads the dated daily QC reviews + today.prev/_manifest.json.
``--date YYYY-MM-DD`` reads the dated daily QC reviews (no manifest retained).
"""

import sys

from jivo_scrape import util
from jivo_scrape.sources import today as today_src


def register(sub):
    p = sub.add_parser(
        "today", help="landing report: did each sweep land, row counts, QC verdict"
    )
    p.add_argument("--platform", help="limit to one platform (default: all)")
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _select(platform_arg):
    if not platform_arg:
        return list(util.PLATFORMS), None
    p = str(platform_arg).strip().lower()
    if p in util.PLATFORMS:
        return [p], None
    return [], "unknown platform %r; choose one of: %s" % (
        platform_arg,
        ", ".join(util.PLATFORMS),
    )


def run(args):
    iso, label = util.resolve_date(args.date)
    platforms, err = _select(args.platform)
    if err:
        print("jivo-desk today: %s" % err, file=sys.stderr)
        return 2

    statuses = today_src.gather(platforms, iso, label)
    counts = today_src.summary_counts(statuses)
    highlights, man_path, man_fresh = today_src.load_manifest(label)

    # meta.freshness: the manifest + each platform's authoritative source mtime.
    freshness = {"manifest": man_fresh}
    for s in statuses:
        freshness[s["platform"]] = (
            s["result_freshness"] if label == "today" else s["review_freshness"]
        )

    notes = []
    if label == "today" and counts["not_landed"]:
        notes.append(
            "no sweep dated %s yet for: %s (daily sweeps land ~10:00 IST; showing newest on disk)"
            % (iso, ", ".join(counts["not_landed"]))
        )
    if label != "today":
        notes.append(
            "past-date view: row counts + verdicts come from the dated QC review "
            "(reviews/<platform>-daily-%s.json), not live sweep files" % iso
        )
    if man_path is None:
        notes.append("no snapshot manifest retained for '%s'" % label)

    meta = {
        "command": "today",
        "date": label,
        "date_iso": iso,
        "platform": args.platform or "all",
        "counts": counts,
        "manifest": highlights,
        "manifest_path": man_path,
        "freshness": freshness,
        "partial_fallback": bool(counts["partial_fallback_platforms"]),
        "partial_fallback_platforms": counts["partial_fallback_platforms"],
        "notes": notes,
    }
    results = {"platforms": statuses, "manifest": highlights}

    def human(res):
        print("today · %s (%s)" % (label, iso))
        if highlights:
            print(
                "  manifest: date=%s · generated=%s · mode=%s · files=%s"
                % (
                    highlights.get("date"),
                    highlights.get("generated_at"),
                    highlights.get("mode"),
                    highlights.get("total_files"),
                )
            )
        trows = []
        for s in res["platforms"]:
            landed = "yes" if s["landed"] else "no"
            rows = "-" if s["rows"] is None else "{:,}".format(s["rows"])
            flags = []
            if s["partial_fallback"]:
                flags.append("last-good")
            elif s["partial"]:
                flags.append("partial")
            if s["unreadable"]:
                flags.append("unreadable")
            trows.append(
                [
                    s["platform"],
                    landed,
                    rows,
                    s["review_verdict"] or ("-" if s["review_present"] else "no-QC"),
                    " ".join(flags) or (s.get("note") or ""),
                ]
            )
        print(_table(["PLATFORM", "LANDED", "ROWS", "QC", "FLAGS/NOTE"], trows))
        print(
            "  %d/%d landed · %s total rows"
            % (
                counts["landed_count"],
                counts["platforms_total"],
                "{:,}".format(counts["total_rows"]),
            )
        )
        for n in notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, results, meta, human)
    return 0


# --- tiny local table renderer (kept self-contained, no cross-agent import) ---
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
