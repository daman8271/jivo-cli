#!/usr/bin/env python3
"""Unit tests for live/adapters/factory_history.py.

    cd jolly && python3 -m unittest live.adapters.factory_history_test -v

NO NETWORK, no factory login, no CLI binary: `_cli` and `_run` are replaced with
canned payloads in the shapes the live endpoints actually return (run rows with
segments; movement rows with direction/transaction_label; a gate envelope with
{count, next, results} and numbers as STRINGS, the same truck once per company).

The assertions are the traps, not the happy path:
  * the two litre bases stay two and are never summed
  * only TransType 59 IN is production booked, only AR-invoice OUT is billed
  * a truck is counted once, Oil litres are never the merged litres
  * a gate row is placed on its GATE-OUT date, and today's rows are dropped
  * a Sunday keeps its figures, it is not zeroed to match the plan's rule
  * a failed sub-read publishes NULL, never 0, and the day never settles
  * the settle rule, the cache republish, and the month rollover
  * a spent budget leaves the unread days in missing_dates
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
_JOLLY = os.path.dirname(os.path.dirname(_HERE))
if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)

from live.adapters import factory_history as fh  # noqa: E402


# --------------------------------------------------------------- payloads ---
def run_payload(*runs):
    """`production-execution reports-daily-production` — {meta, results:[run]}."""
    return {"meta": {"source": "live"}, "results": list(runs)}


def a_run(run_id, item, cases, ppc=12.0, lpp=1.0, open_segs=0, line="Clear Pack"):
    segs = [{"produced_cases": cases, "is_active": False,
             "start_time": "2026-09-01T09:00:00+05:30"}]
    for i in range(open_segs):
        segs.append({"produced_cases": 0, "is_active": True,
                     "start_time": "2026-09-01T1%d:00:00+05:30" % (i + 4)})
    return {"id": run_id, "line_name": line, "line": 3, "item_code": item,
            "product": "OLIVE OIL 1 LTR 12 PCS", "pieces_per_case": ppc,
            "litres_per_piece": lpp, "segments": segs,
            "total_running_minutes": 120, "total_breakdown_time": 0,
            "rated_speed": 3000, "required_qty": 500,
            "created_at": "2026-09-01T08:00:00+05:30"}


def move_payload(rows, limit=1000):
    """`reports-production-movement` — {meta, results:{meta, summary, data:[row]}}."""
    return {"meta": {"source": "live"},
            "results": {"meta": {"limit": limit}, "summary": {}, "data": list(rows)}}


def gr_row(code, qty, name="OLIVE OIL 1 LTR 12 PCS", value=1000.0):
    return {"date": "2026-09-01T00:00:00", "item_code": code, "item_name": name,
            "in_qty": qty, "out_qty": 0, "direction": "IN",
            "transaction_type": 59, "transaction_label": "Goods Receipt",
            "transaction_value": value, "item_group": "FG"}


def inv_row(code, qty, name="OLIVE OIL 1 LTR 12 PCS"):
    return {"date": "2026-09-01T00:00:00", "item_code": code, "item_name": name,
            "in_qty": 0, "out_qty": qty, "direction": "OUT",
            "transaction_type": 13, "transaction_label": "AR Invoice",
            "transaction_value": 5000.0, "item_group": "FG"}


def gate_row(day, company, vehicle, litres, status="DISPATCHED", bills=1):
    return {"status": status, "company_code": company, "vehicle_no": vehicle,
            "gate_out_date": day, "out_time": "16:40:00",
            "dispatched_at": day + "T16:40:00+05:30",
            "total_litres": "%0.3f" % litres, "total_boxes": "100.000",
            "sap_doc_total": "130000.00",
            "document_numbers": ["<doc>"] * bills}


def gate_envelope(rows, page=1, num_pages=1, count=None):
    """The shape --page actually returns, verified live 2026-09-05:
    {count, num_pages, page, page_size, results} — NOT DRF's next/previous."""
    return {"count": count if count is not None else len(rows),
            "num_pages": num_pages, "page": page, "page_size": 100,
            "results": list(rows)}


