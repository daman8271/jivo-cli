"""Read-only reader for the today/yesterday landing axis.

Pulls together, per platform, the answer to "did the daily sweep land, and how
big was it?" for a resolved date, plus the today/ manifest highlights.

Sources (all READ-ONLY):
  platforms/<p>/result.json          — live sweep; summary + allRows + partial.
  platforms/<p>/result.last-good.json — fallback when live is partial.
  reviews/<p>-daily-YYYY-MM-DD.json  — the 18:xx QC verdict for a given day
                                       (carries rows / verdict / captured_at).
  today/_manifest.json               — today's snapshot manifest.
  today.prev/_manifest.json          — yesterday's snapshot manifest.

Date axis (per SOURCES.md):
- ``today``     -> live result.json is authoritative for "landed today" + rows;
                  today/_manifest.json supplies the highlights.
- ``yesterday`` -> the dated daily review (reviews/<p>-daily-<iso>.json) is the
                  authoritative dated record for rows + verdict; today.prev/
                  supplies the manifest highlights.
- explicit ``YYYY-MM-DD`` -> dated daily reviews where kept; no manifest.

Nothing here assumes a key exists; a missing/renamed field degrades to None.
"""

import datetime as _dt
import os

from jivo_scrape import util


def _mtime_date(fresh):
    """Calendar date (ISO string) of a freshness dict's mtime, or None."""
    if not fresh or not fresh.get("mtime"):
        return None
    try:
        return _dt.datetime.fromisoformat(fresh["mtime"]).date().isoformat()
    except (ValueError, TypeError):
        return None


# --- manifest -------------------------------------------------------------
def manifest_path(label):
    """(path_or_None) for the manifest that matches a date label."""
    if label == "today":
        return os.path.join(util.TODAY_DIR, "_manifest.json")
    if label == "yesterday":
        return os.path.join(util.YDAY_DIR, "_manifest.json")
    return None  # arbitrary dated builds are not retained as manifests


def load_manifest(label):
    """(highlights_or_None, path_or_None, freshness_or_None)."""
    path = manifest_path(label)
    if not path or not os.path.exists(path):
        return None, path, None
    try:
        data = util.load_json(path)
    except (ValueError, OSError):
        return None, path, util.freshness(path)
    if not isinstance(data, dict):
        return None, path, util.freshness(path)
    srcs = data.get("sources")
    src_files = {}
    if isinstance(srcs, dict):
        for name, meta in srcs.items():
            src_files[name] = meta.get("files") if isinstance(meta, dict) else None
    highlights = {
        "date": data.get("date"),
        "generated_at": data.get("generated_at"),
        "mode": data.get("mode"),
        "dry_run": data.get("dry_run"),
        "total_files": data.get("total_files"),
        "source_files": src_files,
    }
    return highlights, path, util.freshness(path)


# --- live sweep result ----------------------------------------------------
def _result_files(platform):
    pdir = os.path.join(util.PLATFORMS_DIR, platform)
    return (
        os.path.join(pdir, "result.json"),
        os.path.join(pdir, "result.last-good.json"),
    )


def load_result(platform):
    """Read a platform's live result.json defensively.

    Returns a dict describing presence, row count (summary.total_rows preferred,
    else len(allRows)), the partial flag, and whether we fell back to last-good.
    Never raises on a missing/garbled file.
    """
    live, lastgood = _result_files(platform)
    out = {
        "path": None,
        "freshness": None,
        "rows": None,
        "rows_source": None,
        "partial": None,
        "partial_fallback": False,
        "missing": False,
        "unreadable": False,
    }
    if not os.path.exists(live):
        out["missing"] = True
        return out
    try:
        data = util.load_json(live)
    except (ValueError, OSError):
        out["unreadable"] = True
        out["path"] = live
        out["freshness"] = util.freshness(live)
        return out
    if not isinstance(data, dict):
        out["unreadable"] = True
        out["path"] = live
        out["freshness"] = util.freshness(live)
        return out

    src = live
    out["partial"] = data.get("partial")
    if data.get("partial") and os.path.exists(lastgood):
        try:
            good = util.load_json(lastgood)
            if isinstance(good, dict):
                data = good
                src = lastgood
                out["partial_fallback"] = True
        except (ValueError, OSError):
            pass  # keep the partial live data if last-good is unreadable

    summary = data.get("summary")
    total = summary.get("total_rows") if isinstance(summary, dict) else None
    if isinstance(total, bool):
        total = None
    if isinstance(total, (int, float)):
        out["rows"] = int(total)
        out["rows_source"] = "summary.total_rows"
    else:
        rows = data.get("allRows")
        if isinstance(rows, list):
            out["rows"] = len(rows)
            out["rows_source"] = "allRows"

    out["path"] = src
    out["freshness"] = util.freshness(src)
    return out


