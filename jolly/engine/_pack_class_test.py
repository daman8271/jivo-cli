#!/usr/bin/env python3
"""Unit tests for engine/pack_class.py — R15, the pack comes from the RECIPE.

    cd jolly && python3 -m unittest engine._pack_class_test -v

Two halves:

  * REGRESSION — pack_class() reproduces `rulebook.sku_pack` for every row of the
    frozen plan, key for key. This is the guard on the refactor that moved the
    rule out of reference/build_mark4_rulebook.py: the freeze and gen's AC06
    check now call this module, so a silent drift here would put 15-litre tins
    back on Clear Pack without anything failing.
  * THE CASES THAT DECIDE A LINE — the eight rows where the plan sheet says PET
    and the recipe says tin, the four combo sets that are two one-litre bottles
    apiece, the 3 L bottle Mark 3 called unproducible, the small packs with no
    bottle in their recipe at all, the drums, the pouches, and synthetic bottles
    no plan row exercises today.
  * WHAT THE RULEBOOK CLAIMS ABOUT ITSELF — the caller list, the post-efficiency
    flag on every speed, and the two slot vocabularies. It is published on the
    site's /assumptions page, where a reader goes precisely to check.

`sim/sep-inputs.json` holds 84 plan rows (the resolvable subset of the sheet's
99); the regression covers all 84 and the rulebook's own count is asserted, so a
re-freeze that changes the sheet fails here rather than passing quietly.
"""

from __future__ import annotations

import ast
import json
import os
import unittest

try:                                                # normal: run from jolly/
    from engine.pack_class import (ALL_FAMILIES, ENGINE_SLOTS, FAMILIES, SLOTS, bottle_family,
                                   container_litres, container_of, engine_slot, pack_class,
                                   sheet_slot, slot_by_litres)
except ImportError:                                 # run from inside engine/
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from engine.pack_class import (ALL_FAMILIES, ENGINE_SLOTS, FAMILIES, SLOTS, bottle_family,
                                   container_litres, container_of, engine_slot, pack_class,
                                   sheet_slot, slot_by_litres)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUTS = os.path.join(ROOT, "sim/sep-inputs.json")
RULEBOOK = os.path.join(ROOT, "reference/mark4-rulebook.json")
RUNS_CSV = os.path.join(ROOT, "out/august-actuals-SCORING.csv")
CALIBRATION = os.path.join(ROOT, "reference/august-calibration.json")

# The rows where the sheet says PET and the recipe uses a tin (R15). Seven are
# 15-litre tins; SO Olive is a printed 5-litre tin.
SHEET_DISAGREES = ["FG0000191", "FG0000015", "FG0000275", "FG0000132",
                   "FG0000158", "FG0000367", "FG0000026", "FG0000232"]

# "1 LTR + 1 LTR COMBO 10 SET": one saleable piece, TWO one-litre 40 g bottles.
# Read as a 2-litre pack these went to a 2 L slot at half the bottle count, and
# the mustard one escaped both the mustard rule and the 40 g rule (B13).
COMBOS = ["FG0000033", "FG0000088", "FG0000091", "FG0000429"]

# The files the regression stands on. Absent, six setUpClass calls raise SkipTest,
# unittest collapses each class into ONE "s", and the command still exits 0 — 55
# tests become 27 and the R15 regression silently does not run. BaselinePresent
# turns that into a failure; set this to 1 on a fresh clone that has not built the
# rulebook yet.
ALLOW_MISSING = os.environ.get("PACK_CLASS_ALLOW_MISSING_BASELINE") == "1"

# The live copies of the LEGACY sheet-based slot rule that pack_class.sheet_slot()
# claims to reproduce, and that the rulebook publishes as `sku_pack.sheet_slot`.
# live/freeze_live.py had a third copy until WS3 deleted it as dead code (the freeze
# refuses to run without a rulebook, so its legacy slot table could never be reached
# again). gen keeps ITS copy because the -sep path still needs it, so gen stays here —
# this list names the copies that EXIST, and a copy that comes back has to be added.
LEGACY_COPIES = [("engine/august_sim.py", "slot"),
                 ("live/gen_live.py", "slot_of")]

# What a `planning_rule.kind` may be. gen recomputes `planning` from these and
# nothing else — a new kind must be taught to the recompute, not just published.
PLANNING_KINDS = {"capped", "rated", "carried", "typical", "derived", "none"}


def _load():
    if not (os.path.exists(INPUTS) and os.path.exists(RULEBOOK)):
        raise unittest.SkipTest("sim/sep-inputs.json or reference/mark4-rulebook.json "
                                "is absent — run reference/build_mark4_rulebook.py")
    with open(INPUTS, encoding="utf-8") as fh:
        S = json.load(fh)
    with open(RULEBOOK, encoding="utf-8") as fh:
        R = json.load(fh)
    return S, R


class Regression(unittest.TestCase):
    """pack_class() == rulebook.sku_pack, row for row."""

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()
        cls.plan = {p["code"]: p for p in cls.S["plan"]}
        cls.bom, cls.items = cls.S["bom"], cls.S["items"]
        cls.sku_pack = cls.R["sku_pack"]

    def _classed(self, code):
        p = self.plan[code]
        return pack_class(code, self.bom, self.items, p["litres_per_piece"], p["pack_type"])

    def test_every_plan_code_reproduced(self):
        self.assertEqual(len(self.sku_pack), 84, "the frozen plan is 84 rows")
        self.assertEqual(sorted(self.sku_pack), sorted(self.plan), "sku_pack and plan disagree on codes")
        for code in sorted(self.plan):
            got, want = self._classed(code), self.sku_pack[code]
            for k in ("slot", "family", "container", "container_name", "sheet_disagrees",
                      "fills_per_piece", "litres_per_fill", "container_litres", "engine_slot"):
                self.assertEqual(got[k], want[k], "%s %s: %r != rulebook %r" % (code, k, got[k], want[k]))

    def test_slot_and_family_labels_are_published_ones(self):
        for code, v in self.sku_pack.items():
            self.assertIn(v["slot"], SLOTS, "%s has an unpublished slot" % code)
            self.assertIn(v["family"], ALL_FAMILIES, "%s has an unpublished family" % code)

    def test_module_constants_match_the_rulebook(self):
        self.assertEqual(SLOTS, self.R["pack_class"]["slots"])
        self.assertEqual(FAMILIES, self.R["pack_class"]["families"])

    def test_no_plan_row_is_unclassed(self):
        # UNKNOWN means neither a container in the recipe nor a small pack: the
        # freeze would have nothing to schedule it on.
        self.assertEqual([c for c, v in self.sku_pack.items() if v["family"] == "UNKNOWN"], [])


class SheetDisagrees(unittest.TestCase):
    """The eight rows R15 exists for."""

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()
        cls.plan = {p["code"]: p for p in cls.S["plan"]}
        cls.bom, cls.items = cls.S["bom"], cls.S["items"]

    def _classed(self, code):
        p = self.plan[code]
        return pack_class(code, self.bom, self.items, p["litres_per_piece"], p["pack_type"])

    def test_the_eight_are_tins(self):
        flagged = sorted(c for c, v in self.R["sku_pack"].items() if v["sheet_disagrees"])
        self.assertEqual(flagged, sorted(SHEET_DISAGREES))
        for code in SHEET_DISAGREES:
            got = self._classed(code)
            self.assertEqual(self.plan[code]["pack_type"], "PET", "%s: the sheet no longer says PET" % code)
            self.assertEqual(got["family"], "TIN", "%s is not classed as a tin" % code)
            self.assertTrue(got["sheet_disagrees"], "%s should be flagged" % code)
            want = "5L" if code == "FG0000232" else "15L"
            self.assertEqual(got["slot"], want, "%s slot" % code)
            self.assertIn("TIN", got["container_name"])

    def test_a_tin_the_sheet_calls_a_tin_is_not_flagged(self):
        tins = [c for c, v in self.R["sku_pack"].items()
                if v["family"] == "TIN" and v["sheet_pack_type"] == "TIN"]
        self.assertTrue(tins, "no plan row is a tin on both sides")
        for code in tins:
            self.assertFalse(self._classed(code)["sheet_disagrees"], "%s wrongly flagged" % code)


class RealRows(unittest.TestCase):
    """The rows a wrong answer sends to the wrong machine."""

    @classmethod
    def setUpClass(cls):
        cls.S, _R = _load()
        cls.plan = {p["code"]: p for p in cls.S["plan"]}
        cls.bom, cls.items = cls.S["bom"], cls.S["items"]

    def _classed(self, code):
        p = self.plan[code]
        return pack_class(code, self.bom, self.items, p["litres_per_piece"], p["pack_type"])

    def test_cold_press_3l_is_a_3l_hdpe_bottle(self):
        # Mark 3 called FG0000043 unproducible; it is a 3 L bottle for the 6 Head.
        got = self._classed("FG0000043")
        self.assertEqual((got["slot"], got["family"]), ("3L", "HDPE"))
        self.assertEqual(got["container"], "PM0000113")

    def test_kachi_ghani_500ml_has_no_bottle_in_its_recipe(self):
        got = self._classed("FG0000448")
        self.assertEqual((got["slot"], got["family"]), ("1L", "SMALL"))
        self.assertIsNone(got["container"])
        self.assertIsNone(got["container_name"])
        self.assertFalse(got["sheet_disagrees"])

    def test_a_small_bottle_beats_its_gram_family(self):
        # 500 ml in a 34 g bottle: SMALL, not "34G" — the line cares about the pack.
        got = self._classed("FG0000035")
        self.assertEqual((got["slot"], got["family"]), ("1L", "SMALL"))
        self.assertEqual(got["container_name"], "PET BOTTLE 500 MLS 34 GMS")

    def test_the_drums(self):
        for code in ("FG0000034", "FG0000328", "FG0000006"):
            got = self._classed(code)
            self.assertEqual((got["slot"], got["family"]), ("DRUM", "DRUM"), code)

    def test_the_pouches(self):
        for code in ("FG0000194", "FG0000106", "FG0000021"):
            got = self._classed(code)
            self.assertEqual((got["slot"], got["family"]), ("POUCH", "POUCH"), code)

    def test_mustard_1l_is_a_26g_bottle_and_groundnut_is_52g(self):
        self.assertEqual(self._classed("FG0000030")["family"], "26G")   # JP's own bottle
        self.assertEqual(self._classed("FG0000142")["family"], "52G")   # 52 g: JP last resort


