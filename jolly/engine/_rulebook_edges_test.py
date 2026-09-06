#!/usr/bin/env python3
"""_rulebook_edges_test.py — the corners of Mark 4's rulebook mode.

    cd jolly && python3 -m unittest engine._rulebook_edges_test -v
    cd jolly && python3 engine/_rulebook_edges_test.py

`_rulebook_sim_test.py` proves the rulebook on its happy path: a tin on a tin
line, families, the change cap, a named night line, Sunday. This file is the
other half — the states that only turn up once, and that a plan run on the real
plant will eventually hit:

  * a slot the rulebook NAMES but no line has a planning speed for (B16). It must
    not run there, and — the part that would be invisible — it must not sit at
    preference 1 holding the product off a machine that CAN fill it.
  * the 15 L derivation. Legacy derives a 15 L slot from a 5 L one; rulebook mode
    must not, even when the rulebook claims the slot (AC02). Both halves asserted,
    because turning it off for August would move the calibration.
  * the night line when NOTHING is order-backed, and when there is nothing left to
    make at all. Both must still publish a reason (R03/A07) — the site prints it.
  * a 200 L drum the rulebook's `drums.skus` list forgot: the DRUM slot alone has
    to make it hand-filled, or a new drum code walks into the schedule (R14).
  * a plan code the rulebook never classed, in a run where it actually has room —
    the sibling test's version of this assertion is vacuous because the code never
    gets a slot on the busy synthetic plant.
  * SIM_SUNDAYS_OFF as a scenario, not a plan.
  * reference/august-calibration.json as a real gate: a moved engine and a missing
    artefact both have to be refusals, because that artefact is the only thing
    standing between an engine edit and a silently wrong trust sentence.

The underscore keeps the file out of the loop's adapter discovery (commit b1c6facf).
"""
import collections
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
JOLLY = os.path.dirname(HERE)
if JOLLY not in sys.path:
    sys.path.insert(0, JOLLY)

from engine import _rulebook_sim_test as T          # the synthetic plant, reused whole

CLEAR_H = T.CLEAR_H


class SlotWithNoRate(unittest.TestCase):
    """B16 — a line with no planning speed for a pack cannot fill it, and therefore
    cannot be the 'better machine' that holds the pack off a line that can."""

    def setUp(self):
        S = T.inputs()
        # JP claims 5 L tins at preference 1 — ahead of the 6 Head (1) and the Tin
        # Head (2) — while `lines` gives JP no 5 L rate at all.
        S["rulebook"]["lines"]["JP Machine"]["slots"]["5L"] = {"TIN": 1}
        self.phantom = T.run_engine(S, tag="-norate")
        self.base = T.run_engine(T.inputs(), tag="-norate-base")
        for r in (self.phantom, self.base):
            self.assertEqual(r["rc"], 0, r["stderr"])

    @staticmethod
    def _runs(r, code=None):
        return [dict(x, date=d["date"]) for d in r["days"] for x in d["runs"]
                if code is None or x["code"] == code]

    def test_a_line_with_no_speed_never_runs_the_pack(self):
        self.assertEqual([x for x in self._runs(self.phantom) if x["line"] == "JP Machine"
                          and x["slot"] == "5L"], [])

    def test_a_rateless_preference_one_line_does_not_strand_the_product(self):
        made = sum(x["pieces"] for x in self._runs(self.phantom, "FGT05"))
        was = sum(x["pieces"] for x in self._runs(self.base, "FGT05"))
        self.assertTrue(was > 0, "the baseline never made the 5 L tin — the test proves nothing")
        self.assertEqual(made, was,
                         "a line that cannot fill a pack changed the plan for it (B16)")


class FifteenLitreDerivation(unittest.TestCase):
    """AC02 — 15 L belongs to the Tin Head. The legacy 5 L / 3 slot derivation is the
    Mark 3 misplacement that put 252,786 L of September on a 5 L head."""

    def test_rulebook_mode_does_not_derive_a_fifteen_litre_slot(self):
        S = T.inputs()
        # Clear Pack has a 5 L rate and no 15 L rate; now it also CLAIMS the slot.
        S["rulebook"]["lines"]["Clear Pack"]["slots"]["15L"] = {"TIN": 1}
        r = T.run_engine(S, tag="-noderive")
        self.assertEqual(r["rc"], 0, r["stderr"])
        runs = [x for d in r["days"] for x in d["runs"]]
        self.assertTrue([x for x in runs if x["slot"] == "15L"], "no 15 L ran at all")
        self.assertEqual(sorted({x["line"] for x in runs if x["slot"] == "15L"}), ["Tin Head"])

    def test_the_legacy_path_still_derives_it(self):
        r = T.run_engine(T.inputs(rulebook=False, efficiency=0.5, legacy_15l=True), tag="-derive")
        self.assertEqual(r["rc"], 0, r["stderr"])
        lines = sorted({x["line"] for d in r["days"] for x in d["runs"] if x["code"] == "FGP15"})
        self.assertTrue(lines, "August and September depend on this derivation — it vanished")
        self.assertTrue(set(lines) <= {"Clear Pack", "6 Head"}, lines)


class NightLineFallbacks(unittest.TestCase):
    """R03/A07 — the plan names the night line and says why, on every working day,
    including the days when the reason is 'there was nothing to pick on'."""

    def test_nothing_order_backed_still_names_a_line_and_a_reason(self):
        S = T.inputs()
        for o in S["orders"]:                       # every row becomes a forecast row
            o["channel"] = "FORECAST"
            o["docnum"] = "FCST-" + o["docnum"]
            o["value"] = 0.0
            o["customer"] = "(forecast — not yet ordered)"
        r = T.run_engine(S, tag="-nopo")
        self.assertEqual(r["rc"], 0, r["stderr"])
        working = [d for d in r["days"] if d["working"]]
        self.assertTrue(working)
        for d in working:
            nl = d["night_line"]
            self.assertEqual(nl["po_backed_l_unmade"], 0)
            self.assertIsNotNone(nl["line"], f"{d['date']} picked no night line")
            self.assertIn("nothing order-backed left", nl["reason"])
            self.assertTrue(nl["candidates"])

    def test_nothing_left_to_make_opens_no_second_session(self):
        S = T.inputs()
        for p in S["plan"]:
            p["pieces"] = 5
            p["litres"] = 5 * p["litres_per_piece"]
        S["orders"] = [dict(docnum="PO-01", customer="A REAL CUSTOMER", channel="GT",
                            code="FGB26", date=T.D0, pieces=5, value=750.0)]
        r = T.run_engine(S, tag="-nothingleft")
        self.assertEqual(r["rc"], 0, r["stderr"])
        idle = [d for d in r["days"] if d["working"] and d["made_litres"] == 0]
        self.assertTrue(idle, "nothing was left idle — the branch was never reached")
        for d in idle:
            self.assertIsNone(d["night_line"]["line"])
            self.assertEqual(d["night_line"]["reason"], "nothing left to make")
            self.assertEqual(sorted(set(d["line_hours_max"].values())), [10.0],
                             "a line got a night session with nothing to put in it")
        self.assertEqual(r["summary"]["rulebook"]["night_sessions"],
                         sum(1 for d in r["days"] if (d.get("night_line") or {}).get("line")))

    def test_an_empty_order_stream_is_refused_not_silently_planned(self):
        S = T.inputs()
        S["orders"] = []
        r = T.run_engine(S, tag="-noorders")
        self.assertNotEqual(r["rc"], 0)
        self.assertIn("S['orders'] is empty", r["stderr"])

    def test_only_the_named_line_produces_at_night(self):
        """R03 — labour allows ONE line a second session. Every run the engine tags
        `night` has to be on the line that day's plan named, or the site's sentence
        ('one line at night, here is which') is false."""
        r = T.run_engine(T.inputs(), tag="-nightonly")
        self.assertEqual(r["rc"], 0, r["stderr"])
        tagged = [(d["date"], x["line"], (d["night_line"] or {}).get("line"))
                  for d in r["days"] for x in d["runs"] if x["night"]]
        self.assertTrue(tagged, "no run was tagged night — the assertion proves nothing")
        stray = [t for t in tagged if t[1] != t[2]]
        self.assertEqual(stray, [], f"{len(stray)} night run(s) on a line nobody named")


