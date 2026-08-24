"""xlsx.py — the zero-dependency review workbook, written and read back.

Two things have to hold or the whole review loop is unsafe:
  1. what we write, we can read (round trip)
  2. what EXCEL writes, we can read — Excel re-saves the file its own way
     (sharedStrings, t="s", dates as serial numbers) and that is the version
     `acc batch send` will actually be handed.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from acc.apbatch import rules, xlsx

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def review_sheet() -> xlsx.SheetSpec:
    return xlsx.SheetSpec(
        name="Review",
        headers=["Row", "GRPO DocNum", "Taxable", "Status", "Approve? (yes/no)",
                 "Vendor bill date (TaxDate)", "Note"],
        rows=[[1, 2026086625, 214500.0, "READY", "", "2026-08-13", ""],
              [2, 2026086724, 4465530.0, "DUPLICATE", "", "2026-08-13", "already keyed by Neetu"]],
        widths=[5, 14, 14, 12, 16, 20, 30],
        styles={2: "inr"},
        editable={4, 5, 6},
        validations={4: ["yes", "no"]},
    )


class RoundTripTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "review.xlsx"
        self.addCleanup(self._tmp.cleanup)

    def test_write_then_read(self):
        xlsx.write_workbook(self.path, [review_sheet()])
        got = xlsx.read_workbook(self.path)
        self.assertEqual(["Review"], list(got))
        self.assertEqual(["Row", "GRPO DocNum", "Taxable", "Status", "Approve? (yes/no)",
                          "Vendor bill date (TaxDate)", "Note"], got["Review"][0])
        self.assertEqual([1, 2026086625, 214500.0, "READY", "", "2026-08-13", ""],
                         got["Review"][1])

    def test_numbers_stay_numbers_and_text_stays_text(self):
        xlsx.write_workbook(self.path, [review_sheet()])
        row = xlsx.read_workbook(self.path)["Review"][1]
        self.assertIsInstance(row[1], int)
        self.assertIsInstance(row[2], float)
        self.assertIsInstance(row[5], str)

    def test_a_long_docnum_is_not_rounded(self):
        # 2026086625 through a float would still be exact, but a 15-digit e-way
        # bill number would not; the writer must not float-ify an int.
        spec = xlsx.SheetSpec(name="S", headers=["n"], rows=[[352312357085123]])
        xlsx.write_workbook(self.path, [spec])
        self.assertEqual(352312357085123, xlsx.read_workbook(self.path)["S"][1][0])

    def test_three_sheets_keep_their_order_and_names(self):
        specs = [xlsx.SheetSpec(name=n, headers=["a"], rows=[[n]])
                 for n in ("Review", "Lines", "About")]
        xlsx.write_workbook(self.path, specs)
        self.assertEqual(["Review", "Lines", "About"], list(xlsx.read_workbook(self.path)))

    def test_blank_cells_come_back_blank_not_missing(self):
        spec = xlsx.SheetSpec(name="S", headers=["a", "b", "c"], rows=[["x", None, "z"]])
        xlsx.write_workbook(self.path, [spec])
        self.assertEqual(["x", "", "z"], xlsx.read_workbook(self.path)["S"][1])

    def test_xml_hostile_text_survives(self):
        nasty = 'M/S <ARORA> & SONS "PVT" LTD'
        spec = xlsx.SheetSpec(name="S", headers=["a"], rows=[[nasty]])
        xlsx.write_workbook(self.path, [spec])
        self.assertEqual(nasty, xlsx.read_workbook(self.path)["S"][1][0])

    def test_the_rupee_sign_and_middots_survive(self):
        text = "0: PM0000851 … 42,900 @5.00 · ₹2,53,110.00"
        spec = xlsx.SheetSpec(name="S", headers=["a"], rows=[[text]])
        xlsx.write_workbook(self.path, [spec])
        self.assertEqual(text, xlsx.read_workbook(self.path)["S"][1][0])

    def test_every_xml_part_is_well_formed(self):
        # Excel refuses the whole file for one stray character, and the operator
        # then just sees "we found a problem with some content".
        from xml.etree import ElementTree as ET
        xlsx.write_workbook(self.path, [review_sheet()])
        with zipfile.ZipFile(self.path) as z:
            for name in z.namelist():
                if name.endswith((".xml", ".rels")):
                    ET.fromstring(z.read(name))

    def test_it_is_a_real_zip_with_the_parts_excel_expects(self):
        xlsx.write_workbook(self.path, [review_sheet()])
        with zipfile.ZipFile(self.path) as z:
            names = set(z.namelist())
        for part in ("[Content_Types].xml", "_rels/.rels", "xl/workbook.xml",
                     "xl/_rels/workbook.xml.rels", "xl/styles.xml",
                     "xl/worksheets/sheet1.xml"):
            self.assertIn(part, names)


class SheetFeaturesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "review.xlsx"
        self.addCleanup(self._tmp.cleanup)
        xlsx.write_workbook(self.path, [review_sheet()])
        with zipfile.ZipFile(self.path) as z:
            self.sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            self.styles = z.read("xl/styles.xml").decode("utf-8")

    def test_header_row_is_frozen(self):
        self.assertIn('<pane ySplit="1" topLeftCell="A2"', self.sheet)
        self.assertIn('state="frozen"', self.sheet)

    def test_column_widths_are_set(self):
        self.assertIn("<cols>", self.sheet)
        self.assertIn('customWidth="1"', self.sheet)

    def test_yes_no_validation_is_on_the_approve_column(self):
        self.assertIn("<dataValidations", self.sheet)
        self.assertIn('type="list"', self.sheet)
        self.assertIn('<formula1>"yes,no"</formula1>', self.sheet)
        self.assertIn('sqref="E2:E3"', self.sheet)      # column E = Approve?, 2 rows

    def test_the_sheet_is_protected_but_sorting_is_allowed(self):
        self.assertIn("<sheetProtection", self.sheet)
        self.assertIn('sheet="1"', self.sheet)
        self.assertIn('sort="0"', self.sheet)
        self.assertIn('autoFilter="0"', self.sheet)

    def test_indian_number_format_is_declared(self):
        self.assertIn("##0.00", self.styles)
        self.assertIn("numFmt", self.styles)

    def test_editable_cells_are_unlocked_and_yellow(self):
        self.assertIn('<protection locked="0"/>', self.styles)
        self.assertIn("FFFFF2CC", self.styles.upper())   # the yellow

    def test_locked_cells_are_locked(self):
        self.assertIn('<protection locked="1"/>', self.styles)

    def test_editable_text_cells_carry_the_text_format(self):
        # numFmtId 49 = "@". Without it Excel eats a leading zero on a vendor
        # reference and reformats a typed date into its own locale.
        self.assertIn('numFmtId="49"', self.styles)

    def test_locked_data_cells_carry_the_grey_the_about_sheet_promises(self):
        # The About sheet tells the operator "everything grey is checked against
        # SAP again". Locked cells used to be white, which made the promise a
        # sentence rather than a signal.
        self.assertIn("FFF5F5F5", self.styles.upper())


class PerRowLockingTest(unittest.TestCase):
    """Editable is a property of a CELL, not of a column.

    Row 1 is READY, row 2 is DUPLICATE. Only row 1's V-Z may be typed in: a
    yellow Approve? box on a row that can never be sent invites an operator to
    fill fifty of them and be told no fifty times.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "review.xlsx"
        self.addCleanup(self._tmp.cleanup)
        spec = review_sheet()
        spec.editable_rows = [0]                     # only the READY row
        xlsx.write_workbook(self.path, [spec])
        with zipfile.ZipFile(self.path) as z:
            self.sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")

    def style_of(self, ref):
        m = re.search(r'<c r="%s" s="(\d+)"' % ref, self.sheet)
        self.assertIsNotNone(m, f"no cell {ref} in the sheet")
        return int(m.group(1))

    def test_the_ready_rows_approve_cell_is_the_editable_style(self):
        self.assertEqual(xlsx.S_EDIT_LIST, self.style_of("E2"))

    def test_the_duplicate_rows_approve_cell_is_locked(self):
        self.assertEqual(xlsx.S_TEXT, self.style_of("E3"))
        self.assertNotEqual(xlsx.S_EDIT_LIST, self.style_of("E3"))
        self.assertNotEqual(xlsx.S_EDIT, self.style_of("E3"))

    def test_the_duplicate_rows_other_editable_cells_are_locked_too(self):
        for ref in ("F3", "G3"):
            self.assertEqual(xlsx.S_TEXT, self.style_of(ref), ref)

    def test_without_editable_rows_every_row_is_editable(self):
        path = self.path.with_name("all.xlsx")
        xlsx.write_workbook(path, [review_sheet()])
        with zipfile.ZipFile(path) as z:
            sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn('<c r="E3" s="%d"' % xlsx.S_EDIT_LIST, sheet)


