#!/usr/bin/env python3
"""Field-level profile of a live SAP table: what JIVO's operators actually fill in.

    profile.py OPCH                              # A/P invoice headers, all 3 books
    profile.py PCH1 --co OIL --days 120          # its lines, Oil, recent window
    profile.py OPCH --out ../_data/OPCH.md       # write markdown

For every column it reports how often the field is non-empty across all history
and across a recent window, how many distinct values it holds, and — where the
cardinality is low enough to be a vocabulary rather than data — the actual values
with counts. That is the difference between "SAP has a field called CostingCode3"
and "at JIVO that field is filled on 61% of factory lines and only ever holds one
of four budget codes".

Every table costs a handful of SQL statements, not one per column: each round trip
crosses an SSH tunnel, so the profile is built from a few wide conditional-aggregate
scans and one UNION ALL vocabulary sweep.
"""
from __future__ import annotations
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import q, q1, columns, table_exists, filled_expr, COMPANIES, NUMERIC, TEXTUAL, LOB

DATE_PREF = ["DocDate", "RefDate", "TaxDate", "CreateDate", "DueDate"]
NOISE = {"LogInstanc", "UserSign2", "Instance", "DataSource", "UpdateDate", "UpdateTime", "Segment"}


def date_col(schema, table):
    names = {c[0] for c in columns(schema, table)}
    return next((d for d in DATE_PREF if d in names), None)


def profile(schema, table, days, chunk=45):
    cols = columns(schema, table)
    dc = date_col(schema, table)
    rec = f'"{dc}" >= ADD_DAYS(CURRENT_DATE, -{days})' if dc else "1=0"

    head = q(f'''SELECT COUNT(*) N, SUM(CASE WHEN {rec} THEN 1 ELSE 0 END) NR
                 {f', MIN("{dc}") A, MAX("{dc}") B' if dc else ''}
                 FROM "{schema}"."{table}"''')[0]
    n = int(head["N"] or 0)
    if n == 0:
        return {"n": 0}
    n_rec = int(head["NR"] or 0)
    rng = (head["A"], head["B"]) if dc else None

    f_all, f_rec, dist = {}, {}, {}
    for i in range(0, len(cols), chunk):
        part = cols[i:i + chunk]
        sel = []
        for j, (c, t, _l, _p) in enumerate(part):
            fe = filled_expr(c, t)
            sel.append(f'{fe} AS "A{j}"')
            # the same predicate, restricted to the window — one scan, both numbers
            sel.append(f'{fe.replace("CASE WHEN ", f"CASE WHEN ({rec}) AND ", 1)} AS "R{j}"')
            if t not in LOB:
                sel.append(f'COUNT(DISTINCT "{c}") AS "D{j}"')
        r = q(f'SELECT {", ".join(sel)} FROM "{schema}"."{table}"')[0]
        for j, (c, t, _l, _p) in enumerate(part):
            f_all[c] = int(r[f"A{j}"] or 0)
            f_rec[c] = int(r[f"R{j}"] or 0)
            if t not in LOB:
                dist[c] = int(r[f"D{j}"] or 0)
    return {"n": n, "n_recent": n_rec, "date_col": dc, "range": rng,
            "cols": cols, "colset": {c[0] for c in cols},
            "f_all": f_all, "f_rec": f_rec, "dist": dist}


def vocabularies(schema, table, p, vocab_max, limit=30):
    """One statement, every low-cardinality column's value list."""
    targets = [(c, t) for (c, t, _l, _pp) in p["cols"]
               if c not in NOISE and t not in LOB
               and 0 < p["dist"].get(c, 0) <= vocab_max and p["f_all"].get(c, 0) > 0]
    if not targets:
        return {}
    parts = [f'''SELECT '{c}' AS C, TO_VARCHAR("{c}") AS V, COUNT(*) AS N
                 FROM "{schema}"."{table}" GROUP BY TO_VARCHAR("{c}")''' for c, _t in targets]
    out = {}
    B = 40  # keep the statement from getting absurd on very wide tables
    for i in range(0, len(parts), B):
        for r in q("\nUNION ALL ".join(parts[i:i + B]) + " ORDER BY C, N DESC"):
            out.setdefault(r["C"], []).append((r["V"], int(r["N"])))
    # A closed set of long free-text blobs (addresses, remarks) is not a vocabulary —
    # it is just sparse data, and printing it drowns the real drop-downs.
    def flat(v):
        return " ".join((v or "").split())
    keep = {}
    for k, v in out.items():
        vals = [(flat(a), b) for a, b in sorted(v, key=lambda x: -x[1])[:limit]]
        if max((len(a) for a, _ in vals), default=0) > 48:
            continue
        keep[k] = vals
    return keep


