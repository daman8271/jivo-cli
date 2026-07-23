"""'compare' command — one summary row per platform for a SKU, side by side.

    jivo-desk compare --sku JID-0016

For each platform (ALL of them), summarises the matching listings: match count,
min / modal / max price, and in-stock %. Human output is a side-by-side table.
"""

import sys

from jivo_scrape import operational_identity, util
from jivo_scrape.sources import sweeps


def register(sub):
    p = sub.add_parser("compare", help="side-by-side price/stock summary per platform")
    p.add_argument(
        "--sku",
        required=True,
        help="exact JID, price code/key, qualified listing, or Factory key",
    )
    p.add_argument("--pincode", help="limit to one pincode (optional)")
    operational_identity.add_identity_map_flag(p)
    util.add_common_flags(p)
    p.set_defaults(func=run)


def run(args):
    iso, label = util.resolve_date(args.date)
    platforms = list(util.PLATFORMS)  # compare is always across ALL platforms
    store, targets, identity_meta, error = operational_identity.prepare(
        args, "compare", args.sku
    )
    if error is not None:
        return error
    gathered = sweeps.gather(
        platforms,
        label,
        listing_targets=targets,
        pincode_filter=args.pincode,
    )

    summary = []
    for g in gathered:
        prices = []
        listings = []
        n_in = n_oos = n_unk = 0
        for raw in g["rows"]:
            nr = sweeps.normalize(raw, g["platform"], store)
            listings.append(nr)
            if nr["price"] is not None:
                prices.append(nr["price"])
            st = nr["in_stock"]
            if st is True:
                n_in += 1
            elif st is False:
                n_oos += 1
            else:
                n_unk += 1
        n = len(g["rows"])
        known = n_in + n_oos
        summary.append(
            {
                "platform": g["platform"],
                "matches": n,
                "min_price": min(prices) if prices else None,
                "modal_price": sweeps.mode(prices),
                "max_price": max(prices) if prices else None,
                "in_stock": n_in,
                "oos": n_oos,
                "unknown": n_unk,
                "in_stock_pct": round(100.0 * n_in / known, 1) if known else None,
                "identity_states": operational_identity.summarize_states(listings),
                "listing_ids": [row["listing_id"] for row in listings],
                "listing_keys": [row["listing_key"] for row in listings],
                "canonical_product_keys": sorted(
                    {
                        row["canonical_product_key"]
                        for row in listings
                        if row["canonical_product_key"] is not None
                    }
                ),
                "jids": sorted(
                    {row["jid"] for row in listings if row["jid"] is not None}
                ),
                "factory_item_keys": sorted(
                    {
                        binding["factory_item_key"]
                        for row in listings
                        for binding in row["factory_bindings"]
                    }
                ),
                "listings": listings,
            }
        )

    src = sweeps.sources_meta(gathered)
    meta = {
        "command": "compare",
        "date": label,
        "date_iso": iso,
        "sku": args.sku,
        "pincode": args.pincode,
        "platforms_with_matches": sum(1 for s in summary if s["matches"]),
        "identity": identity_meta,
        "identity_states": operational_identity.summarize_states(
            [listing for row in summary for listing in row["listings"]]
        ),
        "freshness": src["freshness"],
        "partial_fallback": src["partial_fallback"],
        "partial_fallback_platforms": src["partial_fallback_platforms"],
        "missing_sources": src["missing_sources"],
        "notes": src["notes"],
    }

    def human(rows):
        print(
            "compare · %s · sku=%r%s"
            % (
                label,
                args.sku,
                "" if not args.pincode else " · pincode=%s" % args.pincode,
            )
        )
        trows = []
        for s in rows:
            trows.append(
                [
                    s["platform"],
                    s["matches"],
                    sweeps.fmt_price(s["min_price"]),
                    sweeps.fmt_price(s["modal_price"]),
                    sweeps.fmt_price(s["max_price"]),
                    "-" if s["in_stock_pct"] is None else "%.1f%%" % s["in_stock_pct"],
                ]
            )
        print(sweeps.table(["PLATFORM", "N", "MIN", "MODAL", "MAX", "IN%"], trows))
        hits = [s["platform"] for s in rows if s["matches"]]
        print(
            "  %d of %d platforms carry a match%s."
            % (len(hits), len(rows), ("" if not hits else ": " + ", ".join(hits)))
        )
        _footer(meta)

    util.emit(args, summary, meta, human)
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
