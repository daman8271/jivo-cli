#!/usr/bin/env python3
"""Unit tests for the MARK 4 half of live/gen_live.py.

    cd jolly && python3 -m unittest live._gen_mark4_test -v

NO NETWORK, no login, and nothing is written: every cross-check in gen_live.py that
Mark 4 added is a small function taking the `check` collector, so each one is driven
here with a hand-built dict that PASSES and one that FAILS. A check that cannot fail
is not a check, and that is the half these tests are really for.

The cases are the mistakes this file has already made or was one edit away from:
  * "no machine can fill it" read off a slot-key guess — the Mark 3 question that
    called four tins unfillable while the planner was filling them (AC03)
  * a 15 L speed invented as the 5 L speed divided by three (AC02)
  * a basis word the site cannot draw (AC05)
  * a tin on Clear Pack, a pouch off the pouch machine, a drum on any machine at all
    (AC01, AC02, AC03)
  * a 26 g bottle on Clear Pack or a 40 g on JP (AC07)
  * a line over ten hours that is not the night line, and production on a Sunday (AC04)
  * "trucks left today" creeping back onto the front page (AC09)
  * an assumptions page missing an id or a question (AC10)
  * the questions file: a question is ANSWERED the moment a line under it starts
    `Answer:`, because that is the whole convention Gurvinder was given

The last class checks the real published plan when there is one on this box, so the
synthetic tests above cannot drift away from what the chain actually writes.
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_JOLLY = os.path.dirname(_HERE)
if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)

from live import gen_live as gl  # noqa: E402

PLAN_DIR = os.path.join(_HERE, "state", "plan")
RULEBOOK = os.path.join(_JOLLY, "reference", "mark4-rulebook.json")


# --------------------------------------------------------------- fixtures ---
def run_check(fn, *args, **kwargs):
    """Drive one check function and hand back the collector. A failing check prints to
    stderr by design; swallow it so a passing run does not read like a failing one."""
    check = gl.Checks()
    with contextlib.redirect_stderr(io.StringIO()):
        fn(check, *args, **kwargs)
    return check


def failed(check):
    return [name for name, ok, _detail in check.rows if not ok]


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# A cut-down rulebook in the real shape: five machines, the eligibility table, the
# drums, and enough sku_pack to place a run.
def a_rulebook(**over):
    rb = {
        "version": "mark4-test", "written": "2026-09-06", "owner": "test",
        "lines": {
            "Tin Head": {"slots": {"15L": {"TIN": 1}, "5L": {"TIN": 2}}},
            "6 Head": {"slots": {"5L": {"HDPE": 1, "TIN": 1}, "3L": {"HDPE": 1, "TIN": 2}}},
            "Clear Pack": {"slots": {"1L": {"40G": 1, "52G": 2}, "5L": {"HDPE": 1}}},
            "JP Machine": {"slots": {"1L": {"26G": 1, "SMALL": 1, "52G": 3}}},
            "Pouch Machine": {"slots": {"POUCH": {"ANY": 1}}},
        },
        "pack_class": {"slots": ["1L", "2L", "3L", "4L", "5L", "15L", "POUCH", "DRUM"]},
        "drums": {"skus": ["FG-DRUM"], "display": "filled by hand, not scheduled here"},
        "demand": {"months": 3},
        "money": {"target_inr_per_day": 25000000, "floor_inr_per_day": 20000000},
        "sku_pack": {
            "FG-TIN15": {"sku": "SOYABEAN 15 LTR", "slot": "15L", "family": "TIN",
                         "sheet_pack_type": "PET", "container_name": "TIN 15 LTR",
                         "sheet_disagrees": True, "fills_per_piece": 1},
            "FG-JP1": {"sku": "MUSTARD 1 LTR", "slot": "1L", "family": "26G",
                       "sheet_disagrees": False, "fills_per_piece": 1},
            "FG-CP5": {"sku": "GROUNDNUT 5 LTR", "slot": "5L", "family": "HDPE",
                       "sheet_disagrees": False, "fills_per_piece": 1},
            "FG-DRUM": {"sku": "SOME OIL 200 LTR", "slot": "DRUM", "family": "DRUM",
                        "sheet_disagrees": False, "fills_per_piece": 1},
        },
        "settled": [{"id": "R01", "rule": "factory truth is the factory app", "source": "meeting"}],
        "assumed": [{"id": "A01", "assumption": "a speed rule", "why": "because",
                     "changes_it": "a number from the plant"}],
        "build_choices": [{"id": "B01", "choice": "a choice", "why": "because",
                           "changes_it": "a ruling"}],
        # the real shape: AC06 names which products the sheet gets wrong, and
        # check_pack_class reads the count and the codes back out of this line
        "acceptance_checks": [
            "AC01 no tin off the tin machine",
            "AC06 Pack class of every plan SKU equals the BOM container (R15): "
            "the 0 '15 LTR' rows + FG-TIN15 are TIN.",
        ],
    }
    rb.update(over)
    return rb


# the freeze's `lines`: the planning speed per line-slot the engine really used. 6 Head
# 3 L is deliberately absent — the rulebook allows it and nobody has a speed (B16).
LINES = {"Tin Head": {"15L": 192.0, "5L": 192.0},
         "6 Head": {"5L": 480.0},
         "Clear Pack": {"1L": 2927.0, "5L": 1068.0},
         "JP Machine": {"1L": 2910.0},
         "Pouch Machine": {"POUCH": 1982.0}}
MULTI = {"Clear Pack": {"1L": 1277.0}}


def a_run(**over):
    run = {"line": "Tin Head", "code": "FG-TIN15", "sku": "SOYABEAN 15 LTR",
           "slot": "15L", "family": "TIN", "pref": 1, "pieces": 100, "litres": 1500,
           "hours": 0.5, "value": 100000, "po_backed": True, "night": False}
    run.update(over)
    return run


def a_day(**over):
    day = {"date": "2026-09-07", "weekday": "Monday", "working": True,
           "made_litres": 1500, "runs": [a_run()], "blocked": [],
           "line_hours": {"Tin Head": 9.0, "6 Head": 10.0},
           "line_hours_max": {"Tin Head": 10.0, "6 Head": 20.0},
           "night_line": {"line": "6 Head", "reason": "the most ordered litres still unmade"}}
    day.update(over)
    return day


QUESTIONS_MD = """# Questions

