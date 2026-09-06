#!/usr/bin/env python3
"""Unit tests for the MARK 4 half of live/freeze_live.py.

    cd jolly && python3 -m unittest live._freeze_mark4_test -v

NO NETWORK and no login. The pure functions are driven with hand-built inputs; the one
end-to-end test runs the real `build()` against the state files already on disk
(`live/state/`, written by the loop) and the TRACKED baseline fixture
(`live/fixtures/demand_baseline.json`), writing to a temp path. It skips itself, with a
sentence saying how to fix it, when there is no state.json to read.

The assertions are the traps Mark 3 fell into, not the happy path:
  * expected demand is shaped over FIVE week-of-month buckets, not four — bucket 5 is
    days 29-31 and it is 6.6x bucket 1, which is the whole reason R17 exists
  * a SKU that did not sell in every month of the window takes the POOLED shape
  * the real trade book is netted off and FLOORS AT ZERO; e-com is never netted
  * every FORECAST row is triple-tagged and says which basis shaped it
  * the lag is the daily file when it is fresh and the static 3 Sep note when it is not,
    and it SAYS WHICH
  * pendency is NULL with a reason when no day carries a gate figure — never 0
  * the money split names the rate that priced each rupee, and A10 prices the new carton
    code as the product it is
  * `lines` carries the rulebook's slots: Tin Head has 15L/3L/5L and NOTHING that is not
    a tin line carries a 15L key at all (AC02)
  * rules.shift_hours is 10 and rules.efficiency is 1.0 (A01/AC04)
"""

from __future__ import annotations

import contextlib
import io
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

from live import freeze_live as fz  # noqa: E402

STATE_DIR = os.path.join(_HERE, "state")
FIXTURE = os.path.join(_HERE, "fixtures", "demand_baseline.json")


# --------------------------------------------------------------- fixtures ---
def a_baseline(**over):
    """The shape live/demand_baseline_sap.py writes, cut down to two SKUs."""
    data = {
        "window": {"from": "2026-06-01", "to": "2026-08-31", "months": 3},
        "channel_field": "OCRD.U_Main_Group",
        "channels_included": ["GT", "MT"],
        "channels_excluded": ["E-COMMERCE"],
        "intercompany_excluded": ["CUSTA000606"],
        "by_channel": {"GT": {"litres": 600, "inr": 60000, "lines": 2}},
        "week_of_month": {"1": {"days": 21, "litres": 60, "litres_per_day": 3, "share": 0.10},
                          "2": {"days": 21, "litres": 60, "litres_per_day": 3, "share": 0.10},
                          "3": {"days": 21, "litres": 60, "litres_per_day": 3, "share": 0.10},
                          "4": {"days": 21, "litres": 120, "litres_per_day": 6, "share": 0.20},
                          "5": {"days": 8, "litres": 300, "litres_per_day": 37, "share": 0.50}},
        "skus": {
            # sold in all three months -> its OWN shape, everything in bucket 5
            "FGA": {"name": "A 1 LTR", "sku": "1 LTR", "type": "PREMIUM", "sub_group": "OLIVE",
                    "litres_per_piece": 1.0, "litres_per_month": 300, "inr_per_month": 60000,
                    "months_seen": 3, "by_week": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 900},
                    "in_plan_sheet": True},
            # seen once -> the POOLED shape
            "FGB": {"name": "B 5 LTR", "sku": "5 LTR", "type": "COMMODITY", "sub_group": "MUSTARD",
                    "litres_per_piece": 5.0, "litres_per_month": 100, "inr_per_month": 15000,
                    "months_seen": 1, "by_week": {"1": 300, "2": 0, "3": 0, "4": 0, "5": 0},
                    "in_plan_sheet": True},
        },
        "totals": {"litres": 1200, "inr": 225000, "lines": 4, "skus": 2},
        "basis": "SAP OINV/INV1 minus ORIN/RIN1, Oil book",
    }
    data.update(over)
    return data


