"""SapCli — the subprocess wrapper over the sapb1 binary.

Everything here runs against `fixtures/sapb1_stub.py` copied in as `sapb1`, so
no test touches SAP, the network, or a login.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from acc.apbatch import sap as sapmod
from acc.apbatch.sap import (
    SapAuth,
    SapCli,
    SapConfig,
    SapRejected,
    SapUnknownOutcome,
    SapUnreachable,
    SapUsage,
    SapWriteRefused,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def make_repo(tmp: Path, *, windows: bool = False) -> Path:
    """A throwaway repo whose sapb1 is the stub."""
    cli_dir = tmp / ("sap-b1/accounts-kit" if windows else "sap-b1/cli")
    cli_dir.mkdir(parents=True)
    target = cli_dir / ("sapb1.exe" if windows else "sapb1")
    shutil.copy(FIXTURES / "sapb1_stub.py", target)
    target.chmod(target.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return tmp


class StubCase(unittest.TestCase):
    """A repo whose sapb1 is the stub, and a clean set of STUB_* variables."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.repo = make_repo(self.tmp)
        self.log = self.tmp / "calls.jsonl"
        for k in ("STUB_LOG", "STUB_EXIT", "STUB_EXIT_SEQ", "STUB_STDOUT", "STUB_STDERR",
                  "STUB_SIGNAL", "STUB_SLEEP"):
            os.environ.pop(k, None)
        os.environ["STUB_LOG"] = str(self.log)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(lambda: [os.environ.pop(k, None) for k in
                                 ("STUB_LOG", "STUB_EXIT", "STUB_EXIT_SEQ", "STUB_STDOUT",
                                  "STUB_STDERR", "STUB_SIGNAL", "STUB_SLEEP")])

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines() if l.strip()]


