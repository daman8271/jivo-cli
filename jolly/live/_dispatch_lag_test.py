#!/usr/bin/env python3
"""Unit tests for live/dispatch_lag.py.

    cd jolly && python3 -m unittest live._dispatch_lag_test -v

NO NETWORK, no factory login, no CLI binary: `_run` is replaced with canned payloads in
the shape the live endpoint actually returns (verified 2026-09-06: `--page` switches
`gate-core sales-dispatch` from a bare array to `{count, num_pages, page, page_size,
results}`, wrapped again by the CLI in `{meta, results}`; numbers come back as STRINGS;
every row carries `driver_name`, `driver_mobile_no`, `vehicle_no` and `document_numbers`).

The assertions are the traps, not the happy path:
  * the median, p90 and max are the lag in whole days, off gate_out_date - sap_doc_date
  * a row that is not DISPATCHED measures nothing and is not counted as a dispatch
  * a DISPATCHED row missing either date lands in undated_rows, never as a zero-day lag
  * the three books stay three: JIVO_OIL is not the merged figure
  * paging stops at num_pages, and the page cap sets `truncated`
  * NO plate, driver, customer, bill number or mobile reaches the written file
  * the mask runs on the way to disk
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
_JOLLY = os.path.dirname(_HERE)
if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)

from live import dispatch_lag as dl  # noqa: E402


# --------------------------------------------------------------- payloads ---
def gate_row(doc_date, out_date, company="JIVO_OIL", status="DISPATCHED", **over):
    """One `gate-core sales-dispatch` row, with every field we must NOT publish on it."""
    row = {
        "id": 1502, "entry_no": "DOCK-20260905-0013",
        "company": 1, "company_code": company, "company_name": "Jivo Oil",
        "status": status,
        "sap_doc_date": doc_date, "gate_out_date": out_date,
        "dispatched_at": (out_date + "T22:08:36.406855+05:30") if out_date else None,
        "updated_at": "2026-09-05T22:09:00+05:30",
        "sap_doc_num": "626080722, 626080734", "document_numbers": ["626080722", "626080734"],
        "sap_doc_total": "1614054.00", "total_litres": "8368.000", "total_boxes": "490.000",
        "vehicle_no": "HR67C1036", "driver_name": "Sompal 8295058874",
        "driver_mobile_no": "9876543210", "driver_license_no": "DL0420110149646",
        "customer_name": "AGGARWAL AGENCIES", "customer_code": "CUSTA000981",
        "gatepass_no": "GP-2026-5640", "eway_bill": "352327874892",
    }
    row.update(over)
    return row


def page(rows, page_no=1, num_pages=1, count=None):
    """The CLI envelope around the endpoint's own --page envelope."""
    return {"meta": {"source": "live"},
            "results": {"count": count if count is not None else len(rows),
                        "num_pages": num_pages, "page": page_no,
                        "page_size": dl.PAGE_SIZE, "results": list(rows)}}


def runner_for(*payloads):
    """A stand-in for factory_dispatch._run that serves the canned pages in order."""
    seen = []

    def run(name, args, timeout=None):
        seen.append(args)
        i = len(seen) - 1
        if i >= len(payloads):
            return None, {"name": name, "ok": False, "ms": 1, "args": " ".join(args),
                          "error": "no such page"}
        return payloads[i], {"name": name, "ok": True, "ms": 1, "args": " ".join(args),
                             "error": None}

    run.seen = seen
    return run


# ------------------------------------------------------------------ tests ---
class Stats(unittest.TestCase):
    def test_empty_is_null_not_zero(self):
        s = dl.stats([])
        self.assertEqual(s["n"], 0)
        for k in ("median_days", "p90_days", "max_days", "mean_days"):
            self.assertIsNone(s[k], k)

    def test_median_p90_max_mean(self):
        s = dl.stats([0, 1, 1, 2, 2, 2, 3, 6, 9, 14])
        self.assertEqual(s["median_days"], 2)
        self.assertEqual(s["p90_days"], 9)         # nearest rank: the 9th of 10
        self.assertEqual(s["max_days"], 14)
        self.assertEqual(s["mean_days"], 4.0)
        self.assertEqual(s["n"], 10)

    def test_even_median_is_the_midpoint(self):
        self.assertEqual(dl.stats([1, 4])["median_days"], 2.5)


