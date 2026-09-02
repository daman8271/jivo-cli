#!/usr/bin/env python3
"""Derive the Service-Layer-property to HANA-column map by matching VALUES, not names.

    rosetta.py PurchaseCreditNotes ORPC            # newest document, Oil
    rosetta.py PurchaseInvoices OPCH --n 4         # cross-check across 4 documents
    rosetta.py Drafts ODRF --where '"ObjType"=18'

The write API and the database use different names for the same field, and the difference
is not guessable: `OriginalRefNo` is stored in a column called `RevRefNo`. Finding that by
hand cost an hour. So do not guess — read one real document through BOTH doors and match on
the value.

Names lie; values do not. A property and a column holding the identical value on the same
document are the same field. Checking several documents kills the coincidences (two fields
that both happen to be 0, or both hold the same date).

Output is a markdown table: property -> column, plus the properties that have no column
(computed, or living on a child table) and the columns no property exposes.

CHOOSING DOCUMENTS MATTERS. Two fields that happen to hold the same value on every document
you sampled come out "ambiguous", and the fix is a document where they differ, not more
documents. Real example: on eight consecutive credit memos the vendor's own number and the
original invoice number were identical, so `OriginalRefNo` matched both `NumAtCard` and
`RevRefNo`. Adding a predicate that forces them apart resolved it instantly:

    rosetta.py PurchaseCreditNotes ORPC --n 8 \
        --where '"NumAtCard" <> "RevRefNo" AND "RevRefNo" IS NOT NULL'

So when a property you care about lands in the ambiguous list, write a --where that
separates the candidates.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import q, columns, ROOT, COMPANIES, LOB

# sapb1 reads its .env from the CURRENT directory, so it must be run from its own folder
SAPB1_DIR = os.path.join(ROOT, "sap-b1", "cli")
SAPB1 = os.path.join(SAPB1_DIR, "sapb1")
# Fields SAP repeats on every document — matching on them produces noise, not knowledge.
BORING = {"DocEntry", "DocNum", "ObjType", "Series"}


def sl_read(entity, where, company, n):
    env = dict(os.environ, SAPB1_HOST="127.0.0.1", SAPB1_PORT="15000")
    if company:
        env["SAPB1_COMPANY"] = COMPANIES[company]
    cmd = [SAPB1, "query", entity, "--filter", where, "--top", str(n), "--json"]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300, cwd=SAPB1_DIR)
    if p.returncode != 0:
        raise SystemExit(f"sapb1 failed: {(p.stderr or p.stdout)[:500]}")
    j = json.loads(p.stdout)
    return j if isinstance(j, list) else j.get("rows") or j.get("value") or [j]


def norm(v):
    """Canonical form for comparison across the two doors."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "tYES" if v else "tNO"
    if isinstance(v, (int, float)):
        f = float(v)
        return None if f == 0 else round(f, 4)
    s = str(v).strip()
    if s in ("", "NULL", "None"):
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ]", s)   # 2026-08-13T00:00:00Z / 2026-08-13 00:00:00.0
    if m:
        return m.group(1)
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        f = float(s)
        return None if f == 0 else round(f, 4)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entity", help="Service Layer entity set, e.g. PurchaseCreditNotes")
    ap.add_argument("table", help="HANA header table, e.g. ORPC")
    ap.add_argument("--co", default="OIL")
    ap.add_argument("--n", type=int, default=3, help="documents to cross-check")
    ap.add_argument("--where", default="", help="extra HANA predicate for picking documents")
    ap.add_argument("--lines", metavar="LINE_TABLE",
                    help="map the DocumentLines collection against this line table, e.g. PCH1")
    ap.add_argument("--out")
    a = ap.parse_args()
    sch = COMPANIES[a.co.upper()]

    W = f"WHERE {a.where}" if a.where else ""
    keys = [int(r["DocEntry"]) for r in
            q(f'SELECT "DocEntry" FROM "{sch}"."{a.table}" {W} ORDER BY "DocEntry" DESC LIMIT {a.n}')]
    if not keys:
        raise SystemExit(f"no rows in {sch}.{a.table} {a.where}")

    cols = [c for c in columns(sch, a.table) if c[1] not in LOB]
    names = ", ".join(f'"{c[0]}"' for c in cols)
    hana = {int(r["DocEntry"]): r for r in
            q(f'SELECT {names} FROM "{sch}"."{a.table}" '
              f'WHERE "DocEntry" IN ({",".join(map(str, keys))})')}

    filt = " or ".join(f"DocEntry eq {k}" for k in keys)
    sl = {int(r["DocEntry"]): r for r in sl_read(a.entity, filt, a.co.upper(), len(keys))
          if isinstance(r.get("DocEntry"), int)}

    common = [k for k in keys if k in hana and k in sl]
    if not common:
        raise SystemExit("could not read the same document through both doors")

    # --lines: compare the API's DocumentLines against the HANA line table, matching
    # line-for-line on LineNum. The line side is where the naming diverges worst —
    # CostingCode..CostingCode5 are stored as OcrCode..OcrCode5 — and a line property
    # written under the wrong name is silently dropped exactly like a header one.
    if a.lines:
        lt = a.lines.upper()
        lcols = [c for c in columns(sch, lt) if c[1] not in LOB]
        lnames = ", ".join(f'"{c[0]}"' for c in lcols)
        hl = {}
        for r in q(f'SELECT {lnames} FROM "{sch}"."{lt}" '
                   f'WHERE "DocEntry" IN ({",".join(map(str, common))})'):
            hl[(int(r["DocEntry"]), int(r["LineNum"]))] = r
        pairs = []
        for k in common:
            for i, ln in enumerate(sl[k].get("DocumentLines") or []):
                key = (k, int(ln.get("LineNum", i)))
                if key in hl:
                    pairs.append((ln, hl[key]))
        if not pairs:
            raise SystemExit(f"no line pairs matched between DocumentLines and {lt}")
        lcand = {}
        lseen = defaultdict(int)
        for api_ln, h_ln in pairs:
            h = {c: norm(v) for c, v in h_ln.items()}
            this = defaultdict(set)
            for prop, pv in api_ln.items():
                if isinstance(pv, (list, dict)):
                    continue
                nv = norm(pv)
                if nv is None:
                    continue
                lseen[prop] += 1
                for c, hv in h.items():
                    if hv is not None and hv == nv:
                        this[prop].add(c)
            for pp, cs in this.items():
                # intersect only over pairs where this property actually had a value;
                # a NULL on one line says nothing about the mapping
                lcand[pp] = cs if pp not in lcand else (lcand[pp] & cs)
        lex = {pp: next(iter(cs)) for pp, cs in lcand.items() if len(cs) == 1}
        lamb = {pp: sorted(cs) for pp, cs in lcand.items() if len(cs) > 1}
        lnone = sorted(pp for pp, cs in lcand.items() if not cs)
        lren = {pp: c for pp, c in lex.items() if pp != c and pp not in BORING}
        LL = [f"# Rosetta (lines) — `{a.entity}`.DocumentLines ↔ `{lt}` · {a.co.upper()}", "",
              f"Derived from **{len(pairs)} real line pairs** across DocEntry "
              f"{', '.join(map(str, common))}, matched on `LineNum`. A pair had to agree on "
              f"every line sampled.", "",
              f"- **{len(lex)}** properties mapped to exactly one column",
              f"- **{len(lren)}** renamed ← the ones that bite", ""]
        if lren:
            LL += ["## Line properties whose name differs", "",
                   "| API property (what you send on a line) | HANA column |", "|---|---|"]
            for pp, c in sorted(lren.items()):
                LL.append(f"| `{pp}` | **`{c}`** |")
            LL.append("")
        lsame = sorted(pp for pp, c in lex.items() if pp == c)
        if lsame:
            LL += [f"## Same name on both sides ({len(lsame)})", "",
                   ", ".join(f"`{pp}`" for pp in lsame), ""]
        if lnone:
            LL += [f"## Value matched no column ({len(lnone)})", "",
                   "Computed by the Service Layer, or held on another table.", "",
                   ", ".join(f"`{pp}`" for pp in lnone), ""]
        if lamb:
            LL += ["## Ambiguous — narrow with a --where that separates the candidates", "",
                   "| API property | Candidates |", "|---|---|"]
            for pp, cs in sorted(lamb.items()):
                LL.append(f"| `{pp}` | {', '.join(f'`{c}`' for c in cs)} |")
            LL.append("")
        md = "\n".join(LL)
        if a.out:
            os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
            open(a.out, "w").write(md)
            print(f"wrote {a.out}: {len(lex)} mapped, {len(lren)} renamed, {len(pairs)} line pairs")
        else:
            print(md)
        return

    # candidate columns per property: must agree on EVERY document we looked at
    cand = {}
    prop_seen = defaultdict(int)
    for k in common:
        h = {c: norm(v) for c, v in hana[k].items()}
        this = defaultdict(set)
        for prop, pv in sl[k].items():
            if isinstance(pv, (list, dict)):
                continue
            nv = norm(pv)
            if nv is None:
                continue
            prop_seen[prop] += 1
            for c, hv in h.items():
                if hv is not None and hv == nv:
                    this[prop].add(c)
        for p, cs in this.items():
            # same rule as the line pass: only pairs where the property had a value count
            cand[p] = cs if p not in cand else (cand[p] & cs)

    exact, ambiguous, unmatched = {}, {}, []
    for p, cs in sorted(cand.items()):
        if len(cs) == 1:
            exact[p] = next(iter(cs))
        elif cs:
            ambiguous[p] = sorted(cs)
        else:
            unmatched.append(p)
    unmatched += [p for p in sorted(prop_seen) if p not in cand]

    interesting = {p: c for p, c in exact.items() if p != c and p not in BORING}
    L = [f"# Rosetta — `{a.entity}` (API) ↔ `{a.table}` (HANA) · {a.co.upper()}", "",
         f"Derived by value-matching {len(common)} real document(s) "
         f"(`DocEntry` {', '.join(map(str, common))}) read through both doors. "
         f"A pair had to agree on **every** document to be reported.", "",
         f"- **{len(exact)}** properties mapped to exactly one column",
         f"- **{len(interesting)}** of those have a **different name** on the two sides ← the dangerous ones",
         f"- {len(ambiguous)} ambiguous (several columns held the same value)",
         f"- {len(unmatched)} with no column (computed, or on a child table)", ""]

    if interesting:
        L += ["## The names that differ — memorise these or look them up", "",
              "| API property (what you send) | HANA column (what you query) |", "|---|---|"]
        for p, c in sorted(interesting.items()):
            L.append(f"| `{p}` | **`{c}`** |")
        L.append("")

    same = sorted(p for p, c in exact.items() if p == c)
    if same:
        L += [f"## Same name on both sides ({len(same)})", "",
              ", ".join(f"`{p}`" for p in same), ""]
    if ambiguous:
        L += ["## Ambiguous — value matched more than one column", "",
              "Usually a field SAP stores twice (document currency and system currency), "
              "or two flags that happen to agree. Add `--n` to break the tie.", "",
              "| API property | Candidate columns |", "|---|---|"]
        for p, cs in sorted(ambiguous.items()):
            L.append(f"| `{p}` | {', '.join(f'`{c}`' for c in cs)} |")
        L.append("")
    if unmatched:
        L += [f"## No column found ({len(unmatched)})", "",
              "Computed by the Service Layer, held on a child table, or genuinely absent "
              "from the header. Not a bug — just not queryable from this table.", "",
              ", ".join(f"`{p}`" for p in sorted(set(unmatched))), ""]

    md = "\n".join(L)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w").write(md)
        print(f"wrote {a.out}: {len(exact)} mapped, {len(interesting)} renamed")
    else:
        print(md)


if __name__ == "__main__":
    main()
