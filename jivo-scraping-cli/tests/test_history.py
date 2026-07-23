"""Offline-deterministic tests for the 'history' family (sources + command).

Builds a throwaway ecom-intel root under a tmp dir with only
data/amazon/history.csv (copied from tests/fixtures/history-amazon.csv), points
util.ECOM at it, and exercises read_history() + the command. Never touches the
live clone.

The fixture deliberately uses VARIED headers
(run,obs_ts,marketplace,product_code,city,pin,sale_price,list_mrp,discount,availability)
to prove the defensive column discovery, and carries 6 rows: 5 well-formed
(one with an unparseable date, "NA") + 1 malformed short row (r6).
"""

import argparse
import contextlib
import datetime as _dt
import io
import json
import os
import shutil
import tempfile
import unittest

from jivo_scrape import util
from jivo_scrape.commands import history as history_cmd
from jivo_scrape.sources import histcsv

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "history-amazon.csv")


class HistoryBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jivo-hist-")
        amazon_dir = os.path.join(self.tmp, "data", "amazon")
        os.makedirs(amazon_dir)
        shutil.copyfile(FIXTURE, os.path.join(amazon_dir, "history.csv"))
        self._old_ecom = util.ECOM
        util.ECOM = self.tmp  # histcsv.history_path reads util.ECOM live

    def tearDown(self):
        util.ECOM = self._old_ecom
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestReadHistory(HistoryBase):
    def test_wellformed_rows_and_skipped_count(self):
        rows, freshness, notes = histcsv.read_history("amazon")
        # 6 fixture rows minus the one malformed short row -> 5 kept.
        self.assertEqual(len(rows), 5)
        self.assertEqual(notes["row_count"], 5)
        self.assertEqual(notes["skipped_rows"], 1)
        # no date filter => undated rows are not counted, and r5 ("NA") is kept.
        self.assertEqual(notes["undated_rows"], 0)
        self.assertIn("NA", [r["date"] for r in rows])

    def test_defensive_column_discovery(self):
        rows, _, _ = histcsv.read_history("amazon")
        r1 = next(r for r in rows if r["sku"] == "jivo-olive-1l" and r["date"] == "2026-05-01")
        self.assertEqual(r1["platform"], "amazon")
        self.assertEqual(r1["price"], "415")   # from 'sale_price'
        self.assertEqual(r1["mrp"], "1049")    # from 'list_mrp'
        self.assertEqual(r1["avail"], "in_stock")  # from 'availability'

    def test_freshness_present(self):
        _, freshness, _ = histcsv.read_history("amazon")
        self.assertIn("amazon", freshness)
        self.assertIsNotNone(freshness["amazon"])
        self.assertIn("mtime", freshness["amazon"])
        self.assertIn("age_minutes", freshness["amazon"])

    def test_sku_filter_is_case_insensitive_substring(self):
        rows, _, _ = histcsv.read_history("amazon", sku="OLIVE")
        self.assertEqual(len(rows), 2)  # r1 + r3
        self.assertTrue(all("olive" in r["sku"].lower() for r in rows))

    def test_date_from_filter_keeps_undated(self):
        rows, _, notes = histcsv.read_history(
            "amazon", date_from=_dt.date(2026, 6, 1)
        )
        # r3 (06-01) + r4 (06-20) in range, r5 ("NA") kept as undated => 3 rows.
        self.assertEqual(len(rows), 3)
        self.assertEqual(notes["undated_rows"], 1)
        self.assertEqual(notes["skipped_rows"], 1)
        dates = [r["date"] for r in rows]
        self.assertIn("2026-06-01", dates)
        self.assertIn("2026-06-20", dates)
        self.assertIn("NA", dates)
        self.assertNotIn("2026-05-01", dates)
        self.assertNotIn("2026-05-15", dates)

    def test_date_range_from_and_to(self):
        rows, _, notes = histcsv.read_history(
            "amazon",
            date_from=_dt.date(2026, 5, 10),
            date_to=_dt.date(2026, 6, 10),
        )
        # r2 (05-15) + r3 (06-01) in range; r1/r4 out; r5 undated kept => 3.
        dates = [r["date"] for r in rows]
        self.assertIn("2026-05-15", dates)
        self.assertIn("2026-06-01", dates)
        self.assertIn("NA", dates)
        self.assertNotIn("2026-05-01", dates)
        self.assertNotIn("2026-06-20", dates)
        self.assertEqual(notes["undated_rows"], 1)

    def test_iso_string_date_bounds_accepted(self):
        rows, _, _ = histcsv.read_history(
            "amazon", date_from="2026-06-01", date_to="2026-06-24"
        )
        # r3 (06-01) + r4 (06-20) + r5 undated => 3
        self.assertEqual(len(rows), 3)

    def test_all_platforms_notes_missing_csvs_without_crashing(self):
        rows, freshness, notes = histcsv.read_history("all")
        # only amazon has a csv in the tmp root.
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["platform"] == "amazon" for r in rows))
        self.assertIsNotNone(freshness["amazon"])
        # every platform is represented in freshness; the rest are None.
        for p in util.PLATFORMS:
            self.assertIn(p, freshness)
        self.assertIsNone(freshness["blinkit"])
        self.assertEqual(
            sorted(notes["missing_platforms"]),
            sorted(p for p in util.PLATFORMS if p != "amazon"),
        )
        self.assertTrue(
            any("no history.csv for" in m for m in notes["messages"])
        )


def _run(argv):
    """Build the real subparser, parse argv, run the command; return (rc, stdout)."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    history_cmd.register(sub)
    args = parser.parse_args(argv)
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, out.getvalue()


class TestHistoryCommand(HistoryBase):
    def test_human_table_renders(self):
        rc, stdout = _run(["history", "--platform", "amazon"])
        self.assertEqual(rc, 0)
        self.assertIn("DATE", stdout)
        self.assertIn("jivo-olive-1l", stdout)
        self.assertIn("of 5 row(s).", stdout)

    def test_json_envelope_meta(self):
        rc, stdout = _run(
            ["history", "--platform", "amazon", "--from", "2026-06-01", "--json"]
        )
        self.assertEqual(rc, 0)
        payload = json.loads(stdout)
        meta = payload["meta"]
        self.assertEqual(meta["command"], "history")
        self.assertEqual(meta["platform"], "amazon")
        self.assertEqual(meta["from"], "2026-06-01")
        self.assertEqual(meta["row_count"], 3)
        self.assertEqual(meta["skipped_rows"], 1)
        self.assertEqual(meta["undated_rows"], 1)
        self.assertIn("amazon", meta["freshness"])
        self.assertEqual(len(payload["results"]), 3)

    def test_limit_truncates_and_notes(self):
        rc, stdout = _run(
            ["history", "--platform", "amazon", "--limit", "2", "--json"]
        )
        self.assertEqual(rc, 0)
        payload = json.loads(stdout)
        meta = payload["meta"]
        self.assertEqual(meta["row_count"], 5)
        self.assertEqual(meta["shown"], 2)
        self.assertEqual(len(payload["results"]), 2)
        self.assertTrue(any("showing 2 of 5" in n for n in meta["notes"]))

    def test_missing_platform_all_degrades_gracefully(self):
        rc, stdout = _run(["history", "--platform", "all", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["meta"]["row_count"], 5)
        self.assertTrue(payload["meta"]["missing_platforms"])
        self.assertTrue(
            any("no history.csv for" in n for n in payload["meta"]["notes"])
        )

    def test_unknown_platform_exits_2(self):
        rc, _ = _run(["history", "--platform", "nosuch-platform"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
