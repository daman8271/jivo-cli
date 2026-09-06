#!/usr/bin/env python3
"""Unit tests for live/adapters/_mask.py.

    cd jolly && python3 -m unittest live.adapters._mask_test -v

Two halves, and the first one is the important one:

  * LEAVE ALONE — every class of ten-digit-looking thing this plant actually
    produces (plates, gate ids, PO and GRPO numbers, SAP doc numbers, order
    numbers, item codes, timestamps, litres, rupees). A masker that eats one of
    these corrupts the public feed silently, which is worse than the leak it
    was written to stop.
  * MASK — the five shapes a driver's mobile has ever arrived in.
"""

from __future__ import annotations

import unittest

try:                                                # normal: run from jolly/
    from live.adapters._mask import (MASK, MOBILE_RE, mask_phones,
                                     mask_phones_verbose, scan_phones)
except ImportError:                                 # run from inside adapters/
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    from live.adapters._mask import (MASK, MOBILE_RE, mask_phones,
                                     mask_phones_verbose, scan_phones)


class LeaveAlone(unittest.TestCase):
    """Real values from live/state/*.json that must survive untouched."""

    def _unchanged(self, key, value):
        doc = {key: value}
        out, recs = mask_phones_verbose(doc)
        self.assertEqual(out[key], value, "%s=%r was altered" % (key, value))
        self.assertEqual(recs, [], "%s=%r was masked" % (key, value))
        self.assertEqual(scan_phones(doc), [], "guard flagged %r" % (value,))

    # 1
    def test_iso_timestamp(self):
        self._unchanged("fetched_at", "2026-09-03T13:10:20+05:30")

    # 2
    def test_iso_timestamp_utc_z(self):
        self._unchanged("server_at", "2026-09-03T07:40:20.123456Z")

    # 3
    def test_plain_date(self):
        self._unchanged("gate_in_date", "2026-09-03")

    # 4
    def test_date_and_time_in_prose(self):
        self._unchanged("note", "gated in 2026-09-03 16:30, still inside")

    # 5
    def test_vehicle_plate(self):
        self._unchanged("vehicle_no", "HR67C4904")

    # 6
    def test_vehicle_plate_long(self):
        self._unchanged("vehicle_no", "DL01LAN4065")

    # 7
    def test_vehicle_plate_under_vehicle_key(self):
        self._unchanged("vehicle", "GJ39TA1566")

    # 8
    def test_litres(self):
        self._unchanged("litres", "9876543.21")

    # 9
    def test_rupees_numeric(self):
        self._unchanged("value_inr", 9876543210)

    # 10
    def test_order_number(self):
        self._unchanged("order_number", "ORD-20260903-0016")

    # 11
    def test_sales_invoice_number(self):
        self._unchanged("order_no", "626080715")

    # 12
    def test_gate_entry_id(self):
        self._unchanged("entry_no", "GE-2026-5640")

    # 13
    def test_gate_vehicle_entry_id(self):
        self._unchanged("entry_no", "EVGI-20260903-0008")

    # 14
    def test_dock_id(self):
        self._unchanged("entry_no", "DOCK-20260903-0012")

    # 15
    def test_fg_code(self):
        self._unchanged("sku_code", "FG0000155")

    # 16
    def test_rm_code(self):
        self._unchanged("rm_code", "RM0000013")

    # 17
    def test_pm_code(self):
        self._unchanged("code", "PM0000271")

    # 18
    def test_po_number_nine_digits(self):
        self._unchanged("po_number", "220926010")

    # 19
    def test_po_number_ten_digits_starting_six(self):
        # The sharp one: an OMS PO is ten digits and starts with 6, exactly a
        # mobile's shape. Only the key tells them apart.
        self._unchanged("po_number", "6500262904")

    # 20
    def test_grpo_number(self):
        self._unchanged("grpo_no", "2026086831")

    # 21
    def test_sap_doc_number_starting_one(self):
        self._unchanged("sap_doc_number", "1726086707")

    # 22
    def test_sap_doc_number_in_prose(self):
        self._unchanged("note", "posted as 1726086707 on 2026-09-03")

    # 23
    def test_long_digit_run_is_not_a_mobile(self):
        self._unchanged("weighbridge_slip_no", "98765432109876")

    # 24
    def test_nine_digit_run_is_not_a_mobile(self):
        self._unchanged("note", "batch 925226664 cleared QC")

    # 25 — the decimals the full stop in the lookbehind was written to protect.
    # These are the reason `Ravi.9876543210` was allowed to leak, so they are pinned
    # here beside the leak: the fix has to keep every one of them untouched.
    def test_litres_with_ten_decimal_places(self):
        self._unchanged("note", "tank dip 1234.5678901234 L at 06:00")

    # 26
    def test_a_decimal_whose_fraction_is_mobile_shaped(self):
        # the fractional tail of a longer number is not a phone number
        self._unchanged("note", "meter read 1234.9876543210 at the gate")

    # 27
    def test_rupees_with_paise(self):
        self._unchanged("note", "billed 9876543210.50 today")

    # 28
    def test_a_timestamp_with_fractional_seconds_in_prose(self):
        self._unchanged("note", "posted 2026-09-03T07:40:20.123456Z by the loop")

    # 29
    def test_a_document_number_after_a_full_stop_in_prose(self):
        self._unchanged("note", "see doc 1726086707. Next line follows")

    # 30
    def test_empty_and_null_survive(self):
        doc = {"driver_mobile_no": "", "mobile_no": None, "ok": True}
        out, recs = mask_phones_verbose(doc)
        self.assertEqual(out, {"driver_mobile_no": "", "mobile_no": None,
                               "ok": True})
        self.assertEqual(recs, [])


