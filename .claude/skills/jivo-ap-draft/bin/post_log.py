#!/usr/bin/env python3
"""post_log — a Desktop record of every document posted DIRECT (no JSAP).

Daman, 2026-09-04: whenever something is posted that was never going to JSAP,
it must be written down on the Desktop -- the draft number, what it was, and
what it became. A posted document cannot be undone or re-attributed from this
CLI, so the record is the only thing that says who did what.

Where it goes:
    ~/Desktop/JIVO-Direct-Posts/
        YYYY-MM.csv        one row per post, the whole month (open in Excel)
        YYYY-MM-DD.md      the day, readable, grouped by desk
        ALL-POSTS.csv      every post ever, appended, never rewritten

What each row carries:
    when · book · DRAFT number · posted invoice number · vendor · vendor's bill
    number · what it was for · amount · TDS · the desk that CREATED the draft ·
    the SAP login that POSTED it · lane · in-scope? · outcome

Usage
    post_log.py --record 55651 56123        # after posting, per DocEntry
    post_log.py --record 55651 --company oil
    post_log.py --backfill                  # rebuild from the shared write log
    post_log.py --show                      # print today's file

Read-only against SAP. Writes only under ~/Desktop and nothing else.
"""
import argparse
import csv
import datetime
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jsap_route import POST_NOW, WAITS, binary, classify  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DESK = os.path.expanduser("~/Desktop/JIVO-Direct-Posts")
HANA = None  # resolved lazily

COMPANY_DB = {"oil": "JIVO_OIL_HANADB", "mart": "JIVO_MART_HANADB",
              "bev": "JIVO_BEVERAGES_HANADB"}
SCHEMA = COMPANY_DB
BOOK = {v: k for k, v in COMPANY_DB.items()}

# The five desks whose drafts are ours to post (harness rule, 2026-09-04).
IN_SCOPE = {"USER07", "USER08", "USER09", "USER19", "USER39"}

FIELDS = ["when", "book", "draft", "invoice_docnum", "invoice_docentry",
          "vendor", "vendor_bill", "what_for", "amount", "tds",
          "draft_made_by", "posted_by_login", "lane", "in_scope", "outcome"]


def _money(v):
    """SAP hands back '113.000000'. Nobody reads that."""
    try:
        return "{:,.2f}".format(float(v))
    except (TypeError, ValueError):
        return ""


def hana(sql):
    global HANA
    if HANA is None:
        HANA = binary("hana-sql", "hana-sql")
    p = subprocess.run([HANA, "-csv", sql], capture_output=True, text=True, timeout=180)
    out = (p.stdout or "").strip()
    if p.returncode != 0 or out.startswith("QUERY ERROR"):
        raise RuntimeError((p.stderr or out).strip().splitlines()[0][:200])
    import io
    return list(csv.DictReader(io.StringIO(out))) if out else []


def draft_facts(company, docentries):
    """Everything we want to remember about a draft, read straight from SAP.

    Deliberately reads the DRAFT, not just the invoice: once a draft is posted
    the invoice no longer says which desk keyed it, and that is the fact this
    log exists to preserve."""
    s = SCHEMA[company]
    inlist = ",".join(str(int(d)) for d in docentries)
    sql = """
SELECT h."DocEntry" AS DRAFT, h."DocTotal" AS AMOUNT, h."CardName" AS VENDOR,
       h."NumAtCard" AS VENDOR_BILL, u."USER_CODE" AS MADE_BY,
       i."DocNum" AS INV_DOCNUM, i."DocEntry" AS INV_DOCENTRY,
       (SELECT STRING_AGG(x.D, ' + ') FROM (
            SELECT DISTINCT COALESCE(NULLIF(l."Dscription",''), a."AcctName") AS D
            FROM {s}.DRF1 l
            LEFT JOIN {s}.OACT a ON a."AcctCode" = l."AcctCode"
            WHERE l."DocEntry" = h."DocEntry") x) AS WHAT_FOR,
       (SELECT SUM(w."WTAmnt") FROM {s}.DRF5 w WHERE w."AbsEntry" = h."DocEntry") AS TDS,
       (SELECT STRING_AGG(y.A, ',') FROM (
            SELECT DISTINCT l2."AcctCode" AS A FROM {s}.DRF1 l2
            WHERE l2."DocEntry" = h."DocEntry" AND l2."AcctCode" IS NOT NULL) y) AS ACCTS,
       (SELECT STRING_AGG(z.B, ',') FROM (
            SELECT DISTINCT COALESCE(l3."OcrCode3",'') AS B FROM {s}.DRF1 l3
            WHERE l3."DocEntry" = h."DocEntry") z) AS DIMS
FROM {s}.ODRF h
LEFT JOIN {s}.OUSR u ON u."USERID" = h."UserSign"
LEFT JOIN {s}.OPCH i ON i."draftKey" = h."DocEntry"
WHERE h."DocEntry" IN ({ids})
""".format(s=s, ids=inlist)
    return {int(r["DRAFT"]): r for r in hana(sql)}


def lane_of(row):
    """Re-derive the lane from the draft's own accounts + Budget dimension, so
    the log says WHY it was a direct post and not just that it was."""
    accts = [a for a in (row.get("ACCTS") or "").split(",") if a]
    dims = [d for d in (row.get("DIMS") or "").split(",") if d]
    lines = [{"acct": a, "budget_dim": (dims[0] if dims else ""), "acct_name": ""}
             for a in accts]
    if not lines:
        return "UNKNOWN"
    lane, _ = classify(lines)
    return lane


