#!/usr/bin/env python3
"""daily_sort — stop the batch moving as one lump.

THE PROBLEM THIS SOLVES
-----------------------
Every A/P draft sits in one list, mixed together. Nobody wants to read 143 rows
to work out which ones need nothing after Bhawani, so Accounts wait until the
WHOLE batch is approved and post it all at once. The result: a packing-material
bill that needed nothing is held hostage for days by a transport bill stuck in
JSAP waiting for the above office.

Bhawani's approval is NOT the bottleneck and is not touched here. The lumping is
the bottleneck. This splits the lump.

It reads. It writes nothing. It prints the trays and the exact command for the
one tray that is ready to go.

    python3 daily_sort.py                      # Oil
    python3 daily_sort.py --company bev
    python3 daily_sort.py --all                # all three books
    python3 daily_sort.py --json               # for a cron / dashboard

Lane rule and its accuracy: reference/jsap-routing.md
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jsap_route import NEVER_JSAP, POST_NOW, WAITS, binary, classify  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SAPB1 = binary("sap-b1/cli", "sapb1")
COMPANY_DB = {
    "oil": "JIVO_OIL_HANADB",
    "mart": "JIVO_MART_HANADB",
    "bev": "JIVO_BEVERAGES_HANADB",
}
LABEL = {"oil": "JIVO OIL", "mart": "JIVO MART", "bev": "JIVO BEVERAGES"}

# SAP's own word for where a draft stands. dasCancelled is old abandoned stock
# (828 of them in Oil, some from 2024) -- never show it as work.
NOT_SENT, WITH_HER, APPROVED, REJECTED = (
    "dasWithout", "dasPending", "dasApproved", "dasRejected")


def rupees(n):
    """Indian grouping, and crores/lakhs once it is worth saying."""
    n = float(n)
    if n >= 1e7:
        return "Rs %.2f Cr" % (n / 1e7)
    if n >= 1e5:
        return "Rs %.2f L" % (n / 1e5)
    return "Rs %s" % ("{:,.0f}".format(n))


def fetch(company):
    flt = ("DocObjectCode eq 'oPurchaseInvoices' and DocumentStatus eq "
           "'bost_Open' and AuthorizationStatus ne 'dasCancelled'")
    cmd = [SAPB1, "query", "Drafts", "--filter", flt, "--all", "--json",
           "--company", COMPANY_DB[company], "--select",
           "DocEntry,DocNum,CardName,NumAtCard,DocTotal,AuthorizationStatus,DocumentLines"]
    # sapb1 reads its .env (and the operator's login) from its own directory.
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                       cwd=os.path.dirname(SAPB1))
    if p.returncode != 0:
        sys.exit("SAP read failed (%s): %s" % (company, (p.stderr or p.stdout).strip()[:300]))
    return json.loads(p.stdout or "[]")


def lane_of(draft, company):
    if company == "mart":
        return POST_NOW, ["Mart is not in the JSAP budget process"]
    lines = [{"acct": (l.get("AccountCode") or "").strip(),
              "acct_name": "",
              "budget_dim": (l.get("CostingCode3") or "").strip(),
              "from_grpo": l.get("BaseType") == 20}
             for l in draft.get("DocumentLines", [])]
    if lines and not any(l["acct"] or l["from_grpo"] for l in lines):
        return "UNKNOWN", ["no account on any line - cannot call the lane"]
    return classify(lines)


def sort_book(company):
    trays = {k: [] for k in ("ready", "jsap_approved", "with_her_fast",
                             "with_her_slow", "not_sent", "rejected", "unknown")}
    for d in fetch(company):
        st = d.get("AuthorizationStatus")
        lane, _ = lane_of(d, company)
        row = (d["DocEntry"], d.get("CardName") or "", d.get("NumAtCard") or "",
               float(d.get("DocTotal") or 0))
        if lane == "UNKNOWN":
            trays["unknown"].append(row)
        elif st == APPROVED:
            trays["ready" if lane == POST_NOW else "jsap_approved"].append(row)
        elif st == WITH_HER:
            trays["with_her_fast" if lane == POST_NOW else "with_her_slow"].append(row)
        elif st == NOT_SENT:
            trays["not_sent"].append(row)
        elif st == REJECTED:
            trays["rejected"].append(row)
    return trays


def tot(rows):
    return sum(r[3] for r in rows)


def show(company, trays, limit):
    print("=" * 74)
    print("%s  --  A/P drafts" % LABEL[company])
    print("=" * 74)

    ready = sorted(trays["ready"], key=lambda r: -r[3])
    print("\n>> READY TO POST  --  %d drafts, %s" % (len(ready), rupees(tot(ready))))
    print("   Bhawani has approved these and they need NOTHING else.")
    print("   They are not waiting on JSAP and never were.\n")
    if not ready:
        print("     (none right now)")
    for de, nm, ref, amt in ready[:limit]:
        print("     %-7s %-36s %-16s %14s" % (de, nm[:36], ref[:16], "{:,.0f}".format(amt)))
    if len(ready) > limit:
        print("     ... and %d more" % (len(ready) - limit))
    if ready:
        # Print a line the operator can actually paste on THIS machine:
        # sapb1.exe on Windows, ./sapb1 on the Mac.
        exe = os.path.basename(SAPB1)
        call = exe if sys.platform == "win32" else "./" + exe
        print("\n   Post them:")
        print("     cd sap-b1%scli" % os.sep)
        print("     %s add-draft %s --dry-run"
              % (call, " ".join(str(r[0]) for r in ready[:limit])))
        print("     (drop --dry-run once the preview looks right)")

    ja = trays["jsap_approved"]
    if ja:
        print("\n>> APPROVED BUT STILL WAITING ON JSAP  --  %d, %s"
              % (len(ja), rupees(tot(ja))))
        print("   Above-office budget approval. Nothing you can do; don't hold the others for these.")

    fast, slow = trays["with_her_fast"], trays["with_her_slow"]
    print("\n>> WITH BHAWANI NOW  --  %d drafts, %s"
          % (len(fast) + len(slow), rupees(tot(fast) + tot(slow))))
    print("     %-4d will post straight after her   %s" % (len(fast), rupees(tot(fast))))
    print("     %-4d then go to JSAP and wait       %s" % (len(slow), rupees(tot(slow))))

    ns = trays["not_sent"]
    if ns:
        print("\n>> NOT SENT TO HER YET  --  %d, %s" % (len(ns), rupees(tot(ns))))
        print("   Use the jivo-add-and-new skill. A draft nobody submits is invisible to her.")

    rj, un = trays["rejected"], trays["unknown"]
    if rj:
        print("\n>> REJECTED  --  %d, %s   (her decision; fix or delete)"
              % (len(rj), rupees(tot(rj))))
    if un:
        print("\n>> CANNOT CALL THE LANE  --  %d   <- look at these by hand" % len(un))
        for de, nm, ref, amt in un[:limit]:
            print("     %-7s %-36s %s" % (de, nm[:36], ref[:16]))

    print("\n" + "-" * 74)
    if ready:
        print("Bottom line: %s can be posted today instead of waiting for the batch."
              % rupees(tot(ready)))
    else:
        print("Bottom line: nothing is approved-and-ready at this moment.")
    print()


def _default_log():
    """queries/<operator>/jsap-lane-predictions.jsonl -- the same per-operator
    shape sapb1 uses for its write log. Every box appends to its OWN file, so
    fifteen desks pushing predictions never collide on one path."""
    slug = "unregistered"
    try:
        with open(os.path.join(REPO, "harness", ".operator")) as f:
            slug = (json.load(f).get("slug") or slug).strip() or slug
    except (OSError, ValueError):
        pass
    return os.path.join(REPO, "queries", slug, "jsap-lane-predictions.jsonl")


def snapshot(company, trays, path):
    """Write down what we predicted, today, for drafts nobody has resolved yet.
    This is what makes the claim checkable later instead of just asserted: the
    rule is deterministic, but a draft's lines CAN be edited before posting, so
    the honest test records the call at the time it was made."""
    import datetime
    now = datetime.datetime.now().isoformat(timespec="seconds")
    lane = {}
    for k in ("with_her_fast", "not_sent"):
        for r in trays[k]:
            lane[r[0]] = POST_NOW
    for r in trays["with_her_slow"]:
        lane[r[0]] = WAITS
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for de, pred in sorted(lane.items()):
            f.write(json.dumps({"time": now, "company": company,
                                "DocEntry": de, "predicted": pred}) + "\n")
    print("snapshot: %d undecided drafts recorded -> %s" % (len(lane), path))


def score(path):
    """Grade every past prediction against what SAP and JSAP actually did.

    Reads EVERY desk's log, not just this box's -- the whole team's calls are
    one body of evidence, and they all sync to main."""
    import glob
    logs = sorted(glob.glob(os.path.join(REPO, "queries", "*",
                                         "jsap-lane-predictions.jsonl")))
    if path not in logs and os.path.exists(path):
        logs.append(path)
    if not logs:
        sys.exit("no prediction log yet -- run with --snapshot first")
    preds = {}
    for lg in logs:
        for ln in open(lg):
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            preds[(r["company"], r["DocEntry"])] = r      # last call wins
    print("reading %d desk log(s)" % len(logs))
    import collections
    byco = collections.defaultdict(dict)
    for (co, de), r in preds.items():
        byco[co][de] = r["predicted"]

    print("Scoring %d recorded predictions against what actually happened\n" % len(preds))
    for co, m in sorted(byco.items()):
        if co == "mart":
            print("%s: %d predictions, all POST NOW -- DEFINITIONAL, not evidence."
                  % (LABEL[co], len(m)))
            print("   JSAP's budget register has no Mart branch, so a Mart draft "
                  "cannot go to JSAP.\n")
            continue
        actual = _actual_lanes(co, list(m))
        tp = fp = tn = fn = pend = 0
        misses = []
        for de, pred in m.items():
            if de not in actual:
                pend += 1
                continue
            act = actual[de]
            if pred == WAITS and act == WAITS:
                tp += 1
            elif pred == WAITS:
                fp += 1
            elif act == WAITS:
                fn += 1
                misses.append(de)
            else:
                tn += 1
        done = tp + fp + tn + fn
        print("%s: %d resolved, %d still undecided" % (LABEL[co], done, pend))
        if done:
            print("   said POST NOW and it posted directly : %d" % tn)
            print("   said POST NOW but it went to JSAP    : %d   <-- the only harmful error" % fn)
            print("   said WAITS and it waited             : %d" % tp)
            print("   said WAITS but it posted directly    : %d   (safe error)" % fp)
            print("   POST NOW precision %.1f%%   overall %.1f%%"
                  % (100 * tn / max(1, tn + fn), 100 * (tp + tn) / done))
        if misses:
            print("   MISSED: %s" % misses)
        print()


def _actual_lanes(company, docentries):
    """Truth = did JSAP's budget register ever take this draft?"""
    branch = {"oil": "OIL", "bev": "BEVERAGE"}.get(company)
    if not branch:
        return {de: POST_NOW for de in docentries}     # Mart is never in JSAP
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
                        "WHERE Branch='%s' AND ObjType='18'" % branch],
                       capture_output=True, text=True, timeout=180, env=env)
    if p.returncode != 0:
        sys.exit("JSAP read failed: %s" % (p.stderr or p.stdout)[:200])
    inj = {int(r["DocEntry"]) for r in json.loads(p.stdout or "[]")}
    # A draft still sitting Open has not chosen a lane yet -- leave it out.
    settled = _settled(company, docentries)
    return {de: (WAITS if de in inj else POST_NOW) for de in docentries if de in settled}