def churn_inputs():
    """A plant that WANTS to change product all day: five small SKUs on one machine,
    each cleared in under two hours. The stock plant never pushes past a single
    change a session, so the cap is only ever exercised here."""
    S = T.inputs()
    for i in range(1, 6):
        code, name = f"FGS{i}", f"SESAME 500 MLS {chr(64 + i)}"
        S["plan"].append(dict(code=code, sku=name, head="COMMODITY", category="OIL",
                              pack_type="PET", litres_per_piece=0.5, pieces=300,
                              litres=150.0, trailing_l_per_month=10.0))
        S["bom"][code] = [["RM0000001", 0.5], ["PM" + code, 1.0]]
        S["items"]["PM" + code] = dict(name="BOTTLE " + name, uom="PCS")
        S["realise"][code] = 150.0
        S["opening"]["stock"]["PM" + code] = 100_000.0
        S["rulebook"]["sku_pack"][code] = dict(sku=name, slot="1L", family="SMALL",
                                               fills_per_piece=1, litres_per_piece=0.5)
        S["orders"].append(dict(docnum="PO-" + code, customer="A REAL CUSTOMER", channel="GT",
                                code=code, date=T.D0, pieces=300, value=45000.0))
    S["orders"] = [o for o in S["orders"] if o["code"] != "FGB26"]   # room for JP to churn
    return S


class SpillOrder(unittest.TestCase):
    """B01 — a SKU reaches a lesser machine only once every better one is out of hours.
    The stock synthetic plant never spills at all (every run is preference 1), so the
    sibling test's spill assertion has nothing to look at. This one forces a spill AND
    puts the pref-2 line FIRST in the engine's line order (it is sorted by top speed),
    so 'ignore the preference order' shows up as a run that happened too early."""

    SESSION_H = 10.0

    def setUp(self):
        S = T.inputs()
        # give the Tin Head a fast 1 L slot so it sorts ahead of the 6 Head, while it is
        # still only preference 2 for the 5 L tin.
        S["lines"]["Tin Head"]["1L"] = 500.0
        S["rulebook"]["lines"]["Tin Head"]["slots"]["1L"] = {"ANY": 1}
        S["orders"] = [dict(docnum=f"PO-{i}", customer="A REAL CUSTOMER", channel="GT",
                            code="FGT05", date=d, pieces=250, value=37500.0)
                       for i, d in enumerate(T._dates())]
        for p in S["plan"]:
            if p["code"] != "FGT05":
                p["pieces"] = 0
                p["litres"] = 0.0
        self.r = T.run_engine(S, tag="-spill")
        self.assertEqual(self.r["rc"], 0, self.r["stderr"])
        self.rb_lines = S["rulebook"]["lines"]
        self.lines = S["lines"]

    def _better(self, run):
        """Lines that fill this run's pack in this bottle at a better preference."""
        out = []
        for ln, d in self.rb_lines.items():
            if ln == run["line"]:
                continue
            fams = (d.get("slots") or {}).get(run["slot"])
            if not fams or run["slot"] not in self.lines.get(ln, {}):
                continue
            p = fams.get(run["family"], fams.get("ANY"))
            if p and p < run["pref"]:
                out.append(ln)
        return out

    def test_a_spill_actually_happens(self):
        prefs = self.r["summary"]["rulebook"]["prefs_used"]
        self.assertIn("2", prefs, f"nothing ever spilled — the test proves nothing ({prefs})")

    def test_no_run_opens_on_a_lesser_line_while_a_better_one_still_has_hours(self):
        for d in self.r["days"]:
            booked = {ln: 0.0 for ln in self.lines}
            for run in d["runs"]:
                if run["night"]:
                    continue                    # the night line's second session
                if run["pref"] > 1:
                    for m in self._better(run):
                        left = self.SESSION_H - booked[m]
                        self.assertLessEqual(
                            left, CLEAR_H + 0.05,
                            f"{run['sku']} opened on {run['line']} (pref {run['pref']}) on "
                            f"{d['date']} while {m} still had {left:.2f} h free (B01)")
                booked[run["line"]] += run["hours"] + run["flush_min"] / 60.0


class NightPickIsNotHardWired(unittest.TestCase):
    """A07/B03 — the night line is where the most ORDERED litres are still unmade. The
    stock plant always answers 'JP Machine', so a hard-wired JP would pass every test in
    the sibling file. Here the orders sit on the Tin Head and JP has nothing at all."""

    def test_the_night_line_follows_the_orders_not_a_default(self):
        S = T.inputs()
        S["orders"] = [dict(docnum=f"PO-{i}", customer="A REAL CUSTOMER", channel="GT",
                            code="FGT15", date=d, pieces=3000, value=900000.0)
                       for i, d in enumerate(T._dates())]
        for p in S["plan"]:
            if p["code"] != "FGT15":
                p["pieces"] = 0
                p["litres"] = 0.0
        r = T.run_engine(S, tag="-nightpick")
        self.assertEqual(r["rc"], 0, r["stderr"])
        picks = {(d.get("night_line") or {}).get("line") for d in r["days"] if d["working"]}
        self.assertEqual(picks, {"Tin Head"},
                         f"the night line ignored where the orders are: {picks}")
        for d in r["days"]:
            if not d["working"]:
                continue
            nl = d["night_line"]
            self.assertEqual(nl["candidates"][0]["line"], nl["line"])
            self.assertGreater(nl["po_backed_l_unmade"], 0)


