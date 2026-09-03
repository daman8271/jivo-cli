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


# --- drafts-only desks: the submit skill is hidden, so it is never named ------
# Mahak's GRPO desk builds drafts and she presses Add herself (Daman 2026-09-03).
# desks.json hides .claude/skills/jivo-add-and-new there, and both the table and
# the per-prompt nudge must fall silent about it — pointing at a bolted door is
# how an operator ends up asking why "the AI keeps saying it sent it".

def test_always_after_is_never_named_when_the_skill_is_hidden(tmp_path):
    empty = tmp_path / "skills"          # a desk carrying no skill folders at all
    empty.mkdir()
    routes = [dict(CFG["routes"][0])]    # a real A/P route, so the nudge fires
    nudge = sr.match_text("yeh bill enter karo", CFG, routes)
    assert nudge, "the entry nudge itself must still fire"
    real = sr.SKILLS
    try:
        sr.SKILLS = empty
        hidden = sr.match_text("yeh bill enter karo", CFG, routes)
        table = sr.table_text(CFG, routes)
    finally:
        sr.SKILLS = real
    assert CFG["always_after"]["skill"] not in hidden, (
        "a desk that does not carry the submit skill must never be told to run it")
    assert CFG["always_after"]["skill"] not in table


def test_desks_json_drafts_only_matches_mahaks_box():
    import importlib.util as _u
    spec = _u.spec_from_file_location("desk", HARNESS / "bin" / "desk.py")
    desk = _u.module_from_spec(spec)
    spec.loader.exec_module(desk)
    assert desk.drafts_only_note(["PC-AUDIT-05"]), "Mahak's box must be drafts-only"
    assert desk.drafts_only_note(["mahak"]), "the operator slug must match too"
    assert not desk.drafts_only_note(["HO-IT-PC1"]), "other desks keep add-draft"


def test_drafts_only_desks_do_not_carry_the_submit_skill():
    """The two halves of the lock must name the same boxes, or a desk gets the
    'send it to Bhawani' skill while its binary refuses to send."""
    cfg = json.loads((HARNESS / "desks.json").read_text(encoding="utf-8"))
    submit_sets = [name for name, paths in cfg["skill_sets"].items()
                   if any("jivo-add-and-new" in p for p in paths)]
    assert submit_sets, "no skill set hides jivo-add-and-new"
    hidden_from = {w.lower() for rule in cfg["exclude"]
                   if set(rule.get("sets", [])) & set(submit_sets)
                   for w in rule["who"]}
    for rule in cfg.get("drafts_only", []):
        for who in rule["who"]:
            assert who.lower() in hidden_from, (
                f"{who} is drafts-only but still carries jivo-add-and-new")
