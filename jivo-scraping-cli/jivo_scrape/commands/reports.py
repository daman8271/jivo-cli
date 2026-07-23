"""'reports' command — the deep-dive report runs + coverage docs.

    jivo-scrape reports
    jivo-scrape reports --name blinkit
    jivo-scrape reports --show reports/blinkit-device-parity-.../REPORT.md
    jivo-scrape reports --json

Merges two families into one newest-first listing:
  <root>/reports/*/REPORT.md   — one row per run dir (dirname, mtime of its
                                 REPORT.md, whether a SHA256SUMS sits beside it);
  <root>/docs/coverage-runs/*  — one row per coverage doc/file.
``--show RELPATH`` cats a REPORT.md or a coverage file raw, through the same
traversal-guarded reader (relpath is taken from the <root>). Absent families are
noted, not fatal. READ-ONLY.
"""

import os
import sys

from jivo_scrape import util
from jivo_scrape.sources import vaultview


def register(sub):
    p = sub.add_parser(
        "reports",
        help="report runs (reports/*/REPORT.md) + coverage docs (docs/coverage-runs/)",
    )
    p.add_argument(
        "--name", help="case-insensitive substring filter over the relpath"
    )
    p.add_argument(
        "--show",
        metavar="RELPATH",
        help="print a REPORT.md or coverage doc raw (path relative to <root>)",
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _iso_mtime(path):
    fr = util.freshness(path)
    return fr["mtime"] if fr else None


def _list_runs(reports_dir, pat):
    """One entry per <reports_dir>/*/REPORT.md run directory (sorted later)."""
    if not os.path.isdir(reports_dir):
        return [], False
    runs = []
    try:
        entries = list(os.scandir(reports_dir))
    except OSError:
        return [], True
    for e in entries:
        try:
            if not e.is_dir():
                continue
        except OSError:
            continue
        report_md = os.path.join(e.path, "REPORT.md")
        if not os.path.isfile(report_md):
            continue  # a run dir only counts once it has a REPORT.md
        rel = os.path.join("reports", e.name, "REPORT.md")
        if pat and pat not in rel.lower():
            continue
        runs.append(
            {
                "dirname": e.name,
                "relpath": rel,
                "mtime": _iso_mtime(report_md),
                "sha256sums": os.path.isfile(os.path.join(e.path, "SHA256SUMS")),
            }
        )
    return runs, True


def _list_coverage(coverage_dir, pat):
    """One entry per file under <root>/docs/coverage-runs/."""
    if not os.path.isdir(coverage_dir):
        return [], False
    covs = []
    try:
        entries = list(os.scandir(coverage_dir))
    except OSError:
        return [], True
    for e in entries:
        try:
            if not e.is_file():
                continue
        except OSError:
            continue
        rel = os.path.join("docs", "coverage-runs", e.name)
        if pat and pat not in rel.lower():
            continue
        covs.append({"name": e.name, "relpath": rel, "mtime": _iso_mtime(e.path)})
    return covs, True


def _newest_first(items):
    items.sort(key=lambda d: d["relpath"])
    items.sort(key=lambda d: (d["mtime"] or ""), reverse=True)
    return items


def run(args):
    reports_dir = os.path.join(util.ECOM, "reports")
    coverage_dir = os.path.join(util.ECOM, "docs", "coverage-runs")

    # --show: raw passthrough through the traversal-guarded reader, based at the
    # <root>. ValueError('path escapes root') -> exit 2; missing -> exit 3.
    if args.show:
        text = vaultview.read_note(util.ECOM, args.show)
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    pat = args.name.lower() if args.name else None
    runs, reports_present = _list_runs(reports_dir, pat)
    covs, coverage_present = _list_coverage(coverage_dir, pat)
    _newest_first(runs)
    _newest_first(covs)

    notes = []
    if not reports_present:
        notes.append("reports/ absent under %s" % util.ECOM)
    if not coverage_present:
        notes.append("docs/coverage-runs/ absent under %s" % util.ECOM)

    meta = {
        "command": "reports",
        "count": len(runs) + len(covs),
        "roots_present": {"reports": reports_present, "coverage": coverage_present},
        "freshness": {
            "reports/": util.freshness(reports_dir),
            "docs/coverage-runs/": util.freshness(coverage_dir),
        },
        "notes": notes,
    }
    results = {"runs": runs, "coverage": covs}

    def human(res):
        print("reports · %s" % ("all" if not args.name else "name~%r" % args.name))
        merged = [("run", r) for r in res["runs"]] + [
            ("coverage", c) for c in res["coverage"]
        ]
        merged.sort(key=lambda kv: kv[1]["relpath"])
        merged.sort(key=lambda kv: (kv[1]["mtime"] or ""), reverse=True)
        if not reports_present and not coverage_present:
            print("  neither reports/ nor docs/coverage-runs/ found under %s" % util.ECOM)
        elif not merged:
            print("  no reports matched.")
        else:
            trows = [
                [
                    kind,
                    d["mtime"] or "-",
                    ("yes" if d.get("sha256sums") else "no") if kind == "run" else "-",
                    d["relpath"],
                ]
                for kind, d in merged
            ]
            print(vaultview.table(["KIND", "MODIFIED", "SHA256SUMS", "RELPATH"], trows))
            print(
                "  %d item(s): %d run(s) + %d coverage doc(s)."
                % (len(merged), len(res["runs"]), len(res["coverage"]))
            )
        for n in notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, results, meta, human)
    return 0
