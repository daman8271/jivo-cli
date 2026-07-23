#!/usr/bin/env python3
"""Independently verify the released JIVO product identity map.

This verifier recomputes authoritative sets from the frozen sources. It never
trusts stored coverage counters as proof.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import posixpath
from pathlib import Path
import sys
import unicodedata
import urllib.parse


ROOT = Path(__file__).resolve().parents[3]
V1 = ROOT / "CLI" / "product-identity" / "v1"
DEFAULT_MAP = V1 / "product-identity-map.json"
SOURCES_DIR = V1 / "sources"
DECISIONS_PATH = V1 / "review-decisions.json"
ATTESTATION_PATH = V1 / "release-attestation.json"

ATTESTATION_FORMAT_VERSION = "1.0.0"
ATTESTATION_CONTRACT_NAME = "jivo-product-identity-release-attestation"
VERIFIER_VERSION = "1.1.0"
# This is a release trust anchor, not a value read from the map. A new release
# must be independently verified, attested, and then deliberately pinned here.
TRUSTED_ATTESTATION_SHA256 = (
    "sha256:ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac"
)


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _strict_json_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _reject_json_constant(value):
    raise ValueError(f"non-finite JSON number {value} is not allowed")


def load_json_bytes_strict(path: Path):
    raw = path.read_bytes()
    return (
        json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        ),
        raw,
    )


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _exact_keys(value, expected: set[str], label: str, errors: list[str]):
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(
            f"{label} keys differ (missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)})"
        )
        return False
    return True


def _attested_file(attestation_path: Path, uri, label: str, errors: list[str]):
    """Resolve a normalized bundle-relative URI without allowing escape."""
    if not isinstance(uri, str) or not uri:
        errors.append(f"{label}.uri must be a non-empty string")
        return None
    if "\\" in uri or uri.startswith("/") or posixpath.normpath(uri) != uri:
        errors.append(f"{label}.uri must be a normalized relative POSIX path")
        return None
    parts = uri.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        errors.append(f"{label}.uri may not contain empty, '.' or '..' segments")
        return None
    base = attestation_path.parent.resolve()
    candidate = (base.joinpath(*parts)).resolve()
    if candidate != base and base not in candidate.parents:
        errors.append(f"{label}.uri escapes the attested release directory")
        return None
    if not candidate.is_file():
        errors.append(f"{label} is missing: {candidate}")
        return None
    return candidate


def verify_release_attestation(
    map_path: Path,
    artifact: dict,
    semantic_check_count: int,
    *,
    trusted_attestation_sha256: str = TRUSTED_ATTESTATION_SHA256,
    attestation_path: Path | None = None,
):
    """Verify the detached release trust chain; return errors and metadata.

    The trusted digest is deliberately an argument only for direct unit tests.
    The command-line interface exposes no flag or environment-variable bypass.
    """
    errors: list[str] = []
    attestation_path = (attestation_path or map_path.parent / ATTESTATION_PATH.name).resolve()
    try:
        attestation, raw = load_json_bytes_strict(attestation_path)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return [f"release attestation cannot be read: {exc}"], None

    attestation_sha256 = sha256_bytes(raw)
    if attestation_sha256 != trusted_attestation_sha256:
        errors.append(
            "release attestation SHA-256 is not the compiled trusted release "
            f"({attestation_sha256})"
        )

    if not _exact_keys(
        attestation,
        {
            "format_version",
            "contract_name",
            "dataset_version",
            "schema_version",
            "release_status",
            "map",
            "evidence_artifacts",
            "verification",
        },
        "release attestation",
        errors,
    ):
        return errors, None

    contract = artifact.get("contract", {}) if isinstance(artifact, dict) else {}
    expected_scalars = {
        "format_version": ATTESTATION_FORMAT_VERSION,
        "contract_name": ATTESTATION_CONTRACT_NAME,
        "dataset_version": contract.get("dataset_version"),
        "schema_version": contract.get("schema_version"),
        "release_status": "released",
    }
    for field, expected in expected_scalars.items():
        if attestation.get(field) != expected:
            errors.append(
                f"release attestation {field} differs: expected {expected!r}, "
                f"got {attestation.get(field)!r}"
            )

    map_record = attestation.get("map")
    if _exact_keys(map_record, {"uri", "sha256"}, "release attestation map", errors):
        attested_map_path = _attested_file(
            attestation_path, map_record.get("uri"), "release attestation map", errors
        )
        if attested_map_path is not None and attested_map_path != map_path.resolve():
            errors.append("release attestation map.uri does not identify the requested map")
        actual_map_sha256 = sha256_bytes(map_path.read_bytes())
        if map_record.get("sha256") != actual_map_sha256:
            errors.append("map SHA-256 does not match the trusted release attestation")

    source_rows = artifact.get("sources", []) if isinstance(artifact, dict) else []
    expected_sources = {
        row.get("source_id"): row
        for row in source_rows
        if isinstance(row, dict) and isinstance(row.get("source_id"), str)
    }
    attested_sources = {}
    evidence_rows = attestation.get("evidence_artifacts")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        errors.append("release attestation evidence_artifacts must be a non-empty array")
        evidence_rows = []
    for position, row in enumerate(evidence_rows):
        label = f"release attestation evidence_artifacts[{position}]"
        if not _exact_keys(row, {"source_id", "uri", "sha256"}, label, errors):
            continue
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{label}.source_id must be a non-empty string")
            continue
        if source_id in attested_sources:
            errors.append(f"release attestation repeats source_id {source_id!r}")
            continue
        attested_sources[source_id] = row
        source = expected_sources.get(source_id)
        if source is None:
            errors.append(f"release attestation has unknown source_id {source_id!r}")
        elif row.get("sha256") != source.get("content_sha256"):
            errors.append(f"attested source hash differs from map source record: {source_id}")
        evidence_path = _attested_file(attestation_path, row.get("uri"), label, errors)
        if evidence_path is not None:
            actual_sha256 = sha256_bytes(evidence_path.read_bytes())
            if actual_sha256 != row.get("sha256"):
                errors.append(f"evidence artifact hash drift: {source_id}")
    if set(attested_sources) != set(expected_sources):
        errors.append(
            "release attestation evidence source set differs from the map "
            f"(missing={sorted(set(expected_sources) - set(attested_sources))}, "
            f"unexpected={sorted(set(attested_sources) - set(expected_sources))})"
        )

    verification = attestation.get("verification")
    if _exact_keys(
        verification,
        {"verifier_version", "check_count"},
        "release attestation verification",
        errors,
    ):
        if verification.get("verifier_version") != VERIFIER_VERSION:
            errors.append("release attestation verifier_version is unsupported")
        if verification.get("check_count") != semantic_check_count:
            errors.append(
                "release attestation check_count differs from independent verification"
            )

    return errors, {
        "path": str(attestation_path),
        "sha256": attestation_sha256,
        "data": attestation,
    }


def pct(value: str) -> str:
    return urllib.parse.quote(unicodedata.normalize("NFC", str(value)), safe="-._~")


def price_key(code: str) -> str:
    return f"urn:jivo:price-sku:pricematch:{pct(code)}"


def listing_key(platform: str, listing_id: str) -> str:
    return f"urn:jivo:listing:{pct(platform)}:{pct(listing_id)}"


def factory_key(company: str, schema: str, code: str) -> str:
    return f"urn:jivo:factory:{pct(company)}:{pct(schema)}:{pct(code)}"


def iter_mapping_rows(sku_map: dict):
    for sku_name, body in sku_map["skus"].items():
        for platform, primary in body.get("platforms", {}).items():
            yield sku_name, platform, primary, "primary"
            for alt in primary.get("alt", []) or []:
                yield sku_name, platform, alt, "alternate"


class Audit:
    def __init__(self):
        self.errors: list[str] = []
        self.checks = 0

    def require(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.errors.append(message)

    def unique(self, values, label: str) -> None:
        values = list(values)
        duplicate = sorted(key for key, count in Counter(values).items() if count > 1)
        self.require(not duplicate, f"{label} contains duplicates: {duplicate[:10]}")


def evidence_ok(audit: Audit, owner: str, rows, source_ids: set[str], minimum: int = 1):
    audit.require(isinstance(rows, list) and len(rows) >= minimum, f"{owner} needs at least {minimum} evidence rows")
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows):
        audit.require(isinstance(row, dict), f"{owner} evidence[{index}] must be an object")
        if not isinstance(row, dict):
            continue
        audit.require(row.get("source_id") in source_ids, f"{owner} evidence[{index}] has unknown source_id")
        audit.require(bool(row.get("pointer")), f"{owner} evidence[{index}] lacks pointer")
        audit.require(bool(row.get("claim")), f"{owner} evidence[{index}] lacks claim")
        audit.require(bool(row.get("evidence_kind")), f"{owner} evidence[{index}] lacks evidence_kind")


def expected_factory_keys(factory_source: dict) -> set[str]:
    return {
        factory_key(row["company_code"], row["sap_schema"], row["item_code"])
        for catalog in factory_source["catalogs"]
        for row in catalog["rows"]
    }


def expected_collision_members(factory_items: list[dict]):
    grouped = defaultdict(set)
    for row in factory_items:
        grouped[row["item_code"]].add(row["factory_item_key"])
    return {code: keys for code, keys in grouped.items() if len(keys) > 1}


def check_sources(audit: Audit, artifact: dict):
    source_ids = set()
    for source in artifact.get("sources", []):
        source_id = source.get("source_id")
        source_ids.add(source_id)
        path = ROOT / source.get("uri", "")
        audit.require(path.is_file(), f"source {source_id} path is missing: {path}")
        if path.is_file():
            audit.require(sha256_bytes(path.read_bytes()) == source.get("content_sha256"), f"source hash drift: {source_id}")
        audit.require(source.get("read_only") is True, f"source {source_id} is not marked read_only")
        audit.require(source.get("pagination_complete") is True, f"source {source_id} lacks complete enumeration proof")
    audit.unique(source_ids, "source IDs")
    audit.require("pricematch-sku-map" in source_ids, "pricematch source is missing")
    audit.require("factory-catalogs" in source_ids, "Factory source is missing")
    audit.require("review-decisions" in source_ids, "review decisions source is missing")
    return source_ids


def verify_semantics(path: Path):
    audit = Audit()
    artifact, _ = load_json_bytes_strict(path)
    sku_map = load_json(SOURCES_DIR / "pricematch-sku-map.json")
    master = load_json(SOURCES_DIR / "pricematch-master-v2.json")
    registry = load_json(SOURCES_DIR / "jid-registry.json")
    factory_source = load_json(SOURCES_DIR / "factory-catalogs.json")

    contract = artifact.get("contract", {})
    audit.require(contract.get("name") == "jivo-product-identity", "wrong contract name")
    audit.require(contract.get("schema_version") == "1.0.0", "unsupported schema version")
    audit.require(contract.get("release_status") == "released", "map is not released")
    audit.require(contract.get("read_only") is True, "map contract is not read_only")
    source_ids = check_sources(audit, artifact)

    price_skus = artifact.get("price_skus", [])
    price_index = {row.get("price_sku_key"): row for row in price_skus}
    expected_prices = {price_key(code) for code in sku_map["skus"]}
    audit.unique((row.get("price_sku_key") for row in price_skus), "price_sku_key")
    audit.require(set(price_index) == expected_prices, "price SKU set does not equal source sku_map keys")
    active_expected = {price_key(code) for code in master["skus"]}
    active_actual = {key for key, row in price_index.items() if row.get("state") == "active"}
    audit.require(active_actual == active_expected, "active price SKU set does not equal master_v2")
    for key, row in price_index.items():
        audit.require(key == price_key(row.get("source_product_code", "")), f"price key does not recompute: {key}")
        evidence_ok(audit, key, row.get("evidence"), source_ids)

    expected_memberships = []
    expected_listing_members = defaultdict(list)
    for sku_name, platform, raw, role in iter_mapping_rows(sku_map):
        key = listing_key(platform, str(raw.get("id")))
        membership = (price_key(sku_name), role)
        expected_memberships.append((key, membership))
        expected_listing_members[key].append(membership)

    listings = artifact.get("listings", [])
    listing_index = {row.get("listing_key"): row for row in listings}
    audit.unique((row.get("listing_key") for row in listings), "listing_key")
    audit.require(set(listing_index) == set(expected_listing_members), "listing identity set does not equal all primary+alternate source rows")
    actual_memberships = []
    for key, row in listing_index.items():
        audit.require(key == listing_key(row.get("platform", ""), str(row.get("listing_id", ""))), f"listing key does not recompute: {key}")
        members = [(member.get("price_sku_key"), member.get("role")) for member in row.get("source_memberships", [])]
        actual_memberships.extend((key, member) for member in members)
        audit.require(Counter(members) == Counter(expected_listing_members[key]), f"listing memberships differ from source: {key}")
        audit.require(set(row.get("price_sku_keys", [])) == {member[0] for member in members}, f"listing price_sku_keys mismatch: {key}")
        audit.require(all(member[0] in price_index for member in members), f"listing references unknown price SKU: {key}")
        evidence_ok(audit, key, row.get("evidence"), source_ids)
    audit.require(Counter(actual_memberships) == Counter(expected_memberships), "334 source membership rows are not accounted exactly")

    products = artifact.get("products", [])
    product_index = {row.get("product_key"): row for row in products}
    audit.unique((row.get("product_key") for row in products), "product_key")
    source_jids = set(registry["entries"])
    map_jids = {row.get("jid") for row in products if row.get("jid")}
    audit.require(map_jids == source_jids, "JID product set differs from source registry")
    for row in products:
        evidence_ok(audit, row.get("product_key", "product"), row.get("evidence"), source_ids)

    aliases = artifact.get("jid_aliases", [])
    alias_jids = {row.get("alias_jid") for row in aliases}
    for row in aliases:
        audit.require(row.get("alias_jid") in source_jids and row.get("canonical_jid") in source_jids, "JID alias references unknown JID")
        audit.require(row.get("alias_jid") != row.get("canonical_jid"), "JID alias is self-referential")
        evidence_ok(audit, row.get("decision_id", "alias"), row.get("evidence"), source_ids)

    factory_items = artifact.get("factory_items", [])
    factory_index = {row.get("factory_item_key"): row for row in factory_items}
    audit.unique((row.get("factory_item_key") for row in factory_items), "factory_item_key")
    expected_factories = expected_factory_keys(factory_source)
    audit.require(set(factory_index) == expected_factories, "Factory item set does not equal union of complete frozen catalogs")
    for key, row in factory_index.items():
        recomputed = factory_key(row.get("company_code", ""), row.get("sap_schema", ""), row.get("item_code", ""))
        audit.require(key == recomputed, f"Factory key does not recompute: {key}")
        evidence_ok(audit, key, row.get("evidence"), source_ids)

    resolutions = artifact.get("resolutions", [])
    resolution_by_listing = defaultdict(list)
    used_factory_bindings = defaultdict(set)
    for row in resolutions:
        resolution_by_listing[row.get("listing_key")].append(row)
        audit.require(row.get("listing_key") in listing_index, "resolution references unknown listing")
        audit.require(row.get("canonical_product_key") in product_index, "resolution references unknown product")
        jid = row.get("canonical_jid")
        if jid:
            audit.require(jid in source_jids, "resolution references unknown JID")
            audit.require(jid not in alias_jids, "resolution targets an alias JID")
            audit.require(product_index[row["canonical_product_key"]].get("jid") == jid, "resolution product/JID disagree")
        audit.require(row.get("factory_mapping_state") == "verified", "released current-scope resolution is not Factory-verified")
        bindings = row.get("factory_bindings", [])
        audit.require(bool(bindings), "verified resolution has no Factory binding")
        primaries_by_scope = defaultdict(int)
        for binding in bindings:
            fkey = binding.get("factory_item_key")
            audit.require(fkey in factory_index, "binding references unknown Factory item")
            if fkey in factory_index and binding.get("primary_for_scope"):
                primaries_by_scope[factory_index[fkey]["factory_scope_key"]] += 1
            if fkey:
                used_factory_bindings[fkey].add(row.get("listing_key"))
            evidence_ok(audit, f"binding {row.get('listing_key')}->{fkey}", binding.get("evidence"), source_ids, 2)
            kinds = {ev.get("evidence_kind") for ev in binding.get("evidence", []) if isinstance(ev, dict)}
            audit.require("exact_listing_identity" in kinds, "binding lacks exact listing identity evidence")
            audit.require("qualified_factory_record" in kinds, "binding lacks qualified Factory record evidence")
        audit.require(all(count <= 1 for count in primaries_by_scope.values()), "resolution has multiple primary bindings in one Factory scope")
    audit.require(set(resolution_by_listing) == set(listing_index), "not every distinct listing has a resolution")
    audit.require(all(len(rows) == 1 for rows in resolution_by_listing.values()), "a listing has multiple resolutions")

    accounting = artifact.get("factory_item_accounting", [])
    accounting_index = {row.get("factory_item_key"): row for row in accounting}
    audit.unique((row.get("factory_item_key") for row in accounting), "Factory accounting key")
    audit.require(set(accounting_index) == set(factory_index), "Factory accounting is not a 1:1 item bijection")
    for fkey, row in accounting_index.items():
        expected_members = used_factory_bindings.get(fkey, set())
        actual_members = set(row.get("listing_keys", []))
        audit.require(actual_members == expected_members, f"Factory accounting listing set differs from resolutions: {fkey}")
        if expected_members:
            audit.require(row.get("disposition") == "mapped", f"used Factory item is not disposition=mapped: {fkey}")
        else:
            audit.require(row.get("disposition") != "mapped", f"unused Factory item is falsely disposition=mapped: {fkey}")
        evidence_ok(audit, f"accounting {fkey}", row.get("evidence"), source_ids)

    collision_rows = artifact.get("factory_code_collisions", [])
    collision_index = {row.get("item_code"): row for row in collision_rows}
    audit.unique((row.get("item_code") for row in collision_rows), "Factory collision code")
    expected_collisions = expected_collision_members(factory_items)
    audit.require(set(collision_index) == set(expected_collisions), "collision code set does not equal every reused bare Factory code")
    for code, expected_keys in expected_collisions.items():
        row = collision_index.get(code, {})
        audit.require(set(row.get("factory_item_keys", [])) == expected_keys, f"collision members incomplete for {code}")
        audit.require(row.get("physical_relation") in {"same_offer", "different_offer", "mixed"}, f"collision {code} is unknown")
        evidence_ok(audit, f"collision {code}", row.get("evidence"), source_ids, 2)

    conflicts = artifact.get("jid_conflicts", [])
    blocking = 0
    for row in conflicts:
        audit.require(set(row.get("involved_jids", [])) <= source_jids, "JID conflict references unknown JID")
        audit.require(set(row.get("involved_listing_keys", [])) <= set(listing_index), "JID conflict references unknown listing")
        evidence_ok(audit, row.get("conflict_id", "conflict"), row.get("evidence"), source_ids)
        if row.get("blocking"):
            blocking += 1

    # Golden hazard regressions.
    hazard_315 = collision_index.get("FG0000315", {})
    audit.require(len(hazard_315.get("factory_item_keys", [])) == 3, "FG0000315 three-company collision is missing")
    shikanji = resolution_by_listing.get(listing_key("amazon", "B0GZ7PXVF8"), [{}])[0]
    shikanji_bindings = {row.get("factory_item_key") for row in shikanji.get("factory_bindings", [])}
    audit.require(factory_key("JIVO_BEVERAGES", "JIVO_BEVERAGES_HANADB", "FG0000315") in shikanji_bindings, "Shikanji lacks exact Beverages FG0000315 binding")
    audit.require(factory_key("JIVO_MART", "JIVO_MART_HANADB", "FG0000315") not in shikanji_bindings, "Shikanji was incorrectly joined to Mart FG0000315")
    sano_extra = resolution_by_listing.get(listing_key("amazon", "B0CCVF1XVS"), [{}])[0]
    sano_classic = resolution_by_listing.get(listing_key("flipkart", "EDOGVEF33GYXKHEW"), [{}])[0]
    audit.require(sano_extra.get("canonical_product_key") != sano_classic.get("canonical_product_key"), "Sano Extra Light and Classic were not split")
    audit.require(sano_extra.get("canonical_jid") is None, "Sano Extra Light was forced into the wrong JID")

    coverage = artifact.get("coverage", {})
    recomputed = {
        "price_skus": {"expected": len(expected_prices), "accounted": len(price_index), "unaccounted": len(expected_prices - set(price_index))},
        "active_price_skus": {"expected": len(active_expected), "accounted": len(active_actual), "unaccounted": len(active_expected - active_actual)},
        "source_mapping_rows": {"expected": len(expected_memberships), "accounted": len(actual_memberships), "unaccounted": max(0, len(expected_memberships) - len(actual_memberships))},
        "listings": {"expected": len(expected_listing_members), "accounted": len(resolution_by_listing), "unaccounted": len(set(expected_listing_members) - set(resolution_by_listing))},
        "jids": {"expected": len(source_jids), "accounted": len(map_jids), "unaccounted": len(source_jids - map_jids)},
        "factory_items": {"expected": len(expected_factories), "accounted": len(accounting_index), "unaccounted": len(expected_factories - set(accounting_index))},
        "unresolved_listings": len(set(listing_index) - set(resolution_by_listing)),
        "unresolved_active_listings": len({key for key, row in listing_index.items() if row.get("state") == "active"} - set(resolution_by_listing)),
        "ambiguous_listings": 0,
        "open_jid_conflicts": blocking,
        "unknown_factory_collisions": sum(1 for row in collision_rows if row.get("physical_relation") == "unknown"),
        "source_identity_sets_match": True,
        "queue_entries_outside_current_master": len(artifact.get("observed_queue_accounting", [])),
    }
    audit.require(coverage == recomputed, "stored coverage differs from independently recomputed coverage")
    audit.require(all(recomputed[name]["unaccounted"] == 0 for name in ("price_skus", "active_price_skus", "source_mapping_rows", "listings", "jids", "factory_items")), "one or more coverage sets are unaccounted")
    audit.require(recomputed["unresolved_listings"] == 0, "unresolved listings remain")
    audit.require(recomputed["open_jid_conflicts"] == 0, "blocking JID conflicts remain")

    return audit, artifact


def verify(path: Path):
    """Verify both map semantics and the detached, pinned release trust chain."""
    audit, artifact = verify_semantics(path)
    attestation_errors, attestation = verify_release_attestation(
        path,
        artifact,
        audit.checks,
    )
    audit.errors.extend(attestation_errors)
    return audit, artifact, attestation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default=str(DEFAULT_MAP))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.map).resolve()
    try:
        audit, artifact, attestation = verify(path)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        result = {"valid": False, "checks": 0, "errors": [str(exc)], "map": str(path)}
        print(json.dumps(result) if args.json else f"INVALID: {exc}")
        return 6
    result = {
        "valid": not audit.errors,
        "checks": audit.checks,
        "errors": audit.errors,
        "map": str(path),
        "dataset_version": artifact.get("contract", {}).get("dataset_version"),
        "map_sha256": sha256_bytes(path.read_bytes()),
        "attestation": (
            {
                "path": attestation["path"],
                "sha256": attestation["sha256"],
            }
            if attestation
            else None
        ),
        "coverage": artifact.get("coverage"),
    }
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif audit.errors:
        print(f"INVALID ({len(audit.errors)} errors, {audit.checks} checks)")
        for error in audit.errors:
            print(f"- {error}")
    else:
        print(f"VALID {result['dataset_version']} ({audit.checks} checks, {result['map_sha256']})")
    return 0 if not audit.errors else 6


if __name__ == "__main__":
    sys.exit(main())
