#!/usr/bin/env python3
"""Tests for tds.py — every SAP read is answered by an in-memory fake HANA, no network.

    python test_tds.py
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tds  # noqa: E402

OIL, BEV, MART = "JIVO_OIL_HANADB", "JIVO_BEVERAGES_HANADB", "JIVO_MART_HANADB"
OWHT = {"1023": "1.000000", "1024": "2.000000", "1031": "0.100000", "1230": "1.000000", "C194": "2.000000", "TDS": "0.100000"}


class FakeHana:
    """Answers tds.Sap's named reads from fixtures. Same signature as tds.hana_query."""

    def __init__(self):
        self.db = {s: {"cards": {}, "owht": dict(OWHT), "posted": {}, "grpo": {}, "drafts": {}} for s in (OIL, BEV, MART)}
        self.calls = []

    def card(self, schema, code, name, group="PURCHASE", liable="Y", pan=None, gstin=None, codes=(), currency="INR"):
        self.db[schema]["cards"][code] = dict(name=name, group=group, liable=liable, pan=pan, gstin=gstin, codes=list(codes),
                                              currency=currency)

    def __call__(self, name, sql, params):
        self.calls.append((name, params))
        db, code = self.db[params["schema"]], params.get("code")
        c = db["cards"].get(code, {})
        if name == "card":
            return [{"CardCode": code, "CardName": c["name"], "CardType": "S", "WTLiable": c["liable"],
                     "Currency": c["currency"], "GroupName": c["group"]}] if c else []
        if name == "tax_ids":
            return [{"Src": "PAN", "Val": c["pan"]}, {"Src": "GSTIN", "Val": c["gstin"]}]
        if name == "card_codes":
            return [{"WTCode": x} for x in c["codes"]]
        if name == "owht":
            return [{"WTCode": k, "Rate": v} for k, v in db["owht"].items()]
        if name == "cards_on_pan":
            p = params["pan"]
            return [{"CardCode": k} for k, v in sorted(db["cards"].items()) if v["pan"] == p or (v["gstin"] or "")[2:12] == p]
        if name == "yearly":
            return [{"Kind": "INV", "Amount": str(sum(db["posted"].get(x, 0) for x in params["cards"]))},
                    {"Kind": "CN", "Amount": "0"},
                    {"Kind": "DRAFT", "Amount": str(sum(db.get("pending", {}).get(x, 0) for x in params["cards"]))}]
        if name == "grpo_lines":
            return [dict(r, DocEntry=str(e), LineNum=str(n)) for (e, n), r in db["grpo"].items() if e in params["entries"]]
        d = db["drafts"].get(params["entry"])
        return {"draft_header": [d["header"]] if d else [], "draft_lines": d and d["lines"], "draft_wt": d and d["wt"]}[name]

    def names(self):
        return [n for n, _ in self.calls]


def bill(card, lines, doc_type=None, **extra):
    body = dict({"DocObjectCode": "oPurchaseInvoices", "CardCode": card, "DocDate": "2026-09-10", "DocumentLines": lines}, **extra)
    if doc_type:
        body["DocType"] = doc_type
    return body