class ChangeCapUnderPressure(unittest.TestCase):
    """R06/B02 — one product change a line a session, lifted only rather than leave the
    line idle, and every lift printed in that day's decisions. On the real September
    plan the cap is lifted 63 times, so this is not a corner: it is the normal case."""

    @classmethod
    def setUpClass(cls):
        cls.r = T.run_engine(churn_inputs(), tag="-churn")
        if cls.r["rc"] != 0:
            raise AssertionError(cls.r["stderr"])

    @staticmethod
    def _lifts(day):
        out = {}
        for x in day["decisions"]:
            if x["kind"] == "CHANGE_CAP_LIFTED":
                out[x["line"]] = out.get(x["line"], 0) + 1
        return out

    def test_the_cap_actually_binds_on_this_plant(self):
        total = sum(len(self._lifts(d)) and sum(self._lifts(d).values()) for d in self.r["days"])
        self.assertGreater(total, 0, "no lift was ever needed — this scenario tests nothing")

    def test_changes_never_exceed_one_plus_the_lifts_that_were_logged(self):
        for d in self.r["days"]:
            lifts = self._lifts(d)
            for ln in T.LINES:
                for night in (False, True):
                    codes = [x["code"] for x in d["runs"] if x["line"] == ln and x["night"] is night]
                    changes = sum(1 for a, b in zip(codes, codes[1:]) if a != b)
                    self.assertLessEqual(
                        changes, 1 + lifts.get(ln, 0),
                        f"{ln} changed product {changes} times on {d['date']} "
                        f"({'night' if night else 'day'}) with {lifts.get(ln, 0)} lift(s) logged")

    def test_every_lift_names_its_line_and_says_why(self):
        seen = 0
        for d in self.r["days"]:
            for x in d["decisions"]:
                if x["kind"] != "CHANGE_CAP_LIFTED":
                    continue
                seen += 1
                self.assertIn(x["line"], T.LINES)
                self.assertIn("rather than stand idle", x["text"])
                self.assertIn(x["line"], x["text"])
        self.assertGreater(seen, 0)
        self.assertEqual(seen, self.r["summary"]["rulebook"]["change_cap_lifted"])


class DrumsAndUnmappedCodes(unittest.TestCase):

    def test_the_drum_slot_alone_makes_a_sku_hand_filled(self):
        """R14 — a new 200 L code that nobody added to drums.skus must still stay out
        of the schedule. The slot is the rule; the list is the belt."""
        S = T.inputs()
        S["rulebook"]["drums"]["skus"] = []
        r = T.run_engine(S, tag="-drumslot")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["manual_skus"], ["FGD20"])
        self.assertEqual([x for d in r["days"] for x in d["runs"] if x["code"] == "FGD20"], [])
        self.assertEqual([b for d in r["days"] for b in d["blocked"] if b["code"] == "FGD20"], [])

    def test_an_unmapped_code_with_room_lands_only_on_an_any_line(self):
        """The sibling test asserts this inside a loop that never runs, because the
        busy synthetic plant never gives the stray code a slot. Here the plant is
        quiet enough that it does — so the assertion actually fires."""
        S = T.inputs()
        for p in S["plan"]:                        # clear the competition off the lines
            p["pieces"] = 1
            p["litres"] = p["litres_per_piece"]
        for o in S["orders"]:
            o["pieces"] = 20
            o["value"] = 3000.0
        S["plan"].append(dict(code="FGNEW", sku="A PRODUCT THE SHEET NEVER SAW", head="COMMODITY",
                              category="OIL", pack_type="PET", litres_per_piece=1.0,
                              pieces=6000, litres=6000.0))
        S["bom"]["FGNEW"] = [["RM0000001", 1.0], ["PMFGNEW", 1.0]]
        S["items"]["PMFGNEW"] = dict(name="A BOTTLE", uom="PCS")
        S["realise"]["FGNEW"] = 150.0
        S["opening"]["stock"]["PMFGNEW"] = 1_000_000.0
        S["orders"].append(dict(docnum="PO-NEW", customer="A REAL CUSTOMER", channel="GT",
                                code="FGNEW", date=T.D0, pieces=6000, value=900000.0))
        r = T.run_engine(S, tag="-unmapped-room")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["unmapped_codes"], ["FGNEW"])
        runs = [x for d in r["days"] for x in d["runs"] if x["code"] == "FGNEW"]
        self.assertTrue(runs, "the unmapped code still never ran — the assertion is vacuous")
        for x in runs:
            self.assertEqual(x["family"], "UNKNOWN")
            fams = T.RB_LINES[x["line"]]["slots"][x["slot"]]
            self.assertIn("ANY", fams,
                          f"an unclassed code was guessed onto {x['line']}, which fills {sorted(fams)}")


class ScenarioOverrides(unittest.TestCase):

    def test_sundays_off_zero_is_a_scenario_and_is_recorded(self):
        r = T.run_engine(T.inputs(), tag="-sun0", env_extra=dict(SIM_SUNDAYS_OFF="0"))
        self.assertEqual(r["rc"], 0, r["stderr"])
        sun = [d for d in r["days"] if d["date"] == T.SUNDAY][0]
        self.assertTrue(sun["working"])
        self.assertGreater(sun["made_litres"], 0)
        self.assertFalse(r["summary"]["rulebook"]["sundays_off"],
                         "a Sunday-working scenario must not read back as the plan")

    def test_the_default_run_carries_the_rulebooks_own_sunday_rule(self):
        r = T.run_engine(T.inputs(), tag="-sundefault")
        self.assertTrue(r["summary"]["rulebook"]["sundays_off"])
        self.assertTrue(r["summary"]["rulebook"]["dispatch_on_sunday"])


