"""Adversarial tests for the shared product-identity release gate."""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V1 = ROOT / "CLI" / "product-identity" / "v1"
MAP = V1 / "product-identity-map.json"
SCHEMA = V1 / "product-identity-map.schema.json"
ATTESTATION = V1 / "release-attestation.json"
ATTESTATION_SCHEMA = V1 / "release-attestation.schema.json"
VERIFY = ROOT / "CLI" / "product-identity" / "tools" / "verify_map.py"
ATTEST = ROOT / "CLI" / "product-identity" / "tools" / "attest_release.py"
COLLECT = ROOT / "CLI" / "product-identity" / "tools" / "collect_sources.py"


def load_map():
    with MAP.open(encoding="utf-8") as handle:
        return json.load(handle)


def verify_data(data):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "map.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VERIFY), "--map", str(path), "--json"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )


class IdentityMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_map()

    def test_current_release_passes_independent_verifier(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY), "--json"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertGreater(payload["checks"], 70000)
        self.assertEqual(payload["coverage"]["unresolved_listings"], 0)
        self.assertEqual(
            payload["attestation"]["sha256"],
            "sha256:ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac",
        )

    def test_detached_attestation_is_reproducible_and_schema_valid(self):
        result = subprocess.run(
            [sys.executable, str(ATTEST), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            "sha256:" + hashlib.sha256(ATTESTATION.read_bytes()).hexdigest(),
            "sha256:ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac",
        )
        try:
            import jsonschema
        except ImportError:
            return
        schema = json.loads(ATTESTATION_SCHEMA.read_text(encoding="utf-8"))
        artifact = json.loads(ATTESTATION.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(artifact))
        self.assertEqual(errors, [], "\n".join(error.message for error in errors))

    def test_verifier_rejects_evidence_drift_and_self_approved_attestation(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "v1"
            shutil.copytree(V1, bundle)
            evidence = bundle / "sources" / "ecom-master-products.json"
            evidence.write_bytes(evidence.read_bytes() + b"\n")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    "--map",
                    str(bundle / "product-identity-map.json"),
                    "--json",
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 6)
            self.assertIn("evidence artifact hash drift", result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "v1"
            shutil.copytree(V1, bundle)
            map_path = bundle / "product-identity-map.json"
            map_path.write_bytes(map_path.read_bytes() + b"\n")
            attestation_path = bundle / "release-attestation.json"
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
            attestation["map"]["sha256"] = (
                "sha256:" + hashlib.sha256(map_path.read_bytes()).hexdigest()
            )
            attestation_path.write_text(
                json.dumps(attestation, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(VERIFY), "--map", str(map_path), "--json"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 6)
            self.assertIn("not the compiled trusted release", result.stdout)

    def test_removed_listing_is_detected(self):
        data = copy.deepcopy(self.data)
        removed = data["listings"].pop()
        data["resolutions"] = [
            row for row in data["resolutions"] if row["listing_key"] != removed["listing_key"]
        ]
        result = verify_data(data)
        self.assertEqual(result.returncode, 6)
        self.assertIn("listing identity set", result.stdout)

    def test_removed_factory_collision_is_detected(self):
        data = copy.deepcopy(self.data)
        data["factory_code_collisions"] = [
            row for row in data["factory_code_collisions"] if row["item_code"] != "FG0000315"
        ]
        result = verify_data(data)
        self.assertEqual(result.returncode, 6)
        self.assertIn("collision code set", result.stdout)

    def test_shikanji_cannot_bind_mart_fg0000315(self):
        data = copy.deepcopy(self.data)
        target = next(
            row
            for row in data["resolutions"]
            if row["listing_key"] == "urn:jivo:listing:amazon:B0GZ7PXVF8"
        )
        mart = next(
            row
            for row in data["factory_items"]
            if row["factory_item_key"]
            == "urn:jivo:factory:JIVO_MART:JIVO_MART_HANADB:FG0000315"
        )
        target["factory_bindings"].append(
            {
                "factory_item_key": mart["factory_item_key"],
                "role": "sellable_unit",
                "factory_uom_per_listing_offer": None,
                "conversion_state": "not_proven",
                "primary_for_scope": False,
                "evidence": [target["evidence"][0], mart["evidence"][0]],
            }
        )
        result = verify_data(data)
        self.assertEqual(result.returncode, 6)
        self.assertIn("incorrectly joined to Mart FG0000315", result.stdout)

    def test_sano_split_cannot_be_collapsed(self):
        data = copy.deepcopy(self.data)
        amazon = next(
            row
            for row in data["resolutions"]
            if row["listing_key"] == "urn:jivo:listing:amazon:B0CCVF1XVS"
        )
        amazon["canonical_product_key"] = "urn:jivo:product:JID-0051"
        amazon["canonical_jid"] = "JID-0051"
        result = verify_data(data)
        self.assertEqual(result.returncode, 6)
        self.assertIn("Sano Extra Light and Classic were not split", result.stdout)

    def test_draft_and_source_hash_drift_fail_closed(self):
        draft = copy.deepcopy(self.data)
        draft["contract"]["release_status"] = "draft"
        self.assertEqual(verify_data(draft).returncode, 6)

        drift = copy.deepcopy(self.data)
        drift["sources"][0]["content_sha256"] = "sha256:" + "0" * 64
        result = verify_data(drift)
        self.assertEqual(result.returncode, 6)
        self.assertIn("source hash drift", result.stdout)

    def test_schema_accepts_current_release(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(self.data))
        self.assertEqual(errors, [], "\n".join(error.message for error in errors[:10]))

    def test_collector_has_get_only_http_surface(self):
        text = COLLECT.read_text(encoding="utf-8")
        self.assertIn('method="GET"', text)
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertNotIn('method="%s"' % method, text)


if __name__ == "__main__":
    unittest.main()
