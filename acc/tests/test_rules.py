"""rules.py — the pure decisions. No SAP, no files, no clock.

The load-bearing test is test_golden_payload_matches_the_logged_draft: it pins
build_payload against the exact bytes that created Draft 54983 in live SAP on
2026-08-22, read back out of the shared write log.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from acc.apbatch import rules

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# The golden draft payload: a copy in fixtures/ (always there) and the operator
# write log it was copied from (only on the box that made the write).
GOLDEN_RECORD = FIXTURES / "write_log_draft_54983.jsonl"
LIVE_WRITE_LOG = REPO / "queries" / "USER36" / "sap-writes.jsonl"


def grpo_25714() -> dict:
    return json.loads((FIXTURES / "grpo_25714.json").read_text(encoding="utf-8"))


class InrTest(unittest.TestCase):
    def test_indian_grouping(self):
        self.assertEqual("₹253,110.00".replace("253,110", "2,53,110"), rules.inr(253110))
        self.assertEqual("₹214.50", rules.inr(214.5))
        self.assertEqual("₹1,00,000.00", rules.inr(100000))
        self.assertEqual("₹8,17,00,000.00", rules.inr(81700000))
        self.assertEqual("-₹20,93,00,000.00", rules.inr(-209300000))
        self.assertEqual("₹0.00", rules.inr(0))

    def test_matches_the_shipped_skill_helper(self):
        # The skill's precheck.py printed these for a year; the refactor must not
        # change a single character of the money it prints.
        for n in (0, 5, 999, 1000, 99999, 100000, 253110, 4688807, -6752477.55):
            self.assertEqual(_legacy_inr(n), rules.inr(n), n)


def _legacy_inr(n):
    """inr() exactly as .claude/skills/jivo-ap-draft/bin/precheck.py had it."""
    import re
    neg = n < 0
    n = abs(float(n))
    i, f = f"{n:.2f}".split(".")
    last3, rest = i[-3:], i[:-3]
    if rest:
        rest = re.sub(r"\B(?=(\d{2})+(?!\d))", ",", rest) + ","
    return ("-" if neg else "") + "₹" + rest + last3 + "." + f


class DateTest(unittest.TestCase):
    def test_fy_indicator(self):
        self.assertEqual("AUG-26-27", rules.fy_indicator(dt.date(2026, 8, 14)))
        self.assertEqual("MAR-25-26", rules.fy_indicator(dt.date(2026, 3, 31)))
        self.assertEqual("APR-26-27", rules.fy_indicator(dt.date(2026, 4, 1)))
        self.assertEqual("JAN-26-27", rules.fy_indicator(dt.date(2027, 1, 5)))

    def test_month_bounds(self):
        self.assertEqual(("2026-07-01", "2026-08-01"), rules.month_bounds("2026-07-24"))
        self.assertEqual(("2026-08-01", "2026-09-01"), rules.month_bounds("2026-08-14T00:00:00Z"))
        # December must roll the year, not the month.
        self.assertEqual(("2026-12-01", "2027-01-01"), rules.month_bounds(dt.date(2026, 12, 31)))
        self.assertEqual(("2026-01-01", "2026-02-01"), rules.month_bounds("2026-01-01"))

    def test_month_bound_excludes_the_next_month(self):
        # The defect this fixes: a July GRPO scanned in August used to pull
        # August's documents and take August's series.
        m0, m1 = rules.month_bounds("2026-07-24")
        self.assertLess(m0, "2026-08-01")
        self.assertEqual("2026-08-01", m1)

    def test_iso_date_strips_the_service_layer_time(self):
        self.assertEqual("2026-08-14", rules.iso_date("2026-08-14T00:00:00Z"))
        self.assertEqual("2026-08-14", rules.iso_date(dt.date(2026, 8, 14)))
        self.assertIsNone(rules.iso_date(None))

    def test_fy_start(self):
        self.assertEqual(dt.date(2026, 4, 1), rules.fy_start(dt.date(2026, 8, 14)))
        self.assertEqual(dt.date(2025, 4, 1), rules.fy_start(dt.date(2026, 3, 31)))


class ParseSheetDateTest(unittest.TestCase):
    def test_four_text_formats(self):
        for text in ("2026-08-13", "13/08/2026", "13-08-2026", "13-Aug-2026"):
            self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date(text), text)

    def test_service_layer_datetime(self):
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date("2026-08-13T00:00:00Z"))

    def test_excel_serial(self):
        # Excel's 1900 system with its deliberate leap-year bug: day 0 = 1899-12-30.
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date(46247))
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date(46247.0))
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date("46247"))

    def test_a_real_date_object_passes_through(self):
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date(dt.date(2026, 8, 13)))

    def test_blank_is_none(self):
        for v in (None, "", "   "):
            self.assertIsNone(rules.parse_sheet_date(v))

    def test_nonsense_raises(self):
        for v in ("next tuesday", "13/13/2026", "2026-02-30"):
            with self.assertRaises(ValueError, msg=v):
                rules.parse_sheet_date(v)


class TdsTest(unittest.TestCase):
    LIABLE = {"SubjectToWithholdingTax": "boYES",
              "BPWithholdingTaxCollection": [{"WTCode": "1031"}]}
    NOT_LIABLE = {"SubjectToWithholdingTax": "boNO", "BPWithholdingTaxCollection": []}

    @staticmethod
    def inv(entry, wtamount=0, wtliable="tNO"):
        return {"DocEntry": entry, "NumAtCard": "R%d" % entry, "DocDate": "2026-08-0%d" % (entry % 9 + 1),
                "WTAmount": wtamount, "DocumentLines": [{"WTLiable": wtliable}]}

    def test_master_not_liable(self):
        p = rules.tds_proposal(self.NOT_LIABLE, [self.inv(1)], None, 214500)
        self.assertEqual(("no", "MASTER-NOT-LIABLE", False), (p.choice, p.basis, p.check))
        self.assertEqual(0, p.expected_amount)

    def test_master_not_liable_but_history_withheld_asks_for_a_check(self):
        p = rules.tds_proposal(self.NOT_LIABLE, [self.inv(1, wtamount=214)], None, 214500)
        self.assertEqual(("no", "MASTER-NOT-LIABLE", True), (p.choice, p.basis, p.check))

    def test_no_history_falls_back_to_the_master(self):
        p = rules.tds_proposal(self.LIABLE, [], 0.1, 214500)
        self.assertEqual(("yes", "NO-HISTORY->MASTER", True), (p.choice, p.basis, p.check))
        self.assertEqual(214, p.expected_amount)

    def test_precedent_yes(self):
        posted = [self.inv(i, wtamount=100.0) for i in (1, 2, 3)]
        p = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500)
        self.assertEqual(("yes", "PRECEDENT-YES", False), (p.choice, p.basis, p.check))

    def test_precedent_no_is_the_tpac_case(self):
        # TPAC, 2026-08-22: master says 194Q 0.1% (₹214), last three posted
        # invoices are all tNO with WTAmount 0 — the operator chose no TDS, and
        # that is how JIVO books this vendor.
        posted = [self.inv(i) for i in (1, 2, 3)]
        p = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500)
        self.assertEqual(("no", "PRECEDENT-NO", False), (p.choice, p.basis, p.check))
        self.assertEqual(0, p.expected_amount)
        self.assertTrue(p.master_liable)
        self.assertEqual("1031", p.wt_code)
        self.assertIn("214", p.evidence())        # what it WOULD be, for the reviewer

    def test_mixed_history_falls_back_to_the_master_and_asks(self):
        posted = [self.inv(1, wtamount=100.0), self.inv(2), self.inv(3)]
        p = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500)
        self.assertEqual(("yes", "MIXED->MASTER", True), (p.choice, p.basis, p.check))

    def test_a_tyes_line_at_zero_rupees_is_NOT_a_precedent_for_withholding(self):
        # The inversion of a rule this build got wrong. WTLiable tYES with
        # WTAmount 0 is the C-0018 shape — somebody ticked liable and SAP
        # computed nothing. Reading it as "we withheld" made the batch propose
        # TDS for a vendor JIVO has never deducted from. It is a contradiction,
        # so: propose no, and mark it for a human.
        posted = [self.inv(i, wtamount=0, wtliable="tYES") for i in (1, 2, 3)]
        p = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500)
        self.assertEqual(("no", "PRECEDENT-NO-AMOUNT", True), (p.choice, p.basis, p.check))
        self.assertEqual(0, p.expected_amount)
        self.assertTrue(all(not x["withheld"] for x in p.precedent))
        self.assertTrue(all(x["marked"] for x in p.precedent))

    def test_the_venda000636_case_leaves_the_answer_to_a_person(self):
        # Live shape (DELHI PUNJAB TRANSPORT CO, 194C @2% on the card, three
        # posted invoices with every line WTLiable tYES and WTAmount 0). The
        # evidence has to SAY the contradiction, and column W has to come out
        # blank — see batch_scan._tds_cell, which keys off exactly this .check.
        card = {"SubjectToWithholdingTax": "boYES",
                "BPWithholdingTaxCollection": [{"WTCode": "1024"}]}
        posted = [self.inv(i, wtamount=0, wtliable="tYES") for i in (7, 8, 9)]
        p = rules.tds_proposal(card, posted, 2.0, 180000)
        self.assertTrue(p.check)
        text = p.evidence()
        self.assertTrue(text.startswith("CHECK: "), text)
        self.assertIn("marked/marked/marked", text)
        self.assertIn("WTAmount 0/0/0", text)
        self.assertIn("lines say WTax liable, nothing was withheld", text)
        self.assertIn("1024", text)

    def test_two_wt_codes_on_the_card_is_never_decided_quietly(self):
        card = {"SubjectToWithholdingTax": "boYES",
                "BPWithholdingTaxCollection": [{"WTCode": "1031"}, {"WTCode": "1024"}]}
        posted = [self.inv(i, wtamount=100.0) for i in (1, 2, 3)]
        p = rules.tds_proposal(card, posted, 0.1, 214500)
        self.assertTrue(p.check, "which of two codes applies is not ours to guess")
        self.assertEqual(["1031", "1024"], p.wt_codes)
        self.assertIn("1031, 1024", p.evidence())
        self.assertIn("2 codes on the card", p.evidence())

    def test_the_proposal_survives_a_sidecar_round_trip(self):
        # send rebuilds this from the sidecar to print the same evidence. It used
        # to carry its taxable as an attribute bolted on after construction,
        # which as_dict() did not record — evidence() then raised on the way back.
        posted = [self.inv(i) for i in (1, 2, 3)]
        before = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500)
        after = rules.TdsProposal.from_dict(json.loads(json.dumps(before.as_dict())))
        self.assertEqual(before.as_dict(), after.as_dict())
        self.assertEqual(before.evidence(), after.evidence())

    def test_an_old_sidecar_without_the_new_keys_still_loads(self):
        old = {"choice": "no", "basis": "PRECEDENT-NO", "check": False, "master_liable": True,
               "wt_code": "1031", "rate": 0.1, "expected_amount": 0, "precedent": []}
        p = rules.TdsProposal.from_dict(old)
        self.assertEqual("no", p.choice)
        self.assertEqual([], p.wt_codes)
        self.assertIn("1031", p.evidence())

    def test_only_the_last_three_count(self):
        posted = [self.inv(i, wtamount=100.0) for i in (1, 2, 3)] + [self.inv(4)]
        p = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500)
        self.assertEqual(3, len(p.precedent))
        self.assertEqual("PRECEDENT-YES", p.basis)

    def test_check_shows_up_in_the_evidence_string(self):
        p = rules.tds_proposal(self.LIABLE, [], 0.1, 214500)
        self.assertTrue(p.evidence().startswith("CHECK:"))

    def test_evidence_names_every_precedent_outcome(self):
        posted = [self.inv(i) for i in (1, 2, 3)]
        text = rules.tds_proposal(self.LIABLE, posted, 0.1, 214500).evidence()
        self.assertIn("no/no/no", text)
        self.assertIn("1031", text)

    def test_no_rate_means_no_estimate(self):
        p = rules.tds_proposal(self.LIABLE, [], None, 214500)
        self.assertEqual(0, p.expected_amount)


class SeriesTest(unittest.TestCase):
    NNM1 = [[3684, "HR_G0826", "GA"], [3732, "CNHR0826", "GA"], [3672, "DL_G0826", "GA"]]

    def test_most_common_series_among_this_months_documents_wins(self):
        docs = [{"Series": 3684}] * 40 + [{"Series": 3732}]
        c = rules.pick_series(docs, self.NNM1, "bod_GSTTaxInvoice", bpl=2, docdate="2026-08-14")
        self.assertEqual(3684, c.series)
        self.assertIsNone(c.problem)
        self.assertIn("41 docs", c.source)
        self.assertIn("Aug-26", c.source)
        self.assertIn("branch 2", c.source)

    def test_first_document_of_the_month_uses_the_single_nnm1_candidate(self):
        c = rules.pick_series([], [[3696, "PB_G0826", "GA"]], "bod_GSTTaxInvoice", bpl=3,
                              docdate="2026-08-14")
        self.assertEqual(3696, c.series)
        self.assertIn("NNM1", c.source)

    def test_several_ga_series_resolve_by_the_xx_g_name(self):
        c = rules.pick_series([], self.NNM1[:2], "bod_GSTTaxInvoice", bpl=2, docdate="2026-08-14")
        self.assertEqual(3684, c.series)      # HR_G0826, not CNHR0826

    def test_a_name_pattern_tie_break_warns_that_it_guessed(self):
        # The pattern is a house convention, not a rule: branch 6's real vendor
        # series is DISD0826, which does not match ^[A-Z]{2,4}_G\\d{4}$. So when a
        # NAME breaks the tie — no document this month, more than one candidate —
        # the row has to say so out loud in column U.
        c = rules.pick_series([], self.NNM1[:2], "bod_GSTTaxInvoice", bpl=2, docdate="2026-08-14")
        self.assertIsNotNone(c.warning)
        self.assertIn("name pattern", c.warning)
        self.assertIn("HR_G0826", c.warning)
        self.assertIn("3684", c.warning)
        self.assertIn("3732", c.warning)      # what it chose between
        self.assertIn("verify", c.warning)

    def test_a_single_candidate_is_not_a_guess_and_does_not_warn(self):
        c = rules.pick_series([], [[3684, "HR_G0826", "GA"]], "bod_GSTTaxInvoice", bpl=2,
                              docdate="2026-08-14")
        self.assertEqual(3684, c.series)
        self.assertIsNone(c.warning)

    def test_a_series_taken_from_this_months_documents_is_not_a_guess(self):
        c = rules.pick_series([{"Series": 3684}] * 12, self.NNM1[:2], "bod_GSTTaxInvoice",
                              bpl=2, docdate="2026-08-14")
        self.assertEqual(3684, c.series)
        self.assertIsNone(c.warning)

    def test_several_xx_g_series_cannot_be_picked(self):
        c = rules.pick_series([], self.NNM1, "bod_GSTTaxInvoice", bpl=2, docdate="2026-08-14")
        self.assertIsNone(c.series)
        self.assertIn("several", c.problem)

    def test_no_docs_and_no_nnm1_is_a_stop(self):
        c = rules.pick_series([], [], "bod_GSTTaxInvoice", bpl=7, docdate="2026-08-14")
        self.assertIsNone(c.series)
        self.assertIn("first document of the month", c.problem)
        self.assertIn("branch 7", c.problem)

    def test_not_being_able_to_check_nnm1_says_so_instead(self):
        # nnm1_rows=None means hana-sql was absent or unreachable — NOT that the
        # branch has no series. Saying "first document of the month" there sends
        # the operator hunting for a fact nobody looked up.
        c = rules.pick_series([], None, "bod_GSTTaxInvoice", bpl=7, docdate="2026-08-14")
        self.assertIsNone(c.series)
        self.assertIn("could not check NNM1", c.problem)
        self.assertIn("hana-sql unreachable", c.problem)
        self.assertNotIn("first document of the month", c.problem)

    def test_a_series_nnm1_does_not_list_is_a_warning_not_a_stop(self):
        c = rules.pick_series([{"Series": 9999}], self.NNM1, "bod_GSTTaxInvoice", bpl=2,
                              docdate="2026-08-14")
        self.assertEqual(9999, c.series)
        self.assertIsNone(c.problem)
        self.assertIn("9999", c.warning)

    def test_nnm1_unavailable_is_not_a_warning(self):
        # hana-sql is optional; when it cannot be reached there is nothing to
        # cross-check against and that must not become noise in column U.
        c = rules.pick_series([{"Series": 3684}], None, "bod_GSTTaxInvoice", bpl=2,
                              docdate="2026-08-14")
        self.assertEqual(3684, c.series)
        self.assertIsNone(c.warning)

    def test_bod_none_looks_for_the_dash_dash_subtype(self):
        c = rules.pick_series([], [[2477, "GRPO0826", "--"], [3684, "HR_G0826", "GA"]],
                             "bod_None", bpl=2, docdate="2026-08-14")
        self.assertEqual(2477, c.series)

    def test_debit_memo_looks_for_gd(self):
        c = rules.pick_series([], [[3700, "HR_D0826", "GD"]], "bod_GSTDebitMemo", bpl=2,
                             docdate="2026-08-14")
        self.assertEqual(3700, c.series)

    def test_series_survives_a_json_round_trip(self):
        c = rules.pick_series([{"Series": 3684}], self.NNM1, "bod_GSTTaxInvoice", bpl=2,
                              docdate="2026-08-14")
        self.assertEqual(3684, json.loads(json.dumps(c.as_dict()))["series"])


class TotalsAndSummaryTest(unittest.TestCase):
    LINES = [
        {"LineNum": 0, "ItemCode": "PM0000851", "ItemDescription": "PET BOTTLE 1 LTR 26 GM",
         "Quantity": 42900, "RemainingOpenQuantity": 42900, "UnitPrice": 5,
         "LineTotal": 214500, "TaxTotal": 38610},
        # SAP's LineTotal/TaxTotal are the WHOLE line: 500 x 2 = 1000 and 18% of
        # it. Only 100 pieces are still open, so only 100 x 2 will be billed.
        {"LineNum": 1, "ItemCode": "PM0000852", "ItemDescription": "CAP 1 LTR",
         "Quantity": 500, "RemainingOpenQuantity": 100, "UnitPrice": 2,
         "LineTotal": 1000, "TaxTotal": 180},
    ]

    def test_gross_of_is_the_money_for_the_OPEN_part_only(self):
        # Line 1 is 100 open of 500. build_payload sends Quantity=100, so the
        # draft is worth 100 x 2 = 200 of that line, not its full 1,000.
        # Summing LineTotal/TaxTotal — which is what this did — showed 215,500
        # and asked an operator to approve a figure ₹800 larger than the document
        # about to be created.
        t = rules.gross_of(self.LINES)
        self.assertEqual(43000, t.open_qty)
        self.assertEqual(42900 * 5 + 100 * 2, t.taxable)
        self.assertEqual(214700.0, t.taxable)
        self.assertNotEqual(215500.0, t.taxable)                      # the full-line sum
        self.assertEqual(round(38610 + 180 * (100 / 500), 2), t.tax)
        self.assertEqual(38646.0, t.tax)
        self.assertEqual(253346.0, t.gross)
        self.assertEqual({"0": 42900, "1": 100}, t.per_line)

    def test_gross_of_names_the_partly_billed_lines(self):
        self.assertEqual([1], rules.gross_of(self.LINES).partial_lines)
        self.assertTrue(rules.gross_of(self.LINES).partial)

    def test_a_fully_open_grpo_has_no_partial_lines(self):
        self.assertEqual([], rules.gross_of(self.LINES[:1]).partial_lines)

    def test_a_half_billed_line_bills_half(self):
        half = [dict(self.LINES[0], Quantity=1000, RemainingOpenQuantity=500,
                     UnitPrice=10, LineTotal=10000, TaxTotal=1800)]
        t = rules.gross_of(half)
        self.assertEqual(5000.0, t.taxable)
        self.assertEqual(900.0, t.tax)
        self.assertEqual(5900.0, t.gross)

    def test_a_service_line_keeps_its_own_total(self):
        # No quantity to pro-rate by: Quantity 0, RemainingOpenQuantity 0, and
        # the whole line is what gets billed. open x UnitPrice would be zero and
        # would put ₹0 on every transporter row in the sheet.
        service = [{"LineNum": 0, "ItemCode": None, "ItemDescription": "FREIGHT",
                    "Quantity": 0, "RemainingOpenQuantity": 0, "UnitPrice": 13000,
                    "LineTotal": 13000.0, "TaxTotal": 650.0}]
        t = rules.gross_of(service)
        self.assertEqual(13000.0, t.taxable)
        self.assertEqual(650.0, t.tax)
        self.assertEqual([], t.partial_lines)

    def test_the_totals_survive_a_sidecar_round_trip(self):
        d = json.loads(json.dumps(rules.gross_of(self.LINES).as_dict()))
        self.assertEqual([1], d["partial_lines"])
        self.assertEqual(214700.0, d["taxable"])
        self.assertEqual({"0": 42900, "1": 100}, d["lines"])

    def test_line_summary_shows_the_item_and_the_open_quantity(self):
        text = rules.line_summary(self.LINES[:1])
        self.assertIn("0: PM0000851", text)
        self.assertIn("42,900", text)
        self.assertIn("@5.00", text)

    def test_line_summary_marks_a_partly_invoiced_line(self):
        self.assertIn("open 100/500", rules.line_summary(self.LINES))

    def test_line_summary_caps_at_three_lines(self):
        many = [dict(self.LINES[0], LineNum=i) for i in range(7)]
        text = rules.line_summary(many)
        self.assertIn("+4 more", text)
        self.assertEqual(3, text.count("PM0000851"))

    def test_line_summary_of_a_service_line(self):
        text = rules.line_summary([{"LineNum": 0, "ItemCode": None, "ItemDescription": "EDIBLE OIL",
                                    "Quantity": 0, "RemainingOpenQuantity": 0, "UnitPrice": 13000,
                                    "LineTotal": 13000, "TaxTotal": 650}])
        self.assertIn("EDIBLE OIL", text)
        self.assertIn("@13000.00", text)

    def test_open_lines_drops_closed_and_zero_quantity_lines(self):
        grpo = {"DocumentLines": [
            {"LineNum": 0, "LineStatus": "bost_Open", "RemainingOpenQuantity": 10},
            {"LineNum": 1, "LineStatus": "bost_Close", "RemainingOpenQuantity": 5},
            {"LineNum": 2, "LineStatus": "bost_Open", "RemainingOpenQuantity": 0},
        ]}
        self.assertEqual([0], [l["LineNum"] for l in rules.open_lines(grpo)])

    def test_open_lines_keeps_service_lines_that_carry_no_quantity(self):
        grpo = {"DocType": "dDocument_Service", "DocumentLines": [
            {"LineNum": 0, "LineStatus": "bost_Open", "RemainingOpenQuantity": 0,
             "Quantity": 0, "LineTotal": 13000},
        ]}
        self.assertEqual([0], [l["LineNum"] for l in rules.open_lines(grpo)])


class CommentsTest(unittest.TestCase):
    def test_base_from_the_grpo(self):
        base = rules.comments_base(grpo_25714(), [220726021])
        self.assertEqual("Based On Goods Receipt PO 2026086625 | PO 220726021 | GATE ENTRY NO 154", base)

    def test_base_without_a_gate_entry_or_po(self):
        grpo = dict(grpo_25714(), Comments="")
        self.assertEqual("Based On Goods Receipt PO 2026086625", rules.comments_base(grpo, []))

    def test_gate_entry_with_a_space_after_no(self):
        grpo = dict(grpo_25714(), Comments="App: FactoryApp v2 | GATE ENTRY NO 154")
        self.assertIn("GATE ENTRY NO 154", rules.comments_base(grpo, []))

    def test_note_and_tag_are_appended(self):
        text = rules.build_comments("Based On Goods Receipt PO 1", note="Veh HR67C9554",
                                    tag="B240824-OIL-7F3A")
        self.assertEqual("Based On Goods Receipt PO 1 | Veh HR67C9554 | B240824-OIL-7F3A", text)

    def test_comments_stay_inside_sap_s_254_characters(self):
        text = rules.build_comments("x" * 400, note="y" * 100, tag="B240824-OIL-7F3A")
        self.assertLessEqual(len(text), 254)

    def test_the_batch_tag_survives_truncation(self):
        # grep B240824-OIL-7F3A over the write log is how a run is found later;
        # if truncation eats the tag the run becomes untraceable.
        text = rules.build_comments("x" * 400, note="y" * 100, tag="B240824-OIL-7F3A")
        self.assertTrue(text.endswith("B240824-OIL-7F3A"), text[-30:])

    def test_no_tag_no_note(self):
        self.assertEqual("base", rules.build_comments("base"))

    def test_an_empty_base_does_not_produce_a_leading_separator(self):
        # A service GRPO with no DocNum-derived base and no note used to give
        # Comments of " | B240824-OIL-7F3A", which reads like something was lost.
        self.assertEqual("B240824-OIL-7F3A", rules.build_comments("", tag="B240824-OIL-7F3A"))
        self.assertEqual("B240824-OIL-7F3A", rules.build_comments("   ", tag="B240824-OIL-7F3A"))
        self.assertEqual("note | B240824-OIL-7F3A",
                         rules.build_comments("", note="note", tag="B240824-OIL-7F3A"))
        self.assertEqual("", rules.build_comments(""))


class PayloadTest(unittest.TestCase):
    def test_golden_payload_matches_the_logged_draft(self):
        """build_payload must reproduce what actually created Draft 54983.

        The comparison target is the write log the CLI itself wrote when the
        draft was sent on 2026-08-22 — the real bytes, not a hand-typed copy.
        The four fields finalized at send time (NumAtCard, TaxDate, Comments,
        per-line WTLiable) plus the DocObjectCode the Go CLI splices in are
        removed before comparing.
        """
        logged = _logged_draft_payload()
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), bpl_id=2, series=3684,
                                      subtype="bod_GSTTaxInvoice")
        self.assertEqual(_strip_send_time_fields(logged), payload)

    @unittest.skipUnless(LIVE_WRITE_LOG.exists(),
                         "this box has no queries/USER36/sap-writes.jsonl")
    def test_the_golden_fixture_still_matches_the_live_write_log(self):
        """The fixture is a copy. This is the check that it is a faithful one.

        Skipped where the operator's write log is not present, which is most
        boxes — that is why the golden test itself reads the fixture and not this
        file.
        """
        live = _draft_intent(LIVE_WRITE_LOG.read_text(encoding="utf-8"))
        self.assertEqual(live, _logged_draft_payload())

    def test_golden_finalizes_back_to_the_logged_payload(self):
        logged = _logged_draft_payload()
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), bpl_id=2, series=3684,
                                      subtype="bod_GSTTaxInvoice")
        final = rules.finalize_payload(
            payload,
            num_at_card=logged["NumAtCard"],
            tax_date=logged["TaxDate"],
            wtliable="tNO",
            comments=logged["Comments"],
        )
        expected = {k: v for k, v in logged.items() if k != "DocObjectCode"}
        self.assertEqual(expected, final)

    def test_payload_carries_no_send_time_fields(self):
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        for field in ("NumAtCard", "TaxDate", "Comments"):
            self.assertNotIn(field, payload)
        for line in payload["DocumentLines"]:
            self.assertNotIn("WTLiable", line)

    def test_payload_posting_date_is_the_grpo_date_not_today(self):
        # C-0017. Never post on today's date or on the vendor's invoice date.
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        self.assertEqual("2026-08-14", payload["DocDate"])
        self.assertNotEqual(rules.iso_date(grpo["TaxDate"]), payload["DocDate"])

    def test_lines_are_drawn_from_the_grpo_never_re_keyed(self):
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        line = payload["DocumentLines"][0]
        self.assertEqual(20, line["BaseType"])
        self.assertEqual(25714, line["BaseEntry"])
        self.assertEqual(0, line["BaseLine"])
        self.assertEqual(42900, line["Quantity"])     # the OPEN quantity

    def test_a_closed_line_is_left_out(self):
        grpo = grpo_25714()
        closed = dict(grpo["DocumentLines"][0], LineNum=1, LineStatus="bost_Close",
                      RemainingOpenQuantity=0)
        grpo["DocumentLines"] = grpo["DocumentLines"] + [closed]
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        self.assertEqual([0], [l["BaseLine"] for l in payload["DocumentLines"]])

    def test_costing_code_is_omitted_when_the_grpo_has_none(self):
        grpo = grpo_25714()
        grpo["DocumentLines"][0]["CostingCode"] = None
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        self.assertNotIn("CostingCode", payload["DocumentLines"][0])

    def test_finalize_omits_wtliable_when_told_to(self):
        # The single-bill skill leaves WTLiable off entirely when the vendor is
        # not TDS-liable, which is what it has always sent.
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        final = rules.finalize_payload(payload, "R1", "2026-08-13", None, "c")
        self.assertNotIn("WTLiable", final["DocumentLines"][0])

    def test_finalize_does_not_mutate_the_sidecar_payload(self):
        grpo = grpo_25714()
        payload = rules.build_payload(grpo, rules.open_lines(grpo), 2, 3684, "bod_GSTTaxInvoice")
        before = json.dumps(payload, sort_keys=True)
        rules.finalize_payload(payload, "R1", "2026-08-13", "tYES", "c")
        self.assertEqual(before, json.dumps(payload, sort_keys=True))


def _draft_intent(text: str) -> dict:
    for line in text.splitlines():
        rec = json.loads(line)
        if rec.get("event") == "intent" and rec.get("path") == "Drafts":
            return rec["payload"]
    raise AssertionError("no draft intent in this write log")


def _logged_draft_payload() -> dict:
    """The first write ever made through this path, as the CLI logged it.

    Read from a COPY of that log line kept in fixtures/, not from
    queries/USER36/sap-writes.jsonl: the log is one operator's, and on any other
    box (a fresh clone, an operator who has never written) it does not exist —
    the golden test would then not fail, it would simply not run, which is the
    worst way for a load-bearing test to behave. The copy is checked against the
    live log by test_the_golden_fixture_still_matches_the_live_write_log when
    that log is there.
    """
    return _draft_intent(GOLDEN_RECORD.read_text(encoding="utf-8"))


def _strip_send_time_fields(logged: dict) -> dict:
    out = {k: v for k, v in logged.items()
           if k not in ("DocObjectCode", "NumAtCard", "TaxDate", "Comments")}
    out["DocumentLines"] = [{k: v for k, v in l.items() if k != "WTLiable"}
                            for l in logged["DocumentLines"]]
    return out


class DuplicateTest(unittest.TestCase):
    GRPO = {"DocEntry": 25714, "DocNum": 2026086625, "CardCode": "VENDA000939",
            "NumAtCard": "2606000806"}

    def test_no_duplicates(self):
        self.assertEqual([], rules.find_duplicates(self.GRPO, {}, {}, {}))

    def test_posted_invoice_with_the_same_ref_any_vendor(self):
        posted = {"2606000806": [{"DocEntry": 49999, "DocNum": 62608123, "CardCode": "VENDA000939",
                                  "DocDate": "2026-08-14", "DocTotal": 253110, "Cancelled": "tNO"}]}
        dups = rules.find_duplicates(self.GRPO, posted, {}, {})
        self.assertEqual(1, len(dups))
        self.assertEqual("posted", dups[0]["kind"])
        self.assertEqual(49999, dups[0]["docentry"])

    def test_a_cancelled_posted_invoice_is_not_a_duplicate(self):
        posted = {"2606000806": [{"DocEntry": 49999, "Cancelled": "tYES", "DocTotal": 1}]}
        self.assertEqual([], rules.find_duplicates(self.GRPO, posted, {}, {}))

    def test_open_draft_with_the_same_ref(self):
        drafts_ref = {"2606000806": [{"DocEntry": 54983, "CardCode": "VENDA000939",
                                      "DocTotal": 253110, "UserSign": 36,
                                      "DocumentStatus": "bost_Open"}]}
        dups = rules.find_duplicates(self.GRPO, {}, drafts_ref, {})
        self.assertEqual("draft-ref", dups[0]["kind"])
        self.assertEqual(36, dups[0]["owner"])

    def test_open_draft_on_this_grpo_under_a_different_ref(self):
        # The typo'd-ref case: the draft exists, keyed by GRPO, with a ref that
        # will never match. This is the check the batch leads with.
        by_base = {25714: [{"DocEntry": 54906, "CardCode": "VENDA000939", "NumAtCard": "typo",
                            "DocTotal": 253110, "UserSign": 7, "DocumentStatus": "bost_Open"}]}
        dups = rules.find_duplicates(self.GRPO, {}, {}, by_base)
        self.assertEqual("draft-grpo", dups[0]["kind"])
        self.assertEqual(54906, dups[0]["docentry"])

    def test_the_same_draft_is_reported_once(self):
        draft = {"DocEntry": 54983, "CardCode": "VENDA000939", "NumAtCard": "2606000806",
                 "DocTotal": 253110, "UserSign": 36, "DocumentStatus": "bost_Open"}
        dups = rules.find_duplicates(self.GRPO, {}, {"2606000806": [draft]}, {25714: [draft]})
        self.assertEqual(1, len(dups))

    def test_a_blank_ref_does_not_match_every_blank_ref(self):
        grpo = dict(self.GRPO, NumAtCard="")
        posted = {"": [{"DocEntry": 1, "Cancelled": "tNO", "DocTotal": 1}]}
        self.assertEqual([], rules.find_duplicates(grpo, posted, {}, {}))

    def test_reason_names_the_document_owner_and_amount(self):
        by_base = {25714: [{"DocEntry": 54906, "CardCode": "VENDA000939", "NumAtCard": "typo",
                            "DocTotal": 253110, "UserSign": 7, "DocumentStatus": "bost_Open"}]}
        reason = rules.duplicate_reason(rules.find_duplicates(self.GRPO, {}, {}, by_base))
        self.assertIn("54906", reason)
        self.assertIn("user 7", reason)
        self.assertIn("2,53,110", reason)

    def test_a_cancellation_mirror_with_no_Cancelled_key_is_not_a_duplicate(self):
        # The Service Layer omits Cancelled entirely on the mirror document SAP
        # creates when an invoice is cancelled (HANA stores 'C'). `!= "tYES"`
        # read that as live and held a bill nobody had booked.
        posted = {"2606000806": [{"DocEntry": 49999, "DocNum": 62608124,
                                  "CardCode": "VENDA000939", "DocTotal": -253110}]}
        self.assertEqual([], rules.find_duplicates(self.GRPO, posted, {}, {}))

    def test_a_live_posted_invoice_still_blocks(self):
        posted = {"2606000806": [{"DocEntry": 49999, "Cancelled": "tNO", "DocTotal": 1}]}
        self.assertEqual(1, len(rules.find_duplicates(self.GRPO, posted, {}, {})))

    def test_a_cancelled_draft_does_not_block(self):
        drafts = {"2606000806": [{"DocEntry": 54983, "Cancelled": "tYES", "DocTotal": 1}]}
        self.assertEqual([], rules.find_duplicates(self.GRPO, {}, drafts, {}))

    def test_the_index_is_keyed_by_the_normalized_reference(self):
        # `.2633100542` on the GRPO, `2633100542` on the invoice: one bill.
        grpo = dict(self.GRPO, NumAtCard=".2633100542")
        posted = {"2633100542": [{"DocEntry": 4, "Cancelled": "tNO", "DocTotal": 361250}]}
        self.assertEqual(1, len(rules.find_duplicates(grpo, posted, {}, {})))

    def test_a_match_on_another_vendors_card_says_so(self):
        posted = {"2606000806": [{"DocEntry": 49999, "CardCode": "VENDA000111",
                                  "Cancelled": "tNO", "DocTotal": 253110,
                                  "NumAtCard": "2606000806"}]}
        dups = rules.find_duplicates(self.GRPO, posted, {}, {})
        self.assertTrue(dups[0]["cross_vendor"])
        reason = rules.duplicate_reason(dups)
        self.assertIn("DIFFERENT vendor VENDA000111", reason)
        self.assertIn("wrong card", reason)

    def test_a_match_on_the_same_vendor_reads_as_a_plain_duplicate(self):
        posted = {"2606000806": [{"DocEntry": 49999, "CardCode": "VENDA000939",
                                  "Cancelled": "tNO", "DocTotal": 253110}]}
        dups = rules.find_duplicates(self.GRPO, posted, {}, {})
        self.assertFalse(dups[0]["cross_vendor"])
        self.assertNotIn("DIFFERENT", rules.duplicate_reason(dups))

    def test_the_reason_says_whether_the_blocking_draft_is_waiting_for_approval(self):
        by_base = {25714: [{"DocEntry": 54906, "CardCode": "VENDA000939", "DocTotal": 253110,
                            "UserSign": 7, "DocumentStatus": "bost_Open",
                            "AuthorizationStatus": "dasPending"}]}
        reason = rules.duplicate_reason(rules.find_duplicates(self.GRPO, {}, {}, by_base))
        self.assertIn("PENDING APPROVAL", reason)
        self.assertIn("bost_Open", reason)

    def test_the_reason_says_when_the_blocking_draft_was_abandoned(self):
        # 817 of the 1,053 open A/P drafts on Oil are dasCancelled (checked live
        # 2026-08-24) — somebody started the approval and gave up. The row is
        # still held, but the operator has to be able to see the difference
        # between that and a colleague's live work.
        by_base = {25714: [{"DocEntry": 54906, "CardCode": "VENDA000939", "DocTotal": 253110,
                            "UserSign": 7, "DocumentStatus": "bost_Open",
                            "AuthorizationStatus": "dasCancelled"}]}
        reason = rules.duplicate_reason(rules.find_duplicates(self.GRPO, {}, {}, by_base))
        self.assertIn("approval CANCELLED", reason)


class NormalizeRefTest(unittest.TestCase):
    def test_the_live_br_agrotech_pair_is_one_reference(self):
        self.assertEqual(rules.normalize_ref(".2633100542"), rules.normalize_ref("2633100542"))

    def test_leading_zeros_padding_and_case(self):
        self.assertEqual(rules.normalize_ref("0025"), rules.normalize_ref("25"))
        self.assertEqual(rules.normalize_ref("  26-27/1450 "), rules.normalize_ref("26-27/1450"))
        self.assertEqual(rules.normalize_ref("ab/1"), rules.normalize_ref("AB/1"))
        self.assertEqual(rules.normalize_ref("GST  12"), rules.normalize_ref("GST 12"))

    def test_it_does_NOT_flatten_the_middle_of_a_reference(self):
        # Two different bills that would collide under an over-eager rule.
        self.assertNotEqual(rules.normalize_ref("26-27/1450"), rules.normalize_ref("26271450"))
        self.assertNotEqual(rules.normalize_ref("1450"), rules.normalize_ref("14500"))

    def test_a_reference_of_only_zeros_keeps_them(self):
        self.assertEqual("000", rules.normalize_ref("000"))

    def test_blank_is_blank(self):
        for v in (None, "", "   ", "."):
            self.assertEqual("", rules.normalize_ref(v), repr(v))

    def test_the_spellings_asked_of_sap_keep_their_case(self):
        self.assertEqual(["ABC/12"], rules.ref_variants("ABC/12"))
        self.assertEqual([".2633100542", "2633100542"], rules.ref_variants(".2633100542"))


class RefCollisionTest(unittest.TestCase):
    # The live pair from the 2026-08-24 Oil scan: one BR Agrotech bill, two open
    # goods receipts, both READY, both for the same money. Approving both would
    # have created two A/P invoices for one bill.
    ROWS = [
        {"row": 12, "docentry": 25710, "docnum": 2026087710, "ref": ".2633100542"},
        {"row": 31, "docentry": 25911, "docnum": 2026087911, "ref": "2633100542"},
        {"row": 40, "docentry": 26001, "docnum": 2026088001, "ref": "OTHER/9"},
    ]

    def test_both_sides_of_a_collision_are_reported(self):
        found = rules.ref_collisions(self.ROWS)
        self.assertEqual({25710, 25911}, set(found))
        self.assertEqual([25911], [o["docentry"] for o in found[25710]])
        self.assertEqual([25710], [o["docentry"] for o in found[25911]])

    def test_a_row_with_a_unique_reference_is_untouched(self):
        self.assertNotIn(26001, rules.ref_collisions(self.ROWS))

    def test_blank_references_do_not_collide_with_each_other(self):
        rows = [{"row": 1, "docentry": 1, "docnum": 9, "ref": ""},
                {"row": 2, "docentry": 2, "docnum": 8, "ref": None}]
        self.assertEqual({}, rules.ref_collisions(rows))

    def test_the_reason_names_the_other_row_and_its_grpo(self):
        found = rules.ref_collisions(self.ROWS)
        reason = rules.collision_reason(".2633100542", found[25710])
        self.assertIn("row 31", reason)
        self.assertIn("2026087911", reason)
        self.assertIn("25911", reason)
        self.assertIn("cannot become two", reason)


class IntercompanyTest(unittest.TestCase):
    def test_a_jivo_named_vendor_is_intercompany(self):
        self.assertTrue(rules.is_intercompany("VENDA000001", "JIVO WELLNESS PVT LTD",
                                              "JIVO_MART_HANADB"))
        self.assertTrue(rules.is_intercompany("VENDA000483", "JIVO MART PVT LTD",
                                              "JIVO_OIL_HANADB"))

    def test_case_and_spacing_do_not_hide_it(self):
        self.assertTrue(rules.is_intercompany("X", "jivo wellness pvt ltd - dl", "JIVO_OIL_HANADB"))

    def test_the_c0005_group_cards_are_intercompany_by_code(self):
        self.assertTrue(rules.is_intercompany("CUSTA000606", "SOME OTHER NAME", "JIVO_OIL_HANADB"))
        self.assertTrue(rules.is_intercompany("CUSTA000926", "SOME OTHER NAME", "JIVO_MART_HANADB"))

    def test_a_group_card_of_another_company_is_not_matched_by_code(self):
        self.assertFalse(rules.is_intercompany("CUSTA001113", "OUTSIDE PARTY", "JIVO_MART_HANADB"))

    def test_an_ordinary_vendor_is_not(self):
        self.assertFalse(rules.is_intercompany("VENDA000939", "TPAC PACKAGING INDIA PVT LTD II",
                                               "JIVO_OIL_HANADB"))
        self.assertFalse(rules.is_intercompany("VENDA000636", "DELHI PUNJAB TRANSPORT CO",
                                               "JIVO_OIL_HANADB"))

    def test_akal_is_matched_too(self):
        self.assertTrue(rules.is_intercompany("VENDA009999", "AKAL AGRO FOODS", "JIVO_OIL_HANADB"))
        self.assertTrue(rules.is_intercompany("V", "SHRI AKAL TRADERS", "JIVO_OIL_HANADB"))

    def test_akal_inside_another_word_is_not_us(self):
        # PRAKALP and SAKAL are ordinary vendors. A substring test excluded them
        # from every batch, and an excluded vendor is a bill nobody books.
        for name in ("PRAKALP ENTERPRISES", "SAKAL PAPERS LTD", "MAKALU FOODS", "BHAKALI AGRO"):
            self.assertFalse(rules.is_intercompany("VENDA00X", name, "JIVO_OIL_HANADB"), name)


class TokensTest(unittest.TestCase):
    def test_matches_the_shipped_skill_helper(self):
        import re

        def legacy(s):
            return {t for t in re.findall(r"[a-z0-9.]+", (s or "").lower()) if len(t) > 1}

        for s in (None, "", "Carton Jivo 1 Ltr x 20 pcs 40 gm", "PET BOTTLE 1 LTR 26 GM"):
            self.assertEqual(legacy(s), rules.tokens(s), repr(s))


class SameRefTest(unittest.TestCase):
    """The comparison the OData filter cannot make."""

    def test_the_live_pair_from_oil_is_one_bill(self):
        # GRPOs 25710 / 25911, both BR Agrotech, both the same money.
        self.assertTrue(rules.same_ref("2633100542", ".2633100542"))
        self.assertTrue(rules.same_ref(".2633100542", "2633100542"))
        self.assertTrue(rules.same_ref("2633100542 ", "002633100542"))

    def test_different_bills_stay_different(self):
        self.assertFalse(rules.same_ref("26-27/1450", "26271450"))
        self.assertFalse(rules.same_ref("2633100542", "2633100543"))

    def test_nothing_is_never_the_same_as_nothing(self):
        # Two GRPOs with an empty (or punctuation-only) reference are not one bill.
        for pair in ((None, None), ("", ""), (".", "."), ("  ", "---")):
            self.assertFalse(rules.same_ref(*pair), pair)


class AdoptionEvidenceTest(unittest.TestCase):
    """--resume may adopt a draft only with evidence that this batch made it."""

    BATCH = "B260824-OIL-7F3A"

    def draft(self, **over):
        d = {"DocEntry": 55123, "UserSign": 7, "Comments": "keyed by hand",
             "DocumentLines": [{"BaseType": 20, "BaseEntry": 20001, "BaseLine": 0}]}
        d.update(over)
        return d

    def test_the_batch_id_in_remarks_is_evidence(self):
        d = self.draft(Comments=f"Based On Goods Receipt PO. {self.BATCH}", UserSign=42)
        why = rules.adoption_evidence(d, batch_id=self.BATCH, login_key=7, grpo_docentry=20001)
        self.assertIn(self.BATCH, why or "")

    def test_this_login_plus_this_grpo_is_evidence(self):
        why = rules.adoption_evidence(self.draft(), batch_id=self.BATCH, login_key=7,
                                      grpo_docentry=20001)
        self.assertIn("UserSign 7", why or "")

    def test_somebody_elses_draft_on_the_same_grpo_is_NOT_evidence(self):
        d = self.draft(UserSign=42)
        self.assertIsNone(rules.adoption_evidence(d, batch_id=self.BATCH, login_key=7,
                                                  grpo_docentry=20001))

    def test_our_login_on_a_different_grpo_is_NOT_evidence(self):
        d = self.draft(DocumentLines=[{"BaseType": 20, "BaseEntry": 29999, "BaseLine": 0}])
        self.assertIsNone(rules.adoption_evidence(d, batch_id=self.BATCH, login_key=7,
                                                  grpo_docentry=20001))

    def test_an_unknown_login_is_never_a_match(self):
        # The Users lookup failed. "No evidence available" must not read as "ours".
        self.assertIsNone(rules.adoption_evidence(self.draft(), batch_id=self.BATCH,
                                                  login_key=None, grpo_docentry=20001))

    def test_a_draft_with_no_lines_is_not_ours(self):
        self.assertIsNone(rules.adoption_evidence(self.draft(DocumentLines=[]),
                                                  batch_id=self.BATCH, login_key=7,
                                                  grpo_docentry=20001))

    def test_the_reason_for_a_foreign_draft_names_who_and_what(self):
        text = rules.foreign_draft_reason(self.draft(UserSign=42, DocNum=626085123,
                                                     NumAtCard="REF/1",
                                                     AuthorizationStatus="dasPending"))
        for token in ("55123", "626085123", "42", "dasPending", "PENDING APPROVAL"):
            self.assertIn(token, text)


class CellTextTest(unittest.TestCase):
    """Column Y must reach SAP as the text that is printed on the bill."""

    def test_a_string_passes_through_trimmed(self):
        self.assertEqual(("26-27/1450", None), rules.cell_text("  26-27/1450 ", "x"))

    def test_a_number_where_the_scan_had_text_falls_back_to_the_scan(self):
        ref, flag = rules.cell_text(2633100542, "REF/2026080001")
        self.assertEqual("REF/2026080001", ref)
        self.assertIn("column Y", flag)

    def test_a_number_with_nothing_to_fall_back_to_is_formatted_flat(self):
        for value in (2633100542, 2633100542.0, 2.633100542e9):
            ref, flag = rules.cell_text(value, 0)
            self.assertEqual("2633100542", ref, value)
            self.assertIn("column Y", flag)

    def test_a_big_number_never_travels_in_exponent_form(self):
        ref, _flag = rules.cell_text(1.2345678901234567e19, None)
        self.assertNotIn("e", ref.lower())

    def test_a_blank_is_still_blank(self):
        self.assertEqual(("", None), rules.cell_text("", "REF/1"))
        self.assertEqual(("", None), rules.cell_text(None, "REF/1"))


if __name__ == "__main__":
    unittest.main()


class NoteBudget(unittest.TestCase):
    """C-0027: a handwritten allocation word is a field value, not a remark."""

    def test_common_maps_to_factory_common(self):
        self.assertEqual(rules.budget_from_note("GATE ENTRY NO 136 | For oil plant | Common | Approved by Chopra sir"),
                         ("FACT_COM", "Common"))

    def test_handwriting_spellings(self):
        for word in ("common", "COMMON", "Comman", "Comon"):
            self.assertEqual(rules.budget_from_note(f"For oil plant {word}")[0], "FACT_COM", word)

    def test_no_allocation_word_means_inherit(self):
        self.assertIsNone(rules.budget_from_note("GE-2026-9529 | Veh HR69G3463 | e-Way 352314494869"))
        self.assertIsNone(rules.budget_from_note(""))
        self.assertIsNone(rules.budget_from_note(None))
        self.assertIsNone(rules.budget_from_note("uncommonly late"))   # word boundary

    def test_apply_budget_hits_every_line(self):
        payload = {"DocumentLines": [{"BaseLine": 0, "CostingCode3": "Factory"}, {"BaseLine": 1}]}
        out = rules.apply_budget(payload, "FACT_COM")
        self.assertIs(out, payload)
        self.assertEqual([r["CostingCode3"] for r in payload["DocumentLines"]], ["FACT_COM", "FACT_COM"])