class Mask(unittest.TestCase):
    """The five shapes a driver's mobile has arrived in."""

    # 1
    def test_bare_mobile_in_prose(self):
        out = mask_phones({"driver_name": "Sompal 8295058874"})
        self.assertEqual(out["driver_name"], "Sompal " + MASK + "74")

    # 2
    def test_plus_91_form(self):
        out = mask_phones({"remark": "call +919560283139 at the gate"})
        self.assertEqual(out["remark"], "call " + MASK + "39 at the gate")

    # 3
    def test_spaced_form(self):
        out = mask_phones({"remark": "driver 98765 43210"})
        self.assertEqual(out["remark"], "driver " + MASK + "10")

    # 4
    def test_dashed_and_zero_prefixed_form(self):
        out = mask_phones({"remark": "09918-186361 (Ramkaran)"})
        self.assertEqual(out["remark"], MASK + "61 (Ramkaran)")

    # 5
    def test_key_named_mobile(self):
        out, recs = mask_phones_verbose({"driver_mobile_no": "8295058874"})
        self.assertEqual(out["driver_mobile_no"], MASK + "74")
        self.assertEqual(recs[0]["reason"], "key")

    # 6 — the key rule fires even when the value is not mobile-shaped, because
    # a field called "phone" has no business holding anything else.
    def test_key_named_phone_with_landline(self):
        out = mask_phones({"contact_no": "011-4567 8900"})
        self.assertEqual(out["contact_no"], MASK + "00")

    # 7
    def test_key_named_whatsapp_numeric_value(self):
        out = mask_phones({"whatsapp": 918899011758})
        self.assertEqual(out["whatsapp"], MASK + "58")

    # 8
    def test_two_mobiles_in_one_string(self):
        out = mask_phones({"note": "Sompal 8295058874 / Ramkaran 9918186361"})
        self.assertEqual(out["note"],
                         "Sompal " + MASK + "74 / Ramkaran " + MASK + "61")

    # 9 — nested exactly like a real dispatch envelope
    def test_nested_bills_and_vehicles(self):
        env = {
            "source": "factory_dispatch",
            "data": {
                "bills": [
                    {"vehicle_no": "HR67C4904", "driver_mobile_no": "9876543210",
                     "litres": 3000.0, "entry_no": "EVGI-20260903-0008"},
                ],
                "vehicles": [{"vehicle_no": "DL01LAN4065",
                              "driver_name": "Ramkaran 9918186361"}],
            },
        }
        out = mask_phones(env)
        bill = out["data"]["bills"][0]
        self.assertEqual(bill["vehicle_no"], "HR67C4904")
        self.assertEqual(bill["entry_no"], "EVGI-20260903-0008")
        self.assertEqual(bill["litres"], 3000.0)
        self.assertEqual(bill["driver_mobile_no"], MASK + "10")
        veh = out["data"]["vehicles"][0]
        self.assertEqual(veh["vehicle_no"], "DL01LAN4065")
        self.assertEqual(veh["driver_name"], "Ramkaran " + MASK + "61")
        self.assertEqual(scan_phones(out), [])

    # 10
    def test_mobile_inside_a_list_of_strings(self):
        out = mask_phones({"notes": ["ok", "ring 8295058874"]})
        self.assertEqual(out["notes"], ["ok", "ring " + MASK + "74"])


