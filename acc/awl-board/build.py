#!/usr/bin/env python3
"""build.py - refresh engine for the AWL party board.

Reads one vendor's ledger live from SAP HANA through the read-only `hana-sql`
CLI and writes a self-contained dashboard to site/index.html.

What it answers, every day:
  - what went out to AWL today, and whether it was an advance or against a bill
  - what bills came in, and what shortage credit notes followed
  - what is still hanging: unpaid bills, and payments with no bill against them

Read-only by construction. hana-sql refuses anything but SELECT/WITH and runs
inside a HANA read-only transaction, so this honours CLAUDE.md RULE 0.

Usage:
    python3 build.py                          # today, JIVO Oil, AWL
    python3 build.py --as-of 2026-08-20
    python3 build.py --card VENDA000224 --company oil
    python3 build.py --days 45                # how much daily history to carry
"""
import argparse
import collections
import datetime
import itertools
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(HERE, "site")

SCHEMAS = {
    "oil": "JIVO_OIL_HANADB",
    "mart": "JIVO_MART_HANADB",
    "bev": "JIVO_BEVERAGES_HANADB",
}
COMPANY_NAME = {"oil": "JIVO Oil", "mart": "JIVO Mart", "bev": "JIVO Beverages"}

ORIGIN = {"18": "PU", "19": "PC", "46": "PS", "24": "RC", "30": "JE"}
KIND = {"18": "bill", "19": "credit note", "46": "payment", "24": "refund"}

# ------------------------------------------------------------------ hana-sql


def hana_bin():
    for name in ("hana-sql.exe", "hana-sql"):
        p = os.path.join(REPO, "hana-sql", name)
        if os.path.exists(p):
            return p
    sys.exit("hana-sql not found under %s/hana-sql" % REPO)


def query(sql):
    """Run one read-only statement, return a list of dicts.

    -env is passed explicitly and cwd is pinned to the repo: hana-sql otherwise
    searches upward from the working directory for connections/hana.env, which
    finds nothing when Task Scheduler runs this from C:\\Windows\\System32.
    """
    cmd = [hana_bin(), "-csv"]
    env_file = os.path.join(REPO, "connections", "hana.env")
    if os.path.exists(env_file):
        cmd += ["-env", env_file]
    out = subprocess.run(cmd + [sql], capture_output=True, text=True, cwd=REPO)
    if out.returncode != 0 or out.stdout.startswith("QUERY ERROR"):
        sys.stderr.write((out.stdout or "") + (out.stderr or ""))
        sys.exit(1)
    import csv as _csv
    return list(_csv.DictReader(out.stdout.splitlines()))


LEDGER_SQL = """
SELECT
  j."TransId" AS TRANSID, j."Line_ID" AS LINEID,
  TO_VARCHAR(j."RefDate",'YYYY-MM-DD') AS POSTDATE,
  TO_VARCHAR(j."DueDate",'YYYY-MM-DD') AS DUEDATE,
  TO_VARCHAR(j."TaxDate",'YYYY-MM-DD') AS DOCDATE,
  j."TransType" AS TTYPE, j."BaseRef" AS DOCNUM, o."Ref2" AS HDR_REF2,
  j."LineMemo" AS LINEMEMO, j."Debit" AS DEBIT, j."Credit" AS CREDIT,
  j."BalDueDeb" AS OPENDEB, j."BalDueCred" AS OPENCRED,
  COALESCE(pi."Comments", cm."Comments", vp."Comments", rc."Comments", o."Memo") AS HDR_REMARK
FROM "{S}"."JDT1" j
JOIN "{S}"."OJDT" o ON o."TransId" = j."TransId"
LEFT JOIN "{S}"."OPCH" pi ON pi."TransId" = j."TransId" AND j."TransType" = '18'
LEFT JOIN "{S}"."ORPC" cm ON cm."TransId" = j."TransId" AND j."TransType" = '19'
LEFT JOIN "{S}"."OVPM" vp ON vp."TransId" = j."TransId" AND j."TransType" = '46'
LEFT JOIN "{S}"."ORCT" rc ON rc."TransId" = j."TransId" AND j."TransType" = '24'
WHERE j."ShortName" = '{C}' AND j."RefDate" <= '{A}'
ORDER BY j."RefDate", j."TransId", j."Line_ID"
"""

