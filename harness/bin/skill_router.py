#!/usr/bin/env python3
"""JIVO harness - skill router: the SAP-entry skills fire on their own.

Two entry points, both called by the hooks and both read-only:

  table   SessionStart      print the routing table for the skills present on
                            THIS checkout, so a session knows which skill owns
                            which document before the first prompt arrives.
  match   UserPromptSubmit  read the hook JSON on stdin; when the prompt looks
                            like an SAP entry, print one short instruction
                            naming the skill(s) to invoke first. Silent otherwise,
                            so an ordinary question still costs zero tokens.

Why a hook and not the skill descriptions alone: Claude Code picks a skill by
its description, which works when the operator types the right words. Accounts
operators drop a PDF and say nothing, or say "yeh karo". The table at session
start plus the nudge per prompt is what makes the right skill fire anyway
(Daman, 2026-09-02: "if the skill is matching what he is doing, it
automatically triggers").

Routes live in harness/skill-router.json. A route is listed only when its
skill folder exists in .claude/skills/, so harness/desks.json exclusions
(HR/tax/IT boxes) apply without a second list.

Output is ASCII only on purpose: PowerShell 5.1 + cp1252 once turned a single
em dash into an empty digest on every Windows box (see session-start.sh).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
CONFIG = HARNESS / "skill-router.json"
SKILLS = REPO / ".claude" / "skills"

TAG = "[jivo skill router]"


def load_config(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def present_routes(cfg: dict, skills_dir: Path = SKILLS) -> list[dict]:
    """Only the skills that exist on this checkout - desk exclusions hide folders."""
    return [r for r in cfg.get("routes", []) if (skills_dir / r["skill"] / "SKILL.md").exists()]


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify(prompt: str, cfg: dict, routes: list[dict]) -> dict:
    """Return which routes match and why. Pure; no I/O."""
    text = prompt or ""
    stripped = text.strip()
    out = {"specific": [], "generic": False, "attachment": False, "slash": False}
    if not stripped or stripped.startswith("/"):
        out["slash"] = bool(stripped)
        return out
    hits = [r for r in routes if _any(r.get("patterns", []), text)]
    # A freight word means "one of the three freight books" - the bill-to
    # decides which, so list the whole group rather than guess.
    groups = {r.get("group") for r in hits if r.get("group")}
    for r in routes:
        if r.get("group") in groups and r not in hits:
            hits.append(r)
    out["specific"] = hits
    out["generic"] = _any(cfg.get("generic_patterns", []), text)
    out["attachment"] = _any(cfg.get("attachment_patterns", []), text)
    return out


def _line(r: dict) -> str:
    return f"  - {r['skill']}: {r['when']}"


def table_text(cfg: dict, routes: list[dict]) -> str:
    if not routes:
        return ""
    lines = [
        "## SAP entry skills - they fire on their own",
        "",
        "When the operator wants something ENTERED in SAP - a bill, a payment, a freight",
        "GRPO, a claim - invoke the skill that owns that document with the Skill tool",
        "BEFORE any other tool call, even when the prompt is only a PDF or photo with no",
        "words at all. Decide from what the document IS, not from the words used.",
        "",
    ]
    lines += [_line(r) for r in routes]
    aa = cfg.get("always_after")
    if aa and (SKILLS / aa["skill"] / "SKILL.md").exists():
        lines += ["", f"  {aa['skill']}: {aa['when']}"]
    lines += ["", "A read question (a balance, a lookup, a report) is not an entry - answer it;",
              "cli-hub says which CLI to reach for when unsure."]
    return "\n".join(lines)


def match_text(prompt: str, cfg: dict, routes: list[dict]) -> str:
    c = classify(prompt, cfg, routes)
    if c["specific"]:
        lines = [f"{TAG} This looks like an SAP entry. If the operator wants something ENTERED,",
                 "invoke the matching skill with the Skill tool BEFORE any other tool call:"]
        lines += [_line(r) for r in c["specific"][:4]]
        lines += ["If it is only a question (a balance, a lookup), ignore this and answer it."]
        aa = cfg.get("always_after")
        # Same gate as table_text: a skill this desk does not carry is never
        # named. A drafts-only desk has jivo-add-and-new hidden, and telling it
        # to "finish the job" would be pointing at a door that is bolted.
        if (aa and (SKILLS / aa["skill"] / "SKILL.md").exists()
                and any(r["skill"].startswith("jivo-ap") for r in c["specific"])):
            lines += [f"After the draft: {aa['skill']} - {aa['when']}"]
        return "\n".join(lines)
    if c["attachment"] or c["generic"]:
        if not routes:
            return ""
        lines = [f"{TAG} A document or an entry was handed over with no clear type. Read it, decide",
                 "what it IS, then invoke that skill with the Skill tool BEFORE any other tool call:"]
        lines += [_line(r) for r in routes]
        return "\n".join(lines)
    return ""


def _ascii(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def _read_prompt() -> str:
    if sys.stdin.isatty():
        return ""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return raw
    return payload.get("prompt", "") if isinstance(payload, dict) else ""


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "table"
    cfg = load_config()
    routes = present_routes(cfg)
    if cmd == "table":
        text = table_text(cfg, routes)
    elif cmd == "match":
        text = match_text(_read_prompt(), cfg, routes)
    elif cmd == "test":
        text = match_text(" ".join(argv[2:]), cfg, routes) or "(silent)"
    else:
        print(__doc__, file=sys.stderr)
        return 2
    if text:
        sys.stdout.write(_ascii(text) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
