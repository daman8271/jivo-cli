"""'price' command — price/MRP for a SKU across one or all platforms.

    jivo-desk price --sku JID-0016 [--platform blinkit] [--pincode 400001]

Emits one row per matching listing: platform, product, price, mrp, pincode,
availability. Human output is an aligned table.
"""

import sys

from jivo_scrape import operational_identity, util
from jivo_scrape.sources import sweeps


def register(sub):
    p = sub.add_parser("price", help="price + MRP for a SKU across platforms")
    p.add_argument(
        "--sku",
        required=True,
        help="exact JID, price code/key, qualified listing, or Factory key",
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
        print("jivo-desk price: %s" % err, file=sys.stderr)
        return 2

    store, targets, identity_meta, error = operational_identity.prepare(
        args, "price", args.sku
    )
    if error is not None:
        return error

    gathered = sweeps.gather(
        platforms,
        label,
        listing_targets=targets,
        pincode_filter=args.pincode,
    )

    rows = []
    for g in gathered:
        for raw in g["rows"]:
            rows.append(sweeps.normalize(raw, g["platform"], store))
    # cheapest first (nulls last), then platform, then product
    rows.sort(
        key=lambda r: (
            r["price"] is None,
            r["price"] if r["price"] is not None else 0,
            r["platform"],
            r["product"] or "",
        )
    )

    src = sweeps.sources_meta(gathered)
    meta = {
        "command": "price",
        "date": label,
        "date_iso": iso,
        "sku": args.sku,
        "platform": args.platform or "all",
        "pincode": args.pincode,
        "match_count": len(rows),
        "identity": identity_meta,
        "identity_states": operational_identity.summarize_states(rows),
        "freshness": src["freshness"],
        "partial_fallback": src["partial_fallback"],
        "partial_fallback_platforms": src["partial_fallback_platforms"],
        "missing_sources": src["missing_sources"],
        "notes": src["notes"],
    }

    def human(results):
        print(
            "price · %s · sku=%r%s%s"
            % (
                label,
                args.sku,
                "" if not args.platform else " · platform=%s" % args.platform,
                "" if not args.pincode else " · pincode=%s" % args.pincode,
            )
        )
        if not results:
            print("  no listings matched.")
        else:
            trows = [
                [
                    r["platform"],
                    r["listing_id"] or "-",
                    r["jid"] or "-",
                    (r["product"] or "-")[:52],
                    sweeps.fmt_price(r["price"]),
                    sweeps.fmt_price(r["mrp"]),
                    r["pincode"] or "national",
                    sweeps.fmt_stock(r["in_stock"]),
                ]
                for r in results
            ]
            print(
                sweeps.table(
                    [
                        "PLATFORM",
                        "LISTING ID",
                        "JID",
                        "PRODUCT",
                        "PRICE",
                        "MRP",
                        "PINCODE",
                        "STOCK",
                    ],
                    trows,
                )
            )
            print("  %d listing(s)." % len(results))
        _footer(meta)

    util.emit(args, rows, meta, human)
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