RECON_SQL = """
SELECT i."ReconNum" AS RECONNUM, TO_VARCHAR(o."ReconDate",'YYYY-MM-DD') AS RECONDATE,
       o."ReconType" AS RECONTYPE, i."TransId" AS TRANSID, i."TransRowId" AS TRANSROW,
       i."ReconSum" AS RECONSUM, i."IsCredit" AS ISCREDIT
FROM "{S}"."ITR1" i
JOIN "{S}"."OITR" o ON o."ReconNum" = i."ReconNum"
WHERE i."ShortName" = '{C}' AND o."Canceled" = 'N' AND o."ReconDate" <= '{A}'
ORDER BY i."ReconNum", i."LineSeq"
"""

PARTY_SQL = """
SELECT "CardCode" AS CARDCODE, "CardName" AS CARDNAME, "Balance" AS BALANCE
FROM "{S}"."OCRD" WHERE "CardCode" = '{C}'
"""


# ------------------------------------------------------------------ shaping


def load(schema, card, asof):
    fmt = dict(S=schema, C=card, A=asof)
    party = query(PARTY_SQL.format(**fmt))
    led = query(LEDGER_SQL.format(**fmt))
    rec = query(RECON_SQL.format(**fmt))

    lk = {}
    for r in led:
        k = (int(r["TRANSID"]), int(r["LINEID"]))
        r["dr"] = float(r["DEBIT"])
        r["cr"] = float(r["CREDIT"])
        r["net"] = r["dr"] - r["cr"]
        r["open"] = float(r["OPENDEB"]) - float(r["OPENCRED"])
        r["docno"] = "%s %s" % (ORIGIN.get(r["TTYPE"], "??"), r["DOCNUM"])
        r["kind"] = KIND.get(r["TTYPE"], "entry")
        for f in ("HDR_REF2", "HDR_REMARK", "LINEMEMO"):
            v = (r.get(f) or "").strip()
            r[f] = "" if v.upper() == "NULL" else v.replace("\n", " ")
        r["reversal"] = r["LINEMEMO"].lower().startswith("reverse")
        lk[k] = r

    members = collections.defaultdict(list)
    meta = {}
    for r in rec:
        k = (int(r["TRANSID"]), int(r["TRANSROW"]))
        members[r["RECONNUM"]].append((k, float(r["RECONSUM"]), r["ISCREDIT"]))
        meta[r["RECONNUM"]] = dict(date=r["RECONDATE"], typ=r["RECONTYPE"])
    return party, lk, members, meta


def pair_up(lk, members, meta):
    """Match the debit and credit side of each SAP reconciliation, closest first.

    ITR1 gives the amount every line contributed; only the choice of partner
    inside a multi-line reconciliation is ours.
    """
    pairs = []
    for rn in sorted(members, key=lambda r: (meta[r]["date"], int(r))):
        cr, dr = {}, {}
        for k, a, side in members[rn]:
            tgt = cr if side == "C" else dr
            tgt[k] = tgt.get(k, 0.0) + a
        while cr and dr:
            _d, c, d = min(((abs(dv - cv), c, d) for c, cv in cr.items()
                            for d, dv in dr.items()), key=lambda t: (t[0], t[1], t[2]))
            amt = min(cr[c], dr[d])
            pairs.append((c, d, amt))
            cr[c] -= amt
            dr[d] -= amt
            if cr[c] <= 0.004:
                del cr[c]
            if dr[d] <= 0.004:
                del dr[d]
    return pairs


