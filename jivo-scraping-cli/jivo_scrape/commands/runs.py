"""'runs' command -- the sweep ledger from git commit history.

Every sweep in the ecom-intel checkout is a git commit (``run: <platform>
<date-time>``), so the commit log IS the run ledger. Without ``--date`` we show
the last N commits overall; with a past ``--date`` we show that single day's
runs. When ``today/runs`` exists we also surface each platform's newest run
snapshot with its freshness.

    jivo-scrape runs                 # last N sweep commits overall
    jivo-scrape runs --limit 40
    jivo-scrape runs --date 2026-07-15   # that day's runs
    jivo-scrape runs --json

If the root is not a git checkout we note that the sweep history is unavailable
and still list the ``today/runs`` snapshots -- graceful degradation, not a crash.
"""

import os
import sys

from jivo_scrape import util
from jivo_scrape.sources import gittime


def register(sub):
    p = sub.add_parser(
        "runs", help="sweep ledger: recent run commits + today/runs snapshots"
    )
    p.add_argument(
        "--limit", type=int, default=20, help="max run commits to show (default: 20)"
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _scan_runs_dir():
    """Summarize today/runs: per-platform newest snapshot + count + freshness.

    Returns {'present': bool, 'path': str, 'platforms': [ {...}, ... ]} where
    each platform entry carries its newest .md run file and that file's
    freshness. Read-only; degrades to present=False when the dir is absent.
    """
    runs_root = os.path.join(util.TODAY_DIR, "runs")
    summary = {"present": os.path.isdir(runs_root), "path": runs_root, "platforms": []}
    if not summary["present"]:
        return summary
    try:
        entries = sorted(os.listdir(runs_root))
    except OSError:
        summary["present"] = False
        return summary
    for name in entries:
        pdir = os.path.join(runs_root, name)
        if not os.path.isdir(pdir):
            continue
        try:
            files = [f for f in os.listdir(pdir) if f.endswith(".md")]
        except OSError:
            continue
        if not files:
            continue
        fresh = [(f, util.freshness(os.path.join(pdir, f))) for f in files]
        fresh = [(f, fr) for (f, fr) in fresh if fr is not None]
        if not fresh:
            continue
        # newest == smallest age_minutes.
        latest_name, latest_fresh = min(
            fresh, key=lambda t: t[1]["age_minutes"]
        )
        summary["platforms"].append(
            {
                "platform": name,
                "latest": latest_name,
                "count": len(files),
                "freshness": latest_fresh,
            }
        )
    return summary


def _fmt_time(commit):
    """'YYYY-MM-DD HH:MM' from a commit's datetime iso, best-effort."""
    dt = commit.get("datetime") or ""
    if len(dt) >= 16 and dt[10] in ("T", " "):
        return dt[:16].replace("T", " ")
    return commit.get("date") or dt or "?"


def run(args):
    iso, label = util.resolve_date(args.date)
    root = util.ECOM
    limit = args.limit if args.limit and args.limit > 0 else None

    notes = []
    is_repo = gittime.is_git_root(root)
    # A specific single day is requested whenever --date names anything other
    # than the bare default or the literal "today" keyword. Key off the RAW spec,
    # not the collapsed label: util.resolve_date() folds an explicit YYYY-MM-DD
    # that equals the current date back to label "today", so relying on the label
    # would silently widen `runs --date <today's date>` into the recent-N view
    # and leak prior days' commits. `--date yesterday` and any explicit date
    # (including today's) are single-day; only "" / "today" mean "recent".
    spec = str(args.date).strip().lower() if args.date is not None else ""
    day_mode = spec not in ("", "today")

    commits = []
    if not is_repo:
        notes.append(
            "root is not a git checkout (%s); sweep history unavailable" % root
        )
    elif day_mode:
        raw = gittime.sweep_log(root, since=iso, until=iso, limit=2000)
        # timezone-independent exact-day slice on the parsed date field.
        commits = [c for c in raw if c.get("date") == iso]
        if limit:
            commits = commits[:limit]
        if not commits:
            notes.append("no run commits dated %s" % iso)
    else:
        commits = gittime.sweep_log(root, limit=limit)
        notes.append(
            "showing the last %d commit(s) overall (no specific --date)" % len(commits)
        )

    runs_dir = _scan_runs_dir()
    if not runs_dir["present"]:
        notes.append("today/runs snapshots not present under %s" % util.TODAY_DIR)

    head_fresh = None
    if commits:
        head_fresh = commits[0].get("datetime")

    meta = {
        "command": "runs",
        "date": label,
        "date_iso": iso,
        "mode": "day" if day_mode else "recent",
        "limit": args.limit,
        "commit_count": len(commits),
        "git_repo": is_repo,
        "runs_dir": runs_dir,
        "freshness": {
            "head_commit": head_fresh,
            "runs_dir": runs_dir["path"] if runs_dir["present"] else None,
        },
        "notes": notes,
    }
    results = {"commits": commits, "runs_dir": runs_dir}

    def human(res):
        scope = "day %s" % iso if day_mode else "recent"
        print("runs · %s (%s) · %s" % (label, iso, scope))
        cs = res["commits"]
        if not cs:
            print("  no run commits.")
        else:
            trows = [[_fmt_time(c), c["subject"]] for c in cs]
            print(_table(["TIME", "SUBJECT"], trows))
            print("  %d run commit(s)." % len(cs))
        rd = res["runs_dir"]
        if rd["present"] and rd["platforms"]:
            print("  today/runs snapshots:")
            srows = [
                [
                    p["platform"],
                    p["latest"],
                    "%d file(s)" % p["count"],
                    "%.0fm old" % p["freshness"]["age_minutes"],
                ]
                for p in rd["platforms"]
            ]
            print(_table(["PLATFORM", "LATEST", "COUNT", "AGE"], srows))
        for n in notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, results, meta, human)
    return 0


# --- tiny local table renderer (self-contained, matches the house style) ---
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