class Synthetic(unittest.TestCase):
    """Packs no plan row exercises today, built by hand."""

    ITEMS = {
        "RM9000001": {"name": "SOME OIL", "uom": "LTR"},
        "PM9000066": {"name": "PET BOTTLE 2 LTR 66 GM", "uom": "PCS"},
        "PM9000000": {"name": "PET BOTTLE 1 LTR PLAIN", "uom": "PCS"},
        "PM9000033": {"name": "PET BOTTLE 1 LTR 33 GM", "uom": "PCS"},
        "PM9000CAP": {"name": "CAP 1 LTR", "uom": "PCS"},
        "PM9000CTN": {"name": "CARTON 1 LTR 20 PCS", "uom": "PCS"},
        "PM9000TIN": {"name": "TIN 15 LTR", "uom": "PCS"},
    }
    BOM = {
        "FG9000002": [["RM9000001", 2.0], ["PM9000066", 1.0]],
        "FG9000001": [["RM9000001", 1.0], ["PM9000000", 1.0]],
        "FG9000033": [["RM9000001", 1.0], ["PM9000033", 1.0]],
        "FG9000CAP": [["RM9000001", 1.0], ["PM9000CAP", 1.0], ["PM9000CTN", 0.05]],
        "FG9000KGS": [["RM9000001", 14.3], ["PM9000TIN", 1.0]],
    }

    def _classed(self, code, litres, pack_type="PET"):
        return pack_class(code, self.BOM, self.ITEMS, litres, pack_type)

    def test_two_litre_bottle_is_2l_any(self):
        # 2 L has no family rule — one family per size above 1 L (A03).
        got = self._classed("FG9000002", 2.0)
        self.assertEqual((got["slot"], got["family"]), ("2L", "ANY"))
        self.assertEqual(got["container"], "PM9000066")

    def test_one_litre_bottle_of_unknown_grams(self):
        got = self._classed("FG9000001", 1.0)
        self.assertEqual((got["slot"], got["family"]), ("1L", "1L-OTHER"))

    def test_one_litre_bottle_of_an_unlisted_gram_weight(self):
        # 33 g is nobody's family: it is named, and no line claims it.
        got = self._classed("FG9000033", 1.0)
        self.assertEqual((got["slot"], got["family"]), ("1L", "33G"))
        self.assertNotIn("33G", FAMILIES)

    def test_a_recipe_with_no_container_at_all(self):
        got = self._classed("FG9000CAP", 1.0)
        self.assertEqual((got["slot"], got["family"]), ("1L", "UNKNOWN"))
        self.assertIsNone(got["container"])

    def test_a_tin_named_by_weight_is_the_15l_slot(self):
        # A 13 kg tin is 14.3 L of oil in the same 15 L tin: same slot, same rate.
        got = self._classed("FG9000KGS", 14.3, "PET")
        self.assertEqual((got["slot"], got["family"]), ("15L", "TIN"))
        self.assertTrue(got["sheet_disagrees"])

    def test_container_of_takes_the_first_container_child_and_its_quantity(self):
        self.assertEqual(container_of("FG9000002", self.BOM, self.ITEMS),
                         ("PM9000066", "PET BOTTLE 2 LTR 66 GM", 1.0))
        self.assertEqual(container_of("FG_NOT_THERE", self.BOM, self.ITEMS), (None, None, 0.0))


class Adversarial(unittest.TestCase):
    """Inputs nobody meant to send: wrong case, wrong type, a name that only
    looks like a container. Each of these is load-bearing — a regex or a cast
    changed carelessly puts a product on the wrong machine, silently."""

    ITEMS = {
        "PM9000026": {"name": "PET BOTTLE 1 LTR 26 GM"},
        "PM9000CAN": {"name": "STICKER CANOLA 1 LTR"},
        "PM9000LBL": {"name": "LABEL 1 LTR CANOLA REFINED"},
        "PM9000LOW": {"name": "pet bottle 1 ltr 26 gm"},
        "PM9000TIN": {"name": "TIN 15 LTR"},
        "PM9000HDP": {"name": "HDPE BOTTLE 5 LTR"},
        "PM9000DRM": {"name": "DRUM 200 LTR"},
    }
    BOM = {
        "FG9000CAN": [["PM9000CAN", 1.0], ["PM9000LBL", 1.0], ["PM9000026", 1.0]],
        "FG9000LOW": [["PM9000LOW", 1.0]],
        "FG9000TIN": [["PM9000TIN", 1.0]],
        "FG9000HDP": [["PM9000HDP", 1.0]],
        "FG9000DRM": [["PM9000DRM", 1.0]],
    }

    def test_canola_is_not_a_can(self):
        # CAN\b must not fire on CANOLA, or every canola row becomes a container
        # and the real bottle is never seen. Two decoys before the bottle.
        self.assertEqual(container_of("FG9000CAN", self.BOM, self.ITEMS),
                         ("PM9000026", "PET BOTTLE 1 LTR 26 GM", 1.0))

    def test_item_names_are_matched_case_insensitively(self):
        got = pack_class("FG9000LOW", self.BOM, self.ITEMS, 1.0, "PET")
        self.assertEqual((got["slot"], got["family"]), ("1L", "26G"))

    def test_pack_type_is_matched_case_insensitively(self):
        self.assertEqual(slot_by_litres(200.0, "drum"), "DRUM")
        self.assertEqual(slot_by_litres(1.0, "Pouch"), "POUCH")
        self.assertEqual(slot_by_litres(15.0, "tin"), "15L")

    def test_litres_arriving_as_a_string(self):
        # the freeze reads JSON that has carried numbers as text before now
        self.assertEqual(slot_by_litres("5", "PET"), "5L")
        self.assertEqual(slot_by_litres("15", "TIN"), "15L")

    def test_an_unknown_code_is_unknown_not_a_crash(self):
        got = pack_class("FG_NEVER_SEEN", self.BOM, self.ITEMS, 1.0, "PET")
        self.assertEqual((got["slot"], got["family"], got["container"]), ("1L", "UNKNOWN", None))

    def test_sheet_disagrees_fires_for_tins_only(self):
        # the flag means "the sheet said PET and the recipe says tin" — nothing else
        self.assertTrue(pack_class("FG9000TIN", self.BOM, self.ITEMS, 15.0, "PET")["sheet_disagrees"])
        self.assertFalse(pack_class("FG9000HDP", self.BOM, self.ITEMS, 5.0, "PET")["sheet_disagrees"])
        self.assertFalse(pack_class("FG9000DRM", self.BOM, self.ITEMS, 200.0, "PET")["sheet_disagrees"])
        self.assertFalse(pack_class("FG9000TIN", self.BOM, self.ITEMS, 15.0, "TIN")["sheet_disagrees"])

    def test_the_small_pack_boundary_is_strict(self):
        # 0.95 L is NOT small; a hair under is. The cut decides which line fills it.
        self.assertEqual(bottle_family("PET BOTTLE 1 LTR 26 GM", 0.95), "26G")
        self.assertEqual(bottle_family("PET BOTTLE 1 LTR 26 GM", 0.9499), "SMALL")

    def test_gram_tolerance_is_one_gram(self):
        self.assertEqual(bottle_family("PET BOTTLE 1 LTR 26.4 GM", 1.0), "26G")
        self.assertEqual(bottle_family("PET BOTTLE 1 LTR 27.5 GM", 1.0), "27.5G")
        self.assertNotIn("27.5G", ALL_FAMILIES)      # named, and eligible nowhere