class Base(unittest.TestCase):
    def setUp(self):
        self.hana, self.tmp = FakeHana(), tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = tds.main(argv, query=self.hana)
        return code, out.getvalue()

    def apply(self, payload, company="OIL", as_json=True):
        path = os.path.join(self.tmp, "payload.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        code, text = self.run_main(["apply", path, "--company", company] + (["--json"] if as_json else []))
        with open(path, encoding="utf-8") as fh:
            written = json.load(fh)
        return code, (json.loads(text) if as_json else text), written

    def wt(self, written):
        return written.get("WithholdingTaxDataCollection"), [ln.get("WTLiable") for ln in written["DocumentLines"]]


class GoodsTests(Base):
    def ssy(self, posted):
        self.hana.card(OIL, "VENDA000936", "SSY CONTAINERS PVT LTD", pan="AAOCS0564L", gstin="06AAOCS0564L1ZY", codes=["1031"])
        self.hana.db[OIL]["posted"]["VENDA000936"] = posted

    def test_over_fifty_lakh_whole_bill_at_point_one_percent(self):
        self.ssy(11340512)
        code, text, written = self.apply(bill("VENDA000936", [
            {"ItemCode": "PM0000914", "Quantity": 2442, "UnitPrice": 34.95},
            {"ItemCode": "PM0000411", "Quantity": 2840, "UnitPrice": 33.28}], Comments="keep me"), as_json=False)
        self.assertEqual(code, 0, text)
        self.assertEqual(self.wt(written), ([{"WTCode": "1031", "TaxableAmount": 179863.1, "WTAmount": 180}], ["tYES", "tYES"]))
        self.assertEqual(written["Comments"], "keep me")
        self.assertIn("Goods (RM/PM) · Oil+Bev this year ₹1,13,40,512 before this bill → over ₹50 lakh · "
                      "TDS 0.1% on ₹1,79,863 = ₹180 (code 1031)", text)

    def test_bill_crossing_fifty_lakh_taxed_only_above_it(self):
        self.hana.card(OIL, "VENDA000335", "KUBER PAPER & PACK", gstin="06AAJCK3867H1Z8")
        self.hana.db[OIL]["posted"]["VENDA000335"] = 4968691
        code, res, written = self.apply(bill("VENDA000335", [{"LineTotal": 345889}], "dDocument_Items"))
        self.assertEqual(code, 0, res)
        self.assertEqual(self.wt(written)[0], [{"WTCode": "1031", "TaxableAmount": 314580.0, "WTAmount": 315}])
        self.assertIn("crosses ₹50 lakh · TDS 0.1% on the ₹3,14,580 above it = ₹315 (code 1031, not on the vendor card)",
                      res["summary"][-1])

    def test_under_fifty_lakh_no_tds_and_old_rows_removed(self):
        self.ssy(4000000)
        code, res, written = self.apply(bill("VENDA000936", [{"LineTotal": 300000}], WithholdingTaxDataCollection=[{"WTCode": "1031"}]))
        self.assertEqual(code, 0, res)
        self.assertEqual(self.wt(written), (None, ["tNO"]))
        self.assertIn("under ₹50 lakh · no TDS", res["summary"][-1])

    def test_oil_and_bev_add_up_across_two_cardcodes_on_one_pan(self):
        self.hana.card(OIL, "VENDA001044", "S.N. INDUSTRIES", gstin="07AANPG8531F1ZO", codes=["1031"])  # PAN only via GSTIN
        self.hana.card(OIL, "VENDA001056", "RAUNAK NURSERY", liable="N")                                # same code, other party
        self.hana.card(BEV, "VENDA001056", "S.N. INDUSTRIES", pan="AANPG8531F", codes=["1031"])
        self.hana.db[OIL]["posted"].update({"VENDA001044": 2000000, "VENDA001056": 9999999})
        self.hana.db[BEV]["posted"]["VENDA001056"] = 3100000
        code, res, written = self.apply(bill("VENDA001056", [{"LineTotal": 34726}, {"LineTotal": 454910.6},
                                                             {"LineTotal": 153922.1}]), company="BEV")
        self.assertEqual(code, 0, res)
        self.assertIn("yearly total counts Oil VENDA001044 · Bev VENDA001056", res["summary"])
        self.assertEqual(self.wt(written)[0], [{"WTCode": "1031", "TaxableAmount": 643558.7, "WTAmount": 644}])

    def test_mart_counts_alone(self):
        for schema, code in ((OIL, "VENDA000001"), (BEV, "VENDA000001"), (MART, "VENDA000996")):
            self.hana.card(schema, code, "S.N. INDUSTRIES", pan="AANPG8531F", codes=["TDS"])
            self.hana.db[schema]["posted"][code] = 1000000 if schema == MART else 9000000
        code, res, written = self.apply(bill("VENDA000996", [{"LineTotal": 200000}]), company="MART")
        self.assertEqual(code, 0, res)
        self.assertEqual([p["schema"] for n, p in self.hana.calls if n == "yearly"], [MART])
        self.assertEqual(self.wt(written), (None, ["tNO"]))

    def test_grpo_copied_lines_priced_from_pdn1_and_half_up(self):
        self.ssy(6000000)
        self.hana.db[OIL]["grpo"].update({(700, 0): {"Quantity": "100", "LineTotal": "10000"},
                                          (700, 1): {"Quantity": "0", "LineTotal": "2500"}})
        code, res, written = self.apply(bill("VENDA000936", [{"BaseType": 20, "BaseEntry": 700, "BaseLine": 0, "Quantity": 50},
                                                             {"BaseType": 20, "BaseEntry": 700, "BaseLine": 1}]))
        self.assertEqual(code, 0, res)  # 10000 x 50/100 + 2500 = 7500 -> 0.1% = 7.50 -> Rs 8
        self.assertEqual(self.wt(written)[0], [{"WTCode": "1031", "TaxableAmount": 7500.0, "WTAmount": 8}])

    def test_import_export_vendor_no_tds(self):
        self.hana.card(OIL, "VENDI1", "OVERSEAS OIL", group="IMPORT & EXPORT", pan="AAACO1234C")
        code, res, written = self.apply(bill("VENDI1", [{"LineTotal": 500000}]))
        self.assertEqual((code, self.wt(written)), (0, (None, ["tNO"])))
        self.assertNotIn("yearly", self.hana.names())

    def test_no_pan_same_cardcode_counted_only_for_same_party(self):
        self.hana.card(BEV, "VENDA001056", "S.N. INDUSTRIES")
        self.hana.card(OIL, "VENDA001056", "RAUNAK NURSERY")
        self.hana.db[OIL]["posted"]["VENDA001056"] = 9000000
        code, res, written = self.apply(bill("VENDA001056", [{"LineTotal": 1000}]), company="BEV")
        self.assertEqual((code, self.wt(written)), (0, (None, ["tNO"])))
        self.assertIn("VENDA001056 in Oil is RAUNAK NURSERY — a different party, not counted", res["notes"])
        self.assertIn("no PAN on the card — counted by vendor code only", res["notes"])

    def test_tds_due_but_card_not_liable_stops_and_payload_untouched(self):
        self.hana.card(OIL, "VENDA000335", "KUBER PAPER & PACK", liable="N", gstin="06AAJCK3867H1Z8")
        self.hana.db[OIL]["posted"]["VENDA000335"] = 4968691
        payload = bill("VENDA000335", [{"LineTotal": 345889}])
        code, res, written = self.apply(payload)
        self.assertEqual((code, written), (2, payload))
        self.assertIn("not marked TDS-liable", res["message"])

    def test_owht_rate_different_from_rules_stops(self):
        self.ssy(9000000)
        self.hana.db[OIL]["owht"]["1031"] = "1.000000"
        code, res, written = self.apply(bill("VENDA000936", [{"LineTotal": 1000}]))
        self.assertEqual(code, 2)
        self.assertIn("OWHT has code 1031 at 1%", res["message"])


class TransportTests(Base):
    def test_exempt_by_pan(self):
        self.hana.card(OIL, "VENDA001661", "PICK & SHIP", group="TRANSPORTER", pan="AAQCP4145A", codes=["1024"])
        code, res, written = self.apply(bill("VENDA001661", [{"AccountCode": "5670001", "LineTotal": 17304.67, "WTLiable": "tYES"}],
                                             "dDocument_Service", WithholdingTaxDataCollection=[{"WTCode": "1024"}]))
        self.assertEqual((code, self.wt(written)), (0, (None, ["tNO"])))
        self.assertEqual(res["summary"], ["Transporter · declaration received (PICK & SHIP LOGISTICS) · no TDS"])

    def test_exempt_by_cardcode_without_pan(self):
        self.hana.card(MART, "VENDA000108", "DELHI PUNJAB CARRIER", group="TRANSPORTER")
        code, res, written = self.apply(bill("VENDA000108", [{"LineTotal": 90000}], "dDocument_Service"), company="MART")
        self.assertEqual((code, self.wt(written)), (0, (None, ["tNO"])))

    def test_other_transporter_two_percent_from_first_rupee(self):
        self.hana.card(OIL, "VENDT1", "SOME ROADWAYS", group="TRANSPORTER", pan="AAECS1234D", codes=["1024"])
        code, res, written = self.apply(bill("VENDT1", [{"LineTotal": 5000}], "dDocument_Service"))
        self.assertEqual((code, self.wt(written)), (0, ([{"WTCode": "1024", "TaxableAmount": 5000.0, "WTAmount": 100}], ["tYES"])))
        self.assertNotIn("yearly", self.hana.names())

    def test_transporter_with_one_percent_card_code_still_two_percent(self):
        self.hana.card(BEV, "VENDT2", "AIR CARGO", group="TRANSPORTER", pan="ABCPK1234L", codes=["1230"])
        code, res, written = self.apply(bill("VENDT2", [{"LineTotal": 5000}], "dDocument_Service"), company="BEV")
        self.assertEqual(self.wt(written)[0], [{"WTCode": "1024", "TaxableAmount": 5000.0, "WTAmount": 100}])

    def test_freight_line_from_grpo_takes_pdn1_amount(self):
        self.hana.card(OIL, "VENDT3", "SOME ROADWAYS", group="TRANSPORTER", pan="AAECS1234D", codes=["C194"])
        self.hana.db[OIL]["grpo"][(26694, 2)] = {"Quantity": "0", "LineTotal": "17304.67"}
        code, res, written = self.apply(bill("VENDT3", [{"BaseType": 20, "BaseEntry": 26694, "BaseLine": 2}], "dDocument_Service"))
        self.assertEqual(self.wt(written)[0], [{"WTCode": "C194", "TaxableAmount": 17304.67, "WTAmount": 346}])


class UntouchedTests(Base):
    def test_service_bill_from_non_transporter_left_alone(self):
        self.hana.card(OIL, "VENDS1", "CONSULTANTS LLP", group="SERVICE", pan="AAKFC1234M", codes=["1027"])
        path = os.path.join(self.tmp, "svc.json")
        raw = '{"DocObjectCode":"oPurchaseInvoices","DocType":"dDocument_Service","CardCode":"VENDS1",' \
              '"DocumentLines":[{"AccountCode":"5680025","LineTotal":90000,"WTLiable":"tYES"}],' \
              '"WithholdingTaxDataCollection":[{"WTCode":"1027"}]}'
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(raw)
        code, text = self.run_main(["apply", path, "--company", "OIL"])
        self.assertEqual(code, 0, text)
        self.assertIn("service bill — TDS left as the skill set it", text)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), raw)

    def test_credit_note_left_alone_without_reading_sap(self):
        path = os.path.join(self.tmp, "cn.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"DocObjectCode": "oPurchaseCreditNotes", "CardCode": "VENDA1", "DocumentLines": [{"LineTotal": 1}]}, fh)
        code, text = self.run_main(["apply", path, "--company", "OIL", "--out", os.path.join(self.tmp, "cn-out.json")])
        self.assertEqual((code, self.hana.calls), (0, []))
        self.assertIn("credit note — TDS left as the skill set it", text)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "cn-out.json")))