def build(schema, company, card, asof, days):
    party, lk, members, meta = load(schema, card, asof)
    name = party[0]["CARDNAME"] if party else card
    pairs = pair_up(lk, members, meta)

    settles = collections.defaultdict(list)      # payment -> bills it settled
    for c, d, amt in pairs:
        if lk[c]["TTYPE"] == "18" and lk[d]["TTYPE"] == "46":
            settles[d].append((lk[c]["docno"], amt))

    def line(k, extra=None):
        r = lk[k]
        row = dict(doc=r["docno"], kind=r["kind"], date=r["POSTDATE"],
                   docdate=r["DOCDATE"], trans=int(r["TRANSID"]),
                   ref=r["HDR_REF2"], memo=r["HDR_REMARK"][:180],
                   dr=round(r["dr"], 2), cr=round(r["cr"], 2),
                   open=round(abs(r["open"]), 2), reversal=r["reversal"])
        if extra:
            row.update(extra)
        return row

    # ---- per-day activity
    byday = collections.defaultdict(lambda: dict(payments=[], bills=[], notes=[]))
    for k, r in lk.items():
        d = byday[r["POSTDATE"]]
        if r["TTYPE"] == "46" and not r["reversal"]:
            against = settles.get(k, [])
            adv = round(max(r["open"], 0.0), 2)
            d["payments"].append(line(k, dict(
                against=[a for a, _s in against],
                applied=round(sum(s for _a, s in against), 2),
                advance=adv,
                mode=("advance" if not against and adv > 0.004
                      else ("part" if adv > 0.004 else "against bill")))))
        elif r["TTYPE"] == "46":
            d["payments"].append(line(k, dict(against=[], applied=0.0,
                                              advance=0.0, mode="reversal")))
        elif r["TTYPE"] == "18":
            d["bills"].append(line(k))
        elif r["TTYPE"] == "19":
            d["notes"].append(line(k))
        elif r["TTYPE"] == "24":
            d["payments"].append(line(k, dict(against=[], applied=0.0,
                                              advance=0.0, mode="refund in")))

    last = datetime.date(*map(int, asof.split("-")))
    series, detail = [], {}
    for i in range(days - 1, -1, -1):
        d = (last - datetime.timedelta(days=i)).isoformat()
        e = byday.get(d, dict(payments=[], bills=[], notes=[]))
        paid = sum(x["dr"] for x in e["payments"])
        billed = sum(x["cr"] for x in e["bills"])
        noted = sum(x["dr"] for x in e["notes"])
        series.append(dict(date=d, paid=round(paid, 2), billed=round(billed, 2),
                           notes=round(noted, 2),
                           n=len(e["payments"]) + len(e["bills"]) + len(e["notes"])))
        detail[d] = e

    # ---- what is still hanging
    open_bills = sorted([line(k, dict(age=(last - datetime.date(
        *map(int, lk[k]["POSTDATE"].split("-")))).days))
        for k, r in lk.items() if r["TTYPE"] == "18" and r["open"] < -0.004],
        key=lambda x: x["date"])
    on_acct = sorted([line(k, dict(age=(last - datetime.date(
        *map(int, lk[k]["POSTDATE"].split("-")))).days))
        for k, r in lk.items() if r["TTYPE"] == "46" and r["open"] > 0.004],
        key=lambda x: x["date"])

    # ---- an open bill and a payment on account that look like the same lorry.
    # The payment has to be within a month of the bill; without that guard an old
    # stray balance matches a recent bill on amount alone and reads as a real pair.
    def day(s):
        return datetime.date(*map(int, s.split("-")))

    todo, used = [], set()
    for b in sorted(open_bills, key=lambda x: -x["open"]):
        best = None
        for p in on_acct:
            if p["doc"] in used or p["open"] <= 100:
                continue
            if abs((day(p["date"]) - day(b["date"])).days) > 30:
                continue
            diff = abs(p["open"] - b["open"])
            if best is None or diff < best[0]:
                best = (diff, p)
        if best and best[0] <= max(0.01 * b["open"], 100):
            used.add(best[1]["doc"])
            todo.append(dict(bill=b["doc"], bill_date=b["date"], bill_amt=b["open"],
                             pay=best[1]["doc"], pay_date=best[1]["date"],
                             pay_amt=best[1]["open"], diff=round(best[0], 2),
                             clean=best[0] <= 100))

    balance = round(sum(r["net"] for r in lk.values()), 2)
    advance = round(sum(x["open"] for x in on_acct), 2)
    unpaid = round(sum(x["open"] for x in open_bills), 2)
    mtd = [s for s in series if s["date"][:7] == asof[:7]]
    lastrecon = max((meta[r]["date"] for r in meta), default=None)
    active = [s["date"] for s in series if s["n"]]

    return dict(
        meta=dict(card=card, name=name, company=COMPANY_NAME.get(company, company),
                  schema=schema, asof=asof,
                  built=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                  last_posting=max((r["POSTDATE"] for r in lk.values()), default=None),
                  last_recon=lastrecon, lines=len(lk), days=days),
        kpi=dict(balance=balance, advance=advance, unpaid=unpaid,
                 open_bills=len(open_bills), on_account=len(on_acct),
                 mtd_paid=round(sum(s["paid"] for s in mtd), 2),
                 mtd_billed=round(sum(s["billed"] for s in mtd), 2),
                 mtd_notes=round(sum(s["notes"] for s in mtd), 2)),
        series=series, detail=detail, active=active,
        open_bills=open_bills, on_account=on_acct, todo=todo)


# ------------------------------------------------------------------ archive

HISTORY = os.path.join(HERE, "history")


