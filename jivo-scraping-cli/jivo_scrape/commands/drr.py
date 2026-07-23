"""'drr' command — the DRR (Daily Run-Rate) panel key numbers.

Surfaces the panel's headline figures: house MTD run-rate + projection,
pace vs monthly target, premium mix vs the north-star, and inventory band
counts — plus a per-platform pace rollup. --platform spotlights one platform.

The panel is a fixed monthly build (single snapshot at meta.as_of over
meta.window), so `--date` cannot pick a different day's file; the resolved
label is echoed and the file mtime is put front-and-center in meta.freshness.
"""

from jivo_scrape import util
from jivo_scrape.sources import drr as drr_src


def register(sub):
    p = sub.add_parser(
        "drr",
        help="DRR panel key numbers: MTD run-rate, pace vs target, premium mix, inventory bands",
    )
    util.add_common_flags(p)
    p.add_argument(
        "--platform", help="spotlight one platform (e.g. amazon, bigbasket, zepto)"
    )
    p.set_defaults(func=run)


def run(args):
    date_iso, label = util.resolve_date(args.date)

    panel = drr_src.load_panel()
    bundle = drr_src.load_bundle()
    if panel is None and bundle is None:
        raise FileNotFoundError(drr_src.PANEL_JSON)

    kn = drr_src.key_numbers(panel, bundle)

    platform_note = None
    if args.platform:
        kn, known = drr_src.filter_platform(kn, args.platform)
        if not known:
            platform_note = f"unknown platform '{args.platform}' — not in the panel"

    as_of = kn.get("as_of")
    window = kn.get("window") or {}
    # The panel is a fixed monthly snapshot; a --date other than as_of does not
    # select a different file. Be honest about that.
    date_note = None
    if date_iso != as_of:
        date_note = (
            f"DRR panel is a fixed monthly build (as_of {as_of}, "
            f"window {window.get('start')}..{window.get('end')}); "
            f"--date {date_iso} ({label}) does not select a different snapshot"
        )

    # Freshness front-and-center: panel mtime leads.
    freshness = {
        "panel_json": util.freshness(drr_src.PANEL_JSON),
        "bundle_json": util.freshness(drr_src.BUNDLE_JSON),
    }

    meta = {
        "command": "drr",
        "date_label": label,
        "requested_date": date_iso,
        "as_of": as_of,
        "window": window,
        "platform_max_date": kn.get("platform_max_date"),
        "units_note": kn.get("units_note"),
        "freshness": freshness,
    }
    if date_note:
        meta["date_note"] = date_note
    if platform_note:
        meta["platform_note"] = platform_note

    util.emit(
        args,
        kn,
        meta,
        human=lambda res: _human(
            res, as_of, label, date_note, platform_note, args.platform
        ),
    )
    return 0


def _n(v):
    """Format a number compactly; passthrough for non-numbers/None."""
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:,.1f}" if abs(v) >= 100 else f"{v:,.2f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def _pct(v):
    return "-" if v is None else f"{v * 100:.1f}%"


def _human(kn, as_of, label, date_note, platform_note, platform):
    scope = platform or "house"
    print(f"DRR panel · as_of {as_of} · {scope}")
    if date_note:
        print(f"  note: {date_note}")
    if platform_note:
        print(f"  note: {platform_note}")

    ht = kn.get("house_trend")
    if ht:
        print()
        print(f"  Run-rate ({'ALL tier'}):")
        print(
            f"    MTD        {_n(ht.get('mtd_ltr'))} L · {_n(ht.get('mtd_units'))} u · Rs {_n(ht.get('mtd_value'))}"
        )
        print(
            f"    DRR/day    {_n(ht.get('drr_ltr'))} L · {_n(ht.get('drr_units'))} u · Rs {_n(ht.get('drr_value'))}"
        )
        print(
            f"    Proj EOM   {_n(ht.get('projected_month_end_ltr'))} L · Rs {_n(ht.get('projected_month_end_value'))}"
        )
        print(
            f"    DoD {_pct((ht.get('dod_ltr_pct') or 0) / 100) if ht.get('dod_ltr_pct') is not None else '-'} · "
            f"WoW {_pct((ht.get('wow_ltr_pct') or 0) / 100) if ht.get('wow_ltr_pct') is not None else '-'} (ltr)"
        )

    pace = kn.get("pace_house")
    if pace and not platform:
        print()
        print("  Pace vs target (house):")
        print(
            f"    target {_n(pace.get('target_ltr'))} L · done {_n(pace.get('mtd_done_ltr'))} L · "
            f"achieved {_pct(pace.get('achieved_pct'))}"
        )
        print(
            f"    proj EOM {_n(pace.get('projected_eom_ltr'))} L → {_pct(pace.get('projected_vs_target_pct'))} of target · "
            f"growth vs last month {_pct(pace.get('growth_pct_vs_last_month'))}"
        )

    mix = kn.get("mix_house")
    if mix and not platform:
        print()
        print("  Premium mix (house):")
        print(
            f"    premium {_n(mix.get('premium_ltr'))} L vs commodity {_n(mix.get('commodity_ltr'))} L · "
            f"mix {_pct(mix.get('premium_mix_pct'))} (north-star {_pct(mix.get('north_star_pct'))}, "
            f"gap {_n(mix.get('gap_to_north_star_pp'))}pp)"
        )

    bands = kn.get("inventory_bands")
    if bands and not platform:
        print()
        print("  Inventory bands: " + " · ".join(f"{k} {v}" for k, v in bands.items()))

    rollup = kn.get("pace_by_platform") or []
    if rollup:
        print()
        print("  Pace by platform:")
        print(
            "    "
            + "PLATFORM".ljust(18)
            + "TARGET".rjust(12)
            + "DONE".rjust(12)
            + "ACHIEVED".rjust(11)
            + "  MISS?"
        )
        for r in rollup:
            miss = "MISS" if r.get("will_miss_target") else ""
            print(
                "    "
                + str(r.get("platform")).ljust(18)
                + _n(r.get("target_ltr")).rjust(12)
                + _n(r.get("mtd_done_ltr")).rjust(12)
                + _pct(r.get("achieved_pct")).rjust(11)
                + "  "
                + miss
            )

    wsr = kn.get("worst_stockout_risk") or []
    if wsr:
        print()
        print("  Worst stock-out risk (lowest DOH):")
        for w in wsr:
            print(
                f"    {str(w.get('platform')).ljust(10)} {str(w.get('item')).ljust(22)} "
                f"DOH {_n(w.get('doh'))}d · SOH {_n(w.get('soh_ltr'))} L · DRR {_n(w.get('drr_ltr'))} L/d"
            )