# ------------------------------------------------------------------ harness --
class Fake:
    """Stands in for `_cli` and `_run`, and records what was asked for."""

    def __init__(self, daily=None, movement=None, gate=None, delay=0.0):
        self.daily = daily or {}          # {iso: payload or None}
        self.movement = movement or {}    # {iso: payload or None}
        self.gate = gate or []            # [envelope or None] per page
        self.delay = delay
        self.cli_names, self.gate_pages = [], 0

    # signature of factory_production._cli
    def cli(self, calls, name, *args, timeout=None):
        self.cli_names.append(name)
        if self.delay:
            fh.time.sleep(self.delay)
        iso = args[-1] if name.startswith("daily_") else name.split("_", 1)[1]
        table = self.daily if name.startswith("daily_") else self.movement
        payload = table.get(iso, "MISSING")
        if payload == "MISSING" or payload is None:
            calls.record(name, args, False, 0.01, "%s: canned failure" % name)
            return None, "%s: canned failure" % name
        calls.record(name, args, True, 0.01, None, "live")
        return payload, None

    # signature of factory_dispatch._run
    def run(self, name, args, timeout=None):
        self.gate_pages += 1
        idx = self.gate_pages - 1
        record = {"name": name, "ok": False, "ms": 5, "args": " ".join(args), "error": None}
        payload = self.gate[idx] if idx < len(self.gate) else None
        if payload is None:
            record["error"] = "canned gate failure"
            return None, record
        record["ok"] = True
        return payload, record


