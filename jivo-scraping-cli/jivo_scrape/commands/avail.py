"""'avail' command — availability / OOS focus with per-platform counts.

    jivo-desk avail [--sku JID-0016] [--platform blinkit] [--pincode 400001]

--sku is optional here (omit it for the whole-catalogue availability picture).
Reports in-stock vs OOS counts per platform, plus an OOS detail table.
"""

import sys

from jivo_scrape import operational_identity, util
from jivo_scrape.sources import sweeps


def register(sub):
    p = sub.add_parser("avail", help="availability / OOS counts per platform")
    p.add_argument(
        "--sku",
        help="exact JID, price code/key, qualified listing, or Factory key (default: all)",
    )
    p.add_argument("--platform", help="limit to one platform (default: all)")
    p.add_argument("--pincode", help="limit to one pincode")
    operational_identity.add_identity_map_flag(p)
    util.add_common_flags(p)
    p.set_defaults(func=run)


def run(args):
    iso, label = util.resolve_date(args.date)
    platforms, err = sweeps.select_platforms(args.platform)
    if err:
        print("jivo-desk avail: %s" % err, file=sys.stderr)
        return 2

    store, targets, identity_meta, error = operational_identity.prepare(
        args, "avail", args.sku
    )
    if error is not None:
        return error

    gathered = sweeps.gather(
        platforms,
        label,
        listing_targets=targets,
        pincode_filter=args.pincode,
    )

    per_platform = []
    listing_rows = []
    oos_rows = []
    tot_in = tot_oos = tot_unknown = 0
    for g in gathered:
        platform_rows = []
        n_in = n_oos = n_unk = 0
        for raw in g["rows"]:
            nr = sweeps.normalize(raw, g["platform"], store)
            platform_rows.append(nr)
            listing_rows.append(nr)
            st = nr["in_stock"]
            if st is True:
                n_in += 1
            elif st is False:
                n_oos += 1
                oos_rows.append(nr)
            else:
                n_unk += 1
        total = n_in + n_oos + n_unk
        known = n_in + n_oos
        per_platform.append(
            {
                "platform": g["platform"],
                "total": total,
                "in_stock": n_in,
                "oos": n_oos,
                "unknown": n_unk,
                "in_stock_pct": round(100.0 * n_in / known, 1) if known else None,
                "identity_states": operational_identity.summarize_states(
                    platform_rows
                ),
            }
        )
        tot_in += n_in
        tot_oos += n_oos
        tot_unknown += n_unk

    oos_rows.sort(key=lambda r: (r["platform"], r["product"] or ""))

    src = sweeps.sources_meta(gathered)
    meta = {
        "command": "avail",
        "date": label,
        "date_iso": iso,
        "sku": args.sku,
        "platform": args.platform or "all",
        "pincode": args.pincode,
        "totals": {"in_stock": tot_in, "oos": tot_oos, "unknown": tot_unknown},
        "identity": identity_meta,
        "identity_states": operational_identity.summarize_states(listing_rows),
        "freshness": src["freshness"],
        "partial_fallback": src["partial_fallback"],
        "partial_fallback_platforms": src["partial_fallback_platforms"],
        "missing_sources": src["missing_sources"],
        "notes": src["notes"],
    }
    results = {
        "per_platform": per_platform,
        "listings": listing_rows,
        "oos_rows": oos_rows,
    }

    def human(res):
        hdr = "avail · %s" % label
        if args.sku:
            hdr += " · sku=%r" % args.sku
        if args.platform:
            hdr += " · platform=%s" % args.platform
        if args.pincode:
            hdr += " · pincode=%s" % args.pincode
        print(hdr)
        trows = []
        for pp in res["per_platform"]:
            trows.append(
                [
                    pp["platform"],
                    pp["total"],
                    pp["in_stock"],
                    pp["oos"],
                    pp["unknown"],
                    "-"
                    if pp["in_stock_pct"] is None
                    else "%.1f%%" % pp["in_stock_pct"],
                ]
            )
        print(sweeps.table(["PLATFORM", "TOTAL", "IN", "OOS", "UNK", "IN%"], trows))
        print(
            "  totals: %d in-stock · %d OOS · %d unknown"
            % (tot_in, tot_oos, tot_unknown)
        )
        oos = res["oos_rows"]
        if oos:
            print("\n  OUT OF STOCK (%d):" % len(oos))
            drows = [
                [
                    r["platform"],
                    r["listing_id"] or "-",
                    r["jid"] or "-",
                    (r["product"] or "-")[:52],
                    r["pincode"] or "national",
                ]
                for r in oos[:40]
            ]
            print(
                sweeps.table(
                    ["PLATFORM", "LISTING ID", "JID", "PRODUCT", "PINCODE"],
                    drows,
                )
            )
            if len(oos) > 40:
                print("  … %d more (use --json for all)." % (len(oos) - 40))
        _footer(meta)

    util.emit(args, results, meta, human)
    return 0


def _footer(meta):
    if meta["partial_fallback"]:
        print(
            "  note: served last-good (live was partial) for: %s"
            % ", ".join(meta["partial_fallback_platforms"]),
            file=sys.stderr,
        )
    for n in meta["notes"]:
        print("  note: %s" % n, file=sys.stderr)
    if meta["missing_sources"]:
        print(
            "  note: no live sweep for: %s" % ", ".join(meta["missing_sources"]),
            file=sys.stderr,
        )
