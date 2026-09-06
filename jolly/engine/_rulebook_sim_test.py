#!/usr/bin/env python3
"""_rulebook_sim_test.py — Mark 4's rulebook mode, proved on a synthetic plant.

    cd jolly && python3 -m unittest engine._rulebook_sim_test -v

engine/august_sim.py is a script, not a library, so it is tested the way it is run: as a
subprocess, in a throwaway directory, on inputs written for the test. Two things are
proved here and nothing else can prove them:

  * with a `rulebook` in the inputs the machine rules hold — a tin only where a tin can be
    filled, a bottle family only where that bottle runs, one product change a line a
    session, ONE line at night with its reason, Sunday making nothing and still
    dispatching, drums never scheduled at all, and the planning speeds used ONCE (A01);
  * without one, the engine is the calibrated August engine, to the litre.

The underscore keeps the file out of any adapter/module discovery (commit b1c6facf).
"""
import collections
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
JOLLY = os.path.dirname(HERE)
ENGINE = os.path.join(HERE, "august_sim.py")
CLEAR_H = 51.3 / 60.0

D0, D1 = "2026-09-07", "2026-09-15"          # Monday .. Tuesday, one Sunday inside (13th)
SUNDAY = "2026-09-13"

# ---------------------------------------------------------------- the synthetic plant
# Six products, one of every shape the rulebook has an opinion about, and one combo set.
SKUS = [
    # code        sku                              lpc  slot   family  fills  head        pieces
    ("FGT15", "TIN OIL 15 LTR",                    15.0, "15L", "TIN",   1, "COMMODITY",   2000),
    ("FGT05", "TIN OIL 5 LTR",                      5.0, "5L",  "TIN",   1, "COMMODITY",   2000),
    ("FGH03", "HDPE OIL 3 LTR",                     3.0, "3L",  "HDPE",  1, "COMMODITY",   2000),
    ("FGB26", "MUSTARD KACHI GHANI 1 LTR",          1.0, "1L",  "26G",   1, "PREMIUM",    40000),
    ("FGB40", "CANOLA 1 LTR",                       1.0, "1L",  "40G",   1, "COMMODITY",   1200),
    ("FGC40", "CANOLA 1 LTR + 1 LTR COMBO SET",     2.0, "1L",  "40G",   2, "COMMODITY",   3000),
    ("FGD20", "OLIVE 200 LTR DRUM",               200.0, "DRUM", "DRUM", 1, "PREMIUM",      100),
]
LINES = {                                   # containers an hour, already post-efficiency
    "Tin Head":   {"15L": 20.0, "5L": 20.0, "3L": 20.0},
    "6 Head":     {"5L": 60.0, "3L": 60.0, "1L": 100.0},
    "JP Machine": {"1L": 200.0},
    "Clear Pack": {"1L": 200.0, "5L": 100.0},
}
LINES_MULTI = {"Clear Pack": {"1L": 100.0}}          # the only line with a combo record (B19)
RB_LINES = {
    "Tin Head":   {"slots": {"15L": {"TIN": 1}, "5L": {"TIN": 2}, "3L": {"TIN": 1}}},
    "6 Head":     {"slots": {"5L": {"HDPE": 1, "TIN": 1}, "3L": {"HDPE": 1, "TIN": 2},
                             "1L": {"ANY": 3}}},
    "JP Machine": {"slots": {"1L": {"26G": 1, "SMALL": 1, "52G": 3}}},
    "Clear Pack": {"slots": {"1L": {"40G": 1, "52G": 2}, "5L": {"HDPE": 1}}},
}


def _dates():
    d, out = date.fromisoformat(D0), []
    while d <= date.fromisoformat(D1):
        out.append(d.isoformat()); d += timedelta(days=1)
    return out


