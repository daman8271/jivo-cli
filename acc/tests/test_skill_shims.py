"""Characterization: the ap-rm-pm skill must print the same thing after the refactor.

These goldens were recorded against the ORIGINAL monolithic
`.claude/skills/ap-rm-pm/bin/{precheck,readback}.py`, before a line of them
moved into acc/apbatch. Every operator's Claude follows that narrative — the
`[1]…[6]` sections, the verdict, the exit codes — so the refactor is only safe
if the bytes are identical.

Nothing here touches SAP: the scripts' module-level `q()` (and precheck's
optional `hana()`) are replaced with a scripted fixture. The refactored scripts
must keep a module-level `q` for exactly this reason.

Re-record deliberately, never casually:
    RECORD_SKILL_GOLDEN=1 python3 -m unittest acc.tests.test_skill_shims
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

SKILL_BIN = REPO / ".claude" / "skills" / "ap-rm-pm" / "bin"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "skill_golden"
SCENARIOS = json.loads((FIXTURES / "skill_scenarios.json").read_text(encoding="utf-8"))
RECORDING = os.environ.get("RECORD_SKILL_GOLDEN") == "1"


def load_script(name: str):
    """Import a skill script by path, fresh, without installing it in sys.modules."""
    spec = importlib.util.spec_from_file_location("skill_" + name, SKILL_BIN / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ScriptedSap:
    """Answers the scripts' queries from a fixture, and records what was asked.

    The dispatch keys are the stable parts of each call — the entity plus the
    one thing that distinguishes two questions about the same entity (a $select
    of DocEntry,Series is the series lookup; a NumAtCard filter is the duplicate
    check). Filters themselves are deliberately NOT matched: the refactor changes
    them (the series query gains its missing upper month bound), and that change
    must not be able to alter what the script prints.
    """

    def __init__(self, table: dict, company_default: str = "JIVO_OIL_HANADB"):
        self.table = table
        self.calls: list[tuple] = []
        self.company_default = company_default

    def key(self, entity, flt, select):
        flt = flt or ""
        select = select or ""
        if entity == "PurchaseInvoices":
            if select == "DocEntry,Series":
                return "series_invoices"
            return "posted_by_ref" if "NumAtCard eq" in flt else "vendor_last3"
        if entity == "Drafts":
            if select == "DocEntry,Series":
                return "series_drafts"
            if "NumAtCard eq" in flt:
                return "drafts_by_ref"
            if "DocEntry eq" in flt:
                return "drafts_by_docentry"
            return "drafts_by_vendor"
        if entity == "PurchaseDeliveryNotes":
            if "DocNum eq" in flt:
                return "grpo_by_docnum"
            if "DocEntry eq" in flt:
                return "grpo_by_docentry"
            return "grpo_by_ref" if "NumAtCard eq" in flt else "grpo_by_vendor"
        return {"BusinessPartners": "vendors", "BusinessPlaces": "branches",
                "PurchaseOrders": "pos", "WithholdingTaxCodes": "wt",
                "Users": "users", "BusinessPartnerGroups": "groups"}.get(entity, entity)

    def q(self, entity, flt=None, select=None, orderby=None, top=None, company=None):
        key = self.key(entity, flt, select)
        self.calls.append((entity, key, company))
        if company and company != self.company_default:
            return []                              # the "is it in another book" sweep
        rows = copy.deepcopy(self.table.get(key, []))
        return rows[:top] if top else rows

    def hana(self, sql):
        return copy.deepcopy(self.table.get("nnm1"))


def scrub(text: str) -> str:
    """Remove anything that depends on where the repo happens to sit."""
    return text.replace(str(REPO), "<REPO>")


def run_script(mod, argv, table, env=None):
    """Run a skill script's main() under the scripted SAP; return (stdout, exit code)."""
    sap = ScriptedSap(table)
    mod.q = sap.q
    if hasattr(mod, "hana"):
        mod.hana = sap.hana
    out = io.StringIO()
    saved_argv, saved_env = sys.argv, dict(os.environ)
    sys.argv = argv
    os.environ.update({"SAPB1_USER": "USER36", "SAPB1_HOST": "127.0.0.1",
                       "SAPB1_COMPANYDB": "JIVO_OIL_HANADB", **(env or {})})
    try:
        with contextlib.redirect_stdout(out):
            try:
                mod.main()
                code = 0
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
    finally:
        sys.argv = saved_argv
        os.environ.clear()
        os.environ.update(saved_env)
    return scrub(out.getvalue()), code, sap