def _settled(company, docentries):
    """Drafts that are no longer Open -- their lane is decided."""
    out = set()
    for i in range(0, len(docentries), 60):
        chunk = docentries[i:i + 60]
        flt = "(%s) and DocumentStatus ne 'bost_Open'" % " or ".join(
            "DocEntry eq %d" % d for d in chunk)
        p = subprocess.run([SAPB1, "query", "Drafts", "--filter", flt,
                            "--select", "DocEntry", "--all", "--json",
                            "--company", COMPANY_DB[company]],
                           capture_output=True, text=True, timeout=300,
                           cwd=os.path.dirname(SAPB1))
        if p.returncode == 0:
            out |= {int(r["DocEntry"]) for r in json.loads(p.stdout or "[]")}
    return out


def main():
    ap = argparse.ArgumentParser(description="Split the A/P draft pile into trays.")
    ap.add_argument("--company", default="oil", choices=sorted(COMPANY_DB))
    ap.add_argument("--all", action="store_true", help="all three books")
    ap.add_argument("--limit", type=int, default=25, help="rows to list per tray")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--snapshot", action="store_true",
                    help="record today's calls on undecided drafts, for later scoring")
    ap.add_argument("--score", action="store_true",
                    help="grade every recorded call against what actually happened")
    ap.add_argument("--log", default=_default_log(),
                    help="prediction log path")
    a = ap.parse_args()

    if a.score:
        return score(a.log)

    books = ["oil", "mart", "bev"] if a.all else [a.company]
    out = {}
    for co in books:
        trays = sort_book(co)
        out[co] = {k: [{"DocEntry": r[0], "CardName": r[1], "NumAtCard": r[2],
                        "DocTotal": r[3]} for r in v] for k, v in trays.items()}
        if not a.json:
            show(co, trays, a.limit)
        if a.snapshot:
            snapshot(co, trays, a.log)
    if a.json:
        print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
