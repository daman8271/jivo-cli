#!/usr/bin/env python3
"""Attach each bilty page to every A/R invoice that bilty carried.

Addressed BY INVOICE NUMBER - the bilty's `B/L No.` names the invoices, so the
scan lands on the exact documents that rode on that truck.

This is the half that WORKS on a posted, closed invoice: linking an attachment
does not change U_BilltyNumber, so the write-once guard (1395114) never fires.
Even an invoice whose bilty number is stuck wrong can still receive the real
bilty page as evidence.

  python3 attach_scan.py mapping.json --pdf "<scan.pdf>"            # preview
  python3 attach_scan.py mapping.json --pdf "<scan.pdf>" --apply

mapping.json bilties need a "page" (1-based page in the scan holding that bilty).
Each invoice gets its OWN Attachments2 row - never share a row between documents.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import REPO as _REPO, sapb1 as _sapb1, hana_sql as _hana, load_env as _load_env

REPO = str(_REPO)
HANA = _hana()
SAPB1 = _sapb1()

def hana(sql):
    r = subprocess.run([HANA, sql], capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        sys.exit(f"HANA failed: {(r.stderr or r.stdout).strip()}")
    ls = [l for l in r.stdout.strip().split("\n") if l.strip()]
    if len(ls) < 2:
        return []
    h = ls[0].split("\t")
    return [dict(zip(h, l.split("\t"))) for l in ls[1:]]

def load_env(company):
    return _load_env(company)

def short(invs):
    """626070362,363,364,365,370 - the house filename convention."""
    invs = [str(i) for i in invs]
    out = [invs[0]]
    for i in invs[1:]:
        out.append(i[-3:] if i[:-3] == invs[0][:-3] else i)
    return ",".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapping"); ap.add_argument("--pdf", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    m = json.load(open(a.mapping)); company = m["company"]
    env = load_env(company)

    allinv = [i for b in m["bilties"] for i in b["invoices"]]
    rows = {int(r["DocNum"]): r for r in hana(
        f'SELECT "DocNum","DocEntry",IFNULL("AtcEntry",-1) AS ATC '
        f'FROM {company}.OINV WHERE "DocNum" IN ({",".join(map(str,allinv))})')}

    plan = []
    for b in m["bilties"]:
        if not b.get("page"):
            print(f"  SKIP GR {b['gr']} - no 'page' in mapping"); continue
        name = short(b["invoices"]) + ".pdf"
        for inv in b["invoices"]:
            r = rows.get(int(inv))
            if not r:
                print(f"  !!   {inv} not found"); continue
            if int(r["ATC"]) != -1:
                print(f"  HAS  {inv}  already has attachment row {r['ATC']} - left alone")
                continue
            plan.append((int(inv), int(r["DocEntry"]), b["page"], name, b["gr"]))

    print(f"\n{len(plan)} invoice(s) to attach:")
    for inv, de, pg, name, gr in plan:
        print(f"  {inv}  DocEntry {de:<6} GR {gr:<6} page {pg}  -> {name}")
    if not a.apply:
        print("\n(preview only - re-run with --apply)"); return
    if not plan:
        return

    tmp = tempfile.mkdtemp(prefix="bilty-")
    pages = {}
    for _, _, pg, _, _ in plan:
        if pg not in pages:
            p = os.path.join(tmp, f"p{pg}.pdf")
            subprocess.run(["pdfseparate", "-f", str(pg), "-l", str(pg), a.pdf, p], check=True)
            pages[pg] = p

    ok = fail = 0
    for inv, de, pg, name, gr in plan:
        # the uploaded file name is the file's own name, so give the page its
        # invoice-list name in a folder of its own
        d = tempfile.mkdtemp(dir=tmp)
        src = os.path.join(d, name)
        shutil.copyfile(pages[pg], src)
        # C-0090: sapb1 attach ticks Copy to Target Document on every line (and
        # the U_CHK/U_CHK2 stamp where the book has it), reads the row back, and
        # exits non-zero unless every line is tYES. No tick, no link.
        u = subprocess.run([SAPB1, "attach", src, "--company", company, "--yes", "--json"],
                           capture_output=True, text=True, env=env, cwd=REPO)
        if u.returncode != 0:
            print(f"  FAIL  {inv} attach (exit {u.returncode}): "
                  f"{(u.stderr or u.stdout).strip().splitlines()[-1][:160]}")
            fail += 1; continue
        ae = json.loads(u.stdout)["absoluteEntry"]
        p = subprocess.run([SAPB1, "patch", f"Invoices({de})", "--yes", "--data",
                            json.dumps({"AttachmentEntry": ae})],
                           capture_output=True, text=True, env=env, cwd=REPO)
        if p.returncode == 0:
            print(f"  OK    {inv}  GR {gr}  -> row {ae}  ({name})"); ok += 1
        else:
            print(f"  FAIL  {inv} link row {ae}: {(p.stderr or p.stdout).strip().splitlines()[-1][:120]}")
            fail += 1

    print(f"\n  {ok} attached, {fail} failed")

if __name__ == "__main__":
    main()