def posted_by(docentry):
    """Which SAP login actually pressed Add, from the shared write log."""
    who = None
    for lg in glob.glob(os.path.join(REPO, "queries", "*", "sap-writes.jsonl")):
        for ln in open(lg, errors="replace"):
            if "DraftsService_SaveDraftToDocument" not in ln:
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            pl = r.get("payload") or {}
            de = str((pl.get("Document") or {}).get("DocEntry", ""))
            if de == str(docentry) and r.get("event") == "outcome":
                who = r.get("user") or who
    return who or "unknown"


def write_rows(rows):
    os.makedirs(DESK, exist_ok=True)
    today = datetime.date.today().isoformat()
    month = today[:7]

    for path in (os.path.join(DESK, "%s.csv" % month),
                 os.path.join(DESK, "ALL-POSTS.csv")):
        new = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in FIELDS})

    md = os.path.join(DESK, "%s.md" % today)
    first = not os.path.exists(md)
    with open(md, "a") as f:
        if first:
            f.write("# Posted direct to SAP — %s\n\n" % today)
            f.write("Documents that went straight into the books. **None of "
                    "these needed JSAP approval.**\nA posted document cannot be "
                    "undone from the CLI — this file is the record.\n\n")
        for r in rows:
            f.write("## Draft %s → invoice %s\n\n" % (r["draft"], r["invoice_docnum"] or "NOT POSTED"))
            f.write("| | |\n|---|---|\n")
            f.write("| Vendor | %s |\n" % r["vendor"])
            f.write("| Their bill | %s |\n" % r["vendor_bill"])
            f.write("| For | %s |\n" % (r["what_for"] or "-"))
            f.write("| Amount | Rs %s |\n" % r["amount"])
            if r.get("tds"):
                f.write("| TDS | Rs %s |\n" % r["tds"])
            f.write("| Book | %s |\n" % r["book"])
            f.write("| Draft made by | %s%s |\n" % (
                r["draft_made_by"],
                "" if r["in_scope"] == "yes" else "  ** OUTSIDE THE FIVE DESKS **"))
            f.write("| Posted by login | %s |\n" % r["posted_by_login"])
            f.write("| Lane | %s |\n" % r["lane"])
            f.write("| Outcome | %s |\n" % r["outcome"])
            f.write("| Logged at | %s |\n\n" % r["when"])
    return md


def record(company, docentries):
    facts = draft_facts(company, docentries)
    rows, skipped = [], []
    now = datetime.datetime.now().isoformat(timespec="seconds")
    for de in docentries:
        f = facts.get(int(de))
        if not f:
            skipped.append((de, "not found in %s" % company))
            continue
        lane = lane_of(f)
        if lane == WAITS:
            # This log is for direct posts only, by instruction.
            skipped.append((de, "JSAP lane - not a direct post, not logged"))
            continue
        made = (f.get("MADE_BY") or "?").strip()
        rows.append({
            "when": now, "book": company,
            "draft": de,
            "invoice_docnum": (f.get("INV_DOCNUM") or "").strip(),
            "invoice_docentry": (f.get("INV_DOCENTRY") or "").strip(),
            "vendor": (f.get("VENDOR") or "").strip(),
            "vendor_bill": (f.get("VENDOR_BILL") or "").strip(),
            "what_for": (f.get("WHAT_FOR") or "").strip(),
            "amount": "{:,.2f}".format(float(f.get("AMOUNT") or 0)),
            "tds": _money(f.get("TDS")),
            "draft_made_by": made,
            "posted_by_login": posted_by(de),
            "lane": lane,
            "in_scope": "yes" if made in IN_SCOPE else "NO",
            "outcome": "POSTED" if (f.get("INV_DOCNUM") or "").strip() else "still a draft",
        })
    if rows:
        md = write_rows(rows)
        print("logged %d post(s) -> %s" % (len(rows), md))
        for r in rows:
            flag = "" if r["in_scope"] == "yes" else "   <-- OUTSIDE THE FIVE DESKS"
            print("   draft %-7s -> %-11s %-28s Rs %14s  by %s%s" % (
                r["draft"], r["invoice_docnum"] or "-", r["vendor"][:28],
                r["amount"], r["draft_made_by"], flag))
    for de, why in skipped:
        print("   skipped %s: %s" % (de, why))
    return rows


def backfill():
    """Rebuild the log from every add-draft in the shared write log."""
    seen = {}
    for lg in glob.glob(os.path.join(REPO, "queries", "*", "sap-writes.jsonl")):
        for ln in open(lg, errors="replace"):
            if "DraftsService_SaveDraftToDocument" not in ln:
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("event") != "outcome" or r.get("status") not in (200, 204):
                continue
            pl = r.get("payload") or {}
            de = (pl.get("Document") or {}).get("DocEntry")
            db = r.get("company_db")
            if de and db in BOOK:
                seen.setdefault(BOOK[db], set()).add(int(de))
    if not seen:
        print("no successful add-draft found in the write log")
        return
    for co, des in sorted(seen.items()):
        print("== %s: %d successful add-draft(s) in the write log" % (co, len(des)))
        record(co, sorted(des))


def main():
    ap = argparse.ArgumentParser(description="Desktop log of direct (non-JSAP) posts")
    ap.add_argument("--record", nargs="+", metavar="DOCENTRY")
    ap.add_argument("--company", default="oil", choices=sorted(COMPANY_DB))
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    if a.show:
        md = os.path.join(DESK, datetime.date.today().isoformat() + ".md")
        if not os.path.exists(md):
            return print("nothing logged today (%s)" % md)
        return print(open(md).read())
    if a.backfill:
        return backfill()
    if a.record:
        return record(a.company, a.record) and None
    ap.error("give --record, --backfill or --show")


if __name__ == "__main__":
    main()