class Base(unittest.TestCase):
    """Every test runs against a throwaway cache file and a frozen 'today'."""

    TODAY = date(2026, 9, 5)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._cache = fh.CACHE_FILE
        fh.CACHE_FILE = os.path.join(self.tmp.name, "factory_history.month.json")
        self._cli, self._run, self._full = fh._cli, fh._run, fh.FULL
        self._budget = fh.BUDGET_S

        class _FixedDT(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(self.TODAY.year, self.TODAY.month, self.TODAY.day,
                                15, 30, 0, tzinfo=fh.IST)

        self._dt = fh.datetime
        fh.datetime = _FixedDT

    def tearDown(self):
        fh.CACHE_FILE = self._cache
        fh._cli, fh._run, fh.FULL = self._cli, self._run, self._full
        fh.datetime, fh.BUDGET_S = self._dt, self._budget
        self.tmp.cleanup()

    def install(self, fake):
        fh._cli, fh._run = fake.cli, fake.run
        return fake

    def full_month(self, gate_rows=(), extra_gate_pages=()):
        """1-4 Sep, every read clean, one gate page."""
        daily, movement = {}, {}
        for d in range(1, 5):
            iso = "2026-09-%02d" % d
            daily[iso] = run_payload(a_run(100 + d, "FG0000081", 100.0 * d))
            movement[iso] = move_payload([gr_row("FG0000081", 120.0 * d),
                                          inv_row("FG0000081", 60.0 * d)])
        pages = [gate_envelope(list(gate_rows))] + list(extra_gate_pages)
        return self.install(Fake(daily=daily, movement=movement, gate=pages))

    @staticmethod
    def by_date(env):
        return {r["date"]: r for r in env["data"]["days"]}


# --------------------------------------------------------------- the tests ---
class Shape(Base):
    def test_envelope_and_day_range(self):
        self.full_month()
        env = fh.fetch(hourly=True)
        self.assertEqual(env["source"], "factory_history")
        self.assertIsNone(env["server_at"])
        self.assertTrue(env["ok"], env["error"])
        data = env["data"]
        self.assertEqual(data["month"], "2026-09")
        self.assertEqual(data["today"], "2026-09-05")
        self.assertEqual(data["through"], "2026-09-04")
        self.assertEqual([r["date"] for r in data["days"]],
                         ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04"])
        self.assertEqual(data["missing_dates"], [])
        self.assertEqual(data["status"], "complete")

    def test_today_is_never_a_record(self):
        self.full_month()
        data = fh.fetch(hourly=True)["data"]
        self.assertNotIn("2026-09-05", [r["date"] for r in data["days"]])

    def test_no_summed_litre_key_anywhere(self):
        self.full_month()
        blob = fh.json.dumps(fh.fetch(hourly=True)["data"])
        for banned in ('"made_l"', '"made_total_l"', '"filled_l"', '"total_made_l"'):
            self.assertNotIn(banned, blob)


class Production(Base):
    def test_litres_use_the_apps_own_case_maths(self):
        # 100 cases x 12 pieces x 1 L = 1,200 L. The NAME alone would say 1 L a
        # case; the app's pieces_per_case x litres_per_piece wins.
        self.full_month()
        row = self.by_date(fh.fetch(hourly=True))["2026-09-01"]
        self.assertEqual(row["made_mes_l"], 1200.0)
        self.assertEqual(row["made_mes_cases"], 100.0)
        self.assertEqual(row["runs"], 1)

    def test_only_goods_receipts_count_as_booked(self):
        daily = {"2026-09-04": run_payload(a_run(1, "FG0000081", 10.0))}
        rows = [gr_row("FG0000081", 500.0),
                inv_row("FG0000081", 900.0),
                {"date": "2026-09-04T00:00:00", "item_code": "FG0000081",
                 "item_name": "OLIVE OIL 1 LTR 12 PCS", "in_qty": 400.0, "out_qty": 0,
                 "direction": "IN", "transaction_type": 21,
                 "transaction_label": "Stock Transfer", "transaction_value": 1.0}]
        self.install(Fake(daily=daily, movement={"2026-09-04": move_payload(rows)},
                          gate=[gate_envelope([])]))
        row = self.by_date(fh.fetch(hourly=True))["2026-09-04"]
        self.assertEqual(row["made_booked_pcs"], 500.0)      # the transfer is not production
        self.assertEqual(row["booked_receipts"], 1)
        self.assertEqual(row["billed_out_pcs"], 900.0)       # the receipt is not a bill
        self.assertEqual(row["billed_lines"], 1)

    def test_booked_by_item_is_pieces_per_code(self):
        daily = {"2026-09-04": run_payload(a_run(1, "FG0000081", 10.0))}
        move = move_payload([gr_row("FG0000081", 300.0), gr_row("FG0000010", 200.0)])
        self.install(Fake(daily=daily, movement={"2026-09-04": move},
                          gate=[gate_envelope([])]))
        row = self.by_date(fh.fetch(hourly=True))["2026-09-04"]
        self.assertEqual(row["booked_by_item"], {"FG0000081": 300.0, "FG0000010": 200.0})

    def test_unparsed_pack_sizes_are_reported_not_hidden(self):
        daily = {"2026-09-04": run_payload(a_run(1, "FG0000081", 1.0))}
        move = move_payload([gr_row("PM0000075", 400.0, name="TAPE ROLL"),
                             inv_row("PM0000075", 100.0, name="TAPE ROLL")])
        self.install(Fake(daily=daily, movement={"2026-09-04": move},
                          gate=[gate_envelope([])]))
        row = self.by_date(fh.fetch(hourly=True))["2026-09-04"]
        self.assertEqual(row["made_booked_l"], 0.0)
        self.assertEqual(row["booked_unparsed_pcs"], 400.0)
        self.assertEqual(row["billed_unparsed_pcs"], 100.0)
        self.assertIn("no pack size", " ".join(row["notes"]))

    def test_open_segments_block_the_settle_and_are_said_out_loud(self):
        daily = {"2026-09-01": run_payload(a_run(1, "FG0000081", 50.0, open_segs=2))}
        self.install(Fake(daily=daily,
                          movement={"2026-09-01": move_payload([gr_row("FG0000081", 10.0)])},
                          gate=[gate_envelope([])]))
        row = self.by_date(fh.fetch(hourly=True))["2026-09-01"]
        self.assertEqual(row["open_segments"], 2)
        self.assertFalse(row["complete"])
        self.assertFalse(row["settled"])
        self.assertIn("still open", " ".join(row["notes"]))

    def test_a_truncated_movement_page_is_a_floor(self):
        rows = [gr_row("FG%07d" % i, 1.0) for i in range(5)]
        self.install(Fake(daily={"2026-09-01": run_payload(a_run(1, "FG0000081", 1.0))},
                          movement={"2026-09-01": move_payload(rows, limit=5)},
                          gate=[gate_envelope([])]))
        row = self.by_date(fh.fetch(hourly=True))["2026-09-01"]
        self.assertTrue(row["booked_truncated"])
        self.assertFalse(row["settled"])


class Gate(Base):
    def test_oil_is_never_the_merged_figure_and_trucks_dedupe(self):
        # One truck, two companies, two rows — 3 Sep's trap: 47,182 L "dispatched"
        # was 89% Beverages.
        rows = [gate_row("2026-09-03", "JIVO_OIL", "HR55AB1234", 5000.0),
                gate_row("2026-09-03", "JIVO_BEVERAGES", "HR55AB1234", 30000.0),
                gate_row("2026-09-03", "JIVO_MART", "HR55CD9999", 2000.0)]
        self.full_month(gate_rows=rows)
        row = self.by_date(fh.fetch(hourly=True))["2026-09-03"]
        self.assertEqual(row["dispatched_oil_l"], 5000.0)
        self.assertEqual(row["dispatched_all_l"], 37000.0)
        self.assertEqual(row["trucks_all"], 2)      # the plate counted once
        self.assertEqual(row["trucks_oil"], 1)
        self.assertEqual(row["rows_oil"], 1)
        self.assertLessEqual(row["dispatched_oil_l"], row["dispatched_all_l"])

    def test_only_dispatched_rows_count(self):
        rows = [gate_row("2026-09-02", "JIVO_OIL", "HR1", 1000.0),
                gate_row("2026-09-02", "JIVO_OIL", "HR2", 9000.0, status="DOCKED"),
                gate_row("2026-09-02", "JIVO_OIL", "HR3", 9000.0, status="CANCELLED")]
        self.full_month(gate_rows=rows)
        row = self.by_date(fh.fetch(hourly=True))["2026-09-02"]
        self.assertEqual(row["dispatched_oil_l"], 1000.0)
        self.assertEqual(row["trucks_oil"], 1)

    def test_rows_land_on_their_gate_out_date_and_today_is_dropped(self):
        rows = [gate_row("2026-09-01", "JIVO_OIL", "HR1", 100.0),
                gate_row("2026-09-04", "JIVO_OIL", "HR2", 200.0),
                gate_row("2026-09-05", "JIVO_OIL", "HR3", 999999.0),   # today
                gate_row("2026-08-31", "JIVO_OIL", "HR4", 888888.0)]   # before the month
        self.full_month(gate_rows=rows)
        days = self.by_date(fh.fetch(hourly=True))
        self.assertEqual(days["2026-09-01"]["dispatched_oil_l"], 100.0)
        self.assertEqual(days["2026-09-04"]["dispatched_oil_l"], 200.0)
        self.assertEqual(days["2026-09-02"]["dispatched_oil_l"], 0.0)
        self.assertNotIn("2026-09-05", days)

    def test_a_dispatched_row_with_no_date_is_counted_not_dropped_silently(self):
        row = gate_row("2026-09-02", "JIVO_OIL", "HR1", 100.0)
        row["gate_out_date"], row["dispatched_at"] = None, None
        self.full_month(gate_rows=[row])
        data = fh.fetch(hourly=True)["data"]
        self.assertEqual(data["undated_dispatched_rows"], 1)
        self.assertIn("no date on them", " ".join(data["notes"]))

    def test_paging_follows_num_pages_and_stops_on_the_last(self):
        p1 = gate_envelope([gate_row("2026-09-01", "JIVO_OIL", "HR%d" % i, 10.0)
                            for i in range(100)], page=1, num_pages=2, count=150)
        p2 = gate_envelope([gate_row("2026-09-01", "JIVO_OIL", "HRB%d" % i, 10.0)
                            for i in range(50)], page=2, num_pages=2, count=150)
        fake = self.full_month(extra_gate_pages=[p2])
        fake.gate[0] = p1
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-01"]
        self.assertEqual(fake.gate_pages, 2)
        self.assertEqual(row["dispatched_oil_l"], 1500.0)
        self.assertEqual(row["trucks_oil"], 150)
        self.assertIsNone(env["error"])

    def test_a_full_last_page_with_a_page_count_is_NOT_called_cut_off(self):
        # 100 rows on the only page is a complete window when the answer says so.
        page = gate_envelope([gate_row("2026-09-01", "JIVO_OIL", "HR%d" % i, 10.0)
                              for i in range(100)], page=1, num_pages=1, count=100)
        fake = self.full_month()
        fake.gate = [page]
        env = fh.fetch(hourly=True)
        self.assertIsNone(env["error"])
        self.assertTrue(self.by_date(env)["2026-09-01"]["settled"])

    def test_a_page_two_failure_leaves_every_day_unsettled(self):
        p1 = gate_envelope([gate_row("2026-09-01", "JIVO_OIL", "HR%d" % i, 10.0)
                            for i in range(100)], page=1, num_pages=2, count=150)
        fake = self.full_month(extra_gate_pages=[None])
        fake.gate[0] = p1
        env = fh.fetch(hourly=True)
        self.assertIn("gate page 2", env["error"])
        self.assertFalse(any(r["settled"] for r in env["data"]["days"]))

    def test_a_failed_gate_page_leaves_the_day_unknown_not_zero(self):
        fake = self.full_month()
        fake.gate = [None]
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-01"]
        self.assertIsNone(row["dispatched_oil_l"])
        self.assertIsNone(row["trucks_oil"])
        self.assertFalse(row["settled"])
        self.assertFalse(env["ok"])
        self.assertIn("gate page 1", env["error"])

    def test_a_full_bare_array_page_is_flagged_as_maybe_cut_off(self):
        # No --page envelope: the CLI answered with a bare array, where a full
        # page is the only evidence the window was cut off.
        bare = [gate_row("2026-09-01", "JIVO_OIL", "HR%d" % i, 10.0) for i in range(100)]
        fake = self.full_month()
        fake.gate = [bare]
        env = fh.fetch(hourly=True)
        self.assertIn("may be cut off", env["error"])
        self.assertIsNone(self.by_date(env)["2026-09-02"]["dispatched_oil_l"])
        self.assertFalse(any(r["settled"] for r in env["data"]["days"]))


class Sunday(Base):
    TODAY = date(2026, 9, 8)     # 6 Sep 2026 is a Sunday

    def test_a_sunday_keeps_its_figures(self):
        daily, movement = {}, {}
        for d in range(1, 8):
            iso = "2026-09-%02d" % d
            daily[iso] = run_payload(a_run(d, "FG0000081", 10.0))
            movement[iso] = move_payload([gr_row("FG0000081", 100.0)])
        self.install(Fake(daily=daily, movement=movement,
                          gate=[gate_envelope([gate_row("2026-09-06", "JIVO_OIL",
                                                        "HR1", 4000.0)])]))
        row = self.by_date(fh.fetch(hourly=True))["2026-09-06"]
        self.assertEqual(row["weekday"], "Sunday")
        self.assertFalse(row["working"])
        self.assertEqual(row["made_mes_l"], 120.0)
        self.assertEqual(row["dispatched_oil_l"], 4000.0)


class Failures(Base):
    def test_a_failed_day_read_is_null_never_zero(self):
        fake = self.full_month()
        fake.daily["2026-09-02"] = None
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-02"]
        self.assertIsNone(row["made_mes_l"])
        self.assertIsNone(row["runs"])
        self.assertIsNotNone(row["made_booked_l"])     # the other half still read
        self.assertFalse(row["complete"])
        self.assertFalse(row["settled"])
        self.assertFalse(env["ok"])
        self.assertEqual(env["data"]["status"], "partial")

    def test_a_day_with_no_read_behind_it_at_all_is_missing_not_a_zero_row(self):
        # Every read for the 2nd fails, the gate included: there is no fact about
        # that day at all, so it is named as unread rather than drawn as empty.
        fake = self.full_month()
        fake.daily["2026-09-02"] = None
        fake.movement["2026-09-02"] = None
        fake.gate = [None]
        data = fh.fetch(hourly=True)["data"]
        self.assertNotIn("2026-09-02", [r["date"] for r in data["days"]])
        self.assertIn("2026-09-02", data["missing_dates"])
        self.assertEqual(data["status"], "partial")
        self.assertIn("not a day the plant did nothing", " ".join(data["notes"]))

    def test_failed_production_over_a_read_gate_keeps_the_day_with_nulls(self):
        # The gate window WAS read to the end, so "nothing left the gate" is a
        # fact about the 2nd. The two production figures are not — they stay null,
        # and the site draws a null as "not read", never as a bar of height zero.
        fake = self.full_month()
        fake.daily["2026-09-02"] = None
        fake.movement["2026-09-02"] = None
        row = self.by_date(fh.fetch(hourly=True))["2026-09-02"]
        self.assertIsNone(row["made_mes_l"])
        self.assertIsNone(row["made_booked_l"])
        self.assertEqual(row["dispatched_oil_l"], 0.0)
        self.assertFalse(row["complete"])
        self.assertFalse(row["settled"])


class Settling(Base):
    def test_only_days_two_days_old_settle(self):
        self.full_month()
        days = self.by_date(fh.fetch(hourly=True))
        self.assertTrue(days["2026-09-01"]["settled"])
        self.assertTrue(days["2026-09-02"]["settled"])
        self.assertTrue(days["2026-09-03"]["settled"])   # 5 - 3 = 2 days old
        self.assertFalse(days["2026-09-04"]["settled"])  # yesterday still moves

    def test_a_settled_day_is_not_read_again(self):
        self.full_month()
        fh.fetch(hourly=True)
        fake = self.full_month()                          # fresh call recorder
        fh.fetch(hourly=True)
        asked = {n.split("_", 1)[1] for n in fake.cli_names}
        self.assertEqual(asked, {"2026-09-04"})

    def test_a_settled_day_keeps_its_figures_across_cycles(self):
        self.full_month()
        first = self.by_date(fh.fetch(hourly=True))["2026-09-01"]
        self.full_month()
        second = self.by_date(fh.fetch(hourly=True))["2026-09-01"]
        self.assertEqual(first, second)


class Cache(Base):
    def test_a_cheap_cycle_makes_no_call_and_says_from_cache(self):
        self.full_month()
        fh.fetch(hourly=True)
        fake = self.full_month()
        env = fh.fetch(hourly=False)
        self.assertEqual(fake.cli_names, [])
        self.assertEqual(fake.gate_pages, 0)
        self.assertTrue(env["data"]["from_cache"])
        self.assertEqual(len(env["data"]["days"]), 4)

    def test_a_cold_cheap_cycle_reads_for_real(self):
        fake = self.full_month()
        env = fh.fetch(hourly=False)
        self.assertTrue(fake.cli_names)
        self.assertFalse(env["data"]["from_cache"])

    def test_a_cache_from_yesterday_is_not_served_after_midnight(self):
        self.full_month()
        fh.fetch(hourly=True)                     # cache written for 5 Sep

        class _Six(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 9, 6, 0, 20, 0, tzinfo=fh.IST)

        fh.datetime = _Six
        fake = self.full_month()
        fake.daily["2026-09-05"] = run_payload(a_run(9, "FG0000081", 7.0))
        fake.movement["2026-09-05"] = move_payload([gr_row("FG0000081", 5.0)])
        env = fh.fetch(hourly=False)
        self.assertFalse(env["data"]["from_cache"])
        self.assertIn("2026-09-05", [r["date"] for r in env["data"]["days"]])

    def test_a_cache_from_another_month_is_discarded(self):
        self.full_month()
        fh.fetch(hourly=True)
        with open(fh.CACHE_FILE) as handle:
            blob = fh.json.load(handle)
        blob["month"] = "2026-08"
        with open(fh.CACHE_FILE, "w") as handle:
            fh.json.dump(blob, handle)
        fake = self.full_month()
        env = fh.fetch(hourly=True)
        self.assertEqual(len({n.split("_", 1)[1] for n in fake.cli_names}), 4)
        self.assertEqual(len(env["data"]["days"]), 4)

    def test_a_wrong_shaped_cache_is_ignored(self):
        with open(fh.CACHE_FILE, "w") as handle:
            handle.write('{"month": "2026-09", "days": "not a dict"}')
        fake = self.full_month()
        env = fh.fetch(hourly=False)
        self.assertTrue(fake.cli_names)
        self.assertEqual(len(env["data"]["days"]), 4)

    def test_a_cycle_that_read_nothing_does_not_overwrite_a_good_cache(self):
        self.full_month()
        fh.fetch(hourly=True)
        with open(fh.CACHE_FILE) as handle:
            before = handle.read()
        fake = self.full_month()
        fake.daily, fake.movement, fake.gate = {}, {}, [None]
        fh.fetch(hourly=True)
        with open(fh.CACHE_FILE) as handle:
            self.assertEqual(handle.read(), before)

    def test_no_vehicle_or_document_identifier_reaches_the_cache(self):
        rows = [gate_row("2026-09-02", "JIVO_OIL", "HR55AB1234", 100.0)]
        self.full_month(gate_rows=rows)
        fh.fetch(hourly=True)
        with open(fh.CACHE_FILE) as handle:
            blob = handle.read()
        self.assertNotIn("HR55AB1234", blob)          # the plate
        self.assertNotIn('"vehicle_no"', blob)        # any field that could hold one
        self.assertNotIn("document_numbers", blob)    # a bill number
        self.assertNotIn("<doc>", blob)
        self.assertNotIn("driver", blob)


class Budget(Base):
    def test_a_spent_budget_leaves_the_rest_in_missing_dates(self):
        fake = self.full_month()
        fake.delay = 0.05
        fh.BUDGET_S = 0.06                       # one day's pair of calls, then stop
        data = fh.fetch(hourly=True)["data"]
        self.assertTrue(data["missing_dates"])
        self.assertEqual(data["status"], "partial")
        # newest first: yesterday is the day that must survive the budget
        self.assertIn("2026-09-04", [r["date"] for r in data["days"]])
        self.assertNotIn("2026-09-04", data["missing_dates"])


class MonthStart(Base):
    TODAY = date(2026, 9, 1)

    def test_on_the_first_there_is_nothing_to_show_and_that_is_fine(self):
        self.install(Fake(gate=[gate_envelope([])]))
        env = fh.fetch(hourly=True)
        data = env["data"]
        self.assertEqual(data["days"], [])
        self.assertEqual(data["missing_dates"], [])
        self.assertEqual(data["through"], "—")
        self.assertEqual(data["status"], "complete")


# ---------------------------------------------------------------------------
# Added by Proof (QA), 2026-09-05. Each of these pins a case the suite reached
# but never asserted, or a state the site is built to draw and the data has not
# produced yet this month.
# ---------------------------------------------------------------------------
class ProofMonthRollover(Base):
    """The 1st of the month: nothing has elapsed, so there is nothing to read.

    That is a SUCCESSFUL empty answer, not a failed source. `ok:false` here is
    read by collect.py as a failed adapter and by freeze_live as a half-failed
    source, which puts "factory_history half-failed this cycle — " (with an
    EMPTY reason, because error is None) into honesty.assumed on the site, all
    day, every 1st.
    """

    TODAY = date(2026, 10, 1)

    def test_the_first_of_the_month_is_a_success_not_a_failure(self):
        self.install(Fake(gate=[gate_envelope([])]))
        env = fh.fetch(hourly=True)
        self.assertEqual(env["data"]["days"], [])
        self.assertEqual(env["data"]["status"], "complete")
        self.assertIsNone(env["error"])
        self.assertTrue(env["ok"], "an empty month-start read must not report ok:false")

    def test_the_first_of_the_month_is_still_republished_cheaply(self):
        """And having read nothing, it must still cache, or every 3-minute cycle
        all day repeats the whole thing."""
        self.install(Fake(gate=[gate_envelope([])]))
        fh.fetch(hourly=True)
        fake = self.install(Fake(gate=[gate_envelope([])]))
        env = fh.fetch(hourly=False)
        self.assertTrue(env["data"]["from_cache"])
        self.assertEqual(fake.cli_names, [])
        self.assertEqual(fake.gate_pages, 0)


class UnknownShape(Base):
    """Exit 0, valid JSON, a body this reader does not recognise.

    Found by Cassius 2026-09-05: every sub-reader used to answer such a body with
    ZEROS — `_booked` its empty dict, `_billed` {0,0,0}, `_gate_page` ([], {}) —
    and `_read_gate` then read "no rows parsed" as "read to the end". A complete
    window with no bucket is defined as a real zero, so the day settled at zero,
    the month cached as `complete`, `ok` stayed true, every gen_live check passed
    (zeros are >= 0) and /days drew a month of empty bars badged HAPPENED, for the
    rest of the month, until somebody deleted the cache by hand.
    """

    UNKNOWN_MOVE = {"meta": {"source": "live"}, "results": {"meta": {"limit": 1000}, "ok": True}}
    UNKNOWN_DAILY = {"meta": {"source": "live"}, "results": {"runs": "moved elsewhere"}}
    UNKNOWN_GATE = {"meta": {"source": "live"}}

    def all_unknown(self):
        daily = {"2026-09-%02d" % d: self.UNKNOWN_DAILY for d in range(1, 5)}
        movement = {"2026-09-%02d" % d: self.UNKNOWN_MOVE for d in range(1, 5)}
        return self.install(Fake(daily=daily, movement=movement, gate=[self.UNKNOWN_GATE]))

    def test_a_month_of_unreadable_answers_is_never_a_month_of_zeros(self):
        self.all_unknown()
        env = fh.fetch(hourly=True)
        self.assertFalse(env["ok"], "an answer nobody could read must not report ok:true")
        self.assertIsNotNone(env["error"])
        self.assertNotEqual(env["data"]["status"], "complete")
        for row in env["data"]["days"]:
            self.assertIsNone(row["made_mes_l"], row["date"])
            self.assertIsNone(row["made_booked_l"], row["date"])
            self.assertIsNone(row["dispatched_oil_l"], row["date"])
            self.assertFalse(row["settled"], row["date"])
            self.assertFalse(row["complete"], row["date"])

    def test_the_unreadable_month_is_never_cached_as_settled(self):
        self.all_unknown()
        fh.fetch(hourly=True)
        fake = self.all_unknown()
        env = fh.fetch(hourly=False)
        # Either it did not cache at all (so the cheap cycle read again), or it
        # cached its own failure. What it may NEVER do is republish ok:true.
        self.assertFalse(env["ok"])
        self.assertTrue(fake.cli_names or env["data"]["from_cache"])

    def test_an_unrecognised_gate_page_leaves_the_day_unknown(self):
        fake = self.full_month()
        fake.gate = [self.UNKNOWN_GATE]
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-01"]
        self.assertIsNone(row["dispatched_oil_l"])       # not 0.0
        self.assertIsNone(row["trucks_oil"])
        self.assertFalse(row["settled"])
        self.assertFalse(env["ok"])
        self.assertIn("not a list of gate rows", env["error"])

    def test_an_unrecognised_movement_page_is_not_a_day_that_booked_nothing(self):
        fake = self.full_month()
        fake.movement["2026-09-02"] = self.UNKNOWN_MOVE
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-02"]
        self.assertIsNone(row["made_booked_l"])
        self.assertIsNone(row["billed_out_l"])
        self.assertIsNotNone(row["made_mes_l"])          # the machine log still read
        self.assertFalse(row["settled"])
        self.assertFalse(env["ok"])
        self.assertIn("not a page of godown movements", env["error"])

    def test_an_unrecognised_run_list_is_not_a_day_with_no_runs(self):
        fake = self.full_month()
        fake.daily["2026-09-03"] = self.UNKNOWN_DAILY
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-03"]
        self.assertIsNone(row["made_mes_l"])
        self.assertIsNone(row["runs"])
        self.assertFalse(row["settled"])
        self.assertFalse(env["ok"])
        self.assertIn("not a list of runs", env["error"])

    def test_the_error_names_the_shape_and_carries_no_row_content(self):
        fake = self.full_month()
        fake.movement["2026-09-02"] = {"meta": {"source": "live"},
                                       "results": {"secret_token": "abc123", "ok": True}}
        env = fh.fetch(hourly=True)
        self.assertIn("secret_token", env["error"])       # the FIELD name is useful
        self.assertNotIn("abc123", env["error"])          # its value never travels

    def test_a_month_cached_by_an_older_reader_is_thrown_away(self):
        # A settled day is kept for the rest of the month, so a month cached by
        # the reader that counted an unknown answer as zero must not survive the
        # fix. One extra full read after a deploy; a month of wrong records
        # otherwise, with nothing on the page to say so.
        self.full_month()
        fh.fetch(hourly=True)
        with open(fh.CACHE_FILE) as handle:
            blob = fh.json.load(handle)
        self.assertEqual(blob["reader"], fh.CACHE_READER)
        blob["reader"] = fh.CACHE_READER - 1
        with open(fh.CACHE_FILE, "w") as handle:
            fh.json.dump(blob, handle)
        fake = self.full_month()
        env = fh.fetch(hourly=False)
        self.assertTrue(fake.cli_names, "an older reader's cache must be re-read, not served")
        self.assertFalse(env["data"]["from_cache"])

    def test_an_empty_but_well_formed_answer_is_still_a_real_zero(self):
        # The other half of the rule: a genuine empty page is a FACT and must
        # still settle, or a quiet day would read as broken.
        daily = {"2026-09-%02d" % d: run_payload() for d in range(1, 5)}
        movement = {"2026-09-%02d" % d: move_payload([]) for d in range(1, 5)}
        self.install(Fake(daily=daily, movement=movement, gate=[gate_envelope([])]))
        env = fh.fetch(hourly=True)
        row = self.by_date(env)["2026-09-01"]
        self.assertTrue(env["ok"], env["error"])
        self.assertEqual(row["made_mes_l"], 0.0)
        self.assertEqual(row["made_booked_l"], 0.0)
        self.assertEqual(row["dispatched_oil_l"], 0.0)
        self.assertTrue(row["settled"])
        self.assertEqual(env["data"]["status"], "complete")


class ProofTotalFailure(Base):
    """Every call fails — an expired login, the plant's app down."""

    def test_nothing_read_is_unavailable_and_never_a_month_of_zeros(self):
        fake = self.install(Fake(daily={}, movement={}, gate=[None]))
        env = fh.fetch(hourly=True)
        data = env["data"]
        self.assertFalse(env["ok"])
        self.assertIsNotNone(env["error"])
        self.assertEqual(data["status"], "unavailable")
        self.assertEqual(data["days"], [])
        self.assertEqual(data["missing_dates"],
                         ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04"])
        self.assertFalse(os.path.exists(fh.CACHE_FILE),
                         "a cycle that read nothing must not write a cache")


class ProofSundayInRange(Base):
    """September 2026's Sundays all fall after today, so the real data never
    exercises the Sunday path. Stand on a date where it does: 7 Sep is a Monday,
    so 6 Sep (Sunday) is an elapsed day."""

    TODAY = date(2026, 9, 7)

    def test_an_elapsed_sunday_is_flagged_closed_and_keeps_what_it_filled(self):
        daily, movement = {}, {}
        for d in range(1, 7):
            iso = "2026-09-%02d" % d
            daily[iso] = run_payload(a_run(200 + d, "FG0000081", 50.0))
            movement[iso] = move_payload([gr_row("FG0000081", 600.0)])
        self.install(Fake(daily=daily, movement=movement,
                          gate=[gate_envelope([gate_row("2026-09-06", "JIVO_OIL",
                                                        "TRUCK-1", 4000.0)])]))
        rows = self.by_date(fh.fetch(hourly=True))
        sunday = rows["2026-09-06"]
        self.assertEqual(sunday["weekday"], "Sunday")
        self.assertFalse(sunday["working"])
        self.assertEqual(sunday["made_mes_l"], 600.0)      # NOT zeroed to the plan
        self.assertEqual(sunday["dispatched_oil_l"], 4000.0)
        self.assertTrue(rows["2026-09-05"]["working"])


class ProofNoDoubleCount(Base):
    """The one arithmetic that must never happen anywhere in the payload."""

    def test_no_figure_in_the_payload_equals_mes_plus_booked(self):
        self.install(self.full_month())
        data = fh.fetch(hourly=True)["data"]
        for row in data["days"]:
            merged = round((row["made_mes_l"] or 0) + (row["made_booked_l"] or 0), 3)
            for key, value in row.items():
                if isinstance(value, (int, float)) and merged:
                    self.assertNotEqual(round(float(value), 3), merged,
                                        "%s on %s equals mes+booked" % (key, row["date"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