class SkillCharacterizationTest(unittest.TestCase):
    maxDiff = None

    def check(self, name: str, text: str):
        path = GOLDEN / (name + ".out")
        if RECORDING:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            self.skipTest("recorded " + str(path))
        self.assertTrue(path.exists(), f"missing golden {path} — record it first")
        self.assertEqual(path.read_text(encoding="utf-8"), text,
                         f"{name}: the skill's output changed")

    # -- precheck --------------------------------------------------------

    def precheck(self, scenario, extra_argv=()):
        mod = load_script("precheck")
        with tempfile.TemporaryDirectory() as tmp:
            argv = ["precheck.py", "--ref", "SPI/26-27/0042", "--vendor", "SUNRISE",
                    "--gstin", "06AAACJ0000A1Z5", "--inv-date", "2026-08-17",
                    "--grpo", "2026080001", "--po", "220826099", "--qty", "10000",
                    "--total", "53100", "--item", "PET BOTTLE 500 ML 18 GM",
                    "--note", "GE-2026-9999 | Veh HR00X0000",
                    "--out", str(Path(tmp) / "payload.json")] + list(extra_argv)
            text, code, sap = run_script(mod, argv, SCENARIOS[scenario])
            text = text.replace(str(Path(tmp) / "payload.json"), "<OUT>/payload.json")
            payload = Path(tmp) / "payload.json"
            written = json.loads(payload.read_text(encoding="utf-8")) if payload.exists() else None
        return text, code, sap, written

    def test_precheck_ready(self):
        text, code, _sap, payload = self.precheck("ready")
        self.check("precheck_ready", text)
        self.assertEqual(0, code)
        self.assertIsNotNone(payload)

    def test_precheck_ready_payload(self):
        _text, _code, _sap, payload = self.precheck("ready")
        self.check("precheck_ready_payload", json.dumps(payload, indent=2) + "\n")

    def test_precheck_common_on_the_paper_sets_factory_common(self):
        """C-0027: a handwritten 'Common' decides the Budget dim, not the GRPO's value."""
        text, code, _sap, payload = self.precheck(
            "ready", extra_argv=("--note", "GE-2026-9999 | For oil plant | Common"))
        self.assertEqual(0, code)
        self.assertIn("FACT_COM", text)
        self.assertIn("the paper says 'Common'", text)
        self.assertTrue(payload["DocumentLines"])
        for row in payload["DocumentLines"]:
            self.assertEqual("FACT_COM", row["CostingCode3"])

    def test_precheck_budget_flag_beats_the_note(self):
        text, code, _sap, payload = self.precheck(
            "ready", extra_argv=("--note", "For oil plant | Common", "--budget", "Factory"))
        self.assertEqual(0, code)
        self.assertIn("--budget", text)
        for row in payload["DocumentLines"]:
            self.assertEqual("Factory", row["CostingCode3"])

    def test_precheck_no_allocation_word_leaves_budget_to_the_grpo(self):
        _text, code, _sap, payload = self.precheck("ready")
        self.assertEqual(0, code)
        for row in payload["DocumentLines"]:
            self.assertNotIn("CostingCode3", row)

    def test_precheck_already_in_sap_exits_2(self):
        text, code, _sap, payload = self.precheck("already")
        self.check("precheck_already", text)
        self.assertEqual(2, code)
        self.assertIsNone(payload)

    def test_precheck_ambiguous_vendor_exits_3(self):
        text, code, _sap, payload = self.precheck("ambiguous_vendor")
        self.check("precheck_ambiguous_vendor", text)
        self.assertEqual(3, code)
        self.assertIsNone(payload)

    def test_precheck_still_exposes_a_module_level_q(self):
        # The shim keeps q() as its single door to SAP; without it this whole
        # file stops testing anything.
        mod = load_script("precheck")
        self.assertTrue(callable(getattr(mod, "q", None)))

    def test_precheck_series_query_is_month_bounded(self):
        # The one deliberate behaviour change of the refactor, asserted rather
        # than assumed: an upper bound so a July GRPO cannot take August's series.
        mod = load_script("precheck")
        seen = []
        sap = ScriptedSap(SCENARIOS["ready"])

        def spy(entity, flt=None, select=None, orderby=None, top=None, company=None):
            seen.append((entity, flt, select))
            return sap.q(entity, flt, select, orderby, top, company)

        with tempfile.TemporaryDirectory() as tmp:
            argv = ["precheck.py", "--ref", "SPI/26-27/0042", "--vendor", "SUNRISE",
                    "--gstin", "06AAACJ0000A1Z5", "--inv-date", "2026-08-17",
                    "--grpo", "2026080001", "--out", str(Path(tmp) / "p.json")]
            mod.q = spy
            mod.hana = sap.hana
            saved = sys.argv
            sys.argv = argv
            os.environ.update({"SAPB1_USER": "USER36", "SAPB1_HOST": "127.0.0.1",
                               "SAPB1_COMPANYDB": "JIVO_OIL_HANADB"})
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.suppress(SystemExit):
                        mod.main()
            finally:
                sys.argv = saved
        series_filters = [f for (e, f, s) in seen if s == "DocEntry,Series"]
        self.assertTrue(series_filters, "no series lookup happened")
        for flt in series_filters:
            self.assertIn("ge '2026-08-01'", flt)
            self.assertIn("lt '2026-09-01'", flt)

    # -- readback --------------------------------------------------------

    def readback(self, scenario, argv_extra=()):
        mod = load_script("readback")
        argv = ["readback.py", "60011", "--expect-total", "53100",
                "--expect-qty", "10000"] + list(argv_extra)
        return run_script(mod, argv, SCENARIOS[scenario])

    def test_readback_clean_exits_0(self):
        text, code, _sap = self.readback("rb_clean")
        self.check("readback_clean", text)
        self.assertEqual(0, code)

    def test_readback_flags_exit_1(self):
        text, code, _sap = self.readback("rb_flags")
        self.check("readback_flags", text)
        self.assertEqual(1, code)

    def test_readback_still_exposes_a_module_level_q(self):
        mod = load_script("readback")
        self.assertTrue(callable(getattr(mod, "q", None)))