class Slots(unittest.TestCase):
    """slot_by_litres — the boundaries, and the tin bucket."""

    def test_pet_boundaries(self):
        for l, want in [(0.01, "1L"), (0.5, "1L"), (1.0, "1L"), (1.05, "1L"), (1.06, "2L"),
                        (2.0, "2L"), (3.0, "3L"), (4.0, "4L"), (5.0, "5L"), (5.06, "15L"), (15.0, "15L")]:
            self.assertEqual(slot_by_litres(l, "PET"), want, "%s L" % l)

    def test_tins_bucket_at_twelve_litres(self):
        self.assertEqual(slot_by_litres(3.0, "TIN"), "3L")
        self.assertEqual(slot_by_litres(5.0, "TIN"), "5L")
        self.assertEqual(slot_by_litres(11.9, "TIN"), "5L")      # below the bucket
        self.assertEqual(slot_by_litres(13.2, "TIN"), "15L")     # a 12 kg tin
        self.assertEqual(slot_by_litres(15.0, "TIN"), "15L")

    def test_drum_and_pouch_come_from_the_pack_type(self):
        self.assertEqual(slot_by_litres(200.0, "DRUM"), "DRUM")
        self.assertEqual(slot_by_litres(1.0, "POUCH"), "POUCH")

    def test_missing_pack_type_is_not_a_crash(self):
        self.assertEqual(slot_by_litres(1.0, None), "1L")
        self.assertEqual(slot_by_litres("5", ""), "5L")

    def test_a_size_nobody_states_is_no_slot_not_the_smallest_one(self):
        # it used to read as zero litres and come back "1L" — a silent wrong
        # machine for anything the sheet forgot to size (B15).
        for missing in (None, "", 0, -1, "abc"):
            self.assertIsNone(slot_by_litres(missing, ""), repr(missing))
        # a drum or a pouch still settles itself: neither needs a size
        self.assertEqual(slot_by_litres(None, "DRUM"), "DRUM")
        self.assertEqual(slot_by_litres(None, "POUCH"), "POUCH")
        self.assertIsNone(slot_by_litres(None, "TIN"))

    def test_bottle_family_labels(self):
        for name, want in [("PET BOTTLE 1 LTR 26 GM", "26G"), ("PET BOTTLE 1 LTR ROUND 23.8 GM", "ROUND-23.8G"),
                           ("PET BOTTLE 1 LTR 40 GMS", "40G"), ("PET BOTTLE 1 LTR 52 GMS POMACE", "52G"),
                           ("PET BOTTLE 1 LTR 75 GM", "75G"), ("PET BOTTLE 1 LTR", "1L-OTHER")]:
            self.assertEqual(bottle_family(name, 1.0), want, name)
        self.assertEqual(bottle_family("PET BOTTLE 1 LTR 26 GM", 0.5), "SMALL")


class MultiFill(unittest.TestCase):
    """A piece that holds more than one container. The line fills CONTAINERS —
    the slot, the bottle and the count all follow the recipe, not the set (B13)."""

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()
        cls.plan = {p["code"]: p for p in cls.S["plan"]}
        cls.bom, cls.items = cls.S["bom"], cls.S["items"]

    def _classed(self, code):
        p = self.plan[code]
        return pack_class(code, self.bom, self.items, p["litres_per_piece"], p["pack_type"])

    def test_the_combo_sets_are_one_litre_bottles_filled_twice(self):
        for code in COMBOS:
            got = self._classed(code)
            self.assertEqual(self.plan[code]["litres_per_piece"], 2.0, code)
            self.assertEqual(got["fills_per_piece"], 2, "%s: the recipe names two bottles" % code)
            self.assertEqual(got["litres_per_fill"], 1.0, code)
            self.assertEqual((got["slot"], got["family"]), ("1L", "40G"), code)
            self.assertEqual(got["engine_slot"], "1L", code)
            self.assertEqual(got["container"], "PM0000194", code)

    def test_the_mustard_combo_reaches_the_bottle_rules_at_all(self):
        # read as a 2 L pack it was family ANY, so neither the mustard ruling
        # (R09) nor the 40 g ruling (R10/A14) could see it.
        got = self._classed("FG0000429")
        self.assertEqual(got["family"], "40G")
        self.assertIn("MUSTARD", self.plan["FG0000429"]["sku"].upper())

    def test_every_other_plan_row_fills_once(self):
        for code, v in self.R["sku_pack"].items():
            if code in COMBOS:
                continue
            self.assertEqual(v["fills_per_piece"], 1, "%s is not a combo" % code)
            self.assertEqual(v["litres_per_fill"], v["litres_per_piece"], code)

    def test_a_tin_named_by_weight_is_not_a_multipack(self):
        # 15 KGS = 16.48 L of oil in ONE 15 LTR tin: the printed size and the fill
        # legitimately differ, and nothing may divide by it.
        got = self._classed("FG0000250")
        self.assertEqual(got["fills_per_piece"], 1)
        self.assertEqual(got["container_litres"], 15.0)
        self.assertEqual(got["litres_per_fill"], self.plan["FG0000250"]["litres_per_piece"])
        self.assertEqual((got["slot"], got["family"]), ("15L", "TIN"))

    def test_container_litres_reads_sizes_not_bottle_weights(self):
        # "40 GMS" is what the bottle weighs, never what it holds
        self.assertEqual(container_litres("PET BOTTLE 1 LTR 40 GMS"), 1.0)
        self.assertEqual(container_litres("GLASS BOTTLE 500 MLS"), 0.5)
        self.assertEqual(container_litres("TIN 15 LTR"), 15.0)
        self.assertIsNone(container_litres("PET BOTTLE PLAIN"))
        self.assertIsNone(container_litres(None))


class NotTheContainer(unittest.TestCase):
    """A carton, a label, a cap or a strip may NAME the container. It is not the
    container (B14). Twenty-two plan recipes list one beside the real thing."""

    ITEMS = {
        "PM9000CTN": {"name": "CARTON 5 LTR TIN PRINTED"},
        "PM9000TOP": {"name": "CARTON TIN TOP"},
        "PM9000LBL": {"name": "LABEL 2 LTR HANDLE BOTTLE FRONT"},
        "PM9000CAP": {"name": "CAPS 250 MLS GLASS BOTTLE"},
        "PM9000STR": {"name": "TIN STRIP"},
        "PM9000BTL": {"name": "PET BOTTLE 1 LTR 26 GM"},
        "PM9000TIN": {"name": "TIN 15 LTR"},
        "PM9000NUL": {"name": None},
    }
    BOM = {
        # the carton is listed FIRST and says TIN — Mark 3's exact failure shape
        "FG9000CTN": [["PM9000CTN", 0.25], ["PM9000BTL", 1.0]],
        "FG9000LBL": [["PM9000LBL", 1.0], ["PM9000BTL", 1.0]],
        "FG9000CAP": [["PM9000CAP", 1.0], ["PM9000BTL", 1.0]],
        "FG9000TOP": [["PM9000TOP", 1.0], ["PM9000STR", 0.01], ["PM9000TIN", 1.0]],
        "FG9000NUL": [["PM9000NUL", 1.0], ["PM9000BTL", 1.0]],
    }

    def _classed(self, code, litres, pack_type="PET"):
        return pack_class(code, self.BOM, self.ITEMS, litres, pack_type)

    def test_a_carton_that_mentions_a_tin_is_not_a_tin(self):
        got = self._classed("FG9000CTN", 1.0)
        self.assertEqual((got["slot"], got["family"]), ("1L", "26G"))
        self.assertFalse(got["sheet_disagrees"], "a carton must not raise the R15 flag")

    def test_a_label_and_a_cap_are_not_the_bottle(self):
        for code in ("FG9000LBL", "FG9000CAP"):
            self.assertEqual(self._classed(code, 1.0)["container"], "PM9000BTL", code)

    def test_the_tin_is_still_found_behind_its_carton_top_and_strip(self):
        got = self._classed("FG9000TOP", 15.0)
        self.assertEqual((got["slot"], got["family"], got["container"]), ("15L", "TIN", "PM9000TIN"))

    def test_an_item_with_no_name_does_not_crash(self):
        # a wider item pull carries nulls; the freeze will meet them (A18)
        got = self._classed("FG9000NUL", 1.0)
        self.assertEqual(got["container"], "PM9000BTL")


class UnknownSize(unittest.TestCase):
    """Nothing states a size. Publish that, never guess the smallest bottle (B15)."""

    ITEMS = {"PM9000BTL": {"name": "PET BOTTLE 1 LTR 26 GM"},
             "PM9000ANY": {"name": "PET BOTTLE PLAIN"},
             "PM9000DRM": {"name": "MS COATED DRUM 200 LTR"}}
    BOM = {"FG9000SIZ": [["PM9000BTL", 1.0]],
           "FG9000NOS": [["PM9000ANY", 1.0]],
           "FG9000DRM": [["PM9000DRM", 1.0]]}

    def test_the_container_supplies_the_size_when_the_sheet_does_not(self):
        got = pack_class("FG9000SIZ", self.BOM, self.ITEMS, None, "PET")
        self.assertEqual((got["slot"], got["family"]), ("1L", "26G"))
        self.assertEqual(got["container_litres"], 1.0)

    def test_no_size_anywhere_is_no_slot(self):
        for missing in (None, "", 0):
            got = pack_class("FG9000NOS", self.BOM, self.ITEMS, missing, "PET")
            self.assertIsNone(got["slot"], repr(missing))
            self.assertEqual(got["family"], "UNKNOWN", repr(missing))
            self.assertIsNone(got["engine_slot"], repr(missing))

    def test_a_drum_needs_no_size(self):
        got = pack_class("FG9000DRM", self.BOM, self.ITEMS, None, "")
        self.assertEqual((got["slot"], got["family"]), ("DRUM", "DRUM"))