def a_plan():
    return {"FGA": {"code": "FGA", "sku": "A 1 LTR", "head": "PREMIUM", "category": "OLIVE",
                    "pack_type": "PET", "litres_per_piece": 1.0, "pieces": 1000, "litres": 1000},
            "FGB": {"code": "FGB", "sku": "B 5 LTR", "head": "COMMODITY", "category": "MUSTARD",
                    "pack_type": "PET", "litres_per_piece": 5.0, "pieces": 200, "litres": 1000}}


def lag_envelope_data(median=3, p90=11, mx=40, mean=4.2, n=131, oil=True):
    """A daily lag file. `median`/`p90`/… are JIVO OIL's — the book the plan runs on
    (freeze_live.PLAN_BOOK) — because that is the one the engine is fed. The merged
    all-books gate is deliberately DIFFERENT here (2 d / p90 9, the real 6 Sep shape),
    so a test that gets 2 back has silently taken the headline instead of Oil's."""
    oil_block = {"median_days": median, "p90_days": p90, "max_days": mx,
                 "mean_days": mean, "n": n}
    return {"window": {"from": "2026-08-07", "to": "2026-09-06", "days": 31},
            "rows": 551, "dispatched_rows": 551, "undated_rows": 0, "pages_read": 6,
            "truncated": False, "measured_on": "2026-09-06", "static": False,
            "all": {"median_days": 2, "p90_days": 9, "max_days": 43,
                    "mean_days": 3.64, "n": 551},
            "by_company": dict(
                {"JIVO_BEVERAGES": {"median_days": 2, "p90_days": 7, "max_days": 43,
                                    "mean_days": 2.83, "n": 313}},
                **({"JIVO_OIL": oil_block} if oil else {})),
            "method": "gate log", "caveat": "the gate log, not the invoice book"}


STATIC_NOTE = {"median_days": 2, "mean_days": 2.93, "p90_days": 6, "max_days": 14,
               "rows": 96, "measured_window": "2026-08-15..2026-09-03",
               "measured_on": "2026-09-03", "method": "page 1 of 4", "caveat": "…",
               "static": True}


# --------------------------------------------------------- expected stream ---
class ExpectedStream(unittest.TestCase):
    def run_it(self, oms=None, baseline=None, plan=None):
        return fz.expected_stream(baseline or a_baseline(), plan or a_plan(),
                                  date(2026, 9, 1), date(2026, 9, 30), oms or {}, 3,
                                  {"FGA": 200.0, "FGB": 150.0}, 148.33)

    def test_five_buckets_and_the_month_end_bunch(self):
        rows, stats = self.run_it()
        by_day = {}
        for r in rows:
            if r["code"] == "FGA":
                by_day[r["date"]] = by_day.get(r["date"], 0.0) + r["pieces"] * 1.0
        # FGA sold ONLY in bucket 5, and bucket 5 is 29-30 Sep (two days in September)
        self.assertEqual(sorted(by_day), ["2026-09-29", "2026-09-30"])
        self.assertAlmostEqual(sum(by_day.values()), 300.0, places=4)

    def test_own_shape_versus_pooled_shape(self):
        rows, stats = self.run_it()
        self.assertEqual(stats["sku_shape_own"], 1)        # FGA, months_seen 3
        self.assertEqual(stats["sku_shape_pooled"], 1)     # FGB, months_seen 1
        # FGB's own history is 100% bucket 1 off ONE month. The pooled shape puts half the
        # month in bucket 5, so that is where its litres land — a shape of one sale is not
        # a shape.
        weeks = {r["docnum"].split("-")[1] for r in rows if r["code"] == "FGB"}
        self.assertIn("W5", weeks)
        self.assertNotEqual(weeks, {"W1"})

    def test_the_trade_book_is_netted_and_floors_at_zero(self):
        _rows, base = self.run_it()
        _rows2, netted = self.run_it(oms={"FGA": 100.0})      # 100 pieces x 1 L
        self.assertAlmostEqual(base["litres"] - netted["litres"], 100.0, places=3)
        self.assertAlmostEqual(netted["netted_oms_pieces"], 100.0, places=3)
        # over-ordered: netted to nothing, never below it
        rows3, floored = self.run_it(oms={"FGA": 99999.0})
        self.assertFalse([r for r in rows3 if r["code"] == "FGA"])
        self.assertGreaterEqual(floored["litres"], 0.0)

    def test_ecom_is_never_netted(self):
        """The caller nets OMS only — the signature takes one book, and that is the rule."""
        _rows, stats = self.run_it(oms={})
        self.assertEqual(stats["netted_oms_pieces"], 0.0)

    def test_rows_are_triple_tagged_and_carry_their_basis(self):
        rows, _ = self.run_it()
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["channel"], "FORECAST")
            self.assertTrue(r["docnum"].startswith("FCST-W"))
            self.assertEqual(r["customer"], fz.FORECAST_CUSTOMER)
            self.assertEqual(r["_src"], "FORECAST")
            self.assertEqual(r["basis"], fz.FORECAST_BASIS_BILLING)
            self.assertGreaterEqual(r["pieces"], 1)          # never a fraction of a bottle

    def test_a_sku_the_plan_cannot_build_is_counted_not_forecast(self):
        rows, stats = self.run_it(plan={"FGA": a_plan()["FGA"]})
        self.assertEqual(stats["skus_known_not_planned"], 1)
        self.assertFalse([r for r in rows if r["code"] == "FGB"])

    def test_sub_bottle_slices_are_counted_out_loud(self):
        base = a_baseline()
        base["skus"]["FGB"]["litres_per_month"] = 5          # 1 piece a month over 30 days
        _rows, stats = fz.expected_stream(base, a_plan(), date(2026, 9, 1), date(2026, 9, 30),
                                          {}, 3, {}, 148.33)
        self.assertGreater(stats["dropped_subpiece_l"], 0)

    def test_week_of_month5_buckets(self):
        self.assertEqual([fz.week_of_month5(date(2026, 9, d)) for d in (1, 7, 8, 21, 22, 28, 29, 30)],
                         [1, 1, 2, 3, 4, 4, 5, 5])


