"""batch_status — what happened to a batch, read off disk.

Contacts nothing. The journal and the sidecar are written before and after every
write precisely so this question can be answered when SAP cannot be reached, or
when the run died halfway, or when somebody else ran it yesterday.

    python3 acc/acc.py batch status acc/_batches/<id>/review-<id>.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import store
from .sap import find_repo

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def run_status(args, repo: Path | str | None = None) -> int:
    repo = Path(repo) if repo else find_repo()
    book = Path(getattr(args, "workbook", "") or "")
    if not book.exists():
        print(f"acc batch status: no such workbook: {book}", file=sys.stderr)
        return 2

    batch_id = store.batch_id_from_workbook(book)
    path = store.find_sidecar_for(book, batch_id=batch_id, repo=repo)
    if not path:
        print(f"acc batch status: no sidecar next to {book.name} or in "
              f"{store.batch_dir(repo, batch_id or '<id>')} — nothing to report on",
              file=sys.stderr)
        return 2
    try:
        sidecar = store.Sidecar.load(path)
    except store.SidecarError as e:
        print(f"acc batch status: {e}", file=sys.stderr)
        return 2

    journal = store.Journal(book.parent / store.journal_name(sidecar.batch_id))
    events = journal.events()
    if not events:                          # a batch scanned before the id-stamped names
        journal = store.Journal(book.parent / "journal.jsonl")
        events = journal.events()

    print(f"== batch {sidecar.batch_id} · {sidecar.company} · scanned by {sidecar.login} "
          f"on {sidecar.scanned_at[:19]} ({sidecar.age_days()} day(s) ago)")
    print(f"   workbook {book}")
    print(f"   sidecar  {path}")
    print(f"   journal  {journal.path}{'' if events else '  (no events yet)'}")

    counts = sidecar.counts()
    print("\n   scan said:")
    for status, n in sorted(counts.items()):
        print(f"     {status:<16} {n:>4}")

    runs = [e for e in events if e.get("event") == "send-start"]
    if runs:
        print("\n   send runs:")
        for e in runs:
            mode = "SENT" if e.get("sending") else "preview"
            print(f"     {e.get('run')}  {mode:<8} by {e.get('login')} on {e.get('host')}"
                  f"{'  (--resume)' if e.get('resume') else ''}")
    else:
        print("\n   send runs: none — this batch has never been sent or previewed")

    # The journal is written BEFORE the sidecar, so a crash between the two
    # leaves the draft's DocEntry in the journal and nowhere else. That is
    # exactly the run somebody is asking this question about, so both are read
    # and the journal fills in what the sidecar never got to record.
    from_journal = _drafts_from_journal(events)
    outcomes = [(int(row.get("row") or 0), key, row) for key, row in sidecar.rows.items()
                if row.get("outcome") or str(key) in from_journal]
    if outcomes:
        print("\n   what SAP holds because of this batch:")
        for _n, key, row in sorted(outcomes):
            out = dict(row.get("outcome") or {})
            journalled = from_journal.get(str(key))
            note = ""
            if journalled and not out.get("draft_entry"):
                out.setdefault("state", journalled["state"])
                out["draft_entry"] = journalled.get("draft_entry")
                note = "  (from the journal — the sidecar never recorded it)"
            entry = out.get("draft_entry")
            line = (f"     row {row.get('row'):>3}  GRPO {key:<8} {str(out.get('state')):<18} "
                    f"{('draft ' + str(entry)) if entry else ''}{note}")
            print(line.rstrip())
            if out.get("message"):
                print(f"            {out['message']}")
    else:
        print("\n   no row of this batch has produced a draft.")

    unfinished = journal.in_flight()
    if unfinished:
        print(f"\n   !! {len(unfinished)} row(s) were sent and never answered: {unfinished}")
        print("      Do NOT re-run them. Look in Document Drafts, then:")
        print(f"      acc batch send \"{book}\" --resume")

    print("\n   every write this batch made, in the shared log:")
    print(f"     grep {sidecar.batch_id} queries/*/sap-writes.jsonl")
    return 0


def _drafts_from_journal(events) -> dict[str, dict]:
    """{GRPO DocEntry: the last draft the journal says was made for it}."""
    out: dict[str, dict] = {}
    for e in events:
        if e.get("event") not in ("draft", "resume"):
            continue
        if e.get("state") not in ("created", "recovered") or not e.get("draft_entry"):
            continue
        out[str(e.get("docentry"))] = {
            "state": "CREATED" if e["state"] == "created" else "CREATED-RECOVERED",
            "draft_entry": e.get("draft_entry"), "draft_num": e.get("draft_num")}
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="acc batch status", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook")
    return ap


def main(argv: list[str] | None = None) -> int:
    return run_status(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
