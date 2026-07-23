"""Regression: `asof` must recover rows from dated sweep snapshots when the
canonical result.json is gitignored (as it is in the real ecom-intel checkout).

asof used to read ONLY platforms/<p>/result.json + result.last-good.json from
git history. This checkout's .gitignore excludes both (runtime data), so those
paths are tracked in NO commit and asof recovered 0 rows for every platform and
every date. The historical sweeps ARE in git at dated-drop paths
(platforms/<p>/**/<p>-YYYY-MM-DD.result.json); the fix discovers and reads the
newest such snapshot at-or-before the target date.

Offline-deterministic: a throwaway git repo that mirrors the real layout — a
.gitignore hiding result.json, plus tracked dated snapshots — with fixed past
dates (no tz dependence).
"""

import argparse
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from jivo_scrape import util  # noqa: E402
from jivo_scrape.commands import asof as asof_cmd  # noqa: E402


def _git(cwd, *argv, env=None):
    full = dict(os.environ)
    if env:
        full.update(env)
    subprocess.run(
        ["git", *argv],
        cwd=cwd,
        env=full,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _snapshot(sale):
    return {
        "summary": {"total_rows": 2},
        "allRows": [
            {
                "fsn": "FSNOLIVE",
                "product_name": "Jivo Extra Virgin Olive Oil 1L",
                "sale": sale,
                "mrp": 1049,
                "pincode": "-",
                "in_stock": True,
            },
            {
                "fsn": "FSNCANOLA",
                "product_name": "Jivo Canola Oil 1L",
                "sale": sale - 100,
                "mrp": 375,
                "pincode": "-",
                "in_stock": False,
            },
        ],
    }


def _capture(fn):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn()
    return rc, out.getvalue(), err.getvalue()


class AsofSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="asof-fixture-")
        cls.repo = os.path.join(cls._tmp, "ecom-intel")
        drops = os.path.join(cls.repo, "platforms", "flipkart", "kvm1-drops")
        os.makedirs(drops)
        _git(cls.repo, "init", "-q")
        _git(cls.repo, "config", "user.email", "fixture@example.test")
        _git(cls.repo, "config", "user.name", "Fixture Bot")
        _git(cls.repo, "config", "commit.gpgsign", "false")
        # Canonical result.json is gitignored, exactly like the real repo.
        with open(os.path.join(cls.repo, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write("**/result.json\n**/result.last-good.json\n")

        def commit_plain(date_iso, name):
            # A commit with NO flipkart drop in its tree, so a target date that
            # lands on it exercises the "commit exists but no snapshot" path
            # (mirrors the real 2026-07-01 case, distinct from "no commit yet").
            with open(os.path.join(cls.repo, name), "w", encoding="utf-8") as fh:
                fh.write("seed\n")
            _git(cls.repo, "add", "-A")
            stamp = "%s 12:00:00 +0000" % date_iso
            _git(
                cls.repo,
                "commit",
                "-q",
                "-m",
                "seed %s" % date_iso,
                env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
            )

        def commit_snapshot(date_iso, sale):
            # dated drop file (tracked) ...
            drop = os.path.join(drops, "flipkart-%s.result.json" % date_iso)
            with open(drop, "w", encoding="utf-8") as fh:
                json.dump(_snapshot(sale), fh)
            # ... plus a canonical result.json that must be IGNORED (a decoy with
            # a wildly different price, so any accidental read is obvious).
            canon = os.path.join(cls.repo, "platforms", "flipkart", "result.json")
            with open(canon, "w", encoding="utf-8") as fh:
                json.dump(_snapshot(99999), fh)
            _git(cls.repo, "add", "-A")
            stamp = "%s 12:00:00 +0000" % date_iso
            _git(
                cls.repo,
                "commit",
                "-q",
                "-m",
                "run: flipkart %s" % date_iso,
                env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
            )

        commit_plain("2026-06-08", "README.md")
        commit_snapshot("2026-06-10", 415)
        commit_snapshot("2026-06-12", 420)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _run(self, argv):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        asof_cmd.register(sub)
        args = parser.parse_args(argv)
        with mock.patch.object(util, "ECOM", self.repo):
            rc, out, err = _capture(lambda: asof_cmd.run(args))
        return rc, json.loads(out)

    def test_gitignore_makes_canonical_untracked(self):
        # Sanity: the canonical path is genuinely NOT tracked in any commit, so
        # the only way asof can return rows is via the snapshot fallback.
        cp = subprocess.run(
            ["git", "-C", self.repo, "log", "--all", "--name-only", "--pretty=format:"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        tracked = set(cp.stdout.split())
        self.assertNotIn("platforms/flipkart/result.json", tracked)
        self.assertIn(
            "platforms/flipkart/kvm1-drops/flipkart-2026-06-12.result.json", tracked
        )

    def test_recovers_newest_snapshot_at_or_before_date(self):
        rc, env = self._run(
            ["asof", "--platform", "flipkart", "--date", "2026-06-12", "--json"]
        )
        self.assertEqual(rc, 0)
        m = env["meta"]
        self.assertEqual(m["row_count"], 2)
        self.assertTrue(m["recovered_from_snapshot"])
        self.assertTrue(m["source_path"].endswith("flipkart-2026-06-12.result.json"))
        # Rows are the real snapshot rows (sale 420 / 320), NOT the 99999 decoy.
        prices = sorted(r["price"] for r in env["results"])
        self.assertEqual(prices, [320, 420])
        self.assertTrue(any("recovered dated snapshot" in n for n in m["notes"]))

    def test_picks_prior_snapshot_for_between_date(self):
        # 2026-06-11 has no drop -> newest at-or-before is the 06-10 snapshot.
        rc, env = self._run(
            ["asof", "--platform", "flipkart", "--date", "2026-06-11", "--json"]
        )
        m = env["meta"]
        self.assertTrue(m["source_path"].endswith("flipkart-2026-06-10.result.json"))
        prices = sorted(r["price"] for r in env["results"])
        self.assertEqual(prices, [315, 415])  # sale 415 and 415-100

    def test_sku_filter_applies_to_recovered_rows(self):
        rc, env = self._run(
            [
                "asof",
                "--platform",
                "flipkart",
                "--date",
                "2026-06-12",
                "--sku",
                "olive",
                "--json",
            ]
        )
        self.assertEqual(env["meta"]["row_count"], 1)
        self.assertIn("Olive", env["results"][0]["product"])

    def test_date_before_any_snapshot_is_empty_but_clean(self):
        # Mirrors the real 2026-07-01 case: a commit EXISTS at-or-before the
        # date (the 06-08 seed) but its tree has no flipkart drop -> 0 rows, a
        # clear note, exit 0 (correct, not a crash and not a wrong-path read).
        rc, env = self._run(
            ["asof", "--platform", "flipkart", "--date", "2026-06-09", "--json"]
        )
        self.assertEqual(rc, 0)
        self.assertIsNotNone(env["meta"]["commit"])  # a commit was found
        self.assertEqual(env["meta"]["row_count"], 0)
        self.assertFalse(env["meta"]["recovered_from_snapshot"])
        self.assertIsNone(env["meta"]["source_path"])
        self.assertTrue(
            any("nor a dated snapshot" in n for n in env["meta"]["notes"])
        )


if __name__ == "__main__":
    unittest.main()