class EngineVocabulary(unittest.TestCase):
    """Mark 4 splits tins by size; the engine's `lines` table has ONE tin bucket.
    Merging a speed across the two without mapping re-keys some rows and not
    others, and the table still looks plausible."""

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()
        cls.plan = {p["code"]: p for p in cls.S["plan"]}
        cls.sku_pack = cls.R["sku_pack"]

    def test_tin_is_a_family_here_and_a_slot_there(self):
        self.assertNotIn("TIN", SLOTS)
        self.assertIn("TIN", FAMILIES)
        self.assertIn("TIN", ENGINE_SLOTS)
        self.assertEqual(ENGINE_SLOTS, self.R["pack_class"]["engine_slots"])

    def test_every_tin_maps_to_the_one_bucket(self):
        for code, v in self.sku_pack.items():
            if v["family"] == "TIN":
                self.assertEqual(engine_slot(v), "TIN", code)
                self.assertIn(v["slot"], ("3L", "5L", "15L"), code)

    def test_everything_else_keeps_its_slot(self):
        for code, v in self.sku_pack.items():
            if v["family"] != "TIN":
                self.assertEqual(engine_slot(v), v["slot"], code)
            self.assertIn(v["engine_slot"], ENGINE_SLOTS, code)

    def test_sheet_slot_reproduces_the_legacy_rule(self):
        # the rule re-stated independently, exactly as engine/august_sim.py slot()
        # has it — if the engine's copy is ever changed, this is what catches it
        def legacy(p):
            pt, sku, l = p["pack_type"].upper(), p["sku"].upper(), p["litres_per_piece"]
            if "DRUM" in pt: return "DRUM"
            if "TIN" in pt or "KGS" in sku: return "TIN"
            if "POUCH" in pt or "POUCH" in sku: return "POUCH"
            for cap, name in ((1.05, "1L"), (2.05, "2L"), (3.05, "3L"), (4.05, "4L"), (5.05, "5L")):
                if l <= cap: return name
            return "15L"
        for code, p in self.plan.items():
            self.assertEqual(sheet_slot(p["sku"], p["pack_type"], p["litres_per_piece"]),
                             legacy(p), code)
            self.assertEqual(self.sku_pack[code]["sheet_slot"], legacy(p), code)

    def test_sheet_slot_reads_a_kgs_name_as_a_tin(self):
        # every KGS row on this sheet also has pack_type TIN, so the plan rows
        # alone cannot tell whether the name half of the legacy rule survives
        self.assertEqual(sheet_slot("SOYABEAN OIL 15 KGS", "PET", 16.4835), "TIN")
        self.assertEqual(sheet_slot("SOYABEAN OIL 15 LTR", "PET", 15.0), "15L")
        self.assertEqual(sheet_slot("REFINED OIL 1 LTR POUCH 12 PCS", "PET", 1.0), "POUCH")
        self.assertEqual(sheet_slot("SOME OIL 200 LTR", "DRUM", 200.0), "DRUM")

    def test_the_published_disagreements_are_the_tins_and_the_combos(self):
        published = self.R["pack_class"]["engine_slot_disagrees"]
        computed = sorted(c for c, v in self.sku_pack.items() if v["sheet_slot"] != v["engine_slot"])
        self.assertEqual(published, computed)
        self.assertEqual(computed, sorted(SHEET_DISAGREES + COMBOS))


class RulebookShape(unittest.TestCase):
    """What the rulebook says about ITSELF has to be true — it is published on the
    site's /assumptions page, where a reader goes precisely to check."""

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()

    def test_it_only_claims_the_callers_it_has(self):
        used = self.R["pack_class"]["used_by"]
        self.assertIn("reference/build_mark4_rulebook.py", used)
        for rel in used:
            src = os.path.join(ROOT, rel)
            self.assertTrue(os.path.exists(src), rel)
            with open(src, encoding="utf-8") as fh:
                self.assertIn("pack_class", fh.read(), "%s does not use pack_class" % rel)
        for rel in self.R["pack_class"]["to_be_wired"]:
            self.assertNotIn(rel, used, "%s is wired — it cannot also be pending" % rel)

    def test_planning_speeds_say_they_are_post_efficiency(self):
        # `lines` in sim/*-inputs.json holds RATED speeds and the engine derates
        # them at run time. A planning speed dropped in there unflagged halves
        # the plant and every cross-check still passes.
        for ln, spec in self.R["lines"].items():
            for slot, sp in spec["speeds"].items():
                self.assertTrue(sp["post_efficiency"], "%s %s" % (ln, slot))
        eff = self.R["efficiency"]
        self.assertTrue(eff["planning_is_post_efficiency"])
        self.assertEqual(eff["rules_efficiency_when_planning_speeds_are_used"], 1.0)

    def test_a_slot_with_no_rate_says_so_rather_than_carrying_a_number(self):
        # B16: no rating, and too little evidence to be a typical rate. It keeps
        # whatever runs it has — the blank is about their WEIGHT, not their absence —
        # so the block must never claim more of them than min_runs allows.
        for ln, spec in self.R["lines"].items():
            for slot, sp in spec["speeds"].items():
                if sp["planning"] is None:
                    self.assertEqual(sp["planning_rule"]["kind"], "none", "%s %s" % (ln, slot))
                    self.assertIsNone(sp["rated"], "%s %s" % (ln, slot))
                    self.assertLess(sp["aug_runs_sustained"], sp["planning_rule"]["min_runs"],
                                    "%s %s: enough sustained runs to be a typical rate, so it "
                                    "should have one" % (ln, slot))
                else:
                    self.assertNotEqual(sp["planning_rule"]["kind"], "none", "%s %s" % (ln, slot))

    def test_clear_pack_has_no_two_litre_record(self):
        # B16: every August "2 L" run on Clear Pack was a combo set of 1 L
        # bottles. If the plant has since run a real 2 L bottle there, this is
        # the test to update — and B16 with it.
        self.assertIsNone(self.R["lines"]["Clear Pack"]["speeds"]["2L"]["planning"])
        self.assertEqual(self.R["lines"]["Clear Pack"]["speeds"]["2L"]["aug_runs"], 0)

    def test_the_six_head_three_litre_slot_is_not_planned_from_a_clock_error(self):
        # B18: the three August runs were 11, 820 and 4,183 pieces/hr. 4,183
        # three-litre bottles is 12,540 L/hr on a line whose best rated slot pours
        # 3,000, and the 71-minute segment that produced it used to set the median
        # that became the planning speed — a 3 L pack filling faster in litres than
        # the 5 L on the same heads.
        sp = self.R["lines"]["6 Head"]["speeds"]["3L"]
        self.assertIsNone(sp["planning"], "6 Head 3 L is planned from two runs again")
        self.assertGreaterEqual(sp["aug_runs_discarded"], 1, "the clock error is back in the pool")
        self.assertLess(sp["aug_max"] * 3, 1.2 * 3000 + 1,
                        "a kept 6 Head run pours more litres than the line's best rated slot")

    def test_a_combo_never_takes_the_plain_bottles_speed(self):
        # B19: on Clear Pack the two populations do not overlap at any point.
        cp = self.R["lines"]["Clear Pack"]
        plain, combo = cp["speeds"]["1L"], cp["speeds_multi"]["1L"]
        self.assertFalse(plain["multi_fill"])
        self.assertTrue(combo["multi_fill"])
        self.assertEqual(plain["aug_runs"], 6)
        self.assertEqual(combo["aug_runs"], 6)
        self.assertLess(combo["aug_max"], plain["aug_min"],
                        "the combo and plain clusters now overlap — re-read B19 before merging")
        self.assertLess(combo["planning"], plain["planning"])

    def test_a_line_with_no_combo_record_publishes_no_combo_rate(self):
        # A blank is the point: a SKU with more than one container per piece cannot
        # be scheduled where the line has never run one (B19).
        for ln, spec in self.R["lines"].items():
            self.assertIn("speeds_multi", spec, ln)
            for slot, sp in spec["speeds_multi"].items():
                self.assertGreater(sp["aug_runs"], 0,
                                   "%s %s combo block with no runs behind it" % (ln, slot))
                self.assertNotIn(sp["planning_rule"]["kind"], ("carried", "derived"),
                                 "%s %s: a combo rate may not be carried or derived" % (ln, slot))
        self.assertEqual({ln for ln, spec in self.R["lines"].items() if spec["speeds_multi"]},
                         {"Clear Pack"}, "a line has gained or lost its combo record")

    def test_the_rulings_and_assumptions_are_published_in_order(self):
        for key in ("settled", "assumed"):
            ids = [r["id"] for r in self.R[key]]
            self.assertEqual(ids, sorted(ids), "%s is out of id order — /assumptions renders it" % key)
            self.assertEqual(len(ids), len(set(ids)), key)

    def test_the_pack_class_block_explains_the_fields_the_plan_will_consume(self):
        pc = self.R["pack_class"]
        for key in ("fills_rule", "container_check", "engine_slot_rule"):
            self.assertTrue(pc[key].strip(), key)
        self.assertIn("speeds_multi", pc["fills_rule"])

    def test_every_build_choice_is_shaped_like_the_others(self):
        ids = [b["id"] for b in self.R["build_choices"]]
        self.assertEqual(ids, sorted(ids), "build choices are out of order")
        self.assertEqual(len(ids), len(set(ids)))
        for b in self.R["build_choices"]:
            self.assertEqual(set(b), {"id", "choice", "why", "changes_it"}, b["id"])
            for k in ("choice", "why", "changes_it"):
                self.assertTrue(b[k].strip(), "%s %s is empty" % (b["id"], k))
        rule_ids = [r["id"] for r in self.R["settled"]] + [a["id"] for a in self.R["assumed"]]
        self.assertFalse(set(ids) & set(rule_ids), "a choice id collides with a ruling")



