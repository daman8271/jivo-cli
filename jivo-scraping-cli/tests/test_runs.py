"""Regression: `runs --date <today's calendar date>` must return that single
day's ledger, not the recent-N view.

util.resolve_date() collapses an explicit YYYY-MM-DD that equals the current
date back to the label "today". runs.py used to derive day-vs-recent from that
collapsed label (``day_mode = label != "today"``), so an explicit current-day
request silently widened into "recent N overall" and leaked prior days'
commits. The fix keys off the RAW --date spec instead. This test builds a tmp
git repo with commits on today AND on a fixed past date and asserts the slice.

Offline-deterministic: a throwaway git repo (the git writes are confined to the
tmp fixture, never a data root). Commit timestamps carry no explicit tz so git
interprets them in the same local timezone that date.today() reports, keeping
the day-slice stable.
"""

import argparse
import contextlib
import datetime as _dt
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
from jivo_scrape.commands import runs as runs_cmd  # noqa: E402


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


def _capture(fn):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn()
    return rc, out.getvalue(), err.getvalue()


class RunsDayModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.today = _dt.date.today()
        cls.past = cls.today - _dt.timedelta(days=3)
        cls._tmp = tempfile.mkdtemp(prefix="runs-fixture-")
        cls.repo = os.path.join(cls._tmp, "ecom-intel")
        os.makedirs(cls.repo)
        _git(cls.repo, "init", "-q")
        _git(cls.repo, "config", "user.email", "fixture@example.test")
        _git(cls.repo, "config", "user.name", "Fixture Bot")
        _git(cls.repo, "config", "commit.gpgsign", "false")
        # Two commits on the PAST day, then two on TODAY (no explicit tz so the
        # committer date's calendar day matches date.today()'s local day).
        cls._commit(cls.past, "12:00:00", "run: past-noon")
        cls._commit(cls.past, "18:00:00", "run: past-eve")
        cls._commit(cls.today, "12:00:00", "run: today-noon")
        cls._commit(cls.today, "18:00:00", "run: today-eve")

    @classmethod
    def _commit(cls, day, hhmmss, subject):
        marker = os.path.join(cls.repo, "sweep.txt")
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (subject, day.isoformat()))
        _git(cls.repo, "add", "-A")
        stamp = "%s %s" % (day.isoformat(), hhmmss)  # local tz, matches today()
        _git(
            cls.repo,
            "commit",
            "-q",
            "-m",
            subject,
            env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _run(self, argv):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        runs_cmd.register(sub)
        args = parser.parse_args(argv)
        with mock.patch.object(util, "ECOM", self.repo):
            rc, out, err = _capture(lambda: runs_cmd.run(args))
        return rc, json.loads(out)

    def test_explicit_current_date_is_single_day_slice(self):
        # THE FIX: explicit today-as-YYYY-MM-DD -> mode "day", only today's runs.
        rc, env = self._run(["runs", "--date", self.today.isoformat(), "--json"])
        self.assertEqual(rc, 0)
        self.assertEqual(env["meta"]["mode"], "day")
        commits = env["results"]["commits"]
        self.assertEqual(len(commits), 2)
        self.assertTrue(all(c["date"] == self.today.isoformat() for c in commits))
        subjects = {c["subject"] for c in commits}
        self.assertEqual(subjects, {"run: today-noon", "run: today-eve"})
        # No prior-day commit leaks in (that was the bug).
        self.assertNotIn(self.past.isoformat(), {c["date"] for c in commits})

    def test_past_date_still_day_slices(self):
        # CONTROL: a genuinely past date already worked and must keep working.
        rc, env = self._run(["runs", "--date", self.past.isoformat(), "--json"])
        self.assertEqual(env["meta"]["mode"], "day")
        commits = env["results"]["commits"]
        self.assertEqual(len(commits), 2)
        self.assertTrue(all(c["date"] == self.past.isoformat() for c in commits))

    def test_default_no_date_is_recent(self):
        # CONTROL: bare `runs` stays the recent-N overall view (all 4 commits).
        rc, env = self._run(["runs", "--json"])
        self.assertEqual(env["meta"]["mode"], "recent")
        self.assertEqual(env["meta"]["commit_count"], 4)

    def test_today_keyword_stays_recent(self):
        # The literal "today" keyword means "no specific day" -> recent, distinct
        # from an explicit YYYY-MM-DD that happens to equal today.
        rc, env = self._run(["runs", "--date", "today", "--json"])
        self.assertEqual(env["meta"]["mode"], "recent")
        self.assertEqual(env["meta"]["commit_count"], 4)


if __name__ == "__main__":
    unittest.main()
