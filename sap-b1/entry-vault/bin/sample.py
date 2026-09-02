#!/usr/bin/env python3
"""Pull real posted documents in full — header, lines, and the journal they made.

    sample.py OPCH --n 3                          # 3 recent A/P invoices, Oil
    sample.py OPCH --n 5 --where "\\"CardCode\\"='VENDA001548'"
    sample.py ODRF --n 3 --where "\\"ObjType\\"=18" --co MART

Field profiles tell you what is usually filled. A real document tells you what a
finished one looks like — which is what you compare a new entry against. Only
non-empty fields are printed, so the output is the document as an operator sees it
rather than 180 columns of blanks.
"""
from __future__ import annotations
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import q, columns, table_exists, COMPANIES, DOCS, LOB, TEXTUAL, NUMERIC

SKIP = {"LogInstanc", "UserSign2", "Instance", "DataSource", "UpdateDate", "UpdateTime", "Segment"}


def blank(v, t):
    if v is None or v == "":
        return True
    if t in NUMERIC:
        try:
            return float(v) == 0
        except ValueError:
            return False
    if t in TEXTUAL and not v.strip():
        return True
    return False


def dump(sch, table, keys, key_col, title, L):
    cols = [c for c in columns(sch, table) if c[0] not in SKIP and c[1] not in LOB]
    names = ", ".join(f'"{c[0]}"' for c in cols)
    inlist = ",".join(str(k) for k in keys)
    rows = q(f'SELECT {names} FROM "{sch}"."{table}" WHERE "{key_col}" IN ({inlist}) ORDER BY "{key_col}"')
    types = {c[0]: c[1] for c in cols}
    by = {}
    for r in rows:
        by.setdefault(r[key_col], []).append(r)
    return by, types


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--co", default="OIL")
    ap.add_argument("--where", default="")
    ap.add_argument("--order", default="")
    ap.add_argument("--no-gl", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    sch = COMPANIES[a.co.upper()]
    T = a.table.upper()
    lines, objtype, label = DOCS.get(T, ([], -1, T))
    key = "AbsEntry" if T in ("OWTR", "OWTQ") and not table_exists(sch, T) else "DocEntry"

    W = f"WHERE {a.where}" if a.where else ""
    ORD = a.order or f'"{key}" DESC'
    keys = [r[key] for r in q(f'SELECT "{key}" FROM "{sch}"."{T}" {W} ORDER BY {ORD} LIMIT {a.n}')]
    if not keys:
        print(f"no rows in {sch}.{T} matching {a.where or '(all)'}"); return

    L = [f"# Real `{T}` documents ({label}) — {a.co.upper()}", "",
         f"Filter: `{a.where or 'none'}`. Only non-empty fields shown.", ""]
    hdr, htypes = dump(sch, T, keys, key, "header", L)
    for k in keys:
        r = hdr.get(k, [{}])[0]
        L.append(f"---\n\n## {T} DocEntry {k}" + (f" — DocNum {r.get('DocNum')}" if r.get("DocNum") else ""))
        L.append("")
        L.append("| Field | Value |"); L.append("|---|---|")
        for c, v in r.items():
            if not blank(v, htypes.get(c, "")):
                L.append(f'| `{c}` | {" ".join(str(v).split())[:160]} |')
        for lt in lines:
            if not table_exists(sch, lt):
                continue
            lb, ltypes = dump(sch, lt, [k], key, lt, L)
            rows = lb.get(k, [])
            if not rows:
                continue
            L += ["", f"### `{lt}` — {len(rows)} line(s)", ""]
            for i, lr in enumerate(rows, 1):
                kept = {c: v for c, v in lr.items() if not blank(v, ltypes.get(c, ""))}
                L.append(f"**line {i}**  " + " · ".join(
                    f'`{c}`={" ".join(str(v).split())[:60]}' for c, v in kept.items() if c != key))
                L.append("")
        # The document carries its own journal key in TransId — that is the only
        # reliable link. (OJDT.CreatedBy is not it, and guessing costs you the whole
        # GL side of the note.)
        tid = r.get("TransId")
        if not a.no_gl and tid and str(tid) not in ("", "NULL", "0"):
            try:
                j = q(f'''SELECT L."Line_ID" LN, L."Account" AC, MAX(O."AcctName") NM, MAX(L."ShortName") SN,
                                 SUM(L."Debit") DR, SUM(L."Credit") CR, MAX(L."LineMemo") M
                          FROM "{sch}"."JDT1" L
                          LEFT JOIN "{sch}"."OACT" O ON O."AcctCode"=L."Account"
                          WHERE L."TransId"={tid}
                          GROUP BY L."Line_ID",L."Account" ORDER BY L."Line_ID"''')
                if j:
                    L += ["", "### Journal it posted", "", "| # | Account | Name | Subledger | Debit | Credit | Memo |",
                          "|---:|---|---|---|---:|---:|---|"]
                    for r2 in j:
                        L.append(f'| {r2["LN"]} | `{r2["AC"]}` | {(r2["NM"] or "").strip()} | {r2["SN"] or ""} '
                                 f'| {float(r2["DR"] or 0):,.2f} | {float(r2["CR"] or 0):,.2f} '
                                 f'| {" ".join((r2["M"] or "").split())[:60]} |')
                    L.append("")
            except Exception as e:
                L.append(f"\n_(journal lookup failed: {e})_\n")
    md = "\n".join(L) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w").write(md); print(f"wrote {a.out} ({len(md):,} bytes)")
    else:
        print(md)


if __name__ == "__main__":
    main()
