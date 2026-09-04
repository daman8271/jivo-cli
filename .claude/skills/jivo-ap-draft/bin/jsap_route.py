#!/usr/bin/env python3
"""jsap_route — will this document WAIT in JSAP, or can it be POSTED NOW?

After Bhawani approves a draft it comes back to Accounts, and from there it
takes one of two lanes:

  POST NOW     — the ledger is made and the document is saved/posted in SAP.
  WAITS IN JSAP — it first needs the above-office BUDGET approval in JSAP.

Today nobody knows which lane a draft is in until it has already gone, so the
whole pile is held back for the slowest document. This tells you at draft time.

THE RULE (derived from live data 2026-09-04, see reference/jsap-routing.md)
--------------------------------------------------------------------------
A document goes to JSAP if **any single line** is budget-controlled, i.e.

    the line carries a Budget dimension (SAP dim-3 / CostingCode3 / OcrCode3)
    AND its GL account is not a stock, fixed-asset or direct-cost account.

Everything else is posted directly. Concretely:

  * RM / PM bought against a GRPO hits 2140001 GOODS RECEIVED BUT NOT INVOICED
    -> POST NOW. 893 of 893 such Oil drafts this FY went direct; not one
    reached JSAP.
  * Service and expense bills hit a 56xxxxx indirect-expense account with a
    Budget dimension -> WAITS IN JSAP (freight outward, repairs, refreshment,
    conveyance, rent, housekeeping, printing, legal...).
  * Fixed assets (12xxxxx, 2140002), job work, import freight, inward freight
    and lab testing carry a Budget dimension but are NOT budget-controlled
    -> POST NOW.
  * JIVO MART never entered the budget process at all -> always POST NOW.

Measured on resolved Oil drafts Apr-Jul 2026 (n=2136): 95.6% accurate, and the
POST NOW call was right 857 times out of 857 -- it has never once mislabelled a
document that then went to JSAP. Applied unchanged to Beverages (n=519) it is
87.7% accurate with, again, zero POST NOW misses. So a POST NOW here is safe to
act on; a WAITS IN JSAP is right ~93% of the time and errs toward waiting.

Read-only. Touches SAP HANA (SELECT) and, only for --refit, the JSAP database.

USAGE
  # one or more existing drafts
  jsap_route.py 55813 55906 --company oil

  # the whole pile still sitting as drafts
  jsap_route.py --pending --company oil

  # before you even send it: classify the payload the A/P skills built
  jsap_route.py --payload /tmp/ap-draft.json --company oil

  # re-derive the account table from live JSAP + SAP history
  jsap_route.py --refit
"""
import argparse
import csv
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

SCHEMA = {
    "oil": "JIVO_OIL_HANADB",
    "mart": "JIVO_MART_HANADB",
    "bev": "JIVO_BEVERAGES_HANADB",
}
# JSAP's budget register only ever carried these two books.
JSAP_BRANCH = {"oil": "OIL", "bev": "BEVERAGE"}

# GL accounts that carry a Budget dimension but are NOT budget-controlled: a
# line on one of these never sends a document to JSAP. Derived from Oil
# FY26-27 (>=5 drafts on the account, none of them ever in JSAP) and validated
# on held-out months and on Beverages. Regenerate with --refit.
NEVER_JSAP = {
    "2140001": "GOODS RECEIVED BUT NOT INVOICED",          # 893 drafts - RM/PM via GRPO
    "1212013": "BUILDINGS WIP CONSTRUCTION -NEW BUILDING",  # 30
    "1212015": "WIP TIN SHED (NEW 50KL TANK)",              # 7
    "1212016": "PEB SHED NEW LAND 2 ACRE",                  # 67
    "1213006": "TANK 50 KL - NEW ( FA0000024)",             # 7
    "5100002": "FREIGHT INWARD CHARGES-DIRECT",             # 24
    "5100009": "JOB WORK",                                  # 11
    "5100016": "PLATE & DIE CHARGES",                       # 7
    "5100018": "LAB & TESTING DIRECT EXPENSE",              # 16
    "5200003": "TAXES/DUTIES/FSSAI AND FEES IMPORT",        # 7
    "5200010": "PROFESSIONAL CHARGES IMPORT",               # 5
    "5500001": "FREIGHT EXPENSE-IMPORT",                    # 15
    "5500003": "JOB WORK FOR REFINING",                     # 44
    "5500005": "FREIGHT EXP - FIXED ASSETS",                # 6
}
# NOT in the list on purpose: 2140002 FIXED ASSETS RECEIVED BUT NOT INVOICED.
# One mixed bill (draft 51537, Shrichand Computers) carried a fixed-asset line
# AND a 5680022 COMPUTER AND HARDWARE line, and it did go to JSAP. The test is
# therefore per LINE, never "this document contains a never-account".
GRNI = "2140001"

