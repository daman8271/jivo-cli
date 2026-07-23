"""Regression: a malformed CSV that makes csv raise mid-parse must be
skipped-and-counted, never crash the `history` command.

Covers the fix for the csv.Error escape: an unterminated quote / oversized field
in data/<platform>/history.csv used to raise ``_csv.Error`` out of
``csv.DictReader`` iteration (a subclass of Exception, NOT OSError), escaping
_read_one's ``except OSError`` and the dispatcher, so ONE corrupt platform file
crashed the whole run with a traceback + exit 1. Now the offending record is
skipped and counted; good records survive.

Everything runs against a throwaway tmp root — never the live clone — and the
oversized field is a genuine >field_size_limit field (no global csv state is
mutated), so the SAME csv.Error path the real repro hit is exercised.
"""

import argparse
import contextlib
import csv
import io
import json
import os
import shutil
import tempfile
import unittest

from jivo_scrape import util
from jivo_scrape.commands import history as history_cmd
from jivo_scrape.sources import histcsv

HEADER = (
    "run_id,date_ist,platform,canonical_sku,city,pincode,price,mrp,discount_pct,in_stock\n"
)
GOOD = "r%d,2026-06-%02d,amazon,jivo-canola-1l,mumbai,400001,415,1049,60,in_stock\n"
# A field guaranteed to exceed csv.field_size_limit() (stdlib default 131072),
# so csv raises "field larger than field limit" exactly like the real repro.
OVERSIZE = "x" * (csv.field_size_limit() + 5000)


def _write_history(root, body):
    d = os.path.join(root, "data", "amazon")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "history.csv"), "w", encoding="utf-8") as fh:
        fh.write(body)


def _run(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    history_cmd.register(sub)
    args = parser.parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, out.getvalue(), err.getvalue()


class MalformedBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jivo-hist-bad-")
        self._old_ecom = util.ECOM
        util.ECOM = self.tmp

    def tearDown(self):
        util.ECOM = self._old_ecom
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestOversizedFieldSkipped(MalformedBase):
    def test_oversized_last_row_is_skipped_not_raised(self):
        # 3 clean rows, then a stray unterminated quote whose quoted field runs
        # past the field-size limit -> csv.Error at EOF. The 3 good rows were
        # already yielded, so they survive; the corrupt record is counted.
        body = HEADER + (GOOD % (1, 1)) + (GOOD % (2, 2)) + (GOOD % (3, 3))
        body += 'r4,2026-06-04,amazon,"' + OVERSIZE + "\n"
        _write_history(self.tmp, body)

        rows, freshness, notes = histcsv.read_history("amazon")  # must NOT raise
        self.assertEqual(notes["row_count"], 3)
        self.assertEqual(len(rows), 3)
        self.assertGreaterEqual(notes["skipped_rows"], 1)
        # The file WAS readable — the platform is not marked unreadable.
        self.assertEqual(notes["unreadable_platforms"], [])
        self.assertIsNotNone(freshness["amazon"])

    def test_command_exit_zero_no_traceback(self):
        body = HEADER + (GOOD % (1, 1)) + 'r2,2026-06-02,amazon,"' + OVERSIZE + "\n"
        _write_history(self.tmp, body)
        rc, out, err = _run(["history", "--platform", "amazon"])
        self.assertEqual(rc, 0)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("Error", err)

    def test_platform_all_one_corrupt_file_does_not_crash_the_run(self):
        # The default --platform all loops every platform; one corrupt file must
        # not take down the whole run (this was the sharpest edge of the bug).
        body = HEADER + (GOOD % (1, 1)) + 'r2,2026-06-02,amazon,"' + OVERSIZE + "\n"
        _write_history(self.tmp, body)
        rc, out, err = _run(["history", "--platform", "all", "--json"])
        self.assertEqual(rc, 0)
        self.assertNotIn("Traceback", err)
        payload = json.loads(out)
        self.assertGreaterEqual(payload["meta"]["skipped_rows"], 1)
        self.assertEqual(payload["meta"]["unreadable_platforms"], [])

    def test_sku_filter_over_corrupt_file_does_not_crash(self):
        # The crash used to fire during csv iteration, BEFORE the sku filter ran.
        body = HEADER + (GOOD % (1, 1)) + 'r2,2026-06-02,amazon,"' + OVERSIZE + "\n"
        _write_history(self.tmp, body)
        rc, out, err = _run(["history", "--platform", "amazon", "--sku", "canola"])
        self.assertEqual(rc, 0)
        self.assertNotIn("Traceback", err)


class TestOversizedHeaderIsUnreadable(MalformedBase):
    def test_corrupt_header_marks_platform_unreadable_not_crash(self):
        # An oversized field in the HEADER line raises csv.Error when
        # reader.fieldnames is first accessed — outside the per-row guard. The
        # outer except must treat the file as unreadable rather than crash.
        body = '"' + OVERSIZE + "\nr1,2026-06-01,amazon,jivo,mumbai,400001,1,2,3,4\n"
        _write_history(self.tmp, body)
        rows, freshness, notes = histcsv.read_history("amazon")  # must NOT raise
        self.assertEqual(rows, [])
        self.assertIn("amazon", notes["unreadable_platforms"])
        self.assertTrue(
            any("unreadable" in m for m in notes["messages"]),
            notes["messages"],
        )


if __name__ == "__main__":
    unittest.main()