def render(table, per_co, days, vocab, vocab_co, show_empty):
    L = [f"# `{table}` — field profile", "",
         f"> Mined live from HANA. Recent window = last **{days} days**. "
         f"*Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` "
         f"in fields nobody ever types in, so a NULL test alone calls every field 100% used.",
         "", "| Book | Rows | Rows in window | Date column | Span |", "|---|---:|---:|---|---|"]
    for co, p in per_co.items():
        if not p.get("n"):
            L.append(f"| {co} | 0 | — | — | **not used in this book** |"); continue
        sp = f"{p['range'][0][:10]} → {p['range'][1][:10]}" if p["range"] else "—"
        L.append(f"| {co} | {p['n']:,} | {p['n_recent']:,} | `{p['date_col'] or '—'}` | {sp} |")
    L.append("")
    live = [c for c in per_co if per_co[c].get("n")]
    if not live:
        return "\n".join(L) + "\nTable is empty in every book.\n"

    base = per_co[live[0]]
    L += ["## Fields", "",
          "Sorted as SAP stores them. **`—`** means the column exists in that book and is "
          "empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the "
          "column does not exist in that book at all — a different fact entirely, and one "
          "that makes a write fail rather than merely do nothing.", "",
          "| Field | Type | " + " | ".join(f"{co} all" for co in live) + " | " +
          " | ".join(f"{co} {days}d" for co in live) + " | Distinct | Reads as |",
          "|---|---|" + "---:|" * (2 * len(live)) + "---:|---|"]
    for (c, t, ln, _p) in base["cols"]:
        if c in NOISE:
            continue
        cells_all, cells_rec, any_use = [], [], False
        for co in live:
            p = per_co[co]
            if c not in p.get("colset", ()):          # column absent in this book
                cells_all.append("n/a"); cells_rec.append("n/a"); continue
            fa = p["f_all"].get(c, 0)
            pa = 100.0 * fa / (p["n"] or 1)
            any_use = any_use or bool(fa)
            cells_all.append("—" if not fa else (f"{pa:.0f}%" if pa >= 1 else "<1%"))
            tr, fr = p["n_recent"] or 0, p["f_rec"].get(c, 0)
            pr = 100.0 * fr / tr if tr else 0
            cells_rec.append("·" if not tr else ("—" if not fr else (f"{pr:.0f}%" if pr >= 1 else "<1%")))
        if not any_use and not show_empty:
            continue
        ty = f"{t}({ln})" if t in TEXTUAL and ln else t
        d = base["dist"].get(c, 0)
        L.append(f"| `{c}` | {ty} | " + " | ".join(cells_all) + " | " + " | ".join(cells_rec) + f" | {d:,} | |")
    L += ["", "_**Reads as** is deliberately blank: fill it with what the field means in JIVO's "
              "terms, not SAP's. That column is the whole point of the note._", ""]

    # Columns that exist in one book and not another. This is the single most common cause
    # of a payload that works in Oil and fails in Mart, so it gets its own section.
    if len(live) > 1:
        allcols = set()
        for co in live:
            allcols |= per_co[co].get("colset", set())
        drift = []
        for c in sorted(allcols):
            have = [co for co in live if c in per_co[co].get("colset", ())]
            if len(have) != len(live):
                drift.append((c, have))
        if drift:
            L += [f"## Columns that do not exist in every book ({len(drift)})", "",
                  "A field present in one book and absent in another. Sending it to the book "
                  "that lacks it is an error, not a no-op.", "",
                  "| Column | Present in | Missing from |", "|---|---|---|"]
            for c, have in drift:
                miss = [co for co in live if co not in have]
                L.append(f"| `{c}` | {', '.join(have)} | **{', '.join(miss)}** |")
            L.append("")

    if vocab:
        L += [f"## Value vocabularies ({vocab_co})", "",
              "Columns holding a small closed set of values. These are the drop-downs and flags "
              "an operator picks from, so the list *is* the rule.", ""]
        for (c, _t, _l, _pp) in base["cols"]:
            if c in vocab:
                shown = ", ".join(f"`{v if v not in (None, '') else '∅'}`×{n:,}" for v, n in vocab[c])
                L.append(f"- **`{c}`** ({len(vocab[c])} values) — {shown}")
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("--co", default="OIL,MART,BEV")
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--vocab-max", type=int, default=25)
    ap.add_argument("--vocab-co", default="OIL")
    ap.add_argument("--show-empty", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    per_co = {}
    for co in [c.strip().upper() for c in a.co.split(",") if c.strip()]:
        sch = COMPANIES[co]
        per_co[co] = profile(sch, a.table, a.days) if table_exists(sch, a.table) else {"n": 0}

    vco = a.vocab_co.upper()
    voc = {}
    if per_co.get(vco, {}).get("n"):
        voc = vocabularies(COMPANIES[vco], a.table, per_co[vco], a.vocab_max)
    elif any(p.get("n") for p in per_co.values()):
        vco = next(c for c in per_co if per_co[c].get("n"))
        voc = vocabularies(COMPANIES[vco], a.table, per_co[vco], a.vocab_max)

    md = render(a.table, per_co, a.days, voc, vco, a.show_empty)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w").write(md)
        print(f"wrote {a.out} ({len(md):,} bytes, {sum(1 for l in md.splitlines() if l.startswith('| `'))} fields)")
    else:
        print(md)


if __name__ == "__main__":
    main()
