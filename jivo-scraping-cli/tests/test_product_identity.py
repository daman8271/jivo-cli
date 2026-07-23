"""Contract and CLI tests for exact cross-system product identity."""

import copy
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
BIN = os.path.join(ROOT, "bin", "jivo-desk")
FIXTURE = os.path.join(HERE, "fixtures", "product-identity-valid.json")
FIXTURE_SOURCE = os.path.join(HERE, "fixtures", "fixture-source.json")
FIXTURE_ATTESTATION = os.path.join(HERE, "fixtures", "release-attestation.json")
FIXTURE_ATTESTATION_SHA256 = (
    "sha256:d4bcce045d2d20801ceb97b586b9c62dc52641d066ee78f9483379885274e7c7"
)
REPO_ROOT = os.path.dirname(os.path.dirname(ROOT))
PRODUCTION_V1 = os.path.join(REPO_ROOT, "CLI", "product-identity", "v1")

sys.path.insert(0, ROOT)
from jivo_scrape import cli, identity  # noqa: E402


def run_cli(*arguments, **kwargs):
    env = kwargs.pop("env", None)
    trusted_attestation_sha256 = kwargs.pop(
        "trusted_attestation_sha256", FIXTURE_ATTESTATION_SHA256
    )
    assert not kwargs
    stdout = io.StringIO()
    stderr = io.StringIO()
    environment = (
        mock.patch.dict(os.environ, env, clear=True)
        if env is not None
        else contextlib.nullcontext()
    )
    with (
        mock.patch.object(
            identity,
            "TRUSTED_ATTESTATION_SHA256",
            trusted_attestation_sha256,
        ),
        environment,
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        returncode = cli.main(list(arguments))
    return subprocess.CompletedProcess(
        [sys.executable, BIN] + list(arguments),
        returncode,
        stdout.getvalue(),
        stderr.getvalue(),
    )


def sha256_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def write_test_bundle(directory, data):
    """Write a synthetic bundle and return its map path and injected trust hash."""
    map_path = os.path.join(directory, "product-identity-map.json")
    source_path = os.path.join(directory, "fixture-source.json")
    attestation_path = os.path.join(directory, "release-attestation.json")
    map_raw = (
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    with open(map_path, "wb") as handle:
        handle.write(map_raw)
    with open(FIXTURE_SOURCE, "rb") as source:
        source_raw = source.read()
    with open(source_path, "wb") as target:
        target.write(source_raw)
    attestation = {
        "format_version": "1.0.0",
        "contract_name": "jivo-product-identity-release-attestation",
        "dataset_version": data["contract"]["dataset_version"],
        "schema_version": data["contract"]["schema_version"],
        "release_status": data["contract"]["release_status"],
        "map": {
            "uri": "product-identity-map.json",
            "sha256": sha256_bytes(map_raw),
        },
        "evidence_artifacts": [
            {
                "source_id": "fixture",
                "uri": "fixture-source.json",
                "sha256": sha256_bytes(source_raw),
            }
        ],
        "verification": {
            "verifier_version": "1.1.0",
            "check_count": 74761,
        },
    }
    attestation_raw = (
        json.dumps(attestation, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    with open(attestation_path, "wb") as handle:
        handle.write(attestation_raw)
    return map_path, sha256_bytes(attestation_raw)


def fixture_data():
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_production_cli(*arguments):
    """Run the real process with its compiled trust anchor and no test patch."""
    env = dict(os.environ)
    env.pop("JIVO_PRODUCT_IDENTITY_MAP", None)
    return subprocess.run(
        [sys.executable, BIN] + list(arguments),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


class ReleaseAttestationTests(unittest.TestCase):
    """Every operational entry point must reject release-bundle tampering."""

    def _copy_production_bundle(self, directory):
        target = os.path.join(directory, "v1")
        shutil.copytree(PRODUCTION_V1, target)
        return target, os.path.join(target, "product-identity-map.json")

    def _assert_all_loads_fail(self, map_path, expected=None):
        commands = (
            ("product", "verify", "--identity-map", map_path),
            ("price", "--sku", "JID-0116", "--identity-map", map_path),
            ("avail", "--sku", "JID-0116", "--identity-map", map_path),
            ("compare", "--sku", "JID-0116", "--identity-map", map_path),
            ("match", "--sku", "JID-0116", "--identity-map", map_path),
        )
        for command in commands:
            with self.subTest(command=command[0]):
                result = run_production_cli(*command)
                self.assertEqual(result.returncode, 6, result.stdout + result.stderr)
                if expected:
                    self.assertIn(expected, result.stderr)

    def test_missing_or_edited_attestation_fails_every_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, map_path = self._copy_production_bundle(directory)
            os.unlink(os.path.join(bundle, "release-attestation.json"))
            self._assert_all_loads_fail(map_path, "attestation cannot be read")
        with tempfile.TemporaryDirectory() as directory:
            bundle, map_path = self._copy_production_bundle(directory)
            attestation = os.path.join(bundle, "release-attestation.json")
            with open(attestation, "a", encoding="utf-8") as handle:
                handle.write("\n")
            self._assert_all_loads_fail(map_path, "not the compiled trusted release")

    def test_evidence_snapshot_drift_fails_every_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, map_path = self._copy_production_bundle(directory)
            evidence = os.path.join(bundle, "sources", "ecom-master-products.json")
            with open(evidence, "a", encoding="utf-8") as handle:
                handle.write("\n")
            self._assert_all_loads_fail(map_path, "evidence artifact hash drift")

    def test_map_source_hash_drift_fails_every_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            _bundle, map_path = self._copy_production_bundle(directory)
            with open(map_path, encoding="utf-8") as handle:
                data = json.load(handle)
            data["sources"][0]["content_sha256"] = "sha256:" + "0" * 64
            with open(map_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
            self._assert_all_loads_fail(map_path, "map SHA-256")

    def test_wrong_shikanji_cross_company_binding_fails_every_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            _bundle, map_path = self._copy_production_bundle(directory)
            with open(map_path, encoding="utf-8") as handle:
                data = json.load(handle)
            listing_key = "urn:jivo:listing:amazon:B0GZ7PXVF8"
            beverages = "urn:jivo:factory:JIVO_BEVERAGES:JIVO_BEVERAGES_HANADB:FG0000315"
            mart = "urn:jivo:factory:JIVO_MART:JIVO_MART_HANADB:FG0000315"
            target = next(
                row for row in data["resolutions"] if row["listing_key"] == listing_key
            )
            binding = next(
                row for row in target["factory_bindings"] if row["factory_item_key"] == beverages
            )
            binding["factory_item_key"] = mart
            for row in data["factory_item_accounting"]:
                if row["factory_item_key"] == beverages:
                    row["listing_keys"] = [
                        value for value in row["listing_keys"] if value != listing_key
                    ]
                    if not row["listing_keys"]:
                        row["disposition"] = "not_in_price_scraping_scope"
                elif row["factory_item_key"] == mart:
                    row["listing_keys"] = sorted(set(row["listing_keys"] + [listing_key]))
                    row["disposition"] = "mapped"
            with open(map_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
            self._assert_all_loads_fail(map_path, "map SHA-256")

    def test_collapsed_sano_split_fails_every_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            _bundle, map_path = self._copy_production_bundle(directory)
            with open(map_path, encoding="utf-8") as handle:
                data = json.load(handle)
            target = next(
                row
                for row in data["resolutions"]
                if row["listing_key"] == "urn:jivo:listing:amazon:B0CCVF1XVS"
            )
            target["canonical_product_key"] = "urn:jivo:product:JID-0051"
            target["canonical_jid"] = "JID-0051"
            with open(map_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
            self._assert_all_loads_fail(map_path, "map SHA-256")

    def test_map_cannot_self_approve_by_editing_detached_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, map_path = self._copy_production_bundle(directory)
            with open(map_path, "ab") as handle:
                handle.write(b"\n")
            with open(map_path, "rb") as handle:
                new_map_sha = sha256_bytes(handle.read())
            attestation_path = os.path.join(bundle, "release-attestation.json")
            with open(attestation_path, encoding="utf-8") as handle:
                attestation = json.load(handle)
            attestation["map"]["sha256"] = new_map_sha
            with open(attestation_path, "w", encoding="utf-8") as handle:
                json.dump(attestation, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
            self._assert_all_loads_fail(
                map_path, "attestation SHA-256 is not the compiled trusted release"
            )

    def test_alternate_map_and_attestation_cannot_be_trusted_by_cli_or_env(self):
        result = run_production_cli(
            "product", "verify", "--identity-map", FIXTURE
        )
        self.assertEqual(result.returncode, 6)
        self.assertIn("not the compiled trusted release", result.stderr)
        env = dict(os.environ)
        env["JIVO_PRODUCT_IDENTITY_MAP"] = FIXTURE
        result = subprocess.run(
            [sys.executable, BIN, "product", "verify"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 6)
        self.assertIn("not the compiled trusted release", result.stderr)


class ProductIdentityTests(unittest.TestCase):
    def test_verify_released_map(self):
        result = run_cli("product", "verify", "--identity-map", FIXTURE, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["results"]["valid"])
        self.assertEqual(payload["results"]["actual_counts"]["listings"], 2)

    def test_price_sku_expands_each_listing_own_jid_and_binding(self):
        result = run_cli(
            "product",
            "resolve",
            "CANOLA 3L",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        resolved = json.loads(result.stdout)["results"]
        self.assertEqual(resolved["entity_type"], "price_sku")
        members = resolved["members"]
        self.assertEqual([m["product"]["jid"] for m in members], ["JID-0116", "JID-0016"])
        self.assertEqual(
            members[0]["resolution"]["factory_bindings"][0]["factory_item"]["item_code"],
            "FG0000317",
        )
        self.assertEqual(
            members[1]["resolution"]["factory_bindings"][0]["factory_item"]["item_code"],
            "FG0000043",
        )

    def test_resolves_full_price_key_and_exact_jid(self):
        price = run_cli(
            "product",
            "resolve",
            "price-match|CANOLA 3L",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        product = run_cli(
            "product",
            "resolve",
            "JID-0116",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(price.returncode, 0, price.stderr)
        self.assertEqual(product.returncode, 0, product.stderr)
        self.assertEqual(json.loads(price.stdout)["results"]["entity_type"], "price_sku")
        self.assertEqual(json.loads(product.stdout)["results"]["product"]["jid"], "JID-0116")

    def test_resolves_exact_product_key(self):
        result = run_cli(
            "product",
            "resolve",
            "product|canola-3l-bottle",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        product = json.loads(result.stdout)["results"]["product"]
        self.assertEqual(product["product_key"], "product|canola-3l-bottle")

    def test_resolves_platform_qualified_listing_identifier(self):
        result = run_cli(
            "product",
            "resolve",
            "amazon:B0CANOLA3L",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        resolved = json.loads(result.stdout)["results"]
        self.assertEqual(resolved["entity_type"], "listing")
        self.assertEqual(resolved["product"]["jid"], "JID-0116")

    def test_resolves_full_qualified_factory_key_never_bare_item_code(self):
        full = "JIVO_MART|JIVO_MART_HANADB|FG0000317"
        result = run_cli(
            "product", "resolve", full, "--identity-map", FIXTURE, "--json"
        )
        bare = run_cli(
            "product", "resolve", "FG0000317", "--identity-map", FIXTURE
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["results"]["factory_item"]["factory_item_key"],
            full,
        )
        self.assertEqual(bare.returncode, 4)
        self.assertIn("product search", bare.stderr)

        reused = run_cli(
            "product",
            "resolve",
            "JIVO_OIL|JIVO_OIL_HANADB|FG0000317",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(reused.returncode, 0, reused.stderr)
        self.assertIn(
            "SESAME",
            json.loads(reused.stdout)["results"]["factory_item"]["item_name"],
        )

    def test_rejects_unreported_reused_factory_code_collision(self):
        self._assert_invalid_map(
            lambda data: data.update(factory_code_collisions=[]),
            "factory_code_collisions missing",
        )

    def test_jid_alias_references_must_exist(self):
        def add_bad_alias(data):
            data["jid_aliases"] = [
                {
                    "alias_jid": "JID-0016",
                    "canonical_jid": "JID-MISSING",
                    "relation": "duplicate_of",
                    "decision_id": "fixture-alias",
                    "reason": "Fixture decision",
                    "evidence": [
                        {
                            "source_id": "fixture",
                            "pointer": "/review/aliases/fixture-alias",
                            "claim": "Alias decision",
                            "evidence_kind": "review_decision",
                        }
                    ],
                }
            ]

        self._assert_invalid_map(add_bad_alias, "missing canonical JID")

    def test_exact_alias_jid_resolves_to_canonical_product(self):
        data = fixture_data()
        data["jid_aliases"] = [
            {
                "alias_jid": "JID-0016",
                "canonical_jid": "JID-0116",
                "relation": "duplicate_of",
                "decision_id": "fixture-alias",
                "reason": "Fixture alias for resolver behavior",
                "evidence": [
                    {
                        "source_id": "fixture",
                        "pointer": "/review/aliases/fixture-alias",
                        "claim": "Alias decision",
                        "evidence_kind": "review_decision",
                    }
                ],
            }
        ]
        store = identity.ProductIdentityMap(data, "fixture")
        resolved = store.resolve("JID-0016")
        self.assertEqual(resolved["product"]["jid"], "JID-0116")
        self.assertEqual(resolved["requested_alias"]["alias_jid"], "JID-0016")

    def test_blocking_jid_conflict_must_match_zero_tolerance_coverage(self):
        def add_blocking_conflict(data):
            data["jid_conflicts"] = [
                {
                    "conflict_id": "fixture-conflict",
                    "kind": "mixed_pack",
                    "involved_jids": ["JID-0016", "JID-0116"],
                    "involved_listing_keys": [
                        "amazon|B0CANOLA3L",
                        "flipkart|EDOCANOLA3X1",
                    ],
                    "status": "resolved_for_price_scope",
                    "blocking": True,
                    "resolution_kind": "listing_level_split",
                    "reason": "Fixture blocking conflict",
                    "evidence": [
                        {
                            "source_id": "fixture",
                            "pointer": "/review/conflicts/fixture-conflict",
                            "claim": "Conflict decision",
                            "evidence_kind": "review_decision",
                        }
                    ],
                }
            ]

        self._assert_invalid_map(add_blocking_conflict, "has 1 blocking row")

    def test_name_search_is_candidate_only_and_name_does_not_resolve(self):
        search = run_cli(
            "product", "search", "Canola Bottle", "--identity-map", FIXTURE, "--json"
        )
        resolve = run_cli(
            "product", "resolve", "Jivo Canola Oil 3L Bottle", "--identity-map", FIXTURE
        )
        self.assertEqual(search.returncode, 0, search.stderr)
        rows = json.loads(search.stdout)["results"]
        self.assertTrue(rows)
        self.assertTrue(all(row["candidate_only"] for row in rows))
        self.assertEqual(resolve.returncode, 4)

    def test_ambiguous_bare_price_code_requires_full_key(self):
        data = fixture_data()
        extra_sku = copy.deepcopy(data["price_skus"][0])
        extra_sku.update(
            price_sku_key="other-source|CANOLA 3L",
            source_namespace="other-source",
            member_listing_keys=["amazon-fresh|B0CANOLA3L-FRESH"],
        )
        data["price_skus"].append(extra_sku)
        extra_listing = copy.deepcopy(data["listings"][0])
        extra_listing.update(
            listing_key="amazon-fresh|B0CANOLA3L-FRESH",
            price_sku_key="other-source|CANOLA 3L",
            platform="amazon-fresh",
            listing_id="B0CANOLA3L-FRESH",
        )
        data["listings"].append(extra_listing)
        extra_resolution = copy.deepcopy(data["resolutions"][0])
        extra_resolution.update(
            resolution_id="resolution|amazon-fresh|B0CANOLA3L-FRESH",
            listing_key="amazon-fresh|B0CANOLA3L-FRESH",
        )
        data["resolutions"].append(extra_resolution)
        data["factory_item_accounting"][0]["listing_keys"].append(
            "amazon-fresh|B0CANOLA3L-FRESH"
        )
        data["coverage"]["price_skus"].update(expected=2, accounted=2)
        data["coverage"]["listings"].update(expected=3, accounted=3)
        store = identity.ProductIdentityMap(data, "fixture")
        with self.assertRaises(identity.IdentityAmbiguousError):
            store.resolve("CANOLA 3L")
        self.assertEqual(
            store.resolve("other-source|CANOLA 3L")["price_sku"]["source_namespace"],
            "other-source",
        )

    def test_one_listing_can_keep_multiple_price_group_memberships(self):
        data = fixture_data()
        second_key = "other-source|CANOLA SINGLE 3L"
        second = copy.deepcopy(data["price_skus"][0])
        second.update(
            price_sku_key=second_key,
            source_namespace="other-source",
            source_product_code="CANOLA SINGLE 3L",
            member_listing_keys=["amazon|B0CANOLA3L"],
        )
        data["price_skus"].append(second)
        listing = data["listings"][0]
        listing["price_sku_keys"] = [listing["price_sku_key"], second_key]
        listing["source_memberships"] = [
            {"price_sku_key": listing["price_sku_key"], "role": "primary"},
            {"price_sku_key": second_key, "role": "secondary"},
        ]
        data["coverage"]["price_skus"].update(expected=2, accounted=2)
        store = identity.ProductIdentityMap(data, "fixture")
        resolved = store.resolve(second_key)
        self.assertEqual(len(resolved["members"]), 1)
        member = resolved["members"][0]
        self.assertEqual(member["price_sku"]["price_sku_key"], second_key)
        self.assertEqual(len(member["price_skus"]), 2)
        self.assertEqual(member["product"]["jid"], "JID-0116")

    def test_explicit_path_precedes_environment(self):
        env = dict(os.environ)
        env["JIVO_PRODUCT_IDENTITY_MAP"] = "/does/not/exist.json"
        result = run_cli(
            "product", "verify", "--identity-map", FIXTURE, "--json", env=env
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_identity_map_flag_is_accepted_before_action(self):
        result = run_cli(
            "product", "--identity-map", FIXTURE, "--json", "verify"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["results"]["valid"])

    def test_environment_path_is_supported(self):
        env = dict(os.environ)
        env["JIVO_PRODUCT_IDENTITY_MAP"] = FIXTURE
        result = run_cli("product", "coverage", "--json", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["results"]["coverage"]["unresolved_listings"],
            0,
        )

    def _assert_invalid_map(self, mutation, expected_message):
        data = copy.deepcopy(fixture_data())
        mutation(data)
        with tempfile.TemporaryDirectory() as directory:
            path, trusted = write_test_bundle(directory, data)
            result = run_cli(
                "product",
                "verify",
                "--identity-map",
                path,
                trusted_attestation_sha256=trusted,
            )
        self.assertEqual(result.returncode, 6)
        self.assertIn(expected_message, result.stderr)

    def test_rejects_non_released_map_with_exit_6(self):
        self._assert_invalid_map(
            lambda data: data["contract"].update(release_status="draft"),
            "release_status",
        )

    def test_rejects_unsupported_schema_major_with_exit_6(self):
        self._assert_invalid_map(
            lambda data: data["contract"].update(schema_version="2.0.0"),
            "unsupported contract.schema_version",
        )

    def test_rejects_every_nonzero_release_gate_with_exit_6(self):
        for field in (
            "unresolved_listings",
            "ambiguous_listings",
            "open_jid_conflicts",
            "unknown_factory_collisions",
        ):
            with self.subTest(field=field):
                self._assert_invalid_map(
                    lambda data, field=field: data["coverage"].update(
                        {field: 1}
                    ),
                    "%s must be zero" % field,
                )

    def test_rejects_source_identity_set_drift_with_exit_6(self):
        self._assert_invalid_map(
            lambda data: data["coverage"].update(source_identity_sets_match=False),
            "source_identity_sets_match must be true",
        )

    def test_rejects_unaccounted_scope_with_exit_6(self):
        def mark_unaccounted(data):
            data["coverage"]["listings"] = {
                "expected": 2,
                "accounted": 1,
                "unaccounted": 1,
            }

        self._assert_invalid_map(mark_unaccounted, "listings.unaccounted must be zero")

    def test_rejects_missing_factory_reference_with_exit_6(self):
        self._assert_invalid_map(
            lambda data: data["resolutions"][0]["factory_bindings"][0].update(
                factory_item_key="missing|factory|key"
            ),
            "references missing factory_item",
        )

    def test_rejects_broken_listing_to_price_sku_reference_with_exit_6(self):
        self._assert_invalid_map(
            lambda data: data["listings"][0].update(price_sku_key="missing|sku"),
            "references missing price_sku",
        )

    def test_rejects_missing_or_unknown_source_evidence_with_exit_6(self):
        self._assert_invalid_map(
            lambda data: data["price_skus"][0].update(evidence=[]),
            "evidence must contain at least 1",
        )
        self._assert_invalid_map(
            lambda data: data["listings"][0]["evidence"][0].update(
                source_id="missing-source"
            ),
            "references missing source",
        )

    def test_binding_requires_exact_source_and_qualified_factory_evidence(self):
        def remove_exact_source(data):
            binding = data["resolutions"][0]["factory_bindings"][0]
            binding["evidence"] = [
                copy.deepcopy(binding["evidence"][1]),
                {
                    "source_id": "fixture",
                    "pointer": "/review/decision",
                    "claim": "Curated review",
                    "evidence_kind": "review_decision",
                },
            ]

        self._assert_invalid_map(remove_exact_source, "requires one of")

    def test_unproven_factory_conversion_is_explicitly_null(self):
        data = fixture_data()
        binding = data["resolutions"][0]["factory_bindings"][0]
        binding["factory_uom_per_listing_offer"] = None
        binding["conversion_state"] = "not_proven"
        identity.ProductIdentityMap(data, "fixture")

        def hide_state(invalid):
            binding = invalid["resolutions"][0]["factory_bindings"][0]
            binding["factory_uom_per_listing_offer"] = None
            binding.pop("conversion_state", None)

        self._assert_invalid_map(hide_state, "requires conversion_state='not_proven'")

    def test_rejects_two_primary_bindings_in_the_same_factory_scope(self):
        def add_second_primary(data):
            first = data["resolutions"][0]["factory_bindings"][0]
            second = copy.deepcopy(first)
            second["factory_item_key"] = "JIVO_MART|JIVO_MART_HANADB|FG0000043"
            second["evidence"][1] = copy.deepcopy(
                data["factory_items"][1]["evidence"][0]
            )
            data["resolutions"][0]["factory_bindings"].append(second)

        self._assert_invalid_map(add_second_primary, "both primary_for_scope")

    def test_factory_accounting_requires_disposition_evidence(self):
        self._assert_invalid_map(
            lambda data: data["factory_item_accounting"][0].update(evidence=[]),
            "factory_item_accounting[0].evidence",
        )

    def test_rejects_active_listing_without_resolution_with_exit_6(self):
        def remove_resolution(data):
            data["resolutions"] = data["resolutions"][1:]

        self._assert_invalid_map(remove_resolution, "has no resolution")

    def test_nullable_jid_with_reviewed_factory_absence_is_valid(self):
        data = fixture_data()
        data["products"][1]["jid"] = None
        resolution = data["resolutions"][0]
        resolution["canonical_jid"] = None
        resolution["factory_mapping_state"] = "reviewed_absent"
        resolution["factory_bindings"] = []
        resolution["factory_absence"] = {
            "reason_code": "not_present_in_complete_factory_catalog",
            "reason": "All three complete fixture catalogs were checked.",
            "scopes_checked": [
                row["factory_scope_key"] for row in data["factory_scopes"]
            ],
            "evidence": [
                {
                    "source_id": "fixture",
                    "pointer": "/listings/amazon/B0CANOLA3L",
                    "claim": "Exact marketplace product reviewed",
                    "evidence_kind": "exact_listing_identity",
                },
                {
                    "source_id": "fixture",
                    "pointer": "/factory/complete-catalogs",
                    "claim": "Product absent from all complete Factory catalogs",
                    "evidence_kind": "complete_catalog_absence",
                },
            ],
        }
        data["factory_item_accounting"][0].update(
            disposition="not_in_price_scraping_scope",
            listing_keys=[],
            reason="No remaining price-scope binding in this mutated fixture.",
        )
        data["coverage"]["jids"] = {
            "expected": 1,
            "accounted": 1,
            "unaccounted": 0,
        }
        with tempfile.TemporaryDirectory() as directory:
            path, trusted = write_test_bundle(directory, data)
            result = run_cli(
                "product",
                "resolve",
                "product|canola-3l-bottle",
                "--identity-map",
                path,
                "--json",
                trusted_attestation_sha256=trusted,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        resolved = json.loads(result.stdout)["results"]
        self.assertIsNone(resolved["product"]["jid"])
        self.assertEqual(
            resolved["listings"][0]["resolution"]["factory_mapping_state"],
            "reviewed_absent",
        )

    def test_reviewed_absence_requires_all_three_scopes_and_evidence(self):
        def invalid_absence(data):
            resolution = data["resolutions"][0]
            resolution["factory_mapping_state"] = "reviewed_absent"
            resolution["factory_bindings"] = []
            resolution["factory_absence"] = {
                "reason_code": "source_gap",
                "reason": "Incomplete review",
                "scopes_checked": [data["factory_scopes"][0]["factory_scope_key"]],
                "evidence": [],
            }

        self._assert_invalid_map(invalid_absence, "must contain all 3 Factory scopes")

    def test_legacy_jid_only_product_and_resolution_remain_readable(self):
        data = fixture_data()
        for product in data["products"]:
            product.pop("product_key")
        for resolution in data["resolutions"]:
            resolution.pop("canonical_product_key")
        store = identity.ProductIdentityMap(data, "fixture")
        resolved = store.resolve("JID-0116")
        self.assertEqual(resolved["product"]["jid"], "JID-0116")

    def test_direct_loader_default_walks_repo_parents(self):
        with tempfile.TemporaryDirectory() as root:
            map_dir = os.path.join(root, "CLI", "product-identity", "v1")
            os.makedirs(map_dir)
            path = os.path.join(map_dir, "product-identity-map.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(fixture_data(), handle)
            nested = os.path.join(root, "CLI", "jivo-desk-cli", "nested")
            os.makedirs(nested)
            self.assertEqual(identity.find_map_path(cwd=nested, environ={}), path)


if __name__ == "__main__":
    unittest.main()