# ------------------------------------------------------------------- A18 ----
class ExpectedOnlyRows(unittest.TestCase):
    BOM = {"FGC": [["RM0000011", 1.0], ["PM0000851", 1.0]],
           "FGD": [["PM0000851", 1.0]]}
    ITEMS = {"RM0000011": {"name": "GROUNDNUT LOOSE OIL", "uom": "LTR"},
             "PM0000851": {"name": "PET BOTTLE 1 LTR 26 GM", "uom": "PCS"}}

    def baseline(self):
        b = a_baseline()
        b["skus"]["FGC"] = {"name": "C 1 LTR", "type": "PREMIUM", "sub_group": "GROUNDNUT",
                            "litres_per_piece": 1.0, "litres_per_month": 500,
                            "inr_per_month": 100000, "months_seen": 3,
                            "by_week": {"1": 1500}, "in_plan_sheet": False}
        b["skus"]["FGD"] = {"name": "D 1 LTR", "type": "PREMIUM", "sub_group": "X",
                            "litres_per_piece": 1.0, "litres_per_month": 90,
                            "inr_per_month": 9000, "months_seen": 3,
                            "by_week": {"1": 270}, "in_plan_sheet": False}
        b["skus"]["FGE"] = {"name": "E 1 LTR", "type": "PREMIUM", "sub_group": "X",
                            "litres_per_piece": 1.0, "litres_per_month": 40,
                            "inr_per_month": 4000, "months_seen": 3,
                            "by_week": {"1": 120}, "in_plan_sheet": False}
        return b

    def test_only_a_resolvable_recipe_becomes_a_plan_row(self):
        realise = {}
        rows, packs, nonplan = fz.expected_only_rows(
            self.baseline(), a_plan(), self.BOM, self.ITEMS, {"RM0000011"}, realise)
        self.assertEqual([r["code"] for r in rows], ["FGC"])
        self.assertEqual(nonplan["appended"], 1)
        reasons = {s["code"]: s["reason"] for s in nonplan["skipped"]}
        self.assertEqual(reasons["FGD"], "no oil in BOM")
        self.assertEqual(reasons["FGE"], "no BOM")
        self.assertEqual(nonplan["candidates"], 3)

    def test_an_appended_row_is_expected_only_and_carries_its_trailing_sales(self):
        realise = {}
        rows, packs, _ = fz.expected_only_rows(
            self.baseline(), a_plan(), self.BOM, self.ITEMS, {"RM0000011"}, realise)
        row = rows[0]
        self.assertIs(row["expected_only"], True)
        self.assertEqual(row["pieces"], 0)
        self.assertEqual(row["trailing_l_per_month"], 500)
        self.assertEqual(row["source"], "demand_baseline A18")
        self.assertEqual(packs["FGC"]["slot"], "1L")
        self.assertEqual(packs["FGC"]["derived_by"], "freeze")
        # its rate is what it actually billed for: 100,000 / 500 = 200 Rs/L
        self.assertAlmostEqual(realise["FGC"], 200.0, places=2)

    def test_an_existing_realise_rate_is_never_overwritten(self):
        realise = {"FGC": 999.0}
        fz.expected_only_rows(self.baseline(), a_plan(), self.BOM, self.ITEMS,
                              {"RM0000011"}, realise)
        self.assertEqual(realise["FGC"], 999.0)