class RowLag(unittest.TestCase):
    def test_dispatched_row_measures_the_gap(self):
        lag, co = dl.row_lag(gate_row("2026-08-31", "2026-09-05"))
        self.assertEqual((lag, co), (5, "JIVO_OIL"))

    def test_not_dispatched_is_not_a_dispatch(self):
        self.assertEqual(dl.row_lag(gate_row("2026-09-01", "2026-09-02", status="PENDING")),
                         (None, None))

    def test_missing_document_date_is_undated_not_zero(self):
        lag, co = dl.row_lag(gate_row(None, "2026-09-05"))
        self.assertIsNone(lag)
        self.assertEqual(co, "JIVO_OIL")

    def test_gate_out_falls_back_to_the_dispatch_stamp(self):
        row = gate_row("2026-09-01", "2026-09-04")
        row["gate_out_date"] = None                  # only the timestamp survives
        self.assertEqual(dl.row_lag(row)[0], 3)


class Summarise(unittest.TestCase):
    def rows(self):
        return [
            gate_row("2026-09-01", "2026-09-02"),                       # oil, 1
            gate_row("2026-08-30", "2026-09-05"),                       # oil, 6
            gate_row("2026-09-03", "2026-09-03"),                       # oil, 0
            gate_row("2026-08-20", "2026-09-05", company="JIVO_BEVERAGES"),   # bev, 16
            gate_row("2026-09-04", "2026-09-05", status="DOCKED"),      # not a dispatch
            gate_row(None, "2026-09-05"),                               # undated
            gate_row("2026-09-06", "2026-09-05"),                       # back-dated, -1
        ]

    def test_counts_and_split(self):
        d = dl.summarise(self.rows(), date(2026, 8, 7), date(2026, 9, 6), 1, False)
        self.assertEqual(d["rows"], 7)
        self.assertEqual(d["dispatched_rows"], 6)     # the DOCKED row is not one
        self.assertEqual(d["undated_rows"], 1)
        self.assertEqual(d["negative_rows"], 1)
        self.assertEqual(d["all"]["n"], 5)
        self.assertEqual(d["all"]["max_days"], 16)
        # Oil is the split, never the headline: the 16-day Beverages row is not Oil's.
        self.assertEqual(d["by_company"]["JIVO_OIL"]["n"], 4)
        self.assertEqual(d["by_company"]["JIVO_OIL"]["max_days"], 6)
        self.assertEqual(d["by_company"]["JIVO_BEVERAGES"]["n"], 1)
        # a book that did nothing reads as n=0, it does not vanish
        self.assertEqual(d["by_company"]["JIVO_MART"]["n"], 0)

    def test_histogram_is_days_to_rows(self):
        d = dl.summarise(self.rows(), date(2026, 8, 7), date(2026, 9, 6), 1, False)
        self.assertEqual(d["histogram"], {"-1": 1, "0": 1, "1": 1, "6": 1, "16": 1})

    def test_window_and_static_flag(self):
        d = dl.summarise([], date(2026, 8, 7), date(2026, 9, 6), 1, False)
        self.assertEqual(d["window"], {"from": "2026-08-07", "to": "2026-09-06", "days": 31})
        self.assertIs(d["static"], False)            # this one is measured, not carried


