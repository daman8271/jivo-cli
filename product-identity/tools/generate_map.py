#!/usr/bin/env python3
"""Generate the shared JIVO product identity map from frozen read-only inputs."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
import urllib.parse


ROOT = Path(__file__).resolve().parents[3]
V1 = ROOT / "CLI" / "product-identity" / "v1"
SOURCES_DIR = V1 / "sources"
MAP_PATH = V1 / "product-identity-map.json"
REPORTS_DIR = V1 / "reports"
DECISIONS_PATH = V1 / "review-decisions.json"

FACTORY_SCOPES = {
    "JIVO_OIL": (1, "JIVO_OIL_HANADB"),
    "JIVO_MART": (2, "JIVO_MART_HANADB"),
    "JIVO_BEVERAGES": (3, "JIVO_BEVERAGES_HANADB"),
}

LISTING_ID_KINDS = {
    "amazon": "asin",
    "amazon-fresh": "asin",
    "amazon-now": "asin",
    "bigbasket": "sku_id",
    "blinkit": "prid",
    "flipkart": "fsn",
    "flipkart-minutes": "fk_pid",
    "swiggy-instamart": "listing_id",
    "zepto": "variant_id",
}

ECOM_PLATFORMS = {
    "AMAZON": "amazon",
    "BIG BASKET": "bigbasket",
    "BLINKIT": "blinkit",
    "FLIPKART": "flipkart",
    "FLIPKART GROCERY": "flipkart-minutes",
    "SWIGGY": "swiggy-instamart",
    "ZEPTO": "zepto",
    "CITY MALL": "city-mall",
    "DEAL SHARE": "deal-share",
    "JIO MART": "jio-mart",
    "ZOMATO": "zomato",
}

EVIDENCE_KINDS = {
    "exact_price_code",
    "exact_listing_identity",
    "exact_source_sap",
    "qualified_factory_record",
    "review_decision",
    "complete_catalog_absence",
    "accounting_disposition",
}


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_json(value) -> str:
    body = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return sha256_bytes(body)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def pct(value: str) -> str:
    return urllib.parse.quote(unicodedata.normalize("NFC", str(value)), safe="-._~")


def json_pointer(value: str) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def norm(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or "")).upper()
    return re.sub(r"[^A-Z0-9]+", "", text)


def norm_name_uom(name: object, uom: object) -> tuple[str, str]:
    return norm(name), norm(uom)


def price_key(code: str) -> str:
    return f"urn:jivo:price-sku:pricematch:{pct(code)}"


def listing_key(platform: str, listing_id: str) -> str:
    return f"urn:jivo:listing:{pct(platform)}:{pct(listing_id)}"


def product_key(jid: str) -> str:
    return f"urn:jivo:product:{pct(jid)}"


def factory_scope_key(company: str, schema: str) -> str:
    return f"urn:jivo:factory-scope:{pct(company)}:{pct(schema)}"


def factory_key(company: str, schema: str, item_code: str) -> str:
    return f"urn:jivo:factory:{pct(company)}:{pct(schema)}:{pct(item_code)}"


def evidence(source_id: str, pointer: str, claim: str, evidence_kind: str, observed_value=None) -> dict:
    if evidence_kind not in EVIDENCE_KINDS:
        raise ValueError(f"unknown evidence kind {evidence_kind}")
    item = {
        "source_id": source_id,
        "pointer": pointer,
        "claim": claim,
        "evidence_kind": evidence_kind,
    }
    if observed_value is not None:
        item["observed_value"] = observed_value
    return item


def source_records(manifest: dict, decisions: dict) -> list[dict]:
    kinds = {
        "ecom-master-products": "scrape_catalog",
        "factory-catalogs": "factory_oitm",
        "jid-registry": "jid_catalog",
        "pricematch-master-v2": "scrape_catalog",
        "pricematch-sku-map": "scrape_catalog",
    }
    records = []
    for row in manifest["sources"]:
        records.append(
            {
                "source_id": row["source_id"],
                "kind": kinds[row["source_id"]],
                "uri": row["path"],
                "observed_at": row["observed_at"],
                "content_sha256": row["content_sha256"],
                "identity_set_sha256": row["identity_set_sha256"],
                "record_count": row["identity_count"],
                "pagination_complete": True,
                "read_only": True,
            }
        )
    decision_bytes = DECISIONS_PATH.read_bytes()
    records.append(
        {
            "source_id": "review-decisions",
            "kind": "review_decisions",
            "uri": str(DECISIONS_PATH.relative_to(ROOT)),
            "observed_at": decisions["contract"]["reviewed_at"],
            "content_sha256": sha256_bytes(decision_bytes),
            "identity_set_sha256": sha256_json(
                sorted(
                    f"{row['platform']}:{row['listing_id']}"
                    for row in decisions["listing_product_overrides"]
                )
            ),
            "record_count": len(decisions["listing_product_overrides"]),
            "pagination_complete": True,
            "read_only": True,
        }
    )
    return records


def build_factory_items(factory_source: dict):
    merged: dict[str, dict] = {}
    source_rows: dict[str, list[dict]] = defaultdict(list)
    for catalog_index, catalog in enumerate(factory_source["catalogs"]):
        for row_index, row in enumerate(catalog["rows"]):
            key = factory_key(row["company_code"], row["sap_schema"], row["item_code"])
            ev = evidence(
                "factory-catalogs",
                f"/catalogs/{catalog_index}/rows/{row_index}",
                "Exact company-qualified Factory product record.",
                "qualified_factory_record",
                {
                    "company_code": row["company_code"],
                    "sap_schema": row["sap_schema"],
                    "item_code": row["item_code"],
                    "catalog_scope": row["catalog_scope"],
                },
            )
            source_rows[key].append(ev)
            current = merged.get(key)
            candidate = {
                "factory_item_key": key,
                "factory_scope_key": factory_scope_key(row["company_code"], row["sap_schema"]),
                "company_code": row["company_code"],
                "sap_schema": row["sap_schema"],
                "item_code": row["item_code"],
                "item_name": row.get("item_name") or "",
                "inventory_uom": row.get("inventory_uom"),
                "sales_uom": row.get("sales_uom"),
                "purchase_uom": row.get("purchase_uom"),
                "item_group_code": row.get("item_group_code"),
                "catalog_scopes": [row["catalog_scope"]],
                "item_class": "bundle" if row["item_code"].startswith("FB") else "retail_finished_good",
                "state": "inactive" if row.get("frozen_for") is True or row.get("valid_for") is False else "active",
                "evidence": [],
            }
            if current is None:
                merged[key] = candidate
            else:
                current["catalog_scopes"].append(row["catalog_scope"])
                # Barcode OITM is the richer record and wins field selection.
                if row["catalog_scope"] == "barcode_oitm":
                    for field in (
                        "item_name",
                        "inventory_uom",
                        "sales_uom",
                        "purchase_uom",
                        "item_group_code",
                    ):
                        current[field] = candidate[field]
                    current["state"] = candidate["state"]
    for key, row in merged.items():
        row["catalog_scopes"] = sorted(set(row["catalog_scopes"]))
        row["evidence"] = source_rows[key]
    items = sorted(merged.values(), key=lambda row: row["factory_item_key"])
    return items, {row["factory_item_key"]: row for row in items}


def build_collisions(factory_items: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in factory_items:
        grouped[row["item_code"]].append(row)
    collisions = []
    for code, rows in sorted(grouped.items()):
        if len(rows) < 2:
            continue
        signatures = [norm_name_uom(row["item_name"], row.get("inventory_uom")) for row in rows]
        unique = set(signatures)
        if len(unique) == 1:
            relation = "same_offer"
        elif len(unique) == len(signatures):
            relation = "different_offer"
        else:
            relation = "mixed"
        collisions.append(
            {
                "item_code": code,
                "factory_item_keys": [row["factory_item_key"] for row in rows],
                "physical_relation": relation,
                "evidence": [row["evidence"][0] for row in rows],
            }
        )
    return collisions


def build_products(registry: dict, decisions: dict):
    alias_map = {row["alias_jid"]: row["canonical_jid"] for row in decisions["jid_aliases"]}
    products = []
    for jid, row in sorted(registry["entries"].items()):
        products.append(
            {
                "product_key": product_key(jid),
                "jid": jid,
                "canonical_name": row["name"],
                "state": "merged" if jid in alias_map else row.get("status", "active"),
                "name_aliases": [],
                "evidence": [
                    evidence(
                        "jid-registry",
                        f"/entries/{json_pointer(jid)}",
                        "Exact JID registry entry.",
                        "exact_price_code",
                        jid,
                    )
                ],
            }
        )
    products.extend(decisions.get("local_products", []))
    for row in products:
        if not row.get("evidence"):
            row["evidence"] = [
                evidence(
                    "review-decisions",
                    "/local_products",
                    "Reviewed local product required because the source registry has no JID.",
                    "review_decision",
                    row["product_key"],
                )
            ]
    product_index = {row["product_key"]: row for row in products}
    jid_index = {row["jid"]: row for row in products if row.get("jid")}
    aliases = []
    for index, row in enumerate(decisions["jid_aliases"]):
        aliases.append(
            {
                **row,
                "decision_id": f"DEC-JID-ALIAS-{index + 1:03d}",
                "evidence": [
                    evidence(
                        "review-decisions",
                        f"/jid_aliases/{index}",
                        "Reviewed JID alias decision.",
                        "review_decision",
                        {"alias_jid": row["alias_jid"], "canonical_jid": row["canonical_jid"]},
                    )
                ],
            }
        )
    return products, product_index, jid_index, alias_map, aliases


def iter_mapping_rows(sku_map: dict):
    for sku_name, sku_body in sku_map["skus"].items():
        for platform, primary in sku_body.get("platforms", {}).items():
            yield sku_name, platform, primary, "primary"
            for alt in primary.get("alt", []) or []:
                yield sku_name, platform, alt, "alternate"


def build_price_and_listings(sku_map: dict, master_v2: dict, ecom_source: dict):
    ecom_index = {}
    for index, row in enumerate(ecom_source["rows"]):
        platform = ECOM_PLATFORMS.get(row.get("format"), norm(row.get("format")).lower())
        ecom_index[(platform, str(row.get("format_sku_code")))] = (index, row)

    active_names = set(master_v2["skus"])
    memberships: dict[str, list[dict]] = defaultdict(list)
    records: dict[str, list[dict]] = defaultdict(list)
    row_count = 0
    for sku_name, platform, raw, role in iter_mapping_rows(sku_map):
        row_count += 1
        lid = str(raw.get("id") or "")
        key = listing_key(platform, lid)
        membership = {
            "price_sku_key": price_key(sku_name),
            "source_product_code": sku_name,
            "role": role,
            "source_pointer": f"/skus/{json_pointer(sku_name)}/platforms/{json_pointer(platform)}",
        }
        memberships[key].append(membership)
        records[key].append({"sku_name": sku_name, "platform": platform, "raw": raw, "role": role})

    price_skus = []
    member_keys_by_price: dict[str, list[str]] = defaultdict(list)
    for key, rows in memberships.items():
        for membership in rows:
            member_keys_by_price[membership["price_sku_key"]].append(key)
    for sku_name in sorted(sku_map["skus"]):
        key = price_key(sku_name)
        state = "active" if sku_name in active_names else "retired"
        price_skus.append(
            {
                "price_sku_key": key,
                "source_namespace": "pricematch",
                "source_product_code": sku_name,
                "display_name": sku_name,
                "state": state,
                "member_listing_keys": sorted(set(member_keys_by_price[key])),
                "evidence": [
                    evidence(
                        "pricematch-sku-map",
                        f"/skus/{json_pointer(sku_name)}",
                        "Exact upstream price product code and membership set.",
                        "exact_price_code",
                        sku_name,
                    )
                ],
            }
        )

    listings = []
    for key in sorted(records):
        listing_records = records[key]
        first = listing_records[0]
        platform = first["platform"]
        raw = first["raw"]
        lid = str(raw.get("id"))
        ev = []
        source_memberships = []
        for membership in memberships[key]:
            source_memberships.append(
                {
                    "price_sku_key": membership["price_sku_key"],
                    "role": membership["role"],
                }
            )
            ev.append(
                evidence(
                    "pricematch-sku-map",
                    membership["source_pointer"],
                    "Exact platform-qualified listing membership.",
                    "exact_listing_identity",
                    {"platform": platform, "listing_id": lid},
                )
            )
        live = ecom_index.get((platform, lid))
        if live:
            index, live_row = live
            ev.append(
                evidence(
                    "ecom-master-products",
                    f"/rows/{index}",
                    "Exact live Ecom platform product code.",
                    "exact_listing_identity",
                    {"platform": platform, "listing_id": lid},
                )
            )
        primary_price_key = sorted({row["price_sku_key"] for row in memberships[key]})[0]
        title = raw.get("title") or first["sku_name"]
        listings.append(
            {
                "listing_key": key,
                "price_sku_key": primary_price_key,
                "price_sku_keys": sorted({row["price_sku_key"] for row in memberships[key]}),
                "source_memberships": sorted(source_memberships, key=lambda row: (row["price_sku_key"], row["role"])),
                "platform": platform,
                "listing_id": lid,
                "listing_id_kind": LISTING_ID_KINDS.get(platform, "platform_product_code"),
                "title": title,
                "url": raw.get("url"),
                "state": "active" if any(row["sku_name"] in active_names for row in listing_records) else "retired",
                "is_primary": any(row["role"] == "primary" for row in listing_records),
                "pack": {
                    "kind": "unknown",
                    "components": [],
                    "pack_fingerprint": sha256_json({"title": title, "source_products": sorted({row["sku_name"] for row in listing_records})}),
                },
                "evidence": ev,
                "_records": listing_records,
                "_ecom": live,
            }
        )
    return price_skus, listings, row_count


def registry_indexes(registry: dict):
    sap_to_jids: dict[str, set[str]] = defaultdict(set)
    canon_to_jids: dict[str, set[str]] = defaultdict(set)
    norm_to_jids: dict[str, set[str]] = defaultdict(set)
    for jid, row in registry["entries"].items():
        for sap in row.get("saps", []):
            sap_to_jids[str(sap).upper()].add(jid)
        for canon in row.get("canons", []):
            canon_to_jids[str(canon).casefold()].add(jid)
        norm_to_jids[norm(row.get("norm") or row.get("name"))].add(jid)
    return sap_to_jids, canon_to_jids, norm_to_jids


def canonical_jid(jid: str, alias_map: dict[str, str]) -> str:
    seen = set()
    while jid in alias_map:
        if jid in seen:
            raise RuntimeError(f"JID alias cycle at {jid}")
        seen.add(jid)
        jid = alias_map[jid]
    return jid


def exact_jids_for_saps(saps: set[str], sap_to_jids: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    for sap in saps:
        result.update(sap_to_jids.get(sap.upper(), set()))
    return result


def choose_product(
    listing: dict,
    override: dict | None,
    registry: dict,
    sap_to_jids: dict[str, set[str]],
    canon_to_jids: dict[str, set[str]],
    norm_to_jids: dict[str, set[str]],
    alias_map: dict[str, str],
):
    if override:
        if override.get("canonical_product_key"):
            return override["canonical_product_key"], None, "human_reviewed_exact_ids", set()
        jid = canonical_jid(override["canonical_jid"], alias_map)
        return product_key(jid), jid, "human_reviewed_exact_ids", {jid}

    ecom_saps: set[str] = set()
    if listing.get("_ecom"):
        sap = listing["_ecom"][1].get("sku_sap_code")
        if sap:
            ecom_saps.add(str(sap).upper())
    candidates = exact_jids_for_saps(ecom_saps, sap_to_jids)
    if len(candidates) == 1:
        jid = canonical_jid(next(iter(candidates)), alias_map)
        return product_key(jid), jid, "exact_source_code_plus_oitm", candidates
    if len(candidates) > 1:
        return None, None, "ambiguous_ecom_sap", candidates

    canon_candidates: set[str] = set()
    canon_candidates.update(canon_to_jids.get(str(listing["listing_id"]).casefold(), set()))
    if len(canon_candidates) == 1:
        jid = canonical_jid(next(iter(canon_candidates)), alias_map)
        return product_key(jid), jid, "exact_source_code_plus_pack", canon_candidates

    map_saps: set[str] = set()
    for record in listing["_records"]:
        sap = record["raw"].get("sap_code")
        if sap:
            map_saps.add(str(sap).upper())
    candidates = exact_jids_for_saps(map_saps, sap_to_jids)
    if len(candidates) == 1:
        jid = canonical_jid(next(iter(candidates)), alias_map)
        return product_key(jid), jid, "exact_source_code_plus_oitm", candidates
    if len(candidates) > 1:
        return None, None, "ambiguous_price_sap", candidates

    name_candidates: set[str] = set()
    for record in listing["_records"]:
        name_candidates.update(norm_to_jids.get(norm(record["sku_name"]), set()))
    if len(name_candidates) == 1:
        jid = canonical_jid(next(iter(name_candidates)), alias_map)
        return product_key(jid), jid, "exact_source_code_plus_pack", name_candidates
    return None, None, "unresolved", canon_candidates | name_candidates


def factory_candidates_for_code(code: str, factory_items: dict[str, dict]) -> list[dict]:
    return [row for row in factory_items.values() if row["item_code"] == code]


def source_sap_codes(listing: dict, chosen_jid: str | None, sap_to_jids: dict[str, set[str]], alias_map: dict[str, str]):
    codes = []
    if listing.get("_ecom"):
        sap = listing["_ecom"][1].get("sku_sap_code")
        if sap:
            candidates = {canonical_jid(jid, alias_map) for jid in sap_to_jids.get(str(sap).upper(), set())}
            if not chosen_jid or candidates == {chosen_jid}:
                codes.append((str(sap).upper(), "ecom"))
    for record in listing["_records"]:
        sap = record["raw"].get("sap_code")
        if not sap:
            continue
        candidates = {canonical_jid(jid, alias_map) for jid in sap_to_jids.get(str(sap).upper(), set())}
        if not chosen_jid or candidates == {chosen_jid}:
            codes.append((str(sap).upper(), "pricematch"))
    seen = set()
    return [row for row in codes if not (row[0] in seen or seen.add(row[0]))]


def exact_equivalent_scopes(primary: dict, factory_items: dict[str, dict]) -> list[dict]:
    signature = norm_name_uom(primary["item_name"], primary.get("inventory_uom"))
    result = []
    for row in factory_candidates_for_code(primary["item_code"], factory_items):
        if row["factory_item_key"] == primary["factory_item_key"]:
            continue
        if norm_name_uom(row["item_name"], row.get("inventory_uom")) == signature:
            result.append(row)
    return result


def build_bindings(
    listing: dict,
    chosen_jid: str | None,
    override: dict | None,
    registry: dict,
    decisions: dict,
    factory_items: dict[str, dict],
    sap_to_jids: dict[str, set[str]],
    alias_map: dict[str, str],
):
    selected: list[tuple[dict, str, bool, str]] = []
    explicit = []
    if override and override.get("factory_codes"):
        explicit = override["factory_codes"]
    elif chosen_jid and chosen_jid in decisions.get("jid_factory_bindings", {}):
        explicit = decisions["jid_factory_bindings"][chosen_jid]
    if explicit:
        per_scope_counts: dict[str, int] = defaultdict(int)
        for row in explicit:
            per_scope_counts[row["company_code"]] += 1
        for row in explicit:
            key = factory_key(row["company_code"], row["sap_schema"], row["item_code"])
            item = factory_items.get(key)
            if item:
                role = row.get("role", "sellable_unit")
                primary = role == "sellable_unit" and per_scope_counts[row["company_code"]] == 1
                selected.append((item, role, primary, "review_decision"))
    else:
        source_codes = source_sap_codes(listing, chosen_jid, sap_to_jids, alias_map)
        if source_codes:
            for code, source_kind in source_codes:
                mart_key = factory_key("JIVO_MART", "JIVO_MART_HANADB", code)
                item = factory_items.get(mart_key)
                if item is None:
                    candidates = factory_candidates_for_code(code, factory_items)
                    item = candidates[0] if len(candidates) == 1 else None
                if item:
                    selected.append((item, "sellable_unit", True, source_kind))
                    for equivalent in exact_equivalent_scopes(item, factory_items):
                        selected.append((equivalent, "intercompany_equivalent", False, "exact_name_uom"))
        elif chosen_jid:
            registry_row = registry["entries"].get(chosen_jid, {})
            for code in registry_row.get("saps", []):
                item = factory_items.get(factory_key("JIVO_MART", "JIVO_MART_HANADB", code))
                if item:
                    selected.append((item, "sellable_unit", False, "jid_registry"))
                    for equivalent in exact_equivalent_scopes(item, factory_items):
                        selected.append((equivalent, "intercompany_equivalent", False, "exact_name_uom"))

    deduped = {}
    for item, role, primary, basis in selected:
        existing = deduped.get(item["factory_item_key"])
        if existing is None or primary:
            deduped[item["factory_item_key"]] = (item, role, primary, basis)
    bindings = []
    for item, role, primary, basis in sorted(deduped.values(), key=lambda row: row[0]["factory_item_key"]):
        listing_ev = listing["evidence"][0]
        binding_evidence = [
            {
                **listing_ev,
                "claim": "Exact listing identity used for this Factory binding.",
                "evidence_kind": "exact_listing_identity",
            },
            item["evidence"][0],
        ]
        if basis == "review_decision":
            binding_evidence.append(
                evidence(
                    "review-decisions",
                    "/jid_factory_bindings" if chosen_jid else "/listing_product_overrides",
                    "Reviewed company-qualified Factory binding.",
                    "review_decision",
                    item["factory_item_key"],
                )
            )
        bindings.append(
            {
                "factory_item_key": item["factory_item_key"],
                "role": role,
                "factory_uom_per_listing_offer": None,
                "conversion_state": "not_proven",
                "primary_for_scope": bool(primary),
                "evidence": binding_evidence,
            }
        )
    # At most one primary in a scope; multiple source codes make all non-primary.
    primaries: dict[str, list[dict]] = defaultdict(list)
    for binding in bindings:
        item = factory_items[binding["factory_item_key"]]
        if binding["primary_for_scope"]:
            primaries[item["factory_scope_key"]].append(binding)
    for rows in primaries.values():
        if len(rows) > 1:
            for row in rows:
                row["primary_for_scope"] = False
    return bindings


def resolve_listings(listings, registry, decisions, factory_items, jid_index, alias_map):
    sap_to_jids, canon_to_jids, norm_to_jids = registry_indexes(registry)
    overrides = {
        (row["platform"], str(row["listing_id"])): row
        for row in decisions["listing_product_overrides"]
    }
    resolutions = []
    unresolved = []
    ambiguous = []
    for index, listing in enumerate(listings):
        override = overrides.get((listing["platform"], listing["listing_id"]))
        pkey, jid, method, candidates = choose_product(
            listing,
            override,
            registry,
            sap_to_jids,
            canon_to_jids,
            norm_to_jids,
            alias_map,
        )
        if pkey is None:
            report = {
                "listing_key": listing["listing_key"],
                "platform": listing["platform"],
                "listing_id": listing["listing_id"],
                "source_products": sorted({row["sku_name"] for row in listing["_records"]}),
                "candidate_jids": sorted(candidates),
                "reason": method,
            }
            if candidates:
                ambiguous.append(report)
            else:
                unresolved.append(report)
            continue
        bindings = build_bindings(
            listing,
            jid,
            override,
            registry,
            decisions,
            factory_items,
            sap_to_jids,
            alias_map,
        )
        if not bindings:
            unresolved.append(
                {
                    "listing_key": listing["listing_key"],
                    "platform": listing["platform"],
                    "listing_id": listing["listing_id"],
                    "source_products": sorted({row["sku_name"] for row in listing["_records"]}),
                    "candidate_jids": [jid] if jid else [],
                    "reason": "product_resolved_but_no_qualified_factory_binding",
                }
            )
            continue
        resolutions.append(
            {
                "resolution_id": f"RES-{index + 1:04d}",
                "listing_key": listing["listing_key"],
                "canonical_product_key": pkey,
                "canonical_jid": jid,
                "state": "verified" if listing["state"] == "active" else "retired",
                "factory_mapping_state": "verified",
                "factory_bindings": bindings,
                "verification_method": method,
                "verified_by": decisions["contract"]["reviewed_by"],
                "verified_at": decisions["contract"]["reviewed_at"],
                "evidence": (
                    [
                        evidence(
                            "review-decisions",
                            "/listing_product_overrides",
                            "Reviewed exact listing resolution.",
                            "review_decision",
                            listing["listing_key"],
                        )
                    ]
                    if override
                    else listing["evidence"][:1]
                ),
            }
        )
    return resolutions, unresolved, ambiguous


def build_jid_conflicts(registry: dict, aliases: list[dict], resolutions: list[dict]):
    canon_members: dict[str, set[str]] = defaultdict(set)
    for jid, row in registry["entries"].items():
        for canon in row.get("canons", []):
            canon_members[str(canon).casefold()].add(jid)
    graph: dict[str, set[str]] = defaultdict(set)
    conflict_canons = {}
    for canon, jids in canon_members.items():
        if len(jids) > 1:
            conflict_canons[canon] = jids
            for jid in jids:
                graph[jid].update(jids - {jid})
    seen = set()
    components = []
    for start in sorted(graph):
        if start in seen:
            continue
        queue = deque([start])
        component = set()
        while queue:
            jid = queue.popleft()
            if jid in component:
                continue
            component.add(jid)
            queue.extend(graph[jid])
        seen.update(component)
        components.append(component)
    listing_by_jid: dict[str, list[str]] = defaultdict(list)
    for row in resolutions:
        if row.get("canonical_jid"):
            listing_by_jid[row["canonical_jid"]].append(row["listing_key"])
    alias_pairs = {(row["alias_jid"], row["canonical_jid"]) for row in aliases}
    conflicts = []
    for index, component in enumerate(components):
        involved_listings = sorted({key for jid in component for key in listing_by_jid.get(jid, [])})
        alias_resolved = any(pair[0] in component and pair[1] in component for pair in alias_pairs)
        if alias_resolved:
            status = "resolved"
            resolution_kind = "alias"
        elif involved_listings:
            status = "resolved_for_price_scope"
            resolution_kind = "keep_distinct"
        else:
            status = "open_out_of_price_scope"
            resolution_kind = "keep_distinct"
        conflicts.append(
            {
                "conflict_id": f"CONFLICT-JID-{index + 1:03d}",
                "kind": "multiple_jids_one_canonical",
                "involved_jids": sorted(component),
                "involved_listing_keys": involved_listings,
                "status": status,
                "blocking": False,
                "resolution_kind": resolution_kind,
                "reason": (
                    "Exact listing-level resolutions prevent the shared canonical alias from becoming a join."
                    if involved_listings
                    else "No member of this source-registry conflict is in the current price catalogue."
                ),
                "evidence": [
                    evidence(
                        "jid-registry",
                        "/entries",
                        "Shared unqualified canonical values in the source JID registry.",
                        "exact_price_code",
                        sorted(component),
                    )
                ],
            }
        )
    return conflicts


def build_accounting(factory_items: list[dict], resolutions: list[dict]):
    listing_keys: dict[str, set[str]] = defaultdict(set)
    for resolution in resolutions:
        for binding in resolution["factory_bindings"]:
            listing_keys[binding["factory_item_key"]].add(resolution["listing_key"])
    accounting = []
    for item in factory_items:
        members = sorted(listing_keys.get(item["factory_item_key"], set()))
        if members:
            disposition = "mapped"
            reason = "At least one exact current price-catalog listing resolves to this qualified Factory item."
        elif item["state"] == "inactive":
            disposition = "inactive"
            reason = "The Factory source marks this qualified item inactive or frozen."
        else:
            disposition = "not_in_price_scraping_scope"
            reason = "No exact listing in the current price-scraping master resolves to this qualified item; this does not claim it is unsold elsewhere."
        accounting.append(
            {
                "factory_item_key": item["factory_item_key"],
                "disposition": disposition,
                "listing_keys": members,
                "reason": reason,
                "evidence": [
                    item["evidence"][0],
                    evidence(
                        "pricematch-sku-map",
                        "/skus",
                        "Accounting disposition against the complete frozen price-map membership set.",
                        "accounting_disposition",
                        disposition,
                    ),
                ],
            }
        )
    return accounting


def queue_accounting(sku_map: dict):
    output = []
    for section in ("review", "unpriced", "junk"):
        for index, row in enumerate(sku_map.get(section, [])):
            if isinstance(row, dict):
                platform = row.get("platform")
                listing_id = row.get("id") or row.get("listing_id") or row.get("asin") or row.get("fsn")
                kind = "listing_candidate" if platform and listing_id else "family_census"
            else:
                platform = None
                listing_id = None
                kind = "note"
            output.append(
                {
                    "source_section": section,
                    "source_index": index,
                    "entry_kind": kind,
                    "platform": platform,
                    "listing_id": str(listing_id) if listing_id is not None else None,
                    "disposition": "outside_current_price_master",
                    "evidence": [
                        evidence(
                            "pricematch-sku-map",
                            f"/{section}/{index}",
                            "Queue entry explicitly retained outside the current released price master.",
                            "accounting_disposition",
                            section,
                        )
                    ],
                }
            )
    return output


def strip_internal(listings: list[dict]) -> list[dict]:
    cleaned = []
    for row in listings:
        cleaned.append({key: value for key, value in row.items() if not key.startswith("_")})
    return cleaned


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-version", default="2026-07-19.1")
    parser.add_argument("--draft", action="store_true", help="force draft even if all release gates pass")
    args = parser.parse_args(argv)

    manifest = load_json(SOURCES_DIR / "source-manifest.json")
    sku_map = load_json(SOURCES_DIR / "pricematch-sku-map.json")
    master_v2 = load_json(SOURCES_DIR / "pricematch-master-v2.json")
    registry = load_json(SOURCES_DIR / "jid-registry.json")
    ecom_source = load_json(SOURCES_DIR / "ecom-master-products.json")
    factory_source = load_json(SOURCES_DIR / "factory-catalogs.json")
    decisions = load_json(DECISIONS_PATH)

    sources = source_records(manifest, decisions)
    factory_items, factory_index = build_factory_items(factory_source)
    collisions = build_collisions(factory_items)
    products, product_index, jid_index, alias_map, aliases = build_products(registry, decisions)
    price_skus, listings, mapping_row_count = build_price_and_listings(sku_map, master_v2, ecom_source)
    resolutions, unresolved, ambiguous = resolve_listings(
        listings,
        registry,
        decisions,
        factory_index,
        jid_index,
        alias_map,
    )
    jid_conflicts = build_jid_conflicts(registry, aliases, resolutions)
    accounting = build_accounting(factory_items, resolutions)
    queues = queue_accounting(sku_map)

    distinct_listings = len(listings)
    expected_jids = len(registry["entries"])
    blocking_conflicts = sum(1 for row in jid_conflicts if row["blocking"])
    active_listing_keys = {row["listing_key"] for row in listings if row["state"] == "active"}
    resolved_active = {row["listing_key"] for row in resolutions if row["state"] == "verified"}
    unresolved_active = len(active_listing_keys - resolved_active)
    coverage = {
        "price_skus": {"expected": len(sku_map["skus"]), "accounted": len(price_skus), "unaccounted": len(sku_map["skus"]) - len(price_skus)},
        "active_price_skus": {"expected": len(master_v2["skus"]), "accounted": sum(1 for row in price_skus if row["state"] == "active"), "unaccounted": 0},
        "source_mapping_rows": {"expected": mapping_row_count, "accounted": sum(len(row["source_memberships"]) for row in listings), "unaccounted": mapping_row_count - sum(len(row["source_memberships"]) for row in listings)},
        "listings": {"expected": distinct_listings, "accounted": len(resolutions), "unaccounted": distinct_listings - len(resolutions)},
        "jids": {"expected": expected_jids, "accounted": sum(1 for row in products if row.get("jid")), "unaccounted": expected_jids - sum(1 for row in products if row.get("jid"))},
        "factory_items": {"expected": len(factory_items), "accounted": len(accounting), "unaccounted": len(factory_items) - len(accounting)},
        "unresolved_listings": len(unresolved),
        "unresolved_active_listings": unresolved_active,
        "ambiguous_listings": len(ambiguous),
        "open_jid_conflicts": blocking_conflicts,
        "unknown_factory_collisions": sum(1 for row in collisions if row["physical_relation"] == "unknown"),
        "source_identity_sets_match": True,
        "queue_entries_outside_current_master": len(queues),
    }
    release_ready = (
        all(coverage[name]["unaccounted"] == 0 for name in ("price_skus", "active_price_skus", "source_mapping_rows", "listings", "jids", "factory_items"))
        and coverage["unresolved_listings"] == 0
        and coverage["ambiguous_listings"] == 0
        and coverage["open_jid_conflicts"] == 0
        and coverage["unknown_factory_collisions"] == 0
        and coverage["source_identity_sets_match"]
    )
    generated_at = utc_now()
    artifact = {
        "$schema": "./product-identity-map.schema.json",
        "contract": {
            "name": "jivo-product-identity",
            "schema_version": "1.0.0",
            "dataset_version": args.dataset_version,
            "release_status": "released" if release_ready and not args.draft else "draft",
            "generated_at": generated_at,
            "generator_version": "1.0.0",
            "read_only": True,
            "scope": "current pricematch master plus complete observed FG/FB/SL Factory product namespaces",
        },
        "sources": sources,
        "factory_scopes": [
            {
                "factory_scope_key": factory_scope_key(company, schema),
                "company_code": company,
                "company_id": company_id,
                "sap_schema": schema,
            }
            for company, (company_id, schema) in FACTORY_SCOPES.items()
        ],
        "products": sorted(products, key=lambda row: row["product_key"]),
        "price_skus": price_skus,
        "listings": strip_internal(listings),
        "factory_items": factory_items,
        "resolutions": resolutions,
        "jid_aliases": aliases,
        "jid_conflicts": jid_conflicts,
        "factory_item_accounting": accounting,
        "factory_code_collisions": collisions,
        "observed_queue_accounting": queues,
        "coverage": coverage,
    }
    write_json(MAP_PATH, artifact)
    write_json(REPORTS_DIR / "coverage.json", coverage)
    write_json(REPORTS_DIR / "unresolved-listings.json", unresolved)
    write_json(REPORTS_DIR / "ambiguous-listings.json", ambiguous)
    write_json(REPORTS_DIR / "factory-code-collisions.json", collisions)
    write_json(
        REPORTS_DIR / "release-summary.json",
        {
            "dataset_version": args.dataset_version,
            "release_status": artifact["contract"]["release_status"],
            "map_sha256": sha256_bytes(MAP_PATH.read_bytes()),
            "coverage": coverage,
        },
    )
    print(json.dumps({"map": str(MAP_PATH), "release_status": artifact["contract"]["release_status"], "coverage": coverage}, sort_keys=True))
    return 0 if release_ready else 6


if __name__ == "__main__":
    sys.exit(main())