# ------------------------------------------------------------------- lag ----
class LagSelection(unittest.TestCase):
    def test_a_fresh_daily_file_wins_and_is_not_static(self):
        days, block, live, say = fz.select_lag(lag_envelope_data(), "fresh", 0,
                                               "2026-09-06T05:00:00+05:30", STATIC_NOTE, 2)
        self.assertEqual(days, 3)
        self.assertTrue(live)
        self.assertIs(block["static"], False)
        self.assertEqual(block["p90_days"], 11)
        self.assertIn("measured DAILY", say)

    def test_the_plan_takes_jivo_oil_s_lag_and_publishes_the_merged_one_beside_it(self):
        """CLAUDE.md: dispatch litres are three companies, Oil is the split, never the
        merged headline — and dispatch_lag.py says the same in its own docstring. The
        engine plans Oil, so it is fed Oil's 3 days, not the gate's merged 2."""
        days, block, _live, say = fz.select_lag(lag_envelope_data(), "fresh", 0, None,
                                                STATIC_NOTE, 2)
        self.assertEqual(days, 3)
        self.assertEqual(block["book"], fz.PLAN_BOOK)
        self.assertEqual(block["median_days"], 3)
        self.assertEqual(block["all_books"]["median_days"], 2)
        self.assertEqual(block["all_books"]["p90_days"], 9)
        self.assertEqual(block["all_books"]["rows"], 551)
        self.assertIn("OIL", say)
        self.assertIn("merged", say)

    def test_a_file_with_no_oil_rows_says_it_is_standing_in_the_merged_gate(self):
        days, block, _live, say = fz.select_lag(lag_envelope_data(oil=False), "fresh", 0,
                                                None, STATIC_NOTE, 2)
        self.assertEqual(days, 2)                       # the merged gate, and only then
        self.assertEqual(block["book"], "ALL_BOOKS")
        self.assertIn("NO JIVO Oil row", say)

    def test_the_static_fallback_admits_it_was_never_split_by_book(self):
        _d, block, _l, say = fz.select_lag(None, "missing", None, None, STATIC_NOTE, 2)
        self.assertEqual(block["book"], "ALL_BOOKS")
        self.assertIsNone(block["all_books"]["median_days"])
        self.assertIn("merged", say)

    def test_a_stale_file_falls_back_to_the_static_note_and_says_so(self):
        days, block, live, say = fz.select_lag(lag_envelope_data(), "stale 30d", 30, None,
                                               STATIC_NOTE, 2)
        self.assertEqual(days, 2)
        self.assertFalse(live)
        self.assertIs(block["static"], True)
        self.assertEqual(block["measured_on"], "2026-09-03")
        self.assertIn("stale 30d", say)
        self.assertIn("live/dispatch_lag.py", say)

    def test_a_missing_file_falls_back_too(self):
        days, block, live, say = fz.select_lag(None, "missing", None, None, STATIC_NOTE, 2)
        self.assertEqual((days, live, block["static"]), (2, False, True))
        self.assertIn("missing", say)

    def test_no_note_at_all_keeps_the_carried_number(self):
        days, block, live, _say = fz.select_lag(None, "missing", None, None, {}, 2)
        self.assertEqual(days, 2)
        self.assertIsNone(block["median_days"])
        self.assertFalse(live)

    def test_a_fractional_median_rounds_to_whole_days(self):
        # the fraction is on OIL's median, because Oil's is the one the plan runs on
        days, _b, _l, _s = fz.select_lag(lag_envelope_data(median=2.5), "fresh", 0, None,
                                         STATIC_NOTE, 2)
        self.assertEqual(days, 2)     # banker's rounding on .5, and a whole number either way