class CalibrationArtefactIsAGate(unittest.TestCase):
    """reference/august-calibration.json is the only thing between an engine edit and
    a wrong trust sentence on the site. Test the gate, not just the number."""

    def setUp(self):
        sys.path.insert(0, HERE)
        import calibrate_august
        self.C = calibrate_august
        self.art_path = os.path.join(JOLLY, "reference", "august-calibration.json")
        if not os.path.exists(self.art_path):
            self.skipTest("reference/august-calibration.json is not here")
        with open(self.art_path, encoding="utf-8") as fh:
            self.art = json.load(fh)

    def _scratch(self):
        tmp = tempfile.mkdtemp(prefix="calib-gate-")
        for sub in ("engine", "reference", "sim"):
            os.makedirs(os.path.join(tmp, sub), exist_ok=True)
        for rel in self.C.DEPENDS_ON:
            shutil.copy(os.path.join(JOLLY, rel), os.path.join(tmp, rel))
        shutil.copy(self.art_path, os.path.join(tmp, "reference", "august-calibration.json"))
        return tmp

    def test_the_pin_matches_the_tree_right_now(self):
        self.assertEqual(self.C.stale(self.art), [],
                         "the August calibration was measured against a different engine — "
                         "re-run python3 engine/calibrate_august.py")

    def test_a_moved_engine_is_caught(self):
        tmp, saved = self._scratch(), self.C.JOLLY
        try:
            self.C.JOLLY = tmp
            self.assertEqual(self.C.stale(self.art), [])
            with open(os.path.join(tmp, "engine", "august_sim.py"), "a", encoding="utf-8") as fh:
                fh.write("\n# one byte of drift\n")
            moved = [rel for rel, _was, _now in self.C.stale(self.art)]
            self.assertIn("engine/august_sim.py", moved)
        finally:
            self.C.JOLLY = saved
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_missing_artefact_is_a_refusal_not_a_pass(self):
        tmp, saved_j, saved_a = self._scratch(), self.C.JOLLY, self.C.ARTEFACT
        try:
            self.C.JOLLY = tmp
            self.C.ARTEFACT = os.path.join(tmp, "reference", "august-calibration.json")
            os.remove(self.C.ARTEFACT)
            with contextlib.redirect_stdout(io.StringIO()) as said:
                rc = self.C.main(["--check"])
            self.assertEqual(rc, 1)
            self.assertIn("is not there", said.getvalue())
        finally:
            self.C.JOLLY, self.C.ARTEFACT = saved_j, saved_a
            shutil.rmtree(tmp, ignore_errors=True)


# ============================================================================
# THE GATES — seven behaviours that mutated freely with the whole suite green
# ============================================================================
# Found 2026-09-06. Each one below is a decision the plan is published on, and each
# could be deleted or inverted in ONE edit without a single test going red. So each
# test here carries the mutation it exists to catch: `engine_mutated` runs the same
# fixture through a one-line-changed copy of the engine and the test asserts the
# output MOVES. An assertion that cannot be shown to bite is not a gate.


@contextlib.contextmanager
def engine_mutated(old, new):
    """Run T.run_engine against a copy of the engine with ONE line changed.

    The engine imports nothing local, so a copy in a temp directory behaves exactly
    like the original. `old` must appear exactly once — if a refactor moves it, this
    raises rather than silently testing nothing.
    """
    with open(T.ENGINE, encoding="utf-8") as fh:
        src = fh.read()
    if src.count(old) != 1:
        raise AssertionError("the mutation target appears %d times, not once: %r"
                             % (src.count(old), old[:60]))
    tmp = tempfile.mkdtemp(prefix="mark4-mutant-")
    path = os.path.join(tmp, "august_sim.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src.replace(old, new))
    saved, T.ENGINE = T.ENGINE, path
    try:
        yield
    finally:
        T.ENGINE = saved
        shutil.rmtree(tmp, ignore_errors=True)


def with_hdpe_5l(S, pieces=4000):
    """Add a 5 L HDPE jar — the shape the real plant's flagship class has: preference 1
    on TWO machines at very different speeds (Clear Pack 100/h, 6 Head 60/h here;
    1,068/h and 480/h in the September rulebook)."""
    S["plan"].append(dict(code="FGH05", sku="HDPE OIL 5 LTR", head="COMMODITY", category="OIL",
                          pack_type="PET", litres_per_piece=5.0, pieces=pieces,
                          litres=pieces * 5.0))
    S["bom"]["FGH05"] = [["RM0000001", 5.0], ["PMFGH05", 1.0]]
    S["items"]["PMFGH05"] = dict(name="HDPE JAR 5 LTR", uom="PCS")
    S["realise"]["FGH05"] = 150.0
    S["opening"]["stock"]["PMFGH05"] = 4_000_000.0
    S["rulebook"]["sku_pack"]["FGH05"] = dict(sku="HDPE OIL 5 LTR", slot="5L", family="HDPE",
                                              fills_per_piece=1, litres_per_piece=5.0)
    return S


class NightHomeIsTheFasterMachine(unittest.TestCase):
    """A07/B03 — a SKU counts ONCE in the night measure, on the best machine that may
    fill it, and `best` is not alphabetical.

    rb_home() was `sorted((rb_pref(c, ln), ln) …)`, so a preference tie fell to the LINE
    NAME. On the real September rulebook all nine 5 L HDPE SKUs are preference 1 on both
    Clear Pack (1,068 containers/h) and 6 Head (480/h), and "6 Head" < "Clear Pack" — so
    the whole flagship 5 L class was attributed to the machine 2.2x slower, every day,
    and the day file published "the most ordered litres still unmade" over a margin
    sorted() had invented.
    """

    def fixture(self):
        S = with_hdpe_5l(T.inputs())
        S["orders"] = [dict(docnum=f"PO-{i}", customer="A REAL CUSTOMER", channel="GT",
                            code="FGH05", date=d, pieces=3000, value=2_250_000.0)
                       for i, d in enumerate(T._dates())]
        for p in S["plan"]:
            if p["code"] != "FGH05":
                p["pieces"] = 0
                p["litres"] = 0.0
        return S

    def test_the_night_goes_to_the_faster_of_two_first_choice_machines(self):
        r = T.run_engine(self.fixture(), tag="-home-fast")
        self.assertEqual(r["rc"], 0, r["stderr"])
        working = [d for d in r["days"] if d["working"]]
        self.assertTrue(working)
        for d in working:
            nl = d["night_line"]
            self.assertEqual(nl["line"], "Clear Pack",
                             f"{d['date']}: the night went to {nl['line']} — Clear Pack fills "
                             f"this pack at 100/h and the 6 Head at 60/h, both preference 1")
            by_line = {c["line"]: c["po_backed_l"] for c in nl["candidates"]}
            self.assertGreater(by_line["Clear Pack"], 0)
            self.assertEqual(by_line["6 Head"], 0,
                             "the litres were counted on the slow machine as well as the fast one")

    def test_breaking_the_tie_on_the_name_instead_puts_it_on_the_slow_machine(self):
        with engine_mutated("return sorted((rb_pref(c, ln), -rb_lph(c, ln), ln)",
                            "return sorted((rb_pref(c, ln), 0, ln)"):
            r = T.run_engine(self.fixture(), tag="-home-alpha")
        self.assertEqual(r["rc"], 0, r["stderr"])
        picks = {d["night_line"]["line"] for d in r["days"] if d["working"]}
        self.assertEqual(picks, {"6 Head"},
                         "the alphabet mutation did not move the plan — the test above is vacuous")

    def test_a_real_dead_heat_is_published_rather_than_hidden(self):
        """Two machines at the same preference AND the same planning speed IS decided by
        the name, and there is nothing better to decide it by — so it is named."""
        S = self.fixture()
        S["lines"]["6 Head"]["5L"] = S["lines"]["Clear Pack"]["5L"]      # a genuine dead heat
        r = T.run_engine(S, tag="-home-tie")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["home_ties"].get("FGH05"),
                         ["6 Head", "Clear Pack"])
        said = [d["night_line"]["reason"] for d in r["days"] if d["working"]]
        self.assertTrue(all("dead heat the line name broke" in x for x in said), said)

    def test_no_dead_heat_claims_one(self):
        r = T.run_engine(self.fixture(), tag="-home-notie")
        self.assertEqual(r["summary"]["rulebook"]["home_ties"], {})
        for d in r["days"]:
            self.assertNotIn("dead heat", (d.get("night_line") or {}).get("reason") or "")