class ControlCharacterTest(unittest.TestCase):
    """Excel refuses to open a workbook containing a control character.

    SAP text carries them (a description pasted out of a PDF). One byte in one
    cell would make the whole batch unreadable, so they are dropped — and
    dropped in clean_text too, because the sidecar records the same values and
    the tamper check compares the two.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "review.xlsx"
        self.addCleanup(self._tmp.cleanup)

    def test_a_control_character_does_not_reach_the_file(self):
        spec = xlsx.SheetSpec(name="Review", headers=["A"],
                              rows=[["PET\x01BOTTLE\x1f 1 LTR"]])
        xlsx.write_workbook(self.path, [spec])
        with zipfile.ZipFile(self.path) as z:
            raw = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertNotIn("\x01", raw)
        self.assertNotIn("\x1f", raw)
        self.assertEqual("PETBOTTLE 1 LTR", xlsx.read_workbook(self.path)["Review"][1][0])

    def test_tabs_and_newlines_survive(self):
        self.assertEqual("a\tb\nc", xlsx.clean_text("a\tb\nc"))

    def test_clean_text_leaves_numbers_alone(self):
        self.assertEqual(214500.0, xlsx.clean_text(214500.0))
        self.assertEqual(25714, xlsx.clean_text(25714))

    def test_the_sheet_and_the_sidecar_are_cleaned_the_same_way(self):
        dirty = "REF\x0100123"
        spec = xlsx.SheetSpec(name="Review", headers=["A"], rows=[[xlsx.clean_text(dirty)]])
        xlsx.write_workbook(self.path, [spec])
        from_sheet = xlsx.read_workbook(self.path)["Review"][1][0]
        self.assertTrue(xlsx.same_cell(from_sheet, xlsx.clean_text(dirty)))


class ThirdPartyReaderTest(unittest.TestCase):
    """A real spreadsheet library must accept the file we hand to Excel.

    openpyxl is NOT a dependency of anything shipped — it is not installed on
    the operator boxes, which is the whole reason xlsx.py exists. It is used
    here, when it happens to be present on a developer machine, as the closest
    available stand-in for Excel opening the file.
    """

    def setUp(self):
        try:
            import openpyxl                       # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not installed — this check is developer-only")
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "review.xlsx"
        self.addCleanup(self._tmp.cleanup)
        xlsx.write_workbook(self.path, [review_sheet()])

    def test_openpyxl_reads_the_values_back(self):
        import openpyxl
        wb = openpyxl.load_workbook(self.path)
        ws = wb["Review"]
        self.assertEqual("GRPO DocNum", ws["B1"].value)
        self.assertEqual(2026086625, ws["B2"].value)
        self.assertEqual(214500.0, ws["C2"].value)
        self.assertEqual("READY", ws["D2"].value)

    def test_openpyxl_sees_the_protection_and_the_unlocked_cells(self):
        import openpyxl
        wb = openpyxl.load_workbook(self.path)
        ws = wb["Review"]
        self.assertTrue(ws.protection.sheet)
        self.assertTrue(ws["B2"].protection.locked)          # grey, locked
        self.assertFalse(ws["E2"].protection.locked)         # yellow, editable

    def test_openpyxl_sees_the_frozen_header_and_the_indian_format(self):
        import openpyxl
        wb = openpyxl.load_workbook(self.path)
        ws = wb["Review"]
        self.assertEqual("A2", ws.freeze_panes)
        self.assertIn("##0.00", ws["C2"].number_format)


class ExcelResavedTest(unittest.TestCase):
    """The file after Excel has had it: sharedStrings, t="s", a date as a serial."""

    def setUp(self):
        self.path = FIXTURES / "excel_resaved.xlsx"
        self.assertTrue(self.path.exists(), "fixture missing — build it with acc/tests/fixtures/make_excel_fixture.py")
        self.book = xlsx.read_workbook(self.path)

    def test_shared_strings_are_resolved(self):
        self.assertEqual(["Row", "GRPO DocEntry", "Approve? (yes/no)", "TDS (yes/no)",
                          "Vendor bill date (TaxDate)", "Vendor ref (NumAtCard)"],
                         self.book["Review"][0])

    def test_an_operator_edit_reads_back(self):
        row = self.book["Review"][1]
        self.assertEqual("yes", row[2])
        self.assertEqual("no", row[3])

    def test_a_date_excel_turned_into_a_serial_still_parses(self):
        row = self.book["Review"][1]
        self.assertEqual(46247, row[4])
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date(row[4]))

    def test_a_date_left_as_text_still_parses(self):
        row = self.book["Review"][2]
        self.assertEqual(dt.date(2026, 8, 13), rules.parse_sheet_date(row[4]))

    def test_a_reference_with_a_leading_zero_is_not_eaten(self):
        self.assertEqual("2606000806", self.book["Review"][1][5])
        self.assertEqual("0042/26-27", self.book["Review"][2][5])

    def test_the_key_column_is_still_the_key(self):
        self.assertEqual([25714, 25936], [r[1] for r in self.book["Review"][1:]])

    def test_a_second_sheet_is_read_too(self):
        self.assertIn("About", self.book)
        self.assertEqual(["batch_id", "B240824-OIL-7F3A"], self.book["About"][0])


class TamperHelperTest(unittest.TestCase):
    def test_column_letters(self):
        self.assertEqual("A", xlsx.column_letter(0))
        self.assertEqual("Z", xlsx.column_letter(25))
        self.assertEqual("AA", xlsx.column_letter(26))
        self.assertEqual("AB", xlsx.column_letter(27))

    def test_column_index(self):
        for i in (0, 1, 25, 26, 27, 51, 52):
            self.assertEqual(i, xlsx.column_index(xlsx.column_letter(i)))

    def test_cell_reference(self):
        self.assertEqual("V2", xlsx.cell_ref(21, 2))     # column V, sheet row 2
        self.assertEqual("A1", xlsx.cell_ref(0, 1))

    def test_same_cell_normalizes_numbers_and_whitespace(self):
        self.assertTrue(xlsx.same_cell(214500, "214500.00"))
        self.assertTrue(xlsx.same_cell(214500.004, 214500.0))
        self.assertTrue(xlsx.same_cell(" READY ", "READY"))
        self.assertTrue(xlsx.same_cell(None, ""))
        self.assertFalse(xlsx.same_cell(214500, 214501))
        self.assertFalse(xlsx.same_cell("READY", "DUPLICATE"))

    def test_same_cell_does_not_call_a_number_equal_to_its_name(self):
        self.assertFalse(xlsx.same_cell(0, "zero"))

    def test_a_date_excel_turned_into_a_serial_is_still_the_same_date(self):
        # The tamper check compares the sheet against the sidecar. Column D is
        # written "2026-08-14"; an operator who clicks in it and presses Enter
        # gets 46248 back. That is Excel, not meddling, and refusing the row as
        # TAMPERED for it would be a false accusation.
        self.assertTrue(xlsx.same_cell("2026-08-14", 46248))
        self.assertTrue(xlsx.same_cell(46248, "2026-08-14"))
        self.assertTrue(xlsx.same_cell(46248.0, "2026-08-14"))

    def test_a_serial_for_a_DIFFERENT_day_is_still_a_difference(self):
        self.assertFalse(xlsx.same_cell("2026-08-14", 46249))
        self.assertFalse(xlsx.same_cell("2026-08-14", 1))        # not a plausible serial

    def test_a_date_against_a_date_is_unaffected(self):
        self.assertTrue(xlsx.same_cell("2026-08-14", "2026-08-14"))
        self.assertFalse(xlsx.same_cell("2026-08-14", "2026-08-15"))

    def test_infinity_and_nan_are_compared_as_words_and_never_raise(self):
        # Decimal("inf") parses happily and then explodes in round(). A cell
        # holding "inf" is a word; the comparison has to answer, not crash the
        # whole send.
        self.assertFalse(xlsx.same_cell("inf", "Infinity"))
        self.assertTrue(xlsx.same_cell("inf", "inf"))
        self.assertTrue(xlsx.same_cell("NaN", "NaN"))
        self.assertFalse(xlsx.same_cell("nan", 5))
        self.assertFalse(xlsx.same_cell(float("inf"), 5))
        self.assertFalse(xlsx.same_cell(float("nan"), 5))


if __name__ == "__main__":
    unittest.main()
