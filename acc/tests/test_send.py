"""batch_send — the half that writes, tested for what it refuses to write.

Every test here goes through a REAL round trip: a scan builds a real workbook
and sidecar with FakeSap, the workbook is edited the way an operator would edit
it (only the yellow cells, unless the test is about tampering), and send reads
it back. Nothing contacts SAP.

The two properties that matter most, and the tests that pin them:
  * without --yes, no call to sapb1 ever carries --yes
    -> test_a_preview_never_passes_yes_to_sapb1
  * an unknown outcome halts the run and is never re-sent
    -> test_exit_7_halts_the_batch / test_resume_never_re_sends
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from acc.apbatch import batch_scan, batch_send, batch_status, rules, store, xlsx
from acc.apbatch.sap import (FakeSap, SapRejected, SapUnknownOutcome, SapUnreachable,
                             SapUsage)
from acc.tests.test_scan import GRPOS, VENDORS, grpo, item_line, make_args, tables

TODAY = dt.date(2026, 8, 24)
NOW = dt.datetime(2026, 8, 24, 15, 30, 12)
BATCH = "B260824-OIL-7F3A"

COL = batch_send.COL


def send_args(workbook, **over):
    args = argparse.Namespace(workbook=str(workbook), yes=False, dry_run=False, resume=False,
                              max_age_days=3, env=None, quiet=True)
    for k, v in over.items():
        setattr(args, k, v)
    return args


def send_tables(grpos, drafts=(), posted=(), draft_read=None):
    """What send asks SAP, as opposed to what scan asks.

    Same entities, different questions: one GRPO by DocEntry, one vendor by
    CardCode, the duplicate checks by reference, and the draft read back.
    """
    base = tables(grpos=grpos, drafts=drafts, posted=posted)

    def drafts_table(flt, select, **kw):
        flt = flt or ""
        if select == "DocEntry,Series":
            return []
        if "DocEntry eq" in flt:                       # the read-back
            return [draft_read] if draft_read else []
        return list(drafts)

    def purchase_invoices(flt, select, **kw):
        flt = flt or ""
        if select == "DocEntry,Series":
            return [{"DocEntry": 9, "Series": 4001}] * 40
        if "NumAtCard eq" in flt:
            return list(posted)
        return [{"DocEntry": 41, "NumAtCard": "R41", "DocDate": "2026-08-05",
                 "DocumentSubType": "bod_GSTTaxInvoice", "WTAmount": 0, "Series": 4001,
                 "DocumentLines": [{"WTLiable": "tNO"}]}]

    base["Drafts"] = drafts_table
    base["PurchaseInvoices"] = purchase_invoices
    base["Users"] = [{"InternalKey": 7, "UserCode": "USER36", "UserName": "Navdeep"}]
    return base


def made_draft(entry=90001, num=626089001, **over):
    """What SAP hands back, and what a read-back of it then looks like."""
    draft = {"DocEntry": entry, "DocNum": num, "DocObjectCode": "oPurchaseInvoices",
             "CardCode": "VENDA000777", "CardName": "SUNRISE PACK INDUSTRIES",
             "NumAtCard": "REF/2026080001", "DocDate": "2026-08-18T00:00:00Z",
             "TaxDate": "2026-08-18T00:00:00Z", "DocDueDate": "2026-09-17T00:00:00Z",
             "DocumentStatus": "bost_Open", "AuthorizationStatus": "basGenerated",
             "Series": 4001, "DocumentSubType": "bod_GSTTaxInvoice",
             "BPL_IDAssignedToInvoice": 2, "UserSign": 7, "WTAmount": 0.0,
             "VatSum": 8100.0, "DocTotal": 53100.0, "AttachmentEntry": None,
             "DocumentLines": [{"LineNum": 0, "ItemCode": "PM0000999", "Quantity": 10000,
                                "UnitPrice": 4.5, "LineTotal": 45000.0, "TaxTotal": 8100.0,
                                "TaxCode": "IGST@18", "WarehouseCode": "BH-PM",
                                "WTLiable": "tNO", "BaseType": 20, "BaseEntry": 20001,
                                "BaseLine": 0, "ItemDescription": "PET BOTTLE 500 ML 18 GM",
                                "MeasureUnit": "PCS"}]}
    draft.update(over)
    return draft


class SendCase(unittest.TestCase):
    """A scan, then whatever the test wants to do to its workbook."""

    GRPOS = [GRPOS[0], GRPOS[4]]                    # one READY, one DUPLICATE

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.scan(self.GRPOS)

    # -- building the batch ----------------------------------------------

    def scan(self, grpos, **over):
        sap = FakeSap(tables(grpos=grpos, **over), company="JIVO_OIL_HANADB")
        args = make_args(out=str(self.out), limit=0)
        code = batch_scan.run_scan(args, sap=sap, today=TODAY, now=NOW, batch_id=BATCH,
                                   repo=self.out)
        self.assertEqual(0, code)
        self.book = self.out / store.workbook_name(BATCH)
        self.side = self.out / store.sidecar_name(BATCH)
        return sap

    # -- editing it the way an operator would ------------------------------

    def edit(self, docentry, **cells):
        """Set cells on one row by column letter, then save the workbook back."""
        sheets = xlsx.read_workbook(self.book)
        review = [list(r) for r in sheets["Review"]]
        for row in review[1:]:
            if row[COL["C"]] == docentry:
                for letter, value in cells.items():
                    row[xlsx.column_index(letter)] = value
                break
        else:
            raise AssertionError(f"no row for GRPO DocEntry {docentry}")
        self._write(review, sheets)

    def drop_row(self, docentry):
        sheets = xlsx.read_workbook(self.book)
        review = [list(r) for r in sheets["Review"]
                  if r[COL["C"]] != docentry]
        self._write(review, sheets)

    def _write(self, review, sheets):
        specs = [xlsx.SheetSpec(name="Review", headers=review[0], rows=review[1:],
                                editable=batch_scan.EDITABLE_COLUMNS,
                                validations=batch_scan.VALIDATIONS)]
        for name in ("Lines", "About"):
            if name in sheets:
                rows = [list(r) for r in sheets[name]]
                specs.append(xlsx.SheetSpec(name=name, headers=rows[0], rows=rows[1:]))
        xlsx.write_workbook(self.book, specs)

    def approve(self, docentry, **over):
        cells = {"V": "yes"}
        cells.update(over)
        self.edit(docentry, **cells)

    # -- running send ------------------------------------------------------

    def send(self, sap=None, **flags):
        sap = sap if sap is not None else self.sap_for()
        self.sap = sap
        code = batch_send.run_send(send_args(self.book, **flags), sap=sap, today=TODAY,
                                   now=NOW, repo=self.out)
        return code, sap

    def sap_for(self, grpos=None, drafts=(), posted=(), draft_read=None, allow_writes=True,
                **over):
        sap = FakeSap(send_tables(grpos if grpos is not None else self.GRPOS, drafts=drafts,
                                  posted=posted, draft_read=draft_read),
                      company="JIVO_OIL_HANADB", allow_writes=allow_writes)
        for k, v in over.items():
            setattr(sap, k, v)
        return sap

    def outcomes(self):
        """{GRPO DocEntry: outcome} off the results workbook this run wrote."""
        results = sorted(self.out.glob("results-*.xlsx"))[-1]
        rows = xlsx.read_workbook(results)["Results"][1:]
        return {r[2]: r[7] for r in rows}

    def messages(self):
        results = sorted(self.out.glob("results-*.xlsx"))[-1]
        rows = xlsx.read_workbook(results)["Results"][1:]
        return {r[2]: str(r[13]) for r in rows}

    def journal(self):
        return store.Journal(self.out / store.journal_name(BATCH)).events()

    def sidecar(self):
        return store.Sidecar.load(self.side)


# --------------------------------------------------------------------------
# rows that never reach SAP
# --------------------------------------------------------------------------

class RefusedRowsTest(SendCase):
    def test_a_row_that_was_not_approved_is_skipped(self):
        code, sap = self.send()
        self.assertEqual(0, code)
        self.assertEqual(batch_send.SKIPPED, self.outcomes()[20001])
        self.assertEqual([], sap.writes)

    def test_approving_a_row_the_scan_held_is_refused(self):
        # 20005 is a DUPLICATE. Its Approve? cell is locked in Excel, but a
        # locked cell is a courtesy, not a control: the sidecar decides.
        self.approve(20005)
        code, sap = self.send()
        self.assertEqual(1, code)
        self.assertEqual(batch_send.REFUSED_STATUS, self.outcomes()[20005])
        self.assertIn("DUPLICATE", self.messages()[20005])
        self.assertEqual([], sap.writes)

    def test_a_changed_grey_cell_makes_the_row_refuse(self):
        self.approve(20001)
        self.edit(20001, E="VENDA000636")                  # vendor code, a locked cell
        code, sap = self.send()
        self.assertEqual(1, code)
        self.assertEqual(batch_send.TAMPERED, self.outcomes()[20001])
        message = self.messages()[20001]
        self.assertIn("cell E2", message)                  # the address, both values
        self.assertIn("VENDA000777", message)
        self.assertIn("VENDA000636", message)
        self.assertEqual([], sap.writes)

    def test_a_changed_amount_is_tampering_too(self):
        self.approve(20001)
        self.edit(20001, N=1.0)
        code, _sap = self.send()
        self.assertEqual(1, code)
        self.assertEqual(batch_send.TAMPERED, self.outcomes()[20001])

    def test_excel_reformatting_a_date_is_NOT_tampering(self):
        # Column D holds "2026-08-18"; Excel gives back the serial 46252 when the
        # operator clicks in the cell. Refusing that row would be a false alarm.
        self.approve(20001)
        self.edit(20001, D=rules_serial("2026-08-18"))
        code, _sap = self.send()
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        self.assertEqual(0, code)

    def test_a_blank_tds_cell_forces_a_human_answer(self):
        self.approve(20001, W="")
        code, sap = self.send()
        self.assertEqual(1, code)
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])
        self.assertIn("must say yes or no", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_nonsense_tds_cell_is_refused(self):
        self.approve(20001, W="maybe")
        _code, _sap = self.send()
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])

    def test_an_empty_vendor_reference_is_refused(self):
        self.approve(20001, Y="   ")
        _code, _sap = self.send()
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])
        self.assertIn("NumAtCard", self.messages()[20001])

    def test_a_vendor_reference_longer_than_sap_takes_is_refused(self):
        self.approve(20001, Y="X" * 101)
        _code, _sap = self.send()
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])

    def test_a_bill_date_in_the_future_is_refused(self):
        self.approve(20001, X="2026-12-01")
        _code, _sap = self.send()
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])
        self.assertIn("future", self.messages()[20001])

    def test_a_bill_date_a_year_before_the_goods_receipt_is_refused(self):
        self.approve(20001, X="2025-08-18")
        _code, _sap = self.send()
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])
        self.assertIn("check the year", self.messages()[20001])

    def test_an_unreadable_bill_date_is_refused_not_guessed(self):
        self.approve(20001, X="next tuesday")
        _code, _sap = self.send()
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])

    def test_a_date_typed_in_the_indian_way_is_accepted(self):
        self.approve(20001, X="18/08/2026")
        code, _sap = self.send()
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        self.assertEqual(0, code)


def rules_serial(iso: str) -> int:
    from acc.apbatch import rules
    return rules.to_excel_serial(iso)


# --------------------------------------------------------------------------
# SAP has moved on since the scan
# --------------------------------------------------------------------------

class StaleTest(SendCase):
    def test_a_grpo_closed_since_the_scan_is_stale(self):
        closed = dict(GRPOS[0], DocumentStatus="bost_Close")
        self.approve(20001)
        code, sap = self.send(sap=self.sap_for(grpos=[closed, GRPOS[4]]))
        self.assertEqual(1, code)
        self.assertEqual(batch_send.STALE, self.outcomes()[20001])
        self.assertIn("somebody invoiced it", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_cancelled_grpo_is_stale(self):
        cancelled = dict(GRPOS[0], Cancelled="tYES")
        self.approve(20001)
        _code, sap = self.send(sap=self.sap_for(grpos=[cancelled, GRPOS[4]]))
        self.assertEqual(batch_send.STALE, self.outcomes()[20001])
        self.assertEqual([], sap.writes)

    def test_a_quantity_that_changed_since_the_scan_is_stale(self):
        # Half of it was invoiced by somebody else this morning. The money on the
        # sheet is no longer this document's money.
        moved = dict(GRPOS[0], DocumentLines=[item_line(RemainingOpenQuantity=5000)])
        self.approve(20001)
        _code, sap = self.send(sap=self.sap_for(grpos=[moved, GRPOS[4]]))
        self.assertEqual(batch_send.STALE, self.outcomes()[20001])
        self.assertIn("5000 open", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_line_closed_since_the_scan_is_stale(self):
        moved = dict(GRPOS[0], DocumentLines=[item_line(LineStatus="bost_Close")])
        self.approve(20001)
        _code, _sap = self.send(sap=self.sap_for(grpos=[moved, GRPOS[4]]))
        self.assertEqual(batch_send.STALE, self.outcomes()[20001])

    def test_a_vendor_frozen_since_the_scan_is_stale(self):
        frozen = [dict(VENDORS[0], Frozen="tYES")] + VENDORS[1:]
        sap = self.sap_for()
        sap.tables["BusinessPartners"] = frozen
        self.approve(20001)
        _code, sap = self.send(sap=sap)
        self.assertEqual(batch_send.STALE, self.outcomes()[20001])
        self.assertIn("FROZEN", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_bill_keyed_by_somebody_else_since_the_scan_is_a_stale_duplicate(self):
        posted = [{"DocEntry": 49999, "DocNum": 62608999, "CardCode": "VENDA000777",
                   "DocDate": "2026-08-23", "DocTotal": 53100.0, "Cancelled": "tNO",
                   "NumAtCard": "REF/2026080001"}]
        self.approve(20001)
        code, sap = self.send(sap=self.sap_for(posted=posted))
        self.assertEqual(1, code)
        self.assertEqual(batch_send.STALE_DUPLICATE, self.outcomes()[20001])
        self.assertIn("49999", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_draft_keyed_on_this_grpo_since_the_scan_is_a_stale_duplicate(self):
        draft = {"DocEntry": 54999, "DocNum": 626080999, "CardCode": "VENDA000777",
                 "NumAtCard": "typo", "DocTotal": 53100.0, "UserSign": 7,
                 "DocumentStatus": "bost_Open", "Cancelled": "tNO",
                 "DocumentLines": [{"BaseType": 20, "BaseEntry": 20001, "BaseLine": 0}]}
        self.approve(20001)
        _code, sap = self.send(sap=self.sap_for(drafts=[draft]))
        self.assertEqual(batch_send.STALE_DUPLICATE, self.outcomes()[20001])
        self.assertIn("54999", self.messages()[20001])
        self.assertEqual([], sap.writes)


# --------------------------------------------------------------------------
# preview
# --------------------------------------------------------------------------

class PreviewTest(SendCase):
    def test_a_preview_never_passes_yes_to_sapb1(self):
        """The structural guarantee, asserted on the real code path.

        `--yes` appears in batch_send.py inside one `if sending:` branch. This
        runs the whole command without it and checks every single call.
        """
        self.approve(20001)
        code, sap = self.send()
        self.assertEqual(0, code)
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        self.assertTrue(sap.writes, "the dry run itself should have happened")
        for call in sap.writes:
            self.assertTrue(call["dry_run"], call)
            self.assertFalse(call["yes"], call)

    def test_dry_run_wins_over_yes(self):
        self.approve(20001)
        code, sap = self.send(yes=True, dry_run=True)
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        self.assertEqual(0, code)
        for call in sap.writes:
            self.assertFalse(call["yes"], call)

    def test_the_preview_writes_the_exact_payload_to_a_file(self):
        self.approve(20001, W="yes", Z="gate 154")
        self.send()
        payload = json.loads((self.out / "payloads" / "20001.json").read_text())
        self.assertEqual("VENDA000777", payload["CardCode"])
        self.assertEqual("2026-08-18", payload["DocDate"])       # C-0017, the GRPO's date
        self.assertEqual("REF/2026080001", payload["NumAtCard"])
        self.assertEqual("tYES", payload["DocumentLines"][0]["WTLiable"])
        self.assertEqual(10000, payload["DocumentLines"][0]["Quantity"])
        self.assertEqual(20001, payload["DocumentLines"][0]["BaseEntry"])

    def test_the_batch_tag_travels_in_comments(self):
        self.approve(20001, Z="gate 154")
        self.send()
        payload = json.loads((self.out / "payloads" / "20001.json").read_text())
        self.assertIn(BATCH, payload["Comments"])
        self.assertIn("gate 154", payload["Comments"])
        self.assertIn("Based On Goods Receipt PO", payload["Comments"])
        self.assertLessEqual(len(payload["Comments"]), 254)

    def test_a_dry_run_transcript_is_kept(self):
        self.approve(20001)
        self.send()
        transcripts = list(self.out.glob("dryrun-*.txt"))
        self.assertEqual(1, len(transcripts))
        text = transcripts[0].read_text(encoding="utf-8")
        self.assertIn("GRPO DocEntry 20001", text)
        self.assertIn("VENDA000777", text)

    def test_nothing_is_recorded_as_an_outcome_by_a_preview(self):
        self.approve(20001)
        self.send()
        self.assertIsNone(self.sidecar().row(20001)["outcome"])


# --------------------------------------------------------------------------
# sending
# --------------------------------------------------------------------------

class SendingTest(SendCase):
    def test_the_happy_path_creates_a_draft_and_records_it(self):
        self.approve(20001)
        sap = self.sap_for(draft_read=made_draft(AttachmentEntry=170999))
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(0, code)
        self.assertEqual(batch_send.CREATED, self.outcomes()[20001])

        drafts = [w for w in sap.writes if w["kind"] == "draft" and not w["dry_run"]]
        self.assertEqual(1, len(drafts))
        self.assertTrue(drafts[0]["yes"])

        outcome = self.sidecar().row(20001)["outcome"]
        self.assertEqual("CREATED", outcome["state"])
        self.assertEqual(90001, outcome["draft_entry"])

    def test_the_journal_records_the_write_before_and_after_it_happens(self):
        self.approve(20001)
        self.send(sap=self.sap_for(draft_read=made_draft(AttachmentEntry=170999)), yes=True)
        drafts = [e for e in self.journal() if e.get("event") == "draft"]
        self.assertEqual(["sending", "created"], [e["state"] for e in drafts])
        self.assertEqual(20001, drafts[0]["docentry"])
        self.assertIn("payload_file", drafts[0])       # the bytes are on disk before the send

    def test_the_attachment_pointer_is_patched_from_the_LIVE_grpo(self):
        # The GRPO gained its bill after the scan. The live value is the one that
        # gets patched, and the change is reported.
        scanned_without = dict(GRPOS[0], AttachmentEntry=None)
        self.scan([scanned_without, GRPOS[4]])
        self.approve(20001)
        sap = self.sap_for(grpos=[dict(GRPOS[0], AttachmentEntry=171555), GRPOS[4]],
                           draft_read=made_draft(AttachmentEntry=171555))
        _code, sap = self.send(sap=sap, yes=True)
        patches = [w for w in sap.writes if w["kind"] == "patch"]
        self.assertEqual(1, len(patches))
        self.assertEqual("Drafts(90001)", patches[0]["target"])
        self.assertEqual({"AttachmentEntry": 171555}, patches[0]["payload"])
        self.assertIn("attachment changed", " ".join(self._flags(20001)))

    def test_a_draft_that_came_back_wrong_is_created_with_gaps(self):
        # TDS was asked for and the draft came out 0 — C-0018, the thing an
        # operator has to tick in the client before Add.
        self.approve(20001, W="yes")
        sap = self.sap_for(draft_read=made_draft(AttachmentEntry=170999, WTAmount=0.0))
        code, _sap = self.send(sap=sap, yes=True)
        self.assertEqual(1, code)
        self.assertEqual(batch_send.CREATED_WITH_GAPS, self.outcomes()[20001])
        self.assertIn("TDS", " ".join(self._flags(20001)))

    def test_sap_saying_no_stops_that_row_and_only_that_row(self):
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        sap = self.sap_for(grpos=rows, draft_read=made_draft(AttachmentEntry=170999))
        sap.draft_results = [SapRejected("[-5002] Series is not defined", code=6),
                             {"DocEntry": 90002, "DocNum": 626089002}]
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(1, code)
        self.assertEqual(batch_send.REJECTED, self.outcomes()[20001])
        self.assertIn("-5002", self.messages()[20001])
        self.assertIn(self.outcomes()[20007], batch_send.MADE_A_DRAFT)
        self.assertEqual(2, len([w for w in sap.writes
                                 if w["kind"] == "draft" and not w["dry_run"]]))

    def test_exit_7_halts_the_batch(self):
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        sap = self.sap_for(grpos=rows, draft_read=made_draft(AttachmentEntry=170999))
        sap.draft_results = [SapUnknownOutcome("no answer came back", code=7),
                             {"DocEntry": 90002, "DocNum": 626089002}]
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN, self.outcomes()[20001])
        self.assertEqual(batch_send.NOT_ATTEMPTED, self.outcomes()[20007])
        # exactly ONE real write happened: the halt is real, not cosmetic
        self.assertEqual(1, len([w for w in sap.writes
                                 if w["kind"] == "draft" and not w["dry_run"]]))
        self.assertEqual("UNKNOWN", self.sidecar().row(20001)["outcome"]["state"])
        self.assertEqual([20001], store.Journal(
            self.out / store.journal_name(BATCH)).in_flight())

    def test_a_row_this_batch_already_created_is_never_sent_twice(self):
        self.approve(20001)
        self.send(sap=self.sap_for(draft_read=made_draft(AttachmentEntry=170999)), yes=True)
        code, sap = self.send(sap=self.sap_for(draft_read=made_draft(AttachmentEntry=170999)),
                              yes=True)
        self.assertEqual(0, code)
        self.assertEqual(batch_send.ALREADY_CREATED, self.outcomes()[20001])
        self.assertEqual([], [w for w in sap.writes if not w["dry_run"]])

    def test_an_unknown_row_blocks_a_re_run_until_someone_looks(self):
        self.approve(20001)
        sap = self.sap_for()
        sap.draft_results = [SapUnknownOutcome("no answer came back", code=7)]
        self.send(sap=sap, yes=True)
        code, sap = self.send(sap=self.sap_for(), yes=True)      # no --resume
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN, self.outcomes()[20001])
        self.assertIn("--resume", self.messages()[20001])
        self.assertEqual([], [w for w in sap.writes if not w["dry_run"]])

    def _flags(self, docentry):
        results = sorted(self.out.glob("results-*.xlsx"))[-1]
        rows = xlsx.read_workbook(results)["Results"][1:]
        return [str(r[12]) for r in rows if r[2] == docentry]


# --------------------------------------------------------------------------
# resume
# --------------------------------------------------------------------------

class ResumeTest(SendCase):
    def leave_an_unknown_row(self):
        self.approve(20001)
        sap = self.sap_for()
        sap.draft_results = [SapUnknownOutcome("no answer came back", code=7)]
        self.send(sap=sap, yes=True)

    def test_resume_adopts_the_draft_the_unknown_outcome_left_behind(self):
        self.leave_an_unknown_row()
        orphan = {"DocEntry": 90055, "DocNum": 626089055, "CardCode": "VENDA000777",
                  "NumAtCard": "REF/2026080001", "DocTotal": 53100.0, "UserSign": 7,
                  "DocumentStatus": "bost_Open", "Cancelled": "tNO", "WTAmount": 0.0,
                  "AttachmentEntry": 170999,
                  "DocumentLines": [{"LineNum": 0, "Quantity": 10000, "BaseType": 20,
                                     "BaseEntry": 20001, "BaseLine": 0}]}
        code, sap = self.send(sap=self.sap_for(drafts=[orphan]), yes=True, resume=True)
        self.assertEqual(batch_send.CREATED_RECOVERED, self.outcomes()[20001])
        self.assertEqual(0, code)
        self.assertEqual(90055, self.sidecar().row(20001)["outcome"]["draft_entry"])
        self.assertEqual([], [w for w in sap.writes if w["kind"] == "draft"],
                         "resume looks; it never sends")

    def test_resume_without_yes_adopts_but_does_not_patch(self):
        # --resume is a LOOK. Adopting the draft it finds is a read; pointing
        # that draft at the bill is a write, and this run was not given --yes.
        self.leave_an_unknown_row()
        orphan = {"DocEntry": 90055, "DocNum": 626089055, "CardCode": "VENDA000777",
                  "NumAtCard": "REF/2026080001", "DocTotal": 53100.0, "UserSign": 7,
                  "DocumentStatus": "bost_Open", "Cancelled": "tNO", "WTAmount": 0.0,
                  "AttachmentEntry": None,
                  "DocumentLines": [{"LineNum": 0, "Quantity": 10000, "BaseType": 20,
                                     "BaseEntry": 20001, "BaseLine": 0}]}
        _code, sap = self.send(sap=self.sap_for(drafts=[orphan]), resume=True)
        self.assertEqual(batch_send.CREATED_RECOVERED, self.outcomes()[20001])
        self.assertEqual([], sap.writes, "a preview writes nothing at all")

    def test_resume_with_yes_does_patch_the_recovered_draft(self):
        self.leave_an_unknown_row()
        orphan = {"DocEntry": 90055, "DocNum": 626089055, "CardCode": "VENDA000777",
                  "NumAtCard": "REF/2026080001", "DocTotal": 53100.0, "UserSign": 7,
                  "DocumentStatus": "bost_Open", "Cancelled": "tNO", "WTAmount": 0.0,
                  "AttachmentEntry": None,
                  "DocumentLines": [{"LineNum": 0, "Quantity": 10000, "BaseType": 20,
                                     "BaseEntry": 20001, "BaseLine": 0}]}
        _code, sap = self.send(sap=self.sap_for(drafts=[orphan]), yes=True, resume=True)
        patches = [w for w in sap.writes if w["kind"] == "patch"]
        self.assertEqual(1, len(patches))
        self.assertEqual("Drafts(90055)", patches[0]["target"])
        self.assertEqual([], [w for w in sap.writes if w["kind"] == "draft"])

    def test_resume_never_re_sends_when_it_finds_nothing(self):
        self.leave_an_unknown_row()
        code, sap = self.send(sap=self.sap_for(), yes=True, resume=True)
        self.assertEqual(7, code)          # still unaccounted for: go and look
        self.assertEqual(batch_send.UNKNOWN_UNRESOLVED, self.outcomes()[20001])
        self.assertIn("NOT re-sent", self.messages()[20001])
        self.assertEqual([], [w for w in sap.writes if w["kind"] == "draft"])

    def test_resume_reports_several_matches_instead_of_choosing(self):
        self.leave_an_unknown_row()
        twins = [{"DocEntry": e, "DocNum": 626089000 + e, "CardCode": "VENDA000777",
                  "NumAtCard": "REF/2026080001", "DocTotal": 53100.0, "UserSign": 7,
                  "DocumentStatus": "bost_Open", "Cancelled": "tNO",
                  "DocumentLines": [{"BaseType": 20, "BaseEntry": 20001, "BaseLine": 0}]}
                 for e in (90055, 90056)]
        code, sap = self.send(sap=self.sap_for(drafts=twins), yes=True, resume=True)
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN_UNRESOLVED, self.outcomes()[20001])
        self.assertIn("90055", self.messages()[20001])
        self.assertIn("90056", self.messages()[20001])
        self.assertEqual([], [w for w in sap.writes if w["kind"] == "draft"])


# --------------------------------------------------------------------------
# preconditions — nothing is contacted at all
# --------------------------------------------------------------------------

class PreconditionTest(SendCase):
    def test_a_workbook_that_is_not_there(self):
        code = batch_send.run_send(send_args(self.out / "nope.xlsx"), sap=self.sap_for(),
                                   today=TODAY, now=NOW, repo=self.out)
        self.assertEqual(2, code)

    def test_a_sidecar_that_is_not_there(self):
        self.side.unlink()
        code, sap = self.send()
        self.assertEqual(2, code)
        self.assertEqual([], sap.calls)

    def test_a_batch_older_than_the_limit_is_refused(self):
        code = batch_send.run_send(send_args(self.book), sap=self.sap_for(), today=TODAY,
                                   now=NOW + dt.timedelta(days=4), repo=self.out)
        self.assertEqual(2, code)

    def test_an_old_batch_can_be_sent_when_the_limit_is_lifted(self):
        self.approve(20001)
        code = batch_send.run_send(send_args(self.book, max_age_days=0), sap=self.sap_for(),
                                   today=TODAY, now=NOW + dt.timedelta(days=40), repo=self.out)
        self.assertEqual(0, code)

    def test_a_workbook_sent_against_the_wrong_company_is_refused(self):
        sap = self.sap_for()
        sap.company_db = "JIVO_MART_HANADB"
        code, sap = self.send(sap=sap)
        self.assertEqual(2, code)
        self.assertEqual([], sap.writes)

    def test_a_row_deleted_from_the_sheet_is_refused(self):
        self.drop_row(20005)
        code, sap = self.send()
        self.assertEqual(2, code)
        self.assertEqual([], sap.calls)

    def test_a_sidecar_from_another_batch_is_refused(self):
        data = json.loads(self.side.read_text())
        data["batch_id"] = "B260824-OIL-0000"
        self.side.write_text(json.dumps(data))
        code, _sap = self.send()
        self.assertEqual(2, code)


# --------------------------------------------------------------------------
# status
# --------------------------------------------------------------------------

class StatusTest(SendCase):
    def test_status_reports_what_the_batch_did(self):
        import contextlib
        import io
        self.approve(20001)
        self.send(sap=self.sap_for(draft_read=made_draft(AttachmentEntry=170999)), yes=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = batch_status.run_status(argparse.Namespace(workbook=str(self.book)),
                                           repo=self.out)
        text = buf.getvalue()
        self.assertEqual(0, code)
        self.assertIn(BATCH, text)
        self.assertIn("CREATED", text)
        self.assertIn("draft 90001", text)
        self.assertIn(f"grep {BATCH} queries/*/sap-writes.jsonl", text)

    def test_status_finds_a_draft_the_sidecar_never_recorded(self):
        """The journal is written before the sidecar. A crash between the two
        leaves the only record of the draft in the journal — and that is the
        moment somebody needs the DocEntry most."""
        import contextlib
        import io
        self.approve(20001)
        self.send(sap=self.sap_for(draft_read=made_draft(AttachmentEntry=170999)), yes=True)
        data = json.loads(self.side.read_text(encoding="utf-8"))
        data["rows"]["20001"]["outcome"] = None          # the sidecar save never happened
        self.side.write_text(json.dumps(data), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            batch_status.run_status(argparse.Namespace(workbook=str(self.book)), repo=self.out)
        text = buf.getvalue()
        self.assertIn("90001", text)
        self.assertIn("journal", text.lower())

    def test_status_names_a_row_that_was_never_answered(self):
        import contextlib
        import io
        self.approve(20001)
        sap = self.sap_for()
        sap.draft_results = [SapUnknownOutcome("no answer came back", code=7)]
        self.send(sap=sap, yes=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            batch_status.run_status(argparse.Namespace(workbook=str(self.book)), repo=self.out)
        text = buf.getvalue()
        self.assertIn("sent and never answered", text)
        self.assertIn("--resume", text)


# --------------------------------------------------------------------------
# a fake that answers the way the Service Layer answers
# --------------------------------------------------------------------------

_EQ = re.compile(r"(\w+) eq '([^']*)'")


def _eq_match(flt, row, fields=("NumAtCard", "CardCode")):
    """Honour the `Field eq 'value'` clauses of a filter, exactly, OR within a field.

    The Service Layer matches NumAtCard as the string it is: asking for
    `2633100542` does NOT find `.2633100542`. A fake that ignores the filter
    cannot show that, which is how the one-directional reference check survived.
    """
    for field in fields:
        values = {v for f, v in _EQ.findall(flt or "") if f == field}
        if values and str(row.get(field) or "") not in values:
            return False
    return True


def service_layer_sap(grpos, drafts=(), posted=(), draft_read=None, cap=20,
                      allow_writes=True, **over):
    """FakeSap with the two behaviours the plain fixture does not have.

    A query without `--all` comes back ONE PAGE long (20 rows, the CLI's default
    --top), and `eq` means eq. Both are needed to reproduce a duplicate that was
    the 25th open draft, and one spelled with a leading dot.
    """
    base = tables(grpos=grpos)
    drafts, posted = list(drafts), list(posted)

    def grpo_table(flt, select, orderby=None, top=None, all=False, page_size=None):
        m = re.search(r"DocEntry eq (\d+)", flt or "")
        return [g for g in grpos if g["DocEntry"] == int(m.group(1))] if m else list(grpos)

    def drafts_table(flt, select, orderby=None, top=None, all=False, page_size=None):
        flt = flt or ""
        if select == "DocEntry,Series":
            return []
        if "DocEntry eq" in flt:
            return [draft_read] if draft_read else []
        rows = [d for d in drafts if _eq_match(flt, d)]
        return rows if all else rows[:cap]

    def posted_table(flt, select, orderby=None, top=None, all=False, page_size=None):
        flt = flt or ""
        if select == "DocEntry,Series":
            return [{"DocEntry": 9, "Series": 4001}] * 40
        rows = [p for p in posted if _eq_match(flt, p)]
        return rows if all else rows[:cap]

    base["PurchaseDeliveryNotes"] = grpo_table
    base["Drafts"] = drafts_table
    base["PurchaseInvoices"] = posted_table
    base["Users"] = [{"InternalKey": 7, "UserCode": "USER36", "UserName": "Navdeep"}]
    sap = FakeSap(base, company="JIVO_OIL_HANADB", allow_writes=allow_writes)
    for k, v in over.items():
        setattr(sap, k, v)
    return sap


def open_draft(entry, ref="OTHER", card="VENDA000777", grpo_entry=None, **over):
    """One open A/P draft as the duplicate sweep sees it."""
    draft = {"DocEntry": entry, "DocNum": 626080000 + entry, "CardCode": card,
             "NumAtCard": ref, "DocTotal": 53100.0, "UserSign": 7, "Comments": "",
             "DocumentStatus": "bost_Open", "Cancelled": "tNO", "WTAmount": 0.0,
             "AuthorizationStatus": "basGenerated", "AttachmentEntry": None,
             "DocumentLines": [{"LineNum": 0, "Quantity": 10000, "BaseType": 20,
                                "BaseEntry": grpo_entry, "BaseLine": 0}] if grpo_entry
             else [{"LineNum": 0, "Quantity": 10000, "BaseType": -1, "BaseEntry": None}]}
    draft.update(over)
    return draft


def sweeps(sap):
    """The four duplicate-sweep reads of one row, by what they ask."""
    out = {}
    for c in sap.calls:
        flt, entity = c["filter"] or "", c["entity"]
        if entity == "Drafts" and "DocEntry eq" not in flt:
            out["drafts_by_ref" if "NumAtCard eq" in flt else "drafts_by_vendor"] = c
        elif entity == "PurchaseInvoices" and c["select"] != "DocEntry,Series":
            out["posted_by_ref" if "NumAtCard eq" in flt else "posted_by_vendor"] = c
    return out


# --------------------------------------------------------------------------
# C1 — the re-validation reads must not stop at the first page
# --------------------------------------------------------------------------

class DuplicateSweepTest(SendCase):
    def test_every_duplicate_sweep_asks_for_every_row(self):
        self.approve(20001)
        sap = service_layer_sap(self.GRPOS)
        code, sap = self.send(sap=sap)
        found = sweeps(sap)
        for name in ("drafts_by_ref", "drafts_by_vendor", "posted_by_ref", "posted_by_vendor"):
            self.assertIn(name, found, f"{name} was never asked")
            self.assertTrue(found[name]["all"], f"{name} is capped at the CLI's default --top 20")
            self.assertIsNone(found[name]["top"], f"{name} passes --top, which --all ignores")

    def test_the_twenty_fifth_open_draft_is_still_a_duplicate(self):
        # 24 of this vendor's open drafts are other bills; the 25th is this GRPO,
        # keyed in the client with a typo'd reference. One page of 20 misses it.
        others = [open_draft(60000 + n, ref=f"OTHER/{n}") for n in range(24)]
        keyed = open_draft(60024, ref="typo", grpo_entry=20001)
        self.approve(20001)
        sap = service_layer_sap(self.GRPOS, drafts=others + [keyed])
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(batch_send.STALE_DUPLICATE, self.outcomes()[20001])
        self.assertIn("60024", self.messages()[20001])
        self.assertEqual([], sap.writes)
        self.assertEqual(1, code)


# --------------------------------------------------------------------------
# H1 — the same reference, spelled the other way round
# --------------------------------------------------------------------------

class RefVariantTest(SendCase):
    def test_a_draft_whose_ref_only_differs_by_a_leading_dot_is_a_duplicate(self):
        # Live shape (Oil, 2026-08-24): one bill, `.2633100542` on one document
        # and `2633100542` on the other. Asking SAP for ours does not find theirs.
        self.approve(20001, Y="2633100542")
        theirs = open_draft(61001, ref=".2633100542")
        sap = service_layer_sap(self.GRPOS, drafts=[theirs])
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(batch_send.STALE_DUPLICATE, self.outcomes()[20001])
        self.assertIn("61001", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_posted_invoice_whose_ref_only_differs_by_a_leading_dot_is_a_duplicate(self):
        self.approve(20001, Y="2633100542")
        theirs = {"DocEntry": 47777, "DocNum": 62604777, "CardCode": "VENDA000777",
                  "DocDate": "2026-08-20", "DocTotal": 53100.0, "Cancelled": "tNO",
                  "NumAtCard": ".2633100542"}
        sap = service_layer_sap(self.GRPOS, posted=[theirs])
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(batch_send.STALE_DUPLICATE, self.outcomes()[20001])
        self.assertIn("47777", self.messages()[20001])
        self.assertEqual([], sap.writes)

    def test_a_different_reference_is_not_a_duplicate(self):
        # The normalizer must not turn every reference into every other one.
        self.approve(20001, Y="2633100542")
        other = open_draft(61002, ref="26-27/1450")
        sap = service_layer_sap(self.GRPOS, drafts=[other],
                                draft_read=made_draft(AttachmentEntry=170999))
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(batch_send.CREATED, self.outcomes()[20001])


# --------------------------------------------------------------------------
# C3 — a write that answered without saying what it made
# --------------------------------------------------------------------------

class UnknownAnswerTest(SendCase):
    def two_rows(self):
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        return rows

    def test_a_write_that_answers_with_no_docentry_is_UNKNOWN_and_halts(self):
        # SAP answered 204 No Content. The draft may well exist; nothing in that
        # answer says which one it is, so it cannot be called CREATED.
        rows = self.two_rows()
        sap = service_layer_sap(rows, draft_read=made_draft(AttachmentEntry=170999))
        sap.draft_result = {"status": 204}
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN, self.outcomes()[20001])
        self.assertEqual(batch_send.NOT_ATTEMPTED, self.outcomes()[20007])
        self.assertEqual("UNKNOWN", self.sidecar().row(20001)["outcome"]["state"])
        self.assertIn("no DocEntry", self.messages()[20001])
        self.assertEqual([20001], store.Journal(
            self.out / store.journal_name(BATCH)).in_flight())
        self.assertEqual([], [w for w in sap.writes if w["kind"] == "patch"],
                         "nothing may be patched when we do not know what was made")

    def test_a_docentry_that_is_not_a_number_is_UNKNOWN_too(self):
        self.approve(20001)
        sap = service_layer_sap(self.GRPOS)
        sap.draft_result = {"DocEntry": "", "DocNum": None}
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN, self.outcomes()[20001])

    def test_a_run_that_halts_still_writes_its_results_and_closes_the_journal(self):
        rows = self.two_rows()
        sap = service_layer_sap(rows)
        sap.draft_result = {"status": 204}
        self.send(sap=sap, yes=True)
        self.assertTrue(sorted(self.out.glob("results-*.xlsx")), "no results workbook")
        self.assertTrue([e for e in self.journal() if e.get("event") == "send-end"],
                        "the journal never recorded the end of the run")


# --------------------------------------------------------------------------
# C2 — --resume may only adopt a draft it has evidence it created
# --------------------------------------------------------------------------

class ForeignDraftTest(SendCase):
    def leave_an_unknown_row(self, rows=None):
        self.approve(20001)
        sap = service_layer_sap(rows or self.GRPOS)
        sap.draft_results = [SapUnknownOutcome("no answer came back", code=7)]
        self.send(sap=sap, yes=True)

    def test_resume_will_not_adopt_a_draft_somebody_else_keyed(self):
        # Neetu keyed this bill by hand between the halt and the resume. Her
        # draft matches on reference and GRPO and is NOT ours.
        self.leave_an_unknown_row()
        neetu = open_draft(55123, ref="REF/2026080001", grpo_entry=20001, UserSign=42,
                           AuthorizationStatus="basPending",
                           Comments="keyed by hand, nothing to do with any batch")
        code, sap = self.send(sap=service_layer_sap(self.GRPOS, drafts=[neetu]),
                              yes=True, resume=True)
        self.assertEqual(batch_send.FOREIGN_DRAFT_FOUND, self.outcomes()[20001])
        self.assertEqual([], sap.writes, "a draft we did not make is never touched")
        message = self.messages()[20001]
        for token in ("55123", "42", "basPending"):
            self.assertIn(token, message)
        self.assertEqual(1, code)
        self.assertNotEqual("CREATED-RECOVERED",
                            (self.sidecar().row(20001)["outcome"] or {}).get("state"))

    def test_resume_adopts_a_draft_that_carries_this_batch_id(self):
        self.leave_an_unknown_row()
        ours = open_draft(55124, ref="REF/2026080001", UserSign=99,
                          AttachmentEntry=170999,
                          Comments=f"Based On Goods Receipt PO 2026080001. {BATCH}")
        code, sap = self.send(sap=service_layer_sap(self.GRPOS, drafts=[ours]),
                              yes=True, resume=True)
        self.assertEqual(batch_send.CREATED_RECOVERED, self.outcomes()[20001])
        self.assertEqual(55124, self.sidecar().row(20001)["outcome"]["draft_entry"])

    def test_resume_adopts_a_draft_this_login_made_from_this_grpo(self):
        self.leave_an_unknown_row()
        ours = open_draft(55125, ref="anything", grpo_entry=20001, UserSign=7,
                          AttachmentEntry=170999)
        code, sap = self.send(sap=service_layer_sap(self.GRPOS, drafts=[ours]),
                              yes=True, resume=True)
        self.assertEqual(batch_send.CREATED_RECOVERED, self.outcomes()[20001])


# --------------------------------------------------------------------------
# H2 — --resume resolves the unknown row BEFORE it sends anything else
# --------------------------------------------------------------------------

class ResumeOrderTest(SendCase):
    def two_rows_one_unknown(self):
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        sap = service_layer_sap(rows)
        sap.draft_results = [SapUnknownOutcome("no answer", code=7)]
        self.send(sap=sap, yes=True)
        return rows

    def real_writes(self, sap):
        return [(w["kind"], w.get("target") or Path(w.get("data_file") or "").name)
                for w in sap.writes if not w.get("dry_run")]

    def test_the_unknown_row_is_resolved_before_the_other_rows_are_sent(self):
        rows = self.two_rows_one_unknown()
        ours = open_draft(90055, ref="REF/2026080001", grpo_entry=20001, UserSign=7)
        sap = service_layer_sap(rows, drafts=[ours],
                                draft_read=made_draft(AttachmentEntry=170999))
        code, sap = self.send(sap=sap, yes=True, resume=True)
        self.assertEqual(batch_send.CREATED_RECOVERED, self.outcomes()[20001])
        self.assertIn(self.outcomes()[20007], batch_send.MADE_A_DRAFT)
        order = self.real_writes(sap)
        self.assertEqual(("patch", "Drafts(90055)"), order[0],
                         f"the unknown row must be settled first, got {order}")
        self.assertEqual(("draft", "20007.json"), order[1])

    def test_an_unresolved_unknown_stops_the_run_from_sending_anything_else(self):
        rows = self.two_rows_one_unknown()
        sap = service_layer_sap(rows)                      # nothing to find
        code, sap = self.send(sap=sap, yes=True, resume=True)
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN_UNRESOLVED, self.outcomes()[20001])
        self.assertEqual(batch_send.NOT_ATTEMPTED, self.outcomes()[20007])
        self.assertEqual([], [w for w in sap.writes if not w.get("dry_run")])

    def test_a_foreign_draft_stops_the_run_from_sending_anything_else(self):
        rows = self.two_rows_one_unknown()
        neetu = open_draft(55123, ref="REF/2026080001", grpo_entry=20001, UserSign=42)
        sap = service_layer_sap(rows, drafts=[neetu])
        code, sap = self.send(sap=sap, yes=True, resume=True)
        self.assertEqual(1, code)
        self.assertEqual(batch_send.FOREIGN_DRAFT_FOUND, self.outcomes()[20001])
        self.assertEqual(batch_send.NOT_ATTEMPTED, self.outcomes()[20007])
        self.assertEqual([], sap.writes)

    def test_a_halted_resume_still_says_what_it_found(self):
        rows = self.two_rows_one_unknown()
        sap = service_layer_sap(rows)
        args = send_args(self.book, yes=True, resume=True)
        args.quiet = False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = batch_send.run_send(args, sap=sap, today=TODAY, now=NOW, repo=self.out)
        text = buf.getvalue()
        self.assertEqual(7, code)
        self.assertIn("2026080001", text, "the unknown row was never reported")
        self.assertIn(batch_send.UNKNOWN_UNRESOLVED, text)


# --------------------------------------------------------------------------
# M2 — an unknown row without --resume
# --------------------------------------------------------------------------

class UnknownWithoutResumeTest(SendCase):
    def test_an_unresolved_row_halts_the_next_run_at_exit_7(self):
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        sap = service_layer_sap(rows)
        sap.draft_results = [SapUnknownOutcome("no answer came back", code=7)]
        self.send(sap=sap, yes=True)
        code, sap = self.send(sap=service_layer_sap(rows), yes=True)      # no --resume
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN, self.outcomes()[20001])
        self.assertIn("--resume", self.messages()[20001])
        self.assertEqual(batch_send.NOT_ATTEMPTED, self.outcomes()[20007])
        self.assertEqual([], [w for w in sap.writes if not w["dry_run"]])


# --------------------------------------------------------------------------
# M4 / M5 — a row that raises, and a SapError nobody planned for
# --------------------------------------------------------------------------

class RowFailureTest(SendCase):
    def test_junk_in_the_row_number_column_does_not_crash_the_run(self):
        # Column A is neither locked nor editable, so `one` typed into it used to
        # end the whole run in int('one') — after earlier rows had been drafted.
        self.approve(20001)
        self.edit(20001, A="one")
        code, sap = self.send(sap=service_layer_sap(self.GRPOS))
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        self.assertIn("column A", " ".join(self._flags(20001)))
        self.assertTrue(sorted(self.out.glob("results-*.xlsx")))

    def test_a_cell_that_cannot_be_read_at_all_refuses_only_that_row(self):
        class Exploding(str):
            def strip(self):
                raise RuntimeError("this cell is not a string at all")

        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        real = batch_send._validate_inputs

        def explode_on_20001(cells, entry, today, ref=None):
            if entry.get("row") == 1:
                raise RuntimeError("this cell is not a string at all")
            return real(cells, entry, today, ref=ref)

        batch_send._validate_inputs = explode_on_20001
        self.addCleanup(setattr, batch_send, "_validate_inputs", real)
        code, sap = self.send(sap=service_layer_sap(rows,
                                                    draft_read=made_draft(AttachmentEntry=170999)),
                              yes=True)
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])
        self.assertIn("not a string at all", self.messages()[20001])
        self.assertIn(self.outcomes()[20007], batch_send.MADE_A_DRAFT)

    def _flags(self, docentry):
        results = sorted(self.out.glob("results-*.xlsx"))[-1]
        rows = xlsx.read_workbook(results)["Results"][1:]
        return [str(r[12]) for r in rows if r[2] == docentry]

    def test_a_sap_error_nobody_planned_for_at_the_write_is_UNKNOWN(self):
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        sap = service_layer_sap(rows)
        sap.draft_results = [SapUsage("something this build has never seen", code=2)]
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(7, code)
        self.assertEqual(batch_send.UNKNOWN, self.outcomes()[20001])
        self.assertEqual(batch_send.NOT_ATTEMPTED, self.outcomes()[20007])
        self.assertTrue([e for e in self.journal() if e.get("event") == "send-end"])


# --------------------------------------------------------------------------
# M1 — the attachment the GRPO no longer carries
# --------------------------------------------------------------------------

class AttachmentTest(SendCase):
    def test_an_attachment_removed_since_the_scan_is_not_patched(self):
        gone = dict(GRPOS[0], AttachmentEntry=None)
        self.approve(20001)
        sap = service_layer_sap([gone, GRPOS[4]], draft_read=made_draft(AttachmentEntry=None))
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual([], [w for w in sap.writes if w["kind"] == "patch"],
                         "patched a value the GRPO no longer holds")
        flags = " ".join(self._flags(20001))
        self.assertIn("no longer carries a bill", flags)
        self.assertNotIn("attachment pointer not set", flags,
                         "the read-back must not chase a scan value either")

    def test_an_attachment_added_since_the_scan_is_the_one_patched(self):
        scanned_without = dict(GRPOS[0], AttachmentEntry=None)
        self.scan([scanned_without, GRPOS[4]])
        self.approve(20001)
        sap = service_layer_sap([dict(GRPOS[0], AttachmentEntry=171555), GRPOS[4]],
                                draft_read=made_draft(AttachmentEntry=171555))
        code, sap = self.send(sap=sap, yes=True)
        patches = [w for w in sap.writes if w["kind"] == "patch"]
        self.assertEqual([{"AttachmentEntry": 171555}], [p["payload"] for p in patches])

    def _flags(self, docentry):
        results = sorted(self.out.glob("results-*.xlsx"))[-1]
        rows = xlsx.read_workbook(results)["Results"][1:]
        return [str(r[12]) for r in rows if r[2] == docentry]


# --------------------------------------------------------------------------
# M7 — Excel turning a reference into a number
# --------------------------------------------------------------------------

class ReferenceCellTest(SendCase):
    def test_a_reference_excel_stored_as_a_number_is_refused_not_guessed(self):
        # `2633100542.0` and `2.6331e+09` are both what str() makes of a cell
        # Excel re-typed. Neither is what is printed on the bill — and neither is
        # the scan's old value, which the reviewer may have deliberately changed.
        # Nobody guesses: the row waits for a retyped text cell.
        self.approve(20001, Y=2633100542)
        sap = service_layer_sap(self.GRPOS, draft_read=made_draft(AttachmentEntry=170999))
        code, sap = self.send(sap=sap, yes=True)
        self.assertEqual(1, code)
        self.assertEqual(batch_send.INVALID_INPUT, self.outcomes()[20001])
        self.assertIn("format the cell as Text", self.messages()[20001])
        self.assertEqual([], sap.writes)
        self.assertFalse((self.out / "payloads" / "20001.json").exists())

    def test_a_reference_typed_as_text_is_sent_exactly_as_typed(self):
        self.approve(20001, Y=" BILL/26-27/0042 ")
        sap = service_layer_sap(self.GRPOS, draft_read=made_draft(AttachmentEntry=170999))
        _code, _sap = self.send(sap=sap, yes=True)
        payload = json.loads((self.out / "payloads" / "20001.json").read_text())
        self.assertEqual("BILL/26-27/0042", payload["NumAtCard"])


# --------------------------------------------------------------------------
# M6 — exit 4 once drafts already exist
# --------------------------------------------------------------------------

class UnreachableAfterWritesTest(SendCase):
    def test_losing_sap_after_a_draft_was_made_never_claims_nothing_was_sent(self):
        # Row 1 made a draft; the bridge died while row 2 was being re-checked.
        # "Stopping before anything else is sent" is then a false statement about
        # a document that exists.
        rows = [GRPOS[0], grpo(20007, 2026080007, "2026-08-19"), GRPOS[4]]
        self.scan(rows)
        self.approve(20001)
        self.approve(20007)
        sap = service_layer_sap(rows, draft_read=made_draft(AttachmentEntry=170999))
        live = sap.tables["PurchaseDeliveryNotes"]

        def dies_on_the_second_row(flt, select, **kw):
            if "20007" in (flt or ""):
                raise SapUnreachable("connection refused", code=5)
            return live(flt, select, **kw)

        sap.tables["PurchaseDeliveryNotes"] = dies_on_the_second_row
        args = send_args(self.book, yes=True)
        args.quiet = False
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = batch_send.run_send(args, sap=sap, today=TODAY, now=NOW, repo=self.out)
        text = buf.getvalue() + err.getvalue()
        self.assertIn(code, (4, 7))
        self.assertIn("90001", text)
        self.assertNotIn("before anything else is sent", text)


# --------------------------------------------------------------------------
# the composition of the actual command line, against the stub binary
# --------------------------------------------------------------------------

class StubArgvTest(SendCase):
    """No FakeSap: a real SapCli, spawning the stub `sapb1`, argv recorded."""

    REPLIES = [
        {"when": "DocEntry eq 90001", "stdout": json.dumps([made_draft(AttachmentEntry=170999)])},
        {"when": "query PurchaseDeliveryNotes", "stdout": json.dumps([GRPOS[0]])},
        {"when": "query BusinessPartners", "stdout": json.dumps([VENDORS[0]])},
        {"when": "query Users", "stdout": json.dumps([{"InternalKey": 7, "UserCode": "USER36"}])},
        {"when": "draft purchase-invoice",
         "stdout": json.dumps({"DocEntry": 90001, "DocNum": 626089001})},
        {"when": "patch Drafts", "stdout": json.dumps({"DocEntry": 90001})},
    ]

    def setUp(self):
        super().setUp()
        from acc.tests.test_sap import make_repo
        make_repo(self.out)
        self.stub_log = self.out / "stub-calls.jsonl"
        replies = self.out / "replies.json"
        replies.write_text(json.dumps(self.REPLIES), encoding="utf-8")
        keep = dict(os.environ)
        os.environ.update({"STUB_LOG": str(self.stub_log), "STUB_REPLIES": str(replies),
                           "STUB_STDOUT": "[]"})
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(keep)))

    def real_sap(self):
        from acc.apbatch.sap import SapCli
        return SapCli(repo=self.out, company="JIVO_OIL_HANADB", allow_writes=True)

    def argvs(self):
        if not self.stub_log.exists():
            return []
        return [json.loads(l)["argv"] for l in
                self.stub_log.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_a_preview_never_puts_yes_on_the_command_line(self):
        self.approve(20001)
        code, _sap = self.send(sap=self.real_sap())
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        drafts = [a for a in self.argvs() if a[0] == "draft"]
        self.assertTrue(drafts, "the dry run never reached the binary")
        for argv in self.argvs():
            self.assertNotIn("--yes", argv, argv)
        for argv in drafts:
            self.assertIn("--dry-run", argv, argv)

    def test_an_env_pointing_at_another_company_is_said_out_loud(self):
        # Reachable in a real run, unlike a company_db mismatch: send names the
        # company itself, so the drafts land in the sidecar's books whatever the
        # env says — but an env pointing elsewhere usually means the wrong env
        # file, and the env file also decides whose login the drafts carry.
        os.environ["SAPB1_COMPANYDB"] = "JIVO_MART_HANADB"
        self.approve(20001)
        args = send_args(self.book)
        args.quiet = False
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = batch_send.run_send(args, sap=self.real_sap(), today=TODAY, now=NOW,
                                       repo=self.out)
        text = buf.getvalue()
        self.assertIn("JIVO_MART_HANADB", text)
        self.assertIn("JIVO_OIL_HANADB", text)
        self.assertEqual(batch_send.PREVIEWED, self.outcomes()[20001])
        for argv in self.argvs():
            self.assertEqual("JIVO_OIL_HANADB", argv[argv.index("--company") + 1])

    def test_sending_puts_yes_on_exactly_one_command_line_per_draft(self):
        self.approve(20001)
        code, _sap = self.send(sap=self.real_sap(), yes=True)
        self.assertEqual(batch_send.CREATED, self.outcomes()[20001])
        drafts = [a for a in self.argvs() if a[0] == "draft"]
        sent = [a for a in drafts if "--yes" in a]
        self.assertEqual(1, len(sent), f"one draft, one --yes: {drafts}")
        self.assertEqual(1, sent[0].count("--yes"))
        self.assertNotIn("--dry-run", sent[0])
        self.assertEqual(1, len([a for a in drafts if "--dry-run" in a]),
                         "the preview still runs before the send")


# --------------------------------------------------------------------------
# the fake must refuse what the real client refuses
# --------------------------------------------------------------------------

class FakeSapContractTest(unittest.TestCase):
    def test_a_write_without_yes_or_dry_run_is_refused(self):
        sap = FakeSap({}, allow_writes=True)
        with self.assertRaises(SapUsage):
            sap.draft("purchase-invoice", {"CardCode": "V1"})
        with self.assertRaises(SapUsage):
            sap.patch("Drafts(1)", {"AttachmentEntry": 1})
        self.assertEqual([], sap.writes)

    def test_a_dry_run_and_a_yes_are_both_allowed(self):
        sap = FakeSap({}, allow_writes=True)
        sap.draft("purchase-invoice", {"CardCode": "V1"}, dry_run=True)
        sap.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertEqual(2, len(sap.writes))


if __name__ == "__main__":
    unittest.main()
