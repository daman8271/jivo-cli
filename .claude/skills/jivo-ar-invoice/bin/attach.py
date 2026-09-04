#!/usr/bin/env python3
"""Attach bilty (G.R.) numbers to A/R invoices — addressed BY INVOICE NUMBER.

The bilty paper is the source (C-0038). Its `B/L No.` field names the JIVO sale
invoice numbers it carried, and the transporter's consolidated bill repeats the
same thing as a GR.NO -> INVOICE NO. table. So the match key is the INVOICE
NUMBER; the G.R. number is the value being written.

THE ONE RULE THAT MATTERS — OINV.U_BilltyNumber IS WRITE-ONCE.
SAP's SBO_SP_TransactionNotification refuses any change once a value exists:
    [SAP -1116] (1395114) Cannot change the Bilty No once updated
There is no override, from this CLI or from the SAP B1 client. So this tool
REFUSES to touch an invoice that already carries a number, and only ever fills
a NULL. A wrong number is permanent — never guess a clipped digit.

    python3 attach.py mapping.json                 # preview (default)
    python3 attach.py mapping.json --apply         # send
    python3 attach.py mapping.json --only 626070520

mapping.json:
  {"company":"JIVO_OIL_HANADB",
   "transporter":"Mahaveer Transport",
   "bilties":[{"gr":"3684","date":"2026-07-15",
               "invoices":[626070362,626070363],"paper":"page5 bilty + bill"}]}
"""
import argparse, json, os, subprocess, sys

REPO = os.environ.get("JIVO_REPO", "/Users/damanpreetsingh/jivo-cli")
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
SAPB1 = os.path.join(REPO, "sap-b1", "cli", "sapb1")
ENVS = {  # company -> env file holding that book's login
    "JIVO_OIL_HANADB":       "sap-b1/cli/user19-oil.env",
    "JIVO_MART_HANADB":      "sap-b1/cli/user19-mart.env",
    "JIVO_BEVERAGES_HANADB": "sap-b1/cli/user19-bev.env",
}

def hana(sql):
    r = subprocess.run([HANA, sql], capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        sys.exit(f"HANA read failed: {(r.stderr or r.stdout).strip()}")
    lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return []
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]

def load_env(company):
    path = os.path.join(REPO, ENVS[company])
    if not os.path.exists(path):
        sys.exit(f"no login file for {company}: {path}")
    env = dict(os.environ)
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env

def fetch(company, nums):
    return {int(r["DocNum"]): r for r in hana(
        f'SELECT "DocNum","DocEntry","CardName","CANCELED",'
        f'CASE WHEN "U_BilltyNumber" IS NULL THEN \'@NULL@\' '
        f'ELSE TRIM("U_BilltyNumber") END AS CUR,'
        f'CASE WHEN "U_BiltyDate" IS NULL THEN \'@NULL@\' '
        f'ELSE TO_VARCHAR("U_BiltyDate",\'YYYY-MM-DD\') END AS CURDT '
        f'FROM {company}.OINV WHERE "DocNum" IN ({",".join(map(str,sorted(nums)))})')}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapping")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", type=int, action="append")
    a = ap.parse_args()

    m = json.load(open(a.mapping))
    company = m["company"]
    if company not in ENVS:
        sys.exit(f"unknown company {company}")

    want = {}
    for b in m["bilties"]:
        gr = str(b["gr"]).strip()
        if not gr:
            sys.exit("empty G.R. number in mapping — never write a guess")
        dt = str(b.get("date", "")).strip()   # the Date box next to G.R. No.
        for inv in b["invoices"]:
            want[int(inv)] = (gr, dt)
    if a.only:
        want = {k: v for k, v in want.items() if k in set(a.only)}
    if not want:
        sys.exit("nothing selected")

    found = fetch(company, want)
    todo, locked, ok_already, missing, cancelled = [], [], [], [], []
    for inv in sorted(want):
        r = found.get(inv)
        if not r:
            missing.append(inv); continue
        if r["CANCELED"] != "N":
            cancelled.append(inv); continue
        gr, dt = want[inv]
        cur, curdt = r["CUR"], r["CURDT"]
        fields = {}
        if cur == "@NULL@":
            fields["U_BilltyNumber"] = gr
        if curdt == "@NULL@" and dt:
            fields["U_BiltyDate"] = dt
        if fields:
            todo.append((inv, int(r["DocEntry"]), fields, r["CardName"], cur, curdt))
        elif cur == gr:
            ok_already.append((inv, cur))
        else:
            locked.append((inv, cur, gr))

    print(f"=== {'APPLY' if a.apply else 'PREVIEW'} — {company} ===\n")
    for inv, cur in ok_already:
        print(f"  OK ALREADY  {inv}  has {cur}")
    for inv in cancelled:
        print(f"  CANCELLED   {inv}  skipped")
    for inv in missing:
        print(f"  NOT FOUND   {inv}  not in {company} — check the other two books (C-0073)")
    for inv, cur, new in locked:
        print(f"  LOCKED      {inv}  has {cur}, paper says {new} — WRITE-ONCE, cannot change")
    if locked:
        print("\n  ^ these need the SAP partner at DB level, or cancel-and-reissue.")
    print()
    for inv, de, fields, name, cur, curdt in todo:
        bits = " · ".join(f"{k.replace('U_','')} NULL -> {v}" for k, v in fields.items())
        note = "" if cur == "@NULL@" else f"  (number stays {cur}, locked)"
        print(f"  FILL        {inv}  DocEntry {de:<6} {bits}{note}  {name[:28]}")
    print(f"\n  {len(todo)} to fill · {len(locked)} locked · {len(ok_already)} already correct "
          f"· {len(cancelled)} cancelled · {len(missing)} missing")

    if not a.apply:
        print("\n(preview only — re-run with --apply)")
        return
    if not todo:
        print("\nnothing to write.")
        return

    env = load_env(company)
    done = []
    for inv, de, fields, name, cur, curdt in todo:
        r = subprocess.run(
            [SAPB1, "patch", f"Invoices({de})", "--yes", "--data", json.dumps(fields)],
            capture_output=True, text=True, env=env, cwd=REPO)
        if r.returncode == 0:
            print(f"  SENT  {inv} -> {fields}"); done.append(inv)
        else:
            print(f"  FAIL  {inv} rc={r.returncode} "
                  f"{(r.stderr or r.stdout).strip().splitlines()[-1][:140]}")

    if done:  # read back — never trust a 204
        print("\n  read-back:")
        back = fetch(company, done)
        bad = 0
        for inv in done:
            got = back[inv]["CUR"]
            got = "" if got == "@NULL@" else got
            mark = "ok " if got == want[inv][0] else "BAD"
            if mark == "BAD":
                bad += 1
            print(f"    {mark} {inv}  SAP now holds {got or '(still null)'}")
        print(f"\n  {len(done)-bad} verified, {bad} did not stick")

if __name__ == "__main__":
    main()