# ------------------------------------------------------------- pendency ----
class Pendency(unittest.TestCase):
    DAYS = [{"dispatched_all_l": 200000.0, "dispatched_oil_l": 100000.0},
            {"dispatched_all_l": 100000.0, "dispatched_oil_l": 50000.0}]

    def test_days_of_work_at_the_recent_pace(self):
        d = fz.dispatch_pendency({"litres": 300000.0, "bills": 499}, self.DAYS, 150000.0)
        self.assertEqual(d["trailing_daily_all_l"], 150000)
        self.assertEqual(d["pendency_days_all"], 2.0)
        self.assertEqual(d["trailing_daily_oil_l"], 75000)
        self.assertEqual(d["pendency_days_oil"], 2.0)
        self.assertIsNone(d["basis_missing"])

    def test_null_with_a_reason_when_no_day_has_a_gate_figure(self):
        d = fz.dispatch_pendency({"litres": 300000.0}, [{"dispatched_all_l": None}], 150000.0)
        self.assertIsNone(d["pendency_days_all"])
        self.assertIsNone(d["pendency_days_oil"])
        self.assertEqual(d["trailing_days"], 0)
        self.assertTrue(d["basis_missing"])

    def test_the_three_books_are_not_one_queue(self):
        d = fz.dispatch_pendency({"litres": 300000.0}, self.DAYS, 150000.0)
        self.assertNotEqual(d["open_l_all_books"], d["oil_pile_l"])
        self.assertEqual(d["oil_pile_l"], 150000)

    def test_no_open_book_is_null_not_zero(self):
        d = fz.dispatch_pendency({}, self.DAYS, 150000.0)
        self.assertIsNone(d["open_l_all_books"])
        self.assertIsNone(d["pendency_days_all"])


# ---------------------------------------------------------------- money ----
class MoneyValuation(unittest.TestCase):
    PLAN = a_plan()
    ITEMS = {"FGZ": {"name": "Z 2 LTR 6 PCS"}}
    REALISE = {"FGA": 200.0}
    SHEET = {"FGA"}
    BL = {"FGB": 150.0}

    def price(self, code, pieces, aliases=None):
        return fz.price_pieces(code, pieces, self.PLAN, self.ITEMS, self.REALISE,
                               self.SHEET, self.BL, aliases or {}, 148.33)

    def test_the_plan_sheets_own_rate_comes_first(self):
        rs, key, unvalued, c = self.price("FGA", 10)
        self.assertEqual((key, unvalued, c), ("realise_rs", 0.0, "FGA"))
        self.assertAlmostEqual(rs, 10 * 1.0 * 200.0)

    def test_then_the_billing_rate(self):
        rs, key, _u, _c = self.price("FGB", 10)
        self.assertEqual(key, "baseline_rs")
        self.assertAlmostEqual(rs, 10 * 5.0 * 150.0)

    def test_then_the_engines_default(self):
        rs, key, _u, _c = self.price("FGZ", 10)      # not on the plan, no billing rate
        self.assertEqual(key, "default_rs")
        self.assertAlmostEqual(rs, 10 * 2.0 * 148.33)

    def test_a_code_with_no_pack_size_is_unvalued_not_free(self):
        rs, key, unvalued, _c = self.price("FGUNKNOWN", 10)
        self.assertEqual((rs, key, unvalued), (0.0, None, 10))

    def test_a10_prices_the_new_carton_code_as_the_product_it_is(self):
        rs, key, _u, c = self.price("FG0000461", 10, aliases={"FG0000461": "FGA"})
        self.assertEqual(c, "FGA")
        self.assertEqual(key, "realise_rs")
        self.assertAlmostEqual(rs, 10 * 1.0 * 200.0)


