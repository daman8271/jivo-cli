#!/usr/bin/env python3
"""Collect read-only product identity inputs into JivoGPT-owned snapshots.

Remote JIVO sources are only read (SSH cat or HTTP GET). This script writes
solely below CLI/product-identity/v1/sources.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[3]
IDENTITY_ROOT = ROOT / "CLI" / "product-identity" / "v1"
SOURCES = IDENTITY_ROOT / "sources"
ECOM_CLI = ROOT / "CLI" / "ecom-cli"
FACTORY_CONFIG = Path.home() / ".config" / "jivo-factory-pp-cli" / "config.toml"

REMOTE_INPUTS = {
    "pricematch-sku-map.json": "/opt/ecom-intel/tools/pricematch/sku_map.json",
    "pricematch-master-v2.json": "/opt/ecom-intel/tools/pricematch/master_v2.json",
    "jid-registry.json": "/opt/ecom-intel/bin/jid_registry.json",
}

COMPANIES = {
    "JIVO_OIL": "JIVO_OIL_HANADB",
    "JIVO_MART": "JIVO_MART_HANADB",
    "JIVO_BEVERAGES": "JIVO_BEVERAGES_HANADB",
}

SURFACES = {
    "barcode_oitm": {
        "endpoint": "/barcode/items/oitm/",
        "cap": 100,
        "roots": ("FG", "FB"),
        "code_field": "item_code",
    },
    "sap_products": {
        "endpoint": "/production-execution/sap/items/",
        "cap": 50,
        "roots": ("FG", "FB", "SL"),
        "code_field": "ItemCode",
    },
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def ssh_json(host: str, remote_path: str) -> object:
    proc = subprocess.run(
        ["ssh", host, "cat", remote_path],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(proc.stdout)


def parse_simple_toml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"\s*([A-Za-z0-9_]+)\s*=\s*(['\"])(.*?)\2\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            values[match.group(1)] = match.group(3)
    return values


def factory_fetch(base: str, token: str, company: str, endpoint: str, prefix: str) -> list[dict]:
    url = base.rstrip("/") + endpoint + "?" + urllib.parse.urlencode({"search": prefix})
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Company-Code": company,
            "Accept": "application/json",
        },
        method="GET",
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
            break
        except Exception as exc:  # transient TLS/upstream failures are retried, then surfaced
            last_error = exc
            if attempt == 3:
                raise RuntimeError(
                    f"Factory GET failed after 4 attempts: {company} {endpoint} search={prefix}"
                ) from exc
            time.sleep(2 ** attempt)
    else:  # pragma: no cover - the loop either breaks or raises
        raise RuntimeError("unreachable Factory retry state") from last_error
    if not isinstance(payload, list):
        raise RuntimeError(f"Factory {company} {endpoint} returned {type(payload).__name__}, expected list")
    return payload


def factory_census(
    base: str,
    token: str,
    company: str,
    endpoint: str,
    cap: int,
    roots: tuple[str, ...],
    code_field: str,
) -> tuple[list[dict], list[dict]]:
    found: dict[str, dict] = {}
    requests: list[dict] = []
    stack = list(reversed(roots))
    while stack:
        prefix = stack.pop()
        rows = factory_fetch(base, token, company, endpoint, prefix)
        matching = 0
        for row in rows:
            code = str(row.get(code_field, "")).upper()
            if code.startswith(prefix):
                found[code] = row
                matching += 1
        requests.append({"prefix": prefix, "returned": len(rows), "matching_codes": matching})
        if len(rows) == cap:
            if len(prefix) >= 9:
                raise RuntimeError(f"unresolved capped Factory leaf: {company} {endpoint} {prefix}")
            stack.extend(prefix + str(number) for number in range(9, -1, -1))
    return [found[key] for key in sorted(found)], requests


def normalize_factory_row(surface: str, company: str, schema: str, endpoint: str, row: dict) -> dict:
    if surface == "barcode_oitm":
        return {
            "source_endpoint": endpoint,
            "catalog_scope": surface,
            "company_code": company,
            "sap_schema": schema,
            "item_code": str(row.get("item_code", "")).upper(),
            "item_name": row.get("item_name"),
            "inventory_uom": row.get("inventory_uom"),
            "sales_uom": row.get("sales_uom"),
            "purchase_uom": row.get("purchase_uom"),
            "item_group_code": row.get("item_group_code"),
            "manage_batch_numbers": row.get("manage_batch_numbers"),
            "manage_serial_numbers": row.get("manage_serial_numbers"),
            "is_inventory_item": row.get("is_inventory_item"),
            "is_sales_item": row.get("is_sales_item"),
            "is_purchase_item": row.get("is_purchase_item"),
            "valid_for": row.get("valid_for"),
            "frozen_for": row.get("frozen_for"),
        }
    return {
        "source_endpoint": endpoint,
        "catalog_scope": surface,
        "company_code": company,
        "sap_schema": schema,
        "item_code": str(row.get("ItemCode", "")).upper(),
        "item_name": row.get("ItemName"),
        "inventory_uom": row.get("UomCode"),
    }


def collect_factory(observed_at: str) -> dict:
    cfg = parse_simple_toml(FACTORY_CONFIG)
    base = cfg.get("base_url")
    token = cfg.get("factory_token") or cfg.get("access_token")
    if not base or not token:
        raise RuntimeError(f"Factory base URL/token not available in {FACTORY_CONFIG}")
    token = re.sub(r"(?i)^Bearer\s+", "", token)
    catalogs: list[dict] = []
    query_proof: list[dict] = []
    for company, schema in COMPANIES.items():
        for surface, spec in SURFACES.items():
            raw_rows, requests = factory_census(
                base,
                token,
                company,
                spec["endpoint"],
                spec["cap"],
                spec["roots"],
                spec["code_field"],
            )
            rows = [normalize_factory_row(surface, company, schema, spec["endpoint"], row) for row in raw_rows]
            catalogs.append(
                {
                    "catalog_scope": surface,
                    "company_code": company,
                    "sap_schema": schema,
                    "endpoint": spec["endpoint"],
                    "known_prefixes": list(spec["roots"]),
                    "endpoint_cap": spec["cap"],
                    "record_count": len(rows),
                    "rows": rows,
                }
            )
            query_proof.append(
                {
                    "catalog_scope": surface,
                    "company_code": company,
                    "endpoint": spec["endpoint"],
                    "requests": requests,
                    "no_capped_leaf": True,
                }
            )
    return {
        "source_kind": "factory_product_catalogs",
        "observed_at": observed_at,
        "read_only": True,
        "enumeration_scope": "known sellable product prefixes FG/FB/SL",
        "catalogs": catalogs,
        "query_proof": query_proof,
    }


def collect_ecom(observed_at: str) -> dict:
    env = os.environ.copy()
    env.pop("JIVO_ECOM_TOKEN", None)
    proc = subprocess.run(
        [
            "go",
            "run",
            "./cmd/jivo-ecom-pp-cli",
            "master",
            "products",
            "--data-source",
            "live",
            "--page-size",
            "10000",
            "--json",
            "--no-cache",
        ],
        cwd=str(ECOM_CLI),
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    envelope = json.loads(proc.stdout)
    results = envelope.get("results", {})
    rows = results.get("results")
    if not isinstance(rows, list):
        raise RuntimeError("Ecom master products did not return results.results[]")
    if results.get("count") != len(rows):
        raise RuntimeError(f"Ecom count mismatch: declared {results.get('count')}, returned {len(rows)}")
    codes = [row.get("format_sku_code") for row in rows]
    if None in codes or "" in codes or len(codes) != len(set(codes)):
        raise RuntimeError("Ecom format_sku_code set is missing or non-unique")
    return {
        "source_kind": "ecom_master_products",
        "observed_at": observed_at,
        "read_only": True,
        "record_count": len(rows),
        "rows": sorted(rows, key=lambda row: (str(row.get("format")), str(row.get("format_sku_code")))),
    }


def identity_values(filename: str, payload: object) -> list[str]:
    if filename == "pricematch-sku-map.json":
        values: list[str] = []
        for sku, body in payload["skus"].items():
            values.append("price:" + sku)
            for platform, listing in body.get("platforms", {}).items():
                values.append(f"listing:{platform}:{listing.get('id')}")
                for alt in listing.get("alt", []) or []:
                    values.append(f"listing:{platform}:{alt.get('id')}")
        return sorted(values)
    if filename == "pricematch-master-v2.json":
        return sorted("price:" + key for key in payload["skus"])
    if filename == "jid-registry.json":
        return sorted(payload["entries"])
    if filename == "ecom-master-products.json":
        return sorted(f"{row['format']}:{row['format_sku_code']}" for row in payload["rows"])
    if filename == "factory-catalogs.json":
        return sorted(
            f"{row['catalog_scope']}:{row['company_code']}:{row['sap_schema']}:{row['item_code']}"
            for catalog in payload["catalogs"]
            for row in catalog["rows"]
        )
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-host", default="vps")
    parser.add_argument("--skip-ecom", action="store_true")
    parser.add_argument("--skip-factory", action="store_true")
    args = parser.parse_args(argv)

    observed_at = utc_now()
    snapshots: dict[str, object] = {}
    for filename, remote_path in REMOTE_INPUTS.items():
        snapshots[filename] = ssh_json(args.ssh_host, remote_path)
    if not args.skip_ecom:
        snapshots["ecom-master-products.json"] = collect_ecom(observed_at)
    if not args.skip_factory:
        snapshots["factory-catalogs.json"] = collect_factory(observed_at)

    manifest_sources: list[dict] = []
    for filename, payload in sorted(snapshots.items()):
        path = SOURCES / filename
        write_json(path, payload)
        content = path.read_bytes()
        identities = identity_values(filename, payload)
        manifest_sources.append(
            {
                "source_id": filename.removesuffix(".json") if hasattr(str, "removesuffix") else filename[:-5],
                "path": str(path.relative_to(ROOT)),
                "observed_at": observed_at,
                "content_sha256": sha256_bytes(content),
                "identity_set_sha256": sha256_bytes(canonical_json_bytes(identities)),
                "identity_count": len(identities),
                "read_only": True,
            }
        )
    manifest = {
        "contract": "jivo-product-identity-source-manifest",
        "generated_at": observed_at,
        "read_only": True,
        "sources": manifest_sources,
    }
    write_json(SOURCES / "source-manifest.json", manifest)
    print(json.dumps({"sources": len(manifest_sources), "path": str(SOURCES), "observed_at": observed_at}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