# --- dated QC review ------------------------------------------------------
def review_path(platform, iso):
    return os.path.join(util.REVIEWS_DIR, "%s-daily-%s.json" % (platform, iso))


def load_review(platform, iso):
    """(review_dict_or_None, path, freshness). Never raises."""
    p = review_path(platform, iso)
    if not os.path.exists(p):
        return None, p, None
    try:
        data = util.load_json(p)
    except (ValueError, OSError):
        return None, p, util.freshness(p)
    if not isinstance(data, dict):
        return None, p, util.freshness(p)
    return data, p, util.freshness(p)


# --- per-platform assembly ------------------------------------------------
def platform_status(platform, iso, label):
    """Assemble the landing/row-count/verdict picture for one platform+date."""
    st = {
        "platform": platform,
        "landed": False,
        "landed_basis": None,
        "rows": None,
        "rows_source": None,
        "partial": None,
        "partial_fallback": False,
        "review_present": False,
        "review_verdict": None,
        "captured_at": None,
        "result_path": None,
        "result_freshness": None,
        "result_mtime_date": None,
        "review_path": None,
        "review_freshness": None,
        "missing": False,
        "unreadable": False,
        "note": None,
    }

    review, rpath, rfresh = load_review(platform, iso)
    st["review_path"] = rpath
    st["review_freshness"] = rfresh
    if review is not None:
        st["review_present"] = True
        st["review_verdict"] = review.get("verdict")
        st["captured_at"] = review.get("captured_at")

    if label == "today":
        res = load_result(platform)
        st["result_path"] = res["path"]
        st["result_freshness"] = res["freshness"]
        st["result_mtime_date"] = _mtime_date(res["freshness"])
        st["partial"] = res["partial"]
        st["partial_fallback"] = res["partial_fallback"]
        st["rows"] = res["rows"]
        st["rows_source"] = res["rows_source"]
        if res["missing"]:
            st["missing"] = True
        if res["unreadable"]:
            st["unreadable"] = True
        # "landed" == the live sweep file is dated the resolved calendar day.
        if st["result_mtime_date"] == iso:
            st["landed"] = True
            st["landed_basis"] = "result.json mtime"
        elif st["review_present"]:
            st["landed"] = True
            st["landed_basis"] = "review file"
        if not st["landed"] and st["result_mtime_date"]:
            st["note"] = "newest sweep is %s" % st["result_mtime_date"]
    else:
        # Past dates: the dated QC review is the authoritative record.
        if review is not None:
            rows = review.get("rows")
            if isinstance(rows, bool):
                rows = None
            if isinstance(rows, (int, float)):
                st["rows"] = int(rows)
                st["rows_source"] = "review.rows"
            st["landed"] = True
            st["landed_basis"] = "review file"
        else:
            st["missing"] = True
            st["note"] = "no dated review retained for %s" % iso

    return st


def gather(platforms, iso, label):
    """Per-platform statuses in platform order."""
    return [platform_status(p, iso, label) for p in platforms]


def summary_counts(statuses):
    """Roll up landed / missing / partial across the platform statuses."""
    landed = [s["platform"] for s in statuses if s["landed"]]
    missing = [s["platform"] for s in statuses if not s["landed"]]
    partial = [s["platform"] for s in statuses if s.get("partial_fallback")]
    total_rows = sum(s["rows"] for s in statuses if isinstance(s.get("rows"), int))
    return {
        "platforms_total": len(statuses),
        "landed_count": len(landed),
        "landed": landed,
        "not_landed": missing,
        "partial_fallback_platforms": partial,
        "total_rows": total_rows,
    }