class AFullStopIsNotAShield(unittest.TestCase):
    """ROUND B item 19 — the leak that blocked the deploy.

    MOBILE_RE opened `(?<![\\d.])`, so a ten-digit run with a FULL STOP in front of
    it was left alone. Question 14 of the file Gurvinder answers asks for WhatsApp
    numbers and he answers in prose on an iPad, so `Ravi.9876543210` is the shape
    that actually arrives — and it reached live/state/plan/assumptions.json, which
    live/publish/ serves at a public hostname, with every check green.

    The full stop stays in the pattern for decimals (LeaveAlone 25-29). What
    changed is that a full stop is only a shield when a DIGIT sits in front of it.
    """

    def test_a_name_glued_to_a_number_by_a_full_stop(self):
        out = mask_phones({"answer": "Answer: Ravi.9876543210"})
        self.assertEqual(out["answer"], "Answer: Ravi." + MASK + "10")

    def test_plus_91_then_a_full_stop(self):
        out = mask_phones({"answer": "bulk oil +91.9876543210"})
        self.assertEqual(out["answer"], "bulk oil " + MASK + "10")

    def test_a_number_split_by_a_full_stop(self):
        out = mask_phones({"answer": "dispatch 98765.43210"})
        self.assertEqual(out["answer"], "dispatch " + MASK + "10")

    def test_the_guard_and_the_masker_agree_on_all_three(self):
        doc = {"a": "Ravi.9876543210", "b": "+91.9876543210", "c": "98765.43210"}
        self.assertEqual(len(scan_phones(dict(doc))), 3, "the guard must see them too")
        self.assertEqual(scan_phones(mask_phones(dict(doc))), [])

    def test_the_shapes_that_already_masked_still_mask(self):
        # nothing above may be bought by loosening what already worked
        for value, tail in (("9876543210", "10"), ("98765 43210", "10"),
                            ("(9876543210)", "10"), ("+91 98765 43210", "10"),
                            ("09918-186361", "61"), ("Sompal 8295058874", "74")):
            with self.subTest(value=value):
                out = mask_phones({"note": value})
                self.assertIn(MASK + tail, out["note"])
                self.assertEqual(scan_phones({"note": out["note"]}), [])


class Idempotent(unittest.TestCase):
    def test_masking_twice_changes_nothing(self):
        doc = {"driver_name": "Sompal 8295058874", "driver_mobile_no": "9918186361"}
        once = mask_phones(dict(doc))
        twice, recs = mask_phones_verbose(dict(once))
        self.assertEqual(twice, once)
        self.assertEqual(recs, [])


class Guard(unittest.TestCase):
    def test_guard_finds_an_unmasked_mobile(self):
        found = scan_phones({"data": {"rows": [{"remark": "call 8295058874"}]}})
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], "$.data.rows[0].remark")

    def test_guard_ignores_allow_listed_keys(self):
        self.assertEqual(scan_phones({"po_number": "6500262904"}), [])

    def test_guard_still_reads_a_phone_named_key(self):
        # allow-list must not shadow a key that names a phone
        self.assertEqual(len(scan_phones({"contact_no": "8295058874"})), 1)

    def test_regex_rejects_a_timestamp(self):
        self.assertIsNone(MOBILE_RE.search("2026-09-03T13:10:20+05:30"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
