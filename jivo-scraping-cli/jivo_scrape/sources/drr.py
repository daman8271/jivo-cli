"""Read-only reader for the DRR (Daily Run-Rate) panel.

Sources (READ-ONLY):
  build/panel.json  — the raw panel: meta (as_of, window, platform_max_date,
                      unit notes), coverage[], and long raw series
                      (platform_day, price_day, sku_day, targets, ...).
  build/bundle.json — the curated digest built from panel.json: headline
                      trend / pace-vs-target / premium-mix / inventory-band
                      numbers, already rolled up to house + per-platform.

The panel is a fixed monthly build (a single snapshot keyed by meta.as_of and
meta.window), NOT a per-day file, so `--date` cannot select a different
snapshot; the caller surfaces the file mtime front-and-center instead.
"""

import os

from jivo_scrape import util

PANEL_JSON = util.DRR_PANEL
BUNDLE_JSON = os.path.join(os.path.dirname(PANEL_JSON), "bundle.json")


def load_panel():
    if not os.path.exists(PANEL_JSON):
        return None
    return util.load_json(PANEL_JSON)


def load_bundle():
    if not os.path.exists(BUNDLE_JSON):
        return None
    return util.load_json(BUNDLE_JSON)


def _get(d, *path, default=None):
    """Safe nested lookup; returns default on any missing/None hop."""
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def key_numbers(panel, bundle):
    """Distil panel + bundle into the DRR headline numbers.

    Robust to either source being absent: panel supplies meta+coverage,
    bundle supplies the curated house/platform rollups; each falls back to
    the other where the same field exists.
    """
    panel = panel or {}
    bundle = bundle or {}

    meta = panel.get("meta") or bundle.get("meta") or {}
    trend_head = _get(bundle, "trend", "headline", default={}) or {}

    out = {
        "as_of": meta.get("as_of"),
        "window": meta.get("window"),
        "platform_max_date": meta.get("platform_max_date"),
        "units_note": meta.get("units_note"),
        "coverage": panel.get("coverage") or bundle.get("coverage"),
        "house_trend": _get(trend_head, "house", "ALL"),
        "pace_house": _get(bundle, "pace", "house"),
        "pace_by_platform": _get(bundle, "pace", "platform_rollup"),
        "pace_misses": _get(bundle, "pace", "misses"),
        "mix_house": _get(bundle, "mix", "house"),
        "inventory_bands": _get(bundle, "inventory", "house", "band_counts"),
        "worst_stockout_risk": (
            _get(bundle, "inventory", "house", "worst_stockout_risk", default=[]) or []
        )[:5],
        "platform_trend": {
            p: (v.get("ALL") if isinstance(v, dict) else None)
            for p, v in trend_head.items()
            if p != "house"
        },
    }
    return out


def filter_platform(kn, platform):
    """Narrow the key-numbers dict to one platform. Returns (kn, known_bool)."""
    known = False
    rollup = kn.get("pace_by_platform") or []
    match = [r for r in rollup if r.get("platform") == platform]
    if match:
        known = True
    kn = dict(kn)
    kn["pace_by_platform"] = match
    kn["pace_misses"] = [
        m for m in (kn.get("pace_misses") or []) if m.get("platform") == platform
    ]
    pt = kn.get("platform_trend") or {}
    if platform in pt:
        known = True
        kn["platform_trend"] = {platform: pt[platform]}
        kn["house_trend"] = pt[platform]  # spotlight the platform in the headline slot
    else:
        kn["platform_trend"] = {}
    kn["worst_stockout_risk"] = [
        w
        for w in (kn.get("worst_stockout_risk") or [])
        if w.get("platform") == platform
    ]
    cov = kn.get("coverage") or []
    cov_match = [c for c in cov if c.get("platform") == platform]
    if cov_match:
        known = True
        kn["coverage"] = cov_match
    return kn, known