class BaselinePresent(unittest.TestCase):
    """A missing baseline must FAIL, not skip.

    Most classes here get their fixtures from setUpClass. When a fixture is absent
    unittest counts the whole class as ONE skip and still exits 0: the run shrinks
    by two thirds, the R15 regression, the eight sheet-disagrees, the four combos
    and every RulebookShape assertion all vanish, and it says OK. Measured, not
    feared — that is exactly what `mv reference/mark4-rulebook.json aside && python3
    -m unittest engine._pack_class_test` printed. A stale rulebook is the failure
    this suite exists to catch, so silence is the one outcome it may not produce.
    """

    def test_the_regression_baseline_is_on_disk(self):
        if ALLOW_MISSING:
            self.skipTest("PACK_CLASS_ALLOW_MISSING_BASELINE=1 was set deliberately")
        for path, how in ((INPUTS, "engine/freeze_sep.py"),
                          (RULEBOOK, "reference/build_mark4_rulebook.py")):
            self.assertTrue(os.path.exists(path),
                            "%s is missing, so the rows that need it were SKIPPED and this "
                            "run still exits 0. Rebuild it with %s, or set "
                            "PACK_CLASS_ALLOW_MISSING_BASELINE=1 to say you meant it."
                            % (os.path.relpath(path, ROOT), how))

    def test_the_whole_suite_is_present_when_the_baseline_is(self):
        # names the size of the hole, so a future skip cannot shrink the run quietly
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName("engine._pack_class_test")
        self.assertEqual(loader.errors, [], "the suite failed to load")
        self.assertGreaterEqual(suite.countTestCases(), 98)


class PlanningRuleRecomputes(unittest.TestCase):
    """AC05 groundwork: `planning_rule` must EXPLAIN `planning`.

    The point of the block is that gen can re-derive the speed without reading
    prose. Publishing one that does not reproduce its own number is worse than
    publishing none — gen's AC05 would then disagree with the site's lines.json
    and there would be no way to tell which was right. Verified by mutation: with
    JP 1L's factor set to 0.5 and its cap to 9999 the suite was green before this
    class existed.
    """

    @classmethod
    def setUpClass(cls):
        _S, cls.R = _load()
        cls.L = cls.R["lines"]

    def _recompute(self, line, slot, seen=(), multi=False):
        """`planning` from `planning_rule` alone — the arithmetic gen will do."""
        pr = self.L[line]["speeds_multi" if multi else "speeds"][slot]["planning_rule"]
        kind = pr["kind"]
        if kind == "none":
            return None
        if kind == "capped":
            return round(min(pr["factor"] * pr["rated"], pr["best"]))
        if kind == "rated":
            return round(pr["factor"] * pr["rated"])
        if kind == "carried":
            return round(pr["factor"] * pr["carried_from"])
        if kind == "typical":
            # the SUSTAINED median (B18): a run under three hours never sets a rate
            return round(pr["median_sustained"])
        if kind == "derived":
            nxt = tuple(pr["derived_from"])
            self.assertNotIn(nxt, seen, "%s %s: derived_from loops" % (line, slot))
            return self._recompute(nxt[0], nxt[1], seen + (nxt,))
        raise AssertionError("%s %s: unknown planning_rule kind %r" % (line, slot, kind))

    def _blocks(self):
        """Every published speed block — the plain ones AND the combo ones (B19).
        A combo block that did not explain itself would be exactly as wrong."""
        for line, spec in self.L.items():
            for table in ("speeds", "speeds_multi"):
                for slot, sp in spec[table].items():
                    yield line, slot, table == "speeds_multi", sp

    def test_every_planning_speed_equals_its_own_rule(self):
        seen = 0
        for line, slot, multi, sp in self._blocks():
            self.assertEqual(self._recompute(line, slot, multi=multi), sp["planning"],
                             "%s %s%s: planning_rule does not reproduce planning"
                             % (line, slot, " combo" if multi else ""))
            seen += 1
        self.assertEqual(seen, 18, "the rulebook no longer has 17 speed blocks and 1 combo block")

    def test_every_kind_is_one_gen_can_recompute(self):
        for line, slot, _multi, sp in self._blocks():
            self.assertIn(sp["planning_rule"]["kind"], PLANNING_KINDS, "%s %s" % (line, slot))

    def test_every_block_carries_the_same_planning_rule_keys(self):
        want = {"kind", "factor", "rated", "best", "median", "median_sustained", "runs",
                "runs_sustained", "sustained_min_minutes", "min_runs", "carried_from",
                "derived_from"}
        for line, slot, _multi, sp in self._blocks():
            self.assertEqual(set(sp["planning_rule"]), want, "%s %s" % (line, slot))

    def test_a_capped_block_really_has_the_runs_it_claims(self):
        # the cap is only allowed once there are min_runs sustained August runs;
        # below that the rule is `rated`, or there is no rate at all
        for line, slot, _multi, sp in self._blocks():
            pr = sp["planning_rule"]
            if pr["kind"] == "capped":
                self.assertGreaterEqual(pr["runs"], pr["min_runs"], "%s %s" % (line, slot))
                self.assertEqual(pr["runs"], sp["aug_runs"], "%s %s" % (line, slot))

    def test_a_typical_block_never_rests_on_a_short_run(self):
        # B18. 6 Head 3 L was [11, 820, 4183] over 265 / 217 / 71 minutes: `best`
        # already threw the 71-minute segment away, and the median it set became the
        # planning speed anyway. A typical rate now needs min_runs SUSTAINED runs.
        for line, slot, _multi, sp in self._blocks():
            pr = sp["planning_rule"]
            if pr["kind"] == "typical":
                self.assertGreaterEqual(pr["runs_sustained"], pr["min_runs"], "%s %s" % (line, slot))
                self.assertEqual(sp["planning"], pr["median_sustained"], "%s %s" % (line, slot))

    def test_the_kept_spread_is_published_and_brackets_its_own_middle(self):
        # a median of 820 over [11, 820, 4183] reads like a measurement; the range
        # column is what stops it looking like one on /assumptions
        for line, slot, _multi, sp in self._blocks():
            where = "%s %s" % (line, slot)
            if not sp["aug_runs"]:
                self.assertIsNone(sp["aug_min"], where)
                self.assertIsNone(sp["aug_max"], where)
                continue
            self.assertLessEqual(sp["aug_min"], sp["aug_median"], where)
            self.assertLessEqual(sp["aug_median"], sp["aug_max"], where)
            self.assertLessEqual(sp["aug_runs_sustained"], sp["aug_runs"], where)
            if sp["aug_best"] is not None:
                self.assertLessEqual(sp["aug_best"], sp["aug_max"], where)

    def test_a_derived_block_points_at_a_block_that_has_a_number(self):
        for line, spec in self.L.items():
            for slot, sp in spec["speeds"].items():
                pr = sp["planning_rule"]
                if pr["kind"] != "derived":
                    continue
                dl, ds = pr["derived_from"]
                self.assertIn(dl, self.L, "%s %s derives from an unknown line" % (line, slot))
                self.assertIn(ds, self.L[dl]["speeds"], "%s %s derives from an unknown slot" % (line, slot))
                self.assertIsNotNone(self.L[dl]["speeds"][ds]["planning"],
                                     "%s %s derives from a rate-less block" % (line, slot))


class LegacySlotCopies(unittest.TestCase):
    """sheet_slot() against the REAL source of the three live copies.

    RulebookShape's sibling test compares sheet_slot() to a rule re-typed inside
    this file, so editing engine/august_sim.py's slot() cannot fail it. This one
    reads the functions out of the files themselves with ast, so it can. Verified
    by mutation: dropping the 'KGS' half of the rule from august_sim.py left the
    suite green before this class existed, while the two rules genuinely disagreed
    (15L vs TIN on a 15 KGS tin).
    """

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()
        cls.impls = {rel: cls._extract(rel, fn) for rel, fn in LEGACY_COPIES}

    @staticmethod
    def _extract(rel, fname):
        """Compile just one function out of a file — no module import, so nothing
        the file does at import time runs."""
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            src = fh.read()
        tree, ns = ast.parse(src), {}
        for node in tree.body:                       # the module-level float helper
            if isinstance(node, ast.FunctionDef) and node.name == "f":
                exec(compile(ast.Module([node], []), rel, "exec"), ns)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == fname:
                exec(compile(ast.Module([node], []), rel, "exec"), ns)
                return ns[fname]
        raise AssertionError("%s has no %s()" % (rel, fname))

    def test_sheet_slot_matches_every_live_copy_on_every_plan_row(self):
        for p in self.S["plan"]:
            mine = sheet_slot(p["sku"], p["pack_type"], p["litres_per_piece"])
            row = {"sku": p["sku"], "pack_type": p["pack_type"],
                   "litres_per_piece": p["litres_per_piece"]}
            for rel, fn in self.impls.items():
                self.assertEqual(fn(row), mine, "%s: %s disagrees with pack_class.sheet_slot()"
                                 % (p["code"], rel))

    def test_sheet_slot_matches_every_live_copy_on_rows_the_plan_cannot_reach(self):
        # the plan has no KGS row that is not also pack_type TIN, so the name half
        # of the rule is unexercised by the sheet — this is where it is checked
        for sku, pt, litres in [("SOYABEAN OIL 15 KGS", "PET", 16.4835),
                                ("SOYABEAN OIL 15 LTR", "PET", 15.0),
                                ("REFINED OIL 1 LTR POUCH 12 PCS", "PET", 1.0),
                                ("SOME OIL 200 LTR", "DRUM", 200.0),
                                ("SOME OIL 1 LTR", "", 1.0)]:
            row = {"sku": sku, "pack_type": pt, "litres_per_piece": litres}
            mine = sheet_slot(sku, pt, litres)
            for rel, fn in self.impls.items():
                self.assertEqual(fn(row), mine, "%s on %r" % (rel, sku))

    def test_the_published_sheet_slot_is_that_same_rule(self):
        plan = {p["code"]: p for p in self.S["plan"]}
        for code, v in self.R["sku_pack"].items():
            p = plan[code]
            self.assertEqual(v["sheet_slot"],
                             sheet_slot(p["sku"], p["pack_type"], p["litres_per_piece"]), code)


