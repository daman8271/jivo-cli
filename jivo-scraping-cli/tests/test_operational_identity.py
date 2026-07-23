"""Operational commands must join only on authoritative listing identities."""

import contextlib
import csv
import datetime
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "product-identity-valid.json")
FIXTURE_ATTESTATION_SHA256 = (
    "sha256:d4bcce045d2d20801ceb97b586b9c62dc52641d066ee78f9483379885274e7c7"
)

sys.path.insert(0, ROOT)
from jivo_scrape import cli, identity, util  # noqa: E402
from jivo_scrape.sources import pricematch, sweeps  # noqa: E402


class ListingIdentityExtractionTests(unittest.TestCase):
    def test_authoritative_field_for_every_observed_platform_contract(self):
        cases = {
            "amazon": ("asin", "A1", "asin"),
            "amazon-fresh": ("asin", "AF1", "asin"),
            "amazon-now": ("asin", "AN1", "asin"),
            "flipkart": ("fsn", "F1", "fsn"),
            "flipkart-minutes": ("fk_pid", "FM1", "fk_pid"),
            "zepto": ("variant_id", "Z1", "variant_id"),
            "blinkit": ("prid", 12345, "prid"),
            "bigbasket": ("sku_id", "BB1", "sku_id"),
            "swiggy-instamart": ("listing_id", "SI1", "listing_id"),
        }
        for platform, (field, value, kind) in cases.items():
            with self.subTest(platform=platform):
                found = sweeps.listing_identity({field: value}, platform)
                self.assertEqual(found["listing_id"], str(value))
                self.assertEqual(found["listing_id_kind"], kind)
                self.assertEqual(
                    found["listing_key"],
                    identity.listing_key_for(platform, str(value)),
                )

    def test_identifier_looking_aliases_are_not_accepted(self):
        amazon = sweeps.listing_identity({"listing_id": "A1"}, "amazon")
        zepto = sweeps.listing_identity({"product_id": "Z1"}, "zepto")
        instamart = sweeps.listing_identity(
            {"listing_id": "I1"}, "instamart"
        )
        self.assertIsNone(amazon["listing_id"])
        self.assertIsNone(zepto["listing_id"])
        self.assertIsNone(instamart["listing_id"])

    def test_exact_enrichment_has_hash_memberships_and_qualified_factory(self):
        store = identity.ProductIdentityMap.load(
            FIXTURE,
            _trusted_attestation_sha256=FIXTURE_ATTESTATION_SHA256,
        )
        row = sweeps.normalize(
            {"asin": "B0CANOLA3L", "product_name": "display only"},
            "amazon",
            store,
        )
        self.assertEqual(row["identity_state"], "mapped")
        self.assertEqual(row["canonical_product_key"], "product|canola-3l-bottle")
        self.assertEqual(row["jid"], "JID-0116")
        self.assertEqual(row["price_sku_keys"], ["price-match|CANOLA 3L"])
        self.assertEqual(row["identity_dataset_version"], "test-2026-07-19")
        self.assertTrue(row["identity_map_sha256"].startswith("sha256:"))
        binding = row["factory_bindings"][0]
        self.assertEqual(binding["company_code"], "JIVO_MART")
        self.assertEqual(binding["sap_schema"], "JIVO_MART_HANADB")
        self.assertEqual(binding["item_code"], "FG0000317")


