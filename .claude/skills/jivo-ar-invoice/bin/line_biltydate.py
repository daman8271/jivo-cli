#!/usr/bin/env python3
"""Copy the header bilty date down onto every invoice LINE.

`U_BiltyDate` exists TWICE: on OINV (the header box under Billty Number) and on
INV1 (the `BiltyDate` column in the item grid). A hand-keyed invoice carries the
same date in both. Filling only the header leaves the grid column blank, which is
what the operator actually looks at.

  python3 line_biltydate.py --invoices 626070362,626070363        # preview
  python3 line_biltydate.py --from-mapping mapping.json --apply
"""
import argparse, json, os, subprocess, sys

REPO = os.environ.get("JIVO_REPO", "/Users/damanpreetsingh/jivo-cli")
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
SAPB1 = os.path.join(REPO, "sap-b1", "cli", "sapb1")
ENVS = {"JIVO_OIL_HANADB": "sap-b1/cli/user19-oil.env",
        "JIVO_MART_HANADB": "sap-b1/cli/user19-mart.env",
        "JIVO_BEVERAGES_HANADB": "sap-b1/cli/user19-bev.env"}

def hana(sql):
    r = subprocess.run([HANA, sql], capture_output=True, text=True, cwd=REPO)
    if r.returncode:
        sys.exit(f"HANA failed: {(r.stderr or r.stdout).strip()}")
    ls = [l for l in r.stdout.strip().split("\n") if l.strip()]
    if len(ls) < 2:
        return []
    h = ls[0].split("\t")
    return [dict(zip(h, l.split("\t"))) for l in ls[1:]]

def load_env(c):
    env = dict(os.environ)
    for line in open(os.path.join(REPO, ENVS[c])):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); env[k] = v
    return env

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--invoices"); ap.add_argument("--from-mapping")
    ap.add_argument("--company", default="JIVO_OIL_HANADB")
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
    nums = sorted(set(nums)); c = a.company

    rows = hana(
        f'SELECT i."DocNum",i."DocEntry",l."LineNum",'
        f'TO_VARCHAR(i."U_BiltyDate",\'YYYY-MM-DD\') AS HDR,'
        f'CASE WHEN l."U_BiltyDate" IS NULL THEN \'@NULL@\' '
        f'ELSE TO_VARCHAR(l."U_BiltyDate",\'YYYY-MM-DD\') END AS LN '
        f'FROM {c}.OINV i JOIN {c}.INV1 l ON l."DocEntry"=i."DocEntry" '
        f'WHERE i."DocNum" IN ({",".join(map(str,nums))}) AND i."CANCELED"=\'N\' '
        f'ORDER BY i."DocNum",l."LineNum"')

    inv = {}
    for r in rows:
        n = int(r["DocNum"])
        inv.setdefault(n, {"de": int(r["DocEntry"]), "hdr": r["HDR"], "lines": []})
        inv[n]["lines"].append((int(r["LineNum"]), r["LN"]))

    todo, skip = [], []
    for n, d in inv.items():
        if d["hdr"] in (None, "", "NULL"):
            skip.append((n, "header U_BiltyDate is empty — nothing to copy down")); continue
        need = [ln for ln, cur in d["lines"] if cur == "@NULL@"]
        if not need:
            skip.append((n, "every line already has it")); continue
        todo.append((n, d["de"], d["hdr"], need))

    print(f"=== {'APPLY' if a.apply else 'PREVIEW'} — {c} ===\n")
    for n, why in skip:
        print(f"  SKIP  {n}  {why}")
    print()
    for n, de, hdr, need in todo:
        print(f"  SET   {n}  DocEntry {de:<6} BiltyDate {hdr} on line(s) "
              f"{', '.join(map(str,need))}")
    print(f"\n  {len(todo)} invoice(s), {sum(len(t[3]) for t in todo)} line(s)")
    if not a.apply:
        print("\n(preview only — re-run with --apply)"); return
    if not todo:
        return

    env = load_env(c); ok = fail = 0
    for n, de, hdr, need in todo:
        payload = {"DocumentLines": [{"LineNum": ln, "U_BiltyDate": hdr} for ln in need]}
        r = subprocess.run([SAPB1, "patch", f"Invoices({de})", "--yes",
                            "--data", json.dumps(payload)],
                           capture_output=True, text=True, env=env, cwd=REPO)
        if r.returncode == 0:
            print(f"  OK    {n}  {len(need)} line(s) -> {hdr}"); ok += 1
        else:
            print(f"  FAIL  {n}  {(r.stderr or r.stdout).strip().splitlines()[-1][:130]}")
            fail += 1
    print(f"\n  {ok} done, {fail} failed")

if __name__ == "__main__":
    main()