POST_NOW = "POST NOW"
WAITS = "WAITS IN JSAP"


def binary(folder, stem):
    """Pick the build for THIS machine.

    The repo ships one binary per OS side by side -- `sapb1` (darwin),
    `sapb1.linux`, `sapb1.exe`. Hardcoding the bare name works on the Mac and
    then dies on an operator's Windows desk with a format error, which is how
    the fleet has been bitten before (dsr, hana-sql). Resolve it instead."""
    if sys.platform == "win32":
        names = [stem + ".exe", stem]
    elif sys.platform == "darwin":
        names = [stem, stem + ".darwin"]
    else:
        names = [stem + ".linux", stem]
    base = os.path.join(REPO, folder)
    for n in names:
        p = os.path.join(base, n)
        if os.path.exists(p):
            return p
    sys.exit("no %s build for %s in %s (looked for: %s)"
             % (stem, sys.platform, base, ", ".join(names)))


def hana(sql):
    """Run one SELECT against SAP HANA and return list-of-dicts."""
    exe = binary("hana-sql", "hana-sql")
    p = subprocess.run([exe, "-csv", sql], capture_output=True, text=True, timeout=180)
    out = (p.stdout or "").strip()
    if p.returncode != 0 or out.startswith("QUERY ERROR"):
        sys.exit("HANA read failed: %s" % ((p.stderr or out).strip().splitlines() or [""])[0][:300])
    return list(csv.DictReader(io.StringIO(out))) if out else []


def classify(lines):
    """lines: iterable of dicts with 'acct' and 'budget_dim' (and optional
    'from_grpo'). Returns (lane, reasons)."""
    reasons = []
    controlled = []
    for ln in lines:
        acct = (ln.get("acct") or "").strip()
        dim = (ln.get("budget_dim") or "").strip()
        if not acct:
            # Pre-send item line copied from a GRPO: it will land on GRNI.
            if ln.get("from_grpo"):
                reasons.append("line from a GRPO -> %s %s" % (GRNI, NEVER_JSAP[GRNI]))
            continue
        if acct in NEVER_JSAP:
            reasons.append("%s %s -> not budget-controlled" % (acct, NEVER_JSAP[acct]))
            continue
        if not dim:
            reasons.append("%s has no Budget dimension" % acct)
            continue
        controlled.append((acct, dim, ln.get("acct_name") or ""))
    if controlled:
        for acct, dim, nm in controlled:
            reasons.append("%s %s + Budget '%s' -> budget-controlled" % (acct, nm[:34], dim))
        return WAITS, _dedupe(reasons)
    return POST_NOW, _dedupe(reasons)


def _dedupe(seq):
    """Same reason on twenty lines is one reason. Keeps first-seen order and
    says how many lines it covered."""
    n, order = {}, []
    for s in seq:
        if s not in n:
            order.append(s)
        n[s] = n.get(s, 0) + 1
    return [s if n[s] == 1 else "%s  (x%d lines)" % (s, n[s]) for s in order]


def fetch(company, where):
    sch = SCHEMA[company]
    sql = """
SELECT h."DocEntry", h."DocNum", h."CardName", h."NumAtCard", h."DocTotal",
       h."DocStatus", h."WddStatus",
       l."AcctCode", a."AcctName", l."OcrCode3", l."BaseType"
FROM {s}.ODRF h
JOIN {s}.DRF1 l ON l."DocEntry" = h."DocEntry"
LEFT JOIN {s}.OACT a ON a."AcctCode" = l."AcctCode"
WHERE h."ObjType" = 18 AND {w}
""".format(s=sch, w=where)
    rows = hana(sql)
    docs = {}
    for r in rows:
        de = r["DocEntry"]
        d = docs.setdefault(de, {"hdr": r, "lines": []})
        d["lines"].append({
            "acct": "" if r["AcctCode"] in ("NULL", "") else r["AcctCode"],
            "acct_name": "" if r["AcctName"] in ("NULL", "") else r["AcctName"],
            "budget_dim": "" if r["OcrCode3"] in ("NULL", "") else r["OcrCode3"],
            "from_grpo": r["BaseType"] == "20",
        })
    return docs