class OperationalCommandTests(unittest.TestCase):
    def setUp(self):
        self.identity_trust_patch = mock.patch.object(
            identity,
            "TRUSTED_ATTESTATION_SHA256",
            FIXTURE_ATTESTATION_SHA256,
        )
        self.identity_trust_patch.start()
        self.temp = tempfile.TemporaryDirectory()
        self.platforms = os.path.join(self.temp.name, "platforms")
        os.makedirs(self.platforms)
        self._write_sweep(
            "amazon",
            [
                {
                    "asin": "B0CANOLA3L",
                    "product_name": "same display name",
                    "sale": 500,
                    "mrp": 600,
                    "in_stock": True,
                },
                {
                    "asin": "WRONG-SAME-NAME",
                    "product_name": "same display name",
                    "sale": 1,
                    "mrp": 2,
                    "in_stock": False,
                },
                {
                    "product_name": "same display name",
                    "sale": 3,
                    "in_stock": False,
                },
            ],
        )
        self._write_sweep(
            "flipkart",
            [
                {
                    "fsn": "EDOCANOLA3X1",
                    "fk_name": "another display name",
                    "selling_price": 450,
                    "in_stock": True,
                }
            ],
        )

        self.history = os.path.join(self.temp.name, "history.csv")
        self.daily = os.path.join(self.temp.name, "daily.csv")
        self.summary_dir = os.path.join(self.temp.name, "summary")
        os.makedirs(self.summary_dir)
        today = datetime.date.today().isoformat()
        history_rows = [
            {
                "date": today,
                "sku": "completely unrelated label",
                "platform": "amazon",
                "listing_id": "B0CANOLA3L",
                "ref_price": "500",
                "live_modal": "490",
                "in_stock": "1",
                "status": "above",
                "diff": "-10",
                "diff_pct": "-2",
            },
            {
                "date": today,
                "sku": "CANOLA 3L",
                "platform": "amazon",
                "listing_id": "WRONG-SAME-NAME",
                "ref_price": "500",
                "live_modal": "1",
                "in_stock": "1",
                "status": "above",
                "diff": "-499",
                "diff_pct": "-99.8",
            },
            {
                "date": today,
                "sku": "CANOLA 3L",
                "platform": "amazon",
                "listing_id": "",
                "ref_price": "500",
                "live_modal": "2",
                "in_stock": "0",
                "status": "not-listed",
                "diff": "",
                "diff_pct": "",
            },
            {
                "date": today,
                "sku": "another label",
                "platform": "flipkart",
                "listing_id": "EDOCANOLA3X1",
                "ref_price": "500",
                "live_modal": "450",
                "in_stock": "1",
                "status": "above",
                "diff": "-50",
                "diff_pct": "-10",
            },
        ]
        self._write_csv(self.history, history_rows)

        self.old_paths = (
            util.PLATFORMS_DIR,
            pricematch.HISTORY_CSV,
            pricematch.DAILY_CSV,
            pricematch.SUMMARY_DIR,
        )
        util.PLATFORMS_DIR = self.platforms
        pricematch.HISTORY_CSV = self.history
        pricematch.DAILY_CSV = self.daily
        pricematch.SUMMARY_DIR = self.summary_dir

    def tearDown(self):
        (
            util.PLATFORMS_DIR,
            pricematch.HISTORY_CSV,
            pricematch.DAILY_CSV,
            pricematch.SUMMARY_DIR,
        ) = self.old_paths
        self.temp.cleanup()
        self.identity_trust_patch.stop()

    def _write_sweep(self, platform, rows):
        directory = os.path.join(self.platforms, platform)
        os.makedirs(directory)
        with open(os.path.join(directory, "result.json"), "w", encoding="utf-8") as handle:
            json.dump({"partial": False, "allRows": rows}, handle)

    @staticmethod
    def _write_csv(path, rows):
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _invoke(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_price_exact_jid_excludes_same_name_wrong_id(self):
        code, stdout, stderr = self._invoke(
            "price",
            "--sku",
            "JID-0116",
            "--platform",
            "amazon",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(len(payload["results"]), 1)
        row = payload["results"][0]
        self.assertEqual(row["listing_id"], "B0CANOLA3L")
        self.assertEqual(row["listing_id_kind"], "asin")
        self.assertEqual(row["identity_state"], "mapped")
        self.assertFalse(payload["meta"]["identity"]["name_join"])

    def test_price_plain_name_exits_2_and_directs_to_search(self):
        code, _stdout, stderr = self._invoke(
            "price",
            "--sku",
            "Jivo Canola Oil",
            "--identity-map",
            FIXTURE,
        )
        self.assertEqual(code, 2)
        self.assertIn("jivo-desk product search", stderr)

    def test_compare_exact_price_code_exposes_each_member_listing(self):
        code, stdout, stderr = self._invoke(
            "compare",
            "--sku",
            "CANOLA 3L",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(code, 0, stderr)
        rows = json.loads(stdout)["results"]
        found = {
            row["platform"]: row["listing_ids"]
            for row in rows
            if row["listing_ids"]
        }
        self.assertEqual(
            found,
            {"amazon": ["B0CANOLA3L"], "flipkart": ["EDOCANOLA3X1"]},
        )
        amazon = next(row for row in rows if row["platform"] == "amazon")
        self.assertEqual(amazon["listings"][0]["jid"], "JID-0116")

    def test_catalogue_avail_retains_mapped_unmapped_and_missing_without_name_join(self):
        code, stdout, stderr = self._invoke(
            "avail",
            "--platform",
            "amazon",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(
            payload["meta"]["identity_states"],
            {"mapped": 1, "unmapped": 1, "missing_listing_id": 1},
        )
        self.assertEqual(len(payload["results"]["listings"]), 3)
        self.assertFalse(payload["meta"]["identity"]["name_join"])

    def test_filtered_avail_uses_exact_member_listing_ids(self):
        code, stdout, stderr = self._invoke(
            "avail",
            "--sku",
            "JID-0116",
            "--platform",
            "amazon",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(code, 0, stderr)
        listings = json.loads(stdout)["results"]["listings"]
        self.assertEqual([row["listing_id"] for row in listings], ["B0CANOLA3L"])

    def test_match_filters_exact_history_listing_id_and_retains_it(self):
        code, stdout, stderr = self._invoke(
            "match",
            "--sku",
            "JID-0116",
            "--identity-map",
            FIXTURE,
            "--json",
        )
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(len(payload["results"]), 1)
        row = payload["results"][0]
        self.assertEqual(row["listing_id"], "B0CANOLA3L")
        self.assertEqual(row["sku"], "completely unrelated label")
        self.assertEqual(row["jid"], "JID-0116")

    def test_unfiltered_match_marks_unmapped_and_missing_ids_without_invention(self):
        code, stdout, stderr = self._invoke(
            "match", "--identity-map", FIXTURE, "--json"
        )
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(
            payload["meta"]["identity_states"],
            {"mapped": 2, "unmapped": 1, "missing_listing_id": 1},
        )
        missing = next(
            row for row in payload["results"] if row["identity_state"] == "missing_listing_id"
        )
        self.assertIsNone(missing["listing_id"])
        self.assertIsNone(missing["listing_key"])

    def test_match_plain_name_exits_2_and_directs_to_search(self):
        code, _stdout, stderr = self._invoke(
            "match",
            "--sku",
            "Jivo Canola Oil",
            "--identity-map",
            FIXTURE,
        )
        self.assertEqual(code, 2)
        self.assertIn("jivo-desk product search", stderr)


if __name__ == "__main__":
    unittest.main()
