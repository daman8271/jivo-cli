"""store.py — batch ids, the sidecar, the journal.

The sidecar is the part a reviewer cannot edit: everything that goes on the wire
except the four cells they can change. If it can be lost, corrupted or silently
mismatched with its workbook, the review is decoration.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from acc.apbatch import store

WHEN = dt.datetime(2026, 8, 24, 15, 30, 12)


class BatchIdTest(unittest.TestCase):
    def test_format(self):
        bid = store.new_batch_id("JIVO_OIL_HANADB", when=WHEN)
        self.assertRegex(bid, r"^B\d{6}-(OIL|MART|BEV)-[0-9A-F]{4}$")

    def test_the_date_and_company_are_readable_in_it(self):
        self.assertTrue(store.new_batch_id("JIVO_OIL_HANADB", when=WHEN).startswith("B260824-OIL-"))
        self.assertTrue(store.new_batch_id("JIVO_MART_HANADB", when=WHEN).startswith("B260824-MART-"))
        self.assertTrue(store.new_batch_id("JIVO_BEVERAGES_HANADB", when=WHEN).startswith("B260824-BEV-"))

    def test_two_batches_the_same_minute_do_not_collide(self):
        ids = {store.new_batch_id("JIVO_OIL_HANADB", when=WHEN) for _ in range(200)}
        self.assertGreater(len(ids), 190)

    def test_an_unknown_company_still_gets_a_tag(self):
        bid = store.new_batch_id("SOME_OTHER_DB", when=WHEN)
        self.assertRegex(bid, r"^B260824-[A-Z0-9]{2,6}-[0-9A-F]{4}$")

    def test_the_id_is_safe_in_a_filename_and_in_comments(self):
        bid = store.new_batch_id("JIVO_OIL_HANADB", when=WHEN)
        self.assertNotIn("/", bid)
        self.assertNotIn(" ", bid)
        self.assertLessEqual(len(bid), 20)      # it has to fit inside 254 chars of Comments

    def test_company_tag(self):
        self.assertEqual("OIL", store.company_tag("JIVO_OIL_HANADB"))
        self.assertEqual("BEV", store.company_tag("JIVO_BEVERAGES_HANADB"))


class SidecarTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.sc = store.Sidecar.new(batch_id="B260824-OIL-7F3A", company="JIVO_OIL_HANADB",
                                    login="USER36", host="127.0.0.1:15000",
                                    scanned_at=WHEN.isoformat(), scan_args={"limit": 50})
        self.sc.add_row(25714, row=1, status="READY", reasons=[],
                        locked={"B": 2026086625, "C": 25714, "D": "2026-08-14", "U": ""},
                        defaults={"V": "", "W": "no", "X": "2026-08-13", "Y": "2606000806", "Z": ""},
                        payload={"CardCode": "VENDA000939", "Series": 3684},
                        comments_base="Based On Goods Receipt PO 2026086625",
                        expect={"open_qty": 42900, "gross": 253110.0},
                        attachment_entry=170187,
                        tds={"choice": "no", "basis": "PRECEDENT-NO"},
                        series={"series": 3684, "source": "40 docs Aug-26 branch 2"})

    def test_round_trip(self):
        path = self.dir / "sidecar.json"
        self.sc.save(path)
        again = store.Sidecar.load(path)
        self.assertEqual("B260824-OIL-7F3A", again.batch_id)
        self.assertEqual("JIVO_OIL_HANADB", again.company)
        self.assertEqual("USER36", again.login)
        self.assertEqual({"CardCode": "VENDA000939", "Series": 3684}, again.row(25714)["payload"])

    def test_schema_version_is_recorded(self):
        path = self.dir / "sidecar.json"
        self.sc.save(path)
        self.assertEqual(1, json.loads(path.read_text(encoding="utf-8"))["schema"])

    def test_row_keys_are_strings_on_disk_but_addressable_by_int(self):
        path = self.dir / "sidecar.json"
        self.sc.save(path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(["25714"], list(raw["rows"]))
        again = store.Sidecar.load(path)
        self.assertEqual(again.row(25714), again.row("25714"))

    def test_a_new_row_starts_with_no_outcome(self):
        self.assertIsNone(self.sc.row(25714)["outcome"])

    def test_update_outcome_persists_immediately(self):
        path = self.dir / "sidecar.json"
        self.sc.save(path)
        self.sc.update_outcome(25714, {"state": "CREATED", "docentry": 54983})
        # Reloaded from disk, not from memory: a crash after the write must not
        # lose the fact that a draft exists.
        again = store.Sidecar.load(path)
        self.assertEqual("CREATED", again.row(25714)["outcome"]["state"])

    def test_update_outcome_on_an_unknown_row_raises(self):
        self.sc.save(self.dir / "sidecar.json")
        with self.assertRaises(KeyError):
            self.sc.update_outcome(99999, {"state": "CREATED"})

    def test_save_is_atomic(self):
        # A half-written sidecar is worse than none: send would read a truncated
        # payload and think the row was never scanned.
        path = self.dir / "sidecar.json"
        self.sc.save(path)
        first = path.read_text(encoding="utf-8")
        self.sc.add_row(25936, row=2, status="DUPLICATE", reasons=["already drafted"],
                        locked={}, defaults={}, payload=None, comments_base="", expect={},
                        attachment_entry=None, tds=None, series=None)
        self.sc.save(path)
        self.assertNotEqual(first, path.read_text(encoding="utf-8"))
        json.loads(path.read_text(encoding="utf-8"))          # still valid JSON
        self.assertEqual([], list(path.parent.glob("*.tmp")))  # no litter left behind

    def test_row_keys_helper(self):
        self.sc.add_row(25936, row=2, status="DUPLICATE", reasons=[], locked={}, defaults={},
                        payload=None, comments_base="", expect={}, attachment_entry=None,
                        tds=None, series=None)
        self.assertEqual({"25714", "25936"}, self.sc.row_keys())

    def test_counts_by_status(self):
        self.sc.add_row(25936, row=2, status="DUPLICATE", reasons=[], locked={}, defaults={},
                        payload=None, comments_base="", expect={}, attachment_entry=None,
                        tds=None, series=None)
        self.assertEqual({"READY": 1, "DUPLICATE": 1}, self.sc.counts())

    def test_age_in_days(self):
        self.assertEqual(0, self.sc.age_days(now=WHEN))
        self.assertEqual(4, self.sc.age_days(now=WHEN + dt.timedelta(days=4)))

    def test_a_sidecar_from_a_future_schema_is_refused(self):
        path = self.dir / "sidecar.json"
        self.sc.save(path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["schema"] = 99
        path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(store.SidecarError):
            store.Sidecar.load(path)


class FindSidecarTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_found_next_to_the_workbook(self):
        book = self.root / "out" / "review-B260824-OIL-7F3A.xlsx"
        book.parent.mkdir(parents=True)
        book.write_bytes(b"x")
        (book.parent / "sidecar.json").write_text("{}", encoding="utf-8")
        self.assertEqual(book.parent / "sidecar.json", store.find_sidecar_for(book))

    def test_found_in_the_batch_folder_when_the_workbook_was_moved(self):
        # An operator emails the workbook to themselves and opens it from
        # Downloads. The sidecar stayed behind in acc/_batches/<id>/.
        batches = self.root / "acc" / "_batches" / "B260824-OIL-7F3A"
        batches.mkdir(parents=True)
        (batches / "sidecar.json").write_text("{}", encoding="utf-8")
        book = self.root / "Downloads" / "review-B260824-OIL-7F3A.xlsx"
        book.parent.mkdir(parents=True)
        book.write_bytes(b"x")
        self.assertEqual(batches / "sidecar.json",
                         store.find_sidecar_for(book, batch_id="B260824-OIL-7F3A", repo=self.root))

    def test_not_found_is_none(self):
        book = self.root / "review.xlsx"
        book.write_bytes(b"x")
        self.assertIsNone(store.find_sidecar_for(book))

    def test_batch_dir(self):
        self.assertEqual(self.root / "acc" / "_batches" / "B260824-OIL-7F3A",
                         store.batch_dir(self.root, "B260824-OIL-7F3A"))

    def test_workbook_name(self):
        self.assertEqual("review-B260824-OIL-7F3A.xlsx",
                         store.workbook_name("B260824-OIL-7F3A"))

    def test_the_sidecar_and_journal_carry_the_batch_id(self):
        self.assertEqual("sidecar-B260824-OIL-7F3A.json",
                         store.sidecar_name("B260824-OIL-7F3A"))
        self.assertEqual("journal-B260824-OIL-7F3A.jsonl",
                         store.journal_name("B260824-OIL-7F3A"))

    def test_the_id_is_read_back_off_the_workbook_name(self):
        self.assertEqual("B260824-OIL-7F3A",
                         store.batch_id_from_workbook("/x/review-B260824-OIL-7F3A.xlsx"))
        self.assertEqual("B260824-BEV-01",
                         store.batch_id_from_workbook("review-B260824-BEV-01.xlsx"))
        self.assertIsNone(store.batch_id_from_workbook("august batch (2).xlsx"))

    def test_two_batches_in_one_folder_do_not_read_each_others_sidecar(self):
        # `--out ~/Desktop/batches` scanned twice — Oil then Beverages — used to
        # leave one sidecar.json (the second scan's) and two workbooks, so the
        # Oil workbook was sent from Beverages payloads.
        out = self.root / "out"
        out.mkdir(parents=True)
        for tag in ("B260824-OIL-7F3A", "B260824-BEV-9C21"):
            (out / store.workbook_name(tag)).write_bytes(b"x")
            (out / store.sidecar_name(tag)).write_text("{}", encoding="utf-8")
        for tag in ("B260824-OIL-7F3A", "B260824-BEV-9C21"):
            found = store.find_sidecar_for(out / store.workbook_name(tag))
            self.assertEqual(out / store.sidecar_name(tag), found)

    def test_the_id_stamped_sidecar_wins_over_a_legacy_bare_one(self):
        out = self.root / "out"
        out.mkdir(parents=True)
        book = out / store.workbook_name("B260824-OIL-7F3A")
        book.write_bytes(b"x")
        (out / "sidecar.json").write_text("{}", encoding="utf-8")
        (out / store.sidecar_name("B260824-OIL-7F3A")).write_text("{}", encoding="utf-8")
        self.assertEqual(out / store.sidecar_name("B260824-OIL-7F3A"),
                         store.find_sidecar_for(book))

    def test_a_bare_sidecar_is_still_found_when_it_is_the_only_one(self):
        out = self.root / "out"
        out.mkdir(parents=True)
        book = out / store.workbook_name("B260824-OIL-7F3A")
        book.write_bytes(b"x")
        (out / "sidecar.json").write_text("{}", encoding="utf-8")
        self.assertEqual(out / "sidecar.json", store.find_sidecar_for(book))

    def test_the_id_stamped_sidecar_is_found_in_the_batch_folder_too(self):
        batches = self.root / "acc" / "_batches" / "B260824-OIL-7F3A"
        batches.mkdir(parents=True)
        (batches / store.sidecar_name("B260824-OIL-7F3A")).write_text("{}", encoding="utf-8")
        book = self.root / "Downloads" / store.workbook_name("B260824-OIL-7F3A")
        book.parent.mkdir(parents=True)
        book.write_bytes(b"x")
        self.assertEqual(batches / store.sidecar_name("B260824-OIL-7F3A"),
                         store.find_sidecar_for(book, repo=self.root))


class JournalTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "journal.jsonl"
        self.addCleanup(self._tmp.cleanup)

    def test_append_and_read(self):
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "sending", "docentry": 25714})
        j.append({"event": "draft", "state": "created", "docentry": 25714, "draft": 54983})
        events = j.events()
        self.assertEqual(2, len(events))
        self.assertEqual("sending", events[0]["state"])
        self.assertEqual(54983, events[1]["draft"])

    def test_every_event_is_stamped(self):
        store.Journal(self.path).append({"event": "scan"})
        self.assertIn("time", store.Journal(self.path).events()[0])

    def test_a_line_left_unterminated_by_a_crash_does_not_swallow_the_next_one(self):
        """A process killed mid-write leaves a line with no newline on it.

        Appending straight onto that line glues two events into one string that
        is neither, and the event that says a draft was created is the one that
        gets lost — exactly when it is the only record of it.
        """
        self.path.write_text('{"event": "draft", "state": "sen', encoding="utf-8")
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "created", "docentry": 25714, "draft": 54983})
        text = self.path.read_text(encoding="utf-8")
        self.assertIn('\n{"time"', text)
        events = j.events()
        self.assertEqual(1, len(events), "the readable event was lost")
        self.assertEqual(54983, events[0]["draft"])

    def test_it_only_ever_appends(self):
        j = store.Journal(self.path)
        j.append({"event": "a"})
        first = self.path.read_text(encoding="utf-8")
        j.append({"event": "b"})
        self.assertTrue(self.path.read_text(encoding="utf-8").startswith(first))

    def test_reading_a_journal_that_does_not_exist_yet(self):
        self.assertEqual([], store.Journal(self.path).events())

    def test_a_corrupt_line_does_not_hide_the_rest(self):
        # This file is read after a crash, which is exactly when its last line
        # may be half-written. One bad line must not blind the operator to the
        # nine good ones above it.
        self.path.write_text('{"event":"a"}\nnot json\n{"event":"b"}\n', encoding="utf-8")
        self.assertEqual(["a", "b"], [e["event"] for e in store.Journal(self.path).events()])

    def test_unsent_rows_can_be_found_after_a_crash(self):
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "sending", "docentry": 25714})
        j.append({"event": "draft", "state": "created", "docentry": 25714})
        j.append({"event": "draft", "state": "sending", "docentry": 25936})   # crash here
        self.assertEqual([25936], j.in_flight())

    def test_a_row_that_came_back_unknown_stays_in_flight(self):
        # The exit-7 shape: the request went out, the answer did not come back.
        # It is the one row a person MUST look at, so "unknown" must not read as
        # settled just because a second journal line exists.
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "sending", "docentry": 25714})
        j.append({"event": "draft", "state": "unknown", "docentry": 25714})
        self.assertEqual([25714], j.in_flight())

    def test_a_rejected_row_is_settled_nothing_was_committed(self):
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "sending", "docentry": 25714})
        j.append({"event": "draft", "state": "rejected", "docentry": 25714})
        self.assertEqual([], j.in_flight())

    def test_resuming_an_unknown_row_settles_it(self):
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "sending", "docentry": 25714})
        j.append({"event": "draft", "state": "unknown", "docentry": 25714})
        j.append({"event": "resume", "state": "recovered", "docentry": 25714,
                  "draft_entry": 90055})
        self.assertEqual([], j.in_flight())

    def test_a_resume_that_found_nothing_also_settles_the_row(self):
        # Not because it is fine, but because a person has now looked. The row's
        # outcome carries the UNKNOWN-UNRESOLVED verdict.
        j = store.Journal(self.path)
        j.append({"event": "draft", "state": "sending", "docentry": 25714})
        j.append({"event": "draft", "state": "unknown", "docentry": 25714})
        j.append({"event": "resume", "state": "unresolved", "docentry": 25714})
        self.assertEqual([], j.in_flight())


if __name__ == "__main__":
    unittest.main()