def inputs(rulebook=True, efficiency=1.0, shift_hours=12, legacy_15l=False):
    """A whole plant in one dict. `legacy_15l` gives the no-rulebook run a 15 L PET SKU and
    a line with a 5 L slot only — the derivation the rulebook turns off."""
    plan, bom, items, realise, fg0, stock = [], {}, {}, {}, {}, {}
    for code, sku, lpc, slot, fam, fills, head, pieces in SKUS:
        pack = {"DRUM": "DRUM", "POUCH": "POUCH"}.get(slot, "TIN" if fam == "TIN" else "PET")
        # NO trailing_l_per_month here on purpose: nothing in the repo writes it today, so
        # a synthetic plant that invents it — and invents it as the SAME number for every
        # SKU — proves nothing about the tier-1 ranking and hides that it was dead in
        # production. TrailingSalesRanking below feeds it real, differing values.
        plan.append(dict(code=code, sku=sku, head=head, category="OIL", pack_type=pack,
                         litres_per_piece=lpc, pieces=pieces, litres=pieces * lpc))
        bom[code] = [["RM0000001", lpc], ["PM" + code, float(fills)]]
        items["PM" + code] = dict(name="CONTAINER " + sku, uom="PCS")
        realise[code] = 150.0
        stock["PM" + code] = 4_000_000.0
    if legacy_15l:
        plan.append(dict(code="FGP15", sku="PET OIL 15 LTR", head="COMMODITY", category="OIL",
                         pack_type="PET", litres_per_piece=15.0, pieces=2000, litres=30000.0))
        bom["FGP15"] = [["RM0000001", 15.0], ["PMFGP15", 1.0]]
        items["PMFGP15"] = dict(name="PET JAR 15 LTR", uom="PCS"); realise["FGP15"] = 150.0
        stock["PMFGP15"] = 400_000.0
    items["RM0000001"] = dict(name="THE OIL", uom="LTR")
    stock["RM0000001"] = 40_000_000.0

    orders = []
    for i, d in enumerate(_dates()):
        # one real order a day on the mustard (so JP carries the most ordered litres and
        # is the night line), and expected rows on the rest — triple-tagged as always.
        orders.append(dict(docnum=f"PO-{i:02d}", customer="A REAL CUSTOMER", channel="GT",
                           code="FGB26", date=d, pieces=4000, value=600000.0))
        for code in ("FGT15", "FGT05", "FGH03", "FGB40", "FGC40") + (("FGP15",) if legacy_15l else ()):
            orders.append(dict(docnum=f"FCST-W1-{code}", customer="(forecast — not yet ordered)",
                               channel="FORECAST", code=code, date=d, pieces=200, value=0.0))
    S = dict(
        meta=dict(horizon=[D0, D1]),
        lines={ln: dict(sl) for ln, sl in LINES.items()},
        rules=dict(shift_hours=shift_hours, sundays_off=True, flush_litres=400,
                   line_clearance_min=51.3, efficiency=efficiency,
                   storage_ceiling_l=90_000_000, storage_peak_l=99_000_000,
                   lead_days=dict(oil=11, packaging=6), invoice_truck_lag_days=2),
        opening=dict(stock=stock, fg=fg0, fg_other_l=0, standing_l=0),
        plan=plan, bom=bom, blends={}, items=items, realise=realise,
        orders=orders, backlog=[], inbound_prebooked={},
        actuals_for_scoring=dict(made_l=1, line_utilisation_pct=1, plan_pct=1),
    )
    if legacy_15l:
        S["lines"] = {"Clear Pack": {"1L": 200.0, "5L": 100.0}, "6 Head": {"5L": 60.0, "1L": 100.0}}
    if rulebook:
        S["lines_multi"] = {ln: dict(sl) for ln, sl in LINES_MULTI.items()}
        S["rulebook"] = dict(
            version="mark4-test",
            shift=dict(hours_per_session=10, sessions_per_day_max=2, night_lines_max=1,
                       sundays_off=True),
            efficiency=dict(planning_factor=0.8, min_runs_for_cap=3),
            changeover=dict(clearance_min=51.3, flush_l_per_oil_change=400,
                            one_product_per_line_per_session=True),
            night=dict(pick="most PO-backed litres unmade after the day session; tie -> JP"),
            drums=dict(scheduled=False, skus=["FGD20"], display="filled by hand, not scheduled here"),
            demand=dict(months=3, priority=["PO-backed", "expected", "plan-sheet remainder"]),
            lines={ln: dict(v) for ln, v in RB_LINES.items()},
            sku_pack={code: dict(sku=sku, slot=slot, family=fam, fills_per_piece=fills,
                                 litres_per_piece=lpc)
                      for code, sku, lpc, slot, fam, fills, _h, _p in SKUS},
        )
    # DEEP. `lines={ln: dict(v) …}` copied the outer dict and shared every `slots` map
    # with the module-level RB_LINES, so a test that did `S["rulebook"]["lines"][ln]
    # ["slots"].pop("3L")` changed the plant for every test that ran after it — measured:
    # SpillOrder went vacuous and NoLineSkus reported a SKU the stock plant can fill.
    # A fixture builder that hands out shared mutable state is a test that lies.
    return copy.deepcopy(S)


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run_engine(S, tag="-t", env_extra=None):
    """Run the engine the way the loop runs it and read back everything it wrote."""
    tmp = tempfile.mkdtemp(prefix="mark4-sim-")
    try:
        os.makedirs(os.path.join(tmp, "sim"))
        path = os.path.join(tmp, "inputs.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(S, fh)
        env = dict(os.environ, SIM_INPUTS=path, SIM_TAG=tag)
        for k in ("SIM_HOURS", "SIM_SUNDAYS_OFF", "SIM_HOURS_SCHEDULE"):
            env.pop(k, None)
        env.update(env_extra or {})
        r = subprocess.run([sys.executable, ENGINE], cwd=tmp, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = dict(rc=r.returncode, stdout=r.stdout.decode("utf-8", "replace"),
                   stderr=r.stderr.decode("utf-8", "replace"), days=[], summary=None)
        sdir = os.path.join(tmp, "sim")
        sfile = os.path.join(sdir, f"summary{tag}.json")
        if os.path.exists(sfile):
            out["summary"] = _read(sfile)
        ddir = os.path.join(sdir, f"days{tag}")
        if os.path.isdir(ddir):
            out["days"] = [_read(os.path.join(ddir, f))
                           for f in sorted(os.listdir(ddir)) if f.startswith("day-")]
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class RulebookMode(unittest.TestCase):
    """One run of the synthetic plant, read every way the rulebook can be broken."""

    @classmethod
    def setUpClass(cls):
        cls.r = run_engine(inputs())
        if cls.r["rc"] != 0:
            raise AssertionError(f"the engine failed (rc={cls.r['rc']}):\n{cls.r['stderr']}")
        cls.days = cls.r["days"]
        cls.runs = [dict(r, date=d["date"]) for d in cls.days for r in d["runs"]]

    def line_of(self, code):
        return sorted({r["line"] for r in self.runs if r["code"] == code})

    # ---- AC01 / AC07: the machine has to be able to fill it, in that bottle
    def test_tins_only_where_tins_are_filled(self):
        tin = sorted({r["line"] for r in self.runs if r["family"] == "TIN"})
        self.assertTrue(set(tin) <= {"Tin Head", "6 Head"}, tin)
        self.assertEqual(self.line_of("FGT15"), ["Tin Head"], "15 L tins are the Tin Head's alone (R07)")
        self.assertTrue(self.runs, "the synthetic plant made nothing at all")

    def test_three_litre_never_on_clear_pack(self):
        self.assertNotIn("Clear Pack", self.line_of("FGH03"))
        self.assertTrue(set(self.line_of("FGH03")) <= {"6 Head", "Tin Head"}, self.line_of("FGH03"))

    def test_bottle_families_hold(self):
        self.assertNotIn("Clear Pack", self.line_of("FGB26"), "26 g bottles never on Clear Pack (A14)")
        self.assertNotIn("JP Machine", self.line_of("FGB40"), "40 g bottles never on JP (A14)")
        for r in self.runs:
            fams = RB_LINES[r["line"]]["slots"][r["slot"]]
            self.assertTrue(r["family"] in fams or "ANY" in fams,
                            f"{r['sku']} ({r['family']}) has no business on {r['line']}")
            self.assertEqual(r["pref"], fams.get(r["family"], fams.get("ANY")))

    # ---- AC03: drums are filled by hand and are out of the schedule entirely
    def test_drums_are_never_scheduled_and_never_stuck(self):
        self.assertEqual([r for r in self.runs if r["code"] == "FGD20"], [])
        self.assertEqual([b for d in self.days for b in d["blocked"] if b["code"] == "FGD20"], [])
        self.assertEqual(self.r["summary"]["rulebook"]["manual_skus"], ["FGD20"])

    # ---- AC04: 10 hours a line, 20 for the one line that runs at night
    def test_hours_per_line_and_the_named_night_line(self):
        for d in self.days:
            night = (d.get("night_line") or {}).get("line")
            self.assertIn("night_line", d, f"{d['date']} does not name a night line")
            self.assertTrue((d["night_line"]["reason"] or "").strip(), f"{d['date']} gives no reason")
            for ln, h in d["line_hours"].items():
                cap = 20.01 if ln == night else 10.01
                self.assertLessEqual(h, cap, f"{ln} ran {h} h on {d['date']}")
                self.assertLessEqual(h, d["line_hours_max"][ln] + 0.05)
            if night:
                self.assertEqual(d["line_hours_max"][night], 20.0)
                self.assertEqual(night, d["night_line"]["candidates"][0]["line"],
                                 "the night line must be the top of its own candidate list (B03)")
        self.assertEqual(self.r["summary"]["rulebook"]["hours_per_session"], 10,
                         "the rulebook sets the shift, not rules.shift_hours (12 in these inputs)")
        self.assertIsNone(self.r["summary"]["rulebook"]["hours_override"])

    def test_the_night_line_is_where_the_orders_are(self):
        # every day carries a real mustard order and JP is the only line that fills 26 g
        # first, so JP is where the unmade ordered litres pile up.
        picks = {(d.get("night_line") or {}).get("line") for d in self.days if d["working"]}
        self.assertEqual(picks, {"JP Machine"}, picks)
        self.assertEqual(self.r["summary"]["rulebook"]["night_sessions"],
                         sum(1 for d in self.days if d["working"]))

    # ---- R04 / A11 / B04: Sunday makes nothing and still dispatches
    def test_sunday_makes_nothing_and_still_dispatches(self):
        sun = [d for d in self.days if d["date"] == SUNDAY]
        self.assertEqual(len(sun), 1)
        sun = sun[0]
        self.assertFalse(sun["working"])
        self.assertEqual(sun["made_litres"], 0)
        self.assertEqual(sorted(set(sun["line_hours"].values())), [0])
        self.assertEqual(sun["runs"], [])
        self.assertGreater(sun["shipped_litres"], 0, "Sunday is for dispatch (R04)")
        self.assertTrue(sun["dispatched"])
        self.assertIsNone(sun["night_line"]["line"])
        self.assertIn("Sunday", sun["night_line"]["reason"])

    # ---- B01: a product only moves to a lesser machine when the better one is full
    def test_spill_only_when_the_better_line_is_full(self):
        for d in self.days:
            if not d["working"]:
                continue
            night = (d["night_line"] or {}).get("line")
            for r in d["runs"]:
                if r["pref"] == 1:
                    continue
                for m in RB_LINES:
                    if m == r["line"] or m == night:
                        continue          # the night line gains 10 h after the day session
                    fams = RB_LINES[m]["slots"].get(r["slot"])
                    better = fams and fams.get(r["family"], fams.get("ANY"))
                    if better and better < r["pref"] and m in LINES and r["slot"] in LINES[m]:
                        left = d["line_hours_max"][m] - d["line_hours"][m]
                        self.assertLessEqual(left, CLEAR_H + 0.15,
                                             f"{r['sku']} went to {r['line']} (pref {r['pref']}) while "
                                             f"{m} still had {left:.2f} h on {d['date']}")

    # ---- B02: one product change a line a session, and every lift is printed
    def test_one_product_change_per_line_per_session(self):
        # the budget is per line PER SESSION — spending a night lift on the day session's
        # allowance let a line change twice as often as B02 allows and still pass.
        for d in self.days:
            lifts = {}
            for x in d["decisions"]:
                if x["kind"] == "CHANGE_CAP_LIFTED":
                    lifts[(x["line"], x["night"])] = lifts.get((x["line"], x["night"]), 0) + 1
                    self.assertIn("rather than stand idle", x["text"])
                    self.assertGreaterEqual(x["nth"], 1)
            for ln in LINES:
                for sess in (False, True):
                    codes = [r["code"] for r in d["runs"] if r["line"] == ln and r["night"] is sess]
                    changes = sum(1 for a, b in zip(codes, codes[1:]) if a != b)
                    self.assertLessEqual(changes, 1 + lifts.get((ln, sess), 0),
                                         f"{ln} changed product {changes} times in the "
                                         f"{'night' if sess else 'day'} session on {d['date']} "
                                         f"with {lifts.get((ln, sess), 0)} lift(s) logged")

    def test_the_day_file_says_how_many_products_each_line_really_ran(self):
        # R06 is "one product on a line all day". The lift count alone understates how far
        # the plan is from it, because the first change of every session is free — so the
        # day file publishes the TRUE number of changes per line and nothing has to be
        # inferred from the decisions list.
        for d in self.days:
            self.assertEqual(sorted(d["product_changes"]), sorted(LINES), d["date"])
            if not d["working"]:
                self.assertEqual(sorted(set(d["product_changes"].values())), [0], d["date"])
                continue
            lifts = collections.Counter(x["line"] for x in d["decisions"]
                                        if x["kind"] == "CHANGE_CAP_LIFTED")
            for ln in LINES:
                inside = 0
                for sess in (False, True):
                    codes = [r["code"] for r in d["runs"] if r["line"] == ln and r["night"] is sess]
                    inside += sum(1 for a, b in zip(codes, codes[1:]) if a != b)
                # one free change a session, two sessions, plus every logged lift
                self.assertGreaterEqual(d["product_changes"][ln], inside, f"{ln} {d['date']}")
                self.assertLessEqual(d["product_changes"][ln], 2 + lifts.get(ln, 0),
                                     f"{ln} {d['date']}")
        rb = self.r["summary"]["rulebook"]
        self.assertEqual(rb["product_changes"],
                         sum(sum(d["product_changes"].values()) for d in self.days))
        self.assertGreaterEqual(rb["product_changes"], rb["change_cap_lifted"],
                                "a lift is a change, so the true count can never be the smaller")

    # ---- B13 / B19: a combo set fills two bottles, at the line's combo rate
    def test_a_combo_set_is_planned_in_bottles(self):
        combo = [r for r in self.runs if r["code"] == "FGC40"]
        self.assertTrue(combo, "the combo set never ran")
        self.assertEqual(sorted({r["line"] for r in combo}), ["Clear Pack"],
                         "only the line with a combo record may run one (B19)")
        for r in combo:
            self.assertEqual(r["fills"], 2)
            self.assertEqual(r["containers"], r["pieces"] * 2)
            self.assertAlmostEqual(r["hours"], r["pieces"] * 2 / LINES_MULTI["Clear Pack"]["1L"], delta=0.02)

    # ---- A01: the planning speeds are applied ONCE
    def test_efficiency_is_one_and_the_speed_is_the_planning_speed(self):
        self.assertEqual(self.r["summary"]["rulebook"]["efficiency_applied"], 1.0)
        for r in self.runs:
            if r["fills"] == 1:
                self.assertAlmostEqual(r["hours"], r["pieces"] / LINES[r["line"]][r["slot"]], delta=0.02)

    def test_the_summary_says_what_the_rulebook_did(self):
        rb = self.r["summary"]["rulebook"]
        self.assertEqual(rb["version"], "mark4-test")
        self.assertTrue(rb["applied"] and rb["dispatch_on_sunday"] and rb["sundays_off"])
        self.assertEqual(rb["unmapped_codes"], [])
        self.assertEqual(rb["multi_fill_skus"], ["FGC40"])
        self.assertEqual(rb["multi_fill_no_rate"], [])
        self.assertTrue(set(rb["prefs_used"]) <= {"1", "2", "3"})
        self.assertEqual(rb["inputs_shift_hours"], 12)

    def test_forecast_rows_stay_tagged_and_never_become_orders(self):
        for d in self.days:
            for o in d["new_orders"]:
                if o["docnum"].startswith("FCST-"):
                    self.assertEqual(o["channel"], "FORECAST")


# ------------------------------------------------- a second plant, built for one question
# B01 asks "is every better machine full?" — and at night the answer has to be about THIS
# session. Two lines, three oils, arranged so the day line stops with hours on the clock:
# Clear Pack fills its 320 groundnut bottles at 60/h and then cannot start the canola,
# because changing oil costs 400 L / 60 an hour plus a clearance (7.5 h) and it has 4.7 h
# left. So it stands there, every day, with canola still wanted. JP finishes the mustard at
# night and asks for that canola at preference 2 — and the only thing that could hold it
# back is a machine that is not running at all.
SPILL_LINES = {"JP Machine": {"1L": 200.0}, "Clear Pack": {"1L": 60.0}}
SPILL_RB_LINES = {
    "JP Machine": {"slots": {"1L": {"26G": 1, "40G": 2}}},
    "Clear Pack": {"slots": {"1L": {"52G": 1, "40G": 1}}},
}
SPILL_SKUS = [
    # code     sku                  lpc  slot  family  oil          head
    ("FGM26", "MUSTARD 1 LTR",      1.0, "1L", "26G", "RM0000001", "COMMODITY"),
    ("FGS52", "GROUNDNUT 1 LTR",    1.0, "1L", "52G", "RM0000002", "COMMODITY"),
    ("FGC40", "CANOLA 1 LTR",       1.0, "1L", "40G", "RM0000003", "COMMODITY"),
]


def spill_inputs():
    plan, bom, items, realise, stock = [], {}, {}, {}, {}
    for code, sku, lpc, slot, fam, oil, head in SPILL_SKUS:
        # pieces 0: want() is then the ORDER book alone, so each day's demand is exactly
        # what the day's rows carry and the arithmetic above holds on every working day.
        plan.append(dict(code=code, sku=sku, head=head, category="OIL", pack_type="PET",
                         litres_per_piece=lpc, pieces=0, litres=0.0))
        bom[code] = [[oil, lpc], ["PM" + code, 1.0]]
        items["PM" + code] = dict(name="BOTTLE " + sku, uom="PCS")
        items[oil] = dict(name="OIL " + oil, uom="LTR")
        realise[code] = 150.0
        stock["PM" + code] = 4_000_000.0
        stock[oil] = 4_000_000.0
    orders = []
    for i, d in enumerate(_dates()):
        # more mustard a day than JP can fill in one session, so JP always carries the most
        # ordered litres into the night — and finishes them with hours left.
        orders.append(dict(docnum=f"PO-M-{i:02d}", customer="A REAL CUSTOMER", channel="GT",
                           code="FGM26", date=d, pieces=2600, value=390000.0))
        orders.append(dict(docnum=f"PO-S-{i:02d}", customer="A REAL CUSTOMER", channel="GT",
                           code="FGS52", date=d, pieces=320, value=48000.0))
        orders.append(dict(docnum=f"FCST-C-{i:02d}", customer="(forecast — not yet ordered)",
                           channel="FORECAST", code="FGC40", date=d, pieces=2000, value=0.0))
    return dict(
        meta=dict(horizon=[D0, D1]),
        lines={ln: dict(sl) for ln, sl in SPILL_LINES.items()},
        lines_multi={},
        rules=dict(shift_hours=12, sundays_off=True, flush_litres=400, line_clearance_min=51.3,
                   efficiency=1.0, storage_ceiling_l=90_000_000, storage_peak_l=99_000_000,
                   lead_days=dict(oil=11, packaging=6), invoice_truck_lag_days=2),
        opening=dict(stock=stock, fg={}, fg_other_l=0, standing_l=0),
        plan=plan, bom=bom, blends={}, items=items, realise=realise,
        orders=orders, backlog=[], inbound_prebooked={},
        actuals_for_scoring=dict(made_l=1, line_utilisation_pct=1, plan_pct=1),
        rulebook=dict(
            version="mark4-spill",
            shift=dict(hours_per_session=10, sessions_per_day_max=2, night_lines_max=1,
                       sundays_off=True),
            efficiency=dict(planning_factor=0.8, min_runs_for_cap=3),
            changeover=dict(clearance_min=51.3, flush_l_per_oil_change=400,
                            one_product_per_line_per_session=True),
            night=dict(pick="most PO-backed litres unmade after the day session; tie -> JP"),
            drums=dict(scheduled=False, skus=[], display="filled by hand, not scheduled here"),
            demand=dict(months=3, priority=["PO-backed", "expected", "plan-sheet remainder"]),
            lines={ln: dict(v) for ln, v in SPILL_RB_LINES.items()},
            sku_pack={code: dict(sku=sku, slot=slot, family=fam, fills_per_piece=1,
                                 litres_per_piece=lpc)
                      for code, sku, lpc, slot, fam, _o, _h in SPILL_SKUS},
        ),
    )


class NightSessionSpill(unittest.TestCase):
    """B01's "every better machine is full" has to mean full OF THIS SESSION.

    At night one line runs and the rest are dark. A dark machine's leftover day hours are
    not a reason to leave the one running line idle — it cannot use them, nobody is standing
    at it, and the work it is holding back is work that will not be done at all (R03/B01).
    """

    @classmethod
    def setUpClass(cls):
        cls.r = run_engine(spill_inputs(), tag="-spill")
        if cls.r["rc"] != 0:
            raise AssertionError(f"the engine failed (rc={cls.r['rc']}):\n{cls.r['stderr']}")
        cls.days = cls.r["days"]

    def _spare(self, d, ln):
        return d["line_hours_max"][ln] - d["line_hours"][ln]

    def test_the_night_belongs_to_jp_with_mustard_still_ordered(self):
        picks = {(d.get("night_line") or {}).get("line") for d in self.days if d["working"]}
        self.assertEqual(picks, {"JP Machine"}, picks)

    def test_a_machine_that_is_not_running_does_not_hold_the_night_line_back(self):
        got = [(d["date"], self._spare(d, "Clear Pack")) for d in self.days
               for r in d["runs"] if r["code"] == "FGC40" and r["line"] == "JP Machine" and r["night"]]
        self.assertTrue(got, "the night line was refused its preference-2 work by a machine that "
                             "was not running — B01 read against the DAY session's free hours")
        for when, spare in got:
            self.assertGreater(spare, CLEAR_H + 0.15,
                               f"Clear Pack was full anyway on {when} ({spare:.2f} h) — vacuous")

    def test_the_day_session_still_obeys_the_spill_rule(self):
        for d in self.days:
            for r in d["runs"]:
                if r["code"] == "FGC40" and not r["night"]:
                    self.assertEqual(r["line"], "Clear Pack",
                                     f"canola opened on a lesser machine in the DAY session on "
                                     f"{d['date']} with Clear Pack still holding "
                                     f"{self._spare(d, 'Clear Pack'):.2f} h")


# ------------------------------------------------ a third plant, for R19's tier-1 ranking
# One machine, one bottle, one preference: the ONLY thing that can order these three
# products is the tier-1 tie-break. FGHI has the trailing sales, FGLO has the bigger
# expected stream, and they disagree on purpose — so a run that follows one of them cannot
# be following plan-sheet insertion order, which is what the tier really did until
# 2026-09-06 (a field nothing wrote, read as 0 for every SKU, 54% of September's litres).
TRAIL_LINE = {"Clear Pack": {"1L": 100.0}}
TRAIL_RB_LINES = {"Clear Pack": {"slots": {"1L": {"40G": 1}}}}
# The three signals that could order this tier point three different ways on purpose:
# trailing sales say FGHI, the expected stream says FGLO, and rupees an hour (what tiers 0
# and 2 rank on) says FGNO. Whichever the engine follows, it is naming itself.
TRAIL_SKUS = [
    # code    sku                        trailing_l_per_month   fcst/day   realise
    ("FGHI", "CANOLA 1 LTR",                          50000.0,      3000,    100.0),
    ("FGLO", "SUNFLOWER 1 LTR",                        5000.0,      4000,    120.0),
    ("FGNO", "A PRODUCT THAT SELLS NOTHING",              None,       500,    200.0),
]


def trailing_inputs(with_trailing=True):
    plan, bom, items, realise, stock, orders = [], {}, {}, {}, {}, []
    for code, sku, trail, _fc, rs in TRAIL_SKUS:
        row = dict(code=code, sku=sku, head="COMMODITY", category="OIL", pack_type="PET",
                   litres_per_piece=1.0, pieces=0, litres=0.0)
        if with_trailing and trail is not None:
            row["trailing_l_per_month"] = trail
        plan.append(row)
        bom[code] = [["RM0000001", 1.0], ["PM" + code, 1.0]]
        items["PM" + code] = dict(name="BOTTLE " + sku, uom="PCS")
        realise[code] = rs
        stock["PM" + code] = 4_000_000.0
    items["RM0000001"] = dict(name="THE OIL", uom="LTR")
    stock["RM0000001"] = 40_000_000.0
    for i, d in enumerate(_dates()):
        for code, _sku, _t, fc, _r in TRAIL_SKUS:
            orders.append(dict(docnum=f"FCST-{code}-{i:02d}", customer="(forecast — not yet ordered)",
                               channel="FORECAST", code=code, date=d, pieces=fc, value=0.0))
    return dict(
        meta=dict(horizon=[D0, D1]),
        lines={ln: dict(sl) for ln, sl in TRAIL_LINE.items()}, lines_multi={},
        rules=dict(shift_hours=12, sundays_off=True, flush_litres=400, line_clearance_min=51.3,
                   efficiency=1.0, storage_ceiling_l=90_000_000, storage_peak_l=99_000_000,
                   lead_days=dict(oil=11, packaging=6), invoice_truck_lag_days=2),
        opening=dict(stock=stock, fg={}, fg_other_l=0, standing_l=0),
        plan=plan, bom=bom, blends={}, items=items, realise=realise,
        orders=orders, backlog=[], inbound_prebooked={},
        actuals_for_scoring=dict(made_l=1, line_utilisation_pct=1, plan_pct=1),
        rulebook=dict(
            version="mark4-trailing",
            shift=dict(hours_per_session=10, sessions_per_day_max=2, night_lines_max=1,
                       sundays_off=True),
            efficiency=dict(planning_factor=0.8, min_runs_for_cap=3),
            changeover=dict(clearance_min=51.3, flush_l_per_oil_change=400,
                            one_product_per_line_per_session=True),
            night=dict(pick="most PO-backed litres unmade after the day session; tie -> JP"),
            drums=dict(scheduled=False, skus=[], display="filled by hand, not scheduled here"),
            demand=dict(months=3, priority=["PO-backed", "expected", "plan-sheet remainder"]),
            lines={ln: dict(v) for ln, v in TRAIL_RB_LINES.items()},
            sku_pack={code: dict(sku=sku, slot="1L", family="40G", fills_per_piece=1,
                                 litres_per_piece=1.0) for code, sku, _t, _f, _r in TRAIL_SKUS},
        ),
    )


class TrailingSalesRanking(unittest.TestCase):
    """R19/B08: a product nobody has ordered yet is ranked by its TRAILING sales.

    Both runs below use the same plant and the same expected orders. The only difference is
    whether the plan rows carry `trailing_l_per_month`, and the two answers are OPPOSITE —
    so neither of them can be the order the rows happen to sit in.
    """

    def test_the_trailing_figure_on_the_plan_row_decides_the_tier(self):
        r = run_engine(trailing_inputs(True), tag="-trail")
        self.assertEqual(r["rc"], 0, r["stderr"])
        made = {run["code"] for d in r["days"] for run in d["runs"]}
        self.assertEqual(made, {"FGHI"}, "the biggest trailing seller takes the machine (R19)")
        rb = r["summary"]["rulebook"]
        self.assertIn("trailing_l_per_month on the plan rows", rb["trailing_source"])
        self.assertEqual(rb["no_trailing_codes"], ["FGNO"],
                         "a SKU with expected demand and no sales behind it is NAMED (R19)")

    def test_without_the_field_the_engine_ranks_on_its_own_expected_stream_and_says_so(self):
        r = run_engine(trailing_inputs(False), tag="-notrail")
        self.assertEqual(r["rc"], 0, r["stderr"])
        made = {run["code"] for d in r["days"] for run in d["runs"]}
        self.assertEqual(made, {"FGLO"}, "the fallback ranks by expected litres, biggest first")
        rb = r["summary"]["rulebook"]
        self.assertIn("this run's own expected-order stream", rb["trailing_source"])
        self.assertEqual(rb["no_trailing_codes"], [],
                         "under the fallback every expected SKU has a figure by construction")

    def test_the_source_is_always_named_so_a_dead_ranking_cannot_hide(self):
        for S in (trailing_inputs(True), trailing_inputs(False), inputs()):
            r = run_engine(S, tag="-src")
            self.assertTrue((r["summary"]["rulebook"]["trailing_source"] or "").strip(),
                            "rulebook mode must name what ranked the expected-only tier")


class ScenarioAndGuards(unittest.TestCase):

    def test_an_efficiency_that_is_not_one_is_refused(self):
        r = run_engine(inputs(efficiency=0.5), tag="-eff")
        self.assertNotEqual(r["rc"], 0, "a double derate must stop the run, not run at half")
        self.assertIn("rules.efficiency 1.0", r["stderr"])
        self.assertIn("(A01)", r["stderr"])

    def test_sim_hours_is_a_scenario_and_is_recorded(self):
        r = run_engine(inputs(), tag="-h8", env_extra=dict(SIM_HOURS="8"))
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["hours_override"], "8")
        self.assertEqual(r["summary"]["rulebook"]["hours_per_session"], 8.0)
        for d in r["days"]:
            night = (d["night_line"] or {}).get("line")
            for ln, h in d["line_hours"].items():
                self.assertLessEqual(h, 16.01 if ln == night else 8.01)

    def test_a_shift_longer_than_the_rulebook_is_refused_not_logged(self):
        # live/loop.sh exports SIM_HOURS=12 by default. On the real rulebook inputs that
        # buys +11% litres and Rs 8 Cr and puts 24 h on a line, against R02's flat "day +
        # night = 20 hours, not 22, not 24". Recording it in the summary is not enough:
        # nothing downstream refused it, and the site publishes what the engine wrote.
        r = run_engine(inputs(), tag="-h12", env_extra=dict(SIM_HOURS="12"))
        self.assertNotEqual(r["rc"], 0, "a 12 h session on a 10 h rulebook must stop the run")
        self.assertIn("R02", r["stderr"])
        self.assertIsNone(r["summary"], "nothing may be written when the shift is refused")
        r = run_engine(inputs(), tag="-sch", env_extra=dict(SIM_HOURS_SCHEDULE="1-30:22"))
        self.assertNotEqual(r["rc"], 0, "a taper schedule may not lengthen the shift either")
        self.assertIn("R02", r["stderr"])

    def test_a_longer_shift_is_still_a_scenario_without_a_rulebook(self):
        # Mark 2's best lever is a flat 22 h day. The cap is R02's, so it belongs to
        # rulebook mode alone and must never reach the August or -sep paths.
        r = run_engine(inputs(rulebook=False, efficiency=0.5), tag="-h22", env_extra=dict(SIM_HOURS="22"))
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["shift"]["hours"], 22.0)

    def test_a_code_the_rulebook_never_saw_is_named_not_guessed(self):
        S = inputs()
        S["plan"].append(dict(code="FGNEW", sku="A PRODUCT THE SHEET NEVER SAW", head="COMMODITY",
                              category="OIL", pack_type="PET", litres_per_piece=1.0,
                              pieces=500, litres=500.0))
        S["bom"]["FGNEW"] = [["RM0000001", 1.0], ["PMFGNEW", 1.0]]
        S["items"]["PMFGNEW"] = dict(name="A BOTTLE", uom="PCS")
        S["realise"]["FGNEW"] = 150.0
        S["opening"]["stock"]["PMFGNEW"] = 100000.0
        r = run_engine(S, tag="-unmapped")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["unmapped_codes"], ["FGNEW"],
                         "a code with no pack class must be NAMED, so gen can refuse the cycle")
        # with no bottle family it can only run where the line takes ANY bottle — never
        # guessed onto a machine that fills a family it was never classed into.
        for d in r["days"]:
            for run in d["runs"]:
                if run["code"] == "FGNEW":
                    self.assertEqual(run["family"], "UNKNOWN")
                    self.assertIn("ANY", RB_LINES[run["line"]]["slots"][run["slot"]])

    def test_without_a_rulebook_nothing_changes(self):
        r = run_engine(inputs(rulebook=False, efficiency=0.5, legacy_15l=True), tag="-legacy")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertNotIn("rulebook", r["summary"], "a legacy summary carries no rulebook block")
        for d in r["days"]:
            self.assertNotIn("night_line", d)
            self.assertNotIn("line_hours_max", d)
            for run in d["runs"]:
                self.assertNotIn("family", run)
        # the 15 L PET jar runs on a line that only lists a 5 L slot: the derivation the
        # rulebook turns off (AC02) is still there for the August and September paths.
        lines15 = sorted({run["line"] for d in r["days"] for run in d["runs"] if run["code"] == "FGP15"})
        self.assertTrue(lines15, "the derived 15 L slot vanished from the legacy path")
        self.assertTrue(set(lines15) <= {"Clear Pack", "6 Head"}, lines15)
        # and a Sunday in legacy mode ships nothing, exactly as it always did
        sun = [d for d in r["days"] if d["date"] == SUNDAY][0]
        self.assertEqual(sun["shipped_litres"], 0)
        self.assertEqual(sun["dispatched"], [])


