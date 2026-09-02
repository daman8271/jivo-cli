#!/usr/bin/env python3
"""Where a document comes from and what it feeds — measured, not assumed.

    flow.py OPCH                 # A/P invoice: copied from what? how often standalone?
    flow.py OPCH --co MART --days 365
    flow.py OINV --targets       # also: what gets built on top of it

SAP records the copy-from link on every line (BaseType / BaseEntry / BaseLine) and
the copy-to link in TrgetEntry. That turns "an A/P invoice usually comes off a GRPO"
from folklore into a percentage — and the percentage is the thing that decides how an
entry is keyed, because a line copied from a receipt arrives with vendor, item, rate,
branch, warehouse and the scanned bill already on it, while a standalone line does not.
"""
from __future__ import annotations
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import q, columns, table_exists, COMPANIES, DOCS, OBJTYPE_NAME


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("--co", default="OIL")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--targets", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    sch = COMPANIES[a.co.upper()]
    T = a.table.upper()
    lines, objtype, label = DOCS.get(T, ([], -1, T))
    lt = next((x for x in lines if table_exists(sch, x)), None)
    if not lt:
        print(f"no line table known for {T}"); return

    cols = {c[0] for c in columns(sch, lt)}
    hcols = {c[0] for c in columns(sch, T)}
    dc = "DocDate" if "DocDate" in hcols else ("RefDate" if "RefDate" in hcols else None)
    W = f'AND H."{dc}" >= ADD_DAYS(CURRENT_DATE, -{a.days})' if dc else ""

    L = [f"# Flow — `{T}` ({label}) · {a.co.upper()}", "",
         f"Lines from `{lt}`, last {a.days} days. The copy-from link is what decides how much of "
         f"an entry is typed and how much arrives for free.", ""]

    if "BaseType" not in cols:
        L.append(f"_`{lt}` carries no `BaseType` — this document is never copied from anything._")
    else:
        L += ["## Copied from", "", "| Base document | Lines | Documents | Share of lines |",
              "|---|---:|---:|---:|"]
        rows = q(f'''SELECT L."BaseType" BT, COUNT(*) N, COUNT(DISTINCT L."DocEntry") D
                     FROM "{sch}"."{lt}" L JOIN "{sch}"."{T}" H ON H."DocEntry"=L."DocEntry"
                     WHERE 1=1 {W} GROUP BY L."BaseType" ORDER BY N DESC''')
        tot = sum(int(r["N"]) for r in rows) or 1
        for r in rows:
            bt = str(r["BT"])
            nm = "**keyed from scratch**" if bt in ("-1", "0", "", "NULL") else OBJTYPE_NAME.get(int(bt), f"ObjType {bt}")
            L.append(f'| `{bt}` — {nm} | {int(r["N"]):,} | {int(r["D"]):,} | {100.0*int(r["N"])/tot:.1f}% |')

        # A document is only "off a receipt" if EVERY line is. A mixed document is a
        # different job for the person keying it, so count them separately.
        L += ["", "## Documents, not lines", "",
              "A document with even one hand-keyed line is a hand-keyed job.", "",
              "| Kind | Documents | Share |", "|---|---:|---:|"]
        rows2 = q(f'''SELECT KIND, COUNT(*) C FROM (
                        SELECT L."DocEntry" DE,
                          CASE WHEN MIN(CASE WHEN L."BaseType" IN (-1,0) THEN 0 ELSE 1 END)=1 THEN 'fully copied'
                               WHEN MAX(CASE WHEN L."BaseType" IN (-1,0) THEN 0 ELSE 1 END)=0 THEN 'fully keyed'
                               ELSE 'mixed' END KIND
                        FROM "{sch}"."{lt}" L JOIN "{sch}"."{T}" H ON H."DocEntry"=L."DocEntry"
                        WHERE 1=1 {W} GROUP BY L."DocEntry")
                      GROUP BY KIND ORDER BY C DESC''')
        t2 = sum(int(r["C"]) for r in rows2) or 1
        for r in rows2:
            L.append(f'| {r["KIND"]} | {int(r["C"]):,} | {100.0*int(r["C"])/t2:.1f}% |')

    if "TrgetEntry" in cols:
        L += ["", "## What was built on top of it", "", "| Outcome | Lines | Share |", "|---|---:|---:|"]
        rows = q(f'''SELECT CASE WHEN L."TrgetEntry" IS NULL THEN 'nothing yet' ELSE 'copied onward' END K,
                            COUNT(*) N
                     FROM "{sch}"."{lt}" L JOIN "{sch}"."{T}" H ON H."DocEntry"=L."DocEntry"
                     WHERE 1=1 {W} GROUP BY CASE WHEN L."TrgetEntry" IS NULL THEN 'nothing yet' ELSE 'copied onward' END''')
        t3 = sum(int(r["N"]) for r in rows) or 1
        for r in rows:
            L.append(f'| {r["K"]} | {int(r["N"]):,} | {100.0*int(r["N"])/t3:.1f}% |')

    # was it drafted first, and does the draft survive?
    if objtype > 0 and table_exists(sch, "ODRF"):
        L += ["", "## Drafted first?", ""]
        r = q(f'''SELECT COUNT(*) N,
                         SUM(CASE WHEN "DocStatus"='O' THEN 1 ELSE 0 END) OPEN_,
                         MIN("DocDate") A, MAX("DocDate") B
                  FROM "{sch}"."ODRF" WHERE "ObjType"={objtype}
                  {f'AND "DocDate" >= ADD_DAYS(CURRENT_DATE, -{a.days})' if True else ''}''')[0]
        n = int(r["N"] or 0)
        if n:
            posted = q(f'''SELECT COUNT(*) N FROM "{sch}"."{T}" H WHERE 1=1 {W}''')[0]
            pn = int(posted["N"] or 0)
            L.append(f"- {n:,} drafts of this type in the window; {pn:,} posted documents. "
                     f"Ratio **{n/pn:.2f} drafts per posted document**"
                     f"{' — practically one each, so drafting is the normal path' if 0.7 <= n/pn <= 1.4 else ''}.")
            L.append(f"- {int(r['OPEN_'] or 0):,} of those drafts are still `DocStatus='O'` "
                     f"(includes drafts that were cancelled rather than posted — see "
                     f"[[Document-Status-and-Cancellation]]).")
        else:
            L.append("- Never drafted. This document type goes straight in.")

    # approval
    if objtype > 0 and table_exists(sch, "OWDD"):
        r = q(f'''SELECT COUNT(*) N, COUNT(DISTINCT "ObjType") OT FROM "{sch}"."OWDD"
                  WHERE "ObjType"={objtype}''')[0]
        L += ["", "## Approval", "",
              f"- {int(r['N'] or 0):,} approval requests ever raised for this object type. "
              f"See [[Approval-Workflow]]."]

    md = "\n".join(L) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w").write(md); print(f"wrote {a.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()