class AFamilyChangeIsAChangeover(unittest.TestCase):
    """The 51.3-minute clearance is per CHANGEOVER, and the BOTTLE is a changeover.

    `sizechg` knew the oil and the slot only. Mark 4 made `family` and `fills_per_piece`
    first-class scheduling dimensions and left this behind, so a same-oil same-slot
    different-CONTAINER change booked fh = 0.0 — 5 L HDPE -> 5 L TIN on the 6 Head, or a
    1 L 26 g bottle -> a 1 L 23.8 g round on JP — which quietly makes the cheapest
    schedule the one that alternates bottles. The same bug as the pack-size one three
    lines above it in the engine, one dimension over.
    """

    MUTANT_FROM = '''                        sizechg = on_slot[ln] is not None and (
                            plan[c]["slot"] != on_slot[ln]
                            or plan[c].get("family") != on_family[ln]
                            or fills(c) != on_fills[ln])'''
    MUTANT_TO = '''                        sizechg = on_slot[ln] is not None and plan[c]["slot"] != on_slot[ln]'''

    def fixture(self):
        S = with_hdpe_5l(T.inputs())
        # only the 6 Head may fill 5 L, so it has to alternate tin and jar
        del S["rulebook"]["lines"]["Clear Pack"]["slots"]["5L"]
        del S["rulebook"]["lines"]["Tin Head"]["slots"]["5L"]
        S["orders"] = []
        for i, d in enumerate(T._dates()):
            for code in ("FGT05", "FGH05"):
                S["orders"].append(dict(docnum=f"PO-{code}-{i}", customer="A REAL CUSTOMER",
                                        channel="GT", code=code, date=d, pieces=300,
                                        value=225_000.0))
        for p in S["plan"]:
            if p["code"] not in ("FGT05", "FGH05"):
                p["pieces"] = 0
                p["litres"] = 0.0
        return S

    @staticmethod
    def _bottle_changes(r):
        """Runs whose line was already on the same oil and the same slot, in a DIFFERENT
        container. Every one of them is a changeover the plant would have to do."""
        prev, out = {}, []
        for d in r["days"]:
            for x in d["runs"]:
                p = prev.get(x["line"])
                if p and p["oil"] == x["oil"] and p["slot"] == x["slot"] and (
                        p["family"] != x["family"] or p["fills"] != x["fills"]):
                    out.append(dict(x, date=d["date"], was=p["family"]))
                prev[x["line"]] = x
        return out

    def test_a_bottle_change_pays_the_clearance(self):
        r = T.run_engine(self.fixture(), tag="-family")
        self.assertEqual(r["rc"], 0, r["stderr"])
        changes = self._bottle_changes(r)
        self.assertTrue(changes, "the fixture never changed bottle — it proves nothing")
        for x in changes:
            self.assertGreaterEqual(
                x["flush_min"], round(CLEAR_H * 60) - 1,
                f"{x['date']} {x['line']}: {x['was']} -> {x['family']} cost "
                f"{x['flush_min']} min of line time")

    def test_without_the_family_test_the_same_change_is_free(self):
        with engine_mutated(self.MUTANT_FROM, self.MUTANT_TO):
            r = T.run_engine(self.fixture(), tag="-family-mut")
        self.assertEqual(r["rc"], 0, r["stderr"])
        free = [x for x in self._bottle_changes(r) if x["flush_min"] == 0]
        self.assertTrue(free, "the mutation charged the clearance anyway — the test above "
                              "cannot tell the two engines apart")


class NoLineSkusIsAGate(unittest.TestCase):
    """A plain SKU that EVERY line refuses is otherwise invisible: it is never a
    candidate, so it is never blocked either, and it simply is not in the plan. A freeze
    that wrote the legacy slot key for the Tin Head took 12 tin SKUs and 493,984 L — 15%
    of the month — out with no error anywhere. `no_line_skus` is the only thing that
    names it, and `no_line_skus=NO_LINE` -> `no_line_skus=[]` was a green edit."""

    def fixture(self):
        S = T.inputs()
        for ln in ("Tin Head", "6 Head"):               # nothing fills a 3 L any more
            S["rulebook"]["lines"][ln]["slots"].pop("3L", None)
        return S

    def test_a_sku_no_machine_can_fill_is_named(self):
        r = T.run_engine(self.fixture(), tag="-noline")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["no_line_skus"], ["FGH03"])
        self.assertEqual([x for d in r["days"] for x in d["runs"] if x["code"] == "FGH03"], [],
                         "it ran somewhere after all — the fixture is wrong")
        self.assertIn("NO MACHINE FILLS THESE", r["stdout"])

    def test_the_stock_plant_has_none_so_the_list_is_not_always_full(self):
        r = T.run_engine(T.inputs(), tag="-noline-none")
        self.assertEqual(r["summary"]["rulebook"]["no_line_skus"], [])

    def test_emptying_the_list_hides_the_disappearance(self):
        with engine_mutated("        no_line_skus=NO_LINE,", "        no_line_skus=[],"):
            r = T.run_engine(self.fixture(), tag="-noline-mut")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["no_line_skus"], [],
                         "the mutation did not take — the assertion above is vacuous")


