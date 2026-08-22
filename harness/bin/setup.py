#!/usr/bin/env python3
"""JIVO setup — register this operator on this machine. Run once.

Asks two questions (name, department) and wires up everything that depends on
knowing who is sitting here:

  harness/.operator      identity, stamped onto every report they produce
  harness/.persona       department, which filters the corrections they carry
  chats/<slug>/          their session log, Obsidian-style, committed to main
  queries/<slug>/        the queries they ran, same convention

The identity files are gitignored (per-machine). The chat and query folders are
TRACKED: every operator commits their own subfolder straight to `main`, which
is what makes one shared history work with no branches to manage.

This tool NEVER touches SAP or any business system.

Usage
-----
  python3 harness/bin/setup.py                 interactive
  python3 harness/bin/setup.py --name "Param Singh" --department accounts
  python3 harness/bin/setup.py --show           print current registration
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode the characters that
# actually occur in JIVO's data — the rupee sign, en dashes, the check marks in
# this tool's own output. Measured on HO-IT-PC2 (Accounts, 2026-08-22):
# `setup.py --show` died with UnicodeEncodeError on "\u2713" AFTER it had already
# written the identity files, so the operator saw a traceback for a run that had
# in fact succeeded. Same guard as harness.py — force UTF-8 before anything prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
OPERATOR = HARNESS / ".operator"
PERSONA = HARNESS / ".persona"
CHATS = REPO / "chats"
QUERIES = REPO / "queries"

# Same set the harness already uses to filter corrections by area (see
# VALID_AREAS in harness.py), so the department answered here doubles as the
# persona and nothing needs mapping. Keep the two lists identical: a department
# that is not a valid area can have corrections written FOR it that are then
# never delivered TO it.
DEPARTMENTS = ["accounts", "sales", "factory", "ecom", "exim", "ops", "hr", "it"]


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "operator"


def _ask(prompt: str, valid: list[str] | None = None) -> str:
    while True:
        try:
            answer = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nsetup: cancelled", file=sys.stderr)
            sys.exit(1)
        if not answer:
            print("  (required)")
            continue
        if valid and answer.lower() not in valid:
            print(f"  pick one of: {', '.join(valid)}")
            continue
        return answer


def _write_log_folder(slug: str, name: str, department: str) -> Path:
    """Create this operator's chat + query folders with an Obsidian MOC.

    Mirrors the convention already used by `chats/` at the top level —
    frontmatter, a MOC that wikilinks every session newest-first — so the
    folder opens cleanly in Obsidian and reads the same way as the rest of
    the vault.
    """
    folder = CHATS / slug
    folder.mkdir(parents=True, exist_ok=True)
    queries = QUERIES / slug
    queries.mkdir(parents=True, exist_ok=True)

    # Git cannot track an empty directory, and an empty pathspec breaks the
    # daily `git commit` outright — which silently stops this operator syncing
    # until they happen to run their first query. Seed the folder so it exists
    # in git from the moment they register.
    readme = queries / "README.md"
    if not readme.exists():
        readme.write_text(
            f"""---
title: {name} — Queries
operator: {name}
department: {department}
type: index
tags: [queries, {department}]
---

# {name} — Queries

Queries run during sessions land here, plus `sap-writes.jsonl` recording every
SAP write attempted from this machine.

Session notes: [[../../chats/{slug}/{slug}-MOC]]
""",
            encoding="utf-8",
        )

    moc = folder / f"{slug}-MOC.md"
    if not moc.exists():
        today = _dt.date.today().isoformat()
        moc.write_text(
            f"""---
title: {name} — Session Log (Map of Content)
created: {today}
updated: {today}
operator: {name}
department: {department}
type: moc
tags: [logs, moc, {department}]
---

# {name} — Session Log

Every session, newest first. One file per day, named `YYYY-MM-DD.md`.
Queries run during a session are captured under [[../../queries/{slug}]].

Part of the shared journal — see [[Chats-MOC]] for the whole team.

## Sessions
_(none yet — the first session will add itself here)_
""",
            encoding="utf-8",
        )
    return folder


def cmd_show() -> int:
    if not OPERATOR.exists():
        print("Not registered on this machine.\n\n  python3 harness/bin/setup.py")
        return 1
    data = json.loads(OPERATOR.read_text(encoding="utf-8"))
    print(json.dumps(data, indent=2))
    slug = data.get("slug", "")
    for label, folder in (("chats  ", CHATS / slug), ("queries", QUERIES / slug)):
        print(f"\n{label}    : {folder}  {'✓' if folder.exists() else '✗ MISSING'}")
    print(f"persona    : {PERSONA.read_text().strip() if PERSONA.exists() else '(unset)'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="setup", description="Register this operator on this machine.")
    ap.add_argument("--name")
    ap.add_argument("--department", choices=DEPARTMENTS)
    ap.add_argument("--show", action="store_true", help="print current registration")
    ap.add_argument("--force", action="store_true", help="re-register over an existing one")
    args = ap.parse_args()

    if args.show:
        return cmd_show()

    if OPERATOR.exists() and not args.force:
        print("Already registered on this machine:\n")
        cmd_show()
        print("\nTo change it:  python3 harness/bin/setup.py --force")
        return 0

    name = args.name
    department = args.department
    if not name or not department:
        print("\n  JIVO toolkit — one-time setup\n")
        print("  Two questions. This is so your work is logged under your own")
        print("  name and any report you produce carries it.\n")
        name = name or _ask("  Your full name: ")
        department = department or _ask(
            f"  Your department ({'/'.join(DEPARTMENTS)}): ", DEPARTMENTS)

    department = department.lower()
    slug = _slug(name)

    OPERATOR.write_text(json.dumps({
        "name": name,
        "department": department,
        "slug": slug,
        "registered_at": _dt.datetime.now().replace(microsecond=0).isoformat(),
    }, indent=2) + "\n", encoding="utf-8")

    PERSONA.write_text(department + "\n", encoding="utf-8")
    folder = _write_log_folder(slug, name, department)

    # A department with no persona file registers fine and then silently gets no
    # team framing at all, which is worse than an obvious error.
    if not (HARNESS / "personas" / f"{department}.md").exists():
        print(f"\n  note: no persona file for '{department}' yet "
              f"(harness/personas/{department}.md).\n"
              f"  You are registered and everything works; tell Daman so your "
              f"team's framing gets written.")

    print(f"""
  Registered.

    name        {name}
    department  {department}
    your chats  chats/{slug}/
    your queries queries/{slug}/

  Reports you produce carry:     powered by daman
                                 {name.split()[0].lower()} · <date>
  Rules you carry are filtered to: {department} (+ team-wide)

  Nothing else to do. Your sessions log themselves.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
