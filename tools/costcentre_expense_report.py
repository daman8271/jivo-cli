#!/usr/bin/env python3
"""
Expense detail for one or more SAP B1 cost/profit centres over a date range.

Read-only. Shells out to the sapb1 CLI; never writes to SAP.

Why it works this way: the Service Layer has no standalone JournalEntryLines
entity and the CLI has no --expand, so we pull whole JournalEntries as JSON
(child lines come back inline as long as we don't pass --select) and do the
cost-centre filtering, grouping and totalling locally.

Usage:
  python tools/costcentre_expense_report.py --centres NPD1,NPD2 \
      --from 2026-04-01 --to 2026-07-31 [--company JIVO_OIL_HANADB]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
KIT = os.path.join(REPO, "sap-b1", "accounts-kit")
EXE = os.path.join(KIT, "sapb1.exe" if os.name == "nt" else "sapb1")
if not os.path.exists(EXE):
    EXE = os.path.join(REPO, "sap-b1", "cli", "sapb1")

# JE line fields that can carry a cost centre (dimensions 1-5)
DIM_FIELDS = ["CostingCode", "CostingCode2", "CostingCode3", "CostingCode4", "CostingCode5"]


def sap(entity, company=None, **opts):
    """Run `sapb1 query <entity> ... --json --all` and return the rows list."""
    cmd = [EXE, "query", entity, "--json", "--all", "--page-size", "200"]
    for key, val in opts.items():
        if val is not None:
            cmd += ["--" + key.replace("_", "-"), str(val)]
    if company:
        cmd += ["--company", company]
    res = subprocess.run(cmd, cwd=KIT, capture_output=True, text=True)
    if res.returncode != 0:
        err = (res.stderr or res.stdout).strip()
        sys.exit("\n[sapb1 failed] " + entity + "\n" + err + "\n")
    rows = []
    dec = json.JSONDecoder()
    buf, i = res.stdout, 0
    while i < len(buf):  # --all can emit one JSON doc per page
        while i < len(buf) and buf[i] in " \r\n\t":
            i += 1
        if i >= len(buf):
            break
        obj, i = dec.raw_decode(buf, i)
        rows += obj.get("value", []) if isinstance(obj, dict) else obj
    return rows


def inr(amount):
    """Indian-grouped money, 2dp, negatives parenthesised."""
    text = "{:.2f}".format(abs(amount))
    whole, frac = text.split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        whole = head + "," + tail
    out = whole + "." + frac
    return "(" + out + ")" if amount < 0 else out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--centres", required=True, help="comma-separated codes, e.g. NPD1,NPD2")
    ap.add_argument("--from", dest="dfrom", required=True)
    ap.add_argument("--to", dest="dto", required=True)
    ap.add_argument("--company", default=None)
    ap.add_argument("--out", default=None, help="write matched lines to this CSV")
    args = ap.parse_args()

    wanted_raw = [c.strip() for c in args.centres.split(",") if c.strip()]
    wanted = set(c.upper() for c in wanted_raw)
    co = args.company or "JIVO_OIL_HANADB"

    # 1. resolve the cost centres so we report real names, not just codes
    print("Resolving cost centres in " + co + " ...")
    centres = sap("ProfitCenters", company=args.company,
                  select="CenterCode,CenterName,InWhichDimension,Active")
    hit = [c for c in centres
           if (c.get("CenterCode") or "").upper() in wanted
           or any(w in (c.get("CenterName") or "").upper() for w in wanted)]
    if not hit:
        print("  !! none of " + str(wanted_raw) + " found among "
              + str(len(centres)) + " centres.")
        near = [c for c in centres
                if "NPD" in ((c.get("CenterCode") or "") + (c.get("CenterName") or "")).upper()]
        if near:
            print("  Closest NPD-ish matches:")
            for c in near:
                print("    {!r:12} {!r} dim={} active={}".format(
                    c.get("CenterCode"), c.get("CenterName"),
                    c.get("InWhichDimension"), c.get("Active")))
        else:
            print("  No centre contains 'NPD'. First 25 codes, so you can spot the real naming:")
            for c in centres[:25]:
                print("    {!r:12} {!r} dim={}".format(
                    c.get("CenterCode"), c.get("CenterName"), c.get("InWhichDimension")))
        sys.exit(1)
    codes = set((c.get("CenterCode") or "").upper() for c in hit)
    for c in hit:
        print("  [ok] {:12} {}  (dimension {}, active={})".format(
            c.get("CenterCode"), c.get("CenterName"),
            c.get("InWhichDimension"), c.get("Active")))

    # 2. G/L account names, for readable output
    print("Fetching chart of accounts ...")
    coa = {}
    for r in sap("ChartOfAccounts", company=args.company, select="Code,Name"):
        coa[r.get("Code")] = r.get("Name")

    # 3. journal entries in the window (no --select: keeps JournalEntryLines inline)
    flt = "ReferenceDate ge '" + args.dfrom + "' and ReferenceDate le '" + args.dto + "'"
    print("Fetching journal entries " + args.dfrom + " .. " + args.dto + " (slow part) ...")
    jes = sap("JournalEntries", company=args.company, filter=flt, orderby="ReferenceDate")
    print("  {:,} journal entries in range".format(len(jes)))

    # 4. keep only lines tagged to our centres
    matched = []
    for je in jes:
        for ln in je.get("JournalEntryLines") or []:
            tag = None
            for f in DIM_FIELDS:
                v = (ln.get(f) or "").upper()
                if v in codes:
                    tag = v
                    break
            if not tag:
                continue
            dr = float(ln.get("Debit") or 0)
            cr = float(ln.get("Credit") or 0)
            matched.append({
                "centre": tag,
                "date": (je.get("ReferenceDate") or "")[:10],
                "jdt": je.get("JdtNum"),
                "account": ln.get("AccountCode"),
                "acctname": coa.get(ln.get("AccountCode"), ""),
                "memo": ln.get("LineMemo") or je.get("Memo") or "",
                "bp": ln.get("ShortName") or "",
                "ref": je.get("Reference") or "",
                "debit": dr,
                "credit": cr,
                "net": dr - cr,
            })
    if not matched:
        sys.exit("\nNo journal lines tagged to " + str(sorted(codes)) + " between "
                 + args.dfrom + " and " + args.dto + ".\n"
                 "(Centres exist, so either nothing was booked to them in this window, "
                 "or the spend is tagged on a different dimension field.)\n")

    total = sum(m["net"] for m in matched)
    print("\n" + "=" * 78)
    print("COST-CENTRE EXPENSE DETAIL  " + args.dfrom + " .. " + args.dto + "   [" + co + "]")
    print("=" * 78)
    print("{:,} tagged journal lines   NET DEBIT (expense) = INR {}\n".format(len(matched), inr(total)))

    # by centre
    print("--- By cost centre " + "-" * 59)
    for c in sorted(codes):
        rows = [m for m in matched if m["centre"] == c]
        if not rows:
            continue
        nm = next((h.get("CenterName") or "" for h in hit
                   if (h.get("CenterCode") or "").upper() == c), "")
        print("  {:10} {:34} {:5,} lines  INR {:>18}".format(
            c, nm[:34], len(rows), inr(sum(r["net"] for r in rows))))

    # by month x centre
    print("\n--- By month " + "-" * 65)
    months = sorted(set(m["date"][:7] for m in matched))
    hdr = "  " + "month".ljust(10) + "".join(c.rjust(20) for c in sorted(codes)) + "TOTAL".rjust(20)
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for mo in months:
        line = "  " + mo.ljust(10)
        for c in sorted(codes):
            line += inr(sum(m["net"] for m in matched
                            if m["date"][:7] == mo and m["centre"] == c)).rjust(20)
        line += inr(sum(m["net"] for m in matched if m["date"][:7] == mo)).rjust(20)
        print(line)

    # by account
    print("\n--- By G/L account " + "-" * 59)
    byacc = defaultdict(float)
    cnt = defaultdict(int)
    for m in matched:
        byacc[(m["account"], m["acctname"])] += m["net"]
        cnt[(m["account"], m["acctname"])] += 1
    for (code, name), amt in sorted(byacc.items(), key=lambda kv: -abs(kv[1])):
        print("  {:14} {:40} {:4} ln  INR {:>18}".format(
            str(code), str(name)[:40], cnt[(code, name)], inr(amt)))

    # line detail
    print("\n--- Line detail " + "-" * 62)
    print("  {:11}{:8}{:8}{:14}{:40}{:>16}".format(
        "date", "centre", "JE", "account", "narration", "amount"))
    for m in sorted(matched, key=lambda x: (x["date"], x["jdt"] or 0)):
        narr = (m["memo"] or m["bp"] or m["ref"])[:38]
        print("  {:11}{:8}{:8}{:14}{:40}{:>16}".format(
            m["date"], m["centre"], str(m["jdt"]), str(m["account"]), narr, inr(m["net"])))
    print("\n  {:>81} INR {}".format("TOTAL", inr(total)))

    # 5. budget vs actual, if these accounts are budgeted
    buds = sap("Budgets", company=args.company,
               select="AccountCode,BudgetScenario,StartofFiscalYear,TotalAnnualBudgetDebitLoc")
    accs = set(c for c, _ in byacc)
    rel = [b for b in buds if b.get("AccountCode") in accs]
    if rel:
        print("\n--- Annual budget on these accounts " + "-" * 42)
        for b in rel:
            ann = float(b.get("TotalAnnualBudgetDebitLoc") or 0)
            act = sum(v for (c, _), v in byacc.items() if c == b.get("AccountCode"))
            pct = "{:.1f}%".format(act / ann * 100) if ann else "n/a"
            print("  {:14} {:30} budget {:>16}  actual {:>16}  used {:>7}  (scenario {}, FY {})".format(
                b.get("AccountCode"), str(coa.get(b.get("AccountCode"), ""))[:30],
                inr(ann), inr(act), pct, b.get("BudgetScenario"),
                str(b.get("StartofFiscalYear"))[:10]))

    if args.out:
        import csv
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(matched[0].keys()))
            w.writeheader()
            w.writerows(matched)
        print("\nMatched lines written to " + args.out)


if __name__ == "__main__":
    main()