class ContainerQuantityIsAPieceCount(unittest.TestCase):
    """A BOM quantity is only a COUNT of containers when something says so (B17).

    Three of the 84 recipes name their container in KGS (a film roll: 0.0083 kg of
    pouch stock per litre). Those quantities are tiny, so nothing was misread — but
    the rule read the number and never the unit, and a container child in KGS at 1.5
    or more went through silently: the row was planned as a multipack, its
    litres_per_fill divided, and `container_litres` disagreed with it by exactly that
    factor with nothing flagging the gap. The fix reads the unit AND checks the
    arithmetic against the container's own printed size. A re-freeze that widens
    `items` (A18) is where this lands.
    """

    PIECE_UOMS = {"PCS", "NOS", "EA", ""}

    @classmethod
    def setUpClass(cls):
        cls.S, cls.R = _load()
        cls.plan = {p["code"]: p for p in cls.S["plan"]}
        cls.bom, cls.items = cls.S["bom"], cls.S["items"]

    def test_no_container_measured_by_weight_is_read_as_a_multipack(self):
        checked = 0
        for code, p in self.plan.items():
            c, _n, _per = container_of(code, self.bom, self.items)
            if c is None:
                continue
            uom = str((self.items.get(c, {}) or {}).get("uom") or "").upper()
            if uom in self.PIECE_UOMS:
                continue
            checked += 1
            got = pack_class(code, self.bom, self.items, p["litres_per_piece"], p["pack_type"])
            self.assertEqual(got["fills_per_piece"], 1,
                             "%s: container %s is measured in %s, so its quantity is not a "
                             "count of containers and must not become fills_per_piece"
                             % (code, c, uom))
            self.assertEqual(got["litres_per_fill"], p["litres_per_piece"], code)
        self.assertEqual(checked, 3, "the three KGS-measured pouch films are the known set")

    def test_a_weight_measured_container_is_one_container(self):
        # 15 kg of steel is one 200 L drum, never fifteen of them.
        items = {"PM_X": {"name": "MS COATED DRUM 200 LTR", "uom": "KGS"}}
        got = pack_class("FGX", {"FGX": [["PM_X", 15.0]]}, items, 200.0, "DRUM")
        self.assertEqual(got["fills_per_piece"], 1)
        self.assertEqual(got["litres_per_fill"], 200.0)
        self.assertEqual(got["container_litres"], 200.0)
        self.assertFalse(got["container_disagrees"])
        self.assertIn("KGS", got["fills_basis"])

    def test_a_quantity_the_container_size_contradicts_is_not_a_count(self):
        # the same guard without a usable unit: 3 x "1 LTR" cannot make a 1 L piece,
        # so the 3 is an amount of something, not three bottles
        items = {"PM_X": {"name": "PET BOTTLE 1 LTR 40 GMS", "uom": "ROL"}}
        got = pack_class("FGX", {"FGX": [["PM_X", 3.0]]}, items, 1.0, "PET")
        self.assertEqual(got["fills_per_piece"], 1)
        self.assertEqual((got["slot"], got["family"]), ("1L", "40G"))
        self.assertIn("not a container count", got["fills_basis"])

    def test_a_quantity_the_container_size_confirms_is_a_count(self):
        items = {"PM_X": {"name": "PET BOTTLE 1 LTR 40 GMS", "uom": "ROL"}}
        got = pack_class("FGX", {"FGX": [["PM_X", 3.0]]}, items, 3.0, "PET")
        self.assertEqual(got["fills_per_piece"], 3)
        self.assertEqual((got["slot"], got["family"]), ("1L", "40G"))
        self.assertEqual(got["litres_per_fill"], 1.0)

    def test_an_unsized_combo_keeps_its_whole_bottle(self):
        # the fallback path B15/A18 says the freeze will exercise: with no size on
        # the sheet, the container's printed size IS one fill and must not be
        # divided again. Halving it here gave a 1 L 40 g bottle as a 500 ml SMALL —
        # and SMALL is JP's first choice, the one bottle A14 says never runs there.
        items = {"PM0000194": {"name": "PET BOTTLE 1 LTR 40 GMS", "uom": "PCS"}}
        got = pack_class("FGX", {"FGX": [["RM", 2.0], ["PM0000194", 2.0]]}, items, None, "PET")
        self.assertEqual((got["slot"], got["family"]), ("1L", "40G"))
        self.assertEqual(got["fills_per_piece"], 2)
        self.assertEqual(got["litres_per_fill"], got["container_litres"])
        self.assertFalse(got["container_disagrees"])

    def test_a_fill_that_does_not_match_its_container_is_flagged(self):
        # nothing on the plan sheet sets it; the field exists so the freeze cannot
        # publish a fill and a printed size that disagree without saying so
        items = {"PM_X": {"name": "PET BOTTLE 1 LTR 40 GMS", "uom": "PCS"}}
        got = pack_class("FGX", {"FGX": [["PM_X", 1.0]]}, items, 5.0, "PET")
        self.assertTrue(got["container_disagrees"])
        self.assertEqual(got["container_ratio"], 5.0)
        for code, p in self.plan.items():
            self.assertFalse(pack_class(code, self.bom, self.items,
                                        p["litres_per_piece"], p["pack_type"])["container_disagrees"],
                             "%s: fill and printed container size disagree" % code)

    def test_every_multipack_row_is_counted_in_pieces(self):
        for code in COMBOS:
            c, _n, _per = container_of(code, self.bom, self.items)
            uom = str((self.items.get(c, {}) or {}).get("uom") or "").upper()
            self.assertIn(uom, self.PIECE_UOMS, "%s: a combo counted in %s" % (code, uom))

    def test_every_plan_row_says_why_it_fills_as_often_as_it_does(self):
        for code, p in self.plan.items():
            got = pack_class(code, self.bom, self.items, p["litres_per_piece"], p["pack_type"])
            self.assertTrue(str(got["fills_basis"]).strip(), code)
            if got["fills_per_piece"] == 1:
                self.assertNotIn(code, COMBOS, code)