# ------------------------------------------------------------ daily_file ----
class DailyFile(unittest.TestCase):
    def envelope(self, tmp, name, fetched_at, ok=True, data=None):
        path = os.path.join(tmp, f"{name}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"source": name, "fetched_at": fetched_at, "server_at": None,
                       "ok": ok, "error": None, "data": data if data is not None else {"x": 1}}, fh)
        return path

    def test_fresh_stale_missing_and_wrong_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["MARK4_DISPATCH_LAG"] = self.envelope(
                tmp, "dispatch_lag", "2026-09-06T05:00:00+05:30")
            try:
                _d, mode, age, _p = fz.daily_file("dispatch_lag", date(2026, 9, 6))
                self.assertEqual((mode, age), ("fresh", 0))
                _d, mode, age, _p = fz.daily_file("dispatch_lag", date(2026, 9, 30))
                self.assertEqual((mode, age), ("stale 24d", 24))
                # a state.json a few minutes older than the file is not "-1 days old"
                _d, mode, age, _p = fz.daily_file("dispatch_lag", date(2026, 9, 5))
                self.assertEqual((mode, age), ("fresh", 0))
                _d, mode, _a, _p = fz.daily_file("dispatch_lag", date(2026, 9, 6),
                                                 month_ok=lambda d: False)
                self.assertEqual(mode, "wrong-month")
            finally:
                del os.environ["MARK4_DISPATCH_LAG"]

    def test_a_failed_envelope_is_missing_not_empty_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["MARK4_DISPATCH_LAG"] = self.envelope(
                tmp, "dispatch_lag", "2026-09-06T05:00:00+05:30", ok=False)
            try:
                data, mode, _a, _p = fz.daily_file("dispatch_lag", date(2026, 9, 6))
                self.assertEqual(mode, "missing")
                self.assertIsNone(data)
            finally:
                del os.environ["MARK4_DISPATCH_LAG"]

    def test_no_file_at_all(self):
        os.environ["MARK4_DISPATCH_LAG"] = "/nonexistent/dispatch_lag.json"
        try:
            data, mode, age, _p = fz.daily_file("dispatch_lag", date(2026, 9, 6))
            self.assertEqual((data, mode, age), (None, "missing", None))
        finally:
            del os.environ["MARK4_DISPATCH_LAG"]


# -------------------------------------------------------------- rulebook ----
class RulebookLoad(unittest.TestCase):
    def test_the_real_rulebook_loads_and_names_its_version(self):
        rb = fz.load_rulebook()
        self.assertTrue(rb["version"])
        self.assertIn("Tin Head", rb["lines"])

    def test_a_missing_rulebook_refuses_rather_than_writing_mark_3(self):
        # die() prints the refusal to stderr on purpose; swallow it so a passing test run
        # does not look like a failing one.
        with io.StringIO() as buf, contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as cm:
                fz.load_rulebook("/nonexistent/mark4-rulebook.json")
            said = buf.getvalue()
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("15 L on Clear Pack", said)