class TheNightMeasureAsksForMaterial(unittest.TestCase):
    """B03 — a line is given a night for litres it can actually make. Ignoring material
    gave the Tin Head 15 September on 21,100 ordered litres whose every component was
    empty: ten line-hours, zero litres, and a day file that said 'the most ordered litres
    still unmade'.

    `rb_can_make` is the ONLY thing standing between the Tin Head and a night session for
    45,000 L of tins that do not exist, and the fixture has to keep it that way: the
    blocked-list filter beside it would hide the mutation, because a SKU that was blocked
    is filtered whether or not the material test exists. So the Tin Head is given a
    SECOND, makeable 15-litre tin worth more an hour, which takes the whole day session
    and leaves the line with no hours — and a SKU on a line with no hours left is never
    attempted, so it is never blocked.

    (Until 2026-09-06 the fixture filled the godown to the ceiling instead. That worked
    only because the engine dropped a run the godown had stopped WITHOUT a blocked row —
    the silence this suite now exists to forbid. With B20 emitting that row, a full
    godown blocks everything, `_blk` covers the tin and the mutation goes vacuous; and
    B20 rosters no crew on a full godown either, so there would be no night to measure.)
    """

    def fixture(self):
        S = T.inputs()
        S["rules"]["lead_days"] = dict(oil=11, packaging=60)           # the buy never lands
        S["opening"]["stock"]["PMFGT15"] = 0.0                         # and no tins on the floor
        # the makeable twin: same slot, same line, worth twice as much an hour so the
        # day session reaches for it first and runs the Tin Head out of hours on it
        S["plan"].append(dict(code="FGT15B", sku="TIN OIL 15 LTR (B)", head="COMMODITY",
                              category="OIL", pack_type="TIN", litres_per_piece=15.0,
                              pieces=0, litres=0.0))
        S["bom"]["FGT15B"] = [["RM0000001", 15.0], ["PMFGT15B", 1.0]]
        S["items"]["PMFGT15B"] = dict(name="TIN 15 LTR B", uom="PCS")
        S["realise"]["FGT15B"] = 300.0
        S["opening"]["stock"]["PMFGT15B"] = 4_000_000.0
        S["rulebook"]["sku_pack"]["FGT15B"] = dict(
            sku="TIN OIL 15 LTR (B)", slot="15L", family="TIN", fills_per_piece=1,
            litres_per_piece=15.0)
        S["orders"] = [
            dict(docnum="PO-T", customer="A REAL CUSTOMER", channel="GT",
                 code="FGT15", date=T.D0, pieces=3000, value=4_500_000.0),   # 45,000 L, unmakeable
            dict(docnum="PO-TB", customer="A REAL CUSTOMER", channel="GT",
                 code="FGT15B", date=T.D0, pieces=400, value=1_800_000.0),   # 6,000 L, makeable
            dict(docnum="PO-B", customer="A REAL CUSTOMER", channel="GT",
                 code="FGB26", date=T.D0, pieces=40000, value=6_000_000.0),  # 40,000 L on JP
        ]
        for p in S["plan"]:
            p["pieces"] = 0
            p["litres"] = 0.0
        return S

    @staticmethod
    def _day1(r):
        return [d for d in r["days"] if d["working"]][0]

    def test_a_line_whose_only_demand_has_no_material_gets_no_night(self):
        r = T.run_engine(self.fixture(), tag="-canmake")
        self.assertEqual(r["rc"], 0, r["stderr"])
        d = self._day1(r)
        # the Tin Head ran out of hours on the makeable twin, so the unmakeable tin was
        # never attempted and never blocked — which is what keeps this test about
        # rb_can_make and not about the blocked list
        self.assertNotIn("FGT15", [b["code"] for b in d["blocked"]],
                         "a blocked row would filter the tin out anyway and prove nothing")
        self.assertTrue(any(r_["code"] == "FGT15B" for r_ in d["runs"]),
                        "the makeable twin did not run — the Tin Head still had hours")
        self.assertEqual(d["line_hours"]["Tin Head"], d["line_hours_max"]["Tin Head"])
        nl = d["night_line"]
        self.assertEqual(nl["line"], "JP Machine",
                         f"{d['date']}: the night went to {nl['line']}")
        tin = [c for c in nl["candidates"] if c["line"] == "Tin Head"][0]
        self.assertLess(tin["po_backed_l"], 45_000,
                        "45,000 L of unmakeable orders were counted as a night's work")

    def test_without_the_material_test_the_empty_machine_takes_the_night(self):
        with engine_mutated("or want(c) < 1 or not rb_can_make(c): continue",
                            "or want(c) < 1: continue"):
            r = T.run_engine(self.fixture(), tag="-canmake-mut")
        self.assertEqual(r["rc"], 0, r["stderr"])
        nl = self._day1(r)["night_line"]
        self.assertEqual(nl["line"], "Tin Head",
                         "the mutation did not move the plan — the assertion above is vacuous")
        tin = [c for c in nl["candidates"] if c["line"] == "Tin Head"][0]
        self.assertGreaterEqual(tin["po_backed_l"], 45_000)


class TieBreaksSayWhatDecidedThem(unittest.TestCase):
    """A07 sends a tie to the JP Machine, and `_why_tied` must never claim a margin the
    pick did not have."""

    def jp_tie(self):
        """JP and Clear Pack dead level on ordered litres unmade, on several days."""
        S = T.inputs()
        del S["rulebook"]["lines"]["6 Head"]["slots"]["1L"]   # no third machine for a 1 L
        S["orders"] = []
        for i, d in enumerate(T._dates()):
            S["orders"].append(dict(docnum=f"PO-J{i}", customer="A REAL CUSTOMER", channel="GT",
                                    code="FGB26", date=d, pieces=5000, value=750_000.0))
            S["orders"].append(dict(docnum=f"PO-C{i}", customer="A REAL CUSTOMER", channel="GT",
                                    code="FGB40", date=d, pieces=5000, value=750_000.0))
        for p in S["plan"]:
            if p["code"] not in ("FGB26", "FGB40"):
                p["pieces"] = 0
                p["litres"] = 0.0
        return S

    @staticmethod
    def _tied_days(r):
        return [d for d in r["days"] if d["working"]
                and len({c["po_backed_l"] for c in d["night_line"]["candidates"][:2]}) == 1]

    def test_a_real_tie_goes_to_jp_and_says_so(self):
        r = T.run_engine(self.jp_tie(), tag="-a07")
        self.assertEqual(r["rc"], 0, r["stderr"])
        tied = self._tied_days(r)
        self.assertTrue(tied, "no day tied — the fixture proves nothing")
        for d in tied:
            self.assertEqual(d["night_line"]["line"], "JP Machine", d["date"])
            self.assertIn("tie to the JP Machine (A07)", d["night_line"]["reason"])

    def test_without_the_jp_key_the_alphabet_takes_the_tie(self):
        with engine_mutated('key=lambda ln: (-_po[ln], 0 if ln == "JP Machine" else 1, -_oth[ln], ln)',
                            'key=lambda ln: (-_po[ln], 1, -_oth[ln], ln)'):
            r = T.run_engine(self.jp_tie(), tag="-a07-mut")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertTrue(any(d["night_line"]["line"] != "JP Machine" for d in self._tied_days(r)),
                        "the mutation did not move the plan — the assertion above is vacuous")

    def test_a_margin_is_only_claimed_against_the_nearest_rival(self):
        """`min(second[ln] for ln in tied)` measured the winner against the WORST line in
        the tie — including lines that had already lost on the JP key — so a pick level
        with its nearest rival still published 'more expected and plan litres behind it'.

        Three machines level on ordered litres, JP below them, and the top TWO level on
        expected-and-plan litres as well. Nothing separates the winner from the runner-up
        but the name, and the reason has to say that. The godown is full at the open so
        nothing is made and the arithmetic stays exactly where it was put.

        That full godown is also why the assertion is on `picked` and not on `line`:
        B20 rosters no crew for a night that cannot put a bottle anywhere, so `line` is
        rightly None here. `picked` is what the A07 measure chose, which is what this
        test is about — and the tie-break reason is still the measure's own.
        """
        S = T.inputs()
        S["opening"]["fg_other_l"] = S["rules"]["storage_ceiling_l"]
        S["orders"] = [
            dict(docnum="PO-T", customer="A REAL CUSTOMER", channel="GT",
                 code="FGT15", date=T.D0, pieces=200, value=90_000.0),      # Tin Head 3,000 L
            dict(docnum="PO-H", customer="A REAL CUSTOMER", channel="GT",
                 code="FGH03", date=T.D0, pieces=1000, value=450_000.0),    # 6 Head    3,000 L
            dict(docnum="PO-C", customer="A REAL CUSTOMER", channel="GT",
                 code="FGB40", date=T.D0, pieces=3000, value=450_000.0),    # Clear Pack 3,000 L
            dict(docnum="PO-J", customer="A REAL CUSTOMER", channel="GT",
                 code="FGB26", date=T.D0, pieces=1000, value=150_000.0),    # JP         1,000 L
        ]
        want = {"FGT15": 400, "FGH03": 2000}      # 6,000 L of plan behind the top two
        for p in S["plan"]:
            p["pieces"] = want.get(p["code"], 0)
            p["litres"] = p["pieces"] * p["litres_per_piece"]
        r = T.run_engine(S, tag="-margin")
        self.assertEqual(r["rc"], 0, r["stderr"])
        d = [x for x in r["days"] if x["working"]][0]
        nl = d["night_line"]
        self.assertEqual(nl["picked"], "6 Head")
        self.assertEqual([c["po_backed_l"] for c in nl["candidates"][:3]], [3000, 3000, 3000])
        self.assertEqual([c["other_l"] for c in nl["candidates"][:2]], [6000, 6000])
        self.assertIn("nothing else separated them, so the line name did", nl["reason"])
        self.assertNotIn("more expected and plan litres behind it", nl["reason"])
        # and the godown, not the measure, is why nobody is rostered (B20)
        self.assertIsNone(nl["line"])
        self.assertIn("no room for another bottle", nl["reason"])
        self.assertEqual(nl["hours_used"], 0)