class Paging(unittest.TestCase):
    def test_stops_at_num_pages(self):
        run = runner_for(page([gate_row("2026-09-01", "2026-09-02")] * 2, 1, 2),
                         page([gate_row("2026-09-01", "2026-09-03")] * 2, 2, 2))
        env = dl.measure(today=date(2026, 9, 6), runner=run)
        self.assertEqual(env["data"]["pages_read"], 2)
        self.assertEqual(len(run.seen), 2)
        self.assertFalse(env["data"]["truncated"])
        self.assertEqual(env["data"]["all"]["n"], 4)

    def test_page_cap_sets_truncated(self):
        run = runner_for(*[page([gate_row("2026-09-01", "2026-09-02")], p, 99)
                           for p in range(1, 5)])
        env = dl.measure(today=date(2026, 9, 6), runner=run, max_pages=3)
        self.assertEqual(env["data"]["pages_read"], 3)
        self.assertTrue(env["data"]["truncated"])
        self.assertTrue(any("cap" in e for e in env["data"]["errors"]))

    def test_a_body_this_reader_cannot_read_is_not_zero_rows(self):
        run = runner_for({"meta": {"source": "live"}, "results": {"detail": "nope"}})
        env = dl.measure(today=date(2026, 9, 6), runner=run)
        self.assertTrue(env["data"]["truncated"])
        self.assertFalse(env["ok"])
        self.assertEqual(env["data"]["all"]["n"], 0)
        self.assertIsNone(env["data"]["all"]["median_days"])

    def test_the_window_is_the_last_30_days(self):
        run = runner_for(page([gate_row("2026-09-01", "2026-09-02")]))
        env = dl.measure(today=date(2026, 9, 6), runner=run)
        self.assertIn("--from-date", run.seen[0])
        self.assertEqual(run.seen[0][run.seen[0].index("--from-date") + 1], "2026-08-07")
        self.assertEqual(run.seen[0][run.seen[0].index("--to-date") + 1], "2026-09-06")
        self.assertEqual(env["data"]["window"]["days"], 31)


class WhatReachesDisk(unittest.TestCase):
    FORBIDDEN = ("HR67C1036", "Sompal", "8295058874", "9876543210", "626080722",
                 "AGGARWAL", "CUSTA000981", "DL0420110149646", "352327874892",
                 "GP-2026-5640")

    def test_no_identifier_survives_into_the_file(self):
        run = runner_for(page([gate_row("2026-09-01", "2026-09-02"),
                               gate_row("2026-08-30", "2026-09-05",
                                        company="JIVO_BEVERAGES")]))
        env = dl.measure(today=date(2026, 9, 6), runner=run)
        with tempfile.TemporaryDirectory() as tmp:
            path = dl.write(env, os.path.join(tmp, "dispatch_lag.json"))
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        for bad in self.FORBIDDEN:
            self.assertNotIn(bad, text, "%s reached the published file" % bad)
        # and it is still a usable measurement
        doc = json.loads(text)
        self.assertEqual(doc["source"], "dispatch_lag")
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["data"]["all"]["n"], 2)

    def test_the_mask_runs_on_the_way_to_disk(self):
        env = dl.measure(today=date(2026, 9, 6), runner=runner_for(page([])))
        # a CLI error string is the one place a number can still ride out
        env["data"]["errors"] = ["page 1: exit 4, driver 9876543210 not found"]
        with tempfile.TemporaryDirectory() as tmp:
            path = dl.write(env, os.path.join(tmp, "dispatch_lag.json"))
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        self.assertNotIn("9876543210", text)
        self.assertIn("••••10", text)

    def test_no_rows_is_not_ok_and_says_why(self):
        env = dl.measure(today=date(2026, 9, 6), runner=runner_for(page([])))
        self.assertFalse(env["ok"])
        self.assertTrue(env["error"])
        self.assertEqual(env["data"]["all"]["n"], 0)

    def test_a_failed_page_may_not_echo_the_gate_body_onto_disk(self):
        """The one channel the row-level test above does not close (found 2026-09-06).

        `factory_dispatch._run` puts up to 300 characters of the CLI's own stdout into
        `record["error"]` whenever the CLI exits non-zero, and `_sanitize` only removes
        JWTs and runs of 10+ digits. `read_pages` copies that string verbatim into BOTH
        `data.errors` and `data.calls[].error`, and `mask_phones` only masks
        phone-SHAPED runs. Nothing in the chain decides what may be published — the
        CLI's own key order and pretty-printing do.

        Measured against the live CLI on 2026-09-06 (indented JSON, `--page-size 2`):
        the plate sits at character 2,484, the driver at 2,716 and the customer at
        1,451, so they fall outside the 300-character window today. `entry_no` sits at
        character 181 and does not. So the file that will run daily on a public-facing
        box publishes a gate/dock reference out of a failed page, and one change to the
        CLI's formatting or field order moves the plate into that window.

        The fix belongs in dispatch_lag.py, not here: describe a failed body with
        `factory_history._shape_of` — which names KEYS and never contents, and which
        this file already imports for the unrecognised-shape case — instead of
        publishing the CLI's stdout.
        """
        from live.adapters.factory_dispatch import _sanitize

        # the CLI pretty-prints, so this is the shape a real failure would echo
        body = json.dumps(page([gate_row("2026-09-01", "2026-09-03")]), indent=2)

        def failing_runner(name, args, timeout=None):
            return None, {"name": name, "args": " ".join(args), "ok": False, "ms": 12,
                          "error": _sanitize("exit 4: " + body[:300])}

        env = dl.measure(today=date(2026, 9, 6), runner=failing_runner)
        with tempfile.TemporaryDirectory() as tmp:
            path = dl.write(env, os.path.join(tmp, "dispatch_lag.json"))
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        self.assertNotIn("DOCK-20260905-0013", text,
                         "a gate reference rode out of a FAILED page's error string")
        for bad in self.FORBIDDEN:
            self.assertNotIn(bad, text,
                             "%s rode out of a FAILED page's error string" % bad)
        # and the failure is still legible: the exit code and the timing survive
        self.assertIn("exited 4", text)
        env = json.loads(text)
        self.assertEqual(env["data"]["calls"][0]["seconds"], 0.012)
        self.assertFalse(env["data"]["calls"][0]["ok"])


