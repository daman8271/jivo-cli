#!/usr/bin/env python3
"""The GL side of a document type: what hitting Add actually posts to the ledger.

    gl.py 18                  # A/P invoice, Oil, last 365 days
    gl.py 18 --co MART --days 120
    gl.py 30 --memo           # manual JEs: also show what people write in the memo

An entry is not finished when the document saves — it is finished when the journal
it produces is the journal Accounts expected. This prints, for one document type,
every GL account its journals touch, on which side, how often, and how much: the
posting fingerprint you can check a new entry against.
"""
from __future__ import annotations
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import q, COMPANIES, OBJTYPE_NAME

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transtype")
    ap.add_argument("--co", default="OIL")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--top", type=int, default=60)
    ap.add_argument("--memo", action="store_true", help="also show the most common line memos")
    ap.add_argument("--out")
    a = ap.parse_args()
    sch = COMPANIES[a.co.upper()]
    tt, W = a.transtype, f'AND J."RefDate" >= ADD_DAYS(CURRENT_DATE, -{a.days})'
    name = OBJTYPE_NAME.get(int(tt), "?") if tt.lstrip("-").isdigit() else "?"

    hdr = q(f'''SELECT COUNT(DISTINCT J."TransId") DOCS, COUNT(*) LINES,
                       SUM(L."Debit") DR, SUM(L."Credit") CR,
                       MIN(J."RefDate") A, MAX(J."RefDate") B
                FROM "{sch}"."OJDT" J JOIN "{sch}"."JDT1" L ON L."TransId"=J."TransId"
                WHERE J."TransType"={tt} {W}''')[0]
    L = [f"# GL fingerprint — TransType `{tt}` ({name}) · {a.co.upper()}", "",
         f"Window: last {a.days} days ({hdr['A'][:10] if hdr['A'] else '—'} → {hdr['B'][:10] if hdr['B'] else '—'}). "
         f"**{int(hdr['DOCS'] or 0):,} journals**, {int(hdr['LINES'] or 0):,} lines, "
         f"Dr ₹{float(hdr['DR'] or 0):,.0f} / Cr ₹{float(hdr['CR'] or 0):,.0f}.", ""]
    if not int(hdr["DOCS"] or 0):
        L.append("_Nothing posted in this window._")
        print("\n".join(L)); return

    L += ["## Accounts touched", "",
          "| Account | Name | Lines | Docs | Debit ₹ | Credit ₹ | Side |", "|---|---|---:|---:|---:|---:|---|"]
    for r in q(f'''SELECT L."Account" A, MAX(T."AcctName") NM, COUNT(*) N,
                          COUNT(DISTINCT L."TransId") D, SUM(L."Debit") DR, SUM(L."Credit") CR
                   FROM "{sch}"."OJDT" J JOIN "{sch}"."JDT1" L ON L."TransId"=J."TransId"
                   LEFT JOIN "{sch}"."OACT" T ON T."AcctCode"=L."Account"
                   WHERE J."TransType"={tt} {W} GROUP BY L."Account" ORDER BY N DESC LIMIT {a.top}'''):
        dr, cr = float(r["DR"] or 0), float(r["CR"] or 0)
        side = "Dr" if dr > cr * 20 else ("Cr" if cr > dr * 20 else "both")
        L.append(f'| `{r["A"]}` | {(r["NM"] or "").strip()} | {int(r["N"]):,} | {int(r["D"]):,} '
                 f'| {dr:,.0f} | {cr:,.0f} | {side} |')

    L += ["", "## Shape", "",
          "How many lines a journal of this type carries — an entry with an unusual line count "
          "is the cheapest signal that something was keyed differently.", "",
          "| Lines per journal | Journals |", "|---:|---:|"]
    for r in q(f'''SELECT N, COUNT(*) C FROM (
                     SELECT J."TransId" TI, COUNT(*) N
                     FROM "{sch}"."OJDT" J JOIN "{sch}"."JDT1" L ON L."TransId"=J."TransId"
                     WHERE J."TransType"={tt} {W} GROUP BY J."TransId")
                   GROUP BY N ORDER BY C DESC LIMIT 15'''):
        L.append(f'| {int(r["N"])} | {int(r["C"]):,} |')

    # which BP subledger and which dimensions the lines carry
    L += ["", "## Dimensions carried on the lines", ""]
    for col, label in [("ShortName", "Subledger / BP code"), ("Project", "Project"),
                       ("ProfitCode", "Profit centre (OcrCode)"), ("OcrCode2", "Dimension 2"),
                       ("OcrCode3", "Dimension 3"), ("OcrCode4", "Dimension 4"), ("OcrCode5", "Dimension 5"),
                       ("BPLId", "Branch (BPLId)"), ("VatGroup", "Tax code")]:
        try:
            r = q(f'''SELECT COUNT(*) N, SUM(CASE WHEN L."{col}" IS NOT NULL AND TRIM(TO_VARCHAR(L."{col}")) NOT IN ('','0') THEN 1 ELSE 0 END) F,
                             COUNT(DISTINCT L."{col}") D
                      FROM "{sch}"."OJDT" J JOIN "{sch}"."JDT1" L ON L."TransId"=J."TransId"
                      WHERE J."TransType"={tt} {W}''')[0]
        except Exception:
            continue
        n, f, d = int(r["N"] or 0), int(r["F"] or 0), int(r["D"] or 0)
        if f:
            L.append(f"- **{label}** (`{col}`) — filled on {100.0*f/n:.0f}% of lines, {d:,} distinct values")
    if a.memo:
        L += ["", "## What people write in the line memo", "", "| Memo | Lines |", "|---|---:|"]
        for r in q(f'''SELECT L."LineMemo" M, COUNT(*) N
                       FROM "{sch}"."OJDT" J JOIN "{sch}"."JDT1" L ON L."TransId"=J."TransId"
                       WHERE J."TransType"={tt} {W} AND L."LineMemo" IS NOT NULL AND TRIM(L."LineMemo")<>''
                       GROUP BY L."LineMemo" ORDER BY N DESC LIMIT 40'''):
            L.append(f'| {" ".join((r["M"] or "").split())[:90]} | {int(r["N"]):,} |')
    md = "\n".join(L) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w").write(md); print(f"wrote {a.out} ({len(md):,} bytes)")
    else:
        print(md)

if __name__ == "__main__":
    main()
