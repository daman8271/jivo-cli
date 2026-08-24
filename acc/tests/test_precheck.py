"""precheck_grpo — one GRPO to one decision, against a scripted SAP.

The statuses are what the whole review sheet hangs on, so each one gets its own
scenario and the ORDER they are decided in is asserted too: a duplicate that is
also missing a reference is a duplicate, not a "go fix the reference".
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from acc.apbatch import precheck, rules
from acc.apbatch.context import ScanContext
from acc.apbatch.sap import FakeSap

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = dt.date(2026, 8, 24)

BRANCHES = [
    {"BPLID": 1, "BPLName": "DELHI", "FederalTaxID": "07AAACJ0000A1Z5", "Disabled": "tNO"},
    {"BPLID": 2, "BPLName": "FACTORY", "FederalTaxID": "06AAACJ0000A1Z5", "Disabled": "tNO"},
    {"BPLID": 9, "BPLName": "OLD BRANCH", "FederalTaxID": "06AAACJ0000A1Z5", "Disabled": "tYES"},
]

GROUPS = [{"Code": 110, "Name": "PURCHASE"}, {"Code": 102, "Name": "TRANSPORTER"}]

VENDOR = {"CardCode": "VENDA000777", "CardName": "SUNRISE PACK INDUSTRIES", "GroupCode": 110,
          "SubjectToWithholdingTax": "boYES",
          "BPWithholdingTaxCollection": [{"WTCode": "1031"}],
          "Valid": "tYES", "Frozen": "tNO", "CurrentAccountBalance": -412500.0}

INTERCO = {"CardCode": "VENDA000001", "CardName": "JIVO WELLNESS PVT LTD", "GroupCode": 110,
           "SubjectToWithholdingTax": "boYES", "BPWithholdingTaxCollection": [{"WTCode": "1031"}],
           "Valid": "tYES", "Frozen": "tNO", "CurrentAccountBalance": -209300000.0}


def grpo(**over):
    base = {
        "DocEntry": 20001, "DocNum": 2026080001, "DocType": "dDocument_Items",
        "DocDate": "2026-08-18T00:00:00Z", "TaxDate": "2026-08-17T00:00:00Z",
        "CardCode": "VENDA000777", "CardName": "SUNRISE PACK INDUSTRIES",
        "NumAtCard": "SPI/26-27/0042",
        "Comments": "Based On Purchase Orders 220826099.GATE ENTRY NO.999",
        "DocumentStatus": "bost_Open", "Cancelled": "tNO", "BPL_IDAssignedToInvoice": 2,
        "BPLName": "FACTORY", "AttachmentEntry": 170999, "DocTotal": 53100.0, "VatSum": 8100.0,
        "DocumentLines": [{
            "LineNum": 0, "LineStatus": "bost_Open", "ItemCode": "PM0000999",
            "ItemDescription": "PET BOTTLE 500 ML 18 GM", "Quantity": 10000,
            "RemainingOpenQuantity": 10000, "UnitPrice": 4.5, "LineTotal": 45000.0,
            "TaxCode": "IGST@18", "TaxTotal": 8100.0, "WarehouseCode": "BH-PM",
            "CostingCode": "MUSTARD", "BaseType": 22, "BaseEntry": 14001, "BaseLine": 0,
            "MeasureUnit": "PCS"}],
    }
    base.update(over)
    return base


def service_grpo(**over):
    base = grpo(DocEntry=20002, DocNum=2026070002, DocType="dDocument_Service",
                CardCode="VENDA000636", CardName="DELHI PUNJAB TRANSPORT CO",
                NumAtCard="13023", DocDate="2026-07-29T00:00:00Z",
                TaxDate="2026-07-29T00:00:00Z", DocTotal=13650.0,
                DocumentLines=[{"LineNum": 0, "LineStatus": "bost_Open", "ItemCode": None,
                                "ItemDescription": "EDIBLE OIL", "Quantity": 0,
                                "RemainingOpenQuantity": 0, "UnitPrice": 13000,
                                "LineTotal": 13000.0, "TaxCode": "GST05R", "TaxTotal": 650.0,
                                "WarehouseCode": None, "CostingCode": "CANOLA",
                                "BaseType": -1, "BaseEntry": None, "BaseLine": None}])
    base.update(over)
    return base


def prev_invoice(entry, wtamount=0, wtliable="tNO", subtype="bod_GSTTaxInvoice"):
    return {"DocEntry": entry, "NumAtCard": "SPI/26-27/00%d" % entry, "DocDate": "2026-08-05",
            "DocumentSubType": subtype, "WTAmount": wtamount, "Series": 4001,
            "DocumentLines": [{"WTLiable": wtliable}]}


def build_ctx(*, vendors=(VENDOR,), drafts=(), posted=(), last3=None, series_docs=None,
              company="JIVO_OIL_HANADB"):
    last3 = [prev_invoice(i) for i in (41, 35, 31)] if last3 is None else last3
    series_docs = [{"DocEntry": 9, "Series": 4001}] if series_docs is None else series_docs

    def purchase_invoices(flt, select, **kw):
        if select == "DocEntry,Series":
            return list(series_docs)
        if flt and "NumAtCard eq" in flt:
            return list(posted)
        return list(last3)

    tables = {
        "BusinessPlaces": BRANCHES,
        "BusinessPartnerGroups": GROUPS,
        "BusinessPartners": list(vendors),
        "Drafts": lambda flt, select, **kw: ([] if select == "DocEntry,Series" else list(drafts)),
        "PurchaseInvoices": purchase_invoices,
        "PurchaseOrders": [{"DocEntry": 14001, "DocNum": 220826099}],
        "WithholdingTaxCodes": [{"WTCode": "1031", "WTName": "194Q", "Rate": 0.1}],
    }
    sap = FakeSap(tables, company=company)
    ctx = ScanContext(sap, company_db=company)
    return sap, ctx


def run(g, ctx, **kw):
    ctx.prefetch_vendors([g["CardCode"]])
    ctx.prefetch_posted_refs([g.get("NumAtCard")])
    ctx.prefetch_po_docnums([l.get("BaseEntry") for l in g["DocumentLines"]])
    kw.setdefault("today", TODAY)
    return precheck.precheck_grpo(ctx, g, **kw)


class ReadyTest(unittest.TestCase):
    def test_a_clean_item_grpo_is_ready(self):
        _sap, ctx = build_ctx()
        res = run(grpo(), ctx)
        self.assertEqual(precheck.READY, res.status, res.reasons)
        self.assertEqual([], res.reasons)

    def test_the_payload_is_built(self):
        _sap, ctx = build_ctx()
        res = run(grpo(), ctx)
        self.assertEqual({"CardCode": "VENDA000777", "DocDate": "2026-08-18",
                          "BPL_IDAssignedToInvoice": 2, "Series": 4001,
                          "DocumentSubType": "bod_GSTTaxInvoice",
                          "DocumentLines": [{"BaseType": 20, "BaseEntry": 20001, "BaseLine": 0,
                                             "ItemCode": "PM0000999", "Quantity": 10000,
                                             "UnitPrice": 4.5, "TaxCode": "IGST@18",
                                             "WarehouseCode": "BH-PM",
                                             "CostingCode": "MUSTARD"}]}, res.payload)

    def test_comments_base_names_the_grpo_the_po_and_the_gate_entry(self):
        _sap, ctx = build_ctx()
        res = run(grpo(), ctx)
        self.assertEqual("Based On Goods Receipt PO 2026080001 | PO 220826099 | GATE ENTRY NO 999",
                         res.comments_base)

    def test_totals_come_off_the_open_lines(self):
        _sap, ctx = build_ctx()
        res = run(grpo(), ctx)
        self.assertEqual(10000, res.totals.open_qty)
        self.assertEqual(45000.0, res.totals.taxable)
        self.assertEqual(53100.0, res.totals.gross)

    def test_tds_follows_precedent_not_the_master_flag(self):
        _sap, ctx = build_ctx()
        res = run(grpo(), ctx)
        self.assertEqual("no", res.tds.choice)
        self.assertEqual("PRECEDENT-NO", res.tds.basis)
        self.assertTrue(res.tds.master_liable)

    def test_group_name_is_resolved(self):
        _sap, ctx = build_ctx()
        self.assertEqual("PURCHASE", run(grpo(), ctx).group_name)

    def test_a_missing_attachment_is_a_note_not_a_stop(self):
        _sap, ctx = build_ctx()
        res = run(grpo(AttachmentEntry=None), ctx)
        self.assertEqual(precheck.READY, res.status)
        self.assertTrue(any("no bill attached" in n for n in res.notes))

    def test_the_bill_date_equalling_the_gate_date_is_noted(self):
        _sap, ctx = build_ctx()
        res = run(grpo(TaxDate="2026-08-18T00:00:00Z"), ctx)
        self.assertEqual(precheck.READY, res.status)
        self.assertIn("check bill", precheck.bill_date_source(grpo(TaxDate="2026-08-18T00:00:00Z")))

    def test_an_off_month_posting_is_noted_but_still_ready(self):
        _sap, ctx = build_ctx()
        res = run(grpo(DocDate="2026-05-04T00:00:00Z"), ctx)
        self.assertEqual(precheck.READY, res.status)
        self.assertTrue(any("May-26" in n for n in res.notes), res.notes)

    def test_last_months_posting_is_not_noted(self):
        _sap, ctx = build_ctx()
        res = run(grpo(DocDate="2026-07-30T00:00:00Z"), ctx)
        self.assertFalse(any("confirm the period" in n for n in res.notes), res.notes)


class DuplicateTest(unittest.TestCase):
    OPEN_DRAFT = {"DocEntry": 54983, "DocNum": 626080077, "CardCode": "VENDA000777",
                  "NumAtCard": "SPI/26-27/0042", "DocDate": "2026-08-18", "DocTotal": 53100.0,
                  "UserSign": 7, "DocumentStatus": "bost_Open",
                  "DocumentLines": [{"BaseType": 20, "BaseEntry": 20001, "BaseLine": 0}]}

    def test_duplicate_by_vendor_reference(self):
        draft = dict(self.OPEN_DRAFT, DocumentLines=[])
        _sap, ctx = build_ctx(drafts=[draft])
        res = run(grpo(), ctx)
        self.assertEqual(precheck.DUPLICATE, res.status)
        self.assertIn("54983", res.reason_text)

    def test_duplicate_by_grpo_even_with_a_typoed_reference(self):
        draft = dict(self.OPEN_DRAFT, NumAtCard="SPI/26-27/O042")
        _sap, ctx = build_ctx(drafts=[draft])
        res = run(grpo(), ctx)
        self.assertEqual(precheck.DUPLICATE, res.status)
        self.assertIn("open draft on this GRPO", res.reason_text)

    def test_duplicate_by_a_posted_invoice_under_another_vendor(self):
        posted = [{"DocEntry": 49999, "DocNum": 62608123, "CardCode": "VENDA000778",
                   "NumAtCard": "SPI/26-27/0042", "DocDate": "2026-08-18", "DocTotal": 53100.0,
                   "Cancelled": "tNO"}]
        _sap, ctx = build_ctx(posted=posted)
        res = run(grpo(), ctx)
        self.assertEqual(precheck.DUPLICATE, res.status)
        self.assertIn("posted A/P invoice", res.reason_text)

    def test_a_cancelled_posted_invoice_is_not_a_duplicate(self):
        posted = [{"DocEntry": 49999, "NumAtCard": "SPI/26-27/0042", "DocTotal": 1,
                   "Cancelled": "tYES"}]
        _sap, ctx = build_ctx(posted=posted)
        self.assertEqual(precheck.READY, run(grpo(), ctx).status)

    def test_duplicate_beats_a_missing_reference(self):
        # Order matters: telling an operator to fix a reference on a bill that
        # is already keyed sends them to do work that must not be done.
        draft = dict(self.OPEN_DRAFT, NumAtCard="")
        _sap, ctx = build_ctx(drafts=[draft])
        res = run(grpo(NumAtCard=""), ctx)
        self.assertEqual(precheck.DUPLICATE, res.status)

    def test_duplicate_beats_a_service_hold(self):
        draft = dict(self.OPEN_DRAFT, DocEntry=54984, NumAtCard="13023",
                     DocumentLines=[{"BaseType": 20, "BaseEntry": 20002, "BaseLine": 0}])
        _sap, ctx = build_ctx(drafts=[draft])
        self.assertEqual(precheck.DUPLICATE, run(service_grpo(), ctx).status)


class HeldTest(unittest.TestCase):
    def test_no_vendor_reference(self):
        _sap, ctx = build_ctx()
        res = run(grpo(NumAtCard=""), ctx)
        self.assertEqual(precheck.NEEDS_REF, res.status)
        self.assertIn("no vendor reference", res.reason_text)

    def test_whitespace_only_reference_is_still_missing(self):
        _sap, ctx = build_ctx()
        self.assertEqual(precheck.NEEDS_REF, run(grpo(NumAtCard="   "), ctx).status)

    def test_service_grpo_is_held(self):
        _sap, ctx = build_ctx(vendors=[dict(VENDOR, CardCode="VENDA000636",
                                            CardName="DELHI PUNJAB TRANSPORT CO", GroupCode=102)])
        res = run(service_grpo(), ctx)
        self.assertEqual(precheck.SERVICE_HOLD, res.status)
        self.assertIn("not been sent live yet", res.reason_text)

    def test_service_grpo_can_be_released_by_flag(self):
        _sap, ctx = build_ctx(vendors=[dict(VENDOR, CardCode="VENDA000636",
                                            CardName="DELHI PUNJAB TRANSPORT CO", GroupCode=102)])
        res = run(service_grpo(), ctx, allow_service=True)
        self.assertEqual(precheck.READY, res.status, res.reasons)
        line = res.payload["DocumentLines"][0]
        self.assertEqual({"BaseType": 20, "BaseEntry": 20002, "BaseLine": 0}, line)

    def test_intercompany_is_excluded_by_default(self):
        _sap, ctx = build_ctx(vendors=[INTERCO], company="JIVO_MART_HANADB")
        res = run(grpo(CardCode="VENDA000001", CardName="JIVO WELLNESS PVT LTD"), ctx)
        self.assertEqual(precheck.INTERCOMPANY, res.status)
        self.assertIn("group company", res.reason_text)

    def test_intercompany_can_be_included_by_flag(self):
        _sap, ctx = build_ctx(vendors=[INTERCO], company="JIVO_MART_HANADB")
        res = run(grpo(CardCode="VENDA000001", CardName="JIVO WELLNESS PVT LTD"), ctx,
                  include_intercompany=True)
        self.assertEqual(precheck.READY, res.status, res.reasons)

    def test_intercompany_beats_everything_else(self):
        _sap, ctx = build_ctx(vendors=[INTERCO], company="JIVO_MART_HANADB")
        res = run(grpo(CardCode="VENDA000001", CardName="JIVO WELLNESS PVT LTD", NumAtCard=""), ctx)
        self.assertEqual(precheck.INTERCOMPANY, res.status)


class CannotBuildTest(unittest.TestCase):
    def test_no_open_lines(self):
        _sap, ctx = build_ctx()
        g = grpo()
        g["DocumentLines"][0]["LineStatus"] = "bost_Close"
        res = run(g, ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("no open lines", res.reason_text)

    def test_frozen_vendor(self):
        _sap, ctx = build_ctx(vendors=[dict(VENDOR, Frozen="tYES")])
        res = run(grpo(), ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("FROZEN", res.reason_text)

    def test_invalid_vendor(self):
        _sap, ctx = build_ctx(vendors=[dict(VENDOR, Valid="tNO")])
        self.assertEqual(precheck.CANNOT_BUILD, run(grpo(), ctx).status)

    def test_unknown_vendor_card(self):
        _sap, ctx = build_ctx(vendors=[])
        res = run(grpo(), ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("could not be read", res.reason_text)

    def test_branch_not_in_business_places(self):
        _sap, ctx = build_ctx()
        res = run(grpo(BPL_IDAssignedToInvoice=77), ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("-5002", res.reason_text)

    def test_disabled_branch(self):
        _sap, ctx = build_ctx()
        res = run(grpo(BPL_IDAssignedToInvoice=9), ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("disabled", res.reason_text)

    def test_previous_financial_year_is_refused(self):
        _sap, ctx = build_ctx()
        res = run(grpo(DocDate="2026-03-20T00:00:00Z"), ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("previous financial year", res.reason_text)

    def test_unresolvable_series(self):
        _sap, ctx = build_ctx(series_docs=[])
        res = run(grpo(), ctx)
        self.assertEqual(precheck.CANNOT_BUILD, res.status)
        self.assertIn("series unknown", res.reason_text)

    def test_a_series_the_month_disagrees_about_is_only_a_note(self):
        _sap, ctx = build_ctx(series_docs=[{"DocEntry": 1, "Series": 4001}])
        res = run(grpo(), ctx)
        self.assertEqual(precheck.READY, res.status)


class QueryEconomyTest(unittest.TestCase):
    def test_the_series_lookup_is_month_bounded(self):
        sap, ctx = build_ctx()
        run(grpo(), ctx)
        series_filters = [c["filter"] for c in sap.calls if c["select"] == "DocEntry,Series"]
        self.assertTrue(series_filters)
        for f in series_filters:
            self.assertIn("DocDate ge '2026-08-01'", f)
            self.assertIn("DocDate lt '2026-09-01'", f)

    def test_a_second_row_on_the_same_vendor_and_month_asks_nothing_new(self):
        sap, ctx = build_ctx()
        run(grpo(), ctx)
        first = len(sap.calls)
        run(grpo(DocEntry=20009, DocNum=2026080009, NumAtCard="SPI/26-27/0043"), ctx)
        # Only the two prefetches for the new row's own reference; masters,
        # vendor, precedent and series all come out of the cache.
        self.assertLessEqual(len(sap.calls) - first, 2, sap.entities_called()[first:])

    def test_nothing_was_written(self):
        sap, ctx = build_ctx()
        run(grpo(), ctx)
        self.assertEqual([], sap.writes)


class GoldenRowTest(unittest.TestCase):
    """The real GRPO 25714 through the batch path lands on the golden payload."""

    def test_grpo_25714_builds_the_logged_draft(self):
        g = json.loads((FIXTURES / "grpo_25714.json").read_text(encoding="utf-8"))
        vendor = dict(VENDOR, CardCode="VENDA000939", CardName="TPAC PACKAGING INDIA PVT LTD II")
        _sap, ctx = build_ctx(vendors=[vendor], series_docs=[{"DocEntry": 1, "Series": 3684}] * 40)
        ctx._po_docnums[12467] = 220726021
        res = run(g, ctx, today=dt.date(2026, 8, 22))
        self.assertEqual(precheck.READY, res.status, res.reasons)

        logged = _logged_payload()
        expected = {k: v for k, v in logged.items()
                    if k not in ("DocObjectCode", "NumAtCard", "TaxDate", "Comments")}
        expected["DocumentLines"] = [{k: v for k, v in l.items() if k != "WTLiable"}
                                     for l in logged["DocumentLines"]]
        self.assertEqual(expected, res.payload)
        self.assertEqual(logged["Comments"].split(" | G.No")[0], res.comments_base)
        self.assertEqual("no", res.tds.choice)          # TPAC: precedent beats the master flag


def _logged_payload() -> dict:
    log = REPO / "queries" / "USER36" / "sap-writes.jsonl"
    for line in log.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("event") == "intent" and rec.get("path") == "Drafts":
            return rec["payload"]
    raise AssertionError("no draft intent in the write log")


if __name__ == "__main__":
    unittest.main()