class CheckTests(Base):
    ROW = [{"WTCode": "1031", "TaxbleAmnt": "179084.000000", "WTAmnt": "179.000000"}]

    def draft(self, entry, wt_sum, wt, liable="Y", card=("VENDA000936", "SSY CONTAINERS PVT LTD"), doc_type="I"):
        if card[0] == "VENDA000936":
            self.hana.card(OIL, *card, pan="AAOCS0564L", codes=["1031"])
            self.hana.db[OIL]["posted"]["VENDA000936"] = 11327764
        self.hana.db[OIL]["drafts"][entry] = {
            "header": {"ObjType": "18", "DocType": doc_type, "CardCode": card[0], "CardName": card[1], "DocDate": "2026-09-10",
                       "DocCur": "INR", "WTSum": str(wt_sum)},
            "lines": [{"LineTotal": "23828.480000", "WtLiable": liable}, {"LineTotal": "155255.520000", "WtLiable": liable}],
            "wt": wt}

    def check(self, entry, *extra):
        return self.run_main(["check", str(entry), "--company", "OIL"] + list(extra))

    def test_pass_and_draft_excluded_from_its_own_yearly_total(self):
        self.draft(56878, "179.000000", self.ROW)
        code, text = self.check(56878)
        self.assertEqual(code, 0, text)
        self.assertIn("PASS — TDS matches the rules (₹179)", text)
        self.assertEqual([p["draft"] for n, p in self.hana.calls if n == "yearly" and p["schema"] == OIL], [56878])

    def test_one_rupee_off_still_passes(self):
        self.draft(56878, "180", [dict(self.ROW[0], WTAmnt="180")])
        self.assertEqual(self.check(56878)[0], 0)

    def test_rows_present_but_wtsum_zero_is_not_applied(self):
        self.draft(56878, "0", self.ROW)
        code, text = self.check(56878)
        self.assertEqual(code, 3, text)
        self.assertIn("TDS was calculated but not applied — open the draft in SAP B1 and save it once", text)

    def test_lines_ticked_no_rows_wtsum_zero_is_not_applied(self):
        self.draft(56841, "0", [])
        code, text = self.check(56841)
        self.assertEqual(code, 3, text)
        self.assertIn("calculated but not applied", text)

    def test_nothing_ticked_and_tds_missing_is_mismatch(self):
        self.draft(16055, "0", [], liable="N")
        code, text = self.check(16055, "--json")
        res = json.loads(text)
        self.assertEqual((code, res["result"]), (3, "MISMATCH"))
        self.assertIn("the rules say ₹179 TDS (code 1031 ₹179 on ₹1,79,084), the draft deducts ₹0", res["message"])

    def test_exempt_transporter_with_ticked_lines_passes(self):
        self.hana.card(OIL, "VENDA001661", "PICK & SHIP", group="TRANSPORTER", pan="AAQCP4145A", codes=["1024"])
        self.draft(57034, "0", [], card=("VENDA001661", "PICK & SHIP"), doc_type="S")
        code, text = self.check(57034)
        self.assertEqual(code, 0, text)

    def test_service_draft_ticked_but_not_applied_fails_and_clean_one_passes(self):
        self.hana.card(OIL, "VENDS1", "CONSULTANTS LLP", group="SERVICE", pan="AAKFC1234M")
        self.draft(1, "0", [], card=("VENDS1", "CONSULTANTS LLP"), doc_type="S")
        self.assertEqual(self.check(1)[0], 3)
        self.draft(2, "0", [], liable="N", card=("VENDS1", "CONSULTANTS LLP"), doc_type="S")
        code, text = self.check(2)
        self.assertEqual(code, 0, text)
        self.assertIn("PASS — service bill, not recalculated", text)

    def test_draft_not_in_book_stops(self):
        code, text = self.check(99)
        self.assertEqual(code, 2, text)
        self.assertIn("not there", text)


