"""'match' command — the price-match counter.

Answers: on <date>, how does Jivo's reference price compare to each rival's
live price, per SKU per platform, and what's the verdict?

Detail rows come from history.csv (filtered to the resolved date); the
day-level KPI rollup comes from daily.csv; the WhatsApp caption blob from the
per-day summary.json. Optional exact --sku and --pincode narrow the listing rows.
"""

from jivo_scrape import operational_identity, util
from jivo_scrape.sources import pricematch as pm


def register(sub):
    p = sub.add_parser(
        "match",
        help="price-match: Jivo reference price vs rival live price + verdict",
    )
    util.add_common_flags(p)
    p.add_argument(
        "--sku",
        help="exact JID, price code/key, qualified listing, or Factory key",
    )
    p.add_argument(
        "--pincode",
        help="filter to a pincode (price-match is a national/modal matrix; "
        "noted in meta if the source has no pincode dimension)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=40,
        help="max rows in the human table (default 40; --json is never capped)",
    )
    operational_identity.add_identity_map_flag(p)
    p.set_defaults(func=run)


def run(args):
    date_iso, label = util.resolve_date(args.date)
    store, targets, identity_meta, error = operational_identity.prepare(
        args, "match", args.sku
    )
    if error is not None:
        return error
    d_fields, d_rows = pm.load_daily()
    h_fields, h_rows = pm.load_history()

    available = pm.dates_in(d_rows) or pm.dates_in(h_rows)

    # Resolve the target date within what the files actually carry.
    target = date_iso
    date_note = None
    if label == "today":
        if available and date_iso not in available:
            target = available[-1]
            date_note = f"no price-match rows for {date_iso} yet; showing latest available snapshot {target}"
    elif available and target not in available:
        span = f"{available[0]}..{available[-1]}" if available else "none"
        date_note = f"no price-match rows for {target} (available: {span})"

    daily_row = next(
        (r for r in d_rows if (r.get("date") or "").strip() == target), None
    )

    rows = [r for r in h_rows if (r.get("date") or "").strip() == target]

    # --sku: exact product-map expansion to exact platform/listing IDs.
    if targets is not None:
        rows = [row for row in rows if pm.listing_identity(row) in targets]

    # --pincode: only if the source actually carries a pincode dimension.
    pincode_note = None
    if args.pincode:
        pin_col = pm.discover_key(h_fields, pm.PINCODE_KEYS)
        if pin_col:
            rows = [
                r
                for r in rows
                if str(r.get(pin_col, "")).strip() == str(args.pincode).strip()
            ]
        else:
            pincode_note = (
                "price-match rows carry no pincode dimension "
                "(national/modal matrix); --pincode ignored"
            )

    listings = [pm.normalize_listing(r, store) for r in rows]

    summary, summary_file = pm.load_summary(target)

    freshness = {
        "daily_csv": util.freshness(pm.DAILY_CSV),
        "history_csv": util.freshness(pm.HISTORY_CSV),
    }
    if summary is not None:
        freshness["summary_json"] = util.freshness(summary_file)

    meta = {
        "command": "match",
        "date": target,
        "date_label": label,
        "requested_date": date_iso,
        "filters": {"sku": args.sku, "pincode": args.pincode},
        "row_count": len(listings),
        "identity": identity_meta,
        "identity_states": operational_identity.summarize_states(listings),
        "freshness": freshness,
    }
    if date_note:
        meta["date_note"] = date_note
    if pincode_note:
        meta["pincode_note"] = pincode_note
    if daily_row:
        meta["day_summary"] = daily_row
    if summary is not None:
        meta["summary_json"] = summary

    util.emit(
        args,
        listings,
        meta,
        human=lambda res: _human(
            res, target, label, daily_row, date_note, pincode_note, args.limit
        ),
    )
    return 0


def _fmt(v):
    return "-" if v is None else str(v)


def _human(listings, target, label, daily_row, date_note, pincode_note, limit):
    print(
        f"Price-Match · {target} ({label})"
        + (f" · {daily_row.get('regime')} regime" if daily_row else "")
    )
    if daily_row:
        print(
            "  rollup: below {below} · above {above} · match {match} · oos {oos} · "
            "not-listed {nl} · exposure Rs {exp}".format(
                below=_fmt(daily_row.get("below")),
                above=_fmt(daily_row.get("above")),
                match=_fmt(daily_row.get("match")),
                oos=_fmt(daily_row.get("oos")),
                nl=_fmt(daily_row.get("not_listed")),
                exp=_fmt(daily_row.get("exposure")),
            )
        )
        top = daily_row.get("top_offender_sku")
        if top:
            print(
                f"  top offender: {top} on {_fmt(daily_row.get('top_offender_platform'))} ({_fmt(daily_row.get('top_offender_diff'))})"
            )
    if date_note:
        print(f"  note: {date_note}")
    if pincode_note:
        print(f"  note: {pincode_note}")

    if not listings:
        print("  (no listing rows for this date / filter)")
        return

    cols = [
        ("SKU", "sku", 24),
        ("PLATFORM", "platform", 15),
        ("LISTING ID", "listing_id", 18),
        ("JID", "jid", 10),
        ("JIVO", "jivo_ref", 7),
        ("RIVAL", "rival_modal", 7),
        ("VERDICT", "verdict", 10),
        ("DIFF", "diff", 7),
    ]
    header = "  " + "  ".join(h.ljust(w) for h, _, w in cols)
    print()
    print(header)
    print("  " + "  ".join("-" * w for _, _, w in cols))
    shown = listings[:limit]
    for row in shown:
        line = "  " + "  ".join(_fmt(row.get(key))[:w].ljust(w) for _, key, w in cols)
        print(line)
    if len(listings) > limit:
        print(f"  ... {len(listings) - limit} more (use --json for all, or --limit)")
