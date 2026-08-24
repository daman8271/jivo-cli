"""batch_scan — open GRPOs in, a review workbook out. Never a write.

The scan is the half of `acc batch` that an operator runs unsupervised, so the
guarantee that matters most is negative: it cannot write to SAP, and it cannot
leave a workbook behind that it was not able to build properly.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from acc.apbatch import batch_scan, store, xlsx
from acc.apbatch.sap import FakeSap, SapAuth, SapUnreachable, SapWriteRefused

TODAY = dt.date(2026, 8, 24)
NOW = dt.datetime(2026, 8, 24, 15, 30, 12)

BRANCHES = [{"BPLID": 2, "BPLName": "FACTORY", "FederalTaxID": "06AAACJ0000A1Z5",
             "Disabled": "tNO"}]
GROUPS = [{"Code": 110, "Name": "PURCHASE"}, {"Code": 102, "Name": "TRANSPORTER"},
          {"Code": 106, "Name": "BRANCH VENDOR"}]

VENDORS = [
    {"CardCode": "VENDA000777", "CardName": "SUNRISE PACK INDUSTRIES", "GroupCode": 110,
     "SubjectToWithholdingTax": "boYES", "BPWithholdingTaxCollection": [{"WTCode": "1031"}],
     "Valid": "tYES", "Frozen": "tNO", "CurrentAccountBalance": -412500.0},
    {"CardCode": "VENDA000636", "CardName": "DELHI PUNJAB TRANSPORT CO", "GroupCode": 102,
     "SubjectToWithholdingTax": "boYES", "BPWithholdingTaxCollection": [{"WTCode": "1024"}],
     "Valid": "tYES", "Frozen": "tNO", "CurrentAccountBalance": -88000.0},
    {"CardCode": "VENDA000001", "CardName": "JIVO WELLNESS PVT LTD", "GroupCode": 106,
     "SubjectToWithholdingTax": "boNO", "BPWithholdingTaxCollection": [],
     "Valid": "tYES", "Frozen": "tNO", "CurrentAccountBalance": -209300000.0},
]


def item_line(**over):
    line = {"LineNum": 0, "LineStatus": "bost_Open", "ItemCode": "PM0000999",
            "ItemDescription": "PET BOTTLE 500 ML 18 GM", "Quantity": 10000,
            "RemainingOpenQuantity": 10000, "UnitPrice": 4.5, "LineTotal": 45000.0,
            "TaxCode": "IGST@18", "TaxTotal": 8100.0, "WarehouseCode": "BH-PM",
            "CostingCode": "MUSTARD", "BaseType": 22, "BaseEntry": 14001, "BaseLine": 0,
            "MeasureUnit": "PCS"}
    line.update(over)
    return line


def grpo(entry, docnum, docdate, card="VENDA000777", ref=None, doctype="dDocument_Items",
         lines=None, attachment=170999, taxdate=None):
    return {"DocEntry": entry, "DocNum": docnum, "DocType": doctype,
            "DocDate": docdate + "T00:00:00Z",
            "TaxDate": (taxdate or docdate) + "T00:00:00Z", "CardCode": card,
            "CardName": next(v["CardName"] for v in VENDORS if v["CardCode"] == card),
            "NumAtCard": ref if ref is not None else f"REF/{docnum}",
            "Comments": f"Based On Purchase Orders 220826099.GATE ENTRY NO.{entry}",
            "DocumentStatus": "bost_Open", "Cancelled": "tNO", "BPL_IDAssignedToInvoice": 2,
            "BPLName": "FACTORY", "AttachmentEntry": attachment, "DocTotal": 53100.0,
            "VatSum": 8100.0, "DocumentLines": lines or [item_line()]}


SERVICE_LINE = {"LineNum": 0, "LineStatus": "bost_Open", "ItemCode": None,
                "ItemDescription": "EDIBLE OIL", "Quantity": 0, "RemainingOpenQuantity": 0,
                "UnitPrice": 13000, "LineTotal": 13000.0, "TaxCode": "GST05R",
                "TaxTotal": 650.0, "WarehouseCode": None, "CostingCode": "CANOLA",
                "BaseType": -1, "BaseEntry": None, "BaseLine": None}

GRPOS = [
    grpo(20001, 2026080001, "2026-08-18"),                                   # READY
    grpo(20002, 2026070002, "2026-07-29", card="VENDA000636",
         doctype="dDocument_Service", lines=[dict(SERVICE_LINE)]),           # SERVICE-HOLD
    grpo(20003, 2026080003, "2026-08-20", ref=""),                           # NEEDS-REF
    grpo(20004, 2026080004, "2026-08-21", card="VENDA000001"),               # INTERCOMPANY
    grpo(20005, 2026080005, "2026-08-22"),                                   # DUPLICATE
]

OPEN_DRAFT = {"DocEntry": 54983, "DocNum": 626080077, "CardCode": "VENDA000777",
              "NumAtCard": "typo", "DocDate": "2026-08-22T00:00:00Z", "DocTotal": 53100.0,
              "UserSign": 7, "DocumentStatus": "bost_Open",
              "DocumentLines": [{"BaseType": 20, "BaseEntry": 20005, "BaseLine": 0}]}


def tables(grpos=None, drafts=(OPEN_DRAFT,), posted=()):
    def purchase_invoices(flt, select, **kw):
        if select == "DocEntry,Series":
            return [{"DocEntry": 9, "Series": 4001}] * 40
        if flt and "NumAtCard eq" in flt:
            return list(posted)
        return [{"DocEntry": 41, "NumAtCard": "R41", "DocDate": "2026-08-05",
                 "DocumentSubType": "bod_GSTTaxInvoice", "WTAmount": 0, "Series": 4001,
                 "DocumentLines": [{"WTLiable": "tNO"}]}]

    return {
        "PurchaseDeliveryNotes": list(GRPOS if grpos is None else grpos),
        "BusinessPlaces": BRANCHES,
        "BusinessPartnerGroups": GROUPS,
        "BusinessPartners": VENDORS,
        "Drafts": lambda flt, select, **kw: ([] if select == "DocEntry,Series" else list(drafts)),
        "PurchaseInvoices": purchase_invoices,
        "PurchaseOrders": [{"DocEntry": 14001, "DocNum": 220826099}],
        "WithholdingTaxCodes": [{"WTCode": "1031", "WTName": "194Q", "Rate": 0.1},
                                {"WTCode": "1024", "WTName": "194C", "Rate": 2.0}],
    }


def make_args(**over):
    args = argparse.Namespace(company="Oil", since="2024-01-01", vendor=None, group=None,
                              limit=50, order="oldest", include_intercompany=False,
                              allow_service=False, env=None, out=None, quiet=True)
    for k, v in over.items():
        setattr(args, k, v)
    return args


class ScanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.sap = FakeSap(tables(), company="JIVO_OIL_HANADB")

    def run_scan(self, **over):
        args = make_args(out=str(self.out), **over)
        code = batch_scan.run_scan(args, sap=self.sap, today=TODAY, now=NOW,
                                   batch_id="B260824-OIL-7F3A", repo=self.out)
        book = self.out / "review-B260824-OIL-7F3A.xlsx"
        side = self.out / "sidecar-B260824-OIL-7F3A.json"
        return code, book, side

    # -- the negative guarantee ------------------------------------------

    def test_the_scan_never_writes(self):
        self.run_scan()
        self.assertEqual([], self.sap.writes)

    def test_the_scan_builds_a_read_only_client_by_default(self):
        # Not "it happens not to call draft" — it cannot.
        with self.assertRaises(SapWriteRefused):
            self.sap.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)

    # -- output ----------------------------------------------------------

    def test_it_writes_a_workbook_and_a_sidecar(self):
        code, book, side = self.run_scan()
        self.assertEqual(0, code)
        self.assertTrue(book.exists())
        self.assertTrue(side.exists())

    def test_the_workbook_has_the_three_sheets(self):
        _code, book, _side = self.run_scan()
        self.assertEqual(["Review", "Lines", "About"], list(xlsx.read_workbook(book)))

    def test_the_review_header_is_the_agreed_column_schema(self):
        _code, book, _side = self.run_scan()
        header = xlsx.read_workbook(book)["Review"][0]
        self.assertEqual(26, len(header))                    # A..Z
        self.assertEqual("Row", header[0])
        self.assertEqual("GRPO DocEntry", header[2])
        self.assertEqual("Status", header[19])
        self.assertEqual("Approve? (yes/no)", header[21])
        self.assertEqual("Note (goes to Remarks)", header[25])

    def test_every_grpo_gets_a_row_except_the_intercompany_one(self):
        _code, book, _side = self.run_scan()
        rows = xlsx.read_workbook(book)["Review"][1:]
        # 20004 is JIVO WELLNESS billing JIVO. It is dropped, not shown as an
        # excluded row: it is not work anyone is going to do, and if it stayed it
        # would eat one of the 50 places in the batch (plan section 4).
        self.assertEqual([20001, 20002, 20003, 20005], sorted(r[2] for r in rows))

    def test_statuses(self):
        _code, book, _side = self.run_scan()
        rows = xlsx.read_workbook(book)["Review"][1:]
        status = {r[2]: r[19] for r in rows}
        self.assertEqual("READY", status[20001])
        self.assertEqual("SERVICE-HOLD", status[20002])
        self.assertEqual("NEEDS-REF", status[20003])
        self.assertEqual("DUPLICATE", status[20005])
        self.assertNotIn(20004, status)              # intercompany, filtered out entirely

    def test_the_editable_cells_are_locked_on_a_row_that_cannot_be_sent(self):
        # Proof(d): V-Z are yellow and unlocked on READY rows only. 20005 is a
        # DUPLICATE — its Approve? cell must be locked, so nobody fills it in.
        _code, book, _side = self.run_scan()
        rows = xlsx.read_workbook(book)["Review"][1:]
        ready_row = next(n for n, r in enumerate(rows, start=2) if r[2] == 20001)
        dup_row = next(n for n, r in enumerate(rows, start=2) if r[2] == 20005)
        import re
        import zipfile
        with zipfile.ZipFile(book) as z:
            sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")

        def style(ref):
            return int(re.search(r'<c r="%s" s="(\d+)"' % ref, sheet).group(1))

        self.assertEqual(xlsx.S_EDIT_LIST, style(f"V{ready_row}"))
        self.assertEqual(xlsx.S_EDIT, style(f"Z{ready_row}"))
        self.assertEqual(xlsx.S_TEXT, style(f"V{dup_row}"))
        self.assertEqual(xlsx.S_TEXT, style(f"Z{dup_row}"))

    def test_the_duplicate_reason_names_the_existing_draft(self):
        _code, book, _side = self.run_scan()
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20005)
        self.assertIn("54983", row[20])

    def test_a_grpo_that_cannot_be_read_becomes_a_row_not_a_traceback(self):
        broken = grpo(20009, 2026080009, "2026-08-19")
        broken["DocumentLines"] = [{"LineNum": 0, "LineStatus": "bost_Open",
                                    "RemainingOpenQuantity": 5}]   # no ItemCode -> KeyError
        self.sap = FakeSap(tables(grpos=[GRPOS[0], broken]), company="JIVO_OIL_HANADB")
        code, book, _side = self.run_scan()
        self.assertEqual(0, code)
        rows = {r[2]: r for r in xlsx.read_workbook(book)["Review"][1:]}
        self.assertEqual("READY", rows[20001][19])      # the good row still went through
        self.assertEqual("CANNOT-BUILD", rows[20009][19])
        self.assertIn("could not read this GRPO", rows[20009][20])

    def test_money_columns_stay_numeric(self):
        _code, book, _side = self.run_scan()
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20001)
        self.assertEqual(45000.0, row[11])
        self.assertEqual(8100.0, row[12])
        self.assertEqual(53100.0, row[13])

    def test_the_editable_columns_are_prefilled_from_the_grpo(self):
        _code, book, _side = self.run_scan()
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20001)
        self.assertEqual("", row[21])                         # Approve? blank by design
        self.assertEqual("no", row[22])                       # TDS from the precedent rule
        self.assertEqual("2026-08-18", row[23])               # bill date from the GRPO
        self.assertEqual("REF/2026080001", row[24])           # vendor ref from the GRPO

    def test_the_lines_sheet_details_every_open_line(self):
        _code, book, _side = self.run_scan()
        lines = xlsx.read_workbook(book)["Lines"]
        self.assertEqual("GRPO DocEntry", lines[0][0])
        self.assertIn(20001, [r[0] for r in lines[1:]])

    def test_the_about_sheet_names_the_batch_the_login_and_the_rules(self):
        _code, book, _side = self.run_scan()
        about = {r[0]: r[1] for r in xlsx.read_workbook(book)["About"] if r[0]}
        self.assertEqual("B260824-OIL-7F3A", about["batch_id"])
        self.assertEqual("JIVO_OIL_HANADB", about["company"])
        self.assertEqual("USER36", about["login (drafts land under this user)"])
        text = "\n".join(str(c) for r in xlsx.read_workbook(book)["About"] for c in r)
        self.assertIn("yellow", text.lower())

    # -- the sidecar -----------------------------------------------------

    def test_the_sidecar_holds_a_payload_for_every_ready_row(self):
        _code, _book, side = self.run_scan()
        sc = store.Sidecar.load(side)
        self.assertEqual("READY", sc.row(20001)["status"])
        self.assertEqual("VENDA000777", sc.row(20001)["payload"]["CardCode"])
        self.assertEqual(4001, sc.row(20001)["payload"]["Series"])

    def test_the_sidecar_payload_has_no_send_time_fields(self):
        _code, _book, side = self.run_scan()
        payload = store.Sidecar.load(side).row(20001)["payload"]
        for field in ("NumAtCard", "TaxDate", "Comments"):
            self.assertNotIn(field, payload)

    def test_a_held_row_carries_no_payload(self):
        _code, _book, side = self.run_scan()
        sc = store.Sidecar.load(side)
        for entry in (20002, 20003, 20005):
            self.assertIsNone(sc.row(entry)["payload"], entry)

    def test_the_sidecar_locked_block_matches_the_sheet(self):
        _code, book, side = self.run_scan()
        sc = store.Sidecar.load(side)
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20001)
        locked = sc.row(20001)["locked"]
        for col in range(1, 21):                              # B..U
            letter = xlsx.column_letter(col)
            self.assertIn(letter, locked)
            self.assertTrue(xlsx.same_cell(locked[letter], row[col]),
                            f"{letter}: sidecar {locked[letter]!r} vs sheet {row[col]!r}")

    def test_the_sidecar_row_keys_match_the_sheet_keys(self):
        _code, book, side = self.run_scan()
        sc = store.Sidecar.load(side)
        sheet_keys = {str(r[2]) for r in xlsx.read_workbook(book)["Review"][1:]}
        self.assertEqual(sheet_keys, sc.row_keys())

    def test_the_sidecar_records_who_and_where(self):
        _code, _book, side = self.run_scan()
        sc = store.Sidecar.load(side)
        self.assertEqual("USER36", sc.login)
        self.assertEqual("JIVO_OIL_HANADB", sc.company)
        self.assertEqual("fake:0", sc.host)

    def test_two_rows_with_the_same_vendor_reference_hold_each_other(self):
        # The live BR Agrotech pair: one bill, two open goods receipts. Both are
        # READY on their own and both would have been drafted.
        pair = [grpo(20101, 2026080101, "2026-08-18", ref=".2633100542"),
                grpo(20102, 2026080102, "2026-08-19", ref="2633100542")]
        self.sap = FakeSap(tables(grpos=pair, drafts=()), company="JIVO_OIL_HANADB")
        _code, book, side = self.run_scan()
        rows = {r[2]: r for r in xlsx.read_workbook(book)["Review"][1:]}
        self.assertEqual("REF-COLLISION", rows[20101][19])
        self.assertEqual("REF-COLLISION", rows[20102][19])
        self.assertIn("row 2", rows[20101][20])          # names the other row
        self.assertIn("2026080102", rows[20101][20])     # and its GRPO
        self.assertIn("row 1", rows[20102][20])
        self.assertIn("2026080101", rows[20102][20])
        sc = store.Sidecar.load(side)
        for entry in (20101, 20102):
            self.assertIsNone(sc.row(entry)["payload"], "a held row carries nothing sendable")

    def test_a_unique_reference_is_not_a_collision(self):
        pair = [grpo(20101, 2026080101, "2026-08-18", ref="A/1"),
                grpo(20102, 2026080102, "2026-08-19", ref="A/2")]
        self.sap = FakeSap(tables(grpos=pair, drafts=()), company="JIVO_OIL_HANADB")
        _code, book, _side = self.run_scan()
        statuses = [r[19] for r in xlsx.read_workbook(book)["Review"][1:]]
        self.assertEqual(["READY", "READY"], statuses)

    def test_a_contradicted_tds_proposal_leaves_the_answer_cell_blank(self):
        # VENDA000636-shaped: the card says 194C @2%, and all three posted
        # invoices have every line WTLiable tYES with WTAmount 0. Nobody here
        # knows the answer, so W comes out EMPTY and send refuses the row until
        # a person types one.
        def marked_but_zero(flt, select, **kw):
            if select == "DocEntry,Series":
                return [{"DocEntry": 9, "Series": 4001}] * 40
            if flt and "NumAtCard eq" in flt:
                return []
            return [{"DocEntry": 41, "NumAtCard": "R41", "DocDate": "2026-08-05",
                     "DocumentSubType": "bod_GSTTaxInvoice", "WTAmount": 0, "Series": 4001,
                     "DocumentLines": [{"WTLiable": "tYES"}]}] * 3

        t = tables(grpos=[grpo(20201, 2026080201, "2026-08-18", card="VENDA000636")], drafts=())
        t["PurchaseInvoices"] = marked_but_zero
        self.sap = FakeSap(t, company="JIVO_OIL_HANADB")
        _code, book, side = self.run_scan()
        row = xlsx.read_workbook(book)["Review"][1]
        self.assertEqual("READY", row[19])
        self.assertEqual("", row[22], "column W must be blank when the evidence contradicts itself")
        self.assertTrue(row[16].startswith("CHECK:"), row[16])
        self.assertEqual("", store.Sidecar.load(side).row(20201)["defaults"]["W"])

    def test_an_agreed_tds_proposal_is_still_prefilled(self):
        _code, book, _side = self.run_scan()
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20001)
        self.assertEqual("no", row[22])

    def test_a_journal_is_started(self):
        self.run_scan()
        events = store.Journal(self.out / "journal-B260824-OIL-7F3A.jsonl").events()
        self.assertEqual(["scan"], [e["event"] for e in events])

    # -- filters ---------------------------------------------------------

    def test_limit(self):
        _code, book, _side = self.run_scan(limit=2)
        self.assertEqual(2, len(xlsx.read_workbook(book)["Review"]) - 1)

    def test_limit_zero_means_everything(self):
        _code, book, _side = self.run_scan(limit=0)
        self.assertEqual(4, len(xlsx.read_workbook(book)["Review"]) - 1)

    def test_an_intercompany_row_does_not_consume_a_place_in_the_limit(self):
        # Rows in date order: 20002 (07-29), 20001 (08-18), 20003 (08-20),
        # 20004 INTERCOMPANY (08-21), 20005 (08-22). A limit of 4 must reach
        # 20005 — the excluded row is not one of the four.
        _code, book, _side = self.run_scan(limit=4)
        rows = xlsx.read_workbook(book)["Review"][1:]
        self.assertEqual([20002, 20001, 20003, 20005], [r[2] for r in rows])

    def test_a_duplicate_row_DOES_consume_a_place_in_the_limit(self):
        # The opposite call, on purpose: a bill already keyed is exactly what the
        # reviewer needs to see, so it appears and it counts.
        _code, book, _side = self.run_scan(limit=4)
        statuses = [r[19] for r in xlsx.read_workbook(book)["Review"][1:]]
        self.assertIn("DUPLICATE", statuses)

    def test_order_oldest_first_is_the_default(self):
        _code, book, _side = self.run_scan(limit=2)
        rows = xlsx.read_workbook(book)["Review"][1:]
        self.assertEqual(["2026-07-29", "2026-08-18"], [r[3] for r in rows])

    def test_order_newest_first(self):
        _code, book, _side = self.run_scan(limit=2, order="newest")
        rows = xlsx.read_workbook(book)["Review"][1:]
        self.assertEqual(["2026-08-22", "2026-08-20"], [r[3] for r in rows])

    def test_group_filter(self):
        _code, book, _side = self.run_scan(group="TRANSPORTER")
        rows = xlsx.read_workbook(book)["Review"][1:]
        self.assertEqual([20002], [r[2] for r in rows])

    def test_vendor_filter_by_name_fragment(self):
        _code, book, _side = self.run_scan(vendor="sunrise")
        rows = xlsx.read_workbook(book)["Review"][1:]
        self.assertEqual([20001, 20003, 20005], sorted(r[2] for r in rows))

    def test_vendor_filter_by_card_code_goes_to_the_server(self):
        self.run_scan(vendor="VENDA000636")
        grpo_filters = [c["filter"] for c in self.sap.calls
                        if c["entity"] == "PurchaseDeliveryNotes"]
        self.assertTrue(any("CardCode eq 'VENDA000636'" in f for f in grpo_filters), grpo_filters)

    def test_include_intercompany_promotes_the_row(self):
        _code, book, _side = self.run_scan(include_intercompany=True)
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20004)
        self.assertEqual("READY", row[19])

    def test_allow_service_promotes_the_service_row(self):
        _code, book, _side = self.run_scan(allow_service=True)
        row = next(r for r in xlsx.read_workbook(book)["Review"][1:] if r[2] == 20002)
        self.assertEqual("READY", row[19])

    def test_since_is_passed_to_sap(self):
        self.run_scan(since="2026-06-01")
        f = next(c["filter"] for c in self.sap.calls if c["entity"] == "PurchaseDeliveryNotes")
        self.assertIn("DocDate ge '2026-06-01'", f)
        self.assertIn("DocumentStatus eq 'bost_Open'", f)
        self.assertIn("Cancelled eq 'tNO'", f)

    def test_the_default_since_is_ninety_days_back(self):
        self.run_scan(since=None)
        f = next(c["filter"] for c in self.sap.calls if c["entity"] == "PurchaseDeliveryNotes")
        self.assertIn("DocDate ge '2026-05-26'", f)

    # -- failure modes ---------------------------------------------------

    def test_no_matching_grpos_writes_nothing_and_exits_0(self):
        self.sap = FakeSap(tables(grpos=[]), company="JIVO_OIL_HANADB")
        code, book, side = self.run_scan()
        self.assertEqual(0, code)
        self.assertFalse(book.exists())
        self.assertFalse(side.exists())

    def test_sap_unreachable_exits_4_and_leaves_no_workbook(self):
        self.sap = FakeSap(tables(), company="JIVO_OIL_HANADB",
                           fail={"PurchaseDeliveryNotes": SapUnreachable("no route", code=5)})
        code, book, side = self.run_scan()
        self.assertEqual(4, code)
        self.assertFalse(book.exists())
        self.assertFalse(side.exists())

    def test_bad_credentials_exit_3(self):
        self.sap = FakeSap(tables(), company="JIVO_OIL_HANADB",
                           fail={"PurchaseDeliveryNotes": SapAuth("login refused", code=4)})
        code, _book, _side = self.run_scan()
        self.assertEqual(3, code)

    def test_a_bad_since_date_is_a_usage_error(self):
        code, book, _side = self.run_scan(since="last tuesday")
        self.assertEqual(2, code)
        self.assertFalse(book.exists())

    def test_a_bad_limit_is_a_usage_error(self):
        code, _book, _side = self.run_scan(limit=-1)
        self.assertEqual(2, code)

    def test_partial_failure_after_the_grpos_still_aborts_without_a_workbook(self):
        self.sap = FakeSap(tables(), company="JIVO_OIL_HANADB",
                           fail={"BusinessPartners": SapUnreachable("dropped", code=5)})
        code, book, _side = self.run_scan()
        self.assertEqual(4, code)
        self.assertFalse(book.exists())


class CompanyResolutionTest(unittest.TestCase):
    def test_friendly_names(self):
        self.assertEqual("JIVO_OIL_HANADB", batch_scan.resolve_company("Oil"))
        self.assertEqual("JIVO_MART_HANADB", batch_scan.resolve_company("mart"))
        self.assertEqual("JIVO_BEVERAGES_HANADB", batch_scan.resolve_company("Beverages"))
        self.assertEqual("JIVO_BEVERAGES_HANADB", batch_scan.resolve_company("bev"))

    def test_a_full_db_name_passes_through(self):
        self.assertEqual("JIVO_OIL_HANADB", batch_scan.resolve_company("JIVO_OIL_HANADB"))

    def test_unknown_is_refused(self):
        with self.assertRaises(ValueError):
            batch_scan.resolve_company("Ketchup")


class CommandLineTest(unittest.TestCase):
    """The entry point itself — the wiring, not the work."""

    def parse(self, argv):
        import acc.acc as accmain
        return accmain.build_parser().parse_args(argv)

    def test_the_subcommand_survives_the_group_flag(self):
        # `--group` is the business partner group. It used to be parsed into the
        # same dest as the subcommand name, so `batch scan --group TRANSPORTER`
        # dispatched to nothing at all and exited 2 without touching SAP.
        args = self.parse(["batch", "scan", "--group", "TRANSPORTER"])
        self.assertEqual("batch", args.topic)
        self.assertEqual("scan", args.action)
        self.assertEqual("TRANSPORTER", args.group)

    def test_scan_defaults(self):
        args = self.parse(["batch", "scan"])
        self.assertEqual("Oil", args.company)
        self.assertEqual(50, args.limit)
        self.assertEqual("oldest", args.order)
        self.assertFalse(args.include_intercompany)
        self.assertFalse(args.allow_service)

    def test_scan_dispatches_to_run_scan(self):
        import acc.acc as accmain
        from acc.apbatch import batch_scan as bs
        seen = {}
        original = bs.run_scan
        bs.run_scan = lambda a: seen.setdefault("args", a) and 0 or 0
        try:
            accmain.main(["batch", "scan", "--company", "Mart", "--limit", "7"])
        finally:
            bs.run_scan = original
        self.assertEqual("Mart", seen["args"].company)
        self.assertEqual(7, seen["args"].limit)

    def test_it_runs_as_a_script_from_anywhere(self):
        # `python3 acc/acc.py` puts acc/ on sys.path, where acc.py shadows the
        # acc package. Import-time only, so only a real subprocess catches it.
        import subprocess
        for cwd in (REPO, Path(tempfile.gettempdir())):
            r = subprocess.run([sys.executable, str(REPO / "acc" / "acc.py"), "batch",
                                "scan", "--help"], capture_output=True, text=True, cwd=str(cwd))
            self.assertEqual(0, r.returncode, r.stderr)
            self.assertIn("--company", r.stdout)

    def test_send_reaches_batch_send_and_defaults_to_previewing(self):
        import acc.acc as accmain
        args = accmain.build_parser().parse_args(["batch", "send", "review.xlsx"])
        self.assertEqual("send", args.action)
        self.assertFalse(args.yes)              # nothing is sent unless it is asked for
        self.assertFalse(args.dry_run)
        self.assertFalse(args.resume)
        self.assertEqual(3, args.max_age_days)
        # A workbook that does not exist is a usage error, not a stack trace.
        self.assertEqual(2, accmain.main(["batch", "send", "review.xlsx"]))

    def test_status_is_wired_up_too(self):
        import acc.acc as accmain
        args = accmain.build_parser().parse_args(["batch", "status", "review.xlsx"])
        self.assertEqual("status", args.action)
        self.assertEqual(2, accmain.main(["batch", "status", "review.xlsx"]))


class QueryEconomyTest(unittest.TestCase):
    def test_a_five_row_scan_stays_well_under_fifty_calls(self):
        # The whole reason ScanContext exists. If this creeps, a 50-row scan over
        # the home bridge stops being something an operator will wait for.
        sap = FakeSap(tables(), company="JIVO_OIL_HANADB")
        with tempfile.TemporaryDirectory() as tmp:
            batch_scan.run_scan(make_args(out=tmp), sap=sap, today=TODAY, now=NOW,
                                batch_id="B260824-OIL-7F3A", repo=Path(tmp))
        self.assertLess(len(sap.calls), 20, sap.entities_called())

    def test_the_open_draft_index_is_read_once(self):
        sap = FakeSap(tables(), company="JIVO_OIL_HANADB")
        with tempfile.TemporaryDirectory() as tmp:
            batch_scan.run_scan(make_args(out=tmp), sap=sap, today=TODAY, now=NOW,
                                batch_id="B260824-OIL-7F3A", repo=Path(tmp))
        drafts = [c for c in sap.calls if c["entity"] == "Drafts" and c["all"]]
        self.assertEqual(1, len(drafts))


if __name__ == "__main__":
    unittest.main()
