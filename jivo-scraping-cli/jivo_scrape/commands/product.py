"""Exact cross-CLI product identity resolution.

    jivo-desk product resolve <IDENTIFIER>
    jivo-desk product search <TEXT>
    jivo-desk product verify
    jivo-desk product coverage

The shared map is external and read-only.  A released map that does not pass
all coverage and referential-integrity gates is rejected with exit code 6.
"""

import argparse
import json
import sys

from jivo_scrape import identity
from jivo_scrape import util


EXIT_NOT_FOUND = 4
EXIT_AMBIGUOUS = 5
EXIT_INVALID_MAP = 6


def _add_flags(parser, preserve_parent=False):
    default = argparse.SUPPRESS if preserve_parent else None
    parser.add_argument(
        "--identity-map",
        default=default,
        help="shared v1 map (default: $JIVO_PRODUCT_IDENTITY_MAP, then repo-relative discovery)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS if preserve_parent else False,
        help="machine-readable envelope on stdout",
    )


def register(sub):
    parent = sub.add_parser(
        "product",
        help="exact SKU/JID/listing/qualified-Factory identity resolution",
        description=(
            "Resolve exact stable product identifiers across price scraping and "
            "Factory. Names are search candidates only."
        ),
    )
    _add_flags(parent)
    commands = parent.add_subparsers(dest="product_command", metavar="<action>")

    resolve = commands.add_parser(
        "resolve",
        help="resolve an exact JID, price SKU, listing, or qualified Factory key",
    )
    resolve.add_argument("identifier", metavar="IDENTIFIER")
    _add_flags(resolve, preserve_parent=True)
    resolve.set_defaults(func=run_resolve)

    search = commands.add_parser(
        "search", help="find name/text candidates (never performs a join)"
    )
    search.add_argument("text", metavar="TEXT")
    search.add_argument(
        "--limit", type=int, default=50, help="maximum candidates (default: 50)"
    )
    _add_flags(search, preserve_parent=True)
    search.set_defaults(func=run_search)

    verify = commands.add_parser(
        "verify", help="validate release status, coverage, references, and bindings"
    )
    _add_flags(verify, preserve_parent=True)
    verify.set_defaults(func=run_verify)

    coverage = commands.add_parser(
        "coverage", help="show released-map coverage and actual entity counts"
    )
    _add_flags(coverage, preserve_parent=True)
    coverage.set_defaults(func=run_coverage)

    def help_only(_args):
        parent.print_help()
        return 2

    parent.set_defaults(func=help_only)


def _load(args):
    try:
        return identity.ProductIdentityMap.load(args.identity_map), None
    except identity.IdentityMapError as exc:
        message = "jivo-desk product: %s" % exc
        print(message, file=sys.stderr)
        if getattr(args, "json", False):
            print(
                json.dumps(
                    {
                        "meta": {"command": "product", "valid": False},
                        "results": {"error": str(exc), "exit_code": EXIT_INVALID_MAP},
                    },
                    indent=2,
                )
            )
        return None, EXIT_INVALID_MAP


def _meta(store, action):
    return {
        "command": "product %s" % action,
        "identity_map": store.path,
        "map_sha256": store.map_sha256,
        "release_attestation": store.attestation_path,
        "attestation_sha256": store.attestation_sha256,
        "dataset_version": store.contract["dataset_version"],
        "schema_version": store.contract["schema_version"],
        "release_status": store.contract["release_status"],
        "read_only": True,
        "freshness": util.freshness(store.path),
    }


def run_resolve(args):
    store, error = _load(args)
    if error is not None:
        return error
    try:
        result = store.resolve(args.identifier)
    except identity.IdentityNotFoundError as exc:
        print("jivo-desk product resolve: %s" % exc, file=sys.stderr)
        return EXIT_NOT_FOUND
    except identity.IdentityAmbiguousError as exc:
        print("jivo-desk product resolve: %s" % exc, file=sys.stderr)
        return EXIT_AMBIGUOUS

    def human(value):
        _print_resolution(value)

    util.emit(args, result, _meta(store, "resolve"), human)
    return 0


def run_search(args):
    if args.limit < 1:
        print("jivo-desk product search: --limit must be at least 1", file=sys.stderr)
        return 2
    store, error = _load(args)
    if error is not None:
        return error
    results = store.search(args.text, args.limit)

    def human(rows):
        print("product search · %r · %d candidate(s)" % (args.text, len(rows)))
        if not rows:
            print("  no candidates found.")
            return
        table_rows = []
        for row in rows:
            context = row.get("context", {})
            qualifier = (
                context.get("platform")
                or context.get("company_code")
                or context.get("source_namespace")
                or context.get("state")
                or "-"
            )
            table_rows.append(
                [
                    row["entity_type"],
                    row["identifier"],
                    (row.get("name") or "-")[:60],
                    qualifier,
                ]
            )
        print(_table(["TYPE", "EXACT IDENTIFIER", "NAME", "CONTEXT"], table_rows))
        print("  candidates only — copy an exact identifier into 'product resolve'.")

    meta = _meta(store, "search")
    meta["query"] = args.text
    meta["candidate_only"] = True
    util.emit(args, results, meta, human)
    return 0


