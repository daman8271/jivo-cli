"""jmail — JIVO mailbox reader, and the bridge from a vendor's emailed bill to SAP.

Read-only by construction: see imapread.py (IMAP) and sapmatch.py (SAP).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .config import load_config
from .imapread import attachment_bytes, session
from .mailprint import find_chrome, render_pdf
from .pdfextract import extract, have
from .sapmatch import SapUnavailable, match_bill, sapb1_bin

# Windows consoles default to cp1252, which cannot encode the check marks below
# (nor the rupee sign that shows up in matched bill amounts). Measured on
# DESKTOP-EQ55Q8H (Accounts, 2026-08-25): `jmail doctor` died with
# UnicodeEncodeError on "\u2713" before printing a single check. Same guard as
# harness/bin/setup.py and harness.py — force UTF-8 before anything prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

OK, WARN, BAD = "✓", "!", "✗"


def eprint(*a):
    print(*a, file=sys.stderr)


def safe_name(name: str) -> str:
    keep = "".join(c if (c.isalnum() or c in "._- ") else "_" for c in name)
    return keep.strip().replace(" ", "_")[:80] or "attachment"


# ---------------------------------------------------------------- doctor
def cmd_doctor(args) -> int:
    cfg, env_path = load_config()
    print("jmail doctor")
    print("============")
    missing = cfg.missing()
    if missing:
        print(f"{BAD} configuration      missing: {', '.join(missing)}")
        print(f"  hint: add them to {env_path} (that file is gitignored)")
        return 1
    print(f"{OK} configuration      user={cfg.user} host={cfg.imap_host}:{cfg.imap_port} "
          f"password={cfg.redacted}")
    try:
        with session(cfg, folder="INBOX") as m:
            count = m.select("INBOX")
            folders = m.folders()
        print(f"{OK} imap login         connected to {cfg.imap_host} as {cfg.user}")
        print(f"{OK} mailbox            INBOX has {count:,} messages, {len(folders)} folders")
    except Exception as exc:
        print(f"{BAD} imap login         {type(exc).__name__}: {str(exc)[:160]}")
        return 1

    print(f"{OK if have('pdftotext') else WARN} pdftotext          "
          f"{'available' if have('pdftotext') else 'MISSING — install poppler for PDF text'}")
    ocr_ready = have("tesseract") and have("pdftoppm")
    print(f"{OK if ocr_ready else WARN} ocr fallback       "
          f"{'tesseract + pdftoppm ready' if ocr_ready else 'not available — scanned bills will not read'}")
    sb = sapb1_bin()
    print(f"{OK if sb.is_file() else WARN} sapb1              "
          f"{'found at ' + str(sb) if sb.is_file() else 'MISSING — `jmail match` cannot reach SAP'}")
    print("\nRead-only: this tool opens mailboxes with EXAMINE and never sends, "
          "flags, moves or deletes mail.")
    return 0


# ---------------------------------------------------------------- folders
def cmd_folders(args) -> int:
    cfg, _ = load_config()
    with session(cfg, folder=None) as m:
        names = m.folders()
        rows = []
        for n in names:
            try:
                rows.append((n, m.select(n)))
            except Exception:
                rows.append((n, -1))
    if args.json:
        print(json.dumps([{"folder": n, "messages": c} for n, c in rows], indent=2))
        return 0
    print(f"{'FOLDER':<24} MESSAGES")
    for n, c in rows:
        print(f"{n:<24} {c if c >= 0 else 'n/a':>8}")
    return 0


# ---------------------------------------------------------------- search
def collect(m, uids, need_attachments: bool):
    for uid in uids:
        try:
            msg = m.fetch(uid)
        except Exception as exc:
            eprint(f"  ! uid {uid}: {exc}")
            continue
        if need_attachments and not msg.attachments:
            continue
        yield msg


def cmd_search(args) -> int:
    cfg, _ = load_config()
    with session(cfg, folder=args.folder) as m:
        uids = m.search(sender=args.sender, subject=args.subject, since=args.since,
                        before=args.before, text=args.text, unseen=args.unseen)
        if not uids:
            print("no messages matched")
            return 0
        uids = uids[-args.limit:]
        out = []
        for msg in collect(m, reversed(uids), args.with_attachments):
            out.append(msg)
            if len(out) >= args.limit:
                break

    if args.json:
        print(json.dumps([{
            "uid": x.uid, "date": x.date, "from": x.sender, "subject": x.subject,
            "attachments": [asdict(a) for a in x.attachments],
        } for x in out], indent=2))
        return 0

    print(f"{len(out)} message(s) in {args.folder}\n")
    for x in out:
        print(f"[{x.uid}] {x.date[:31]}")
        print(f"   from: {x.sender[:72]}")
        print(f"   subj: {x.subject[:76]}")
        for a in x.attachments:
            print(f"     - {a.filename[:52]:<52} {a.content_type:<26} {a.size/1024:>8.1f} KB")
        print()
    return 0


# ---------------------------------------------------------------- show
def cmd_show(args) -> int:
    cfg, _ = load_config()
    with session(cfg, folder=args.folder) as m:
        msg = m.fetch(args.uid)
    if args.json:
        print(json.dumps({"uid": msg.uid, "date": msg.date, "from": msg.sender,
                          "to": msg.to, "subject": msg.subject,
                          "message_id": msg.message_id, "body": msg.body_text,
                          "attachments": [asdict(a) for a in msg.attachments]}, indent=2))
        return 0
    print(f"uid     : {msg.uid}")
    print(f"date    : {msg.date}")
    print(f"from    : {msg.sender}")
    print(f"to      : {msg.to}")
    print(f"subject : {msg.subject}")
    if msg.attachments:
        print("attachments:")
        for a in msg.attachments:
            print(f"  - {a.filename}  ({a.content_type}, {a.size/1024:.1f} KB)")
    body = msg.body_text.strip()
    if body:
        print("\n--- body ---")
        print(body[: args.body_chars])
        if len(body) > args.body_chars:
            print(f"... [{len(body) - args.body_chars} more chars]")
    return 0


# ---------------------------------------------------------------- print
def cmd_print(args) -> int:
    """Render a thread to PDF — the paper an outgoing payment carries (C-0028)."""
    cfg, _ = load_config()
    with session(cfg, folder=args.folder) as m:
        msg = m.fetch(args.uid)
    if args.out:
        out = Path(args.out).expanduser()
    else:
        out = Path.cwd() / f"Jivo Wellness Mail - {safe_name(msg.subject)}.pdf"
    if out.is_dir():
        out = out / f"Jivo Wellness Mail - {safe_name(msg.subject)}.pdf"
    try:
        written = render_pdf(msg, out)
    except RuntimeError as exc:
        eprint(f"{BAD} {exc}")
        return 3
    kb = written.stat().st_size / 1024
    src = "html" if msg.body_html.strip() else "plain-text"
    print(f"{OK} {written}  ({kb:.1f} KB, rendered from the {src} part)")
    print(f"  subject : {msg.subject}")
    print(f"  from    : {msg.sender}")
    print(f"  date    : {msg.date}")
    return 0


# ---------------------------------------------------------------- pull
def cmd_pull(args) -> int:
    cfg, _ = load_config()
    outdir = Path(args.out).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    wanted = [t.lower().lstrip(".") for t in args.types.split(",")] if args.types else []
    written = []
    with session(cfg, folder=args.folder) as m:
        uids = args.uids or m.search(sender=args.sender, subject=args.subject,
                                     since=args.since, before=args.before)[-args.limit:]
        for msg in collect(m, reversed(uids), need_attachments=True):
            for a in msg.attachments:
                ext = a.filename.rsplit(".", 1)[-1].lower() if "." in a.filename else ""
                if wanted and ext not in wanted:
                    continue
                data = attachment_bytes(msg.raw, a.part_index)
                if not data:
                    continue
                dest = outdir / f"{msg.uid}__{safe_name(a.filename)}"
                dest.write_bytes(data)
                written.append({"uid": msg.uid, "date": msg.date, "from": msg.sender,
                                "subject": msg.subject, "file": str(dest),
                                "kb": round(len(data) / 1024, 1)})
    manifest = outdir / "manifest.json"
    manifest.write_text(json.dumps(written, indent=2))
    if args.json:
        print(json.dumps(written, indent=2))
        return 0
    for w in written:
        print(f"{w['kb']:>8.1f} KB  {w['subject'][:46]:<46} -> {Path(w['file']).name}")
    print(f"\n{len(written)} file(s) -> {outdir}")
    print(f"manifest: {manifest}")
    return 0


# ---------------------------------------------------------------- extract
def cmd_extract(args) -> int:
    facts = extract(Path(args.file), ocr_if_empty=not args.no_ocr)
    if args.json:
        d = asdict(facts)
        if not args.with_text:
            d.pop("text", None)
        print(json.dumps(d, indent=2))
        return 0
    print(f"file        : {facts.path}")
    print(f"read via    : {'OCR (scanned)' if facts.ocr_used else 'embedded text'}")
    print(f"grand total : {facts.grand_total:,.2f}" if facts.grand_total else "grand total : (not found)")
    print(f"gstins      : {', '.join(facts.gstins) or '(none)'}")
    print(f"dates       : {', '.join(facts.dates[:8]) or '(none)'}")
    print(f"candidate refs (best first): {', '.join(facts.refs[:12]) or '(none)'}")
    if args.with_text:
        print("\n--- text ---")
        print(facts.text[:4000])
    return 0


# ---------------------------------------------------------------- match
def verdict_mark(v: str) -> str:
    return {"IN_SAP_POSTED": OK, "IN_SAP_DRAFT": OK,
            "REF_MATCH_AMOUNT_DIFFERS": WARN,
            "NOT_IN_SAP": BAD, "SAP_ERROR": WARN}.get(v, WARN)


def match_one(path: Path, company: str | None, no_ocr: bool) -> dict:
    facts = extract(path, ocr_if_empty=not no_ocr)
    res = match_bill(facts.refs, facts.grand_total, company=company)
    return {
        "file": path.name,
        "verdict": res.verdict,
        "matched_ref": res.matched_ref,
        "paper_total": facts.grand_total,
        "candidates_tried": res.tried,
        "amount_note": res.amount_note,
        "error": res.error,
        "ocr_used": facts.ocr_used,
        "hits": [asdict(h) for h in res.hits],
    }


def cmd_match(args) -> int:
    targets: list[Path] = []
    p = Path(args.path).expanduser()
    if p.is_dir():
        targets = sorted(x for x in p.iterdir() if x.suffix.lower() == ".pdf")
    elif p.is_file():
        targets = [p]
    else:
        eprint(f"no such file or directory: {p}")
        return 2
    if not targets:
        eprint(f"no PDFs found in {p}")
        return 2

    results = []
    for t in targets:
        try:
            results.append(match_one(t, args.company, args.no_ocr))
        except SapUnavailable as exc:
            results.append({"file": t.name, "verdict": "SAP_ERROR", "error": str(exc), "hits": []})

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        company = args.company or "(sapb1 default)"
        print(f"Comparing {len(results)} bill(s) against SAP company: {company}\n")
        for r in results:
            print(f"{verdict_mark(r['verdict'])} {r['file']}")
            print(f"    verdict : {r['verdict']}"
                  + (f"  (ref {r['matched_ref']})" if r.get("matched_ref") else ""))
            if r.get("paper_total"):
                print(f"    paper   : {r['paper_total']:,.2f}")
            for h in r.get("hits", []):
                tds = f" TDS {h['wt_amount']:,.2f}" if h.get("wt_amount") else ""
                print(f"    sap     : {h['kind']} DocEntry {h['doc_entry']} "
                      f"({h['card_name'][:34]}) {h['doc_date']} "
                      f"total {h['doc_total']:,.2f}{tds}")
            if r.get("amount_note"):
                print(f"    amount  : {r['amount_note']}")
            if r.get("error"):
                print(f"    error   : {r['error'][:160]}")
            print()
        counts: dict[str, int] = {}
        for r in results:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        print("summary: " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


# ---------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="jmail",
        description="Read the JIVO accounts mailbox and match emailed vendor bills against SAP. "
                    "Read-only: never sends, flags, moves or deletes mail, and never writes to SAP.")
    ap.add_argument("--version", action="version", version=f"jmail {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_folder(p):
        p.add_argument("--folder", default="INBOX", help="mailbox folder (default INBOX)")

    def add_filters(p):
        p.add_argument("--sender", "--from", dest="sender", help="match sender address/name")
        p.add_argument("--subject", help="match subject substring")
        p.add_argument("--since", help="YYYY-MM-DD or '30d'")
        p.add_argument("--before", help="YYYY-MM-DD or '30d'")

    d = sub.add_parser("doctor", help="check mail credentials, connectivity and PDF tooling")
    d.set_defaults(func=cmd_doctor)

    f = sub.add_parser("folders", help="list mailbox folders and message counts")
    f.add_argument("--json", action="store_true")
    f.set_defaults(func=cmd_folders)

    s = sub.add_parser("search", help="search messages")
    add_folder(s); add_filters(s)
    s.add_argument("--text", help="full-text search inside messages")
    s.add_argument("--unseen", action="store_true", help="only unread messages")
    s.add_argument("--with-attachments", action="store_true", help="only messages carrying attachments")
    s.add_argument("--limit", type=int, default=25)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_search)

    sh = sub.add_parser("show", help="show one message")
    add_folder(sh)
    sh.add_argument("uid")
    sh.add_argument("--body-chars", type=int, default=2000)
    sh.add_argument("--json", action="store_true")
    sh.set_defaults(func=cmd_show)

    pr = sub.add_parser("print", help="render a thread to PDF (the approval mail for a payment)")
    pr.add_argument("uid")
    pr.add_argument("--folder", default="INBOX")
    pr.add_argument("--out", help="output .pdf path, or a directory; default: CWD, Gmail-style name")
    pr.set_defaults(func=cmd_print)

    pl = sub.add_parser("pull", help="download attachments to a folder")
    add_folder(pl); add_filters(pl)
    pl.add_argument("uids", nargs="*", help="specific message uids (else use the filters)")
    pl.add_argument("--out", default="./bills", help="output directory (default ./bills)")
    pl.add_argument("--types", default="pdf", help="comma-separated extensions, '' for all")
    pl.add_argument("--limit", type=int, default=50)
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(func=cmd_pull)

    ex = sub.add_parser("extract", help="read a bill PDF and show the identifiers found")
    ex.add_argument("file")
    ex.add_argument("--with-text", action="store_true")
    ex.add_argument("--no-ocr", action="store_true", help="skip the tesseract fallback")
    ex.add_argument("--json", action="store_true")
    ex.set_defaults(func=cmd_extract)

    mt = sub.add_parser("match", help="compare bill PDFs against SAP (posted, drafts, credit notes)")
    mt.add_argument("path", help="a PDF, or a folder of PDFs")
    mt.add_argument("--company", help="oil | mart | beverages (default: sapb1's own default)")
    mt.add_argument("--no-ocr", action="store_true")
    mt.add_argument("--json", action="store_true")
    mt.set_defaults(func=cmd_match)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        eprint("\ninterrupted")
        return 130
    except Exception as exc:
        eprint(f"error: {type(exc).__name__}: {exc}")
        return 1