class ShimWiringTest(unittest.TestCase):
    """The shims must reach acc/apbatch from the skill folder, on any box."""

    def test_precheck_imports_the_shared_rules(self):
        mod = load_script("precheck")
        self.assertIs(mod.inr, __import__("acc.apbatch.rules", fromlist=["inr"]).inr)

    def test_readback_imports_the_shared_rules(self):
        mod = load_script("readback")
        self.assertIs(mod.inr, __import__("acc.apbatch.rules", fromlist=["inr"]).inr)

    def test_neither_shim_hardcodes_the_posix_binary(self):
        """Measured on HO-IPEXP-PC2 (Lovepreet, 2026-08-24): both shims set
        CLI = repo/"sap-b1"/"cli"/"sapb1" and then resolved --env against
        CLI.parent. On a Windows box the kit is accounts-kit, so
        `--env lovepreet-user06.env` exited 3 "no such file" and the printed
        login came back "?" - the operator's own login silently unreachable
        through the skill. Both must go through resolve_cli().
        """
        for name in ("precheck", "readback"):
            src = (SKILL_BIN / (name + ".py")).read_text(encoding="utf-8")
            self.assertNotIn('CLI = repo / "sap-b1" / "cli" / "sapb1"', src,
                             f"{name}.py pins the POSIX binary; Windows kits use accounts-kit")
            self.assertIn("CLI = resolve_cli(repo)", src,
                          f"{name}.py must resolve the binary per platform")

    def test_resolve_cli_picks_the_windows_kit_on_windows(self):
        from acc.apbatch.sap import resolve_cli
        self.assertEqual(resolve_cli(REPO, windows=True),
                         REPO / "sap-b1" / "accounts-kit" / "sapb1.exe")

    def test_both_shims_find_the_repo_from_a_windows_only_kit(self):
        """A checkout carrying only accounts-kit/sapb1.exe is still a checkout."""
        for name in ("precheck", "readback"):
            src = (SKILL_BIN / (name + ".py")).read_text(encoding="utf-8")
            self.assertIn('"accounts-kit" / "sapb1.exe").exists()', src,
                          f"{name}.py's find_repo() rejects a Windows-only kit")


class StaleCheckoutTest(unittest.TestCase):
    """A checkout without acc/apbatch must say so in words an operator can act on.

    This is the shape of a real support call: someone runs the skill out of a
    month-old Drive zip, the import dies with `ModuleNotFoundError: No module
    named 'acc'`, and it reads like a broken Python rather than a folder that
    needs a pull.

    The scripts are run in a subprocess with a sys.path that cannot reach the
    repo — the honest reproduction of a stale copy, and it cannot disturb this
    process's imports.
    """

    HARNESS = (
        "import runpy, sys\n"
        "sys.path[:] = [p for p in sys.path if p not in (REPO, '', '.')]\n"
        "class Blocker:\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name == 'acc' or name.startswith('acc.'):\n"
        "            raise ModuleNotFoundError('No module named %r' % name)\n"
        "        return None\n"
        "sys.meta_path.insert(0, Blocker())\n"
        "runpy.run_path(SCRIPT, run_name='__main__')\n"
    )

    def run_stale(self, name: str):
        import subprocess
        code = (self.HARNESS.replace("REPO", repr(str(REPO)))
                            .replace("SCRIPT", repr(str(SKILL_BIN / (name + ".py")))))
        return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              cwd=str(SKILL_BIN))

    def test_precheck_on_a_stale_checkout_exits_3_with_the_pull_instruction(self):
        r = self.run_stale("precheck")
        self.assertEqual(3, r.returncode, r.stderr)
        self.assertIn("missing acc/apbatch", r.stderr)
        self.assertIn("git pull", r.stderr)
        self.assertIn("stale copy", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_readback_on_a_stale_checkout_exits_3_with_the_pull_instruction(self):
        r = self.run_stale("readback")
        self.assertEqual(3, r.returncode, r.stderr)
        self.assertIn("missing acc/apbatch", r.stderr)
        self.assertIn("git pull", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