Some preamble nobody parses.

*To answer one, add a line under it starting `Answer:` and push this file.*

<!-- questions: 3 -->

## Already settled from the meeting

- a bullet that is not a question

## Machines

**1. Speeds — what number should the plan use?**
You said 80% of capacity.

**2. The 21-gram bottle.** Which one did you mean?
The stock list has three.
Answer: the 26 g one.

## Demand

**3. GT/MT average** (10:37). Three months or six?
"""


# ------------------------------------------------------- the questions file --
class QuestionsParser(unittest.TestCase):
    def test_it_reads_the_number_the_section_and_the_title(self):
        qs = gl.parse_questions(QUESTIONS_MD)
        self.assertEqual([q["number"] for q in qs], [1, 2, 3])
        self.assertEqual([q["section"] for q in qs], ["Machines", "Machines", "Demand"])
        self.assertEqual(qs[1]["title"], "The 21-gram bottle")
        self.assertIn("Which one did you mean?", qs[1]["question"])

    def test_a_bullet_in_the_settled_section_is_not_a_question(self):
        self.assertEqual(len(gl.parse_questions(QUESTIONS_MD)), 3)

    def test_an_answer_line_is_what_makes_it_answered(self):
        qs = {q["number"]: q for q in gl.parse_questions(QUESTIONS_MD)}
        self.assertEqual(qs[1]["status"], "open")
        self.assertEqual(qs[2]["status"], "answered")
        self.assertIn("26 g", qs[2]["answer"])
        self.assertEqual(qs[3]["status"], "open")

    def test_a_bold_answer_counts_too(self):
        qs = gl.parse_questions("## Machines\n\n**1. A question**\n**Answer:** yes\n")
        self.assertEqual(qs[0]["status"], "answered")

    def test_the_heading_count_matches_the_parser(self):
        self.assertEqual(gl.count_question_headings(QUESTIONS_MD), 3)

    def test_the_real_file_has_fourteen_and_says_how_to_answer(self):
        rb = gl.load(RULEBOOK)
        path = os.path.join(_JOLLY, rb["sources"]["questions_for_gurvinder"])
        text = read_text(path)
        qs = gl.parse_questions(text)
        self.assertEqual(len(qs), 14)
        self.assertEqual(len(qs), gl.count_question_headings(text))
        self.assertEqual([q["number"] for q in qs], list(range(1, 15)))
        self.assertIn("Answer:", text.split("## ")[0],
                      "the file must tell him how to answer, above the first section")

    def test_a_number_in_an_answer_is_masked_before_it_is_published(self):
        # question 14 asks for WhatsApp numbers, so one WILL arrive here one day.
        qs = gl.parse_questions("## People\n\n**1. Who do I ask?**\nAnswer: Ravi 9876543210\n")
        masked = gl.mask_questions(qs)
        self.assertNotIn("9876543210", json.dumps(masked))
        self.assertIn("Ravi", json.dumps(masked))

    # ---- round B item 27: the shapes an answer really arrives in --------------
    def test_a_bullet_answer_counts(self):
        # the file's own "already settled" section is written in bullets, so this is
        # the shape he is looking at while he types
        qs = gl.parse_questions("## Machines\n\n**1. A question**\n- Answer: yes\n")
        self.assertEqual(qs[0]["status"], "answered")
        self.assertEqual(qs[0]["answer"], "Answer: yes")

    def test_a_quoted_answer_counts(self):
        qs = gl.parse_questions("## Machines\n\n**1. A question**\n> Answer: yes\n")
        self.assertEqual(qs[0]["status"], "answered")

    def test_an_answer_on_the_question_s_own_line_counts(self):
        qs = gl.parse_questions("## Machines\n\n**1. A question** Answer: yes\n")
        self.assertEqual(qs[0]["status"], "answered")
        self.assertIn("yes", qs[0]["answer"])

    def test_a_question_body_is_still_not_an_answer(self):
        qs = gl.parse_questions("## Machines\n\n**1. A question**\n- the stock list "
                                "has three\n")
        self.assertEqual(qs[0]["status"], "open")

    # ---- round B item 23: the counter must be WIDER than the parser -----------
    def test_a_heading_the_parser_cannot_read_is_still_counted(self):
        # bold broken on the last question: the parser drops it, and the old counter
        # keyed on the parser's own shape, so both said 2 and the check passed
        broken = QUESTIONS_MD.replace("**3. GT/MT average**", "*3. GT/MT average*")
        self.assertEqual(len(gl.parse_questions(broken)), 2)
        self.assertEqual(gl.count_question_headings(broken), 3)

    def test_a_stray_space_in_front_of_a_heading_is_still_counted(self):
        spaced = QUESTIONS_MD.replace("**3. GT/MT", " **3. GT/MT")
        self.assertEqual(len(gl.parse_questions(spaced)), 2)
        self.assertEqual(gl.count_question_headings(spaced), 3)

    def test_a_bulleted_heading_is_still_counted(self):
        bulleted = QUESTIONS_MD.replace("**3. GT/MT", "- **3. GT/MT")
        self.assertEqual(len(gl.parse_questions(bulleted)), 2)
        self.assertEqual(gl.count_question_headings(bulleted), 3)

    def test_the_real_file_declares_its_own_floor(self):
        rb = gl.load(RULEBOOK)
        text = read_text(os.path.join(_JOLLY, rb["sources"]["questions_for_gurvinder"]))
        self.assertEqual(gl.question_floor(text), 14)
        self.assertEqual(gl.heading_numbers(text), list(range(1, 15)))


# ------------------------------------------------------- the speed table ----
class PlanningRecompute(unittest.TestCase):
    def test_capped_is_the_slower_of_the_two(self):
        self.assertEqual(gl.recompute_planning(
            {"kind": "capped", "factor": 0.8, "rated": 5400.0, "best": 2910}), 2910)
        self.assertAlmostEqual(gl.recompute_planning(
            {"kind": "capped", "factor": 0.8, "rated": 2100.0, "best": 1957}), 1680.0)

    def test_rated_is_the_factor_on_the_listed_speed(self):
        self.assertAlmostEqual(gl.recompute_planning(
            {"kind": "rated", "factor": 0.8, "rated": 1260.0}), 1008.0)

    def test_typical_is_the_middle_of_the_long_runs_with_no_factor(self):
        self.assertEqual(gl.recompute_planning(
            {"kind": "typical", "median": 1610, "median_sustained": 820}), 820)

    def test_carried_is_the_factor_on_the_old_table(self):
        self.assertAlmostEqual(gl.recompute_planning(
            {"kind": "carried", "factor": 0.8, "carried_from": 1000.0}), 800.0)

    def test_derived_is_another_slot_unchanged(self):
        self.assertEqual(gl.recompute_planning(
            {"kind": "derived", "derived_from": ["Tin Head", "15L"]},
            {("Tin Head", "15L"): 192}), 192)

    def test_no_rate_means_no_number(self):
        self.assertIsNone(gl.recompute_planning({"kind": "none"}))
        self.assertIsNone(gl.recompute_planning({}))

    def test_every_speed_in_the_real_rulebook_works_out_again(self):
        rb = gl.load(RULEBOOK)
        by_slot = {(line, slot): block["planning"]
                   for line, spec in rb["lines"].items()
                   for slot, block in spec["speeds"].items()}
        for line, spec in rb["lines"].items():
            for slot, block in spec["speeds"].items():
                again = gl.recompute_planning(block["planning_rule"], by_slot)
                if block["planning"] is None:
                    self.assertIsNone(again, f"{line} {slot}")
                else:
                    self.assertLess(abs(again - block["planning"]), 1, f"{line} {slot}")


class PlanningSpeedCheck(unittest.TestCase):
    def rows(self, **over):
        row = {"line": "Tin Head", "slot": "15L", "multi": False, "planning": 192,
               "rate_basis": "capped",
               "planning_rule": {"kind": "capped", "factor": 0.8, "rated": 240.0, "best": 215}}
        row.update(over)
        return [row]

    def test_a_speed_that_matches_its_rule_passes(self):
        self.assertEqual(failed(run_check(gl.check_planning_speeds, self.rows())), [])

    def test_a_speed_that_does_not_match_its_rule_refuses(self):
        bad = run_check(gl.check_planning_speeds, self.rows(planning=240))
        self.assertIn("every machine speed is the rule it says it followed", failed(bad))

    def test_a_rule_nobody_can_work_out_refuses(self):
        bad = run_check(gl.check_planning_speeds,
                        self.rows(planning_rule={"kind": "none"}))
        self.assertIn("every machine speed on the plan can be worked out again", failed(bad))

    def test_a_basis_word_the_site_cannot_draw_refuses(self):
        bad = run_check(gl.check_planning_speeds, self.rows(rate_basis="planning"))
        self.assertIn("every machine speed on this table says where it came from, in a "
                      "word the site knows",
                      failed(bad))


# --------------------------------------------------------- what may run -----
class Eligibility(unittest.TestCase):
    def test_a_fifteen_litre_tin_only_has_the_tin_head(self):
        rb = a_rulebook()
        self.assertEqual(gl.eligible_lines(rb, LINES, MULTI, "15L", "TIN"), {"Tin Head": 1})

    def test_a_five_litre_tin_has_two_machines_in_order(self):
        rb = a_rulebook()
        self.assertEqual(gl.eligible_lines(rb, LINES, MULTI, "5L", "TIN"),
                         {"Tin Head": 2, "6 Head": 1})

    def test_a_slot_nobody_has_a_speed_for_is_not_a_machine(self):
        # 6 Head 3 L is in the rulebook and has no planning speed (B16)
        rb = a_rulebook()
        self.assertEqual(gl.eligible_lines(rb, LINES, MULTI, "3L", "HDPE"), {})

    def test_a_set_of_two_takes_the_set_speed_or_nothing(self):
        rb = a_rulebook()
        rb["lines"]["Clear Pack"]["slots"]["1L"]["ANY"] = 1
        self.assertEqual(gl.eligible_lines(rb, LINES, MULTI, "1L", "ANY", fills=2),
                         {"Clear Pack": 1})
        self.assertEqual(gl.eligible_lines(rb, LINES, {}, "1L", "ANY", fills=2), {})

    def test_the_mark_three_question_would_have_said_no_machine(self):
        # the bug this replaced: `lines` has no TIN key in Mark 4, so a slot-key guess
        # concludes nothing fills a tin while the Tin Head is filling them.
        self.assertNotIn("TIN", {s for slots in LINES.values() for s in slots})
        self.assertTrue(gl.eligible_lines(a_rulebook(), LINES, MULTI, "15L", "TIN"))


class RunsAgainstTheRulebook(unittest.TestCase):
    def check_days(self, *runs):
        rb = a_rulebook()
        days = [a_day(runs=list(runs))]
        return run_check(gl.check_runs, rb, LINES, MULTI, days, rb["sku_pack"])

    def test_a_plan_that_obeys_the_rulebook_passes(self):
        self.assertEqual(failed(self.check_days(a_run())), [])

    def test_a_tin_on_clear_pack_refuses(self):
        bad = self.check_days(a_run(line="Clear Pack"))
        self.assertIn("every tin was filled on a tin machine", failed(bad))

    def test_fifteen_litres_on_the_ten_head_refuses(self):
        bad = self.check_days(a_run(line="10 Head"))
        self.assertIn("nothing ran on a machine that cannot fill it", failed(bad))

    def test_three_litres_on_clear_pack_refuses(self):
        bad = self.check_days(a_run(line="Clear Pack", code="FG-CP3", slot="3L",
                                    family="HDPE", pref=1))
        self.assertIn("nothing ran on a machine that cannot fill it", failed(bad))

    def test_a_pouch_off_the_pouch_machine_refuses(self):
        bad = self.check_days(a_run(line="6 Head", slot="POUCH", family="ANY"))
        self.assertIn("nothing ran on a machine that cannot fill it", failed(bad))

    def test_a_drum_on_any_machine_refuses(self):
        bad = self.check_days(a_run(line="6 Head", code="FG-DRUM", slot="DRUM",
                                    family="DRUM"))
        self.assertIn("no drum was ever put on a machine", failed(bad))

    def test_a_twenty_six_gram_bottle_on_clear_pack_refuses(self):
        bad = self.check_days(a_run(line="Clear Pack", code="FG-JP1", slot="1L",
                                    family="26G"))
        self.assertIn("every run used a bottle its machine handles", failed(bad))

    def test_a_forty_gram_bottle_on_jp_refuses(self):
        bad = self.check_days(a_run(line="JP Machine", code="FG-CP1", slot="1L",
                                    family="40G"))
        self.assertIn("every run used a bottle its machine handles", failed(bad))

    def test_a_preference_that_is_not_the_rulebook_s_refuses(self):
        bad = self.check_days(a_run(line="6 Head", slot="5L", family="TIN", pref=2))
        self.assertIn("every run is one the rulebook allows, at the choice it names",
                      failed(bad))


class HoursAndNights(unittest.TestCase):
    def test_ten_hours_a_machine_and_twenty_for_the_night_one_passes(self):
        self.assertEqual(failed(run_check(gl.check_hours_and_nights,
                                          [a_day(line_hours={"Tin Head": 10.0,
                                                             "6 Head": 20.0})], 10)), [])

    def test_a_machine_over_ten_hours_that_is_not_the_night_one_refuses(self):
        bad = run_check(gl.check_hours_and_nights,
                        [a_day(line_hours={"Tin Head": 12.0})], 10)
        self.assertIn("no machine runs longer than a full shift", failed(bad))

    def test_the_night_machine_over_two_shifts_refuses(self):
        bad = run_check(gl.check_hours_and_nights,
                        [a_day(line_hours={"6 Head": 21.0})], 10)
        self.assertIn("the one machine that runs at night stops at two shifts", failed(bad))

    def test_more_hours_than_the_day_gave_it_refuses(self):
        bad = run_check(gl.check_hours_and_nights,
                        [a_day(line_hours={"Tin Head": 10.6},
                               line_hours_max={"Tin Head": 10.0})], 10)
        self.assertIn("no machine runs longer than the hours it had that day", failed(bad))

    def test_a_day_with_no_night_machine_named_refuses(self):
        bad = run_check(gl.check_hours_and_nights, [a_day(night_line=None)], 10)
        self.assertIn("every day says which machine runs at night, and why", failed(bad))

    def test_a_night_machine_with_no_reason_refuses(self):
        bad = run_check(gl.check_hours_and_nights,
                        [a_day(night_line={"line": "6 Head"})], 10)
        self.assertIn("every day says which machine runs at night, and why", failed(bad))

    # ---- round B item 20: AC04 stopped being enforced and still said "passed" ----
    def test_a_day_with_no_hours_ceiling_at_all_refuses(self):
        # `cap = day.get("line_hours_max") or {}` then `if line in cap`: delete the key
        # from the day files and the cap test became a loop over nothing — rc=0,
        # everything green, and /assumptions told Gurvinder AC04 passed.
        day = a_day()
        day.pop("line_hours_max")
        bad = run_check(gl.check_hours_and_nights, [day], 10)
        self.assertIn("every day says how many hours each machine had", failed(bad))

    def test_a_machine_that_ran_with_no_ceiling_of_its_own_refuses(self):
        bad = run_check(gl.check_hours_and_nights,
                        [a_day(line_hours={"Tin Head": 9.0, "6 Head": 10.0, "JP Machine": 8.0})],
                        10)
        self.assertIn("every day says how many hours each machine had", failed(bad))

    def test_a_plan_built_with_sundays_worked_refuses(self):
        # R04 is a settled ruling, not a knob gen defers to: flipping the freeze's
        # rules.sundays_off to False used to make the Sunday half simply vanish.
        bad = run_check(gl.check_hours_and_nights, [a_day()], 10, sundays_off=False)
        self.assertIn("the plan was built with Sunday closed", failed(bad))

    def test_a_closed_sunday_passes_and_a_working_one_refuses(self):
        sunday = a_day(date="2026-09-06", weekday="Sunday", working=False, made_litres=0,
                       runs=[], line_hours={"Tin Head": 0.0},
                       night_line={"line": None, "reason": "Sunday — no production (R04)"})
        self.assertEqual(failed(run_check(gl.check_hours_and_nights, [sunday], 10)), [])
        bad = run_check(gl.check_hours_and_nights,
                        [dict(sunday, made_litres=900, runs=[a_run()])], 10)
        self.assertIn("nothing is filled on a Sunday", failed(bad))


class PackClass(unittest.TestCase):
    plan = [{"code": "FG-TIN15", "sku": "SOYABEAN 15 LTR", "pieces": 10, "litres": 150},
            {"code": "FG-JP1", "sku": "MUSTARD 1 LTR", "pieces": 10, "litres": 10}]

    def test_a_plan_the_recipe_knows_passes(self):
        self.assertEqual(failed(run_check(gl.check_pack_class, a_rulebook(), self.plan)), [])

    def test_a_product_with_no_recipe_entry_refuses(self):
        bad = run_check(gl.check_pack_class, a_rulebook(),
                        self.plan + [{"code": "FG-NEW", "sku": "?", "pieces": 1, "litres": 1}])
        self.assertIn("every product in the month's target says which container it fills",
                      failed(bad))

    def test_a_sheet_disagreement_that_is_not_a_tin_refuses(self):
        rb = a_rulebook()
        rb["sku_pack"]["FG-TIN15"]["family"] = "HDPE"
        bad = run_check(gl.check_pack_class, rb, self.plan)
        self.assertIn("where the sheet and the recipe disagree, the recipe says tin",
                      failed(bad))

    def test_a_container_size_no_machine_knows_refuses(self):
        rb = a_rulebook()
        rb["sku_pack"]["FG-JP1"]["slot"] = "7L"
        bad = run_check(gl.check_pack_class, rb, self.plan)
        self.assertIn("every container is one of the sizes the machines know", failed(bad))


class EngineGates(unittest.TestCase):
    def srb(self, **over):
        srb = {"applied": True, "version": "mark4-test", "unmapped_codes": [],
               "no_line_skus": [], "multi_fill_no_rate": [], "efficiency_applied": 1.0,
               "hours_override": None, "trailing_source": "the past three months",
               "no_trailing_codes": []}
        srb.update(over)
        return srb

    def test_a_clean_run_passes(self):
        self.assertEqual(failed(run_check(gl.check_engine_gates, a_rulebook(), self.srb(),
                                          "mark4-test")), [])

    def test_a_different_rulebook_between_the_freeze_and_this_checkout_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(), self.srb(), "mark4-other")
        self.assertIn("the plan was built on the rulebook this checkout carries", failed(bad))

    def test_a_product_the_recipe_does_not_know_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(),
                        self.srb(unmapped_codes=["FG-NEW"]), "mark4-test")
        self.assertIn("every product in the month's target is one the recipe knows",
                      failed(bad))

    def test_a_product_with_no_machine_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(),
                        self.srb(no_line_skus=["FG-CP3"]), "mark4-test")
        self.assertIn("every product the plan must make has a machine that can fill it",
                      failed(bad))

    def test_a_set_of_two_with_no_speed_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(),
                        self.srb(multi_fill_no_rate=["FG-COMBO"]), "mark4-test")
        self.assertIn("every set-of-two product has a speed for filling it as a set",
                      failed(bad))

    def test_the_old_half_speed_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(),
                        self.srb(efficiency_applied=0.5), "mark4-test")
        self.assertIn("the machines are planned at their planning speed and nothing is "
                      "slowed twice", failed(bad))

    def test_a_hand_stretched_shift_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(),
                        self.srb(hours_override=22), "mark4-test")
        self.assertIn("nobody stretched the shift by hand on this run", failed(bad))

    def test_a_past_sales_figure_from_nowhere_refuses(self):
        bad = run_check(gl.check_engine_gates, a_rulebook(),
                        self.srb(trailing_source=None), "mark4-test")
        self.assertIn("the past-sales figure the plan ranks by says where it came from",
                      failed(bad))


class DemandBaseline(unittest.TestCase):
    def baseline(self, **over):
        base = {"present": True, "used_for_forecast": True, "months": 3,
                "channels_included": ["GT"], "channels_excluded": ["E-COMMERCE"],
                "intercompany_excluded": ["CUSTA000606"],
                "reconciliation": {"skus_vs_totals_pct": 100.0,
                                   "channels_vs_totals_pct": 99.8,
                                   "weeks_vs_totals_pct": 100.0}}
        base.update(over)
        return base

    def test_a_baseline_that_adds_up_passes(self):
        self.assertEqual(failed(run_check(gl.check_demand_baseline, a_rulebook(),
                                          self.baseline(), [], True)), [])

    def test_the_wrong_number_of_months_refuses(self):
        bad = run_check(gl.check_demand_baseline, a_rulebook(), self.baseline(months=6),
                        [], True)
        self.assertIn("the expected orders look back the number of months the rulebook says",
                      failed(bad))

    def test_a_split_that_does_not_add_up_refuses(self):
        base = self.baseline()
        base["reconciliation"]["weeks_vs_totals_pct"] = 97.0
        bad = run_check(gl.check_demand_baseline, a_rulebook(), base, [], True)
        self.assertIn("the past sales add back up to their own total", failed(bad))

    def test_a_missing_customer_group_list_refuses(self):
        bad = run_check(gl.check_demand_baseline, a_rulebook(),
                        self.baseline(channels_excluded=[]), [], True)
        self.assertIn("the customer groups counted and left out are both named", failed(bad))

    def test_the_fallback_must_be_said_out_loud(self):
        absent = {"present": False, "used_for_forecast": False}
        said = ["expected orders are the plan sheet's weekly buckets — the file is missing"]
        self.assertEqual(failed(run_check(gl.check_demand_baseline, a_rulebook(), absent,
                                          said, False)), [])
        bad = run_check(gl.check_demand_baseline, a_rulebook(), absent, [], False)
        self.assertIn("when past sales could not be read, the plan says what it used instead",
                      failed(bad))


class OverviewHeadline(unittest.TestCase):
    def overview(self, **over):
        out = {
            "money": {"today_plan_rs": 1, "today_booked_rs": 2, "mtd_made_rs": 3,
                      "target_rs_per_day": 25000000, "floor_rs_per_day": 20000000},
            "day1": {"working": True},
            # a strip row says its name, the hours it used and the hours it had —
            # `hours_available: null` on every machine is what the front page looked
            # like when the AC04 cap check had quietly stopped checking anything
            "lines_today": [{"line": "Tin Head", "litres": 1500,
                             "hours_planned": 9.0, "hours_available": 10.0}],
            "dispatch": {"pendency_days_all": 1.5, "pendency_days_oil": 5.1,
                         "lag_median_days": 2, "lag_p90_days": 9,
                         "lag_basis": "the gate log", "headline": "days of work"},
        }
        out.update(over)
        return out

    def test_a_front_page_with_all_four_passes(self):
        self.assertEqual(failed(run_check(gl.check_overview, self.overview())), [])

    def test_no_money_refuses(self):
        bad = run_check(gl.check_overview, self.overview(money={}))
        self.assertIn("the front page says what today's filling is worth, against the "
                      "target and the floor", failed(bad))

    def test_no_strip_per_machine_on_a_working_day_refuses(self):
        bad = run_check(gl.check_overview, self.overview(lines_today=[]))
        self.assertIn("the front page has a strip per machine", failed(bad))

    def test_a_machine_with_no_hours_beside_it_refuses(self):
        bad = run_check(gl.check_overview, self.overview(
            lines_today=[{"line": "Tin Head", "litres": 1500, "hours_planned": 9.0,
                          "hours_available": None}]))
        self.assertIn("every machine on the front page says its name, its hours and the "
                      "hours it had", failed(bad))

    def test_a_dispatch_block_with_no_lag_refuses(self):
        bad = run_check(gl.check_overview, self.overview(
            dispatch={"pendency_days_all": 1.5, "pendency_days_oil": 5.1}))
        self.assertIn("the dispatch headline is days of work in the book and how long a "
                      "bill waits", failed(bad))

    def test_a_trucks_left_today_key_refuses(self):
        over = self.overview()
        over["dispatch"]["trucks_today"] = 41
        bad = run_check(gl.check_overview, over)
        self.assertIn("the trucks that left today are not the headline any more", failed(bad))

    def test_a_count_of_trucks_in_a_headline_refuses(self):
        over = self.overview()
        over["dispatch"]["headline"] = "41 Trucks left today"
        bad = run_check(gl.check_overview, over)
        self.assertIn("the trucks that left today are not the headline any more", failed(bad))

    def test_the_singular_does_not_get_past_it_either(self):
        over = self.overview()
        over["dispatch"]["headline"] = "41 truck left today"
        bad = run_check(gl.check_overview, over)
        self.assertIn("the trucks that left today are not the headline any more", failed(bad))

    # AC09 bans the COUNT of trucks that left today (R21), not the word "truck".
    # These two used to refuse the whole cycle — on a three-minute loop that is the
    # site freezing on its last good plan because of one word in an adapter note.
    def test_gen_s_own_lag_sentence_passes(self):
        over = self.overview()
        over["dispatch"]["headline"] = ("the open dispatch book is 1.5 day(s) of work, and a "
                                        "bill billed today reaches a truck in about 2 day(s)")
        self.assertEqual(failed(run_check(gl.check_overview, over)), [])

    def test_a_warning_that_happens_to_say_trucks_passes(self):
        over = self.overview()
        over["warnings"] = ["3 tanker trucks of crude are still on the water"]
        self.assertEqual(failed(run_check(gl.check_overview, over)), [])


# ------------------------------------------- what could not start, counted ---
class StuckCounts(unittest.TestCase):
    """Two counts, one meaning. `blocked` is one row per ATTEMPT and in rulebook mode
    a product is a candidate on up to four machines, so it tries once per machine:
    87 rows behind 33 products on the worst day of this run. The site quoted the rows
    and called them stuck products. These are the shapes that must never pass again."""

    DAY1 = {"attempts": 15, "products": 13}

    def spine(self, **over):
        row = {"n": 1, "date": "2026-09-05", "blocked": 15, "blocked_products": 13}
        row.update(over)
        return [row]

    def test_attempts_and_products_side_by_side_passes(self):
        self.assertEqual(failed(run_check(gl.check_stuck_counts, self.spine(), self.DAY1)), [])

    def test_more_products_than_attempts_refuses(self):
        check = run_check(gl.check_stuck_counts, self.spine(blocked_products=16), self.DAY1)
        self.assertIn("the spine counts stuck attempts and stuck products apart", failed(check))

    def test_products_with_nothing_stopped_refuses(self):
        check = run_check(gl.check_stuck_counts,
                          self.spine(blocked=0, blocked_products=3),
                          {"attempts": 0, "products": 3})
        self.assertIn("the spine counts stuck attempts and stuck products apart", failed(check))

    def test_tries_stopped_and_no_product_behind_them_refuses(self):
        check = run_check(gl.check_stuck_counts,
                          self.spine(blocked_products=0), {"attempts": 15, "products": 0})
        self.assertIn("the spine counts stuck attempts and stuck products apart", failed(check))

    def test_a_spine_that_never_counted_the_products_refuses(self):
        row = self.spine()[0]
        del row["blocked_products"]
        check = run_check(gl.check_stuck_counts, [row], self.DAY1)
        self.assertIn("the spine counts stuck attempts and stuck products apart", failed(check))

    def test_the_row_count_published_as_the_product_count_refuses(self):
        """The bug itself: the attempt count copied into the products field."""
        check = run_check(gl.check_stuck_counts, self.spine(blocked_products=15), self.DAY1)
        self.assertIn("day 1 says the same stuck counts in the spine and on the front page",
                      failed(check))

    def test_the_front_page_and_the_spine_disagreeing_refuses(self):
        check = run_check(gl.check_stuck_counts, self.spine(),
                          {"attempts": 87, "products": 33})
        self.assertIn("day 1 says the same stuck counts in the spine and on the front page",
                      failed(check))

    def test_no_day_one_at_all_refuses(self):
        self.assertIn("day 1 is in the spine", failed(run_check(gl.check_stuck_counts, [], self.DAY1)))


class AssumptionsPage(unittest.TestCase):
    def page(self, rb, **over):
        out = {"settled": [dict(r) for r in rb["settled"]],
               "assumed": [dict(r) for r in rb["assumed"]],
               "build_choices": [dict(r) for r in rb["build_choices"]],
               "open_questions": gl.parse_questions(QUESTIONS_MD)}
        out.update(over)
        return out

    def test_a_complete_page_passes(self):
        rb = a_rulebook()
        self.assertEqual(failed(run_check(gl.check_assumptions, rb, self.page(rb),
                                          QUESTIONS_MD)), [])

    def test_a_missing_ruling_refuses(self):
        rb = a_rulebook()
        bad = run_check(gl.check_assumptions, rb, self.page(rb, settled=[]), QUESTIONS_MD)
        self.assertIn("every settled ruling is on the page", failed(bad))

    def test_a_missing_guess_refuses(self):
        rb = a_rulebook()
        bad = run_check(gl.check_assumptions, rb, self.page(rb, assumed=[]), QUESTIONS_MD)
        self.assertIn("every guess the plan makes is on the page", failed(bad))

    def test_a_missing_build_choice_refuses(self):
        rb = a_rulebook()
        bad = run_check(gl.check_assumptions, rb, self.page(rb, build_choices=[]),
                        QUESTIONS_MD)
        self.assertIn("every choice made while building it is on the page", failed(bad))

    def test_a_question_the_parser_swallowed_refuses(self):
        rb = a_rulebook()
        page = self.page(rb)
        page["open_questions"] = page["open_questions"][:2]
        bad = run_check(gl.check_assumptions, rb, page, QUESTIONS_MD)
        self.assertIn("every question in the file for Gurvinder is on the page", failed(bad))

    # ---- round B item 19: THE ONE THAT BLOCKED THE DEPLOY --------------------
    def test_a_phone_number_that_got_past_the_door_refuses(self):
        # the check has to be able to fail, or it is not a check: this is the page
        # exactly as it looked when `Ravi.9876543210` was published with 274/274 green
        rb = a_rulebook()
        page = self.page(rb)
        page["open_questions"] = gl.parse_questions(
            QUESTIONS_MD + "\n**4. Who do I ask?**\nAnswer: Ravi.9876543210\n")
        bad = run_check(gl.check_assumptions, rb, page,
                        QUESTIONS_MD + "\n**4. Who do I ask?**\nAnswer: Ravi.9876543210\n")
        self.assertIn("no phone number and no long run of digits is on the questions page",
                      failed(bad))

    def test_the_same_page_masked_at_the_door_passes(self):
        rb = a_rulebook()
        text = QUESTIONS_MD + "\n**4. Who do I ask?**\nAnswer: Ravi.9876543210\n"
        page = self.page(rb, open_questions=gl.mask_questions(gl.parse_questions(text)))
        self.assertNotIn("9876543210", json.dumps(page))
        self.assertEqual(failed(run_check(gl.check_assumptions, rb, page, text)), [])

    def test_every_shape_a_number_arrives_in_is_masked(self):
        text = ("## People\n\n<!-- questions: 1 -->\n**1. Who do I ask?**\n"
                "Answer: Ravi.9876543210, Sukhdev 98765.43210, JP +91.9876543210, "
                "dispatch 9876543210, godown 0123456789\n")
        out = json.dumps(gl.mask_questions(gl.parse_questions(text)))
        for digits in ("9876543210", "98765.43210", "0123456789"):
            self.assertNotIn(digits, out, f"{digits} reached the page")
        self.assertIn("Ravi", out)

    def test_a_date_in_an_answer_is_not_mistaken_for_a_number(self):
        # thirteen digits once the separators are allowed. Refusing to publish because
        # he answered with a date would take the site dark on a three-minute loop.
        qs = gl.parse_questions("## Machines\n\n**1. When?**\nAnswer: fixed by "
                                "2026-09-15 14:30\n")
        self.assertIn("2026-09-15 14:30", json.dumps(gl.mask_questions(qs)))

    def test_a_lost_question_refuses_even_when_the_numbering_still_looks_tidy(self):
        # question 14 dropped: 1..13 is unique, sorted, and matches a parser-shaped
        # count of 13. The floor the file declares is what refuses it.
        rb = a_rulebook()
        page = self.page(rb)
        page["open_questions"] = page["open_questions"][:2]
        text = QUESTIONS_MD.replace("**3. GT/MT average**", "*3. GT/MT average*")
        bad = run_check(gl.check_assumptions, rb, page, text)
        self.assertIn("the file still has every question it says it has", failed(bad))

    def test_a_file_with_no_floor_declared_refuses(self):
        rb = a_rulebook()
        text = QUESTIONS_MD.replace("<!-- questions: 3 -->", "")
        page = self.page(rb, open_questions=gl.parse_questions(text))
        bad = run_check(gl.check_assumptions, rb, page, text)
        self.assertIn("the file still has every question it says it has", failed(bad))

    def test_a_status_that_is_neither_open_nor_answered_refuses(self):
        rb = a_rulebook()
        page = self.page(rb)
        page["open_questions"][0]["status"] = "maybe"
        bad = run_check(gl.check_assumptions, rb, page, QUESTIONS_MD)
        self.assertIn("every question is either open or answered", failed(bad))


# --------------------------------------------------- the plan really written --
class ThePublishedPlan(unittest.TestCase):
    """The files the chain last wrote on this box, if it has run. Everything above is
    synthetic; this is the guard that the synthetic shapes are the real ones."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(PLAN_DIR, "assumptions.json")
        if not os.path.exists(path):
            raise unittest.SkipTest(
                "no live/state/plan/assumptions.json — live/state/ is gitignored. Run the "
                "offline chain first: python3 live/freeze_live.py && "
                "SIM_INPUTS=sim/live-inputs.json SIM_TAG=-live python3 engine/august_sim.py "
                "&& python3 live/gen_live.py")
        cls.assumptions = gl.load(path)
        cls.overview = gl.load(os.path.join(PLAN_DIR, "overview.json"))
        cls.spine = gl.load(os.path.join(PLAN_DIR, "spine.json"))
        cls.lines = gl.load(os.path.join(PLAN_DIR, "lines.json"))
        cls.manifest = gl.load(os.path.join(PLAN_DIR, "manifest.json"))
        cls.rb = gl.load(RULEBOOK)

    def test_every_id_and_every_question_is_on_the_page(self):
        self.assertEqual({r["id"] for r in self.assumptions["settled"]},
                         {r["id"] for r in self.rb["settled"]})
        self.assertEqual({r["id"] for r in self.assumptions["assumed"]},
                         {r["id"] for r in self.rb["assumed"]})
        self.assertEqual({r["id"] for r in self.assumptions["build_choices"]},
                         {r["id"] for r in self.rb["build_choices"]})
        self.assertEqual(len(self.assumptions["open_questions"]), 14)

    def test_the_acceptance_list_carries_this_run_s_own_result(self):
        rows = {r["id"]: r for r in self.assumptions["acceptance"]}
        self.assertEqual(len(rows), len(self.rb["acceptance_checks"]))
        for ac in ("AC01", "AC02", "AC03", "AC04", "AC05", "AC06", "AC08", "AC09"):
            self.assertTrue(rows[ac]["checked_here"], f"{ac} is not checked here")
            self.assertTrue(rows[ac]["passed"], f"{ac} did not pass")

    def test_a_line_this_file_only_half_checks_says_which_half(self):
        """AC10 is four checks in one sentence and two of them are the site's — the
        `/assumptions` page rendering, and `check:numbers`. It used to publish
        `checked_here: true, passed: true` over all four, which is the exact shape
        AC11 was fixed out of one line further down the same list."""
        rows = {r["id"]: r for r in self.assumptions["acceptance"]}
        ac10 = rows["AC10"]
        self.assertFalse(ac10["checked_here"], "AC10 is not wholly this file's to pass")
        self.assertTrue(ac10["checked_here_in_part"])
        self.assertIsNone(ac10["passed"], "a half-checked line may not publish a verdict")
        self.assertTrue(ac10["passed_here"], "the half it did check passed")
        self.assertTrue(ac10["clauses"])
        # every clause says who owns it, and at least one is somebody else's
        for c in ac10["clauses"]:
            self.assertTrue(c["clause"].strip())
            self.assertTrue(c["verdict_by"].strip())
        self.assertTrue(any(not c["checked_here"] for c in ac10["clauses"]))
        self.assertTrue(any(c["checked_here"] for c in ac10["clauses"]))
        # and the two clause verdicts name the thing that really does check them
        elsewhere = " ".join(c["verdict_by"] for c in ac10["clauses"] if not c["checked_here"])
        self.assertIn("npm run build", elsewhere)
        self.assertIn("check:numbers", elsewhere)
        # every other line still carries a whole verdict of its own
        for ac, row in rows.items():
            if row["checked_here"]:
                self.assertIsNotNone(row["passed"], ac)

    def test_it_is_in_the_manifest(self):
        self.assertIn("assumptions.json", self.manifest["files"])

    def test_the_front_page_has_the_money_the_machines_and_the_dispatch_book(self):
        self.assertTrue(self.overview["money"]["target_rs_per_day"])
        self.assertTrue(self.overview["lines_today"])
        self.assertIn("lag_median_days", self.overview["dispatch"])
        # R21 bans the COUNT of trucks that left today, not the word — the freeze
        # carries a warning about EXIM oil "on the way ... only trucks already on the
        # way are", and refusing the cycle over it is how the site goes dark on one
        # word in an adapter note (round B, item 24).
        self.assertFalse([k for k in self.overview if gl.TRUCKS_KEY_RE.search(k)])
        self.assertNotIn("trucks", json.dumps(self.overview.get("dispatch")))
        self.assertIsNone(gl.TRUCK_COUNT_RE.search(self.overview["dispatch"]["headline"]))

    def test_every_machine_on_the_front_page_says_the_hours_it_had(self):
        # the front-page half of AC04: `hours_available: null` for all six machines is
        # what it looked like when the cap check had stopped checking anything
        for row in self.overview["lines_today"]:
            self.assertIsInstance(row["hours_planned"], (int, float), row["line"])
            self.assertIsInstance(row["hours_available"], (int, float), row["line"])

    def test_the_drums_are_filled_by_hand_and_nothing_is_unfillable(self):
        self.assertEqual(sorted(r["code"] for r in self.overview["manual_fill"]),
                         sorted(self.rb["drums"]["skus"]))
        self.assertEqual(self.overview["unproducible"], [])

    def test_no_line_carries_a_fifteen_litre_slot_but_the_tin_head(self):
        for line in self.lines["lines"]:
            slots = {s["slot"] for s in line["slots"]}
            if line["name"] != "Tin Head":
                self.assertNotIn("15L", slots, f"{line['name']} must not have a 15 L speed")
        self.assertEqual(self.lines["efficiency"], 1.0)
        self.assertTrue(self.lines["planning_factor"])

    def test_the_spine_counts_stuck_attempts_and_stuck_products_apart(self):
        for row in self.spine:
            self.assertIsInstance(row["blocked_products"], int, row["date"])
            self.assertLessEqual(row["blocked_products"], row["blocked"], row["date"])
            self.assertEqual(row["blocked_products"] == 0, row["blocked"] == 0, row["date"])
        day1 = self.spine[0]
        self.assertEqual(day1["blocked"], self.overview["day1_blocked"]["attempts"])
        self.assertEqual(day1["blocked_products"], self.overview["day1_blocked"]["products"])
        # this run really does have a day where the two are far apart — if it ever
        # stops having one, the site is being proved against a shape it never meets
        self.assertTrue(any(r["blocked_products"] < r["blocked"] for r in self.spine))
        self.assertIn("ATTEMPTS", day1["blocked_label"])

    def test_the_stuck_block_names_today_s_want_apart_from_the_month_s_target(self):
        stuck = self.overview["stuck"]
        for bucket in ("material", "storage", "no_order", "no_line_time"):
            for row in stuck[bucket]:
                self.assertNotIn("plan_litres", row, f"{bucket} {row['code']}")
                self.assertNotIn("plan_pieces", row, f"{bucket} {row['code']}")
                self.assertIn("month_target_litres", row, f"{bucket} {row['code']}")
        # only the buckets the planner actually TRIED today carry today's want, and
        # storage is one of them: the run was attempted, the machine had the hours and
        # the material was there — the godown had no room for the output (B20).
        for bucket in ("material", "storage"):
            for row in stuck[bucket]:
                self.assertIn("want_litres", row, f"{bucket} {row['code']}")
        for bucket in ("no_order", "no_line_time"):
            for row in stuck[bucket]:
                self.assertNotIn("want_litres", row, f"{bucket} {row['code']}")
        self.assertIn("never add them together", stuck["litres_note"].lower())

    def test_a_product_the_godown_stopped_is_not_filed_as_short_of_material(self):
        """B20. The engine emits a held-up row with STORAGE as the binder; it must not
        land in the bucket whose own words are 'something it is made from ran out',
        because no purchase order fixes a full godown."""
        stuck = self.overview["stuck"]
        for row in stuck["material"]:
            self.assertTrue(row["short_of"], row["code"])
            for short in row["short_of"]:
                self.assertNotEqual(short["code"], "STORAGE", row["code"])
        codes = {r["code"] for r in stuck["storage"]}
        self.assertFalse(codes & {r["code"] for r in stuck["material"]},
                         "a product cannot be in both buckets")
        self.assertFalse(codes & {r["code"] for r in stuck["no_line_time"]})
        self.assertFalse(codes & {r["code"] for r in stuck["no_order"]})
        self.assertEqual(stuck["counts"]["storage"], len(stuck["storage"]))
        self.assertIn("godown", stuck["definitions"]["storage"].lower())
        self.assertIn("godown", stuck["headings"]["storage"].lower())

    def test_every_bucket_s_heading_is_written_from_its_own_rows(self):
        stuck = self.overview["stuck"]
        headings = stuck["headings"]
        # every bucket of rows has a heading and a definition, and no bucket may be
        # rendered with a heading borrowed from another one
        buckets = {k for k, v in stuck.items() if isinstance(v, list)}
        self.assertEqual(set(headings), buckets)
        self.assertEqual(set(stuck["definitions"]), buckets)
        self.assertTrue(buckets >= {"material", "storage", "no_order", "no_line_time",
                                    "manual"})
        self.assertTrue(all(v and v.strip() for v in headings.values()))
        with_room = [r for r in stuck["no_line_time"] if r.get("machines_with_room")]
        self.assertEqual(len(with_room), stuck["counts"]["no_line_time_with_a_free_machine"])
        # the heading the front page used to hardcode — "The machine had no hours left" —
        # above rows that mostly HAD a machine with hours to spare
        if with_room:
            self.assertNotIn("hours", headings["no_line_time"].lower())
            self.assertNotIn("full", headings["no_line_time"].lower())
            self.assertIn("hours to spare", stuck["definitions"]["no_line_time"])
        else:
            self.assertIn("full", headings["no_line_time"].lower())
        for line, free in stuck["hours_free_today"].items():
            self.assertIsInstance(free, (int, float), line)

    def test_every_published_speed_says_a_word_the_site_draws(self):
        for line in self.lines["lines"]:
            for slot in line["slots"]:
                self.assertIn(slot["rate_basis"], gl.RULEBOOK_BASIS_WORDS)
                self.assertEqual(slot["stored_rate_per_hr"], slot["effective_rate_per_hr"])


if __name__ == "__main__":
    unittest.main()