# ------------------------------------------------------------ end to end ----
class EndToEnd(unittest.TestCase):
    """One real build() against the state on disk. No network — everything is a file."""

    out = None

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(os.path.join(STATE_DIR, "state.json")):
            raise unittest.SkipTest(
                "no live/state/state.json — live/state/ is gitignored. Copy "
                "site-live/fixtures/state.json and live/fixtures/demand_baseline.json into "
                "live/state/ (see live/README.md) or run live/collect.py, then re-run.")
        env = {"MARK3_STATE_DIR": STATE_DIR, "MARK4_DEMAND_BASELINE": FIXTURE,
               # forced ABSENT so the static fallback is what this test measures; the fresh
               # path is covered by LagSelection above and by a real file on the VPS
               "MARK4_DISPATCH_LAG": "/nonexistent/dispatch_lag.json"}
        cls._saved = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        cls._saved_state_dir = fz.STATE_DIR
        fz.STATE_DIR = STATE_DIR
        # build() only READS the carry (main() is what saves it), so the real
        # sim/live-carry.json is used and nothing on disk is written by this test.
        try:
            _F, cls.out, cls.recon = fz.build()
        except SystemExit as exc:
            raise unittest.SkipTest(
                "the freeze refused on this box's state (%s). That is the documented "
                "cold-start behaviour, not a bug: the hourly stock set has to have run "
                "once. rm live/state/.cadence.json, then one live/loop.sh." % exc)
        finally:
            fz.STATE_DIR = cls._saved_state_dir
            for k, v in cls._saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_the_rulebook_is_embedded_with_its_version(self):
        rb = self.out["rulebook"]
        self.assertTrue(rb["version"])
        self.assertEqual(self.out["provenance"]["rulebook"]["version"], rb["version"])

    def test_ten_hour_sessions_and_no_second_derate(self):
        r = self.out["rules"]
        self.assertEqual(r["shift_hours"], 10)
        self.assertEqual(r["efficiency"], 1.0)
        self.assertIn("A01", r["efficiency_basis"])
        self.assertEqual(r["night_lines_max"], 1)

    def test_no_fifteen_litre_key_on_a_line_that_is_not_a_tin_line(self):
        lines = self.out["lines"]
        for name in ("Clear Pack", "10 Head", "6 Head"):
            self.assertNotIn("15L", lines[name], f"{name} must never carry a 15 L slot (AC02)")
        self.assertEqual(set(lines["Tin Head"]), {"15L", "3L", "5L"})
        self.assertNotIn("TIN", lines["Tin Head"], "TIN is a bottle family, not a line slot")

    def test_every_line_slot_says_where_its_speed_came_from(self):
        for line, slots in self.out["lines"].items():
            for slot in slots:
                self.assertEqual(self.out["lines_basis"][line][slot], "planning")
                self.assertIn(self.out["lines_basis_kind"][line][slot],
                              {"capped", "rated", "typical", "carried", "derived"})

    def test_the_baseline_is_present_and_actually_used(self):
        b = self.out["demand_baseline"]
        self.assertTrue(b["present"])
        self.assertTrue(b["used_for_forecast"])
        self.assertEqual(b["mode"], "fresh")
        self.assertIsNone(b["fallback_reason"])
        self.assertTrue(b["channels_included"])
        for k in ("skus_vs_totals_pct", "channels_vs_totals_pct", "weeks_vs_totals_pct"):
            self.assertIsNotNone(b["reconciliation"][k], k)

    def test_every_forecast_row_is_triple_tagged(self):
        fc = [o for o in self.out["orders"] if o["channel"] == "FORECAST"]
        self.assertTrue(fc, "the expected stream is empty")
        for r in fc:
            self.assertTrue(r["docnum"].startswith("FCST-"))
            self.assertEqual(r["customer"], fz.FORECAST_CUSTOMER)
            self.assertEqual(r["_src"], "FORECAST")
            self.assertEqual(r["basis"], fz.FORECAST_BASIS_BILLING)

    def test_the_expected_tier_can_be_ranked_by_trailing_sales(self):
        rows = [p for p in self.out["plan"] if p.get("trailing_l_per_month")]
        self.assertTrue(rows, "no plan row carries trailing_l_per_month — R19 ranks by "
                              "insertion order without it")

    def test_every_plan_row_has_a_pack_class(self):
        packs = self.out["rulebook"]["sku_pack"]
        for p in self.out["plan"]:
            self.assertIn(p["code"], packs, p["code"])
            self.assertIsNotNone(packs[p["code"]]["slot"], p["code"])
            self.assertNotEqual(packs[p["code"]]["family"], "UNKNOWN", p["code"])

    def test_sold_but_unplanned_skus_are_either_appended_or_named(self):
        n = self.out["demand_baseline"]["nonplan"]
        self.assertTrue(n["appended"] or n["skipped"],
                        "the baseline knows SKUs the sheet does not; they must be one or the other")
        for s in n["skipped"]:
            self.assertTrue(s["reason"])

    def test_the_lag_falls_back_to_the_static_note_and_says_so(self):
        lag = self.out["lag"]
        self.assertIs(lag["static"], True)
        self.assertIsNotNone(lag["median_days"])
        self.assertEqual(self.out["rules"]["invoice_truck_lag_days"], lag["median_days"])
        self.assertTrue(any("dispatch_lag.json is missing" in a
                            for a in self.out["honesty"]["assumed"]),
                        "a static lag must say the daily file is not there")

    def test_pendency_is_a_number_or_a_reason(self):
        d = self.out["dispatch_book"]
        self.assertTrue(d["pendency_days_all"] is not None or d["basis_missing"])
        self.assertTrue(d["basis"])

    def test_money_carries_the_rulebooks_target_and_a_rate_split(self):
        m = self.out["money"]
        self.assertEqual(m["target_rs_per_day"], self.out["rulebook"]["money"]["target_inr_per_day"])
        self.assertEqual(m["floor_rs_per_day"], self.out["rulebook"]["money"]["floor_inr_per_day"])
        self.assertEqual(sum(m["mtd_by_basis"].values()), m["mtd_made_rs"])

    def test_every_assumption_says_which_plan_mode_it_is_true_in(self):
        """THE POSITIVE CONTRACT (2026-09-06). The engine used to strip carried honesty by
        KEYWORD — "derate", "of rated", "rules.efficiency", "50% again" — which deleted
        sentences that are TRUE under the rulebook and then printed a warning blaming this
        file for writing them. So the freeze tags instead: every sentence carries the mode
        it holds in, and the engine drops by tag."""
        honesty = self.out["honesty"]
        modes = honesty["assumed_modes"]
        self.assertEqual([a for a in honesty["assumed"] if a not in modes], [],
                         "an assumption reached the engine with no mode on it")
        self.assertTrue(set(modes.values()) <= {"legacy", "rulebook", "both"},
                        sorted(set(modes.values())))

    def test_this_freeze_writes_nothing_the_rulebook_run_has_to_drop(self):
        """It only ever writes rulebook inputs — a missing rulebook is a refusal, not a
        fallback — so nothing it writes may be tagged for the legacy path. Anything that
        is would come back as summary.rulebook.honesty_dropped and never reach the site."""
        legacy = [a for a, m in self.out["honesty"]["assumed_modes"].items() if m == "legacy"]
        self.assertEqual(legacy, [])

    def test_no_line_claims_the_engine_derates_the_speeds_again(self):
        """The substance the old keyword filter was really guarding, kept and scoped: A01
        says the planning speeds carry the 80% and the August cap and the engine multiplies
        by 1.0. A sentence saying otherwise is FALSE, whatever it is tagged."""
        false_claims = ("derates everything by 50%", "50% again", "rules.efficiency (0.5)",
                        "efficiency (0.5)")
        bad = [a for a in self.out["honesty"]["assumed"]
               if any(m in a.lower() for m in false_claims)]
        self.assertEqual(bad, [], "a Mark 3 derate sentence is in the plan's honesty block")

    def test_rulebook_applied_records_every_ruling_this_run_touched(self):
        applied = self.out["rulebook_applied"]
        self.assertEqual(set(applied), {"A01", "A09", "A10", "A17", "A18", "R16", "R21"})
        for key, rec in applied.items():
            self.assertIn("in_effect", rec)
            self.assertTrue(rec["note"], key)
        self.assertTrue(applied["A01"]["in_effect"])

    def test_provenance_names_the_daily_files(self):
        p = self.out["provenance"]
        self.assertIn("demand_baseline", p)
        self.assertIn("dispatch_lag", p)
        self.assertEqual(p["rulebook"]["source"], os.path.join("reference", "mark4-rulebook.json"))


if __name__ == "__main__":
    unittest.main()
