"""'files' command — the day's paper trail.

Lists every artifact produced on the resolved date across the deliverable +
QC + pricematch directories, matched either by a date embedded in the filename
or by the file's mtime day, with sizes. Human output is grouped by directory.

    jivo-desk files
    jivo-desk files --date 2026-07-18
    jivo-desk files --date yesterday --json

READ-ONLY: only stat()/scandir over the data directories; nothing is written.
"""

import datetime as _dt
import os
import sys

from jivo_scrape import util

# (label, absolute directory) — the places the daily pipeline drops artifacts.
DIRS = [
    ("deliverables (output/)", util.OUTPUT_DIR),
    ("qc reviews (reviews/)", util.REVIEWS_DIR),
    ("health logs (logs/doctor/)", util.DOCTOR_DIR),
    (
        "pricematch build (tools/pricematch/)",
        os.path.join(util.ECOM, "tools", "pricematch"),
    ),
    ("pricematch data (data/pricematch/)", util.PRICEMATCH_DIR),
]


def register(sub):
    p = sub.add_parser(
        "files",
        help="list artifacts produced on the resolved date, grouped by directory",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=40,
        help="max rows shown per directory in human output (default: 40; --json is unlimited)",
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _dates_in_name(name):
    """Every YYYY-MM-DD token embedded in a filename (manual scan, no regex)."""
    out = []
    n = len(name)
    for i in range(n - 9):
        chunk = name[i : i + 10]
        if (
            chunk[4] == "-"
            and chunk[7] == "-"
            and chunk[0:4].isdigit()
            and chunk[5:7].isdigit()
            and chunk[8:10].isdigit()
        ):
            out.append(chunk)
    return out


def _human_size(n):
    if n is None:
        return "-"
    f = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if f < 1024 or unit == "GB":
            return (
                ("%d %s" % (int(f), unit)) if unit == "B" else ("%.1f %s" % (f, unit))
            )
        f /= 1024.0
    return "%d B" % n


def _scan_dir(dirpath, iso):
    """Return (matches, present). matches = list of file dicts produced on iso."""
    if not os.path.isdir(dirpath):
        return [], False
    matches = []
    try:
        entries = list(os.scandir(dirpath))
    except OSError:
        return [], True
    for e in entries:
        try:
            is_file = e.is_file()
        except OSError:
            continue
        if not is_file:
            continue
        try:
            st = e.stat()
        except OSError:
            continue
        mtime = _dt.datetime.fromtimestamp(st.st_mtime)
        mtime_day = mtime.date().isoformat()
        name_dates = _dates_in_name(e.name)
        by_name = iso in name_dates
        by_mtime = mtime_day == iso
        if not (by_name or by_mtime):
            continue
        basis = "filename" if by_name else "mtime"
        matches.append(
            {
                "name": e.name,
                "path": e.path,
                "bytes": st.st_size,
                "size": _human_size(st.st_size),
                "mtime": mtime.isoformat(timespec="seconds"),
                "mtime_day": mtime_day,
                "match": basis,
                "name_dates": name_dates,
            }
        )
    matches.sort(key=lambda m: (m["mtime"], m["name"]), reverse=True)
    return matches, True


def run(args):
    iso, label = util.resolve_date(args.date)

    groups = []
    freshness = {}
    total_files = 0
    total_bytes = 0
    for glabel, dpath in DIRS:
        matches, present = _scan_dir(dpath, iso)
        groups.append(
            {"label": glabel, "dir": dpath, "present": present, "files": matches}
        )
        freshness[glabel] = util.freshness(dpath)  # directory mtime
        total_files += len(matches)
        total_bytes += sum(m["bytes"] for m in matches)

    meta = {
        "command": "files",
        "date": label,
        "date_iso": iso,
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_size": _human_size(total_bytes),
        "match_rule": "date embedded in filename OR mtime falls on the resolved day",
        "freshness": freshness,
        "notes": [],
    }
    missing_dirs = [g["dir"] for g in groups if not g["present"]]
    if missing_dirs:
        meta["notes"].append("directory absent: " + ", ".join(missing_dirs))

    results = {"groups": groups}

    def human(res):
        print("files · %s (%s) — artifacts produced this day" % (label, iso))
        for g in res["groups"]:
            fs = g["files"]
            if not g["present"]:
                print("\n  %s — (directory absent)" % g["label"])
                continue
            gbytes = sum(m["bytes"] for m in fs)
            print(
                "\n  %s — %d file(s), %s" % (g["label"], len(fs), _human_size(gbytes))
            )
            shown = fs[: args.limit]
            for m in shown:
                tag = "" if m["match"] == "filename" else "  (mtime)"
                print("    %-10s  %s%s" % (m["size"], m["name"], tag))
            if len(fs) > len(shown):
                print(
                    "    … %d more (use --json for the full list)"
                    % (len(fs) - len(shown))
                )
        print("\n  total: %d file(s), %s" % (total_files, _human_size(total_bytes)))
        for n in meta["notes"]:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, results, meta, human)
    return 0
