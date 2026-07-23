"""Offline-deterministic tests for the read-only git time-travel source.

We build a throwaway git repo in a tmp dir with three commits across two fake
dates -- each commit overwrites ``platforms/demo/result.json`` with a different
price and carries a ``run: demo <date-time>`` subject, exactly like a real
sweep. These git *writes* are confined to the tmp fixture (the READ-ONLY LAW
covers data roots; gittime.py itself must never invoke a write verb, which the
last test guards against by construction: only rev-list/show/log/rev-parse).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)

sys.path.insert(0, ROOT)
from jivo_scrape.sources import gittime  # noqa: E402


def _run(cwd, *argv, env=None):
    full = dict(os.environ)
    if env:
        full.update(env)
    cp = subprocess.run(
        ["git", *argv],
        cwd=cwd,
        env=full,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return cp


def _commit(repo, price, when, subject):
    """Write platforms/demo/result.json with `price` and commit it dated `when`."""
    pdir = os.path.join(repo, "platforms", "demo")
    os.makedirs(pdir, exist_ok=True)
    payload = {
        "summary": {"total_rows": 1},
        "allRows": [
            {
                "fsn": "DEMOFSN1",
                "product_name": "Demo Olive Oil 1L",
                "sale": price,
                "mrp": 200,
                "pincode": "-",
                "in_stock": True,
            }
        ],
    }
    with open(os.path.join(pdir, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    _run(repo, "add", "-A")
    stamp = "%s +0000" % when  # explicit UTC so date filters are tz-stable
    _run(
        repo,
        "commit",
        "-q",
        "-m",
        subject,
        env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
    )


class GitTimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp(prefix="gittime-fixture-")
        cls.repo = os.path.join(cls._tmp, "ecom-intel")
        os.makedirs(cls.repo)
        _run(cls.repo, "init", "-q")
        _run(cls.repo, "config", "user.email", "fixture@example.test")
        _run(cls.repo, "config", "user.name", "Fixture Bot")
        _run(cls.repo, "config", "commit.gpgsign", "false")
        # Three commits across two fake dates (two on 06-10, one on 06-12).
        _commit(cls.repo, 100, "2026-06-10 12:00:00", "run: demo 2026-06-10-1200")
        _commit(cls.repo, 120, "2026-06-10 18:00:00", "run: demo 2026-06-10-1800")
        _commit(cls.repo, 150, "2026-06-12 12:00:00", "run: demo 2026-06-12-1200")

        cls.notrepo = os.path.join(cls._tmp, "plain-dir")
        os.makedirs(cls.notrepo)

    @classmethod
    def tearDownClass(cls):
        # Read-only law does not forbid removing our OWN tmp fixture (not a data
        # root); best-effort cleanup.
        import shutil

        shutil.rmtree(cls._tmp, ignore_errors=True)

    # --- is_git_root -------------------------------------------------------
    def test_is_git_root_true_for_repo_false_for_plain_dir(self):
        self.assertTrue(gittime.is_git_root(self.repo))
        self.assertFalse(gittime.is_git_root(self.notrepo))
        self.assertFalse(gittime.is_git_root(os.path.join(self._tmp, "nope")))

    # --- commit_at ---------------------------------------------------------
    def test_commit_at_picks_newest_at_or_before_each_date(self):
        # End of 06-10 -> the 18:00 commit (newest that day).
        sha10, committed10, subj10 = gittime.commit_at(self.repo, "2026-06-10")
        self.assertIsNotNone(sha10)
        self.assertEqual(subj10, "run: demo 2026-06-10-1800")
        self.assertTrue(committed10.startswith("2026-06-10"))

        # 06-11 has no commit -> still the 06-10 18:00 commit.
        sha11, _, subj11 = gittime.commit_at(self.repo, "2026-06-11")
        self.assertEqual(sha11, sha10)
        self.assertEqual(subj11, "run: demo 2026-06-10-1800")

        # End of 06-12 -> the newest commit overall.
        sha12, committed12, subj12 = gittime.commit_at(self.repo, "2026-06-12")
        self.assertNotEqual(sha12, sha10)
        self.assertEqual(subj12, "run: demo 2026-06-12-1200")
        self.assertTrue(committed12.startswith("2026-06-12"))

    def test_commit_at_returns_none_before_first_commit(self):
        sha, committed, subject = gittime.commit_at(self.repo, "2026-06-01")
        self.assertEqual((sha, committed, subject), (None, None, None))

    # --- show_file ---------------------------------------------------------
    def test_show_file_returns_the_version_at_that_commit(self):
        sha10, _, _ = gittime.commit_at(self.repo, "2026-06-10")
        sha12, _, _ = gittime.commit_at(self.repo, "2026-06-12")

        blob10 = gittime.show_file(self.repo, sha10, "platforms/demo/result.json")
        blob12 = gittime.show_file(self.repo, sha12, "platforms/demo/result.json")
        self.assertIsNotNone(blob10)
        self.assertIsNotNone(blob12)

        price10 = json.loads(blob10.decode("utf-8"))["allRows"][0]["sale"]
        price12 = json.loads(blob12.decode("utf-8"))["allRows"][0]["sale"]
        self.assertEqual(price10, 120)  # 06-10 18:00 variant
        self.assertEqual(price12, 150)  # 06-12 variant

    def test_show_file_missing_path_returns_none(self):
        sha12, _, _ = gittime.commit_at(self.repo, "2026-06-12")
        self.assertIsNone(
            gittime.show_file(self.repo, sha12, "platforms/demo/nope.json")
        )
        self.assertIsNone(gittime.show_file(self.repo, None, "anything"))

    # --- list_tree ---------------------------------------------------------
    def test_list_tree_lists_tracked_paths(self):
        sha12, _, _ = gittime.commit_at(self.repo, "2026-06-12")
        under = gittime.list_tree(self.repo, sha12, "platforms/")
        self.assertIn("platforms/demo/result.json", under)
        # prefix scoping: nothing outside platforms/ leaks in.
        self.assertTrue(all(p.startswith("platforms/") for p in under))
        # whole tree (no prefix) is a superset.
        self.assertIn("platforms/demo/result.json", gittime.list_tree(self.repo, sha12))

    def test_list_tree_missing_or_bad_sha_is_empty(self):
        self.assertEqual(gittime.list_tree(self.repo, None, "platforms/"), [])
        self.assertEqual(gittime.list_tree(self.repo, "deadbeef", "platforms/"), [])

    # --- sweep_log ---------------------------------------------------------
    def test_sweep_log_parses_all_commits_newest_first(self):
        log = gittime.sweep_log(self.repo)
        self.assertEqual(len(log), 3)
        self.assertEqual(log[0]["subject"], "run: demo 2026-06-12-1200")
        self.assertEqual(log[-1]["subject"], "run: demo 2026-06-10-1200")
        subjects = {c["subject"] for c in log}
        self.assertIn("run: demo 2026-06-10-1800", subjects)
        # dates parse out of --date=iso.
        self.assertEqual(log[0]["date"], "2026-06-12")
        self.assertTrue(log[0]["datetime"].startswith("2026-06-12"))
        # sha values are full-length hex commit ids.
        for c in log:
            self.assertRegex(c["sha"], r"^[0-9a-f]{40}$")

    def test_sweep_log_limit_and_day_filter(self):
        self.assertEqual(len(gittime.sweep_log(self.repo, limit=1)), 1)
        day = gittime.sweep_log(self.repo, since="2026-06-12", until="2026-06-12")
        # exact-day slice on the parsed date field (matches how `runs` narrows).
        day = [c for c in day if c["date"] == "2026-06-12"]
        self.assertEqual(len(day), 1)
        self.assertEqual(day[0]["subject"], "run: demo 2026-06-12-1200")

    # --- not-a-repo contract ----------------------------------------------
    def test_not_a_repo_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            gittime.commit_at(self.notrepo, "2026-06-10")
        self.assertIn("not a git checkout", str(ctx.exception))
        with self.assertRaises(FileNotFoundError):
            gittime.sweep_log(self.notrepo)
        with self.assertRaises(FileNotFoundError):
            gittime.show_file(self.notrepo, "deadbeef", "platforms/demo/result.json")

    def test_non_read_only_verb_is_refused(self):
        # Defensive: the module must never build a write verb.
        with self.assertRaises(ValueError):
            gittime._git(self.repo, "commit", "-m", "nope")
        with self.assertRaises(ValueError):
            gittime._git(self.repo, "checkout", "HEAD")


if __name__ == "__main__":
    unittest.main()