def run_verify(args):
    store, error = _load(args)
    if error is not None:
        return error
    result = store.verification_result()

    def human(value):
        counts = value["actual_counts"]
        print(
            "product verify · VALID · released dataset %s"
            % store.contract["dataset_version"]
        )
        print("  map: %s" % store.path)
        print(
            "  %d price SKUs · %d listings · %d JIDs · %d qualified Factory items"
            % (
                counts["price_skus"],
                counts["listings"],
                counts["jids"],
                counts["factory_items"],
            )
        )
        print(
            "  %d listing resolutions · %d Factory bindings"
            % (counts["resolutions"], counts["factory_bindings"])
        )
        if counts["products"] != counts["jids"]:
            print(
                "  %d canonical products total · %d reviewed product(s) have no JID"
                % (counts["products"], counts["products"] - counts["jids"])
            )
        print("  release gates: all clear")

    util.emit(args, result, _meta(store, "verify"), human)
    return 0


def run_coverage(args):
    store, error = _load(args)
    if error is not None:
        return error
    result = {
        "coverage": store.coverage,
        "actual_counts": store.actual_counts(),
    }

    def human(value):
        print("product coverage · dataset %s" % store.contract["dataset_version"])
        rows = []
        for name in ("price_skus", "listings", "jids", "factory_items"):
            record = value["coverage"][name]
            rows.append(
                [name, record["expected"], record["accounted"], record["unaccounted"]]
            )
        print(_table(["SCOPE", "EXPECTED", "ACCOUNTED", "UNACCOUNTED"], rows))
        print(
            "  unresolved=%d · ambiguous=%d · open-JID-conflicts=%d · unknown-Factory-collisions=%d"
            % tuple(value["coverage"][name] for name in identity._COVERAGE_ZERO_FIELDS)
        )
        print(
            "  source identity sets match: %s"
            % ("yes" if value["coverage"]["source_identity_sets_match"] else "NO")
        )
        counts = value["actual_counts"]
        if counts["products"] != counts["jids"]:
            print(
                "  canonical products: %d (%d with JID, %d reviewed without JID)"
                % (
                    counts["products"],
                    counts["jids"],
                    counts["products"] - counts["jids"],
                )
            )

    util.emit(args, result, _meta(store, "coverage"), human)
    return 0


def _print_resolution(value):
    entity_type = value["entity_type"]
    print("product resolve · %s" % entity_type)
    if entity_type == "price_sku":
        sku = value["price_sku"]
        print(
            "  %s · %s · %s"
            % (sku["price_sku_key"], sku["source_product_code"], sku["display_name"])
        )
        members = value["members"]
    elif entity_type == "product":
        product = value["product"]
        key = product.get("product_key") or product.get("jid")
        jid = product.get("jid") or "no JID"
        print("  %s · %s · %s" % (key, jid, product["canonical_name"]))
        alias = value.get("requested_alias")
        if alias:
            print(
                "  alias: %s → canonical %s (%s)"
                % (alias["alias_jid"], alias["canonical_jid"], alias["reason"])
            )
        members = value["listings"]
    elif entity_type == "listing":
        listing = value["listing"]
        print(
            "  %s · %s:%s · %s"
            % (
                listing["listing_key"],
                listing["platform"],
                listing["listing_id"],
                listing["title"],
            )
        )
        members = [value]
    else:
        item = value["factory_item"]
        print(
            "  %s · %s/%s/%s · %s"
            % (
                item["factory_item_key"],
                item["company_code"],
                item["sap_schema"],
                item["item_code"],
                item["item_name"],
            )
        )
        members = value["listings"]

    if not members:
        print("  no linked listings.")
        return
    rows = []
    for member in members:
        listing = member["listing"]
        product = member.get("product") or {}
        resolution = member.get("resolution") or {}
        bindings = resolution.get("factory_bindings", [])
        factory_keys = ", ".join(
            entry["factory_item"]["factory_item_key"] for entry in bindings
        )
        rows.append(
            [
                listing["platform"],
                listing["listing_id"],
                product.get("product_key") or product.get("jid") or "-",
                product.get("jid") or "-",
                factory_keys or "-",
            ]
        )
    print(
        _table(
            [
                "PLATFORM",
                "LISTING ID",
                "PRODUCT KEY",
                "JID",
                "QUALIFIED FACTORY KEY(S)",
            ],
            rows,
        )
    )


def _table(headers, rows):
    rendered = [[str(cell) for cell in row] for row in rows]
    widths = [len(str(value)) for value in headers]
    for row in rendered:
        for position, value in enumerate(row):
            widths[position] = max(widths[position], len(value))

    def line(row):
        return "  " + "  ".join(
            str(value).ljust(widths[position])
            for position, value in enumerate(row)
        )

    return "\n".join(
        [line(headers), line(["-" * width for width in widths])]
        + [line(row) for row in rendered]
    )
