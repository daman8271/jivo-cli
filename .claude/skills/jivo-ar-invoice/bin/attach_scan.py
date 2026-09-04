#!/usr/bin/env python3
"""Attach each bilty page to every A/R invoice that bilty carried.

Addressed BY INVOICE NUMBER — the bilty's `B/L No.` names the invoices, so the
scan lands on the exact documents that rode on that truck.

This is the half that WORKS on a posted, closed invoice: linking an attachment
does not change U_BilltyNumber, so the write-once guard (1395114) never fires.
Even an invoice whose bilty number is stuck wrong can still receive the real
bilty page as evidence.

  python3 attach_scan.py mapping.json --pdf "<scan.pdf>"            # preview
  python3 attach_scan.py mapping.json --pdf "<scan.pdf>" --apply

mapping.json bilties need a "page" (1-based page in the scan holding that bilty).
Each invoice gets its OWN Attachments2 row — never share a row between documents.
"""
import argparse, json, os, subprocess, sys, tempfile

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

def load_env(company):
    env = dict(os.environ)
    for line in open(os.path.join(REPO, ENVS[company])):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env

def short(invs):
    """626070362,363,364,365,370 — the house filename convention."""
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
    host, port = env["SAPB1_HOST"], env["SAPB1_PORT"]
    H = f"https://{host}:{port}"

    allinv = [i for b in m["bilties"] for i in b["invoices"]]
    rows = {int(r["DocNum"]): r for r in hana(
        f'SELECT "DocNum","DocEntry",IFNULL("AtcEntry",-1) AS ATC '
        f'FROM {company}.OINV WHERE "DocNum" IN ({",".join(map(str,allinv))})')}

    plan = []
    for b in m["bilties"]:
        if not b.get("page"):
            print(f"  SKIP GR {b['gr']} — no 'page' in mapping"); continue
        name = short(b["invoices"]) + ".pdf"
        for inv in b["invoices"]:
            r = rows.get(int(inv))
            if not r:
                print(f"  !!   {inv} not found"); continue
            if int(r["ATC"]) != -1:
                print(f"  HAS  {inv}  already has attachment row {r['ATC']} — left alone")
                continue
            plan.append((int(inv), int(r["DocEntry"]), b["page"], name, b["gr"]))

    print(f"\n{len(plan)} invoice(s) to attach:")
    for inv, de, pg, name, gr in plan:
        print(f"  {inv}  DocEntry {de:<6} GR {gr:<6} page {pg}  -> {name}")
    if not a.apply:
        print("\n(preview only — re-run with --apply)"); return
    if not plan:
        return

    tmp = tempfile.mkdtemp(prefix="bilty-")
    ck = os.path.join(tmp, "ck")
    login = json.dumps({"CompanyDB": company, "UserName": env["SAPB1_USER"],
                        "Password": env["SAPB1_PASSWORD"]})
    lf = os.path.join(tmp, "l.json"); open(lf, "w").write(login)
    rc = subprocess.run(["curl", "-sk", "-c", ck, "-H", "Content-Type: application/json",
                         "--data-binary", f"@{lf}", f"{H}/b1s/v1/Login",
                         "-o", os.path.join(tmp, "lr.json"), "-w", "%{http_code}"],
                        capture_output=True, text=True)
    os.remove(lf)
    if rc.stdout.strip() != "200":
        sys.exit(f"login failed: {rc.stdout}")

    pages = {}
    for _, _, pg, _, _ in plan:
        if pg not in pages:
            p = os.path.join(tmp, f"p{pg}.pdf")
            subprocess.run(["pdfseparate", "-f", str(pg), "-l", str(pg), a.pdf, p], check=True)
            pages[pg] = p

    ok = fail = 0
    for inv, de, pg, name, gr in plan:
        src = pages[pg]; kb = round(os.path.getsize(src) / 1024)
        up = os.path.join(tmp, "up.json")
        # commas in the name break curl -F (treated as a file separator) — quote it
        r = subprocess.run(["curl", "-sSk", "--http1.1", "-H", "Expect:", "-b", ck,
                            "-X", "POST", f"{H}/b1s/v1/Attachments2",
                            "-F", f'files=@"{src}";type=application/pdf;filename="{name}"',
                            "-o", up, "-w", "%{http_code}"], capture_output=True, text=True)
        if r.stdout.strip() != "201":
            print(f"  FAIL  {inv} upload {r.stdout.strip()} {r.stderr.strip()[:100]}")
            fail += 1; continue
        ae = json.load(open(up))["AbsoluteEntry"]
        subprocess.run([SAPB1, "patch", f"Attachments2({ae})", "--yes", "--data",
                        json.dumps({"Attachments2_Lines": [
                            {"AbsoluteEntry": ae, "LineNum": 1, "U_CHK": kb, "U_CHK2": "OK"}]})],
                       capture_output=True, text=True, env=env, cwd=REPO)
        p = subprocess.run([SAPB1, "patch", f"Invoices({de})", "--yes", "--data",
                            json.dumps({"AttachmentEntry": ae})],
                           capture_output=True, text=True, env=env, cwd=REPO)
        if p.returncode == 0:
            print(f"  OK    {inv}  GR {gr}  -> row {ae}  ({name})"); ok += 1
        else:
            print(f"  FAIL  {inv} link {(p.stderr or p.stdout).strip().splitlines()[-1][:120]}")
            fail += 1

    subprocess.run(["curl", "-sk", "-b", ck, "-X", "POST", f"{H}/b1s/v1/Logout"],
                   capture_output=True)
    print(f"\n  {ok} attached, {fail} failed")

if __name__ == "__main__":
    main()
