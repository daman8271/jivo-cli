"""Shared helpers: paths, date resolution, JSON envelope, freshness.

Contract for every command:
- add_common_flags(parser) gives --json and --date.
- emit(args, results, meta) prints the {"meta":...,"results":...} envelope
  (with meta.freshness) under --json, else a human-readable rendering.
- All reads are READ-ONLY; never open any data path for writing.
"""

import datetime as _dt
import json
import os

# Root = any ecom-intel checkout (the VPS live godown at /opt/ecom-intel IS a
# checkout of github.com/daman8271/ecom-intel). Point JIVO_SCRAPE_ROOT at any
# clone to read the same data families elsewhere. READ-ONLY, always.
ECOM = os.environ.get("JIVO_SCRAPE_ROOT", "/opt/ecom-intel")
PLATFORMS_DIR = os.path.join(ECOM, "platforms")
TODAY_DIR = os.path.join(ECOM, "today")
YDAY_DIR = os.path.join(ECOM, "today.prev")
PRICEMATCH_DIR = os.path.join(ECOM, "data", "pricematch")
REVIEWS_DIR = os.path.join(ECOM, "reviews")
DOCTOR_DIR = os.path.join(ECOM, "logs", "doctor")
OUTPUT_DIR = os.path.join(ECOM, "output")
BASELINES_DIR = os.path.join(ECOM, "baselines")
DRR_PANEL = os.environ.get("JIVO_DRR_PANEL", "/root/jivo-drr-panel/build/panel.json")

PLATFORMS = [
    "amazon",
    "amazon-fresh",
    "amazon-now",
    "bigbasket",
    "blinkit",
    "flipkart",
    "flipkart-minutes",
    "instamart",
    "swiggy-instamart",
    "zepto",
]


def add_common_flags(parser):
    parser.add_argument(
        "--json", action="store_true", help="machine-readable envelope on stdout"
    )
    parser.add_argument(
        "--date",
        default="today",
        help="today | yesterday | YYYY-MM-DD (default: today)",
    )


def resolve_date(spec):
    """Return (iso_date_string, label) where label is today/yesterday/dated."""
    today = _dt.date.today()
    if spec in (None, "", "today"):
        return today.isoformat(), "today"
    if spec == "yesterday":
        return (today - _dt.timedelta(days=1)).isoformat(), "yesterday"
    d = _dt.date.fromisoformat(spec)  # raises ValueError on garbage
    if d == today:
        return d.isoformat(), "today"
    if d == today - _dt.timedelta(days=1):
        return d.isoformat(), "yesterday"
    return d.isoformat(), "dated"


def freshness(path):
    """mtime info for a source file, or None if absent."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    mtime = _dt.datetime.fromtimestamp(st.st_mtime)
    age_min = (_dt.datetime.now() - mtime).total_seconds() / 60.0
    return {
        "path": path,
        "mtime": mtime.isoformat(timespec="seconds"),
        "age_minutes": round(age_min, 1),
    }


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def emit(args, results, meta=None, human=None):
    """Print envelope under --json, else call human(results) or a default dump."""
    if getattr(args, "json", False):
        print(
            json.dumps({"meta": meta or {}, "results": results}, indent=2, default=str)
        )
        return
    if human is not None:
        human(results)
    else:
        print(json.dumps(results, indent=2, default=str))