class TheChangeCapCountsAreTrustworthy(unittest.TestCase):
    """R06/B02. A reviewer's judgement to PUBLISH the R06 breach rather than cap it rests
    on `change_cap_lifted_twice_or_more` being the number it says it is — and `nth > 1`
    -> `nth > 0` was a one-character edit with the whole suite green."""

    @classmethod
    def setUpClass(cls):
        cls.r = T.run_engine(churn_inputs(), tag="-nth")
        if cls.r["rc"] != 0:
            raise AssertionError(cls.r["stderr"])
        cls.lifts = [x for d in cls.r["days"] for x in d["decisions"]
                     if x["kind"] == "CHANGE_CAP_LIFTED"]

    def test_the_headline_counts_the_second_lift_and_later_only(self):
        rb = self.r["summary"]["rulebook"]
        self.assertEqual(rb["change_cap_lifted"], len(self.lifts))
        self.assertEqual(rb["change_cap_lifted_twice_or_more"],
                         sum(1 for x in self.lifts if x["nth"] > 1))

    def test_a_first_lift_exists_so_the_two_counts_are_not_the_same_number(self):
        firsts = [x for x in self.lifts if x["nth"] == 1]
        self.assertTrue(firsts, "every lift on this plant is a second one — 'twice or more' "
                                "cannot be told from 'at all' and the assertion is vacuous")
        rb = self.r["summary"]["rulebook"]
        self.assertLess(rb["change_cap_lifted_twice_or_more"], rb["change_cap_lifted"])

    def test_the_nth_on_each_decision_is_the_change_number_on_that_line(self):
        for d in self.r["days"]:
            per = collections.Counter()
            for x in d["decisions"]:
                if x["kind"] != "CHANGE_CAP_LIFTED":
                    continue
                per[(x["line"], x["night"])] += 1
                self.assertEqual(x["nth"], per[(x["line"], x["night"])],
                                 f"{d['date']} {x['line']}: nth {x['nth']} on lift "
                                 f"{per[(x['line'], x['night'])]}")
                self.assertIn(f"product change {x['nth'] + 1} on this line", x["text"])


def sliver_inputs():
    """A plant that runs a line down to a SLIVER of its session: JP fills three 1-litre
    26 g products off the same oil (so a change between them costs no clearance at all),
    and the first two run out with 0.15 h of the day left. That last sliver is exactly
    what B02's `free[ln] > CLEAR_H` refuses to start a third product in."""
    S = T.inputs()
    S["meta"]["horizon"] = [T.D0, T.D0]                  # one day, so nothing carries over
    del S["rulebook"]["lines"]["6 Head"]["slots"]["1L"]  # only JP fills these
    for i, (code, pieces) in enumerate((("FGB26A", 800), ("FGB26B", 4000))):
        name = f"MUSTARD KACHI GHANI 1 LTR {chr(65 + i)}"
        S["plan"].append(dict(code=code, sku=name, head="PREMIUM", category="OIL",
                              pack_type="PET", litres_per_piece=1.0, pieces=0, litres=0.0))
        S["bom"][code] = [["RM0000001", 1.0], ["PM" + code, 1.0]]
        S["items"]["PM" + code] = dict(name="BOTTLE " + name, uom="PCS")
        S["realise"][code] = 150.0 - (i + 1)             # FGB26, then A, then B
        S["opening"]["stock"]["PM" + code] = 1_000_000.0
        S["rulebook"]["sku_pack"][code] = dict(sku=name, slot="1L", family="26G",
                                               fills_per_piece=1, litres_per_piece=1.0)
        S["orders"] = [o for o in S["orders"] if o["code"] == "FGB26"]
    for p in S["plan"]:
        p["pieces"] = 0
        p["litres"] = 0.0
    S["orders"] = [
        dict(docnum="PO-1", customer="A REAL CUSTOMER", channel="GT", code="FGB26",
             date=T.D0, pieces=1000, value=150_000.0),      # 5.00 h after a cold start
        dict(docnum="PO-2", customer="A REAL CUSTOMER", channel="GT", code="FGB26A",
             date=T.D0, pieces=800, value=120_000.0),       # 4.00 h, no clearance to pay
        dict(docnum="PO-3", customer="A REAL CUSTOMER", channel="GT", code="FGB26B",
             date=T.D0, pieces=4000, value=600_000.0),      # would fit 29 in what is left
    ]
    return S