def archive(data, card, company, asof):
    """Keep each day's position, because most of it cannot be rebuilt later.

    A past *balance* is recoverable — re-run with --as-of and JDT1 gives it back.
    A past *open position* is not: BalDueDeb / BalDueCred are current-state
    fields, so the moment Accounts reconciles a bill, the fact that it stood open
    on a given morning is gone from SAP. Same for which payments were still
    sitting on account. That is the part worth keeping.

    Writes history/<card>/<date>.json (the day, in full) and appends one row to
    history/<card>/positions.csv (the trend). Re-running the same day overwrites
    that day rather than duplicating it.
    """
    # Only today can be archived. --as-of rebuilds a past balance correctly, but
    # the open figures on it are still TODAY's BalDue* flags, so a back-dated
    # snapshot would record an open position that never existed on that date.
    if asof != datetime.date.today().isoformat():
        print("  not archived  (--as-of %s is a rebuilt position; its open "
              "figures are today's, so archiving it would be wrong)" % asof)
        return None

    folder = os.path.join(HISTORY, card)
    os.makedirs(folder, exist_ok=True)

    day = data["detail"].get(asof, dict(payments=[], bills=[], notes=[]))
    snap = dict(meta=data["meta"], kpi=data["kpi"], day=day,
                open_bills=data["open_bills"], on_account=data["on_account"],
                todo=data["todo"])
    with open(os.path.join(folder, "%s.json" % asof), "w", encoding="utf-8") as f:
        json.dump(snap, f, separators=(",", ":"))

    k = data["kpi"]
    row = [asof, card, company, data["meta"]["name"],
           "%.2f" % k["balance"], "%.2f" % k["advance"], "%.2f" % k["unpaid"],
           str(k["open_bills"]), str(k["on_account"]),
           "%.2f" % sum(x["dr"] for x in day["payments"]),
           "%.2f" % sum(x["cr"] for x in day["bills"]),
           "%.2f" % sum(x["dr"] for x in day["notes"]),
           str(len(data["todo"])), data["meta"]["built"]]
    head = ("date,card,company,name,balance,advance,unpaid,open_bills,"
            "on_account,paid_today,billed_today,notes_today,to_reconcile,built")
    path = os.path.join(folder, "positions.csv")
    kept = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            kept = [ln.rstrip("\n") for ln in f
                    if ln.strip() and not ln.startswith("date,")
                    and not ln.startswith(asof + ",")]
    kept.append(",".join(row))
    kept.sort()
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n" + "\n".join(kept) + "\n")
    return folder


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", default="VENDA000224")
    ap.add_argument("--company", default="oil", choices=list(SCHEMAS))
    ap.add_argument("--as-of", dest="asof", default=datetime.date.today().isoformat())
    ap.add_argument("--days", type=int, default=45)
    ap.add_argument("--json-only", action="store_true")
    a = ap.parse_args()

    data = build(SCHEMAS[a.company], a.company, a.card, a.asof, a.days)
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    archived = archive(data, a.card, a.company, a.asof)

    if not a.json_only:
        tpl = os.path.join(HERE, "template.html")
        if os.path.exists(tpl):
            html = open(tpl, encoding="utf-8").read()
            html = html.replace("/*__DATA__*/null",
                                json.dumps(data, separators=(",", ":")))
            # template.html is a body fragment (so it can also be published as an
            # artifact, which supplies its own skeleton). A file opened straight
            # off disk needs the doctype, or the browser drops into quirks mode
            # and tables stop inheriting colour.
            page = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n'
                    '<meta charset="utf-8">\n'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                    '<meta name="color-scheme" content="light dark">\n'
                    '</head>\n<body>\n' + html + '\n</body>\n</html>\n')
            with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
                f.write(page)

    k = data["kpi"]
    print("%s (%s) - %s, as at %s" % (data["meta"]["name"], a.card,
                                      data["meta"]["company"], a.asof))
    print("  balance          %18s Dr" % f"{k['balance']:,.2f}")
    print("  advance with AWL %18s  (%d payments)" % (f"{k['advance']:,.2f}", k["on_account"]))
    print("  unpaid bills     %18s  (%d bills)" % (f"{k['unpaid']:,.2f}", k["open_bills"]))
    print("  this month       paid %s | billed %s"
          % (f"{k['mtd_paid']:,.2f}", f"{k['mtd_billed']:,.2f}"))
    print("  to reconcile in SAP: %d" % len(data["todo"]))
    print("  written to", os.path.join(SITE, "index.html"))
    if archived:
        print("  archived  ", os.path.join(archived, a.asof + ".json"))


if __name__ == "__main__":
    main()