class SpeedEvidence(unittest.TestCase):
    """The published August evidence, re-derived from the raw run log.

    Every other test here reads what the builder wrote. This one re-buckets
    out/august-actuals-SCORING.csv from scratch — the usability filter, the clock
    guard, the combo split, the sustained window — and compares the counts and the
    spread it gets to the ones the rulebook publishes. A speed table can be
    perfectly self-consistent and still describe runs that never happened; this is
    the only class that goes back to the evidence.
    """

    SLOT_LITRES = {"1L": 1.0, "2L": 2.0, "3L": 3.0, "4L": 4.0, "5L": 5.0, "15L": 15.0,
                   "POUCH": 1.0, "DRUM": 200.0}
    SUSTAINED_MIN = 180
    IMPLAUSIBLE = 1.2

    @classmethod
    def setUpClass(cls):
        import csv
        import io
        if not os.path.exists(RUNS_CSV):
            raise unittest.SkipTest("out/august-actuals-SCORING.csv is absent")
        _S, cls.R = _load()
        with open(RUNS_CSV, encoding="utf-8") as fh:
            text = fh.read().splitlines()
        rows = csv.DictReader(io.StringIO("\n".join(text[1:])))
        cls.runs = [r for r in rows if r.get("section") == "APP_RUN"]
        cls.pack = cls.R["sku_pack"]

    def _f(self, v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def _ceiling(self, line):
        """The most litres an hour any RATED slot on this line can pour."""
        best = [sp["rated"] * self.SLOT_LITRES[slot]
                for slot, sp in self.R["lines"][line]["speeds"].items()
                if sp["rated"] and self.SLOT_LITRES.get(slot)]
        return max(best) if best else None

    def _by_name(self, r):
        """The slot of a run whose item code is not on the plan sheet — nine of the
        usable runs. Re-derived here rather than imported, so the two have to agree."""
        import re
        n = r["product"].upper()
        lit = self._f(r["pack_litres"])
        if "POUCH" in n:
            return "POUCH"
        if "KGS" in n or "TIN" in n or re.search(r"15\s*L", n):
            if lit >= 12 or "KGS" in n or re.search(r"15\s*L", n):
                return "15L"
            return "3L" if lit <= 3.05 else "5L"
        if "200 L" in n:
            return "DRUM"
        return slot_by_litres(lit, "PET")

    def _buckets(self):
        out = {}
        for r in self.runs:
            mins, pcs = self._f(r["segment_running_minutes"]), self._f(r["pieces"])
            if mins < 60 or pcs <= 0 or mins > 20 * 60:
                continue
            v = self.pack.get(r.get("item_code"))
            slot, fills = (v["slot"], v["fills_per_piece"]) if (v and v["slot"]) else (self._by_name(r), 1)
            if slot is None:
                continue
            out.setdefault((r["line"], slot, fills > 1), []).append(
                (pcs * fills / (mins / 60.0), mins))
        return out

    def _kept(self, line, slot, raw):
        sp = self.R["lines"][line]["speeds"].get(slot)
        rated = sp and sp["rated"]
        if rated:
            return [(x, m) for x, m in raw if x <= self.IMPLAUSIBLE * rated]
        ceiling, lit = self._ceiling(line), self.SLOT_LITRES.get(slot)
        if ceiling and lit:
            return [(x, m) for x, m in raw if x * lit <= self.IMPLAUSIBLE * ceiling]
        return list(raw)

    def test_every_published_block_matches_the_run_log(self):
        seen = 0
        for (line, slot, multi), raw in self._buckets().items():
            if line not in self.R["lines"]:
                continue
            table = self.R["lines"][line]["speeds_multi" if multi else "speeds"]
            self.assertIn(slot, table, "%s %s%s ran in August and has no block"
                          % (line, slot, " combo" if multi else ""))
            sp, kept = table[slot], self._kept(line, slot, raw)
            o = [x for x, _m in kept]
            sus = [x for x, m in kept if m >= self.SUSTAINED_MIN]
            where = "%s %s%s" % (line, slot, " combo" if multi else "")
            self.assertEqual(sp["aug_runs"], len(o), where)
            self.assertEqual(sp["aug_runs_sustained"], len(sus), where)
            self.assertEqual(sp["aug_runs_discarded"], len(raw) - len(kept), where)
            self.assertEqual(sp["aug_min"], round(min(o)) if o else None, where)
            self.assertEqual(sp["aug_max"], round(max(o)) if o else None, where)
            self.assertEqual(sp["aug_best"], round(max(sus)) if sus else
                             (round(max(o)) if o else None), where)
            seen += 1
        self.assertGreaterEqual(seen, 10, "the run log stopped reaching the speed table")

    def test_no_kept_run_pours_more_litres_than_its_line_can(self):
        # B18 stated as an outcome rather than as a mechanism: whatever the guard
        # is, nothing may survive it that beats the line's own best rated slot by
        # half again in LITRES an hour.
        for line, spec in self.R["lines"].items():
            ceiling = self._ceiling(line)
            if not ceiling:
                continue
            for table in ("speeds", "speeds_multi"):
                for slot, sp in spec[table].items():
                    lit = self.SLOT_LITRES.get(slot)
                    if not (lit and sp["aug_max"]):
                        continue
                    self.assertLessEqual(sp["aug_max"] * lit, self.IMPLAUSIBLE * ceiling + 1,
                                         "%s %s: a kept run pours %s L/hr on a line whose best "
                                         "rated slot pours %s"
                                         % (line, slot, round(sp["aug_max"] * lit), round(ceiling)))

    def test_the_combo_runs_are_the_combo_skus_and_nothing_else(self):
        # two of the four combo SKUs ran in August, both on Clear Pack. If a third
        # appears, or one turns up on another line, B19's "no combo rate elsewhere"
        # has to be revisited rather than quietly widened.
        multi = {(r["line"], r["item_code"]) for r in self.runs
                 if (self.pack.get(r.get("item_code")) or {}).get("fills_per_piece", 1) > 1}
        self.assertLessEqual({code for _ln, code in multi}, set(COMBOS))
        self.assertEqual({code for _ln, code in multi}, {"FG0000091", "FG0000429"})
        self.assertEqual({ln for ln, _code in multi}, {"Clear Pack"})


class SpeedRuleBranches(unittest.TestCase):
    """The speed rule on runs the plant has not produced.

    No line is on the `typical` branch today — 6 Head 3 L was, and the clock guard
    took it off — so nothing in the live data exercises it, and a change to it
    passes every other test here. Proved by mutation: putting the short runs back
    into the typical median left the whole suite green. So this class imports the
    builder and feeds speed_block() buckets of its own.
    """

    LINE, SLOT = "6 Head", "4L"        # a real line, a slot the app never rated
    CEILING_L = 3000.0                 # its best rated slot: 5 L at 600/hr

    @classmethod
    def setUpClass(cls):
        import sys
        if not os.path.exists(INPUTS):
            raise unittest.SkipTest("sim/sep-inputs.json is absent")
        sys.path.insert(0, os.path.join(ROOT, "reference"))
        try:
            import build_mark4_rulebook as B
        except Exception as exc:                     # a builder that will not import
            raise unittest.SkipTest("reference/build_mark4_rulebook.py: %s" % exc)
        cls.B = B

    def _block(self, runs):
        key = (self.LINE, self.SLOT, False)
        self.B.obs_raw[key] = list(runs)
        self.B._speed_cache.pop(key, None)
        try:
            return self.B.speed_block(self.LINE, self.SLOT)
        finally:
            self.B.obs_raw.pop(key, None)
            self.B._speed_cache.pop(key, None)

    def test_a_typical_rate_needs_three_runs_of_three_hours(self):
        # four usable runs, only two of them sustained: not a typical rate
        blk = self._block([(500, 200), (600, 200), (700, 100), (800, 100)])
        self.assertEqual(blk["aug_runs"], 4)
        self.assertEqual(blk["aug_runs_sustained"], 2)
        self.assertIsNone(blk["planning"],
                          "planned from a median that includes runs under three hours")
        self.assertEqual(blk["planning_rule"]["kind"], "none")

    def test_a_typical_rate_is_the_median_of_the_sustained_runs(self):
        blk = self._block([(500, 200), (600, 200), (700, 200), (800, 200)])
        self.assertEqual(blk["planning_rule"]["kind"], "typical")
        self.assertEqual(blk["planning"], 650)
        self.assertEqual(blk["planning"], blk["aug_median_sustained"])

    def test_the_median_ignores_the_short_runs_even_when_they_would_move_it(self):
        # the short runs are both at the bottom: including them halves the answer
        blk = self._block([(500, 200), (600, 200), (700, 200), (10, 100), (20, 100)])
        self.assertEqual(blk["planning"], 600)
        self.assertEqual(blk["aug_median"], 500, "the all-runs median is still published")
        self.assertEqual(blk["aug_min"], 10)

    def test_a_clock_error_is_discarded_on_a_slot_the_app_never_rated(self):
        # 900 x 4 L = 3,600 L/hr is the last speed this line could pour; 1,200 is not
        blk = self._block([(500, 200), (600, 200), (700, 200), (1200, 200)])
        self.assertEqual(blk["aug_runs_discarded"], 1)
        self.assertEqual(blk["aug_runs"], 3)
        self.assertEqual(blk["aug_max"], 700)
        self.assertIn("litres/hour", blk["planning_basis"])
        self.assertLessEqual(blk["aug_max"] * 4, 1.2 * self.CEILING_L)

    def test_a_combo_rate_is_never_carried_or_derived(self):
        # Clear Pack 4L is CARRIED and Tin Head 3L is DERIVED; neither fallback may
        # invent a rate for a pack the line has never run as a set (B19)
        for line, slot in (("Clear Pack", "4L"), ("Tin Head", "3L")):
            self.B._speed_cache.pop((line, slot, True), None)
            blk = self.B.speed_block(line, slot, True)
            self.B._speed_cache.pop((line, slot, True), None)
            self.assertIsNone(blk["planning"], "%s %s combo" % (line, slot))
            self.assertEqual(blk["planning_rule"]["kind"], "none", "%s %s combo" % (line, slot))


class AugustCalibrationIsPinned(unittest.TestCase):
    """The site's one trust sentence may not come from a file the engine rewrites.

    Until 2026-09-06 gen_live.py read it out of sim/summary.json — a working file
    that a bare `python3 engine/august_sim.py` overwrites — and it had drifted to
    2,122,639 L / 0.16% while the engine in the tree made 2,124,866 L / 0.27%.
    Nothing failed because nothing looked. It is an artefact now, stamped with the
    sha256 of everything it depends on.
    """

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(CALIBRATION):
            if ALLOW_MISSING:
                raise unittest.SkipTest("PACK_CLASS_ALLOW_MISSING_BASELINE=1")
            raise unittest.SkipTest("reference/august-calibration.json is absent")
        with open(CALIBRATION, encoding="utf-8") as fh:
            cls.C = json.load(fh)

    def test_it_carries_its_own_arithmetic(self):
        made, actual = self.C["sim_made_l"], self.C["actual_made_l"]
        self.assertGreater(actual, 0)
        self.assertEqual(self.C["delta_pct"], round(abs(made - actual) / actual * 100, 2))
        self.assertLess(self.C["delta_pct"], 1.0, "the August backtest has drifted past 1%")

    def test_it_still_matches_the_engine_in_this_tree(self):
        import hashlib
        moved = []
        for rel, was in self.C["depends_on"].items():
            path = os.path.join(ROOT, rel)
            self.assertTrue(os.path.exists(path), rel)
            with open(path, "rb") as fh:
                if hashlib.sha256(fh.read()).hexdigest() != was:
                    moved.append(rel)
        self.assertEqual(moved, [], "changed since the backtest was measured: %s — re-run "
                                    "`python3 engine/calibrate_august.py` in the same commit"
                                    % ", ".join(moved))

    def test_it_depends_on_the_engine_and_the_august_inputs(self):
        deps = set(self.C["depends_on"])
        self.assertIn("engine/august_sim.py", deps)
        self.assertIn("sim/sim-inputs.json", deps)

    def test_gen_reads_the_artefact_and_not_the_working_summary(self):
        with open(os.path.join(ROOT, "live/gen_live.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("august-calibration.json", src)
        self.assertNotIn('load(os.path.join(SIM, "summary.json"))', src,
                         "gen_live.py is reading the August claim out of a working file again")

    def test_the_offline_fixtures_carry_the_same_measurement(self):
        # fixture mode is what `npm run build` renders; a fixture holding the old
        # unreproducible number would publish exactly what this fix removed
        for rel, key in (("site-live/fixtures/plan/honesty.json", "august_calibration"),
                         ("site-live/fixtures/plan/overview.json", "august")):
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                got = json.load(fh)[key]
            self.assertEqual(got["sim_made_l"], self.C["sim_made_l"], rel)
            self.assertEqual(got["delta_pct"], self.C["delta_pct"], rel)


class TheFiltersNobodyPublishes(unittest.TestCase):
    """The two run filters that never reach the page — and the proof they cost nothing.

    Before the clock guard runs at all, the builder throws away every logged run
    under an hour and every one over twenty (`mins < 60 or mins > 20 * 60`).
    Neither reaches the JSON: `aug_runs_discarded` counts the clock guard alone, so
    a reader of lines.json sees Clear Pack 1 L as "6 runs, 0 discarded" where the
    log holds eight. The long window is the one with weight — thirteen runs of 20
    to 49 hours are dropped, every one of them a PLAUSIBLE rate and every one of
    them SLOW, so the filter can only push a published speed UP.

    That is a reporting gap and not a wrong number, and these two tests are what
    holds it there. Whatever the window is, it may never be the reason a speed is
    what it is: if someone widens it and a planning speed could move, this fails
    and the window has to be published instead of assumed harmless.
    """

    SLOT_LITRES = SpeedEvidence.SLOT_LITRES
    IMPLAUSIBLE = 1.2
    WINDOW_MIN, WINDOW_MAX = 60, 20 * 60

    @classmethod
    def setUpClass(cls):
        import csv
        import io
        if not os.path.exists(RUNS_CSV):
            raise unittest.SkipTest("out/august-actuals-SCORING.csv is absent")
        _S, cls.R = _load()
        with open(RUNS_CSV, encoding="utf-8") as fh:
            rows = csv.DictReader(io.StringIO("\n".join(fh.read().splitlines()[1:])))
            cls.runs = [r for r in rows if r.get("section") == "APP_RUN"]
        cls.pack = cls.R["sku_pack"]

    def _f(self, v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def _ceiling(self, line):
        best = [sp["rated"] * self.SLOT_LITRES[slot]
                for slot, sp in self.R["lines"][line]["speeds"].items()
                if sp["rated"] and self.SLOT_LITRES.get(slot)]
        return max(best) if best else None

    def _plausible(self, line, slot, multi, rate):
        """The clock guard, applied to a run the length window already threw out."""
        table = self.R["lines"][line]["speeds_multi" if multi else "speeds"]
        sp = table.get(slot) or self.R["lines"][line]["speeds"].get(slot)
        rated = sp and sp["rated"]
        if rated:
            return rate <= self.IMPLAUSIBLE * rated
        ceiling, lit = self._ceiling(line), self.SLOT_LITRES.get(slot)
        if ceiling and lit:
            return rate * lit <= self.IMPLAUSIBLE * ceiling
        return True

    def _hidden(self):
        """(line, slot, multi, minutes, rate) for every run the length window hides
        and the clock guard would have KEPT — the runs whose absence is invisible."""
        out = []
        for r in self.runs:
            mins, pcs = self._f(r["segment_running_minutes"]), self._f(r["pieces"])
            if pcs <= 0 or mins <= 0 or self.WINDOW_MIN <= mins <= self.WINDOW_MAX:
                continue
            v = self.pack.get(r.get("item_code"))
            if not (v and v["slot"]):
                continue                       # a name-derived slot is SpeedEvidence's job
            line, slot, fills = r["line"], v["slot"], v["fills_per_piece"]
            if line not in self.R["lines"]:
                continue
            rate = pcs * fills / (mins / 60.0)
            if self._plausible(line, slot, fills > 1, rate):
                out.append((line, slot, fills > 1, mins, rate))
        return out

    def test_no_run_the_length_window_hides_could_raise_a_speed(self):
        # `planning` is min(80% x rated, best) or 80% x rated, and `best` only ever
        # goes up. A hidden run faster than the published best is a speed the plant
        # reached and the plan does not offer it.
        hidden = self._hidden()
        self.assertTrue(hidden, "no run is outside the window any more — retire this test "
                                "or the window, but do not leave both in place")
        for line, slot, multi, mins, rate in hidden:
            sp = self.R["lines"][line]["speeds_multi" if multi else "speeds"][slot]
            best = sp["aug_best"]
            if best is None:
                continue
            self.assertLessEqual(round(rate), best,
                                 "%s %s: a %d-minute run at %d/hr is hidden by the length "
                                 "window and beats the published best of %d — the window is "
                                 "setting the speed, so publish it"
                                 % (line, slot, round(mins), round(rate), best))

    def test_the_length_window_never_decides_whether_a_block_has_enough_runs(self):
        # the cap and the typical branch both turn on `min_runs`. If the hidden runs
        # would carry a block over that line, the window is choosing the branch.
        extra = {}
        for line, slot, multi, _mins, _rate in self._hidden():
            extra[(line, slot, multi)] = extra.get((line, slot, multi), 0) + 1
        for (line, slot, multi), n in sorted(extra.items()):
            sp = self.R["lines"][line]["speeds_multi" if multi else "speeds"][slot]
            pr = sp["planning_rule"]
            crossed = sp["aug_runs"] < pr["min_runs"] <= sp["aug_runs"] + n
            self.assertFalse(crossed,
                             "%s %s has %d usable runs and %d more hidden by the length "
                             "window — the window, not the evidence, is why this block is "
                             "%r" % (line, slot, sp["aug_runs"], n, pr["kind"]))


class NothingIsStranded(unittest.TestCase):
    """B16 and B18 took two planning speeds away. Nothing checked what that stranded.

    Prose says "nothing is stranded either way: 2 L keeps the 10 Head and the
    6 Head, 3 L keeps the 10 Head and the Tin Head". That sentence is true today and
    is not a test. A rate removed from the last line that can run a pack is a
    product with nowhere to go, and the rulebook would still be internally perfect.
    """

    @classmethod
    def setUpClass(cls):
        _S, cls.R = _load()
        cls.L = cls.R["lines"]

    def _lines_for(self, slot, family, multi):
        """[(line, preference, planning)] — every line whose eligibility table names
        this pack, with the speed it would be planned at."""
        out = []
        for line, spec in self.L.items():
            fams = (spec["slots"] or {}).get(slot)
            if not fams:
                continue
            pref = fams.get(family, fams.get("ANY"))
            if pref is None:
                continue
            table = spec["speeds_multi"] if multi else spec["speeds"]
            blk = table.get(slot)
            out.append((line, pref, blk["planning"] if blk else None))
        return sorted(out, key=lambda x: (x[1], x[0]))

    def test_every_plan_row_has_a_line_that_has_a_speed(self):
        drums = set(self.R["drums"]["skus"])
        for code, v in sorted(self.R["sku_pack"].items()):
            if code in drums or v["slot"] == "DRUM":
                continue                       # R14: filled by hand, never scheduled
            got = self._lines_for(v["slot"], v["family"], v["fills_per_piece"] > 1)
            self.assertTrue(got, "%s %s/%s: no line's eligibility table names it"
                            % (code, v["slot"], v["family"]))
            self.assertTrue(any(p is not None for _ln, _pref, p in got),
                            "%s %s/%s can only go to %s, and not one of them has a "
                            "planning speed" % (code, v["slot"], v["family"],
                                                [ln for ln, _p, _s in got]))

    def test_a_combo_row_has_a_line_with_a_COMBO_speed(self):
        # B19 forbids carrying or deriving a combo rate, so a combo with no
        # speeds_multi block anywhere is unschedulable rather than slow.
        combos = [c for c, v in self.R["sku_pack"].items() if v["fills_per_piece"] > 1]
        self.assertEqual(sorted(combos), sorted(COMBOS))
        for code in sorted(combos):
            v = self.R["sku_pack"][code]
            got = self._lines_for(v["slot"], v["family"], True)
            self.assertTrue(any(p is not None for _ln, _pref, p in got),
                            "%s is a combo set and no line publishes a combo rate for "
                            "%s/%s" % (code, v["slot"], v["family"]))

    def test_a_family_no_line_names_falls_through_to_the_open_ANY_rule(self):
        # UNKNOWN, 1L-OTHER and the "<n>G" labels are what an unrecognised bottle
        # becomes. No line NAMES them — but the 6 Head's 1 L slot is `{"ANY": 3}`, so
        # a bottle nobody has ruled on is still schedulable there at preference 3.
        # That is worth knowing rather than assuming: B15 makes an unknown SIZE
        # unplaceable; an unknown BOTTLE of a known size is not. Pinned here so the
        # day someone decides ANY should mean "any bottle we have ruled on", this
        # fails instead of quietly moving a product.
        for family in ("UNKNOWN", "1L-OTHER", "33G"):
            self.assertEqual(self._lines_for("1L", family, False),
                             self._lines_for("1L", "ANY", False),
                             "%s is only ever as eligible as an explicit ANY rule" % family)
        self.assertEqual([ln for ln, _p, _s in self._lines_for("1L", "UNKNOWN", False)],
                         ["6 Head"], "only the 6 Head's 1 L slot is an open ANY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
