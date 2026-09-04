#!/usr/bin/env python3
"""Mark an A/R invoice RECEIVED: received qty on every line + received date.

JIVO's receiving workflow, enforced by SBO_SP_TransactionNotification:

  130001002  "Please Attach its Receiving" - U_Recv_Date cannot be set unless
             the invoice already has an attachment (AtcEntry). ATTACH FIRST.
  1300013    "Please update the received qty" - with U_Recv_Date set, EVERY
             line must carry a non-zero U_Recvd_Qty.
  1300014    U_Recv_Date must not be earlier than DocDate.

So this sends one PATCH per invoice carrying the date and all lines together -
the guards test the final state, so a partial write is refused.

  python3 receive.py --invoices 626070363,626070364        # preview
  python3 receive.py --invoices ... --apply
  python3 receive.py --from-mapping mapping.json --apply
  python3 receive.py --invoices ... --date 2026-09-04 --apply   # default: today
"""
import argparse, datetime, json, os, subprocess, sys

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invoices"); ap.add_argument("--from-mapping")
    ap.add_argument("--company", default="JIVO_OIL_HANADB")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    nums = []
    if a.from_mapping:
        m = json.load(open(a.from_mapping))
        a.company = m.get("company", a.company)
        nums = [int(i) for b in m["bilties"] for i in b["invoices"]]
    if a.invoices:
        nums += [int(x) for x in a.invoices.replace(" ", "").split(",") if x]
    if not nums:
        sys.exit("give --invoices or --from-mapping")
    nums = sorted(set(nums))
    company = a.company

    rows = hana(
        f'SELECT i."DocNum",i."DocEntry",l."LineNum",TO_VARCHAR(l."Quantity") AS QTY,'
        f'TO_VARCHAR(IFNULL(l."U_Recvd_Qty",0)) AS RECVD,'
        f'TO_VARCHAR(i."U_Recv_Date",\'YYYY-MM-DD\') AS RECVDATE,'
        f'IFNULL(i."AtcEntry",-1) AS ATC,TO_VARCHAR(i."DocDate",\'YYYY-MM-DD\') AS DOCDATE,'
        f'i."CANCELED" '
        f'FROM {company}.OINV i JOIN {company}.INV1 l ON l."DocEntry"=i."DocEntry" '
        f'WHERE i."DocNum" IN ({",".join(map(str,nums))}) ORDER BY i."DocNum",l."LineNum"')

    inv = {}
    for r in rows:
        inv.setdefault(int(r["DocNum"]), {"de": int(r["DocEntry"]), "atc": int(r["ATC"]),
                                          "recv": r["RECVDATE"], "docdate": r["DOCDATE"],
                                          "cancelled": r["CANCELED"], "lines": []})
        inv[int(r["DocNum"])]["lines"].append(
            (int(r["LineNum"]), float(r["QTY"]), float(r["RECVD"])))

    todo, skip = [], []
    for n in nums:
        d = inv.get(n)
        if not d:
            skip.append((n, "not found in " + company)); continue
        if d["cancelled"] != "N":
            skip.append((n, "cancelled")); continue
        if d["atc"] == -1:
            skip.append((n, "NO ATTACHMENT - guard 130001002 will refuse; attach first"))
            continue
        if a.date < d["docdate"]:
            skip.append((n, f"date {a.date} is before DocDate {d['docdate']} - guard 1300014"))
            continue
        if d["recv"] not in (None, "", "NULL") and all(r > 0 for _, _, r in d["lines"]):
            skip.append((n, f"already received on {d['recv']}")); continue
        todo.append((n, d))

    print(f"=== {'APPLY' if a.apply else 'PREVIEW'} - {company} | recv date {a.date} ===\n")
    for n, why in skip:
        print(f"  SKIP  {n}  {why}")
    print()
    for n, d in todo:
        ls = ", ".join(f"line {ln}: {q:g}" for ln, q, _ in d["lines"])
        print(f"  RECV  {n}  DocEntry {d['de']:<6} atc {d['atc']:<7} {ls}")
    print(f"\n  {len(todo)} to receive, {len(skip)} skipped")
    if not a.apply:
        print("\n(preview only - re-run with --apply)"); return
    if not todo:
        return

    env = load_env(company)
    ok = fail = 0
    for n, d in todo:
        payload = {"U_Recv_Date": a.date,
                   "DocumentLines": [{"LineNum": ln, "U_Recvd_Qty": q}
                                     for ln, q, _ in d["lines"]]}
        r = subprocess.run([SAPB1, "patch", f"Invoices({d['de']})", "--yes",
                            "--data", json.dumps(payload)],
                           capture_output=True, text=True, env=env, cwd=REPO)
        if r.returncode == 0:
            print(f"  OK    {n}  {len(d['lines'])} line(s) received"); ok += 1
        else:
            print(f"  FAIL  {n}  {(r.stderr or r.stdout).strip().splitlines()[-1][:130]}")
            fail += 1
    print(f"\n  {ok} received, {fail} failed")

if __name__ == "__main__":
    main()