def report(docs, company, verbose):
    if company == "mart":
        print("JIVO MART never entered the JSAP budget process -- every Mart "
              "document is POST NOW.\n")
    buckets = {POST_NOW: [], WAITS: []}
    for de, d in sorted(docs.items(), key=lambda kv: int(kv[0])):
        lane, why = (POST_NOW, ["Mart is not in JSAP"]) if company == "mart" \
            else classify(d["lines"])
        buckets[lane].append((de, d["hdr"], why))

    for lane in (POST_NOW, WAITS):
        items = buckets[lane]
        mark = "OK" if lane == POST_NOW else "--"
        print("%s  %s  (%d)" % (mark, lane, len(items)))
        if not items:
            print("     none\n")
            continue
        for de, h, why in items:
            try:
                amt = "{:,.0f}".format(float(h["DocTotal"]))
            except (TypeError, ValueError):
                amt = h["DocTotal"]
            print("     draft %-7s %-34s %-14s Rs %12s" % (
                de, (h["CardName"] or "")[:34], (h["NumAtCard"] or "")[:14], amt))
            if verbose:
                for r in why:
                    print("               - %s" % r)
        print()
    total = len(buckets[POST_NOW]) + len(buckets[WAITS])
    if total:
        print("%d of %d can be posted without waiting for JSAP." % (
            len(buckets[POST_NOW]), total))


def refit():
    """Re-derive NEVER_JSAP from live JSAP + SAP. Prints a paste-ready dict."""
    dsr = binary("dsr-cli", "dsr")
    env = dict(os.environ)
    aryenv = os.path.join(REPO, "connections", "ary.env")
    if os.path.exists(aryenv):
        for ln in open(aryenv):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip().strip("'").strip('"')
    p = subprocess.run([dsr, "query", "--db", "jsaplive3", "--json", "--quiet",
                        "SELECT DISTINCT DocEntry FROM bud.jsBudgetTable "
                        "WHERE Branch='OIL' AND ObjType='18'"],
                       capture_output=True, text=True, timeout=180, env=env)
    if p.returncode != 0:
        sys.exit("JSAP read failed: %s" % (p.stderr or p.stdout)[:300])
    inj = {str(r["DocEntry"]) for r in json.loads(p.stdout or "[]")}
    docs = fetch("oil", "h.\"DocDate\" >= '2026-04-01'")
    stat = {}
    for de, d in docs.items():
        # count DRAFTS per account, not lines -- a 24-bilty freight bill is one
        # draft, and counting its lines would make the threshold meaningless.
        for acct in {ln["acct"] for ln in d["lines"] if ln["acct"]}:
            nm = next(ln["acct_name"] for ln in d["lines"] if ln["acct"] == acct)
            s = stat.setdefault(acct, {"n": 0, "j": 0, "name": nm})
            s["n"] += 1
            s["j"] += (de in inj)
    print("NEVER_JSAP = {")
    for a, s in sorted(stat.items()):
        if s["n"] >= 5 and s["j"] == 0:
            print('    "%s": "%s",   # %d drafts, 0 in JSAP' % (a, s["name"][:44], s["n"]))
    print("}")


def main():
    ap = argparse.ArgumentParser(description="Which lane will this document take?")
    ap.add_argument("docentry", nargs="*", help="draft DocEntry(s)")
    ap.add_argument("--company", default="oil", choices=sorted(SCHEMA))
    ap.add_argument("--pending", action="store_true",
                    help="every draft still open (nothing posted yet)")
    ap.add_argument("--payload", help="a draft payload JSON, to classify before sending")
    ap.add_argument("--since", help="only drafts created on/after YYYY-MM-DD")
    ap.add_argument("-v", "--verbose", action="store_true", help="show the reasoning")
    ap.add_argument("--refit", action="store_true", help="re-derive the account table")
    a = ap.parse_args()

    if a.refit:
        return refit()

    if a.payload:
        pl = json.load(open(a.payload))
        lines = [{"acct": ln.get("AccountCode") or "",
                  "acct_name": "",
                  "budget_dim": ln.get("CostingCode3") or "",
                  "from_grpo": ln.get("BaseType") == 20}
                 for ln in pl.get("DocumentLines", [])]
        lane, why = (POST_NOW, ["Mart is not in JSAP"]) if a.company == "mart" \
            else classify(lines)
        print("%s   %s  %s" % (lane, pl.get("CardCode", ""), pl.get("NumAtCard", "")))
        for r in why:
            print("   - %s" % r)
        return

    if a.pending:
        where = 'h."DocStatus" = \'O\''
    elif a.docentry:
        where = 'h."DocEntry" IN (%s)' % ",".join(str(int(d)) for d in a.docentry)
    else:
        ap.error("give DocEntry(s), --pending or --payload")
    if a.since:
        where += " AND h.\"CreateDate\" >= '%s'" % a.since

    docs = fetch(a.company, where)
    if not docs:
        print("No drafts matched.")
        return
    report(docs, a.company, a.verbose)


if __name__ == "__main__":
    main()