class PlumbingTests(Base):
    def fake_binary(self, body):
        script = os.path.join(self.tmp, "fake_hana.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(body)
        return mock.patch.object(tds, "hana_command", lambda: [sys.executable, script])

    def test_hana_unreachable_is_stop(self):
        with self.fake_binary("import sys\nsys.stderr.write('dial tcp 10.0.0.9:30015: connection refused\\n')\nsys.exit(1)\n"):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = tds.main(["check", "56878", "--company", "OIL"])
        self.assertEqual(code, 2, out.getvalue())
        self.assertIn("SAP HANA read failed (dial tcp 10.0.0.9:30015", out.getvalue())

    def test_query_error_is_stop_and_csv_null_is_none(self):
        with self.fake_binary("print('QUERY ERROR: SQL Error 260 - invalid column name')\n"), self.assertRaises(tds.Stop):
            tds.hana_query("x", "SELECT 1 FROM DUMMY", {})
        with self.fake_binary("print('CardCode,TaxId0')\nprint('VENDA1,NULL')\nprint('\"V,2\",AAOCS0564L')\n"):
            rows = tds.hana_query("x", "SELECT 1 FROM DUMMY", {})
        self.assertEqual(rows, [{"CardCode": "VENDA1", "TaxId0": None}, {"CardCode": "V,2", "TaxId0": "AAOCS0564L"}])

    def test_indian_grouping(self):
        self.assertEqual([tds.inr(x) for x in (11340512, 179863.1, 999, 100000)], ["₹1,13,40,512", "₹1,79,863", "₹999", "₹1,00,000"])

    def test_unsafe_cardcode_stops_before_any_query(self):
        code, res, written = self.apply(bill("X' OR '1'='1", [{"LineTotal": 1}]))
        self.assertEqual((code, self.hana.calls), (2, []))

    def test_bad_arguments_exit_one(self):
        self.assertEqual(self.run_main(["check"])[0], 1)
        self.assertEqual(self.run_main(["check", "abc", "--company", "OIL"])[0], 1)
        self.assertEqual(self.run_main(["check", "1", "--company", "XYZ"])[0], 1)



class ReviewFixTests(Base):
    """Fixes from the 17 Sept review, before deploy."""

    def test_payload_without_docobjectcode_is_treated_as_invoice(self):
        self.hana.card(OIL, "VENDA000936", "SSY CONTAINERS PVT LTD", pan="AAOCS0564L", codes=["1031"])
        self.hana.db[OIL]["posted"]["VENDA000936"] = 11340512
        body = bill("VENDA000936", [{"LineTotal": 179863.1}]); body.pop("DocObjectCode")
        code, res, written = self.apply(body)
        self.assertEqual(code, 0, res)
        self.assertEqual(self.wt(written)[0], [{"WTCode": "1031", "TaxableAmount": 179863.1, "WTAmount": 180}])
        self.assertNotIn("DocObjectCode", written)

    def test_no_docobjectcode_but_copied_from_invoice_stops(self):
        body = bill("VENDA1", [{"BaseType": 18, "BaseEntry": 5, "BaseLine": 0, "LineTotal": 10}]); body.pop("DocObjectCode")
        code, res, written = self.apply(body)
        self.assertEqual(code, 2, res)
        self.assertIn("credit note", res["message"])

    def test_drafts_already_in_approval_count_towards_fifty_lakh(self):
        self.hana.card(OIL, "VENDA000936", "SSY CONTAINERS PVT LTD", pan="AAOCS0564L", codes=["1031"])
        self.hana.db[OIL]["posted"]["VENDA000936"] = 4500000
        self.hana.db[OIL]["pending"] = {"VENDA000936": 600000}
        code, res, written = self.apply(bill("VENDA000936", [{"LineTotal": 300000}]))
        self.assertEqual(code, 0, res)
        self.assertEqual(self.wt(written)[0], [{"WTCode": "1031", "TaxableAmount": 300000.0, "WTAmount": 300}])
        sql = [q for n, q in [(c[0], c[1]) for c in self.hana.calls] if n == "yearly"]
        self.assertTrue(sql)

    def test_unexpected_error_is_a_stop_not_usage(self):
        self.hana.card(OIL, "VENDA000936", "SSY CONTAINERS PVT LTD", pan="AAOCS0564L", codes=["1031"])
        code, res, written = self.apply(bill("VENDA000936", [{"Quantity": "1,000", "UnitPrice": 5}]))
        self.assertEqual(code, 2, res)
        self.assertIn("unexpected", res["message"])

    def test_pan_typo_on_card_falls_back_to_gstin(self):
        self.hana.card(OIL, "VENDA001745", "JATIN SINGH", pan="BP0PR2824F", gstin="06BPOPR2824F1ZX")
        self.assertEqual(tds.find_pan(tds.Sap(self.hana), OIL, "VENDA001745"), "BPOPR2824F")

    def test_service_bill_with_two_pans_is_left_alone(self):
        self.hana.card(OIL, "VENDS2", "SOME SERVICE", group="SERVICE", pan="AAAAA1111A", gstin="06BBBBB2222B1ZX")
        code, res, written = self.apply(bill("VENDS2", [{"LineTotal": 100}], "dDocument_Service"))
        self.assertEqual(code, 0, res)
        self.assertIn("service bill", res["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
