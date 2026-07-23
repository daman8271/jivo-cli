"""Read-only readers for the price-match godown.

Sources (all READ-ONLY):
  daily.csv    — one row per date: the day-level KPI rollup
                 (regime, below/above/match/oos counts, exposure, top offender).
  history.csv  — one row per (date, sku, platform, listing): the detail behind
                 the rollup (ref_price vs live price, status/verdict, diff).
  Jivo-Price-Match-<date>.xlsx.summary.json — the WhatsApp-caption summary blob.

Field names in these CSVs are stable today but we still discover them
defensively (candidate-key lists) so a header change degrades to null rather
than KeyError-ing, per the CLI contract.
"""

import csv
import os

from jivo_scrape import identity, util
from jivo_scrape.sources import sweeps

DAILY_CSV = os.path.join(util.PRICEMATCH_DIR, "daily.csv")
HISTORY_CSV = os.path.join(util.PRICEMATCH_DIR, "history.csv")
SUMMARY_DIR = os.path.join(util.ECOM, "tools", "pricematch")

# Candidate column names, tried in order. First present + non-empty wins.
SKU_KEYS = ("sku", "canonical_sku", "item", "product", "name", "title")
PINCODE_KEYS = ("pincode", "pin", "pin_code", "zip", "postal_code")
JIVO_PRICE_KEYS = ("ref_price", "jivo_price", "target_price", "reference_price")
RIVAL_PRICE_KEYS = ("live_modal", "selling_price", "sp", "price", "live_min")
VERDICT_KEYS = ("status", "verdict", "result", "compliance")
INSTOCK_KEYS = ("in_stock", "availability", "available")


def discover_key(fieldnames, candidates):
    """Return the first candidate present in a CSV header, else None."""
    fields = set(fieldnames or ())
    for c in candidates:
        if c in fields:
            return c
    return None


def first(row, candidates):
    """First non-empty value among candidate keys in a row, else None."""
    for c in candidates:
        if c in row:
            v = row[c]
            if v is not None and str(v).strip() != "":
                return v
    return None


def numish(v):
    """Best-effort number: '1409'->1409, '-11.79'->-11.79, ''/None->None."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f.is_integer() else f


def _read_csv(path):
    """(fieldnames, rows) for a CSV, or ([], []) if the file is absent."""
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        rows = list(r)
        return (r.fieldnames or []), rows


def load_daily():
    return _read_csv(DAILY_CSV)


def load_history():
    return _read_csv(HISTORY_CSV)


def dates_in(rows):
    """Sorted distinct 'date' values present in a row list."""
    return sorted({(r.get("date") or "").strip() for r in rows if r.get("date")})


def summary_path(date_iso):
    return os.path.join(SUMMARY_DIR, f"Jivo-Price-Match-{date_iso}.xlsx.summary.json")


def load_summary(date_iso):
    """(summary_dict_or_None, path). Never raises on a malformed blob."""
    p = summary_path(date_iso)
    if not os.path.exists(p):
        return None, p
    try:
        return util.load_json(p), p
    except (ValueError, OSError):
        return None, p


def listing_identity(row):
    """Exact ``(platform, listing_id)`` observed in one history CSV row.

    The price-match contract has its own literal ``listing_id`` column. Empty
    cells remain missing; SKU/name columns are never used as an identity alias.
    """
    platform = row.get("platform") if isinstance(row, dict) else None
    platform = platform.strip().lower() if isinstance(platform, str) else None
    raw_id = row.get("listing_id") if isinstance(row, dict) else None
    listing_id = None
    if raw_id is not None and not isinstance(raw_id, bool):
        candidate = str(raw_id).strip()
        listing_id = candidate or None
    return platform, listing_id


def normalize_listing(row, identity_store=None):
    """Map history to a stable record, retaining and exactly enriching its ID."""
    platform, listing_id = listing_identity(row)
    source_contract = sweeps.LISTING_ID_FIELDS.get(platform)
    normalized = {
        "sku": first(row, SKU_KEYS),
        "platform": platform,
        "listing_id": listing_id,
        "listing_id_kind": source_contract[1] if source_contract else "listing_id",
        "listing_key": identity.listing_key_for(platform, listing_id),
        "jivo_ref": numish(first(row, JIVO_PRICE_KEYS)),
        "rival_modal": numish(row.get("live_modal")),
        "rival_min": numish(row.get("live_min")),
        "rival_max": numish(row.get("live_max")),
        "in_stock": first(row, INSTOCK_KEYS),
        "verdict": first(row, VERDICT_KEYS),
        "diff": numish(row.get("diff")),
        "diff_pct": numish(row.get("diff_pct")),
    }
    if identity_store is not None:
        normalized.update(identity_store.enrich_listing(platform, listing_id))
    return normalized
