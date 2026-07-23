"""'vault' command — browse the Obsidian memory vault under <root>/vault.

    jivo-scrape vault
    jivo-scrape vault --section daily --name 2026-07
    jivo-scrape vault --show daily/2026-07-19.md
    jivo-scrape vault --json

Lists note files (.md / .json / .csv) under ``<root>/vault``, newest-first, as
an aligned table (modified, size, relpath); ``--show RELPATH`` cats one note raw
(its own frontmatter headers pass straight through). When ``vault/`` is absent
the command notes it rather than crashing. READ-ONLY.
"""

import os
import sys

from jivo_scrape import util
from jivo_scrape.sources import vaultview


def register(sub):
    p = sub.add_parser(
        "vault",
        help="browse the Obsidian memory vault (notes under <root>/vault)",
    )
    p.add_argument(
        "--section",
        help="limit to a vault section: %s" % ", ".join(vaultview.VAULT_SECTIONS),
    )
    p.add_argument(
        "--name", help="case-insensitive substring filter over the note relpath"
    )
    p.add_argument(
        "--show",
        metavar="RELPATH",
        help="print one note raw (path relative to vault/); headers pass through",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=40,
        help="max rows shown in human output (default: 40; --json is unlimited)",
    )
    util.add_common_flags(p)
    p.set_defaults(func=run)


def run(args):
    vault_dir = os.path.join(util.ECOM, "vault")
    index_path = os.path.join(vault_dir, "index.md")
    present = os.path.isdir(vault_dir)

    # --show: raw passthrough of a single note (traversal-guarded reader).
    # A ValueError('path escapes root') bubbles to the dispatcher (exit 2);
    # a genuinely missing note bubbles as FileNotFoundError (exit 3).
    if args.show:
        text = vaultview.read_note(vault_dir, args.show)
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return 0

    entries = vaultview.list_notes(vault_dir, section=args.section, pattern=args.name)

    notes = []
    if not present:
        notes.append("vault/ absent under %s" % util.ECOM)
    elif args.section and not os.path.isdir(os.path.join(vault_dir, args.section)):
        notes.append(
            "section %r not found (known: %s)"
            % (args.section, ", ".join(vaultview.VAULT_SECTIONS))
        )

    meta = {
        "command": "vault",
        "section": args.section,
        "pattern": args.name,
        "count": len(entries),
        "freshness": {"vault/index.md": util.freshness(index_path)},
        "notes": notes,
    }
    results = {"notes": entries}

    def human(res):
        print(
            "vault · %s%s"
            % (
                args.section or "all sections",
                "" if not args.name else " · name~%r" % args.name,
            )
        )
        rows = res["notes"]
        if not present:
            print("  vault/ not found at %s" % vault_dir)
        elif not rows:
            print("  no notes matched.")
        else:
            shown = rows[: args.limit]
            trows = [
                [e["mtime"], vaultview.human_size(e["size"]), e["relpath"]]
                for e in shown
            ]
            print(vaultview.table(["MODIFIED", "SIZE", "RELPATH"], trows))
            if len(shown) < len(rows):
                print(
                    "  %d note(s) — showing newest %d (use --json for all)"
                    % (len(rows), len(shown))
                )
            else:
                print("  %d note(s)." % len(rows))
        for n in notes:
            print("  note: %s" % n, file=sys.stderr)

    util.emit(args, results, meta, human)
    return 0
