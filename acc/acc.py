#!/usr/bin/env python3
"""acc — the Accounts workbench command line.

    python3 acc/acc.py batch scan --company Oil --limit 50
    python3 acc/acc.py batch send  acc/_batches/<id>/review-<id>.xlsx
    python3 acc/acc.py batch status acc/_batches/<id>/review-<id>.xlsx

On Windows use `acc\\acc.cmd` with the same arguments.

`scan` is READ-ONLY: it walks the open goods receipts, works out which ones can
become A/P invoice drafts and which cannot, and writes a review workbook. It
cannot write to SAP — the client it builds refuses.

`send` reads the workbook back and creates DRAFTS for the rows a person ticked.
Nothing it makes is posted: a human opens SAP B1 → Document Drafts and presses
Add. Without --yes it only previews.

Standard exit codes across the subcommands:
    0 fine · 2 usage / bad workbook · 3 config or login · 4 SAP unreachable
    7 a write went out and no answer came back — go look, then `send --resume`.
      Exit 4 and exit 7 both name any draft the run had already created; a halt
      never claims nothing was sent.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Drop this script's own directory: it contains acc.py, which would shadow the
# `acc` package and break `import acc.apbatch` when run as `python3 acc/acc.py`.
_HERE = str(Path(__file__).resolve().parent)
sys.path[:] = [p for p in sys.path if p not in ("", ".", _HERE)]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="acc", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # dest="topic", NOT "group": `batch scan` has its own --group flag (the
    # business partner group), and argparse would let it overwrite the
    # subcommand's own dest — which it did, and the whole command silently fell
    # through to "nothing to do".
    sub = ap.add_subparsers(dest="topic", required=True)

    batch = sub.add_parser("batch", help="A/P invoice drafts from open GRPOs, 50 at a time")
    bsub = batch.add_subparsers(dest="action", required=True)

    scan = bsub.add_parser(
        "scan", help="read open GRPOs and write a review workbook (never writes to SAP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n"
               "  python3 acc/acc.py batch scan --company Oil --limit 50 "
               "--env navdeep-user36.env\n")
    scan.add_argument("--company", default="Oil",
                      help="Oil (default), Mart, Beverages, or a full JIVO_*_HANADB name")
    scan.add_argument("--since", help="earliest GRPO posting date, YYYY-MM-DD (default: 90 days back)")
    scan.add_argument("--vendor", help="a CardCode (filtered in SAP) or part of a vendor name")
    scan.add_argument("--group", help="only vendors in this business partner group, e.g. TRANSPORTER")
    scan.add_argument("--limit", type=int, default=50, help="how many rows to review (0 = all)")
    scan.add_argument("--order", choices=["oldest", "newest"], default="oldest",
                      help="which end of the pile to take the rows from")
    scan.add_argument("--include-intercompany", action="store_true",
                      help="also build drafts for JIVO group companies (C-0020); held by default")
    scan.add_argument("--allow-service", action="store_true",
                      help="also build drafts for service GRPOs — that payload shape is unproven")
    scan.add_argument("--env", help="per-operator env file next to sapb1 (decides whose drafts these are)")
    scan.add_argument("--out", help="write the workbook here instead of acc/_batches/<batch id>/")
    scan.add_argument("--quiet", action="store_true", help="only errors")

    send = bsub.add_parser(
        "send", help="create drafts for the approved rows of a review workbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Without --yes it PREVIEWS: every approved row is re-checked against SAP and\n"
               "dry-run through sapb1, and nothing is sent.\n\n"
               "  python3 acc/acc.py batch send review-B260824-OIL-7F3A.xlsx\n"
               "  python3 acc/acc.py batch send review-B260824-OIL-7F3A.xlsx --yes\n")
    send.add_argument("workbook")
    send.add_argument("--yes", action="store_true", help="actually send (without this it previews)")
    send.add_argument("--dry-run", action="store_true",
                      help="preview explicitly; wins over --yes if both are given")
    send.add_argument("--resume", action="store_true",
                      help="settle the rows an earlier run never got an answer for. On its own "
                           "it LOOKS and reports; with --yes it settles them FIRST and only "
                           "then sends the rest — and if any of them is still unaccounted for, "
                           "nothing else is sent at all")
    send.add_argument("--max-age-days", type=int, default=3,
                      help="refuse a sidecar older than this many days (0 = no limit)")
    send.add_argument("--env", help="per-operator env file next to sapb1 (whose drafts these are)")
    send.add_argument("--quiet", action="store_true", help="only errors")

    status = bsub.add_parser("status", help="what happened to a batch (reads disk, not SAP)")
    status.add_argument("workbook")

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.topic == "batch" and args.action == "scan":
        from acc.apbatch import batch_scan
        return batch_scan.run_scan(args)

    if args.topic == "batch" and args.action == "send":
        from acc.apbatch import batch_send
        return batch_send.run_send(args)

    if args.topic == "batch" and args.action == "status":
        from acc.apbatch import batch_status
        return batch_status.run_status(args)

    print("acc: nothing to do", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