class AugustIsUntouched(unittest.TestCase):
    """The calibration is the only reason these numbers get to have an opinion. It is
    pinned in reference/august-calibration.json with the sha256 of everything it depends
    on; this test re-runs it and demands the same litres and the same rupees."""

    def test_august_reproduces_the_pinned_calibration(self):
        art = os.path.join(JOLLY, "reference", "august-calibration.json")
        inp = os.path.join(JOLLY, "sim", "sim-inputs.json")
        if not (os.path.exists(art) and os.path.exists(inp)):
            self.skipTest("reference/august-calibration.json or sim/sim-inputs.json is not here")
        pinned, S = _read(art), _read(inp)
        self.assertNotIn("rulebook", S, "the August inputs must stay rulebook-free")
        r = run_engine(S, tag="-augustcheck")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["totals"]["made_l"], pinned["sim_made_l"])
        self.assertNotIn("rulebook", r["summary"])
        if "sim_value" in pinned:
            self.assertEqual(r["summary"]["totals"]["value"], pinned["sim_value"])

    def test_the_pin_carries_the_rupees_and_the_shift_it_ran_under(self):
        """Litres alone do not pin this backtest.

        A change that keeps 2,124,866 L and moves the SKU mix changes every rupee on the
        money page and passes a litres-only assertion — and the money page is the front
        page. The shift is pinned for the same reason: the replay used to inherit the
        shell's SIM_HOURS_SCHEDULE, so the trust number could be measured under a taper
        August never worked and `--check`, which only compares file hashes, would still
        call it reproducible.

        RED until `python3 engine/calibrate_august.py` is re-run — which CLAUDE.md says
        happens in the same commit as an engine change, not before it.
        """
        art = os.path.join(JOLLY, "reference", "august-calibration.json")
        if not os.path.exists(art):
            self.skipTest("reference/august-calibration.json is not here")
        pinned = _read(art)
        self.assertIn("sim_value", pinned,
                      "the artefact pins litres but not rupees — re-measure it with "
                      "python3 engine/calibrate_august.py")
        self.assertIn("shift", pinned,
                      "the artefact does not say what shift the replay ran under — "
                      "re-measure it with python3 engine/calibrate_august.py")


if __name__ == "__main__":
    unittest.main()
