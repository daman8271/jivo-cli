"""Offline tests for the vault/reports explorer (sources.vaultview + commands).

Everything runs against a throwaway tmp fixture tree — never the live clone — so
the suite is deterministic. Covers: list_notes listing / section / pattern /
newest-first, read_note content, the two traversal-escape refusals, and the
vault + reports commands (human table, --json envelope, --show passthrough).
"""

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from jivo_scrape import util  # noqa: E402
from jivo_scrape.commands import reports as reports_cmd  # noqa: E402
from jivo_scrape.commands import vault as vault_cmd  # noqa: E402
from jivo_scrape.sources import vaultview  # noqa: E402


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _touch(path, mtime):
    os.utime(path, (mtime, mtime))


def _parse(register, argv):
    """Exercise a command's register() through a real argparse round-trip."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register(sub)
    return parser.parse_args(argv)


def _capture(fn):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = fn()
    return rc, out.getvalue(), err.getvalue()


class BaseFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="vaultview-")
        self.addCleanup(self._cleanup)
        self.vault = os.path.join(self.tmp, "vault")
        # vault/daily/x.md (older) + vault/index.md (newer)
        _write(os.path.join(self.vault, "daily", "x.md"), "# daily note\nbody\n")
        _write(os.path.join(self.vault, "index.md"), "# index\nhome moc\n")
        _write(os.path.join(self.vault, "monthly", "2026-07.md"), "# month\n")
        _touch(os.path.join(self.vault, "daily", "x.md"), 1_000_000)
        _touch(os.path.join(self.vault, "monthly", "2026-07.md"), 2_000_000)
        _touch(os.path.join(self.vault, "index.md"), 3_000_000)  # newest
        # reports/run1/REPORT.md + SHA256SUMS
        self.reports = os.path.join(self.tmp, "reports")
        _write(os.path.join(self.reports, "run1", "REPORT.md"), "# run1 report\n")
        _write(os.path.join(self.reports, "run1", "SHA256SUMS"), "abc  REPORT.md\n")
        # a run dir with NO report — must be excluded from the listing
        _write(os.path.join(self.reports, "run0-no-report", "notes.txt"), "x\n")
        # docs/coverage-runs/c.md
        self.coverage = os.path.join(self.tmp, "docs", "coverage-runs")
        _write(os.path.join(self.coverage, "c.md"), "# coverage doc\n")

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)


class TestListNotes(BaseFixture):
    def test_lists_all_note_files(self):
        entries = vaultview.list_notes(self.vault)
        rels = {e["relpath"] for e in entries}
        self.assertEqual(
            rels,
            {"index.md", os.path.join("daily", "x.md"), os.path.join("monthly", "2026-07.md")},
        )
        for e in entries:
            self.assertIn("size", e)
            self.assertIn("mtime", e)

    def test_newest_first_order(self):
        rels = [e["relpath"] for e in vaultview.list_notes(self.vault)]
        # index.md (mtime 3e6) > monthly (2e6) > daily/x.md (1e6)
        self.assertEqual(
            rels,
            ["index.md", os.path.join("monthly", "2026-07.md"), os.path.join("daily", "x.md")],
        )

    def test_section_narrows(self):
        entries = vaultview.list_notes(self.vault, section="daily")
        self.assertEqual([e["relpath"] for e in entries], [os.path.join("daily", "x.md")])

    def test_pattern_filters(self):
        entries = vaultview.list_notes(self.vault, pattern="index")
        self.assertEqual([e["relpath"] for e in entries], ["index.md"])

    def test_pattern_is_case_insensitive(self):
        self.assertEqual(len(vaultview.list_notes(self.vault, pattern="INDEX")), 1)

    def test_missing_root_is_empty(self):
        self.assertEqual(vaultview.list_notes(os.path.join(self.tmp, "nope")), [])

    def test_missing_section_is_empty(self):
        self.assertEqual(vaultview.list_notes(self.vault, section="platforms"), [])


class TestReadNote(BaseFixture):
    def test_reads_content(self):
        self.assertEqual(vaultview.read_note(self.vault, "index.md"), "# index\nhome moc\n")

    def test_reads_nested(self):
        self.assertIn("daily note", vaultview.read_note(self.vault, os.path.join("daily", "x.md")))

    def test_relative_traversal_refused(self):
        with self.assertRaises(ValueError) as cm:
            vaultview.read_note(self.vault, "../../etc/passwd")
        self.assertIn("escapes root", str(cm.exception))

    def test_absolute_path_refused(self):
        with self.assertRaises(ValueError) as cm:
            vaultview.read_note(self.vault, "/etc/passwd")
        self.assertIn("escapes root", str(cm.exception))

    def test_missing_note_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            vaultview.read_note(self.vault, "nope.md")

    def test_directory_target_raises_isadirectory(self):
        # An in-root relpath that resolves to a DIRECTORY must raise a clean
        # IsADirectoryError (dispatcher -> exit 3), not let open() spill a
        # traceback. '.' is the base dir itself; 'daily' is a subdir.
        with self.assertRaises(IsADirectoryError):
            vaultview.read_note(self.vault, ".")
        with self.assertRaises(IsADirectoryError):
            vaultview.read_note(self.vault, "daily")


class TestVaultCommand(BaseFixture):
    def _run(self, argv):
        args = _parse(vault_cmd.register, argv)
        with mock.patch.object(util, "ECOM", self.tmp):
            return _capture(lambda: vault_cmd.run(args))

    def test_human_listing(self):
        rc, out, err = self._run(["vault"])
        self.assertEqual(rc, 0)
        self.assertIn("index.md", out)
        self.assertIn("MODIFIED", out)
        self.assertIn("3 note(s)", out)

    def test_json_envelope(self):
        rc, out, err = self._run(["vault", "--json"])
        env = json.loads(out)
        self.assertEqual(env["meta"]["command"], "vault")
        self.assertEqual(env["meta"]["count"], 3)
        self.assertIsNotNone(env["meta"]["freshness"]["vault/index.md"])
        rels = [n["relpath"] for n in env["results"]["notes"]]
        self.assertEqual(rels[0], "index.md")  # newest-first preserved in JSON

    def test_section_and_name_flags(self):
        rc, out, err = self._run(["vault", "--section", "daily", "--json"])
        env = json.loads(out)
        self.assertEqual(env["meta"]["section"], "daily")
        self.assertEqual(env["meta"]["count"], 1)

    def test_show_passthrough(self):
        rc, out, err = self._run(["vault", "--show", "index.md"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "# index\nhome moc\n")

    def test_show_escape_raises_valueerror(self):
        # bubbles to the dispatcher, which maps it to exit 2
        args = _parse(vault_cmd.register, ["vault", "--show", "../../etc/passwd"])
        with mock.patch.object(util, "ECOM", self.tmp):
            with self.assertRaises(ValueError):
                vault_cmd.run(args)

    def test_show_directory_raises_isadirectory(self):
        # bubbles to the dispatcher, which maps it to exit 3 (no traceback)
        args = _parse(vault_cmd.register, ["vault", "--show", "daily"])
        with mock.patch.object(util, "ECOM", self.tmp):
            with self.assertRaises(IsADirectoryError):
                vault_cmd.run(args)

    def test_absent_vault_noted(self):
        args = _parse(vault_cmd.register, ["vault", "--json"])
        empty = os.path.join(self.tmp, "empty-root")
        os.makedirs(empty)
        with mock.patch.object(util, "ECOM", empty):
            rc, out, err = _capture(lambda: vault_cmd.run(args))
        env = json.loads(out)
        self.assertEqual(env["meta"]["count"], 0)
        self.assertTrue(any("vault/ absent" in n for n in env["meta"]["notes"]))


class TestReportsCommand(BaseFixture):
    def _run(self, argv):
        args = _parse(reports_cmd.register, argv)
        with mock.patch.object(util, "ECOM", self.tmp):
            return _capture(lambda: reports_cmd.run(args))

    def test_human_listing_merges_families(self):
        rc, out, err = self._run(["reports"])
        self.assertEqual(rc, 0)
        self.assertIn(os.path.join("reports", "run1", "REPORT.md"), out)
        self.assertIn(os.path.join("docs", "coverage-runs", "c.md"), out)
        self.assertIn("1 run(s) + 1 coverage doc(s)", out)
        # the run dir without a REPORT.md must not appear
        self.assertNotIn("run0-no-report", out)

    def test_json_envelope_shape(self):
        rc, out, err = self._run(["reports", "--json"])
        env = json.loads(out)
        self.assertEqual(env["meta"]["command"], "reports")
        self.assertEqual(env["meta"]["count"], 2)
        self.assertEqual(
            env["meta"]["roots_present"], {"reports": True, "coverage": True}
        )
        run = env["results"]["runs"][0]
        self.assertEqual(run["dirname"], "run1")
        self.assertTrue(run["sha256sums"])  # SHA256SUMS detected

    def test_name_filter(self):
        rc, out, err = self._run(["reports", "--name", "coverage", "--json"])
        env = json.loads(out)
        self.assertEqual(env["meta"]["count"], 1)
        self.assertEqual(env["results"]["runs"], [])
        self.assertEqual(len(env["results"]["coverage"]), 1)

    def test_show_report(self):
        rc, out, err = self._run(
            ["reports", "--show", os.path.join("reports", "run1", "REPORT.md")]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out, "# run1 report\n")

    def test_show_coverage_doc(self):
        rc, out, err = self._run(
            ["reports", "--show", os.path.join("docs", "coverage-runs", "c.md")]
        )
        self.assertEqual(out, "# coverage doc\n")

    def test_show_escape_raises_valueerror(self):
        args = _parse(reports_cmd.register, ["reports", "--show", "../../etc/passwd"])
        with mock.patch.object(util, "ECOM", self.tmp):
            with self.assertRaises(ValueError):
                reports_cmd.run(args)

    def test_show_directory_raises_isadirectory(self):
        # reports --show on an in-root directory -> IsADirectoryError (exit 3)
        args = _parse(
            reports_cmd.register, ["reports", "--show", os.path.join("docs", "coverage-runs")]
        )
        with mock.patch.object(util, "ECOM", self.tmp):
            with self.assertRaises(IsADirectoryError):
                reports_cmd.run(args)

    def test_absent_roots_noted(self):
        args = _parse(reports_cmd.register, ["reports", "--json"])
        empty = os.path.join(self.tmp, "bare-root")
        os.makedirs(empty)
        with mock.patch.object(util, "ECOM", empty):
            rc, out, err = _capture(lambda: reports_cmd.run(args))
        env = json.loads(out)
        self.assertEqual(env["meta"]["count"], 0)
        self.assertEqual(
            env["meta"]["roots_present"], {"reports": False, "coverage": False}
        )
        self.assertEqual(len(env["meta"]["notes"]), 2)


if __name__ == "__main__":
    unittest.main()
