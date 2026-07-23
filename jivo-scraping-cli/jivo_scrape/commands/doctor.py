"""'doctor' command — source health check for the whole godown.

Walks every source in SOURCES.md and reports, for each: present? readable?
fresh (age vs a ~daily expectation)? partial? Rolls the individual checks into
an overall verdict.

Known gotcha (SOURCES.md): a doctor RED that is *only* swiggy-instamart (and its
residential-only sibling instamart, which never runs from this VPS) is a NOTE,
not an alarm — those two are demoted so they never flip the exit code.

    jivo-desk doctor
    jivo-desk doctor --json

Exit code: 0 = healthy, 1 = one or more real warnings.
READ-ONLY: only stat()/open-for-read; nothing is written anywhere.
"""

import glob
import os
import sys

from jivo_scrape import util

STALE_H = 36.0  # daily sources older than this are STALE (a day + margin)
# Residential-only / chronically-flaky platforms: their staleness is expected
# from this VPS and must never raise the alarm on its own (SOURCES.md gotcha).
KNOWN_FLAKY = {"swiggy-instamart", "instamart"}


def register(sub):
    p = sub.add_parser(
        "doctor",
        help="source health check (present/readable/fresh/partial); exit 1 on warnings",
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def _age_h(fresh):
    if not fresh or fresh.get("age_minutes") is None:
        return None
    return round(fresh["age_minutes"] / 60.0, 1)


def _newest(dirpath, pattern):
    """Newest file matching a glob inside dirpath, or None."""
    if not os.path.isdir(dirpath):
        return None
    hits = glob.glob(os.path.join(dirpath, pattern))
    if not hits:
        return None
    return max(hits, key=lambda p: os.path.getmtime(p))


def _check(source, path, expect_daily=True, known_flaky=False, info_only=False):
    """One source's health record."""
    rec = {
        "source": source,
        "path": path,
        "present": False,
        "readable": None,
        "age_hours": None,
        "status": None,
        "detail": "",
        "known_flaky": known_flaky,
    }
    if path is None or not os.path.exists(path):
        rec["present"] = False
        rec["status"] = "MISSING"
        rec["detail"] = "not found"
        return rec
    rec["present"] = True
    fresh = util.freshness(path)
    rec["age_hours"] = _age_h(fresh)

    # readability: a directory is readable if we can list it; a file if we can open it.
    try:
        if os.path.isdir(path):
            os.listdir(path)
        else:
            with open(path, "rb") as fh:
                fh.read(1)
        rec["readable"] = True
    except OSError:
        rec["readable"] = False
        rec["status"] = "UNREADABLE"
        rec["detail"] = "present but could not be read"
        return rec

    if info_only:
        rec["status"] = "INFO"
        rec["detail"] = "age %s" % (
            ("%.1fh" % rec["age_hours"]) if rec["age_hours"] is not None else "n/a"
        )
        return rec

    if expect_daily and rec["age_hours"] is not None and rec["age_hours"] > STALE_H:
        rec["status"] = "STALE"
        rec["detail"] = "%.1fh old (> %.0fh daily threshold)" % (
            rec["age_hours"],
            STALE_H,
        )
    else:
        rec["status"] = "OK"
        rec["detail"] = "age %s" % (
            ("%.1fh" % rec["age_hours"]) if rec["age_hours"] is not None else "n/a"
        )
    return rec


def _platform_check(platform):
    """result.json health for one platform, including the partial flag."""
    known = platform in KNOWN_FLAKY
    path = os.path.join(util.PLATFORMS_DIR, platform, "result.json")
    rec = _check("sweep:%s" % platform, path, expect_daily=True, known_flaky=known)
    if rec["status"] in ("OK", "STALE") and rec["readable"]:
        # inspect partial flag + row count without assuming keys exist
        try:
            data = util.load_json(path)
        except (ValueError, OSError):
            rec["status"] = "UNREADABLE"
            rec["detail"] = "present but JSON did not parse"
            return rec
        if isinstance(data, dict):
            summary = (
                data.get("summary") if isinstance(data.get("summary"), dict) else {}
            )
            rows = summary.get("total_rows")
            if not isinstance(rows, int) or isinstance(rows, bool):
                ar = data.get("allRows")
                rows = len(ar) if isinstance(ar, list) else None
            rec["rows"] = rows
            if data.get("partial"):
                lastgood = os.path.join(
                    util.PLATFORMS_DIR, platform, "result.last-good.json"
                )
                served = (
                    "last-good available"
                    if os.path.exists(lastgood)
                    else "NO last-good"
                )
                # PARTIAL is only an escalation over OK; a stale+partial stays STALE-worse.
                if rec["status"] == "OK":
                    rec["status"] = "PARTIAL"
                rec["detail"] = "live sweep partial (%s); %s" % (served, rec["detail"])
            if rows == 0 and rec["status"] == "OK":
                rec["status"] = "EMPTY"
                rec["detail"] = "0 rows; " + rec["detail"]
    return rec


# statuses that count as a real warning (before the known-flaky demotion)
WARN_STATUSES = {"MISSING", "UNREADABLE", "STALE", "PARTIAL", "EMPTY"}


def run(args):
    _iso, label = util.resolve_date(args.date)
    checks = []

    # 1. platform sweeps
    for p in util.PLATFORMS:
        checks.append(_platform_check(p))
    # bigbasket pincode serviceability
    checks.append(
        _check(
            "sweep:bigbasket/result_pincode",
            os.path.join(util.PLATFORMS_DIR, "bigbasket", "result_pincode.json"),
        )
    )

    # 2. today / yesterday snapshot manifests
    checks.append(
        _check(
            "snapshot:today/_manifest", os.path.join(util.TODAY_DIR, "_manifest.json")
        )
    )
    checks.append(
        _check(
            "snapshot:today.prev/_manifest",
            os.path.join(util.YDAY_DIR, "_manifest.json"),
            info_only=True,
        )
    )

    # 3. pricematch
    checks.append(
        _check("pricematch:daily.csv", os.path.join(util.PRICEMATCH_DIR, "daily.csv"))
    )
    checks.append(
        _check(
            "pricematch:history.csv", os.path.join(util.PRICEMATCH_DIR, "history.csv")
        )
    )
    pm_summary = _newest(
        os.path.join(util.ECOM, "tools", "pricematch"),
        "Jivo-Price-Match-*.xlsx.summary.json",
    )
    checks.append(_check("pricematch:newest-summary", pm_summary))

    # 4. DRR panel (a fixed monthly build → informational, not a daily freshness fail)
    checks.append(_check("drr:panel.json", util.DRR_PANEL, info_only=True))
    checks.append(
        _check(
            "drr:bundle.json",
            os.path.join(os.path.dirname(util.DRR_PANEL), "bundle.json"),
            info_only=True,
        )
    )

    # 5. QC reviews + doctor logs (newest daily)
    newest_review = _newest(util.REVIEWS_DIR, "*-daily-*.json")
    checks.append(_check("qc:newest-daily-review", newest_review))
    newest_doctor = _newest(util.DOCTOR_DIR, "daily-*.json")
    checks.append(_check("health:newest-doctor-log", newest_doctor))

    # 6. deliverables + baselines (informational)
    checks.append(_check("deliverables:output/", util.OUTPUT_DIR, info_only=True))
    checks.append(_check("baselines/", util.BASELINES_DIR, info_only=True))

    # --- roll up, applying the swiggy/instamart gotcha demotion ---
    warnings = []
    demoted = []
    for c in checks:
        if c["status"] in WARN_STATUSES:
            if c["known_flaky"]:
                demoted.append(c)
            else:
                warnings.append(c)

    overall = "OK" if not warnings else "WARN"
    exit_code = 0 if not warnings else 1

    # ecom-pipeline's own doctor verdict, with the same gotcha lens (context only)
    pipeline = _pipeline_doctor(newest_doctor)

    notes = []
    if demoted:
        notes.append(
            "demoted (residential-only, expected from VPS — NOT an alarm): "
            + ", ".join("%s=%s" % (c["source"], c["status"]) for c in demoted)
        )
    if pipeline and pipeline.get("gotcha_note"):
        notes.append(pipeline["gotcha_note"])

    meta = {
        "command": "doctor",
        "date": label,
        "overall": overall,
        "warnings": len(warnings),
        "checked": len(checks),
        "stale_threshold_hours": STALE_H,
        "freshness": {
            c["source"]: util.freshness(c["path"]) for c in checks if c["path"]
        },
        "pipeline_doctor": pipeline,
        "notes": notes,
    }
    results = {
        "overall": overall,
        "checks": checks,
        "warnings": [c["source"] for c in warnings],
        "demoted_known_flaky": [c["source"] for c in demoted],
    }

    def human(_res):
        print("doctor · %s · overall %s" % (label, overall))
        rows = []
        for c in checks:
            flag = " *" if c["known_flaky"] and c["status"] in WARN_STATUSES else ""
            rows.append([c["source"] + flag, c["status"], c["detail"]])
        print(_table(["SOURCE", "STATUS", "DETAIL"], rows))
        if warnings:
            print(
                "\n  %d warning(s): %s"
                % (len(warnings), ", ".join(c["source"] for c in warnings))
            )
        else:
            print("\n  no warnings — all daily sources fresh & readable")
        if pipeline:
            print(
                "  ecom-pipeline doctor (%s): overall=%s"
                % (pipeline.get("path_date") or "?", pipeline.get("overall"))
            )
        for n in notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, results, meta, human)
    return exit_code


def _pipeline_doctor(path):
    """Read the ecom pipeline's own doctor log for context, applying the gotcha."""
    if not path or not os.path.exists(path):
        return None
    try:
        data = util.load_json(path)
    except (ValueError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    issues = data.get("issues") if isinstance(data.get("issues"), list) else []
    non_green = [
        i for i in issues if str(i.get("severity")).upper() in ("RED", "YELLOW")
    ]
    platforms = {str(i.get("platform")) for i in non_green if i.get("platform")}
    only_flaky = bool(platforms) and platforms.issubset(KNOWN_FLAKY)
    out = {
        "path": path,
        "path_date": data.get("date"),
        "overall": data.get("overall"),
        "issue_count": len(issues),
        "gotcha_note": None,
    }
    if str(data.get("overall")).upper() == "RED" and only_flaky:
        out["gotcha_note"] = (
            "ecom doctor is RED but every flagged platform is "
            "swiggy/instamart-only — per the gotcha, treat as a note"
        )
    return out


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