class SapCliTest(StubCase):
    # ---- happy path ----------------------------------------------------

    def test_query_returns_rows_and_passes_the_flags(self):
        os.environ["STUB_STDOUT"] = json.dumps([{"DocEntry": 1}, {"DocEntry": 2}])
        cli = SapCli(repo=self.repo, company="JIVO_OIL_HANADB")
        rows = cli.query("PurchaseDeliveryNotes", filter="DocEntry eq 1",
                         select="DocEntry,DocNum", orderby="DocEntry asc", top=5)
        self.assertEqual([{"DocEntry": 1}, {"DocEntry": 2}], rows)
        argv = self.calls()[0]["argv"]
        self.assertEqual(["query", "PurchaseDeliveryNotes", "--json"], argv[:3])
        self.assertIn("--filter", argv)
        self.assertEqual("DocEntry eq 1", argv[argv.index("--filter") + 1])
        self.assertEqual("DocEntry,DocNum", argv[argv.index("--select") + 1])
        self.assertEqual("DocEntry asc", argv[argv.index("--orderby") + 1])
        self.assertEqual("5", argv[argv.index("--top") + 1])
        self.assertEqual("JIVO_OIL_HANADB", argv[argv.index("--company") + 1])

    def test_query_all_paginates_via_the_cli(self):
        cli = SapCli(repo=self.repo)
        cli.query_all("Drafts", filter="x eq 1", page_size=50)
        argv = self.calls()[0]["argv"]
        self.assertIn("--all", argv)
        self.assertEqual("50", argv[argv.index("--page-size") + 1])
        self.assertNotIn("--top", argv)

    def test_empty_stdout_is_an_empty_row_list(self):
        os.environ["STUB_STDOUT"] = ""
        self.assertEqual([], SapCli(repo=self.repo).query("Items"))

    def test_runs_from_the_cli_directory(self):
        # sapb1 reads .env from its working directory; the wrapper must not
        # inherit whatever directory the operator happened to run acc from.
        SapCli(repo=self.repo).query("Items")
        self.assertEqual(str((self.repo / "sap-b1" / "cli").resolve()),
                         str(Path(self.calls()[0]["cwd"]).resolve()))

    def test_env_file_fills_gaps_but_exported_values_win(self):
        envfile = self.repo / "sap-b1" / "cli" / "op.env"
        envfile.write_text("SAPB1_USER=USER36\nSAPB1_HOST=138.252.101.222\n# comment\n", encoding="utf-8")
        os.environ["SAPB1_HOST"] = "127.0.0.1"
        self.addCleanup(lambda: os.environ.pop("SAPB1_HOST", None))
        SapCli(repo=self.repo, env_file="op.env").query("Items")
        env = self.calls()[0]["env"]
        self.assertEqual("USER36", env["SAPB1_USER"])          # from the file
        self.assertEqual("127.0.0.1", env["SAPB1_HOST"])       # the bridge wins

    def test_env_file_does_not_leak_into_this_process(self):
        envfile = self.repo / "sap-b1" / "cli" / "op.env"
        envfile.write_text("SAPB1_PASSWORD=hunter2\n", encoding="utf-8")
        SapCli(repo=self.repo, env_file="op.env").query("Items")
        self.assertIsNone(os.environ.get("SAPB1_PASSWORD"))

    # ---- exit code map -------------------------------------------------

    def test_exit_codes_map_to_exceptions(self):
        for code, exc in ((2, SapUsage), (3, SapConfig), (4, SapAuth),
                          (5, SapUnreachable), (6, SapRejected), (7, SapUnknownOutcome)):
            with self.subTest(code=code):
                os.environ["STUB_EXIT"] = str(code)
                os.environ["STUB_STDERR"] = "boom on %d\n" % code
                cli = SapCli(repo=self.repo, retries=0)
                with self.assertRaises(exc) as caught:
                    cli.query("Items")
                self.assertEqual(code, caught.exception.code)
                self.assertIn("boom on %d" % code, str(caught.exception))

    def test_unknown_exit_code_is_still_a_sap_error(self):
        os.environ["STUB_EXIT"] = "42"
        with self.assertRaises(sapmod.SapError):
            SapCli(repo=self.repo, retries=0).query("Items")

    # ---- retries -------------------------------------------------------

    def test_unreachable_is_retried_then_gives_up(self):
        os.environ["STUB_EXIT_SEQ"] = "5"
        slept = []
        cli = SapCli(repo=self.repo, retries=3, sleep=slept.append)
        with self.assertRaises(SapUnreachable):
            cli.query("Items")
        self.assertEqual(4, len(self.calls()))          # 1 attempt + 3 retries
        self.assertEqual([2, 4, 8], slept)

    def test_unreachable_that_recovers_returns_rows(self):
        os.environ["STUB_EXIT_SEQ"] = "5,5,0"
        os.environ["STUB_STDOUT"] = json.dumps([{"DocEntry": 9}])
        cli = SapCli(repo=self.repo, retries=3, sleep=lambda _s: None)
        self.assertEqual([{"DocEntry": 9}], cli.query("Items"))
        self.assertEqual(3, len(self.calls()))

    def test_a_data_error_is_not_retried(self):
        os.environ["STUB_EXIT"] = "6"
        cli = SapCli(repo=self.repo, retries=3, sleep=lambda _s: None)
        with self.assertRaises(SapRejected):
            cli.query("Items")
        self.assertEqual(1, len(self.calls()))

    # ---- read-only instances cannot write ------------------------------

    def test_read_only_instance_refuses_to_draft(self):
        cli = SapCli(repo=self.repo, allow_writes=False)
        with self.assertRaises(SapWriteRefused):
            cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertEqual([], self.calls())              # nothing was even spawned

    def test_read_only_instance_refuses_to_patch(self):
        cli = SapCli(repo=self.repo, allow_writes=False)
        with self.assertRaises(SapWriteRefused):
            cli.patch("Drafts(1)", {"AttachmentEntry": 5}, yes=True)
        self.assertEqual([], self.calls())

    def test_read_only_instance_refuses_even_a_dry_run(self):
        # A dry run sends nothing, but a scan has no business building write
        # commands at all — the refusal is the point of the flag.
        cli = SapCli(repo=self.repo, allow_writes=False)
        with self.assertRaises(SapWriteRefused):
            cli.draft("purchase-invoice", {"CardCode": "V1"}, dry_run=True)

    # ---- the write shape (used by send in a later phase) ----------------

    def test_draft_dry_run_never_passes_yes(self):
        os.environ["STUB_STDOUT"] = json.dumps({"dryRun": True})
        cli = SapCli(repo=self.repo, allow_writes=True)
        cli.draft("purchase-invoice", {"CardCode": "V1"}, dry_run=True)
        argv = self.calls()[0]["argv"]
        self.assertEqual(["draft", "purchase-invoice"], argv[:2])
        self.assertIn("--dry-run", argv)
        self.assertNotIn("--yes", argv)
        self.assertIn("--json", argv)

    def test_draft_send_passes_yes_and_a_data_file(self):
        os.environ["STUB_STDOUT"] = json.dumps({"DocEntry": 54983, "DocNum": 626080001})
        cli = SapCli(repo=self.repo, allow_writes=True)
        created = cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertEqual(54983, created["DocEntry"])
        argv = self.calls()[0]["argv"]
        self.assertIn("--yes", argv)
        self.assertNotIn("--dry-run", argv)
        self.assertIn("--data-file", argv)

    def test_draft_without_yes_or_dry_run_is_refused_locally(self):
        cli = SapCli(repo=self.repo, allow_writes=True)
        with self.assertRaises(SapUsage):
            cli.draft("purchase-invoice", {"CardCode": "V1"})
        self.assertEqual([], self.calls())

    def test_draft_uses_a_caller_supplied_payload_file_verbatim(self):
        payload = self.tmp / "row.json"
        payload.write_text('{"CardCode":"V1"}', encoding="utf-8")
        os.environ["STUB_STDOUT"] = json.dumps({"DocEntry": 1})
        cli = SapCli(repo=self.repo, allow_writes=True)
        cli.draft("purchase-invoice", data_file=payload, yes=True)
        argv = self.calls()[0]["argv"]
        self.assertEqual(str(payload), argv[argv.index("--data-file") + 1])

    def test_unknown_outcome_from_a_write_raises_the_go_look_error(self):
        os.environ["STUB_EXIT"] = "7"
        os.environ["STUB_STDERR"] = "write outcome unknown\n"
        cli = SapCli(repo=self.repo, allow_writes=True, retries=3, sleep=lambda _s: None)
        with self.assertRaises(SapUnknownOutcome):
            cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertEqual(1, len(self.calls()))          # a write is NEVER retried

    # ---- what an UNRECOGNIZED exit code means on a write ----------------
    #
    # 2/3/5/6 are promises that nothing was sent. Every other non-zero code is
    # not a promise this build holds, and guessing "nothing happened" is the one
    # guess that creates a second A/P invoice.

    def test_a_signal_death_mid_write_is_an_unknown_outcome(self):
        os.environ["STUB_SIGNAL"] = "15"                # returncode -15
        cli = SapCli(repo=self.repo, allow_writes=True)
        with self.assertRaises(SapUnknownOutcome) as caught:
            cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertEqual(-15, caught.exception.code)
        self.assertIn("go look", str(caught.exception))

    def test_a_bare_exit_1_from_a_write_is_an_unknown_outcome(self):
        os.environ["STUB_EXIT"] = "1"
        os.environ["STUB_STDERR"] = "panic: something the CLI did not classify\n"
        cli = SapCli(repo=self.repo, allow_writes=True)
        with self.assertRaises(SapUnknownOutcome) as caught:
            cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertEqual(1, caught.exception.code)

    def test_exit_8_from_a_write_is_an_unknown_outcome_too(self):
        # 8 = SAP answered, the read-back disagreed. The document may well exist.
        os.environ["STUB_EXIT"] = "8"
        cli = SapCli(repo=self.repo, allow_writes=True)
        with self.assertRaises(SapUnknownOutcome):
            cli.patch("Drafts(54983)", {"AttachmentEntry": 1}, yes=True)

    def test_the_nothing_was_sent_codes_keep_their_own_exceptions(self):
        for code, exc in ((2, SapUsage), (3, SapConfig), (5, SapUnreachable), (6, SapRejected)):
            with self.subTest(code=code):
                os.environ["STUB_EXIT"] = str(code)
                # built inside the loop: SapCli snapshots the environment
                cli = SapCli(repo=self.repo, allow_writes=True, retries=0)
                with self.assertRaises(exc):
                    cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)

    def test_a_dry_run_keeps_the_plain_exit_code_mapping(self):
        # A dry run never sends anything, so an odd exit code there is just an
        # error — turning it into "may have committed" would halt a batch for
        # nothing.
        os.environ["STUB_EXIT"] = "2"
        cli = SapCli(repo=self.repo, allow_writes=True)
        with self.assertRaises(SapUsage):
            cli.draft("purchase-invoice", {"CardCode": "V1"}, dry_run=True)

    # ---- a process that never comes back --------------------------------

    def test_a_write_that_never_returns_is_an_unknown_outcome(self):
        os.environ["STUB_SLEEP"] = "5"
        os.environ["SAPB1_SUBPROC_TIMEOUT"] = "1"
        self.addCleanup(lambda: os.environ.pop("SAPB1_SUBPROC_TIMEOUT", None))
        cli = SapCli(repo=self.repo, allow_writes=True)
        with self.assertRaises(SapUnknownOutcome) as caught:
            cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertIn("did not return", str(caught.exception))
        self.assertIn("Document Drafts", str(caught.exception))

    def test_a_read_that_never_returns_is_unreachable_and_is_retried(self):
        os.environ["STUB_SLEEP"] = "3"
        os.environ["SAPB1_SUBPROC_TIMEOUT"] = "1"
        self.addCleanup(lambda: os.environ.pop("SAPB1_SUBPROC_TIMEOUT", None))
        cli = SapCli(repo=self.repo, retries=1, sleep=lambda _s: None)
        with self.assertRaises(SapUnreachable):
            cli.query("Items")
        self.assertEqual(2, len(self.calls()))           # tried, waited, tried again

    # ---- filters that would quietly lie ---------------------------------

    def test_all_and_top_together_is_refused_before_anything_is_spawned(self):
        # --all sweeps every page and ignores --top, so a caller asking for both
        # gets more rows than it bounded and never finds out.
        cli = SapCli(repo=self.repo)
        with self.assertRaises(SapUsage):
            cli.query("BusinessPartners", all=True, top=20)
        self.assertEqual([], self.calls())

    # ---- --env that is not there ----------------------------------------

    def test_an_env_file_that_does_not_exist_names_the_path_it_tried(self):
        # Carrying on with the default login would put the drafts under somebody
        # else's name, which is the one thing --env exists to decide.
        with self.assertRaises(SapConfig) as caught:
            SapCli(repo=self.repo, env_file="typo-user36.env")
        message = str(caught.exception)
        self.assertIn("typo-user36.env", message)
        self.assertIn(str(self.repo / "sap-b1" / "cli"), message)

    def test_an_env_file_that_exists_is_remembered_for_the_banner(self):
        env = self.repo / "sap-b1" / "cli" / "navdeep-user36.env"
        env.write_text("SAPB1_USER=USER36\n", encoding="utf-8")
        cli = SapCli(repo=self.repo, env_file="navdeep-user36.env")
        self.assertEqual(env.resolve(), cli.env_path.resolve())
        self.assertEqual("USER36", cli.user)

    def test_no_env_file_asked_for_is_not_an_error(self):
        self.assertIsNone(SapCli(repo=self.repo).env_path)

    # ---- binary resolution ---------------------------------------------

    def test_windows_uses_the_accounts_kit_exe(self):
        win = make_repo(self.tmp / "win", windows=True)
        self.assertEqual(win / "sap-b1" / "accounts-kit" / "sapb1.exe",
                         sapmod.resolve_cli(win, windows=True))

    def test_posix_uses_the_go_binary(self):
        self.assertEqual(self.repo / "sap-b1" / "cli" / "sapb1",
                         sapmod.resolve_cli(self.repo, windows=False))

    def test_missing_binary_is_a_config_error(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        with self.assertRaises(SapConfig):
            SapCli(repo=empty)

    def test_find_repo_walks_up_from_this_file(self):
        self.assertTrue((sapmod.find_repo() / "sap-b1" / "cli").exists())


class OutputThatIsNotJsonTest(StubCase):
    """sapb1 exiting 0 and printing something else. It has happened: a warning
    on stdout, a Go panic, an HTML error page from a proxy in front of SAP."""

    def test_a_read_says_what_it_actually_printed(self):
        os.environ["STUB_STDOUT"] = "<html>504 Gateway Time-out</html>"
        cli = SapCli(repo=self.repo, company="JIVO_OIL_HANADB")
        with self.assertRaises(sapmod.SapError) as caught:
            cli.query("Drafts")
        self.assertNotIsInstance(caught.exception, SapUnknownOutcome)
        self.assertIn("504 Gateway Time-out", str(caught.exception))

    def test_a_read_quotes_at_most_the_first_200_characters(self):
        os.environ["STUB_STDOUT"] = "x" * 5000
        cli = SapCli(repo=self.repo, company="JIVO_OIL_HANADB")
        with self.assertRaises(sapmod.SapError) as caught:
            cli.query("Drafts")
        self.assertLess(len(str(caught.exception)), 400)

    def test_a_real_write_that_prints_junk_is_an_UNKNOWN_outcome(self):
        # The write went out. Whatever came back is unreadable, so "nothing
        # happened" is a guess, and it is the guess that duplicates an invoice.
        os.environ["STUB_STDOUT"] = "panic: runtime error: invalid memory address"
        cli = SapCli(repo=self.repo, company="JIVO_OIL_HANADB", allow_writes=True)
        with self.assertRaises(SapUnknownOutcome) as caught:
            cli.draft("purchase-invoice", {"CardCode": "V1"}, yes=True)
        self.assertIn("panic", str(caught.exception))
        self.assertIn("--resume", str(caught.exception))

    def test_a_dry_run_that_prints_junk_is_NOT_an_unknown_outcome(self):
        os.environ["STUB_STDOUT"] = "not json at all"
        cli = SapCli(repo=self.repo, company="JIVO_OIL_HANADB", allow_writes=True)
        with self.assertRaises(sapmod.SapError) as caught:
            cli.draft("purchase-invoice", {"CardCode": "V1"}, dry_run=True)
        self.assertNotIsInstance(caught.exception, SapUnknownOutcome)


class ExportedUserTest(StubCase):
    def env_file(self, user: str) -> Path:
        path = self.repo / "sap-b1" / "cli" / "someone.env"
        path.write_text(f"SAPB1_USER={user}\nSAPB1_PASSWORD=x\n", encoding="utf-8")
        return path

    def test_an_exported_user_that_contradicts_the_env_file_is_refused(self):
        path = self.env_file("USER36")
        os.environ["SAPB1_USER"] = "USER01"
        self.addCleanup(lambda: os.environ.pop("SAPB1_USER", None))
        with self.assertRaises(SapConfig) as caught:
            SapCli(repo=self.repo, env_file=path, allow_writes=True)
        self.assertIn("USER01", str(caught.exception))
        self.assertIn("USER36", str(caught.exception))

    def test_the_same_user_in_both_places_is_fine(self):
        path = self.env_file("USER36")
        os.environ["SAPB1_USER"] = "USER36"
        self.addCleanup(lambda: os.environ.pop("SAPB1_USER", None))
        self.assertEqual("USER36", SapCli(repo=self.repo, env_file=path).user)



if __name__ == "__main__":
    unittest.main()
