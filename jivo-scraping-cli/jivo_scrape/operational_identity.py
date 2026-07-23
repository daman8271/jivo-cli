"""Shared exact-identity setup for operational jivo-desk commands."""

import shlex
import sys

from jivo_scrape import identity


EXIT_INVALID_MAP = 6
EXIT_IDENTIFIER_REQUIRED = 2


def add_identity_map_flag(parser):
    parser.add_argument(
        "--identity-map",
        help="shared product map (default: $JIVO_PRODUCT_IDENTITY_MAP, then repo discovery)",
    )


def _search_command(identifier):
    return "jivo-desk product search %s" % shlex.quote(str(identifier))


def prepare(args, command, identifier=None):
    """Load the released map and optionally resolve an operational identifier.

    Returns ``(store, targets, meta, exit_code)``. ``targets`` is ``None`` for
    catalogue-wide commands and otherwise a set of exact platform/listing-ID
    tuples. Names never enter this path.
    """
    try:
        store = identity.ProductIdentityMap.load(
            getattr(args, "identity_map", None)
        )
    except identity.IdentityMapError as exc:
        print("jivo-desk %s: %s" % (command, exc), file=sys.stderr)
        return None, None, None, EXIT_INVALID_MAP

    targets = None
    resolved = None
    if identifier is not None:
        try:
            targets, resolved = store.listing_targets(identifier)
        except identity.IdentityNotFoundError:
            print(
                "jivo-desk %s: %r is not an exact product identifier; run: %s"
                % (command, identifier, _search_command(identifier)),
                file=sys.stderr,
            )
            return None, None, None, EXIT_IDENTIFIER_REQUIRED
        except identity.IdentityAmbiguousError as exc:
            print(
                "jivo-desk %s: %s; use one of the full keys, or run: %s"
                % (command, exc, _search_command(identifier)),
                file=sys.stderr,
            )
            return None, None, None, EXIT_IDENTIFIER_REQUIRED

    meta = {
        "map_path": store.path,
        "dataset_version": store.contract["dataset_version"],
        "map_sha256": store.map_sha256,
        "attestation_path": store.attestation_path,
        "attestation_sha256": store.attestation_sha256,
        "release_status": store.contract["release_status"],
        "join": "exact platform + listing_id",
        "name_join": False,
    }
    if identifier is not None:
        meta.update(
            {
                "requested_identifier": identifier,
                "resolved_entity_type": resolved["entity_type"],
                "target_listing_count": len(targets),
            }
        )
    return store, targets, meta, None


def summarize_states(rows):
    counts = {"mapped": 0, "unmapped": 0, "missing_listing_id": 0}
    for row in rows:
        state = row.get("identity_state")
        counts[state] = counts.get(state, 0) + 1
    return counts
