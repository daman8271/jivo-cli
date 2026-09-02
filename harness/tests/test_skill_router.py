"""skill_router: the SAP-entry skills fire on their own (Daman 2026-09-02)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("skill_router", HARNESS / "bin" / "skill_router.py")
sr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr)

CFG = sr.load_config()
ROUTES = sr.present_routes(CFG)


def names(text):
    return [l.split(":")[0].strip("- ").strip() for l in text.splitlines() if l.startswith("  - ")]


def test_every_route_skill_exists_on_this_checkout():
    missing = [r["skill"] for r in CFG["routes"] if r not in ROUTES]
    assert not missing, f"router names skills that are not in .claude/skills: {missing}"


def test_every_pattern_compiles():
    import re
    for r in CFG["routes"]:
        for p in r["patterns"]:
            re.compile(p)
    for p in CFG["generic_patterns"] + CFG["attachment_patterns"]:
        re.compile(p)


@pytest.mark.parametrize("prompt,skill", [
    ("yeh bill enter karo", "jivo-ap-draft"),
    ("ARNAV ka payment punch kar do", "jivo-outgoing-payment"),
    ("rent invoice for kundli godown", "jivo-rent-invoice"),
    ("loading unloading bill aaya hai", "jivo-loading-unloading-ap"),
    ("credit note from vendor", "jivo-ap-credit-memo"),
    ("expense claim of Gautam", "jivo-service-vehicle-expense"),
    ("send it to bhawani", "jivo-add-and-new"),
    ("bank statement ki entry", "jivo-banking"),
    ("summary pdf of today's entries", "jivo-summary-pdf"),
])
def test_specific_route(prompt, skill):
    out = sr.match_text(prompt, CFG, ROUTES)
    assert skill in names(out), out


def test_freight_lists_all_three_books():
    out = sr.match_text("PICK & SHIP bilty NCR-358", CFG, ROUTES)
    got = names(out)
    for s in ("jivo-oil-freight-grpo", "jivo-mart-freight-grpo", "jivo-bev-freight-grpo"):
        assert s in got, out


def test_attachment_with_no_words_lists_the_table():
    out = sr.match_text(r"C:\Users\Jivo108\Downloads\IMG_2201.jpg", CFG, ROUTES)
    assert "handed over" in out
    assert len(names(out)) == len(ROUTES)


def test_generic_entry_word_lists_the_table():
    out = sr.match_text("iski entry kar do", CFG, ROUTES)
    assert "handed over" in out


def test_ap_draft_nudges_add_and_new_after():
    out = sr.match_text("enter this invoice", CFG, ROUTES)
    assert "jivo-add-and-new" in out


@pytest.mark.parametrize("prompt", [
    "what is the balance of ARNAV",
    "turnover of oil this month",
    "/help",
    "",
    "   ",
    "thanks",
])
def test_silent_on_questions_and_slash(prompt):
    assert sr.match_text(prompt, CFG, ROUTES) == ""


def test_hidden_skill_is_not_listed(tmp_path):
    (tmp_path / "jivo-ap-draft").mkdir()
    (tmp_path / "jivo-ap-draft" / "SKILL.md").write_text("x")
    routes = sr.present_routes(CFG, tmp_path)
    assert [r["skill"] for r in routes] == ["jivo-ap-draft"]
    out = sr.match_text("rent invoice", CFG, routes)
    assert "jivo-rent-invoice" not in out


def test_output_is_ascii():
    for text in (sr.table_text(CFG, ROUTES), sr.match_text("enter this bill", CFG, ROUTES)):
        sr._ascii(text).encode("ascii")
        assert sr._ascii(text) == text, "router text must be plain ASCII (Windows cp1252 hooks)"


def test_table_mentions_every_present_skill():
    t = sr.table_text(CFG, ROUTES)
    for r in ROUTES:
        assert r["skill"] in t


def test_reads_hook_json(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", type("S", (), {"isatty": lambda self: False, "read": lambda self: json.dumps({"prompt": "rent invoice"})})())
    assert sr.main(["skill_router.py", "match"]) == 0
    assert "jivo-rent-invoice" in capsys.readouterr().out