class SafeError(unittest.TestCase):
    """`_safe_error` is the thing that decides what a failed page may say."""

    def test_a_parseable_body_is_described_by_its_keys_only(self):
        body = json.dumps(page([gate_row("2026-09-01", "2026-09-03")]))
        said = dl._safe_error({"error": "exit 4: " + body})
        self.assertIn("exited 4", said)
        # _shape_of names the keys of the endpoint envelope and stops there
        self.assertIn("an object with keys count", said)
        for bad in WhatReachesDisk.FORBIDDEN + ("DOCK-20260905-0013", "Jivo Oil"):
            self.assertNotIn(bad, said, "%s survived _safe_error" % bad)

    def test_a_truncated_body_publishes_only_its_length(self):
        body = json.dumps(page([gate_row("2026-09-01", "2026-09-03")]), indent=2)[:300]
        said = dl._safe_error({"error": "exit 4: " + body})
        self.assertIn("exited 4", said)
        self.assertIn("could not parse", said)
        self.assertNotIn("DOCK", said)

    def test_a_timeout_and_a_missing_cli_stay_verbatim(self):
        for text in ("timed out after 30s", "CLI not found at /opt/jivo/factory-cli"):
            self.assertEqual(dl._safe_error({"error": text}), text)

    def test_an_exception_publishes_its_type_and_not_its_message(self):
        said = dl._safe_error({"error": "JSONDecodeError: Expecting value at DOCK-2026"})
        self.assertIn("JSONDecodeError", said)
        self.assertNotIn("DOCK-2026", said)

    def test_anything_unrecognised_is_not_published_at_all(self):
        said = dl._safe_error({"error": "HR67C1036 AGGARWAL AGENCIES"})
        self.assertNotIn("HR67C1036", said)
        self.assertNotIn("AGGARWAL", said)

    def test_a_page_that_did_not_fail_says_nothing(self):
        self.assertIsNone(dl._safe_error({"ok": True, "error": None}))


if __name__ == "__main__":
    unittest.main()