def late_lifts(r, session_h):
    """Every run that is the SECOND or later product change of its line-session — a lift —
    with the hours the line had already spent when it opened. B02 lifts the cap 'rather
    than leave a line idle with hours to spare', so a lift with under one clearance left
    is not a lift, it is a sliver run the plant cannot change parts for."""
    last, out = {}, []
    for d in r["days"]:
        for night in (False, True):
            for ln in sorted({x["line"] for x in d["runs"]}):
                used, changes = 0.0, 0
                for x in [y for y in d["runs"] if y["line"] == ln and y["night"] is night]:
                    if last.get(ln) is not None and x["code"] != last[ln]:
                        changes += 1
                    if changes >= 2:
                        out.append(dict(date=d["date"], line=ln, night=night, code=x["code"],
                                        used_h=round(used, 3), left_h=round(session_h - used, 3),
                                        nth=changes))
                    used += x["hours"] + x["flush_min"] / 60.0
                    last[ln] = x["code"]
    return out


class ContinuationAndTheLiftGate(unittest.TestCase):
    """Two scheduling keys nothing asserted on: the continuation key that IS R06, and the
    free-hours clause that is the whole of 'lifted rather than leave a line idle'."""

    SESSION_H = 10.0

    def setUp(self):
        self.churn = churn_inputs()
        self.base = T.run_engine(self.churn, tag="-keys-base")
        self.assertEqual(self.base["rc"], 0, self.base["stderr"])

    @staticmethod
    def _changes(r):
        return r["summary"]["rulebook"]["product_changes"]

    def test_continuation_ranks_first_and_that_is_what_keeps_r06(self):
        """R06 asks for ONE product on a line all day. `0 if c == on_code[ln] else 1` is
        the whole of it: without that key the line re-picks by value at every placement
        and the plant churns. Measured on this fixture: 10 product changes become 29, and
        it makes fewer litres for the privilege."""
        with engine_mutated("return (rb_pref(c, ln), 0 if c == on_code[ln] else 1, t,",
                            "return (rb_pref(c, ln), 0, t,"):
            loose = T.run_engine(self.churn, tag="-keys-r06")
        self.assertEqual(loose["rc"], 0, loose["stderr"])
        self.assertLess(self._changes(self.base), self._changes(loose),
                        "dropping the continuation key changed no product change count — "
                        "R06 is not being enforced by that key at all")
        self.assertGreaterEqual(self.base["summary"]["totals"]["made_l"],
                                loose["summary"]["totals"]["made_l"],
                                "churning made MORE — R06 would be costing litres")

    def test_no_lift_opens_inside_the_last_clearance_of_a_session(self):
        for S, tag in ((self.churn, "-lift-churn"), (sliver_inputs(), "-lift-sliver")):
            r = T.run_engine(S, tag=tag)
            self.assertEqual(r["rc"], 0, r["stderr"])
            for x in late_lifts(r, self.SESSION_H):
                self.assertGreater(
                    x["left_h"], CLEAR_H - 1e-6,
                    f"{tag} {x['date']} {x['line']}: the cap was lifted for {x['code']} with "
                    f"{x['left_h']:.2f} h left, under the {CLEAR_H:.2f} h it takes to change "
                    f"the line over (B02)")

    def test_without_the_free_hours_clause_a_sliver_run_opens(self):
        S = sliver_inputs()
        self.assertEqual(late_lifts(T.run_engine(S, tag="-lift-ok"), self.SESSION_H), [],
                         "the fixture already lifts late — it cannot show the clause working")
        with engine_mutated("                            if free[ln] > CLEAR_H:",
                            "                            if True:"):
            loose = T.run_engine(S, tag="-lift-mut")
        self.assertEqual(loose["rc"], 0, loose["stderr"])
        late = late_lifts(loose, self.SESSION_H)
        self.assertTrue(late, "the mutation did not open a sliver run — the assertion above "
                              "is vacuous")
        self.assertLess(late[0]["left_h"], CLEAR_H)


class HonestyIsDroppedByTagNotByKeyword(unittest.TestCase):
    """The freeze tags every carried assumption with the mode it is true in
    (`honesty.assumed_modes`) and the engine drops only what is tagged for the other one.

    It replaced a keyword blocklist — "derate", "rules.efficiency", "of rated",
    "50% again" — which deleted two sentences that are TRUE under the rulebook and then
    printed a warning blaming the freeze for writing them. A filter that cannot tell a
    true sentence from a false one is not a filter, and the words this plan needs to
    explain itself were exactly the words it was banning.
    """

    TRUE_IN_BOTH = ("every line is planned at 80% of rated capacity, capped by its best "
                    "August hour, and the plan never derates a planning speed a second "
                    "time (R05/A01)")
    LEGACY_ONLY = "the engine applies rules.efficiency (0.5) on top of the rated speed"
    UNTAGGED = "supply arrives exactly on its lead time"

    def fixture(self):
        S = T.inputs()
        S["honesty"] = {
            "measured": ["the opening position"],
            "assumed": [self.TRUE_IN_BOTH, self.LEGACY_ONLY, self.UNTAGGED],
            "assumed_modes": {self.TRUE_IN_BOTH: "both", self.LEGACY_ONLY: "legacy"},
        }
        return S

    def test_a_true_sentence_full_of_the_old_banned_words_survives(self):
        r = T.run_engine(self.fixture(), tag="-honesty")
        self.assertEqual(r["rc"], 0, r["stderr"])
        assumed = r["days"][0]["honesty"]["assumed"]
        self.assertIn(self.TRUE_IN_BOTH, assumed,
                      "a sentence tagged as true in both modes was deleted")
        self.assertIn(self.UNTAGGED, assumed, "an untagged sentence must default to kept")

    def test_a_sentence_tagged_for_the_other_mode_is_dropped_and_named(self):
        r = T.run_engine(self.fixture(), tag="-honesty2")
        assumed = r["days"][0]["honesty"]["assumed"]
        self.assertNotIn(self.LEGACY_ONLY, assumed)
        self.assertEqual(r["summary"]["rulebook"]["honesty_dropped"], [self.LEGACY_ONLY])

    def test_the_tag_map_itself_is_never_published(self):
        r = T.run_engine(self.fixture(), tag="-honesty3")
        for d in r["days"]:
            self.assertNotIn("assumed_modes", d["honesty"])

    def test_the_run_states_its_own_rules_first(self):
        r = T.run_engine(self.fixture(), tag="-honesty4")
        assumed = r["days"][0]["honesty"]["assumed"]
        self.assertIn("(A01)", assumed[0])
        self.assertLess(assumed.index(assumed[0]), assumed.index(self.TRUE_IN_BOTH))

    def test_nothing_is_dropped_when_nothing_is_tagged(self):
        S = T.inputs()
        S["honesty"] = {"measured": [], "assumed": [self.TRUE_IN_BOTH, self.LEGACY_ONLY]}
        r = T.run_engine(S, tag="-honesty-untagged")
        self.assertEqual(r["rc"], 0, r["stderr"])
        self.assertEqual(r["summary"]["rulebook"]["honesty_dropped"], [])
        self.assertIn(self.LEGACY_ONLY, r["days"][0]["honesty"]["assumed"])


if __name__ == "__main__":
    unittest.main()
