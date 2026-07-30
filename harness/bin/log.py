#!/usr/bin/env python3
"""JIVO log — write this operator's session note into their own folder.

One file per operator per day, `chats/<slug>/YYYY-MM-DD.md`, in the same
Obsidian shape as the top-level `chats/` journal: frontmatter, a heading per
entry, `[[wikilinks]]` between notes. The operator's MOC is kept in sync so the
folder always reads newest-first.

Claude calls this; a cron does not. A scraper can only capture the text of a
question, which is the least useful half — what matters is what was actually
found, which number came back, and what it means. Only the agent that did the
work knows that, so the agent writes the note.

This tool NEVER touches SAP or any business system. It writes only under
`chats/<slug>/`.

Usage
-----
  # append an entry (body on stdin — the normal path)
  echo "Pulled July Oil turnover: Rs 26.18 Cr net." \\
    | python3 harness/bin/log.py add --title "Oil turnover, July"

  python3 harness/bin/log.py add --title "..." --body "..."
  python3 harness/bin/log.py today          # path to today's file
  python3 harness/bin/log.py status         # has this session been logged?
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
OPERATOR = HARNESS / ".operator"
CHATS = REPO / "chats"


def _registration() -> dict:
    if not OPERATOR.exists():
        sys.stderr.write(
            "log: not registered on this machine — run:\n"
            "       python3 harness/bin/setup.py\n")
        raise SystemExit(2)
    try:
        return json.loads(OPERATOR.read_text(encoding="utf-8"))
    except Exception as exc:
        sys.stderr.write(f"log: unreadable {OPERATOR}: {exc}\n")
        raise SystemExit(2)


def _today_path(slug: str) -> Path:
    return CHATS / slug / f"{_dt.date.today().isoformat()}.md"


def _ensure_day(path: Path, reg: dict) -> None:
    """Create today's note with frontmatter if it does not exist yet."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    today = _dt.date.today().isoformat()
    slug = reg.get("slug", "operator")
    path.write_text(
        f"""---
title: {reg.get('name', 'Operator')} — {today}
date: {today}
operator: {reg.get('name', '')}
department: {reg.get('department', '')}
type: session-log
tags: [chats, {reg.get('department', 'general')}]
---

# {today}

Session log. Index: [[{slug}-MOC]]
""",
        encoding="utf-8",
    )


def _update_moc(reg: dict, title: str) -> None:
    """Add today's note to the operator's MOC, newest first, once per day."""
    slug = reg.get("slug", "operator")
    moc = CHATS / slug / f"{slug}-MOC.md"
    if not moc.exists():
        return
    today = _dt.date.today().isoformat()
    text = moc.read_text(encoding="utf-8")

    line = f"- [[{today}]] — {title}"
    if f"[[{today}]]" in text:
        # Already listed today; refresh the summary rather than adding a
        # second bullet for the same day.
        text = re.sub(rf"^- \[\[{re.escape(today)}\]\].*$", line, text,
                      count=1, flags=re.M)
    else:
        placeholder = "_(none yet — the first session will add itself here)_"
        if placeholder in text:
            text = text.replace(placeholder, line)
        elif "## Sessions" in text:
            text = text.replace("## Sessions\n", f"## Sessions\n{line}\n", 1)
        else:
            text = text.rstrip() + f"\n\n## Sessions\n{line}\n"

    text = re.sub(r"^updated: .*$", f"updated: {today}", text, count=1, flags=re.M)
    moc.write_text(text, encoding="utf-8")


def cmd_add(args: argparse.Namespace) -> int:
    reg = _registration()
    body = args.body if args.body is not None else sys.stdin.read()
    body = body.strip()
    if not body and not args.title:
        sys.stderr.write("log: nothing to write (empty body and no --title)\n")
        return 2

    path = _today_path(reg["slug"])
    _ensure_day(path, reg)

    stamp = _dt.datetime.now().strftime("%H:%M")
    entry = f"\n## {stamp} — {args.title}\n\n{body}\n" if args.title else f"\n{body}\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry)

    if args.title:
        _update_moc(reg, args.title)

    print(f"log: wrote to {path.relative_to(REPO)}")
    return 0


def cmd_today(args: argparse.Namespace) -> int:
    reg = _registration()
    path = _today_path(reg["slug"])
    print(path if args.absolute else path.relative_to(REPO))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    reg = _registration()
    path = _today_path(reg["slug"])
    print(f"operator : {reg.get('name')} ({reg.get('department')})")
    print(f"today    : {path.relative_to(REPO)}")
    if path.exists():
        entries = len(re.findall(r"^## \d\d:\d\d — ", path.read_text(encoding="utf-8"), re.M))
        print(f"logged   : yes — {entries} entr{'y' if entries == 1 else 'ies'}")
        return 0
    print("logged   : NOT YET today")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="log", description="Write this operator's session note.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", help="append an entry to today's note")
    p.add_argument("--title", default="", help="short heading; also the MOC summary")
    p.add_argument("--body", help="entry body (default: read stdin)")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("today", help="print the path to today's note")
    p.add_argument("-a", "--absolute", action="store_true")
    p.set_defaults(func=cmd_today)

    p = sub.add_parser("status", help="has this operator logged today?")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
